from __future__ import annotations

import pytest

SAMPLE_MD = b"""---
title: "Test Document"
---

# Heading One

This is a paragraph with **bold** and *italic*.

- bullet one
- bullet two

| col a | col b |
| --- | --- |
| 1 | 2 |
"""


@pytest.fixture(scope="module")
def chromium_ready():
    """Skip md-to-pdf tests if Playwright's Chromium isn't installed locally."""
    from playwright.sync_api import sync_playwright

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            browser.close()
    except Exception as exc:
        pytest.skip(f"Playwright chromium unavailable: {exc}")


def test_md_to_pdf_returns_pdf(client, chromium_ready):
    resp = client.post(
        "/api/md-to-pdf",
        files={"file": ("doc.md", SAMPLE_MD, "text/markdown")},
    )
    assert resp.status_code == 200, resp.text
    assert resp.headers["content-type"].startswith("application/pdf")
    assert resp.content[:5] == b"%PDF-"


def test_md_to_pdf_renders_a_gfm_alert(client, chromium_ready):
    # The callout extension is wired into the render endpoint (#159): a document
    # with a GFM alert renders end-to-end through Chromium without error. The
    # transform-to-callout HTML is covered in tests/unit/test_callouts.py.
    alert_md = b"# Doc\n\n> [!WARNING]\n> This action cannot be undone.\n"
    resp = client.post(
        "/api/md-to-pdf",
        files={"file": ("doc.md", alert_md, "text/markdown")},
    )
    assert resp.status_code == 200, resp.text
    assert resp.content[:5] == b"%PDF-"


def test_md_to_pdf_render_mermaid_reaches_the_pipeline(client, chromium_ready):
    # #439: the render_mermaid option must flow API -> service -> convert, not
    # just be accepted by the schema (ledger pattern 15). Assert structurally,
    # not on raw bytes: PDF output is not byte-stable, so off.content != on.content
    # could pass without a diagram actually rendering. The flowchart draws vector
    # paths a plain code block never does, so the page's drawing count is the
    # observable proof. Mirrors tests/regression/test_md_to_pdf_regression.py.
    import json

    import fitz

    mermaid_md = b"# Doc\n\n```mermaid\nflowchart LR\n  A --> B\n```\n"
    off = client.post(
        "/api/md-to-pdf",
        files={"file": ("d.md", mermaid_md, "text/markdown")},
        data={"options": json.dumps({"render_mermaid": False})},
    )
    on = client.post(
        "/api/md-to-pdf",
        files={"file": ("d.md", mermaid_md, "text/markdown")},
        data={"options": json.dumps({"render_mermaid": True})},
    )
    assert off.status_code == 200, off.text
    assert on.status_code == 200, on.text
    assert off.content[:5] == b"%PDF-"
    assert on.content[:5] == b"%PDF-"

    on_doc = fitz.open(stream=on.content, filetype="pdf")
    off_doc = fitz.open(stream=off.content, filetype="pdf")
    on_paths = len(on_doc[0].get_drawings())
    off_paths = len(off_doc[0].get_drawings())
    # The rendered flowchart draws vector paths the plain code block never does.
    assert on_paths > off_paths, f"diagram did not render (on={on_paths}, off={off_paths})"
    # Off leaves the mermaid source visible as code text; on replaces it with a diagram.
    assert "flowchart LR" in off_doc[0].get_text()
    assert "flowchart LR" not in on_doc[0].get_text()


def test_md_to_pdf_unknown_theme_returns_400(client):
    # An unknown theme is rejected at the service before any rendering, so this
    # needs no Chromium. Uses the documented error envelope.
    import json

    resp = client.post(
        "/api/md-to-pdf",
        files={"file": ("doc.md", SAMPLE_MD, "text/markdown")},
        data={"options": json.dumps({"theme": "no-such-theme"})},
    )
    assert resp.status_code == 400, resp.text
    assert resp.json()["error"]["code"] == "unknown_theme"


def test_md_to_pdf_rejects_non_md(client):
    resp = client.post(
        "/api/md-to-pdf",
        files={"file": ("doc.txt", b"hello", "text/plain")},
    )
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "wrong_file_type"


# A YAML billion-laughs payload in front matter (#150 review): the parser must
# reject the aliases and still render the body, so the endpoint returns 200 with
# a PDF, not a 500. Confirms the malformed-front-matter contract end to end.
BOMB_MD = b"""---
a: &a [1,1,1,1,1,1,1,1,1]
b: &b [*a,*a,*a,*a,*a,*a,*a,*a,*a]
c: &c [*b,*b,*b,*b,*b,*b,*b,*b,*b]
d: [*c,*c,*c,*c,*c,*c,*c,*c,*c]
---

# Body still renders

A paragraph after a hostile front matter block.
"""


def test_md_to_pdf_survives_yaml_bomb_front_matter(client, chromium_ready):
    resp = client.post(
        "/api/md-to-pdf",
        files={"file": ("bomb.md", BOMB_MD, "text/markdown")},
    )
    assert resp.status_code == 200, resp.text
    assert resp.content[:5] == b"%PDF-"


