"""Unit coverage for opt-in nested ordered lists (#194).

The emitter is a pure function over assembled items, so the state machine is
covered here cross-platform; the real-PDF path is in
tests/integration/test_nested_ordered_lists.py.
"""
from __future__ import annotations

from app.services.packages_loader import md_to_pdf_module, pdf_to_md_module

mod = pdf_to_md_module()


def _profile(*, nested: bool) -> object:
    # list_base_x0=72, indent_unit=18: x0 72 -> level 0, 90 -> level 1, 108 -> 2.
    return mod.DocProfile(
        body_size=11.0,
        body_font="Body",
        heading_thresholds={1: 18.0, 2: 14.0, 3: 12.5},
        small_size=10.0,
        body_x0=72.0,
        list_base_x0=72.0,
        indent_unit=18.0,
        nested_ordered_lists=nested,
    )


def _block(text: str, top: float, x0: float = 72.0):
    bbox = (x0, top, x0 + 228.0, top + 10.0)
    span = mod.Span(text=text, size=11.0, font="Body", flags=0, bbox=bbox)
    return mod.Block(lines=[mod.Line(spans=[span], bbox=bbox)], bbox=bbox)


def _render(items, *, nested: bool) -> str:
    return mod.assemble_markdown(items, _profile(nested=nested))


# A two-level nested numbered list: the sublist starts at "3." mid-run.
_TWO_LEVEL = [
    ("block", _block("1. First", 0.0)),
    ("block", _block("2. Second", 14.0)),
    ("block", _block("3. Sub-a", 28.0, x0=90.0)),
    ("block", _block("4. Sub-b", 42.0, x0=90.0)),
    ("block", _block("3. Third", 56.0)),
]


def test_off_is_byte_identical_to_legacy_flat_numbering():
    # Default path: the sublist flattens to `1.` at a 2-space indent, exactly as
    # before #194.
    assert _render(_TWO_LEVEL, nested=False) == (
        "1. First\n1. Second\n  1. Sub-a\n  1. Sub-b\n1. Third"
    )


def test_on_preserves_sublist_start_and_indents_four_spaces():
    # The sublist keeps its own `3.` start and sits at a 4-space indent so the
    # renderer nests it; the level-0 run still renumbers from 1.
    assert _render(_TWO_LEVEL, nested=True) == (
        "1. First\n1. Second\n    3. Sub-a\n    1. Sub-b\n1. Third"
    )


def test_on_reentry_after_shallower_level_starts_a_fresh_sublist():
    # Going back to level 0 closes the level-1 sublist, so a second descent is a
    # new sublist and preserves its own start (both 5. and 7. survive).
    items = [
        ("block", _block("1. A", 0.0)),
        ("block", _block("2. B", 14.0)),
        ("block", _block("5. B1", 28.0, x0=90.0)),
        ("block", _block("3. C", 42.0)),
        ("block", _block("7. C1", 56.0, x0=90.0)),
    ]
    assert _render(items, nested=True) == (
        "1. A\n1. B\n    5. B1\n1. C\n    7. C1"
    )


def test_on_output_round_trips_to_nested_ol_with_preserved_start():
    # The emitted markdown must nest in the shipped renderer and keep the start.
    md_mod = md_to_pdf_module()
    rendered = _render(_TWO_LEVEL, nested=True)
    html = md_mod.markdown.markdown(
        rendered, extensions=md_mod.MD_EXTENSIONS, output_format="html5"
    )
    assert html.count("<ol") == 2  # one outer list, one nested sublist
    assert 'start="3"' in html  # the sublist keeps its source start


def test_off_output_does_not_nest_in_the_renderer():
    # The legacy 2-space indent flattens into a single ordered list.
    md_mod = md_to_pdf_module()
    html = md_mod.markdown.markdown(
        _render(_TWO_LEVEL, nested=False),
        extensions=md_mod.MD_EXTENSIONS,
        output_format="html5",
    )
    assert html.count("<ol") == 1


def test_children_outnumbering_parents_still_nest():
    # The run-local base comes from the outermost (first) item, not the most
    # frequent margin, so a sublist with more children than parents still nests
    # instead of clamping every item to level 0 (#194 review, finding 1).
    items = [
        ("block", _block("1. p-one", 0.0)),
        ("block", _block("2. p-two", 14.0)),
        ("block", _block("3. c1", 28.0, x0=90.0)),
        ("block", _block("4. c2", 42.0, x0=90.0)),
        ("block", _block("5. c3", 56.0, x0=90.0)),
    ]
    # Even when the profile's own base is the child margin, nesting holds.
    prof = mod.DocProfile(
        body_size=11.0,
        body_font="Body",
        heading_thresholds={1: 18.0, 2: 14.0, 3: 12.5},
        small_size=10.0,
        body_x0=72.0,
        list_base_x0=90.0,  # the dominant-child-margin trap
        indent_unit=18.0,
        nested_ordered_lists=True,
    )
    assert mod.assemble_markdown(items, prof) == (
        "1. p-one\n1. p-two\n    3. c1\n    1. c2\n    1. c3"
    )


def _mixed_profile():
    return mod.DocProfile(
        body_size=11.0,
        body_font="Body",
        heading_thresholds={1: 18.0, 2: 14.0, 3: 12.5},
        small_size=10.0,
        body_x0=72.0,
        list_base_x0=72.0,
        indent_unit=18.0,
        tight_loose_lists=True,
        nested_ordered_lists=True,
    )


def test_ordered_children_under_a_bullet_share_one_consistent_indent():
    # With both opt-ins on, every ordered child of a bullet parent takes the same
    # 4-space step in the same run, instead of the first child at 2 spaces and the
    # rest at 4 in a split run (#194 review, finding 2).
    items = [
        ("block", _block("• Parent", 0.0)),
        ("block", _block("1. child-a", 14.0, x0=90.0)),
        ("block", _block("2. child-b", 28.0, x0=90.0)),
    ]
    rendered = mod.assemble_markdown(items, _mixed_profile())
    lines = rendered.splitlines()
    child_lines = [ln for ln in lines if ln.lstrip().startswith(("1.", "2."))]
    assert len(child_lines) == 2
    assert all(ln.startswith("    ") and not ln.startswith("     ") for ln in child_lines)
    # It round-trips to one bullet list holding one nested ordered list.
    md_mod = md_to_pdf_module()
    html = md_mod.markdown.markdown(
        rendered, extensions=md_mod.MD_EXTENSIONS, output_format="html5"
    )
    assert html.count("<ul") == 1
    assert html.count("<ol") == 1
