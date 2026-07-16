"""Smoke regression for the markdown-to-pdf skill.

PDF binaries are not stable byte-for-byte across runs (timestamps, fonts,
metadata), so the regression here is structural: each fixture markdown renders
to a non-empty PDF that starts with the `%PDF-` magic and is at least 1 KB.

This gate does not inspect the rendered appearance, so it does not catch a
theme's print-CSS changes (heading numbering, accent colours, table rules).
Those are checked manually against the committed reference renders under
`docs/design/themes/`; an automated PDF visual regression is a follow-up.
"""
from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

SAMPLE_MD = """---
title: "Regression Sample"
---

# Heading One

A paragraph with **bold** and *italic* text.

## Subheading

- item one
- item two

| col a | col b |
| --- | --- |
| 1 | 2 |
| 3 | 4 |
"""


@pytest.fixture(scope="module")
def chromium_ready():
    from playwright.sync_api import sync_playwright

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            browser.close()
    except Exception as exc:
        pytest.skip(f"Playwright chromium unavailable: {exc}")


@pytest.mark.parametrize(
    "theme",
    [
        "default",
        "academic",
        "business",
        "minimal",
        # Redesign theme pack (#393): smoke-render every new overlay so a
        # malformed stylesheet that breaks Chromium is caught, not just its
        # metadata.
        "letter",
        "manuscript",
        "newsprint",
        "notebook",
        "novel",
        "resume",
        "slate",
        "slides",
        "techbook",
        "whitepaper",
    ],
)
def test_md_to_pdf_renders_each_theme(theme, md_to_pdf_mod, chromium_ready):
    # Every registered theme renders the standard sample to a valid PDF (#23).
    # The PDF binary is not stable byte-for-byte, so the regression stays
    # structural (magic + size), matching the rest of this suite. CSS paths are
    # resolved from the templates dir directly (the registry's own resolution is
    # unit-tested under the API venv; this root suite avoids the FastAPI import
    # chain), mirroring the renderer's stack-on-default contract.
    from app.config import MD_TO_PDF_TEMPLATES

    default_css = MD_TO_PDF_TEMPLATES / "default.css"
    css_paths = [default_css] if theme == "default" else [default_css, MD_TO_PDF_TEMPLATES / f"{theme}.css"]
    assert all(p.exists() for p in css_paths), f"missing css for theme {theme}: {css_paths}"

    with tempfile.TemporaryDirectory(prefix="regress-md2pdf-") as raw:
        md_path = Path(raw) / "doc.md"
        pdf_path = Path(raw) / "doc.pdf"
        md_path.write_text(SAMPLE_MD, encoding="utf-8")
        md_to_pdf_mod.convert(md_path, pdf_path, css_paths, lang="pt-BR")
        data = pdf_path.read_bytes()

    assert data.startswith(b"%PDF-"), f"theme {theme}: output is not a PDF"
    assert len(data) > 1024, f"theme {theme}: PDF too small ({len(data)} bytes)"


MERMAID_MD = """---
title: "Diagram"
---

# Flow

```mermaid
flowchart LR
  A[PDF] --> B[Markdown]
  B --> C[PDF]
```
"""


def test_mermaid_opt_in_renders_a_diagram(md_to_pdf_mod, chromium_ready):
    # #394: with render_mermaid on, the fence renders to an SVG diagram (extra
    # vector paths); off, it stays a plain code block. Structural like the rest
    # of the suite (PDFs are not byte-stable), comparing the two renders of the
    # same document so the diagram's paths are the observable difference.
    import fitz
    from app.config import MD_TO_PDF_TEMPLATES

    css_paths = [MD_TO_PDF_TEMPLATES / "default.css"]
    with tempfile.TemporaryDirectory(prefix="regress-mermaid-") as raw:
        md_path = Path(raw) / "doc.md"
        md_path.write_text(MERMAID_MD, encoding="utf-8")
        on_pdf = Path(raw) / "on.pdf"
        off_pdf = Path(raw) / "off.pdf"

        md_to_pdf_mod.convert(md_path, on_pdf, css_paths, lang="pt-BR", render_mermaid=True)
        md_to_pdf_mod.convert(md_path, off_pdf, css_paths, lang="pt-BR", render_mermaid=False)

        on_bytes = on_pdf.read_bytes()
        assert on_bytes.startswith(b"%PDF-")
        with fitz.open(on_pdf) as on_doc, fitz.open(off_pdf) as off_doc:
            on_paths = len(on_doc[0].get_drawings())
            off_paths = len(off_doc[0].get_drawings())

    # The rendered flowchart draws vector paths the plain code block never does.
    assert on_paths > off_paths, f"diagram did not render (on={on_paths}, off={off_paths})"


