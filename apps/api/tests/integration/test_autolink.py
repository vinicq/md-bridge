"""Integration coverage for bare-URL/email autolinking (#157).

Builds a real PDF with PyMuPDF (no mock): a body line with a bare URL and one
with a bare email. With the opt-in flags both gain CommonMark autolinks; by
default they stay plain text (the byte-identical behavior). The pure pass is
covered cross-platform by tests/unit/test_convert_links.py.
"""
from __future__ import annotations

import sys

import pymupdf
import pytest
from app.schemas.convert import PdfToMdOptions
from app.services.pdf_to_md import convert_pdf_bytes


def _pdf_with_links() -> bytes:
    doc = pymupdf.open()
    page = doc.new_page(width=612, height=792)
    page.insert_text((72, 120), "Visit https://example.com for details", fontsize=11)
    page.insert_text((72, 160), "Write to team@example.com anytime", fontsize=11)
    try:
        return doc.tobytes()
    finally:
        doc.close()


@pytest.mark.skipif(
    sys.platform == "win32",
    reason=(
        "The vendored converter holds the PyMuPDF handle open, which locks the "
        "per-request tempdir on Windows during cleanup. POSIX unlinks open files, "
        "so CI exercises this; the autolink pass is covered cross-platform by "
        "tests/unit/test_convert_links.py."
    ),
)
def test_autolinks_when_enabled():
    md = convert_pdf_bytes(
        _pdf_with_links(),
        filename="links.pdf",
        options=PdfToMdOptions(autolink_urls=True, autolink_emails=True),
    ).md
    assert "<https://example.com>" in md
    assert "<team@example.com>" in md


@pytest.mark.skipif(
    sys.platform == "win32",
    reason="Same Windows tempdir-lock constraint as the case above.",
)
def test_plain_text_by_default():
    md = convert_pdf_bytes(_pdf_with_links(), filename="links.pdf").md
    assert "<https://example.com>" not in md
    assert "https://example.com" in md
