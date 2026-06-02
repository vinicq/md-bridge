"""Unit tests for the pdf-to-markdown heuristics that are easy to isolate.

These exercise pure-Python helpers without touching real PDFs:
  - classify_block
  - build_profile
  - merge_continued_paragraphs
  - normalize_headings_from_toc
"""
from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture(scope="module")
def mod(pdf_to_md_mod):
    return pdf_to_md_mod


def _make_block(mod, text: str, size: float, *, bold=False, x0=72.0, font="Body"):
    flags = (1 << 4) if bold else 0
    span = mod.Span(text=text, size=size, font=font, flags=flags, bbox=(x0, 0.0, x0 + 100, 12.0))
    line = mod.Line(spans=[span], bbox=(x0, 0.0, x0 + 100, size + 2))
    return mod.Block(lines=[line], bbox=(x0, 0.0, x0 + 100, size + 2))


def _profile(mod, body_size=11.0, body_font="Body"):
    return mod.DocProfile(
        body_size=body_size,
        body_font=body_font,
        heading_thresholds={1: 17.5, 2: 13.5, 3: 12.0},
        small_size=body_size - 1.0,
        body_x0=72.0,
        list_base_x0=72.0,
        indent_unit=18.0,
    )


def test_classify_block_heading_levels(mod):
    profile = _profile(mod)
    assert mod.classify_block(_make_block(mod, "Title 1", 24.0), profile) == "heading1"
    assert mod.classify_block(_make_block(mod, "Title 2", 14.0), profile) == "heading2"
    assert mod.classify_block(_make_block(mod, "Title 3", 12.5), profile) == "heading3"


def test_classify_block_bullet_and_numbered(mod):
    profile = _profile(mod)
    assert mod.classify_block(_make_block(mod, "- list item", 11.0), profile) != "bullet"
    bullet_block = _make_block(mod, "• a bullet", 11.0)
    assert mod.classify_block(bullet_block, profile) == "bullet"

    numbered = _make_block(mod, "1. first step", 11.0)
    assert mod.classify_block(numbered, profile) == "numbered"


def test_classify_block_small_text(mod):
    profile = _profile(mod)
    block = _make_block(mod, "footnote-ish caption", 9.5)
    assert mod.classify_block(block, profile) == "small"


def test_classify_block_paragraph_default(mod):
    profile = _profile(mod)
    block = _make_block(mod, "Just a normal sentence in the body.", 11.0)
    assert mod.classify_block(block, profile) == "paragraph"


def test_merge_continued_paragraphs_joins_lowercase_continuation(mod):
    md = "This sentence is\n\ncontinued on the next block."
    out = mod.merge_continued_paragraphs(md)
    assert out == "This sentence is continued on the next block."


def test_merge_continued_paragraphs_keeps_hard_breaks(mod):
    md = "Sentence ends.\n\nNew sentence starts."
    out = mod.merge_continued_paragraphs(md)
    assert out == md


def test_merge_continued_paragraphs_repairs_hyphenation(mod):
    md = "self-\n\nconfident author"
    out = mod.merge_continued_paragraphs(md)
    assert out == "selfconfident author"


def test_merge_does_not_fuse_a_page_footer_into_prose(mod):
    # #141: small-font footers now render as plain text. A running footer like
    # "v4.0 GA Page 3 of 77 2025/05/02" starts lowercase and would otherwise be
    # fused onto preceding prose that lacks terminal punctuation. The page-
    # furniture guard keeps it as its own block.
    md = "a paragraph that wraps without a period\n\nv4.0 GA Page 3 of 77 2025/05/02"
    out = mod.merge_continued_paragraphs(md)
    assert out == md  # untouched: the footer stays on its own line
    assert mod.is_block_paragraph("v4.0 GA Page 3 of 77 2025/05/02") is False
    assert mod.looks_like_page_furniture("Page 12 of 40") is True
    assert mod.looks_like_page_furniture("a normal sentence about a page") is False


def test_normalize_headings_from_toc_relevels(mod):
    md = "### 1 Motivation\n\nbody text"
    toc = [(1, "1 Motivation", 1)]
    out = mod.normalize_headings_from_toc(md, toc)
    assert out.startswith("# 1 Motivation")


def test_normalize_headings_from_toc_no_match_keeps_level(mod):
    md = "## Existing heading\n\nbody"
    toc = [(1, "Some Other Title", 1)]
    out = mod.normalize_headings_from_toc(md, toc)
    assert "## Existing heading" in out


def test_normalize_headings_from_toc_empty_returns_input(mod):
    md = "## h\n\nbody"
    assert mod.normalize_headings_from_toc(md, []) == md


def test_build_profile_on_real_pdf(mod):
    """Profile building against the committed ISTQB syllabus so every clone can
    exercise the real-PDF code path without dev-local fixtures."""
    import fitz

    pdf = Path(__file__).resolve().parents[2] / "apps" / "api" / "tests" / "fixtures" / "istqb-ctal-ta-syllabus-en.pdf"
    assert pdf.exists(), f"committed fixture missing: {pdf}"
    doc = fitz.open(pdf)
    profile = mod.build_profile(doc)
    doc.close()

    assert profile.body_size > 0
    assert profile.heading_thresholds[1] > profile.heading_thresholds[2] >= profile.heading_thresholds[3]
    assert profile.small_size < profile.body_size


