"""Integration coverage for PDF text-highlight annotations -> ==mark== (#162).

Builds a real PDF with PyMuPDF (no mock, per the integration rule): a line of
text with a highlight annotation over the first words. With extract_highlights
on, the converter reads the annotation geometry, finds the glyphs under it, and
emits pymdownx-mark ==...==. Off (the default) the output stays byte-identical,
so the annotation is ignored. The wrapping logic itself is covered
cross-platform by tests/unit/test_render_span_escaping.py.
"""
from __future__ import annotations

import sys

import pymupdf
import pytest
from app.schemas.convert import PdfToMdOptions
from app.services.pdf_to_md import convert_pdf_bytes


def _pdf_with_highlight() -> bytes:
    doc = pymupdf.open()
    page = doc.new_page(width=612, height=792)
    page.insert_text((72, 200), "This important clause deserves attention.", fontsize=13)
    # A highlight over the whole sentence, which is how a PDF stores a text
    # highlight the user drew across the line (rect ~ the line's glyph band).
    page.add_highlight_annot(pymupdf.Rect(70, 188, 312, 203))
    try:
        return doc.tobytes()
    finally:
        doc.close()


_WIN_SKIP = pytest.mark.skipif(
    sys.platform == "win32",
    reason=(
        "The vendored converter holds the PyMuPDF handle open, which locks the "
        "per-request tempdir on Windows during cleanup. POSIX unlinks open files, "
        "so CI exercises this; the wrapping logic is covered cross-platform by "
        "tests/unit/test_render_span_escaping.py."
    ),
)


@_WIN_SKIP
def test_highlight_emits_mark_when_enabled():
    pdf = _pdf_with_highlight()
    md = convert_pdf_bytes(
        pdf, filename="hl.pdf", options=PdfToMdOptions(extract_highlights=True)
    ).md
    assert "==" in md, f"expected ==mark== in output, got: {md!r}"
    assert "important" in md


@_WIN_SKIP
def test_highlight_ignored_by_default():
    # Default off: the annotation is not read, so no ==...== leaks into output.
    pdf = _pdf_with_highlight()
    md = convert_pdf_bytes(pdf, filename="hl.pdf").md
    assert "==" not in md, f"highlight should be ignored by default, got: {md!r}"
    assert "important" in md