# --- #243: page setup (page size, margins, running header/footer) -----------

PT = 72.0 / 2.54  # points per cm; PyMuPDF page.rect is in points
PAGE_PT = {"A4": (595, 842), "Letter": (612, 792), "Legal": (612, 1008)}


def _render(client, md: bytes, options: dict | None = None):
    import json

    data = {"options": json.dumps(options)} if options else None
    resp = client.post("/api/md-to-pdf", files={"file": ("doc.md", md, "text/markdown")}, data=data)
    return resp


def test_page_setup_letter_changes_the_page_dimensions(client, chromium_ready):
    import fitz

    resp = _render(client, SAMPLE_MD, {"page_setup": {"page_size": "Letter"}})
    assert resp.status_code == 200, resp.text
    doc = fitz.open(stream=resp.content, filetype="pdf")
    w, h = doc[0].rect.width, doc[0].rect.height
    assert abs(w - PAGE_PT["Letter"][0]) < 2 and abs(h - PAGE_PT["Letter"][1]) < 2, (w, h)


def test_default_page_is_a4(client, chromium_ready):
    import fitz

    resp = _render(client, SAMPLE_MD)
    doc = fitz.open(stream=resp.content, filetype="pdf")
    w, h = doc[0].rect.width, doc[0].rect.height
    assert abs(w - PAGE_PT["A4"][0]) < 2 and abs(h - PAGE_PT["A4"][1]) < 2, (w, h)


def test_footer_page_number_renders_in_the_output(client, chromium_ready):
    import fitz

    resp = _render(client, SAMPLE_MD, {"page_setup": {"footer": {"center": "{{page}} / {{pages}}"}}})
    assert resp.status_code == 200, resp.text
    doc = fitz.open(stream=resp.content, filetype="pdf")
    text = doc[0].get_text()
    # Chromium fills pageNumber/totalPages: page 1 of 1 -> "1 / 1" in the footer band.
    assert "1 / 1" in text or "1/1" in text.replace(" ", ""), text[-200:]


def test_header_substitutes_front_matter_title(client, chromium_ready):
    import fitz

    md = b"""---\ntitle: "Quarterly Report"\n---\n\n# Body\n\nText.\n"""
    resp = _render(client, md, {"page_setup": {"header": {"left": "{{title}}"}}})
    assert resp.status_code == 200, resp.text
    doc = fitz.open(stream=resp.content, filetype="pdf")
    assert "Quarterly Report" in doc[0].get_text()


def test_page_setup_render_is_content_deterministic(client, chromium_ready):
    # page.pdf embeds a creation timestamp so bytes are not stable; assert the
    # content is: same page count, dimensions, and text across two runs (#243).
    import fitz

    opts = {"page_setup": {"page_size": "Letter", "footer": {"center": "{{page}}"}}}
    a = _render(client, SAMPLE_MD, opts)
    b = _render(client, SAMPLE_MD, opts)
    da, db = fitz.open(stream=a.content, filetype="pdf"), fitz.open(stream=b.content, filetype="pdf")
    assert da.page_count == db.page_count
    assert [p.rect.width for p in da] == [p.rect.width for p in db]
    assert [p.get_text() for p in da] == [p.get_text() for p in db]


def test_invalid_page_size_is_422(client):
    # Outside the Literal -> schema rejects before any render; no Chromium needed.
    resp = _render(client, SAMPLE_MD, {"page_setup": {"page_size": "A3"}})
    assert resp.status_code == 422, resp.text


def test_unknown_page_setup_field_is_422(client):
    resp = _render(client, SAMPLE_MD, {"page_setup": {"bogus": 1}})
    assert resp.status_code == 422, resp.text


# --- #177 setext headings + #160 HTML comments: accepted renderer input ------

SETEXT_MD = b"""Setext H1
=========

Setext H2
---------

Body paragraph.
"""


def test_setext_headings_render_as_headings(client, chromium_ready):
    # Underlined (setext) headings are valid CommonMark input; they must reach
    # the PDF as heading text, not literal "=====" lines (#177). Read the real
    # page back with PyMuPDF rather than trusting the request.
    import fitz

    resp = _render(client, SETEXT_MD)
    assert resp.status_code == 200, resp.text
    doc = fitz.open(stream=resp.content, filetype="pdf")
    text = doc[0].get_text()
    assert "Setext H1" in text and "Setext H2" in text, text
    # The underline markers must not survive as literal characters.
    assert "=========" not in text and "---------" not in text, text


COMMENT_MD = b"""Para A.

<!-- hidden build note -->

Para B.
"""


def test_html_comment_does_not_render_in_the_pdf(client, chromium_ready):
    # HTML comments pass through to the HTML but must stay invisible in the
    # rendered PDF: the note text must not leak as visible content (#160).
    import fitz

    resp = _render(client, COMMENT_MD)
    assert resp.status_code == 200, resp.text
    doc = fitz.open(stream=resp.content, filetype="pdf")
    text = doc[0].get_text()
    assert "Para A" in text and "Para B" in text, text
    assert "hidden build note" not in text, text
