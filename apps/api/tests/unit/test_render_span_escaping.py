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


def test_render_span_superscript_emits_caret_not_html():
    # #141: a superscript span renders as Pandoc `^x^`, not raw <sup>.
    out = mod.render_span(span("2", flags=mod.FLAG_SUPERSCRIPT))
    assert out == "^2^"
    assert "<sup>" not in out


def test_render_span_leaves_literal_caret_bare():
    # A literal caret in prose stays bare: `^` is inert in the shipped renderer,
    # so escaping it would only leak a backslash to plain-Markdown consumers
    # without preventing any real misparse (#141).
    assert mod.render_span(span("25^C")) == "25^C"


def test_render_span_strikethrough_wraps_in_tildes():
    # #142: a struck span renders as GFM ~~...~~.
    assert mod.render_span(Span(text="gone", size=10.0, font="Arial", flags=0, is_strikethrough=True)) == "~~gone~~"


def test_render_span_strikethrough_nests_outside_emphasis():
    # Canonical nested order is ~~**text**~~ (strikethrough wraps the emphasis).
    bold = Span(text="gone", size=10.0, font="Arial-Bold", flags=0, is_strikethrough=True)
    assert mod.render_span(bold) == "~~**gone**~~"
    both = Span(text="gone", size=10.0, font="Bold-Italic", flags=0, is_strikethrough=True)
    assert mod.render_span(both) == "~~***gone***~~"


def test_render_span_without_strikethrough_has_no_tildes():
    assert "~~" not in mod.render_span(span("plain text"))


def test_render_span_highlight_wraps_in_double_equals():
    # #162: a highlighted span renders as pymdownx-mark ==...==.
    s = Span(text="key point", size=10.0, font="Arial", flags=0, is_highlight=True)
    assert mod.render_span(s) == "==key point=="


def test_render_span_highlight_nests_outside_emphasis():
    # Highlight wraps the emphasis: ==*text*== (italic here from the font name).
    s = Span(text="foo", size=10.0, font="Italic", flags=0, is_highlight=True)
    assert mod.render_span(s) == "==*foo*=="


def test_render_span_highlight_wraps_strikethrough():
    # Canonical nested order is ==~~text~~== (highlight outermost of the markers).
    s = Span(text="foo", size=10.0, font="Arial", flags=0, is_strikethrough=True, is_highlight=True)
    assert mod.render_span(s) == "==~~foo~~=="


def test_render_span_without_highlight_has_no_double_equals():
    assert "==" not in mod.render_span(span("plain text"))


def test_render_line_does_not_merge_highlighted_with_plain():
    # Adjacent spans of differing highlight state must stay separate, or a single
    # ==...== would swallow the unmarked text.
    Line = mod.Line
    marked = Span(text="marked ", size=10.0, font="Arial", flags=0, is_highlight=True)
    plain = Span(text="plain", size=10.0, font="Arial", flags=0, is_highlight=False)
    out = mod.render_line(Line(spans=[marked, plain], bbox=(0, 0, 10, 10)))
    assert out == "==marked== plain"


def test_render_line_does_not_merge_struck_with_unstruck():
    # Adjacent spans of differing strikethrough state must stay separate, or a
    # single ~~...~~ would swallow the unstruck text.
    Line = mod.Line
    struck = Span(text="deleted ", size=10.0, font="Arial", flags=0, is_strikethrough=True)
    kept = Span(text="kept", size=10.0, font="Arial", flags=0, is_strikethrough=False)
    out = mod.render_line(Line(spans=[struck, kept], bbox=(0, 0, 10, 10)))
    assert out == "~~deleted~~ kept"


# --- #202: a full-width rule crossing text must not be read as a strike ---


def test_strikethrough_confirmed_local_stroke_is_a_real_strike():
    # A stroke spanning roughly the struck word, within its x-range.
    span_bbox = (50.0, 70.0, 93.0, 85.0)
    strokes = [(76.0, 50.0, 95.0)]
    assert mod.strikethrough_confirmed(span_bbox, strokes) is True


def test_strikethrough_confirmed_rejects_overrunning_rule():
    # A full-width page rule overruns the span toward both margins.
    span_bbox = (50.0, 150.0, 207.0, 168.0)
    strokes = [(157.0, 20.0, 400.0)]
    assert mod.strikethrough_confirmed(span_bbox, strokes) is False


