"""Unit coverage for image bbox width attr-list hints (#169)."""
from __future__ import annotations

from app.services.packages_loader import pdf_to_md_module

mod = pdf_to_md_module()


def test_image_width_attr_converts_points_to_css_pixels():
    # bbox width is PDF points; attr_list width renders as CSS px (1/96in), so
    # convert x96/72 to round-trip at the source size (#169 review).
    assert mod._image_width_attr(72.0) == "width=96"  # 1 inch
    assert mod._image_width_attr(150.0) == "width=200"
    assert mod._image_width_attr(0.4) == "width=1"  # rounds and clamps up


def test_image_width_attr_skips_empty_or_invalid_bbox_widths():
    assert mod._image_width_attr(0) is None
    assert mod._image_width_attr(-1) is None
