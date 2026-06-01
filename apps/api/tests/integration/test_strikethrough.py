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


def _pdf_with_full_width_rule_over_text() -> bytes:
    doc = pymupdf.open()
    page = doc.new_page(width=420, height=300)
    page.insert_text((50, 160), "a section divider follows this line", fontsize=15)
    # A full-width rule that overlaps the text at mid-height. mupdf sets the
    # strikeout char_flag for it, but it is page furniture, not a strike.
    page.draw_line((20, 155), (400, 155), width=1)
    try:
        return doc.tobytes()
    finally:
        doc.close()


@pytest.mark.skipif(
    sys.platform == "win32",
    reason=(
        "The vendored converter holds the PyMuPDF handle open, which locks the "
        "per-request tempdir on Windows during cleanup. POSIX unlinks open files, "
        "so CI exercises this; the geometry logic is covered cross-platform by "
        "tests/unit/test_render_span_escaping.py."
    ),
)
def test_full_width_rule_is_not_read_as_strikethrough():
    # #202: a page rule crossing text overruns the span toward the margins, so
    # the geometry cross-check clears the strikeout flag — no spurious ~~.
    pdf = _pdf_with_full_width_rule_over_text()
    md = convert_pdf_bytes(pdf, filename="rule.pdf").md
    assert "~~" not in md, f"a full-width rule was misread as strikethrough: {md!r}"
    assert "section divider follows" in md


def _pdf_with_thin_rect_rule_over_text() -> bytes:
    doc = pymupdf.open()
    page = doc.new_page(width=420, height=300)
    page.insert_text((50, 160), "divider drawn as a thin rectangle", fontsize=15)
    # Some PDFs draw a rule as a thin filled rectangle rather than a line.
    page.draw_rect(pymupdf.Rect(20, 154, 400, 157), fill=(0, 0, 0), color=(0, 0, 0))
    try:
        return doc.tobytes()
    finally:
        doc.close()


@pytest.mark.skipif(
    sys.platform == "win32",
    reason=(
        "The vendored converter holds the PyMuPDF handle open, which locks the "
        "per-request tempdir on Windows during cleanup. POSIX unlinks open files, "
        "so CI exercises this; the geometry logic is covered cross-platform by "
        "tests/unit/test_render_span_escaping.py."
    ),
)
def test_thin_rect_rule_is_not_read_as_strikethrough():
    # #202: a rule drawn as a thin filled rectangle (not a line) is also caught
    # by the geometry cross-check and does not produce a spurious strike.
    pdf = _pdf_with_thin_rect_rule_over_text()
    md = convert_pdf_bytes(pdf, filename="rect-rule.pdf").md
    assert "~~" not in md, f"a thin-rect rule was misread as strikethrough: {md!r}"
    assert "thin rectangle" in md
