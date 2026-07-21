"""Unit coverage for the deterministic OCR-candidate selection (#140).

`_ocr_candidate_keys` picks which embedded images are eligible for OCR by pure
PyMuPDF geometry (no Tesseract, no Pillow), so this runs on every platform. It
is distinct from the ImageOcrProcessor LRU cache (that is per-image OCR output);
this covers the size/area/vector-overlap/format filter and the 50-candidate cap.
"""
from __future__ import annotations

import io

import pymupdf
import pytest
from app.services.packages_loader import pdf_to_md_module

pytest.importorskip("PIL.Image")

mod = pdf_to_md_module()


def _png(px_w: int, px_h: int) -> bytes:
    from PIL import Image, ImageDraw

    image = Image.new("RGB", (px_w, px_h), "white")
    ImageDraw.Draw(image).rectangle([0, 0, px_w // 2, px_h], fill="black")
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def _doc(specs):
    """specs: list of (px_w, px_h, rect). One page, images inserted in order."""
    doc = pymupdf.open()
    page = doc.new_page(width=800, height=600)
    for px_w, px_h, rect in specs:
        page.insert_image(rect, stream=_png(px_w, px_h))
    return doc


def _keys(doc, selector=lambda _b, _e: True):
    return mod._ocr_candidate_keys(doc, selector)


def test_small_pixel_image_is_rejected():
    # 100x50 px is below the 200x100 minimum: a logo/icon, never a candidate.
    doc = _doc([(100, 50, pymupdf.Rect(40, 40, 400, 300))])
    keys, truncated = _keys(doc)
    assert keys == frozenset() and truncated is False


def test_large_image_over_the_area_floor_is_selected():
    doc = _doc([(600, 300, pymupdf.Rect(40, 40, 600, 400))])
    keys, truncated = _keys(doc)
    assert keys == frozenset({(0, 0)}) and truncated is False


def test_tiny_bbox_area_is_rejected():
    # Big pixels but a bbox under 0.5% of the 800x600 page (2400 sq pt): a
    # watermark-sized placement, rejected by the area floor.
    doc = _doc([(600, 300, pymupdf.Rect(10, 10, 40, 40))])  # 30x30 = 900 < 2400
    keys, _ = _keys(doc)
    assert keys == frozenset()


def test_more_than_fifty_candidates_truncates_to_the_largest():
    specs = []
    for i in range(55):
        x, y = (i % 10) * 70 + 20, (i // 10) * 70 + 20
        specs.append((300, 200, pymupdf.Rect(x, y, x + 60, y + 60)))
    keys, truncated = _keys(_doc(specs))
    assert len(keys) == 50
    assert truncated is True


def test_selector_can_reject_a_geometrically_eligible_image():
    doc = _doc([(600, 300, pymupdf.Rect(40, 40, 600, 400))])
    keys, _ = _keys(doc, selector=lambda _b, _e: False)
    assert keys == frozenset()


def test_image_ocr_block_emits_the_ocr_container():
    # The converter emits the `::: ocr` marker (renderer builds the figure from
    # it, ADR-001). This locks the exact emitted syntax without depending on the
    # CI-Linux-only real-Tesseract integration test, which Windows skips.
    assert mod._image_ocr_block("recognized text") == "::: ocr\nrecognized text\n:::"