def test_custom_css_changes_the_render(md_to_pdf_mod, chromium_ready):
    # #395: user CSS stacks after the theme, so it changes the render. Compare the
    # same document with and without a body-background rule; with print_background
    # on, the styled page rasterizes differently. Empty custom CSS is a no-op by
    # construction (the block is only appended when non-blank), so output stays
    # byte-for-byte unchanged then.
    import fitz
    from app.config import MD_TO_PDF_TEMPLATES

    css_paths = [MD_TO_PDF_TEMPLATES / "default.css"]
    with tempfile.TemporaryDirectory(prefix="regress-custom-css-") as raw:
        md_path = Path(raw) / "doc.md"
        md_path.write_text(SAMPLE_MD, encoding="utf-8")
        plain = Path(raw) / "plain.pdf"
        styled = Path(raw) / "styled.pdf"

        md_to_pdf_mod.convert(md_path, plain, css_paths, lang="pt-BR")
        md_to_pdf_mod.convert(
            md_path, styled, css_paths, lang="pt-BR", custom_css="body { background: #123456; }"
        )

        assert styled.read_bytes().startswith(b"%PDF-")
        with fitz.open(plain) as p_doc, fitz.open(styled) as s_doc:
            p_px = p_doc[0].get_pixmap(dpi=60)
            s_px = s_doc[0].get_pixmap(dpi=60)
            same_size = (p_px.width, p_px.height) == (s_px.width, s_px.height)
            differ = p_px.samples != s_px.samples

    assert same_size and differ, "custom CSS did not change the rendered page"


COMPLEX_FM_MD = """---
title: "Front Matter Sample"
keywords: [zzqkeyword1, zzqkeyword2, zzqkeyword3]
author:
  name: Ada Lovelace
  email: ada@example.org
description: |
  First line of the abstract.
  Second line of the abstract.
---

# Body Heading

A plain body paragraph.
"""


def test_md_to_pdf_renders_complex_front_matter(md_to_pdf_mod, chromium_ready):
    # #150: list, nested-mapping, and block-scalar front matter must not leak
    # into the rendered body and must still produce a valid PDF.
    from app.config import MD_TO_PDF_TEMPLATES

    css = MD_TO_PDF_TEMPLATES / "default.css"

    # The parsed front matter carries the structured values, and none of them
    # bleed into the body markdown that gets rendered.
    fm, body_md = md_to_pdf_mod.split_front_matter(COMPLEX_FM_MD)
    assert fm["keywords"] == ["zzqkeyword1", "zzqkeyword2", "zzqkeyword3"]
    assert fm["author"] == {"name": "Ada Lovelace", "email": "ada@example.org"}
    assert "zzqkeyword1" not in body_md
    assert "ada@example.org" not in body_md

    with tempfile.TemporaryDirectory(prefix="regress-md2pdf-fm-") as raw:
        md_path = Path(raw) / "doc.md"
        pdf_path = Path(raw) / "doc.pdf"
        md_path.write_text(COMPLEX_FM_MD, encoding="utf-8")
        md_to_pdf_mod.convert(md_path, pdf_path, [css], lang="en")
        data = pdf_path.read_bytes()

    assert data.startswith(b"%PDF-"), "output is not a PDF"
    assert len(data) > 1024, f"PDF too small to be plausible: {len(data)} bytes"
