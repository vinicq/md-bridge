"""Integration coverage for caption-derived image alt text (#149).

Builds a real PDF with PyMuPDF (no mock): a body paragraph, an embedded image
with a small-font caption ~12pt below it, and a second image with no caption.
Conversion runs through `convert_document` with --with-images, the same path the
CLI uses (the API service never extracts images), so it behaves identically on
POSIX and Windows, like the corpus regression test.
"""
from __future__ import annotations

import struct
import tempfile
import zlib
from pathlib import Path

import pymupdf
from app.services.packages_loader import pdf_to_md_module


def _tiny_png(pixels: bytes) -> bytes:
    # Distinct pixel data per image so PyMuPDF does not dedupe two identical
    # images into a single xref (which would drop one placement).
    def chunk(tag: bytes, data: bytes) -> bytes:
        body = tag + data
        return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF)

    sig = b"\x89PNG\r\n\x1a\n"
    ihdr = struct.pack(">IIBBBBB", 2, 2, 8, 2, 0, 0, 0)  # 2x2, 8-bit RGB
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
    page.insert_text((50, 232), "Figure 1: Architecture overview", fontsize=8)  # caption ~12pt below
    page.insert_image(pymupdf.Rect(50, 320, 200, 420), stream=_PNG_B)  # no caption below
    page.insert_text(
        (50, 520),
        "Closing body text that is not a caption because it sits far below the second image.",
        fontsize=11,
    )
    try:
        return doc.tobytes()
    finally:
        doc.close()


def _convert(pdf_bytes: bytes, *, caption_alt_text: bool) -> str:
    mod = pdf_to_md_module()
    # ignore_cleanup_errors: convert_document keeps the PyMuPDF handle open, so
    # on Windows the source PDF inside the temp dir cannot be unlinked at exit;
    # the conversion and assertions have already completed by then.
    with tempfile.TemporaryDirectory(prefix="caption-alt-", ignore_cleanup_errors=True) as raw:
        src = Path(raw) / "doc.pdf"
        src.write_bytes(pdf_bytes)
        out = Path(raw) / "doc.md"
        mod.convert_document(
            src, out, front_matter=False, extract_images=True, caption_alt_text=caption_alt_text
        )
        return out.read_text(encoding="utf-8")


def test_caption_becomes_alt_when_enabled():
    md = _convert(_build_pdf(), caption_alt_text=True)
    images = [line for line in md.splitlines() if line.startswith("![")]
    # First image takes the caption as alt; the uncaptioned one stays empty.
    assert any(line.startswith("![Figure 1: Architecture overview](") for line in images)
    assert any(line.startswith("![](") for line in images)
    # The caption text is consumed, not also emitted as a body paragraph.
    body = "\n".join(line for line in md.splitlines() if not line.startswith("!["))
    assert "Figure 1: Architecture overview" not in body


def _build_side_by_side_pdf() -> bytes:
    doc = pymupdf.open()
    page = doc.new_page(width=400, height=500)
    # A body paragraph at 11pt sets the body size so the 8pt captions read as
    # small font (the caption gate keys on small_size).
    page.insert_text(
        (40, 60),
        "Body paragraph at the dominant font size with enough words to set the baseline here.",
        fontsize=11,
    )
    # Two figures on the same row, each with its own caption directly below.
    page.insert_image(pymupdf.Rect(40, 120, 180, 220), stream=_PNG_A)
    page.insert_text((40, 232), "Left figure caption", fontsize=8)
    page.insert_image(pymupdf.Rect(220, 120, 360, 220), stream=_PNG_B)
    page.insert_text((220, 232), "Right figure caption", fontsize=8)
    try:
        return doc.tobytes()
    finally:
        doc.close()


def test_side_by_side_figures_keep_their_own_caption():
    # Both captions share the same vertical gap; horizontal overlap must decide
    # the pairing so neither image steals the other's caption (#323 Codex P2).
    md = _convert(_build_side_by_side_pdf(), caption_alt_text=True)
    images = [line for line in md.splitlines() if line.startswith("![")]
    left = next(line for line in images if "p1_img1" in line)
    right = next(line for line in images if "p1_img2" in line)
    assert left.startswith("![Left figure caption](")
    assert right.startswith("![Right figure caption](")


def test_default_keeps_empty_alt_and_caption_in_body():
    md = _convert(_build_pdf(), caption_alt_text=False)
    images = [line for line in md.splitlines() if line.startswith("![")]
    assert len(images) == 2  # both distinct images were extracted
    assert all(line.startswith("![](") for line in images)  # every alt empty
    assert "Figure 1: Architecture overview" in md  # caption stays inline
