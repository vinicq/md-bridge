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


# --- #188: font-size clustering for heading bands ----------------------------


def _level(mod, thresholds, size):
    p = _profile(mod)
    p.heading_thresholds = thresholds
    return p.heading_level(size)


def test_cluster_bands_single_size_above_body(mod):
    th = mod.cluster_heading_bands({11.0: 1000, 16.0: 50}, 11.0)
    assert _level(mod, th, 16.0) == 1
    assert _level(mod, th, 11.0) is None


def test_cluster_bands_two_sizes(mod):
    th = mod.cluster_heading_bands({11.0: 1000, 14.0: 30, 20.0: 20}, 11.0)
    assert _level(mod, th, 20.0) == 1
    assert _level(mod, th, 14.0) == 2
    assert _level(mod, th, 13.0) is None


def test_cluster_bands_close_siblings_share_level(mod):
    # The bug this fixes: 12.8 and 13.0 sit a hair apart and must land in the
    # same band, not be split by a fixed cutoff.
    th = mod.cluster_heading_bands({11.0: 1000, 12.8: 40, 13.0: 40, 20.0: 20}, 11.0)
    assert _level(mod, th, 12.8) == _level(mod, th, 13.0)
    assert _level(mod, th, 20.0) == 1
    assert _level(mod, th, 13.0) == 2


def test_cluster_bands_caps_at_three(mod):
    th = mod.cluster_heading_bands(
        {11.0: 1000, 13.0: 10, 16.0: 10, 22.0: 10, 28.0: 10, 34.0: 10}, 11.0
    )
    levels = {_level(mod, th, s) for s in (34.0, 28.0, 22.0, 16.0, 13.0)}
    assert None not in levels
    assert levels <= {1, 2, 3}
    assert _level(mod, th, 34.0) == 1


def test_cluster_bands_deterministic(mod):
    hist = {11.0: 1000, 14.0: 10, 20.0: 10, 26.0: 10}
    outs = [mod.cluster_heading_bands(hist, 11.0) for _ in range(5)]
    assert all(o == outs[0] for o in outs)


def test_cluster_bands_no_sizes_above_body(mod):
    th = mod.cluster_heading_bands({11.0: 1000}, 11.0)
    assert set(th) == {1, 2, 3}
    assert _level(mod, th, 11.0) is None


def test_heading_run_merges_same_level_consecutive(mod):
    profile = _profile(mod)
    profile.cluster_headings = True
    items = [
        ("block", _make_block(mod, "Test Analysis and Design", 14.0)),
        ("block", _make_block(mod, "Techniques", 14.0)),
    ]
    assert mod.assemble_markdown(items, profile) == "## Test Analysis and Design Techniques"


def test_heading_run_different_level_not_merged(mod):
    profile = _profile(mod)
    profile.cluster_headings = True
    items = [
        ("block", _make_block(mod, "Big Title", 24.0)),
        ("block", _make_block(mod, "Subsection", 14.0)),
    ]
    assert mod.assemble_markdown(items, profile) == "# Big Title\n\n## Subsection"


def test_heading_run_broken_by_body_block(mod):
    profile = _profile(mod)
    profile.cluster_headings = True
    items = [
        ("block", _make_block(mod, "First Heading", 14.0)),
        ("block", _make_block(mod, "Body sentence sitting in between the two.", 11.0)),
        ("block", _make_block(mod, "Second Heading", 14.0)),
    ]
    md = mod.assemble_markdown(items, profile)
    assert "## First Heading" in md
    assert "## Second Heading" in md
    assert "First Heading Second Heading" not in md


def test_heading_run_off_by_default(mod):
    profile = _profile(mod)  # cluster_headings defaults False
    items = [
        ("block", _make_block(mod, "Test Analysis and Design", 14.0)),
        ("block", _make_block(mod, "Techniques", 14.0)),
    ]
    assert mod.assemble_markdown(items, profile) == "## Test Analysis and Design\n\n## Techniques"


