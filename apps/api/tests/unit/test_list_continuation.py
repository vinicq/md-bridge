"""Unit coverage for multi-paragraph list items (#167).

Drives the pure `assemble_markdown` state machine through the API loader, then
re-parses the emitted Markdown with the same `markdown` library shipped in the
API. A paragraph block indented past a list item's marker must render as a
second <p> inside that <li>, not as a sibling block that splits the list.
"""
from __future__ import annotations

import markdown
from app.services.packages_loader import pdf_to_md_module

mod = pdf_to_md_module()


def _profile():
    return mod.DocProfile(
        body_size=11.0,
        body_font="Body",
        heading_thresholds={1: 18.0, 2: 14.0, 3: 12.5},
        small_size=10.0,
        body_x0=72.0,
        list_base_x0=72.0,
        indent_unit=18.0,
    )


def _block(text: str, x0: float, *, size: float = 11.0, font: str = "Body"):
    bbox = (x0, 0.0, x0 + 200.0, 10.0)
    span = mod.Span(text=text, size=size, font=font, flags=0, bbox=bbox)
    line = mod.Line(spans=[span], bbox=bbox)
    return mod.Block(lines=[line], bbox=bbox)


def test_bullet_continuation_nests_paragraph_in_item():
    items = [
        ("block", _block("• First bullet.", 72.0)),
        ("block", _block("Second paragraph still part of the first bullet.", 90.0)),
        ("block", _block("• Second bullet.", 72.0)),
    ]
    md = mod.assemble_markdown(items, _profile())

    # The renderer binds a continuation only at a 4-space indent, not column 0.
    assert "\n    Second paragraph still part of the first bullet." in md

    html = markdown.markdown(md)
    # One list, two items: the continuation did not open a second <ul>.
    assert html.count("<ul>") == 1
    assert html.count("<li>") == 2
    first_item = html.split("</li>")[0]
    assert "Second paragraph still part of the first bullet." in first_item


def test_numbered_continuation_nests_paragraph_in_item():
    items = [
        ("block", _block("1. First step.", 72.0)),
        ("block", _block("Detail under the first step.", 90.0)),
        ("block", _block("2. Second step.", 72.0)),
    ]
    md = mod.assemble_markdown(items, _profile())

    assert "\n    Detail under the first step." in md  # 4-space nest

    html = markdown.markdown(md)
    assert html.count("<ol>") == 1
    assert html.count("<li>") == 2
    first_item = html.split("</li>")[0]
    assert "Detail under the first step." in first_item


def test_unindented_paragraph_ends_the_list():
    items = [
        ("block", _block("• Bullet.", 72.0)),
        ("block", _block("A following body paragraph.", 72.0)),
    ]
    md = mod.assemble_markdown(items, _profile())

    # At body x0 the paragraph is a sibling block, not a continuation.
    assert "\nA following body paragraph." in md
    assert "  A following body paragraph." not in md

    html = markdown.markdown(md)
    assert html.count("<li>") == 1
    assert "<p>A following body paragraph.</p>" in html


def test_two_continuations_under_one_item():
    items = [
        ("block", _block("• Item.", 72.0)),
        ("block", _block("First continuation.", 90.0)),
        ("block", _block("Another continuation.", 90.0)),
    ]
    md = mod.assemble_markdown(items, _profile())

    html = markdown.markdown(md)
    assert html.count("<ul>") == 1
    assert html.count("<li>") == 1
    first_item = html.split("</li>")[0]
    assert "First continuation." in first_item
    assert "Another continuation." in first_item
