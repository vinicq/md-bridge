"""Unit coverage for opt-in tight and loose PDF list spacing (#168)."""
from __future__ import annotations

import markdown
from app.services.packages_loader import pdf_to_md_module

mod = pdf_to_md_module()


def _profile(*, enabled: bool, detect_task_lists: bool = False) -> object:
    return mod.DocProfile(
        body_size=11.0,
        body_font="Body",
        heading_thresholds={1: 18.0, 2: 14.0, 3: 12.5},
        small_size=10.0,
        body_x0=72.0,
        list_base_x0=72.0,
        indent_unit=18.0,
        tight_loose_lists=enabled,
        detect_task_lists=detect_task_lists,
    )


def _block(text: str, top: float, x0: float = 72.0):
    bbox = (x0, top, x0 + 228.0, top + 10.0)
    span = mod.Span(text=text, size=11.0, font="Body", flags=0, bbox=bbox)
    return mod.Block(lines=[mod.Line(spans=[span], bbox=bbox)], bbox=bbox)


def _render(marker: str, *, enabled: bool, loose: bool) -> str:
    second_top = 40.0 if loose else 22.0
    items = [("block", _block(f"{marker} one", 0.0)), ("block", _block(f"{marker} two", second_top))]
    return mod.assemble_markdown(items, _profile(enabled=enabled))


def test_default_output_keeps_legacy_bullet_and_numbered_spacing():
    assert _render("•", enabled=False, loose=False) == "- one\n\n- two"
    assert _render("1.", enabled=False, loose=False) == "1. one\n1. two"


def test_enabled_tight_lists_have_no_blank_item_separator():
    for marker in ("•", "1."):
        rendered = _render(marker, enabled=True, loose=False)
        assert "\n\n" not in rendered
        assert "<p>" not in markdown.markdown(rendered)


def test_enabled_loose_lists_blank_separate_every_item():
    for marker in ("•", "1."):
        rendered = _render(marker, enabled=True, loose=True)
        assert "\n\n" in rendered
        assert markdown.markdown(rendered).count("<p>") == 2


def test_enabled_nested_opposite_marker_stays_one_tight_run():
    # A bullet parent with an indented numbered child stays one tight list; the
    # cross-marker flush must not split it into blank-separated blocks (#168 review).
    items = [("block", _block("• Parent", 0.0)), ("block", _block("1. Child", 18.0, x0=90.0))]
    rendered = mod.assemble_markdown(items, _profile(enabled=True))
    assert rendered == "- Parent\n  1. Child"
    assert "\n\n" not in rendered


def test_enabled_task_items_follow_geometry_not_forced_loose():
    # Checkbox items classify as paragraphs; with task detection on they must
    # honor tight/loose spacing rather than always render loose (#168 review).
    prof = _profile(enabled=True, detect_task_lists=True)
    tight = mod.assemble_markdown([("block", _block("☐ One", 0.0)), ("block", _block("☐ Two", 18.0))], prof)
    loose = mod.assemble_markdown([("block", _block("☐ One", 0.0)), ("block", _block("☐ Two", 40.0))], prof)
    assert mod._normalize_task_lists(tight, extended=False) == "- [ ] One\n- [ ] Two"
    assert mod._normalize_task_lists(loose, extended=False) == "- [ ] One\n\n- [ ] Two"


def test_cli_list_loose_threshold_rejects_nonpositive_and_nonfinite():
    import argparse

    import pytest
    for bad in ("0", "-1", "nan", "inf", "-inf"):
        with pytest.raises(argparse.ArgumentTypeError):
            mod._positive_finite_float(bad)
    assert mod._positive_finite_float("1.5") == 1.5