# Code-block detection


FLAG_MONO_BIT = 1 << 3


def _span(mod, text: str, *, font: str = "Body", flags: int = 0, size: float = 11.0):
    return mod.Span(text=text, size=size, font=font, flags=flags, bbox=(72.0, 0.0, 200.0, size + 2))


def _multi_block(mod, spans_per_line, x0=72.0):
    lines = []
    for line_spans in spans_per_line:
        lines.append(mod.Line(spans=list(line_spans), bbox=(x0, 0.0, x0 + 200, 12.0)))
    return mod.Block(lines=lines, bbox=(x0, 0.0, x0 + 200, 12.0 * max(1, len(lines))))


def test_is_mono_span_detects_flag(mod):
    assert mod.is_mono_span(_span(mod, "x", flags=FLAG_MONO_BIT))


def test_is_mono_span_detects_courier_name(mod):
    assert mod.is_mono_span(_span(mod, "x", font="Courier"))
    assert mod.is_mono_span(_span(mod, "x", font="Consolas-Bold"))
    assert mod.is_mono_span(_span(mod, "x", font="JetBrainsMono-Regular"))


def test_is_mono_span_detects_modern_editor_fonts(mod):
    # Fira Code and Source Code Pro carry no "Mono" token, so they need their
    # own hints; the rest are covered for robustness.
    assert mod.is_mono_span(_span(mod, "x", font="FiraCode-Retina"))
    assert mod.is_mono_span(_span(mod, "x", font="SourceCodePro-Regular"))
    assert mod.is_mono_span(_span(mod, "x", font="RobotoMono-Regular"))
    assert mod.is_mono_span(_span(mod, "x", font="IBMPlexMono-Regular"))


def test_is_mono_span_rejects_proportional_siblings(mod):
    # Plex, Source, Fira and Roboto all ship proportional families. A hint
    # must not flag body text set in those as a code block.
    assert not mod.is_mono_span(_span(mod, "x", font="IBMPlexSans-Regular"))
    assert not mod.is_mono_span(_span(mod, "x", font="SourceSansPro-Regular"))
    assert not mod.is_mono_span(_span(mod, "x", font="FiraSans-Regular"))
    assert not mod.is_mono_span(_span(mod, "x", font="Roboto-Regular"))


def test_is_mono_span_rejects_serif(mod):
    assert not mod.is_mono_span(_span(mod, "x", font="TimesNewRoman"))


def test_mono_ratio_full_mono(mod):
    block = _multi_block(mod, [[_span(mod, "print('hi')", font="Courier")]])
    assert mod.mono_ratio(block) == 1.0


def test_mono_ratio_below_threshold_when_prose_dominates(mod):
    spans = [_span(mod, "a", font="Courier"), _span(mod, "bcdefghij", font="Body")]
    block = _multi_block(mod, [spans])
    # 1 mono / 10 total = 0.1
    assert mod.mono_ratio(block) == 0.1


def test_mono_ratio_zero_for_no_mono(mod):
    block = _multi_block(mod, [[_span(mod, "plain prose", font="Body")]])
    assert mod.mono_ratio(block) == 0.0


def test_classify_block_code_when_mono_dominant(mod):
    profile = _profile(mod)
    block = _multi_block(mod, [[_span(mod, "def foo():", font="Courier")]])
    assert mod.classify_block(block, profile) == "code"


def test_classify_block_paragraph_when_mono_below_threshold(mod):
    profile = _profile(mod)
    spans = [_span(mod, "x", font="Courier"), _span(mod, "y" * 9, font="Body")]
    block = _multi_block(mod, [spans])
    # 1/10 mono < 0.7 threshold
    assert mod.classify_block(block, profile) == "paragraph"


def test_classify_block_heading_wins_over_mono(mod):
    profile = _profile(mod)
    span = _span(mod, "Title in Mono", font="Courier", flags=FLAG_MONO_BIT, size=24.0)
    block = _multi_block(mod, [[span]])
    assert mod.classify_block(block, profile) == "heading1"


def test_detect_language_python(mod):
    assert mod.detect_language("def foo():\n    return 1") == "python"
    assert mod.detect_language("from pathlib import Path") == "python"


def test_detect_language_javascript(mod):
    assert mod.detect_language("function foo() { return 1 }") == "javascript"
    assert mod.detect_language("const x = 42") == "javascript"


def test_detect_language_sql(mod):
    assert mod.detect_language("SELECT id, name FROM users WHERE active = 1") == "sql"
    assert mod.detect_language("select * from accounts;") == "sql"


def test_detect_language_html(mod):
    assert mod.detect_language("<!DOCTYPE html>\n<html>") == "html"
    assert mod.detect_language("<html lang='en'>") == "html"


def test_detect_language_json(mod):
    assert mod.detect_language('{"name": "ok", "value": 1}') == "json"


def test_detect_language_empty_when_no_match(mod):
    assert mod.detect_language("just some prose here") == ""
    assert mod.detect_language("") == ""