def _multiline_block(mod, lines_x0, *, size=11.0, font="Body"):
    """Block whose lines each carry their own x0, to model sustained indent
    (all lines inset) versus a first-line-only indent (a normal paragraph)."""
    lines = []
    for text, x0 in lines_x0:
        bbox = (x0, 0.0, x0 + 100, size + 2)
        span = mod.Span(text=text, size=size, font=font, flags=0, bbox=bbox)
        lines.append(mod.Line(spans=[span], bbox=bbox))
    block_x0 = min(x0 for _, x0 in lines_x0)
    return mod.Block(lines=lines, bbox=(block_x0, 0.0, block_x0 + 100, (size + 2) * len(lines)))


def test_classify_blockquote_sustained_indent_when_enabled(mod):
    # body_x0=72, indent_unit=18 -> threshold 90; both lines sit at 108.
    profile = _profile(mod)
    profile.detect_blockquotes = True
    block = _multiline_block(mod, [("A quoted passage that", 108.0), ("runs across two lines.", 108.0)])
    assert mod.classify_block(block, profile) == "blockquote"


def test_classify_blockquote_off_by_default(mod):
    # Same inset block, flag left at its default: stays a plain paragraph.
    profile = _profile(mod)
    block = _multiline_block(mod, [("A quoted passage that", 108.0), ("runs across two lines.", 108.0)])
    assert mod.classify_block(block, profile) == "paragraph"


def test_classify_blockquote_first_line_indent_only_stays_paragraph(mod):
    # A first-line indent is how ordinary paragraphs start; only the first line
    # is inset, so it must not read as a quote even with the flag on.
    profile = _profile(mod)
    profile.detect_blockquotes = True
    block = _multiline_block(mod, [("First line is indented,", 108.0), ("the rest sits at margin.", 72.0)])
    assert mod.classify_block(block, profile) == "paragraph"


def test_classify_blockquote_does_not_steal_bullets(mod):
    # An inset bullet is still a bullet: the bullet check precedes the quote one.
    profile = _profile(mod)
    profile.detect_blockquotes = True
    block = _multiline_block(mod, [("• an inset bullet", 108.0)])
    assert mod.classify_block(block, profile) == "bullet"


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


def test_detect_language_bash(mod):
    assert mod.detect_language("#!/bin/bash\necho hi") == "bash"
    assert mod.detect_language("#!/usr/bin/env bash\nset -e") == "bash"
    assert mod.detect_language("$ git push origin main") == "bash"
    # A bare builtin in prose must not register as bash.
    assert mod.detect_language("cd into the project folder and run it") == ""


def test_detect_language_dockerfile(mod):
    df = "FROM python:3.12-slim\nRUN pip install .\nCMD [\"app\"]"
    assert mod.detect_language(df) == "dockerfile"
    # FROM alone (prose) without a second instruction does not register.
    assert mod.detect_language("FROM the very beginning of the story") == ""


def test_detect_language_go(mod):
    assert mod.detect_language("package main\n\nfunc main() {}") == "go"
    assert mod.detect_language("func handler(w http.ResponseWriter) {}") == "go"
    # Prose starting with "package" must not register.
    assert mod.detect_language("package the files before shipping them") == ""


def test_detect_language_rust(mod):
    assert mod.detect_language("fn main() {\n    let mut x = 1;\n}") == "rust"
    assert mod.detect_language("pub fn add(a: i32) -> i32 { a }") == "rust"
    assert mod.detect_language("use std::collections::HashMap;") == "rust"


def test_detect_language_typescript(mod):
    assert mod.detect_language("interface User {\n  name: string\n}") == "typescript"
    assert mod.detect_language("type Id = number") == "typescript"
    # "interface" as a prose word must not register.
    assert mod.detect_language("interface with the legacy system carefully") == ""


def test_detect_language_yaml(mod):
    assert mod.detect_language("---\nname: build\non: push") == "yaml"
    assert mod.detect_language("name: build\nversion: 1.0") == "yaml"
    # A single "key: value"-looking prose line does not register.
    assert mod.detect_language("Note: see the appendix for details") == ""


def test_detect_language_empty_when_no_match(mod):
    assert mod.detect_language("just some prose here") == ""
    assert mod.detect_language("") == ""
    # Prose that brushes the new rules must still fall through to no language.
    assert mod.detect_language("Warning: this section is long but readable") == ""
