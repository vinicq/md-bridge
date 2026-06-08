"""Integration coverage for code-fence language detection (#145).

Builds a real PDF with PyMuPDF (no mock, per the integration rule): one
monospace block per language so each is classified as a code block and run
through the full pipeline. Asserts the emitted fence opens with the expected
language tag, proving detect_language is reached with the body intact, not just
that the regex matches in isolation.
"""
from __future__ import annotations

import sys

import pymupdf
import pytest
from app.services.pdf_to_md import convert_pdf_bytes

# (monospace code body, expected fence language)
SAMPLES = [
    ("#!/bin/bash\nset -euo pipefail", "bash"),
    ("FROM python:3.12-slim\nRUN pip install .", "dockerfile"),
    ("package main\nfunc main() {}", "go"),
    ("fn main() {\n    let mut x = 1;\n}", "rust"),
    ("interface User {\n  name: string\n}", "typescript"),
    ("name: build\nversion: 1", "yaml"),
]


def _pdf_with_code_blocks() -> bytes:
    doc = pymupdf.open()
    page = doc.new_page(width=612, height=792)
    y = 80
    for code, _ in SAMPLES:
        # Courier is monospace, so each block clears the mono-ratio code gate;
        # the wide vertical gaps keep every sample as its own PyMuPDF block.
        page.insert_text((72, y), code, fontname="courier", fontsize=10)
        y += 80
    try:
        return doc.tobytes()
    finally:
        doc.close()


@pytest.mark.skipif(
    sys.platform == "win32",
    reason=(
        "The vendored converter holds the PyMuPDF handle open, which locks the "
        "per-request tempdir on Windows during cleanup. POSIX unlinks open files, "
        "so CI exercises this; the detection rules are covered cross-platform by "
        "tests/unit/test_heuristics.py."
    ),
)
def test_each_language_opens_its_fence():
    md = convert_pdf_bytes(_pdf_with_code_blocks(), filename="snippets.pdf").md
    # A check always runs, even if SAMPLES were ever emptied: the loop alone
    # would pass vacuously otherwise. The per-language fences below are the real
    # oracle; this is the anti-vacuous guard, not a weak terminal assert.
    assert md, "conversion produced no markdown"  # falsegreen: ignore[C6]
    for _, lang in SAMPLES:
        assert f"```{lang}" in md, f"expected a ```{lang} fence in:\n{md}"
