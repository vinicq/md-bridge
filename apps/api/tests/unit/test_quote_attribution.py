"""Unit tests for quote attribution pairing (#173).

The pairing is a pure str->str post-pass, covered here cross-platform.
"""
from __future__ import annotations

from app.services.packages_loader import pdf_to_md_module


def test_attribution_folds_into_blockquote():
    mod = pdf_to_md_module()
    md = "> The unexamined life is not worth living.\n\n— Socrates"
    assert mod._pair_quote_attribution(md) == (
        "> The unexamined life is not worth living.\n>\n> — Socrates"
    )


def test_attribution_en_dash_and_double_hyphen_variants():
    mod = pdf_to_md_module()
    assert mod._pair_quote_attribution("> q\n\n– Author").endswith("> – Author")
    assert mod._pair_quote_attribution("> q\n\n-- Author").endswith("> -- Author")


def test_no_blockquote_is_noop():
    mod = pdf_to_md_module()
    md = "Just a paragraph.\n\n— not attached to any quote"
    assert mod._pair_quote_attribution(md) == md


def test_attribution_only_when_standalone_paragraph():
    # The dash line is followed by more body text, so it is not a standalone
    # attribution and must not be folded into the quote.
    mod = pdf_to_md_module()
    md = "> q\n\n— a dash that starts a sentence\nand keeps going"
    assert mod._pair_quote_attribution(md) == md


def test_multiparagraph_quote_keeps_internal_separators():
    mod = pdf_to_md_module()
    md = "> para one\n>\n> para two\n\n— Author"
    out = mod._pair_quote_attribution(md)
    assert out == "> para one\n>\n> para two\n>\n> — Author"


def test_page_break_separator_is_not_folded():
    # A `---` page separator (or any thematic break) after a quote must not be
    # swallowed as an attribution, even though it starts with a dash run.
    mod = pdf_to_md_module()
    for sep in ("---", "***", "___", "- - -"):
        md = f"> quote ending a page\n\n{sep}\n\nnext page"
        assert mod._pair_quote_attribution(md) == md


def test_quote_inside_fenced_code_is_not_folded():
    # A `>` line and a dash line living inside a fence are a code sample, not a
    # blockquote with an attribution, and must pass through untouched.
    mod = pdf_to_md_module()
    md = "```\n> sample quote\n\n— inside the fence\n```"
    assert mod._pair_quote_attribution(md) == md
