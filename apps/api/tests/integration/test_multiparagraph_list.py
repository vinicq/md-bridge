"""Integration coverage for #167: a list item that spans two paragraphs in the
PDF stays one list item in the Markdown.

Builds a real PDF with PyMuPDF (no mock, per the integration rule): a numbered
item, a paragraph indented past the marker, then a second numbered item. The
three land as separate text blocks. Without the continuation tracker the middle
paragraph escapes to top level and splits the list in two. The test re-parses
the emitted Markdown with the same `markdown` library shipped in the API and
asserts the continuation renders as a second <p> inside the first <li>.

A numbered list is used rather than a bulleted one because `1.`/`2.` are ASCII
and survive PyMuPDF's default Base-14 font, whereas the `•` glyph (U+2022) is
outside Helvetica and renders as a replacement char. The bulleted path is
covered cross-platform by tests/unit/test_list_continuation.py.
"""
from __future__ import annotations

import sys

import markdown
import pymupdf
import pytest
from app.services.pdf_to_md import convert_pdf_bytes


def _pdf_with_multiparagraph_item() -> bytes:
    doc = pymupdf.open()
    page = doc.new_page(width=612, height=792)
    # Increasing y stacks the lines top-to-bottom; the gaps keep them as three
    # distinct blocks, and the middle line is indented past the marker so it
    # reads as a continuation of the first item.
    page.insert_text((72, 600), "1. First step here in the procedure.", fontsize=12)
    page.insert_text((100, 640), "Detail paragraph still part of the first step.", fontsize=12)
    page.insert_text((72, 680), "2. Second step here in the procedure.", fontsize=12)
    try:
        return doc.tobytes()
    finally:
        doc.close()


@pytest.mark.skipif(
    sys.platform == "win32",
    reason=(
        "The vendored converter holds the PyMuPDF handle open, which locks the "
        "per-request tempdir on Windows during cleanup. POSIX unlinks open files, "
        "so CI exercises this; the assembly logic itself is covered cross-platform "
        "by tests/unit/test_list_continuation.py."
    ),
)
def test_multiparagraph_list_item_survives_round_trip():
    pdf = _pdf_with_multiparagraph_item()
    md = convert_pdf_bytes(pdf, filename="multiparagraph.pdf").md
    html = markdown.markdown(md)

    # One list, two items: the continuation did not split the list in two.
    assert html.count("<ol>") == 1
    assert html.count("<li>") == 2
    # The continuation nests inside the first item rather than floating between
    # the two lists as a top-level paragraph.
    first_item = html.split("</li>")[0]
    assert "Detail paragraph still part of the first step." in first_item
