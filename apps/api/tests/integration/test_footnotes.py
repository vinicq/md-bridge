"""Integration coverage for footnote pairing (#148).

Builds a real PDF with PyMuPDF (no mock): a body in the dominant 11pt font and
three small-font (7pt) definition blocks pinned to the bottom band, each shaped
like `N prose`. With the opt-in flag those blocks leave the body and reappear as
a sorted `[^N]:` tail; by default they stay inline as plain text (the
byte-identical behavior).

PyMuPDF cannot synthesize a real FLAG_SUPERSCRIPT span (insert_text re-reads as
flags=0), so the body-ref -> `[^N]` rewrite is covered cross-platform by the
hand-built superscript spans in tests/unit/test_heuristics.py. Here we exercise
the other half end-to-end: bottom-band detection, body suppression, tail emission.
"""
from __future__ import annotations

import sys

import pymupdf
import pytest
from app.schemas.convert import PdfToMdOptions
from app.services.pdf_to_md import convert_pdf_bytes

DEFS = [
    "1 First footnote explains the first marked term in detail.",
    "2 Second footnote clarifies a different point at length here.",
    "3 Third footnote adds yet another bottom-of-page remark.",
]


def _pdf_with_footnotes() -> bytes:
    doc = pymupdf.open()
    page = doc.new_page(width=612, height=792)
    # Eight body lines at 11pt so that size dominates the histogram; the 7pt
    # footnotes then read as small font, not body.
    y = 90
    for i in range(8):
        page.insert_text(
            (72, y),
            f"Body line {i} with enough ordinary words to dominate the font size histogram clearly.",
            fontsize=11,
        )
        y += 22
    # Bottom-band definitions, spaced apart so each lands in its own block.
    for def_y, text in zip((690, 720, 750), DEFS):
        page.insert_text((72, def_y), text, fontsize=7)
    try:
        return doc.tobytes()
    finally:
        doc.close()


@pytest.mark.skipif(
    sys.platform == "win32",
    reason=(
        "The vendored converter holds the PyMuPDF handle open, which locks the "
        "per-request tempdir on Windows during cleanup. POSIX unlinks open files, "
        "so CI exercises this; the detection predicate and tail renderer are "
        "covered cross-platform by tests/unit/test_heuristics.py."
    ),
)
def test_footnote_blocks_move_to_tail_when_enabled():
    md = convert_pdf_bytes(
        _pdf_with_footnotes(),
        filename="notes.pdf",
        options=PdfToMdOptions(footnote_pairing=True),
    ).md
    assert "[^1]: First footnote explains the first marked term in detail." in md
    assert "[^2]: Second footnote clarifies a different point at length here." in md
    assert "[^3]: Third footnote adds yet another bottom-of-page remark." in md
    # The tail is sorted and sits after the body.
    assert md.index("[^1]:") < md.index("[^2]:") < md.index("[^3]:")
    # The definition no longer appears in the body as a bare `N prose` line.
    assert "\n1 First footnote" not in md


@pytest.mark.skipif(
    sys.platform == "win32",
    reason="Same Windows tempdir-lock constraint as the case above.",
)
def test_footnote_blocks_stay_inline_by_default():
    md = convert_pdf_bytes(_pdf_with_footnotes(), filename="notes.pdf").md
    assert "[^1]:" not in md
    assert "1 First footnote explains the first marked term in detail." in md
