"""Integration coverage for hard line breaks from PDF layout (#156).

Builds a real PDF with PyMuPDF (no mock): a short same-font, same-indent stanza
that should keep its line breaks, and a long wrapped paragraph that should not.
With the opt-in flag the stanza emits CommonMark hard breaks; by default it
collapses to one line (the byte-identical behavior).
"""
from __future__ import annotations

import sys

import pymupdf
import pytest
from app.schemas.convert import PdfToMdOptions
from app.services.pdf_to_md import convert_pdf_bytes

STANZA = ["Roses are red", "Violets are blue", "Sugar is sweet", "So are you too"]


def _pdf_with_stanza() -> bytes:
    doc = pymupdf.open()
    page = doc.new_page(width=612, height=792)
    # Tight 14pt leading keeps the four short lines in one PyMuPDF block.
    y = 120
    for line in STANZA:
        page.insert_text((72, y), line, fontsize=11)
        y += 14
    # A long wrapped paragraph well below, far enough to be its own block.
    page.insert_text(
        (72, 320),
        "This is an ordinary running paragraph that the converter wraps across the page "
        "and should join back into a single line without any hard breaks at all here.",
        fontsize=11,
    )
    try:
        return doc.tobytes()
    finally:
        doc.close()


@pytest.mark.skipif(
    sys.platform == "win32",
    reason=(
        "The vendored converter holds the PyMuPDF handle open, which locks the "
        "per-request tempdir on Windows during cleanup. POSIX unlinks open files, "
        "so CI exercises this; the break predicate is covered cross-platform by "
        "tests/unit/test_heuristics.py."
    ),
)
def test_stanza_keeps_hard_breaks_when_enabled():
    md = convert_pdf_bytes(
        _pdf_with_stanza(), filename="poem.pdf", options=PdfToMdOptions(preserve_line_breaks=True)
    ).md
    assert "  \n" in md
    for line in STANZA:
        assert line in md


@pytest.mark.skipif(
    sys.platform == "win32",
    reason="Same Windows tempdir-lock constraint as the case above.",
)
def test_stanza_collapses_by_default():
    md = convert_pdf_bytes(_pdf_with_stanza(), filename="poem.pdf").md
    assert "  \n" not in md
