"""Unit coverage for the interchangeable OCR provider contract (#441).

These run without an installed OCR binary: selection, the metadata shape, and
the unavailable-provider error are exercised through a fake provider and the
real resolver, so the seam is tested, not bypassed.
"""
from __future__ import annotations

import pymupdf
import pytest
from app.errors import ApiError
from app.services import ocr


def _one_page_pdf() -> bytes:
    doc = pymupdf.open()
    try:
        doc.new_page(width=200, height=200)
        return doc.tobytes()
    finally:
        doc.close()


class _FakeProvider:
    name = "fake"

    def available(self) -> bool:
        return True

    def ocr(self, pdf_bytes: bytes, *, lang: str) -> ocr.OcrResult:
        return ocr.OcrResult(
            pdf_bytes=pdf_bytes,
            provider=self.name,
            lang=lang,
            duration_ms=0,
            warnings=["degraded: fake engine"],
        )


def test_env_selects_the_provider(monkeypatch):
    monkeypatch.setitem(ocr._PROVIDERS, "fake", _FakeProvider)
    monkeypatch.setenv("MD_BRIDGE_OCR_PROVIDER", "fake")
    provider = ocr.resolve_ocr_provider()
    assert isinstance(provider, _FakeProvider)
    assert provider.name == "fake"


def test_default_provider_is_tesseract(monkeypatch):
    monkeypatch.delenv("MD_BRIDGE_OCR_PROVIDER", raising=False)
    monkeypatch.setattr(ocr, "ocr_stack_available", lambda: True)
    provider = ocr.resolve_ocr_provider()
    assert isinstance(provider, ocr.TesseractOcrProvider)
    assert provider.name == "tesseract"


def test_result_shape_carries_metadata_not_content(monkeypatch):
    # The provider result surfaces provider/lang/duration/warnings and holds no
    # text or filename field, so it cannot leak document content downstream.
    result = _FakeProvider().ocr(_one_page_pdf(), lang="eng+por")
    assert result.provider == "fake"
    assert result.lang == "eng+por"
    assert result.duration_ms >= 0
    assert result.warnings == ["degraded: fake engine"]
    assert result.pdf_bytes[:5] == b"%PDF-"
    assert not hasattr(result, "text")


def test_unknown_provider_raises_typed_error(monkeypatch):
    monkeypatch.setenv("MD_BRIDGE_OCR_PROVIDER", "no-such-engine")
    with pytest.raises(ApiError) as excinfo:
        ocr.resolve_ocr_provider()
    assert excinfo.value.status_code == 503
    assert excinfo.value.code == "ocr_provider_unavailable"


def test_selected_provider_with_missing_stack_raises_not_fallback(monkeypatch):
    # An explicitly selected provider whose stack is absent is a typed error, not
    # a silent switch to another engine.
    monkeypatch.setenv("MD_BRIDGE_OCR_PROVIDER", "tesseract")
    monkeypatch.setattr(ocr, "ocr_stack_available", lambda: False)
    with pytest.raises(ApiError) as excinfo:
        ocr.resolve_ocr_provider()
    assert excinfo.value.status_code == 503
    assert excinfo.value.code == "ocr_provider_unavailable"
