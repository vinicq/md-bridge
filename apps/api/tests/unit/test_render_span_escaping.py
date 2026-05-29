"""Unit coverage for the Markdown literal escaping in the converter (#155).

Loads the vendored converter through the same loader the API uses and drives
`escape_markdown_inline` and `render_span` directly. Pure functions, no fitz.
"""
from __future__ import annotations

from app.services.packages_loader import pdf_to_md_module

mod = pdf_to_md_module()
Span = mod.Span


def span(text: str, font: str = "Arial", flags: int = 0) -> object:
    return Span(text=text, size=10.0, font=font, flags=flags)


def test_escape_inline_covers_the_dangerous_set():
    assert mod.escape_markdown_inline("5 * 3 = 15") == r"5 \* 3 = 15"
    assert mod.escape_markdown_inline("my_var_name") == r"my\_var\_name"
    assert mod.escape_markdown_inline("[NOTE]") == r"\[NOTE\]"
    assert mod.escape_markdown_inline("a`b") == r"a\`b"
    # A literal backslash is doubled so it renders as one backslash.
    assert mod.escape_markdown_inline("a\\b") == r"a\\b"


def test_render_span_escapes_plain_prose():
    assert mod.render_span(span("5 * 3 = 15")) == r"5 \* 3 = 15"
    assert mod.render_span(span("my_var_name")) == r"my\_var\_name"


def test_render_span_escapes_before_wrapping_italic():
    # A font name carrying "Italic" makes the span italic; the literal asterisk
    # is escaped and only the emphasis markers we add stay live.
    assert mod.render_span(span("5 * 3", font="Italic")) == r"*5 \* 3*"


def test_render_span_does_not_escape_inside_a_code_span():
    # A mono font is wrapped in backticks; code content is literal, so the
    # underscore must NOT be escaped inside it.
    assert mod.render_span(span("a_b", font="Courier")) == "`a_b`"


def test_render_span_mono_with_backtick_falls_back_to_escaped_prose():
    # A single-backtick code span cannot contain a literal backtick, so a mono
    # span whose text already has one degrades to escaped prose instead of
    # emitting a broken code span.
    out = mod.render_span(span("a`b", font="Courier"))
    assert out == r"a\`b"
