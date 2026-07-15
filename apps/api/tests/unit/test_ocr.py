"""Unit coverage for the OCR pre-pass timeout handling (#364)."""
from __future__ import annotations

import pymupdf
import pytest
from app.errors import ApiError
from app.services import ocr

pytest.importorskip("pytesseract")
pytest.importorskip("PIL")


def _one_page_pdf() -> bytes:
    doc = pymupdf.open()
    try:
        doc.new_page(width=200, height=200)
        return doc.tobytes()
    finally:
        doc.close()


def test_page_timeout_maps_to_ocr_failed_naming_the_page(monkeypatch):
    # pytesseract raises RuntimeError when it kills a run past the timeout.
    # ocr_pdf_bytes must translate that into ocr_failed and name the page,
    # not let the request hang or surface a code-less 500.
    import pytesseract

    captured: dict = {}

    def _timeout(*args, **kwargs):
        captured.update(kwargs)
        raise RuntimeError("Tesseract process timeout")

    monkeypatch.setattr(pytesseract, "image_to_pdf_or_hocr", _timeout)
    monkeypatch.delenv("MD_BRIDGE_OCR_PAGE_TIMEOUT", raising=False)

    with pytest.raises(ApiError) as excinfo:
        ocr.ocr_pdf_bytes(_one_page_pdf(), lang="eng")

    err = excinfo.value
    assert err.status_code == 500
    assert err.code == "ocr_failed"
    assert "page 1" in err.message
    # Every Tesseract call must carry an explicit timeout.
    assert captured.get("timeout") == ocr.DEFAULT_OCR_PAGE_TIMEOUT


def test_page_timeout_env_override(monkeypatch):
    monkeypatch.setenv("MD_BRIDGE_OCR_PAGE_TIMEOUT", "5")
    assert ocr.get_page_timeout() == 5
    # A non-positive or malformed value falls back to the default.
    monkeypatch.setenv("MD_BRIDGE_OCR_PAGE_TIMEOUT", "0")
    assert ocr.get_page_timeout() == ocr.DEFAULT_OCR_PAGE_TIMEOUT
    monkeypatch.setenv("MD_BRIDGE_OCR_PAGE_TIMEOUT", "abc")
    assert ocr.get_page_timeout() == ocr.DEFAULT_OCR_PAGE_TIMEOUT
