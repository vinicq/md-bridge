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
    # Place text in the body area (y=120, not near the footer zone at ~760).
    # fontsize=11 and explicit fontname="helv" match the body-text pattern used
    # by other integration fixtures, ensuring classify_block sees "paragraph"
    # rather than "code" or a footer-skipped block on any OS.
    page.insert_text((72, 120), text, fontsize=11, fontname="helv")
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


@pytest.mark.skipif(
    sys.platform == "win32",
    reason=(
        "The vendored converter holds the PyMuPDF handle open, which locks the "
        "per-request tempdir on Windows during cleanup. POSIX unlinks open files, "
        "so CI exercises this; the line-start escaping itself is covered "
        "cross-platform by tests/unit/test_render_span_escaping.py."
    ),
)
def test_line_start_special_survives_round_trip():
    # #192: a literal paragraph that begins with `#` must not parse as a heading
    # after conversion. The single span carries no line position, so this is the
    # line-level escape pass, not the span pass.
    pdf = _pdf_with("# this is prose, not a heading")
    md = convert_pdf_bytes(pdf, filename="linestart.pdf").md
    html = markdown.markdown(md)

    assert "<h1>" not in html
    # The hash stays in the rendered text as a literal character.
    assert "# this is prose, not a heading" in html
