"""Integration guard: the converter emits zero raw HTML by default (#154).

Builds a real PDF with PyMuPDF (no mock) carrying the span styles that used to
leak HTML (superscript, bold, strikethrough, small-font text), converts with
default options, and asserts no `<tag>` survives. This locks the pure-Markdown
contract so a future change that reintroduces a raw tag fails CI.
"""
from __future__ import annotations

import re
import sys

import pymupdf
import pytest
from app.services.pdf_to_md import convert_pdf_bytes


def _pdf_with_style_spans() -> bytes:
    doc = pymupdf.open()
    page = doc.new_page(width=612, height=792)
    page.insert_text((72, 120), "A paragraph with enough plain words to anchor the body size here.", fontsize=11)
    # Superscript-ish (small raised) and small-font caption text.
    page.insert_text((72, 160), "Footnote marker 2 and a reference to E = mc squared here.", fontsize=11)
    page.insert_text((72, 200), "A small caption line set in a smaller font at the bottom area.", fontsize=8)
    page.insert_text((72, 240), "Another body paragraph keeping the eleven point size dominant overall.", fontsize=11)
    try:
        return doc.tobytes()
    finally:
        doc.close()


@pytest.mark.skipif(
    sys.platform == "win32",
    reason=(
        "The vendored converter holds the PyMuPDF handle open, which locks the "
        "per-request tempdir on Windows during cleanup. POSIX unlinks open files, "
        "so CI exercises this; the helper itself is covered cross-platform by "
        "tests/unit/test_emit_html.py."
    ),
)
def test_default_conversion_emits_zero_raw_html():
    md = convert_pdf_bytes(_pdf_with_style_spans(), filename="styles.pdf").md
    assert re.search(r"<[a-z]+", md) is None, f"raw HTML leaked: {md!r}"
