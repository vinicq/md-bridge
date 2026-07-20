"""Real-PDF integration coverage for image width attr-list hints (#169)."""
from __future__ import annotations

import struct
import sys
import tempfile
import zlib
from pathlib import Path

import pymupdf
import pytest
from app.schemas.convert import PdfToMdOptions
from app.services.packages_loader import pdf_to_md_module
from app.services.pdf_to_md import convert_pdf_bytes

WIN_TEMPDIR_LOCK = pytest.mark.skipif(
    sys.platform == "win32",
    reason="convert_pdf_bytes holds the source PDF while its tempdir exits on Windows.",
)


def _tiny_png() -> bytes:
    def chunk(tag: bytes, data: bytes) -> bytes:
        body = tag + data
        return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF)

    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", 2, 2, 8, 2, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(b"\x00\xff\x00\x00\x00\xff\x00\x00\x00\xff\x00\x00\x00"))
        + chunk(b"IEND", b"")
    )


def _build_pdf() -> bytes:
    doc = pymupdf.open()
    page = doc.new_page(width=400, height=300)
    page.insert_text(
        (40, 60),
        "Body paragraph at the dominant font size with enough words to set the baseline here.",
        fontsize=11,
    )
    page.insert_image(pymupdf.Rect(40, 100, 190, 180), stream=_tiny_png())
    page.insert_text((40, 192), "Figure 1: Width hint fixture", fontsize=8)
    try:
        return doc.tobytes()
    finally:
        doc.close()


def _convert(pdf_bytes: bytes, **kwargs: object) -> str:
    mod = pdf_to_md_module()
    with tempfile.TemporaryDirectory(prefix="image-width-", ignore_cleanup_errors=True) as raw:
        src = Path(raw) / "doc.pdf"
        src.write_bytes(pdf_bytes)
        out = Path(raw) / "doc.md"
        mod.convert_document(src, out, front_matter=False, extract_images=True, **kwargs)
        return out.read_text(encoding="utf-8")


def test_emits_extracted_image_bbox_width_when_enabled():
    md = _convert(_build_pdf(), image_width_hints=True)
    image_line = next(line for line in md.splitlines() if line.startswith("!["))
    assert image_line.endswith("{width=200}")


def test_default_and_explicit_off_keep_image_output_byte_identical():
    pdf = _build_pdf()
    default_md = _convert(pdf)
    explicit_off_md = _convert(pdf, image_width_hints=False)
    assert explicit_off_md == default_md
    assert "{width=" not in default_md


def test_width_hint_combines_with_figure_anchor_in_one_attr_list():
    pdf = _build_pdf()
    md = _convert(pdf, image_width_hints=True, emit_figure_anchors=True)
    image_line = next(line for line in md.splitlines() if line.startswith("!["))
    assert image_line.endswith("{#fig-1 .figure width=200}")


@WIN_TEMPDIR_LOCK
def test_api_with_images_forwards_width_hint_to_inline_image():
    response = convert_pdf_bytes(
        _build_pdf(),
        filename="image-width.pdf",
        options=PdfToMdOptions(with_images=True, front_matter=False, image_width_hints=True),
    )
    image_line = next(line for line in response.md.splitlines() if line.startswith("!["))
    assert image_line.startswith("![](data:image/")
    assert image_line.endswith("{width=200}")


@WIN_TEMPDIR_LOCK
def test_api_default_and_explicit_off_keep_inline_image_output_byte_identical():
    pdf = _build_pdf()
    default_md = convert_pdf_bytes(
        pdf,
        filename="image-width.pdf",
        options=PdfToMdOptions(with_images=True, front_matter=False),
    ).md
    explicit_off_md = convert_pdf_bytes(
        pdf,
        filename="image-width.pdf",
        options=PdfToMdOptions(with_images=True, front_matter=False, image_width_hints=False),
    ).md
    assert explicit_off_md == default_md
    assert "{width=" not in default_md


def test_cli_with_images_forwards_width_hint(monkeypatch: pytest.MonkeyPatch):
    mod = pdf_to_md_module()
    with tempfile.TemporaryDirectory(prefix="image-width-cli-", ignore_cleanup_errors=True) as raw:
        src = Path(raw) / "doc.pdf"
        src.write_bytes(_build_pdf())
        out = Path(raw) / "doc.md"
        monkeypatch.setattr(
            sys,
            "argv",
            [
                "convert.py",
                str(src),
                "--output",
                str(out),
                "--no-front-matter",
                "--with-images",
                "--image-width-hints",
            ],
        )
        assert mod.main() == 0
        image_line = next(line for line in out.read_text(encoding="utf-8").splitlines() if line.startswith("!["))
        assert image_line.endswith("{width=200}")