def test_strikethrough_confirmed_rejects_single_margin_overrun():
    # A stroke that overruns only one side (starts at the span but runs far
    # past the right margin) is still a rule, not a strike.
    span_bbox = (50.0, 150.0, 120.0, 168.0)
    strokes = [(157.0, 50.0, 400.0)]
    assert mod.strikethrough_confirmed(span_bbox, strokes) is False


def test_strikethrough_confirmed_trusts_flag_when_no_geometry():
    # No drawing evidence (e.g. get_drawings returned nothing): keep the flag.
    span_bbox = (50.0, 70.0, 93.0, 85.0)
    assert mod.strikethrough_confirmed(span_bbox, []) is True


def test_strikethrough_confirmed_ignores_strokes_off_the_band():
    # A stroke well above/below the span's vertical band does not count.
    span_bbox = (50.0, 70.0, 93.0, 85.0)
    strokes = [(40.0, 50.0, 95.0)]
    assert mod.strikethrough_confirmed(span_bbox, strokes) is True


def test_render_span_mono_with_backtick_falls_back_to_escaped_prose():
    # A single-backtick code span cannot contain a literal backtick, so a mono
    # span whose text already has one degrades to escaped prose instead of
    # emitting a broken code span.
    out = mod.render_span(span("a`b", font="Courier"))
    assert out == r"a\`b"


def test_is_mono_span_excludes_glyph_less_font():
    # GlyphLessFont is PyMuPDF's internal placeholder for unresolvable glyphs.
    # It carries FLAG_MONO (it IS a fixed-pitch fallback) but is NOT real code
    # content. A block of GlyphLessFont spans must not become a code fence.
    s = span("hello", font="GlyphLessFont", flags=mod.FLAG_MONO)
    assert mod.is_mono_span(s) is False


# --- #192: line-start block markers in literal prose get escaped ---


def test_escape_line_start_heading():
    assert mod.escape_line_start_specials("# not a heading") == r"\# not a heading"


def test_escape_line_start_bullet_markers():
    assert mod.escape_line_start_specials("- not a bullet") == r"\- not a bullet"
    assert mod.escape_line_start_specials("+ not a bullet") == r"\+ not a bullet"
    assert mod.escape_line_start_specials("* not a bullet") == r"\* not a bullet"


def test_escape_line_start_blockquote():
    assert mod.escape_line_start_specials("> not a quote") == r"\> not a quote"


def test_escape_line_start_ordered_list_dot_and_paren():
    # Only the punctuation that triggers the list is escaped; the digit stays.
    assert mod.escape_line_start_specials("1. not a list") == r"1\. not a list"
    assert mod.escape_line_start_specials("3) not a list") == r"3\) not a list"
    assert mod.escape_line_start_specials("12. still prose") == r"12\. still prose"


def test_escape_line_start_tolerates_up_to_three_leading_spaces():
    # CommonMark allows up to three spaces before a block marker, so a marker
    # behind that much indent still needs escaping.
    assert mod.escape_line_start_specials("   # indented") == r"   \# indented"


def test_escape_line_start_leaves_plain_prose_untouched():
    # No leading marker: the line is returned byte-identical (default path).
    assert mod.escape_line_start_specials("ordinary prose line") == "ordinary prose line"
    # A hyphen glued to a word is not a bullet (no following space).
    assert mod.escape_line_start_specials("-fast option") == "-fast option"
    # A digit not followed by list punctuation is not a list.
    assert mod.escape_line_start_specials("2024 was a year") == "2024 was a year"
    # A four-space indent is a code block, not a paragraph; leave it alone.
    assert mod.escape_line_start_specials("    # deep") == "    # deep"


def test_escape_line_start_applies_per_line():
    # A hard-broken paragraph (#156) gets each physical line checked.
    src = "First line\n- second looks like a bullet"
    assert mod.escape_line_start_specials(src) == "First line\n\\- second looks like a bullet"


def test_escape_line_start_only_escapes_the_leading_marker():
    # An inner `#` or `-` is untouched; only the line-start one is escaped.
    assert mod.escape_line_start_specials("# a - b # c") == r"\# a - b # c"
