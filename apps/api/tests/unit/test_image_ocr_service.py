"""Unit coverage for the per-image OCR service (#140).

The deterministic density filter runs on Pillow alone (no subprocess), and the
Tesseract error handling is exercised by mocking only the pytesseract binding,
so both run without the Tesseract binary and without a skip on Windows. This is
the coverage the real-Tesseract integration test cannot give (it is skipped
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
    """A flat white fill: every pixel in one bin, variance 0 -> a non-text photo."""
    from PIL import Image

    return _png(Image.new("RGB", (400, 200), "white"))


def _texty_png() -> bytes:
    """A high-contrast image (half black, half white): the histogram spreads
    across two far bins and the variance is high, so the density filter reads it
    as content worth OCR rather than a flat fill or smooth photo."""
    from PIL import Image, ImageDraw

    image = Image.new("RGB", (400, 200), "white")
    ImageDraw.Draw(image).rectangle([0, 0, 200, 200], fill="black")
    return _png(image)


def test_auto_rejects_a_uniform_photo_but_all_accepts_it():
    uniform = _uniform_png()
    assert ImageOcrProcessor(mode="auto", lang="eng").is_candidate(uniform, "png") is False
    assert ImageOcrProcessor(mode="all", lang="eng").is_candidate(uniform, "png") is True


def test_auto_accepts_a_high_contrast_text_image():
    texty = _texty_png()
    assert ImageOcrProcessor(mode="auto", lang="eng").is_candidate(texty, "png") is True
    assert ImageOcrProcessor(mode="all", lang="eng").is_candidate(texty, "png") is True


def test_is_candidate_caches_by_image_hash():
    proc = ImageOcrProcessor(mode="auto", lang="eng")
    texty = _texty_png()
    assert proc.is_candidate(texty, "png") is True
    # second call is served from the per-request eligibility cache, same answer.
    assert proc.is_candidate(texty, "png") is True


def test_tesseract_error_warns_failed_not_timeout(monkeypatch: pytest.MonkeyPatch):
    """A bad binary/langpack (TesseractError, a RuntimeError subclass) must warn
    ocr_image_failed, never ocr_image_timeout (#140 review, B4 regression)."""
    def boom(*_a, **_k):
        raise pytesseract.TesseractError(1, "language data missing")

    monkeypatch.setattr(pytesseract, "image_to_data", boom)
    proc = ImageOcrProcessor(mode="all", lang="eng")
    assert proc(_texty_png(), "png") is None
    assert "ocr_image_failed" in proc.warnings
    assert "ocr_image_timeout" not in proc.warnings


def test_plain_runtime_error_warns_timeout(monkeypatch: pytest.MonkeyPatch):
    """pytesseract raises a plain RuntimeError when it kills an overrun run."""
    def boom(*_a, **_k):
        raise RuntimeError("Tesseract process timeout")

    monkeypatch.setattr(pytesseract, "image_to_data", boom)
    proc = ImageOcrProcessor(mode="all", lang="eng")
    assert proc(_texty_png(), "png") is None
    assert "ocr_image_timeout" in proc.warnings
    assert "ocr_image_failed" not in proc.warnings
