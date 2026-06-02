"""Integration coverage for recurrent header/footer subtraction (#187).

Builds a real multi-page PDF with PyMuPDF (no mock, per the integration rule):
the same running footer on every page plus distinct body text per page. With
the opt-in flag the footer is subtracted; by default it stays. A one-off title
in the band on page one survives either way.
"""
from __future__ import annotations

import sys

import pymupdf
import pytest
from app.schemas.convert import PdfToMdOptions
from app.services.pdf_to_md import convert_pdf_bytes


def _pdf_with_running_footer() -> bytes:
    doc = pymupdf.open()
    n = 4
    for i in range(1, n + 1):
        page = doc.new_page(width=612, height=792)
        if i == 1:
            # A one-off title in the top band on the cover page.
            page.insert_text((72, 40), "Unique Cover Title That Appears Once", fontsize=13)
        page.insert_text((72, 360), f"Distinct body paragraph for page {i} with plenty of real words.", fontsize=11)
        page.insert_text((72, 400), f"A second body line on page {i} keeping the body size dominant here.", fontsize=11)
        # Running footer near the bottom, same text (bar the page number) on each page.
        page.insert_text((72, 760), f"Confidential Report Page {i} of {n}", fontsize=9)
    try:
        return doc.tobytes()
    finally:
        doc.close()


@pytest.mark.skipif(
    sys.platform == "win32",
    reason=(
        "The vendored converter holds the PyMuPDF handle open, which locks the "
        "per-request tempdir on Windows during cleanup. POSIX unlinks open files, "
        "so CI exercises this; the selection logic is covered cross-platform by "
        "tests/unit/test_furniture (via the API loader)."
    ),
)
def test_running_footer_removed_when_flag_on():
    pdf = _pdf_with_running_footer()
    opts = PdfToMdOptions(subtract_running_furniture=True)
    md = convert_pdf_bytes(pdf, filename="report.pdf", options=opts).md

    assert "Confidential Report Page" not in md
    assert "Distinct body paragraph for page 2" in md  # body survives


@pytest.mark.skipif(
    sys.platform == "win32",
    reason="Same Windows tempdir-lock constraint as the case above.",
)
def test_running_footer_kept_by_default():
    pdf = _pdf_with_running_footer()
    md = convert_pdf_bytes(pdf, filename="report.pdf").md

    assert "Confidential Report Page" in md


@pytest.mark.skipif(
    sys.platform == "win32",
    reason="Same Windows tempdir-lock constraint as the cases above.",
)
def test_one_off_band_title_survives_subtraction():
    pdf = _pdf_with_running_footer()
    opts = PdfToMdOptions(subtract_running_furniture=True)
    md = convert_pdf_bytes(pdf, filename="report.pdf", options=opts).md

    # The cover title appears on one page only, so recurrence never removes it.
    assert "Unique Cover Title That Appears Once" in md
