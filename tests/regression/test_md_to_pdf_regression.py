"""Smoke regression for the markdown-to-pdf skill.

PDF binaries are not stable byte-for-byte across runs (timestamps, fonts,
metadata), so the regression here is structural: each fixture markdown renders
to a non-empty PDF that starts with the `%PDF-` magic and is at least 1 KB.
Visual changes are caught by the per-PDF golden files of pdf-to-md round-trip
elsewhere in the suite.
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


@pytest.mark.parametrize("theme", ["default", "academic", "business", "minimal"])
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
