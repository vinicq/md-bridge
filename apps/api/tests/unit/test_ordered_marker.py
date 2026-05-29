"""Unit coverage for ordered-list marker normalization (#144).

Loads the vendored converter through the API loader and drives the pure
`normalize_ordered_marker` helper.
"""
from __future__ import annotations

from app.services.packages_loader import pdf_to_md_module

mod = pdf_to_md_module()


def test_digit_marker_first_item_preserves_start():
    assert mod.normalize_ordered_marker("7) start here", first=True) == ("7.", "start here")
    assert mod.normalize_ordered_marker("1. first", first=True) == ("1.", "first")


def test_non_first_items_renumber_from_one():
    # CommonMark increments from the first marker, so the rest are always "1.".
    assert mod.normalize_ordered_marker("2. second", first=False) == ("1.", "second")
    assert mod.normalize_ordered_marker("9) ninth", first=False) == ("1.", "ninth")


def test_alpha_and_roman_markers_map_to_one():
    assert mod.normalize_ordered_marker("a) alpha", first=True) == ("1.", "alpha")
    assert mod.normalize_ordered_marker("i. roman", first=True) == ("1.", "roman")


def test_unrecognized_marker_returns_text_unchanged():
    assert mod.normalize_ordered_marker("no marker here", first=True) == ("", "no marker here")
