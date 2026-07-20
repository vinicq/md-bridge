"""Real-PDF integration coverage for image click-action links (#170)."""
from __future__ import annotations

import struct
import sys
import tempfile
import zlib
from pathlib import Path

import pymupdf
import pytest
from app.schemas.convert import PdfToMdOptions
from app.services.packages_loader import md_to_pdf_module, pdf_to_md_module
from app.services.pdf_to_md import convert_pdf_bytes

_TARGET_URI = "https://example.com/image"
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


def _build_pdf(*, partial_link: bool = False, caption: bool = False) -> bytes:
    doc = pymupdf.open()
    page = doc.new_page(width=400, height=300)
    page.insert_text(
        (40, 60),
        "Body paragraph at the dominant font size with enough words to set the baseline here.",
        fontsize=11,
    )
    image_rect = pymupdf.Rect(40, 100, 190, 180)
    page.insert_image(image_rect, stream=_tiny_png())
    link_rect = pymupdf.Rect(40, 100, 160, 180) if partial_link else image_rect
    page.insert_link({"kind": pymupdf.LINK_URI, "from": link_rect, "uri": _TARGET_URI})
    if caption:
        page.insert_text((40, 192), "Figure 1: Linked image", fontsize=8)
    try:
        return doc.tobytes()
    finally:
        doc.close()


def _convert(pdf_bytes: bytes, **kwargs: object) -> str:
    mod = pdf_to_md_module()
    with tempfile.TemporaryDirectory(prefix="image-link-", ignore_cleanup_errors=True) as raw:
        src = Path(raw) / "doc.pdf"
        src.write_bytes(pdf_bytes)
        out = Path(raw) / "doc.md"
        mod.convert_document(src, out, front_matter=False, extract_images=True, **kwargs)
        return out.read_text(encoding="utf-8")


def test_wraps_an_extracted_image_in_its_source_link_when_enabled():
    md = _convert(_build_pdf(), image_link_anchors=True)
    image_line = next(line for line in md.splitlines() if line.startswith("[!["))
    assert len([line for line in md.splitlines() if line.startswith("[![")]) == 1
    assert image_line.startswith("[![](images/doc/p1_img1.png)](")
    assert image_line.endswith(f"]({_TARGET_URI})")


def test_default_and_explicit_off_keep_image_output_byte_identical():
    pdf = _build_pdf()
    default_md = _convert(pdf)
    explicit_off_md = _convert(pdf, image_link_anchors=False)
    assert explicit_off_md == default_md
    assert len([line for line in default_md.splitlines() if line.startswith("![")]) == 1
    assert f"]({_TARGET_URI})" not in default_md


def test_partial_click_area_does_not_link_the_whole_image():
    md = _convert(_build_pdf(partial_link=True), image_link_anchors=True)
    image_line = next(line for line in md.splitlines() if line.startswith("!["))
    assert image_line.startswith("![](images/doc/p1_img1.png)")
    assert f"]({_TARGET_URI})" not in image_line


def test_link_wrapper_keeps_figure_attr_list_on_the_image():
    md = _convert(_build_pdf(caption=True), image_link_anchors=True, emit_figure_anchors=True)
    image_line = next(line for line in md.splitlines() if line.startswith("[!["))
    assert image_line.endswith(f"{{#fig-1 .figure}}]({_TARGET_URI})")

    html = md_to_pdf_module().markdown.markdown(
        image_line,
        extensions=md_to_pdf_module().MD_EXTENSIONS,
        output_format="html5",
    )
    assert f'href="{_TARGET_URI}"' in html
    assert 'id="fig-1"' in html
    assert 'class="figure"' in html


@WIN_TEMPDIR_LOCK
def test_api_with_images_forwards_image_link_anchor_to_inline_image():
    response = convert_pdf_bytes(
        _build_pdf(),
        filename="image-link.pdf",
        options=PdfToMdOptions(with_images=True, front_matter=False, image_link_anchors=True),
    )
    image_line = next(line for line in response.md.splitlines() if line.startswith("[!["))
    assert image_line.startswith("[![](data:image/")
    assert image_line.endswith(f"]({_TARGET_URI})")


def test_cli_with_images_forwards_image_link_anchor(monkeypatch: pytest.MonkeyPatch):
    mod = pdf_to_md_module()
    with tempfile.TemporaryDirectory(prefix="image-link-cli-", ignore_cleanup_errors=True) as raw:
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
                "--image-link-anchors",
            ],
        )
        assert mod.main() == 0
        image_line = next(line for line in out.read_text(encoding="utf-8").splitlines() if line.startswith("[!["))
        assert image_line.endswith(f"]({_TARGET_URI})")
