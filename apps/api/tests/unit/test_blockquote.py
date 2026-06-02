"""Unit coverage for blockquote detection (#147).

Drives the pure `assemble_markdown` state machine through the API loader, then
re-parses the emitted Markdown with the `markdown` library shipped in the API.
Two things matter: a standalone inset block renders as a <blockquote>, and an
inset block under an OPEN LIST stays a list continuation (#167/#197 precedence)
rather than turning into a quote.
"""
from __future__ import annotations

import markdown
from app.services.packages_loader import pdf_to_md_module

mod = pdf_to_md_module()


def _profile(*, detect_blockquotes: bool = False):
    return mod.DocProfile(
        body_size=11.0,
        body_font="Body",
        heading_thresholds={1: 18.0, 2: 14.0, 3: 12.5},
        small_size=10.0,
        body_x0=72.0,
        list_base_x0=72.0,
        indent_unit=18.0,
        detect_blockquotes=detect_blockquotes,
    )


def _block(text: str, x0: float, *, size: float = 11.0, font: str = "Body"):
    bbox = (x0, 0.0, x0 + 200.0, 10.0)
    span = mod.Span(text=text, size=size, font=font, flags=0, bbox=bbox)
    line = mod.Line(spans=[span], bbox=bbox)
    return mod.Block(lines=[line], bbox=bbox)


def test_standalone_inset_block_renders_as_blockquote():
    # body_x0=72, indent_unit=18 -> threshold 90; the block sits at 108.
    items = [("block", _block("A quoted passage standing on its own.", 108.0))]
    md = mod.assemble_markdown(items, _profile(detect_blockquotes=True))

    assert md.startswith("> ")
    html = markdown.markdown(md)
    assert "<blockquote>" in html
    assert "A quoted passage standing on its own." in html


def test_inset_block_stays_paragraph_when_flag_off():
    items = [("block", _block("A quoted passage standing on its own.", 108.0))]
    md = mod.assemble_markdown(items, _profile())

    assert ">" not in md
    html = markdown.markdown(md)
    assert "<blockquote>" not in html
    assert "<p>A quoted passage standing on its own.</p>" in html


def test_inset_block_under_open_list_is_continuation_not_quote():
    # The critical anti-regression: with the flag ON, an indented body block
    # under an open list item is item content (#167), never a pull quote. List
    # continuation wins, so no `>` marker appears and the list stays intact.
    items = [
        ("block", _block("• First bullet.", 72.0)),
        ("block", _block("An inset line that could be mistaken for a quote.", 108.0)),
        ("block", _block("• Second bullet.", 72.0)),
    ]
    md = mod.assemble_markdown(items, _profile(detect_blockquotes=True))

    assert ">" not in md
    html = markdown.markdown(md)
    assert "<blockquote>" not in html
    assert html.count("<ul>") == 1
    assert html.count("<li>") == 2
    first_item = html.split("</li>")[0]
    assert "inset line that could be mistaken for a quote" in first_item


# --- #174: multi-paragraph quotes ---------------------------------------------


def test_two_consecutive_quote_blocks_become_one_blockquote():
    items = [
        ("block", _block("First paragraph of the quote.", 108.0)),
        ("block", _block("Second paragraph of the quote.", 108.0)),
    ]
    md = mod.assemble_markdown(items, _profile(detect_blockquotes=True))

    # CommonMark 5.1: a bare `>` line separates the two quoted paragraphs.
    assert "> First paragraph of the quote.\n>\n> Second paragraph of the quote." in md
    html = markdown.markdown(md)
    assert html.count("<blockquote>") == 1
    quote = html.split("<blockquote>")[1].split("</blockquote>")[0]
    assert quote.count("<p>") == 2


def test_quote_run_terminated_by_paragraph_stays_one_blockquote():
    items = [
        ("block", _block("Quote line one.", 108.0)),
        ("block", _block("Quote line two.", 108.0)),
        ("block", _block("A following body paragraph at the margin.", 72.0)),
    ]
    md = mod.assemble_markdown(items, _profile(detect_blockquotes=True))
    html = markdown.markdown(md)

    assert html.count("<blockquote>") == 1
    assert html.split("</blockquote>")[0].count("<p>") == 2
    after = html.split("</blockquote>")[1]
    assert "<p>A following body paragraph at the margin.</p>" in after


def test_quote_run_terminated_by_heading():
    items = [
        ("block", _block("A quoted sentence before the heading.", 108.0)),
        ("block", _block("A Heading", 72.0, size=18.0)),
    ]
    md = mod.assemble_markdown(items, _profile(detect_blockquotes=True))
    html = markdown.markdown(md)

    assert html.count("<blockquote>") == 1
    assert "<h1>A Heading</h1>" in html


def test_quote_run_interrupted_by_paragraph_then_resumes():
    # The clear-on-flush guard: the resumed run must not fuse with the first.
    items = [
        ("block", _block("First quote, standing alone.", 108.0)),
        ("block", _block("A normal paragraph breaks the run.", 72.0)),
        ("block", _block("Resumed quote, paragraph one.", 108.0)),
        ("block", _block("Resumed quote, paragraph two.", 108.0)),
    ]
    md = mod.assemble_markdown(items, _profile(detect_blockquotes=True))
    html = markdown.markdown(md)

    assert html.count("<blockquote>") == 2
    assert html.split("</blockquote>")[0].count("<p>") == 1
    second = html.split("<blockquote>")[2].split("</blockquote>")[0]
    assert second.count("<p>") == 2


def test_quote_before_list_stays_separate_from_continuation():
    # A quote run closes before a list opens (flush site), and the list
    # continuation that follows binds to the item, never to the quote.
    items = [
        ("block", _block("A standalone quote.", 108.0)),
        ("block", _block("• A bullet item.", 72.0)),
        ("block", _block("Indented continuation of the bullet.", 108.0)),
    ]
    md = mod.assemble_markdown(items, _profile(detect_blockquotes=True))
    html = markdown.markdown(md)

    assert html.count("<blockquote>") == 1
    assert html.count("<ul>") == 1
    assert html.count("<li>") == 1
    assert "Indented continuation" not in html.split("</blockquote>")[0]
    assert "Indented continuation of the bullet." in html.split("<li>")[1]


def test_multi_paragraph_quote_inert_when_flag_off():
    items = [
        ("block", _block("First paragraph of the quote.", 108.0)),
        ("block", _block("Second paragraph of the quote.", 108.0)),
    ]
    md = mod.assemble_markdown(items, _profile())

    assert ">" not in md
    html = markdown.markdown(md)
    assert "<blockquote>" not in html
    assert html.count("<p>") == 2
