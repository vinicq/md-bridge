from __future__ import annotations

import shutil

import pymupdf
import pytest
from app.services.ocr import ocr_pdf_bytes

pytest.importorskip("pytesseract")
pytestmark = pytest.mark.skipif(
    shutil.which("tesseract") is None,
    reason="tesseract binary is not installed",
)


def _extract_text(pdf_bytes: bytes) -> str:
    with pymupdf.open(stream=pdf_bytes, filetype="pdf") as doc:
        return "\n".join(page.get_text() for page in doc)


def test_ocr_pdf_bytes_adds_extractable_text(scanned_pdf_bytes: bytes):
    assert not _extract_text(scanned_pdf_bytes).strip()

    ocr_pdf = ocr_pdf_bytes(scanned_pdf_bytes, lang="eng")
    text = _extract_text(ocr_pdf).upper()

    assert "OCR" in text
    assert "BRIDGE" in text
