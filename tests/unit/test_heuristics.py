"""Unit tests for the pdf-to-markdown heuristics that are easy to isolate.

These exercise pure-Python helpers without touching real PDFs:
  - classify_block
  - build_profile
  - merge_continued_paragraphs
  - normalize_headings_from_toc
"""
from __future__ import annotations

from dataclasses import dataclass

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


def test_build_profile_on_real_pdf(mod, fixtures_dir):
    import fitz

    pdf = fixtures_dir / "ddp-factsheet-en.pdf"
    if not pdf.exists():
        pytest.skip("fixture not present")
    doc = fitz.open(pdf)
    profile = mod.build_profile(doc)
    doc.close()

    assert profile.body_size > 0
    assert profile.heading_thresholds[1] > profile.heading_thresholds[2] >= profile.heading_thresholds[3]
    assert profile.small_size < profile.body_size
