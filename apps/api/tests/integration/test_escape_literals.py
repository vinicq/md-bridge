"""Integration coverage for #155: literal Markdown punctuation in PDF prose
survives conversion as plain text.

Builds a real PDF with PyMuPDF (no mock, per the integration rule), runs the
real conversion pipeline, then re-parses the emitted Markdown with the same
`markdown` library shipped in the API. Without the escape pass `*stars*` and
`_unders_` would turn into emphasis; the test asserts they stay literal.
"""
from __future__ import annotations

import sys

import markdown
import pymupdf
import pytest
from app.services.pdf_to_md import convert_pdf_bytes


def _pdf_with(text: str) -> bytes:
    doc = pymupdf.open()
    page = doc.new_page(width=612, height=792)
    page.insert_text((72, 720), text, fontsize=12)
    try:
        return doc.tobytes()
    finally:
        doc.close()


@pytest.mark.skipif(
    sys.platform == "win32",
    reason=(
        "The vendored converter holds the PyMuPDF handle open, which locks the "
        "per-request tempdir on Windows during cleanup. POSIX unlinks open files, "
        "so CI exercises this; the escaping logic itself is covered cross-platform "
        "by tests/unit/test_render_span_escaping.py."
    ),
)
def test_literal_punctuation_survives_round_trip():
    pdf = _pdf_with("Note: use *stars* and _unders_ and [brackets] literally.")
    md = convert_pdf_bytes(pdf, filename="literals.pdf").md
    html = markdown.markdown(md)

    # The punctuation would otherwise have become emphasis or a link.
    assert "<em>" not in html
    assert "<a " not in html  # the brackets did not get synthesized into a link
    assert "*stars*" in html
    assert "_unders_" in html
    assert "[brackets]" in html
