"""Integration coverage for figure attr-list anchors (#165).

Builds a real PDF with PyMuPDF (no mock): two images, each with a numbered
caption just below it. Conversion runs through `convert_document` with
--with-images (the CLI path; the API service never extracts images), so it
behaves identically on POSIX and Windows, like the caption-alt regression test.
"""
from __future__ import annotations

import struct
import tempfile
import zlib
from pathlib import Path

import pymupdf
from app.services.packages_loader import pdf_to_md_module


def _tiny_png(pixels: bytes) -> bytes:
    def chunk(tag: bytes, data: bytes) -> bytes:
        body = tag + data
        return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF)

    sig = b"\x89PNG\r\n\x1a\n"
    ihdr = struct.pack(">IIBBBBB", 2, 2, 8, 2, 0, 0, 0)
    idat = zlib.compress(pixels)
    return sig + chunk(b"IHDR", ihdr) + chunk(b"IDAT", idat) + chunk(b"IEND", b"")


_PNG_A = _tiny_png(b"\x00\xff\x00\x00\x00\xff\x00\x00\x00\xff\x00\x00\x00")
_PNG_B = _tiny_png(b"\x00\x00\x00\xff\x00\x00\x00\xff\x00\x00\x00\xff\x00")


def _build_pdf() -> bytes:
    doc = pymupdf.open()
    page = doc.new_page(width=400, height=700)
    page.insert_text(
        (50, 80),
        "Intro paragraph at body size with enough words to set the body font baseline here.",
        fontsize=11,
    )
    page.insert_image(pymupdf.Rect(50, 120, 200, 220), stream=_PNG_A)
    page.insert_text((50, 232), "Figure 1: Architecture overview", fontsize=8)
    page.insert_image(pymupdf.Rect(50, 320, 200, 420), stream=_PNG_B)
    page.insert_text((50, 432), "Figure 2: Data flow", fontsize=8)
    try:
        return doc.tobytes()
    finally:
        doc.close()


def _convert(pdf_bytes: bytes, **kwargs) -> str:
    mod = pdf_to_md_module()
    with tempfile.TemporaryDirectory(prefix="fig-anchor-", ignore_cleanup_errors=True) as raw:
        src = Path(raw) / "doc.pdf"
        src.write_bytes(pdf_bytes)
        out = Path(raw) / "doc.md"
        mod.convert_document(src, out, front_matter=False, extract_images=True, **kwargs)
        return out.read_text(encoding="utf-8")


def test_numbered_figures_get_sequential_anchors():
    md = _convert(_build_pdf(), emit_figure_anchors=True)
    images = [line for line in md.splitlines() if line.startswith("![")]
    assert any("{#fig-1 .figure}" in line for line in images)
    assert any("{#fig-2 .figure}" in line for line in images)
    # The caption stays visible in the body (the anchor reads it, does not consume it).
    assert "Figure 1: Architecture overview" in md


def test_no_anchors_by_default():
    md = _convert(_build_pdf())
    assert "{#fig-" not in md
    # Both images still extracted, captions still inline.
    assert len([line for line in md.splitlines() if line.startswith("![")]) == 2
    assert "Figure 1: Architecture overview" in md


def test_anchor_and_caption_alt_combine():
    # With both options, the caption becomes alt (consumed) AND the image gets
    # the anchor id.
    md = _convert(_build_pdf(), emit_figure_anchors=True, caption_alt_text=True)
    images = [line for line in md.splitlines() if line.startswith("![")]
    assert any(line.startswith("![Figure 1: Architecture overview](") and "{#fig-1 .figure}" in line for line in images)
