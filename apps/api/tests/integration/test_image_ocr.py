"""Production-path coverage for selective OCR of embedded PDF images (#140)."""
from __future__ import annotations

import contextlib
import io
import sys
import tempfile
from pathlib import Path

import pymupdf
import pytest
from app.errors import ApiError
from app.schemas.convert import PdfToMdOptions
from app.services import pdf_to_md
from app.services.ocr import ocr_stack_available
from app.services.packages_loader import pdf_to_md_module
from app.services.pdf_to_md import convert_pdf_bytes

WIN_TEMPDIR_LOCK = pytest.mark.skipif(
    sys.platform == "win32",
    reason="convert_pdf_bytes keeps the source PDF open while its tempdir exits on Windows.",
)


def _pdf_with_ocrable_image() -> bytes:
    Image = pytest.importorskip("PIL.Image")
    ImageDraw = pytest.importorskip("PIL.ImageDraw")
    ImageFont = pytest.importorskip("PIL.ImageFont")

    image = Image.new("RGB", (1200, 400), "white")
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default(size=72)
    draw.text((80, 140), "OCR IMAGE CONTRACT", fill="black", font=font)
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")

    doc = pymupdf.open()
    try:
        page = doc.new_page(width=800, height=600)
        page.insert_text(
            (50, 70),
            "This vector paragraph has enough ordinary content to clear the scan "
            "gate before the embedded image is considered for OCR processing.",
            fontsize=11,
        )
        page.insert_image(pymupdf.Rect(50, 180, 750, 420), stream=buffer.getvalue())
        return doc.tobytes()
    finally:
        doc.close()


def _converter_result(pdf_bytes: bytes, callback):
    with tempfile.TemporaryDirectory(prefix="image-ocr-", ignore_cleanup_errors=True) as raw:
        source = Path(raw) / "source.pdf"
        output = Path(raw) / "output.md"
        source.write_bytes(pdf_bytes)
        warnings = pdf_to_md_module().convert_document(
            source,
            output,
            front_matter=False,
            inline_images=True,
            image_ocr_selector=lambda _bytes, _extension: True,
            image_ocr=callback,
        )
        return warnings, output.read_text(encoding="utf-8")


def test_converter_places_callback_ocr_after_each_selected_image():
    calls: list[bytes] = []

    def callback(image_bytes: bytes, _extension: str) -> str:
        calls.append(image_bytes)
        return "diagram text"

    warnings, markdown = _converter_result(_pdf_with_ocrable_image(), callback)
    assert warnings == []
    assert len(calls) == 1
    assert markdown.index("data:image/png;base64,") < markdown.index(
        "::: ocr"
    )
    assert "diagram text" in markdown


@WIN_TEMPDIR_LOCK
@pytest.mark.skipif(not ocr_stack_available(), reason="requires the optional Tesseract OCR runtime")
def test_image_ocr_reaches_convert_pdf_bytes_with_real_tesseract(monkeypatch: pytest.MonkeyPatch):
    """Pattern 15: the API production path reaches actual image OCR, no mock."""
    monkeypatch.setenv("MD_BRIDGE_OCR_ENABLED", "1")
    response = convert_pdf_bytes(
        _pdf_with_ocrable_image(),
        filename="image-ocr.pdf",
        options=PdfToMdOptions(front_matter=False, ocr_images="all"),
    )
    assert "data:image/png;base64," in response.md
    assert "::: ocr" in response.md
    assert "OCR IMAGE CONTRACT" in response.md.upper()
    assert response.ocr_images_applied is True
    assert response.ocr_applied is False  # page pre-pass did not run, only image OCR


@WIN_TEMPDIR_LOCK
def test_image_ocr_default_off_is_byte_identical_to_explicit_off():
    pdf = _pdf_with_ocrable_image()
    default = convert_pdf_bytes(
        pdf, filename="image-ocr.pdf", options=PdfToMdOptions(front_matter=False, with_images=True)
    ).md
    explicit_off = convert_pdf_bytes(
        pdf,
        filename="image-ocr.pdf",
        options=PdfToMdOptions(front_matter=False, with_images=True, ocr_images="off"),
    ).md
    assert explicit_off == default
    assert "::: ocr" not in default


def test_image_ocr_returns_typed_422_when_runtime_is_disabled(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(pdf_to_md, "image_ocr_enabled", lambda: False)
    with pytest.raises(ApiError) as caught:
        convert_pdf_bytes(
            _pdf_with_ocrable_image(),
            filename="image-ocr.pdf",
            options=PdfToMdOptions(ocr_images="auto"),
        )
    assert caught.value.status_code == 422
    assert caught.value.code == "ocr_not_available"


def test_image_ocr_chain_runs_via_convert_pdf_bytes_with_mocked_binding(
    monkeypatch: pytest.MonkeyPatch,
):
    """Pattern 15 on every platform: the production path convert_pdf_bytes ->
    ImageOcrProcessor -> figure runs with ONLY the pytesseract binding mocked
    (no Tesseract binary, no Windows tempdir skip), so the chain is proven here
    too, not only on CI Linux where the real-Tesseract test runs."""
    pytesseract = pytest.importorskip("pytesseract")
    monkeypatch.setenv("MD_BRIDGE_OCR_ENABLED", "1")
    monkeypatch.setattr("app.services.ocr.ocr_stack_available", lambda: True)

    def fake_data(*_a, **_k):
        return {
            "text": ["MOCKED", "OCR"], "conf": ["95", "95"],
            "block_num": [1, 1], "par_num": [1, 1], "line_num": [1, 1],
        }

    monkeypatch.setattr(pytesseract, "image_to_data", fake_data)

    @contextlib.contextmanager
    def _safe_tempdir():
        with tempfile.TemporaryDirectory(prefix="ocr-chain-", ignore_cleanup_errors=True) as raw:
            yield Path(raw)

    monkeypatch.setattr(pdf_to_md, "_tempdir", _safe_tempdir)

    response = convert_pdf_bytes(
        _pdf_with_ocrable_image(),
        filename="chain.pdf",
        options=PdfToMdOptions(front_matter=False, with_images=True, ocr_images="all"),
    )
    assert "::: ocr" in response.md
    assert "MOCKED OCR" in response.md
    assert response.ocr_images_applied is True
