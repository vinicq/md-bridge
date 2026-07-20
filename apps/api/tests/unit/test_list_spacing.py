"""Unit coverage for opt-in tight and loose PDF list spacing (#168)."""
from __future__ import annotations

import markdown
from app.services.packages_loader import pdf_to_md_module

mod = pdf_to_md_module()


def _profile(*, enabled: bool) -> object:
    return mod.DocProfile(
        body_size=11.0,
        body_font="Body",
        heading_thresholds={1: 18.0, 2: 14.0, 3: 12.5},
        small_size=10.0,
        body_x0=72.0,
        list_base_x0=72.0,
        indent_unit=18.0,
        tight_loose_lists=enabled,
    )


def _block(text: str, top: float):
    bbox = (72.0, top, 300.0, top + 10.0)
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
