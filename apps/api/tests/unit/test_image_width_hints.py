"""Unit coverage for image bbox width attr-list hints (#169)."""
from __future__ import annotations

from app.services.packages_loader import pdf_to_md_module

mod = pdf_to_md_module()


def test_image_width_attr_rounds_positive_bbox_widths():
    assert mod._image_width_attr(0.4) == "width=1"
    assert mod._image_width_attr(149.6) == "width=150"
    assert mod._image_width_attr(150.4) == "width=150"


def test_image_width_attr_skips_empty_or_invalid_bbox_widths():
    assert mod._image_width_attr(0) is None
    assert mod._image_width_attr(-1) is None
