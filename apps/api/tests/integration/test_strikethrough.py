"""Integration coverage for GFM strikethrough detection (#142).

Builds a real PDF with PyMuPDF (no mock, per the integration rule): a line of
text with a stroke drawn through part of it, which is how PDFs encode
strikethrough. The converter reads the page with style collection, so PyMuPDF
correlates the drawn line with the glyphs and flags the span; the converter
emits GFM `~~...~~`. The detection mechanism itself is covered cross-platform
by tests/unit/test_render_span_escaping.py.
"""
from __future__ import annotations

import sys

import pymupdf
import pytest
from app.services.pdf_to_md import convert_pdf_bytes


def _pdf_with_strikethrough() -> bytes:
    doc = pymupdf.open()
    page = doc.new_page(width=612, height=792)
    page.insert_text((72, 200), "This deleted clause stays in the source.", fontsize=13)
    # A stroke through the first words is how a PDF renders strikethrough.
    page.draw_line((72, 196), (150, 196), width=1.2)
    try:
        return doc.tobytes()
    finally:
        doc.close()


@pytest.mark.skipif(
    sys.platform == "win32",
    reason=(
        "The vendored converter holds the PyMuPDF handle open, which locks the "
        "per-request tempdir on Windows during cleanup. POSIX unlinks open files, "
        "so CI exercises this; the detection logic is covered cross-platform by "
        "tests/unit/test_render_span_escaping.py."
    ),
)
def test_strikethrough_round_trips_to_gfm_tildes():
    pdf = _pdf_with_strikethrough()
    md = convert_pdf_bytes(pdf, filename="strike.pdf").md
    assert "~~" in md, f"expected GFM strikethrough in output, got: {md!r}"
