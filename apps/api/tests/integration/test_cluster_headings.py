"""Integration coverage for heading-size clustering and multi-line merge (#188).

Builds a real PDF with PyMuPDF (no mock, per the integration rule): body text
to anchor the body size, then a heading that wraps across two consecutive
blocks at the same large size. With the opt-in flag the converter rejoins them
into one heading; by default they stay as separate headings.

ASCII text so it survives PyMuPDF's default Base-14 font; each line clears the
OCR auto-trigger threshold.
"""
from __future__ import annotations

import sys

import markdown
import pymupdf
import pytest
from app.schemas.convert import PdfToMdOptions
from app.services.pdf_to_md import convert_pdf_bytes


def _pdf_with_split_heading() -> bytes:
    doc = pymupdf.open()
    page = doc.new_page(width=612, height=792)
    # Body paragraphs anchor the body size at 11pt.
    page.insert_text((72, 110), "Body paragraph one with enough words to anchor the body size firmly.", fontsize=11)
    page.insert_text((72, 150), "Body paragraph two also at the left margin with plenty of words here.", fontsize=11)
    page.insert_text((72, 190), "Body paragraph three keeping eleven point the most common size around.", fontsize=11)
    # A heading wrapped across two consecutive blocks at the same large size.
    page.insert_text((72, 260), "Test Analysis and Design", fontsize=18)
    page.insert_text((72, 300), "Techniques for Practitioners", fontsize=18)
    page.insert_text((72, 360), "Body text after the heading to close the run cleanly at the margin.", fontsize=11)
    try:
        return doc.tobytes()
    finally:
        doc.close()


@pytest.mark.skipif(
    sys.platform == "win32",
    reason=(
        "The vendored converter holds the PyMuPDF handle open, which locks the "
        "per-request tempdir on Windows during cleanup. POSIX unlinks open files, "
        "so CI exercises this; the clustering and merge logic is covered "
        "cross-platform by tests/unit/test_heuristics.py."
    ),
)
def test_split_heading_merges_when_clustering_on():
    pdf = _pdf_with_split_heading()
    opts = PdfToMdOptions(cluster_headings=True)
    md = convert_pdf_bytes(pdf, filename="heading.pdf", options=opts).md
    html = markdown.markdown(md)

    assert "<h1>Test Analysis and Design Techniques for Practitioners</h1>" in html


@pytest.mark.skipif(
    sys.platform == "win32",
    reason="Same Windows tempdir-lock constraint as the case above.",
)
def test_split_heading_stays_split_by_default():
    pdf = _pdf_with_split_heading()
    md = convert_pdf_bytes(pdf, filename="heading.pdf").md
    html = markdown.markdown(md)

    # Without clustering, the two heading blocks emit independently.
    assert html.count("<h1>") >= 2


def _pdf_with_six_heading_sizes() -> bytes:
    doc = pymupdf.open()
    page = doc.new_page(width=612, height=792)
    # Body at 11pt (dominant), then six distinct heading sizes with clear gaps.
    for i, y in enumerate(range(80, 200, 20)):
        page.insert_text((72, y), f"Body paragraph {i} with enough real words to anchor the size.", fontsize=11)
    headings = [("Heading one", 34), ("Heading two", 28), ("Heading three", 24),
                ("Heading four", 20), ("Heading five", 17), ("Heading six", 14)]
    y = 240
    for text, size in headings:
        page.insert_text((72, y), text, fontsize=size)
        y += 50
    try:
        return doc.tobytes()
    finally:
        doc.close()


@pytest.mark.skipif(
    sys.platform == "win32",
    reason="Same Windows tempdir-lock constraint as the cases above.",
)
def test_six_level_headings_with_max_six():
    pdf = _pdf_with_six_heading_sizes()
    opts = PdfToMdOptions(cluster_headings=True, max_heading_level=6)
    md = convert_pdf_bytes(pdf, filename="levels.pdf", options=opts).md
    html = markdown.markdown(md)
    assert "<h4>" in html
    assert "<h5>" in html
    assert "<h6>" in html


@pytest.mark.skipif(
    sys.platform == "win32",
    reason="Same Windows tempdir-lock constraint as the cases above.",
)
def test_deep_levels_capped_at_three_by_default():
    pdf = _pdf_with_six_heading_sizes()
    opts = PdfToMdOptions(cluster_headings=True)  # default max_heading_level=3
    md = convert_pdf_bytes(pdf, filename="levels.pdf", options=opts).md
    html = markdown.markdown(md)
    assert "<h4>" not in html
