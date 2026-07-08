"""Integration coverage for the OCR page cap (#208) over the real pipeline.

The over-cap path is asserted with real PyMuPDF inspection: it rejects the scan
before the OCR subprocess starts, so it runs even without Tesseract. The
under-cap path drives the real Tesseract pre-pass end to end and skips when the
binary is absent (per the no-mocked-binary rule for the integration tier).
"""
from __future__ import annotations

import io
import shutil

import pymupdf
import pytest
from app.errors import ApiError
from app.services.pdf_to_md import convert_pdf_bytes


def _scanned_pdf(pages: int) -> bytes:
    """An image-only (needs_ocr) PDF with `pages` rasterized text pages."""
    Image = pytest.importorskip("PIL.Image")
    ImageDraw = pytest.importorskip("PIL.ImageDraw")
    ImageFont = pytest.importorskip("PIL.ImageFont")

    image = Image.new("RGB", (1200, 400), "white")
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default(size=72)
    draw.text((80, 140), "OCR BRIDGE SAMPLE", fill="black", font=font)
    png = io.BytesIO()
    image.save(png, format="PNG")

    doc = pymupdf.open()
    try:
        for _ in range(pages):
            page = doc.new_page(width=612, height=252)
            page.insert_image(page.rect, stream=png.getvalue())
        return doc.tobytes()
    finally:
        doc.close()


def test_scan_over_cap_returns_413(monkeypatch):
    monkeypatch.setenv("MD_BRIDGE_OCR_ENABLED", "1")
    monkeypatch.setenv("MD_BRIDGE_OCR_MAX_PAGES", "1")
    pdf = _scanned_pdf(pages=2)

    with pytest.raises(ApiError) as exc:
        convert_pdf_bytes(pdf, filename="long-scan.pdf")

    assert exc.value.status_code == 413
    assert exc.value.code == "ocr_too_many_pages"
    assert exc.value.extra_detail == {"pages": 2, "max_pages": 1}


@pytest.mark.skipif(
    shutil.which("tesseract") is None,
    reason="tesseract binary is not installed",
)
def test_scan_under_cap_is_converted(monkeypatch):
    pytest.importorskip("pytesseract")
    monkeypatch.setenv("MD_BRIDGE_OCR_ENABLED", "1")
    monkeypatch.setenv("MD_BRIDGE_OCR_MAX_PAGES", "5")
    pdf = _scanned_pdf(pages=2)

    result = convert_pdf_bytes(pdf, filename="short-scan.pdf")

    assert result.ocr_applied is True
    assert "OCR" in result.md.upper()
