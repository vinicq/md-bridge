"""Integration coverage for the OCR provider against the real Tesseract binary.

The provider contract (#441) is unit-tested with a fake in
tests/unit/test_ocr_provider.py; this tier proves the shipped Tesseract provider
actually produces an extractable text layer and populates the metadata, using
the real binary (no subprocess mock). Skips when Tesseract is not installed.
"""
from __future__ import annotations

import shutil

import pymupdf
import pytest
from app.services.ocr import TesseractOcrProvider

pytest.importorskip("pytesseract")
pytestmark = pytest.mark.skipif(
    shutil.which("tesseract") is None,
    reason="tesseract binary is not installed",
)


def _extract_text(pdf_bytes: bytes) -> str:
    with pymupdf.open(stream=pdf_bytes, filetype="pdf") as doc:
        return "\n".join(page.get_text() for page in doc)


def test_tesseract_provider_returns_searchable_pdf_and_metadata(scanned_pdf_bytes: bytes):
    assert not _extract_text(scanned_pdf_bytes).strip()

    result = TesseractOcrProvider().ocr(scanned_pdf_bytes, lang="eng")

    assert result.provider == "tesseract"
    assert result.lang == "eng"
    assert result.duration_ms >= 0
    assert result.pdf_bytes[:5] == b"%PDF-"
    text = _extract_text(result.pdf_bytes).upper()
    assert "OCR" in text
    assert "BRIDGE" in text
