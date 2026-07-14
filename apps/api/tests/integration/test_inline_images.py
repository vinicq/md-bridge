"""Integration coverage for inline base64 images (#372).

Proves the self-contained-Markdown path end to end: an embedded image comes out
as a `data:` URI (no external file, no relative path), and the API honors
`with_images` by inlining instead of the old no-op. Builds a real PDF with
PyMuPDF (no mock).
"""
from __future__ import annotations

import base64
import json
import re
import struct
import sys
import tempfile
import zlib
from pathlib import Path

import pymupdf
import pytest
from app.services.packages_loader import pdf_to_md_module

_PNG_SIG = b"\x89PNG\r\n\x1a\n"

# convert_pdf_bytes keeps the PyMuPDF handle open, which locks the per-request
# tempdir on Windows during cleanup; POSIX (CI) unlinks open files, so the API
# path is exercised there. The converter-level test below uses its own tempdir
# with ignore_cleanup_errors, so it covers the inline logic cross-platform.
WIN_TEMPDIR_LOCK = pytest.mark.skipif(
    sys.platform == "win32",
    reason="PyMuPDF holds the handle open; the service tempdir cannot be unlinked on Windows.",
)


def _tiny_png() -> bytes:
    def chunk(tag: bytes, data: bytes) -> bytes:
        body = tag + data
        return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF)

    ihdr = struct.pack(">IIBBBBB", 2, 2, 8, 2, 0, 0, 0)  # 2x2, 8-bit RGB
    idat = zlib.compress(b"\x00\xff\x00\x00\x00\xff\x00\x00\x00\xff\x00\x00\x00")
    return _PNG_SIG + chunk(b"IHDR", ihdr) + chunk(b"IDAT", idat) + chunk(b"IEND", b"")


def _pdf_with_image() -> bytes:
    doc = pymupdf.open()
    page = doc.new_page(width=400, height=500)
    page.insert_text(
        (50, 80),
        "Body text with enough words here to set the body font baseline and keep OCR off.",
        fontsize=11,
    )
    page.insert_image(pymupdf.Rect(50, 120, 200, 220), stream=_tiny_png())
    try:
        return doc.tobytes()
    finally:
        doc.close()


def test_convert_document_inlines_images_as_data_uri():
    mod = pdf_to_md_module()
    with tempfile.TemporaryDirectory(prefix="inline-img-", ignore_cleanup_errors=True) as raw:
        src = Path(raw) / "doc.pdf"
        src.write_bytes(_pdf_with_image())
        out = Path(raw) / "doc.md"
        mod.convert_document(src, out, front_matter=False, inline_images=True)
        md = out.read_text(encoding="utf-8")

    # Nothing written to disk beside the .md: inline mode creates no images dir.
    assert not (Path(raw) / "images").exists()
    # The image is emitted as a data URI, not a relative path.
    m = re.search(r"!\[[^\]]*\]\((data:image/[^;]+;base64,([A-Za-z0-9+/=]+))\)", md)
    assert m, f"expected an inline data-URI image, got:\n{md}"
    # The payload round-trips back to the original PNG.
    assert base64.b64decode(m.group(2)).startswith(_PNG_SIG)


@WIN_TEMPDIR_LOCK
def test_api_with_images_returns_self_contained_markdown(client):
    resp = client.post(
        "/api/pdf-to-md",
        files={"file": ("doc.pdf", _pdf_with_image(), "application/pdf")},
        data={"options": json.dumps({"with_images": True})},
    )
    assert resp.status_code == 200, resp.text
    md = resp.json()["md"]
    assert "data:image/" in md, "images should be inlined on the API path"
    assert "](images/" not in md, "no relative image path should leak into the .md"
