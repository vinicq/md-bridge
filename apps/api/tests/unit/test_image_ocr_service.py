"""Unit coverage for the per-image OCR service (#140).

`is_candidate` runs on Pillow alone (no subprocess) and the Tesseract error
handling is exercised by mocking only the pytesseract binding, so both run
without the Tesseract binary and without a skip on Windows. This is the
coverage the real-Tesseract integration test cannot give (it is skipped
wherever the binary is absent), so the chain is proven on every platform.
"""
from __future__ import annotations

import io

import pytest

pytest.importorskip("PIL.Image")
pytesseract = pytest.importorskip("pytesseract")

from app.services.ocr import ImageOcrProcessor  # noqa: E402


def _png(image) -> bytes:
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def _uniform_png() -> bytes:
    """A flat white fill: no text, but `all` skips content filtering entirely."""
    from PIL import Image

    return _png(Image.new("RGB", (400, 200), "white"))


def _cmyk_jpg() -> bytes:
    """A CMYK JPEG, the print-oriented colorspace the OCR path cannot read yet."""
    from PIL import Image

    buffer = io.BytesIO()
    Image.new("CMYK", (400, 200), (0, 0, 0, 0)).save(buffer, format="JPEG")
    return buffer.getvalue()


def test_all_mode_accepts_any_non_cmyk_image():
    # `all` transcribes every image over the converter's geometry floor; it does
    # not second-guess the content. A flat fill is eligible (Tesseract just
    # returns nothing), which keeps the mode's contract simple and predictable.
    proc = ImageOcrProcessor(mode="all", lang="eng")
    assert proc.is_candidate(_uniform_png(), "png") is True


def test_all_mode_still_skips_cmyk_pinning_446():
    # Pins the current CMYK exclusion. `all` should eventually transcribe CMYK
    # too (convert to RGB first), tracked in #446; until then it is held back so
    # the OCR path never hands Tesseract a colorspace it misreads.
    proc = ImageOcrProcessor(mode="all", lang="eng")
    assert proc.is_candidate(_cmyk_jpg(), "jpg") is False


def test_is_candidate_caches_by_image_hash():
    proc = ImageOcrProcessor(mode="all", lang="eng")
    image = _uniform_png()
    assert proc.is_candidate(image, "png") is True
    # second call is served from the per-request eligibility cache, same answer.
    assert proc.is_candidate(image, "png") is True


def test_tesseract_error_warns_failed_not_timeout(monkeypatch: pytest.MonkeyPatch):
    """A bad binary/langpack (TesseractError, a RuntimeError subclass) must warn
    ocr_image_failed, never ocr_image_timeout (#140 review, B4 regression)."""
    def boom(*_a, **_k):
        raise pytesseract.TesseractError(1, "language data missing")

    monkeypatch.setattr(pytesseract, "image_to_data", boom)
    proc = ImageOcrProcessor(mode="all", lang="eng")
    assert proc(_uniform_png(), "png") is None
    assert "ocr_image_failed" in proc.warnings
    assert "ocr_image_timeout" not in proc.warnings


def test_plain_runtime_error_warns_timeout(monkeypatch: pytest.MonkeyPatch):
    """pytesseract raises a plain RuntimeError when it kills an overrun run."""
    def boom(*_a, **_k):
        raise RuntimeError("Tesseract process timeout")

    monkeypatch.setattr(pytesseract, "image_to_data", boom)
    proc = ImageOcrProcessor(mode="all", lang="eng")
    assert proc(_uniform_png(), "png") is None
    assert "ocr_image_timeout" in proc.warnings
    assert "ocr_image_failed" not in proc.warnings
