"""Integration coverage for blockquote detection (#147).

Builds a real PDF with PyMuPDF (no mock, per the integration rule): two body
paragraphs at the left margin, an inset pull-quote line, then body text again.
The quote sits past the body margin by more than one indent unit, so with the
opt-in flag the converter fences it as a CommonMark blockquote. With the flag
off (the default) the same block stays an ordinary paragraph, which is the
end-to-end guard that the feature ships dormant.

Plain ASCII text is used so it survives PyMuPDF's default Base-14 font, and each
line clears the OCR auto-trigger threshold (40 chars/page).
"""
from __future__ import annotations

import sys

import markdown
import pymupdf
import pytest
from app.schemas.convert import PdfToMdOptions
from app.services.pdf_to_md import convert_pdf_bytes


def _pdf_with_pull_quote() -> bytes:
    doc = pymupdf.open()
    page = doc.new_page(width=612, height=792)
    # Body paragraphs anchor body_x0 at 72; the quote at x=110 is inset past
    # the 90pt threshold (body_x0 72 + indent_unit 18).
    page.insert_text((72, 120), "Regular body text introducing the topic at the left margin.", fontsize=11)
    page.insert_text((72, 170), "A second ordinary paragraph also anchored at the body margin.", fontsize=11)
    page.insert_text((110, 240), "This is a quoted passage standing apart from the body text.", fontsize=11)
    page.insert_text((72, 320), "Body text resumes after the quote back at the left margin.", fontsize=11)
    try:
        return doc.tobytes()
    finally:
        doc.close()


@pytest.mark.skipif(
    sys.platform == "win32",
    reason=(
        "The vendored converter holds the PyMuPDF handle open, which locks the "
        "per-request tempdir on Windows during cleanup. POSIX unlinks open files, "
        "so CI exercises this; the classification and assembly logic is covered "
        "cross-platform by tests/unit/test_heuristics.py and "
        "apps/api/tests/unit/test_blockquote.py."
    ),
)
def test_pull_quote_renders_as_blockquote_when_enabled():
    pdf = _pdf_with_pull_quote()
    opts = PdfToMdOptions(detect_blockquotes=True)
    md = convert_pdf_bytes(pdf, filename="quote.pdf", options=opts).md
    html = markdown.markdown(md)

    assert "<blockquote>" in html
    assert "quoted passage standing apart" in html


@pytest.mark.skipif(
    sys.platform == "win32",
    reason="Same Windows tempdir-lock constraint as the enabled case above.",
)
def test_pull_quote_stays_paragraph_by_default():
    pdf = _pdf_with_pull_quote()
    md = convert_pdf_bytes(pdf, filename="quote.pdf").md
    html = markdown.markdown(md)

    assert ">" not in md
    assert "<blockquote>" not in html
    assert "quoted passage standing apart" in md


def _pdf_with_three_paragraph_quote() -> bytes:
    doc = pymupdf.open()
    page = doc.new_page(width=612, height=792)
    # Four body paragraphs at x=72 keep body_x0 anchored at the margin; the
    # three quote paragraphs at x=110 are inset past the 90pt threshold. Wide
    # vertical gaps keep every line as its own PyMuPDF block.
    page.insert_text((72, 90), "Body text introducing the long quotation that follows here.", fontsize=11)
    page.insert_text((72, 130), "More body text setting up the quoted passage just below now.", fontsize=11)
    page.insert_text((110, 200), "First paragraph of the quoted passage taken from the book.", fontsize=11)
    page.insert_text((110, 270), "Second paragraph continuing that same quoted passage onward.", fontsize=11)
    page.insert_text((110, 340), "Third and final paragraph closing the quoted passage here.", fontsize=11)
    page.insert_text((72, 410), "Body text resumes after the quotation back at the left margin.", fontsize=11)
    page.insert_text((72, 450), "A closing body paragraph anchoring the body margin firmly now.", fontsize=11)
    try:
        return doc.tobytes()
    finally:
        doc.close()


@pytest.mark.skipif(
    sys.platform == "win32",
    reason="Same Windows tempdir-lock constraint as the cases above.",
)
def test_three_paragraph_quote_renders_as_one_blockquote():
    pdf = _pdf_with_three_paragraph_quote()
    opts = PdfToMdOptions(detect_blockquotes=True)
    md = convert_pdf_bytes(pdf, filename="quote3.pdf", options=opts).md
    html = markdown.markdown(md)

    # One blockquote (#174), three paragraphs inside it, not three quotes.
    assert html.count("<blockquote>") == 1
    quote = html.split("<blockquote>")[1].split("</blockquote>")[0]
    assert quote.count("<p>") == 3


@pytest.mark.skipif(
    sys.platform == "win32",
    reason="Same Windows tempdir-lock constraint as the cases above.",
)
def test_three_paragraph_quote_stays_paragraphs_by_default():
    pdf = _pdf_with_three_paragraph_quote()
    md = convert_pdf_bytes(pdf, filename="quote3.pdf").md
    html = markdown.markdown(md)

    assert ">" not in md
    assert "<blockquote>" not in html
