"""Unit coverage for image click-action link detection (#170)."""
from __future__ import annotations

from app.services.packages_loader import pdf_to_md_module

mod = pdf_to_md_module()


def test_image_link_uri_returns_a_target_that_covers_the_image():
    link = {"from": (20, 30, 170, 110), "uri": "https://example.com/image"}
    assert mod.image_link_uri((20, 30, 170, 110), [link]) == "https://example.com/image"


def test_image_link_uri_rejects_a_small_partial_overlap():
    link = {"from": (20, 30, 80, 110), "uri": "https://example.com/partial"}
    assert mod.image_link_uri((20, 30, 170, 110), [link]) is None


def test_image_link_uri_rejects_an_overlap_that_leaves_one_edge_uncovered():
    link = {"from": (20, 30, 140, 110), "uri": "https://example.com/partial"}
    assert mod.image_link_uri((20, 30, 170, 110), [link]) is None


def test_image_link_uri_keeps_internal_page_destinations():
    link = {"from": (20, 30, 170, 110), "page": 2}
    assert mod.image_link_uri((20, 30, 170, 110), [link]) == "#page-3"
