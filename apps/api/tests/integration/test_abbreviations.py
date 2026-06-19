"""Integration coverage for abbreviation-glossary extraction (#163).

Builds real PDFs with PyMuPDF (no mock) for the two glossary layouts seen in
the wild: a side-by-side two-column list, and a one-line-per-entry list with
the abbreviation as the leading token. With the opt-in flag the converter emits
a sorted `*[TOKEN]: expansion` tail (consumed by the markdown-to-pdf renderer's
`abbr` extension); by default it emits nothing and the output is unchanged.

The glossary coordinates mirror a real thesis page (TESE Elvys Alves Soares,
abbreviation page: left column x~90, right column x~193, body 12pt).

Re-rendering to assert `<abbr title>` is the markdown-to-pdf package's contract,
not this one's, so the assertions stop at the emitted Markdown tail.
"""
from __future__ import annotations

import sys

import pymupdf
import pytest

from app.schemas.convert import PdfToMdOptions
from app.services.pdf_to_md import convert_pdf_bytes

WIN_TEMPDIR_LOCK = pytest.mark.skipif(
    sys.platform == "win32",
    reason=(
        "The vendored converter holds the PyMuPDF handle open, which locks the "
        "per-request tempdir on Windows during cleanup. POSIX unlinks open files, "
        "so CI exercises this; the pairing and tail logic are covered "
        "cross-platform by tests/unit/test_abbreviations.py."
    ),
)

TWO_COLUMN_ROWS = [
    ("GQM", "Goal Question Metric"),
    ("MLM", "Multivocal Literature Mapping"),
    ("NLP", "Natural Language Processing"),
]
INLINE_ROWS = [
    "AR Assertion Roulette",
    "AST Abstract Syntax Tree",
    "CLI Command Line Interface",
]


def _two_column_pdf(heading: str = "List of Abbreviations and Acronyms") -> bytes:
    doc = pymupdf.open()
    page = doc.new_page(width=595, height=842)
    page.insert_text((90, 90), heading, fontsize=14)
    y = 140
    for token, expansion in TWO_COLUMN_ROWS:
        page.insert_text((90, y), token, fontsize=12)
        page.insert_text((193, y), expansion, fontsize=12)
        y += 26
    try:
        return doc.tobytes()
    finally:
        doc.close()


def _inline_pdf() -> bytes:
    doc = pymupdf.open()
    page = doc.new_page(width=595, height=842)
    page.insert_text((85, 90), "Lista de Siglas e Acrônimos", fontsize=14)
    y = 140
    for line in INLINE_ROWS:
        page.insert_text((85, y), line, fontsize=12)
        y += 26
    try:
        return doc.tobytes()
    finally:
        doc.close()


@WIN_TEMPDIR_LOCK
def test_two_column_glossary_emits_tail_when_enabled():
    md = convert_pdf_bytes(
        _two_column_pdf(),
        filename="abbr.pdf",
        options=PdfToMdOptions(extract_abbreviations=True),
    ).md
    expected = [f"*[{token}]: {expansion}" for token, expansion in TWO_COLUMN_ROWS]
    missing = [line for line in expected if line not in md]
    assert missing == []
    # The tail is sorted by token and sits at the document end.
    assert md.index("*[GQM]:") < md.index("*[MLM]:") < md.index("*[NLP]:")


@WIN_TEMPDIR_LOCK
def test_inline_glossary_emits_tail_when_enabled():
    md = convert_pdf_bytes(
        _inline_pdf(),
        filename="abbr.pdf",
        options=PdfToMdOptions(extract_abbreviations=True),
    ).md
    assert "*[AR]: Assertion Roulette" in md
    assert "*[AST]: Abstract Syntax Tree" in md
    assert "*[CLI]: Command Line Interface" in md


@WIN_TEMPDIR_LOCK
def test_no_tail_by_default():
    md = convert_pdf_bytes(_two_column_pdf(), filename="abbr.pdf").md
    assert "*[" not in md  # byte-identical default: nothing emitted
    # The glossary text still rendered inline somewhere in the body.
    assert "Goal Question Metric" in md


@WIN_TEMPDIR_LOCK
def test_glossary_heading_word_not_in_term_set_does_not_trigger():
    # "Glossary" is a prose definition list, not an abbreviation table; the
    # same rows under that heading must not be picked up.
    md = convert_pdf_bytes(
        _two_column_pdf(heading="Glossary"),
        filename="abbr.pdf",
        options=PdfToMdOptions(extract_abbreviations=True),
    ).md
    assert "*[" not in md
