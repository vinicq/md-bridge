"""Unit tests for the GFM task-list normalization post-pass (#172).

Pure string transform, covered cross-platform. End-to-end propagation through
the converter is in tests/integration/test_task_lists.py.
"""
from __future__ import annotations

import pytest
from app.services.packages_loader import pdf_to_md_module


@pytest.fixture(scope="module")
def norm():
    return pdf_to_md_module()._normalize_task_lists


def test_default_output_is_unchanged_without_checkboxes(norm):
    src = "- Buy milk\n- Ship it\n\nA plain paragraph."
    assert norm(src, extended=False) == src


@pytest.mark.parametrize("glyph", ["☐", "□", "▢"])
def test_unchecked_glyphs_map_to_empty_box(norm, glyph):
    assert norm(f"{glyph} Buy milk", extended=False) == "- [ ] Buy milk"


@pytest.mark.parametrize("glyph", ["☑", "☒", "✓", "✔", "✗", "✘"])
def test_checked_glyphs_map_to_checked_box(norm, glyph):
    assert norm(f"{glyph} Buy milk", extended=False) == "- [x] Buy milk"


def test_glyph_after_an_existing_bullet_marker(norm):
    assert norm("- ☐ Buy milk", extended=False) == "- [ ] Buy milk"
    assert norm("* ☑ Ship it", extended=False) == "- [x] Ship it"


@pytest.mark.parametrize("bullet_glyph", ["▪", "■", "•", "●", "◦"])
def test_bullet_glyphs_are_not_treated_as_checkboxes(norm, bullet_glyph):
    # These are list markers, not checkboxes; a bullet list must never become a
    # checklist. The line is left exactly as-is.
    src = f"{bullet_glyph} a normal bullet"
    assert norm(src, extended=False) == src


def test_ocr_bracket_forms_are_canonicalized(norm):
    assert norm("[ ] Buy milk", extended=False) == "- [ ] Buy milk"
    assert norm("[x] Buy milk", extended=False) == "- [x] Buy milk"
    assert norm("[X] Buy milk", extended=False) == "- [x] Buy milk"


def test_backslash_escaped_brackets_are_canonicalized(norm):
    # The converter escapes literal `[`/`]` in body text, so an OCR'd checkbox
    # reaches this pass as `\[ \]` / `\[x\]`.
    assert norm(r"\[ \] Buy milk", extended=False) == "- [ ] Buy milk"
    assert norm(r"\[x\] Ship it", extended=False) == "- [x] Ship it"


def test_already_canonical_task_items_are_idempotent(norm):
    src = "- [ ] Buy milk\n- [x] Ship it"
    assert norm(src, extended=False) == src


def test_in_progress_marker_only_in_extended_mode(norm):
    assert norm("[-] Buy milk", extended=False) == "[-] Buy milk"
    assert norm("[-] Buy milk", extended=True) == "- [-] Buy milk"


def test_fenced_code_block_is_untouched(norm):
    src = "```\n☐ not a checkbox here\n```\n☑ real one"
    out = norm(src, extended=False)
    assert "☐ not a checkbox here" in out  # inside the fence, unchanged
    assert out.endswith("- [x] real one")


def test_blockquote_is_untouched(norm):
    src = "> ☐ quoted, not a task"
    assert norm(src, extended=False) == src
