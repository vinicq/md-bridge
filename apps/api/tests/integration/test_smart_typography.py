"""Integration coverage for the smart-typography post-pass (#171).

Runs the real converter over a committed fixture that genuinely contains
Unicode typography. `wikipedia-markdown-en.pdf` (Chromium-rendered, CC BY-SA)
carries five em-dashes and eleven en-dashes in prose, so the dash fold is
exercised on real content, not a synthetic string. A synthetic PyMuPDF page is
not usable here: the base-14 font substitutes curly quotes / em-dash with a
middle dot at insert time, so the glyphs never reach extraction.

This proves the flag propagates from the schema through `convert_pdf_bytes`
to the Markdown, and that the default path preserves the source glyphs. The
per-transform matrix (quotes, ellipsis, code/URL protection, idempotency) is in
tests/unit/test_smart_typography.py.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest
from app.schemas.convert import PdfToMdOptions
from app.services.pdf_to_md import convert_pdf_bytes

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "wikipedia-markdown-en.pdf"

WIN_TEMPDIR_LOCK = pytest.mark.skipif(
    sys.platform == "win32",
    reason=(
        "The vendored converter holds the PyMuPDF handle open, which locks the "
        "per-request tempdir on Windows during cleanup. POSIX unlinks open files, "
        "so CI exercises this; the fold transforms are covered cross-platform by "
        "tests/unit/test_smart_typography.py."
    ),
)

EM_DASH = "—"
EN_DASH = "–"


@WIN_TEMPDIR_LOCK
def test_dashes_preserved_by_default():
    md = convert_pdf_bytes(FIXTURE.read_bytes(), filename="wiki.pdf").md
    # The fixture's prose dashes survive untouched on the default path.
    assert EM_DASH in md or EN_DASH in md


@WIN_TEMPDIR_LOCK
def test_dashes_folded_to_ascii_when_enabled():
    default_md = convert_pdf_bytes(FIXTURE.read_bytes(), filename="wiki.pdf").md
    assert default_md.count(EM_DASH) > 0  # guard against a vacuous fixture
    folded_md = convert_pdf_bytes(
        FIXTURE.read_bytes(),
        filename="wiki.pdf",
        options=PdfToMdOptions(smart_typography_dashes="ascii"),
    ).md
    # Every prose em/en dash folded; none of the fixture's dashes sit in code.
    assert folded_md.count(EM_DASH) == 0
    assert folded_md.count(EN_DASH) == 0
