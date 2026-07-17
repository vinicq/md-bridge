"""Unit coverage for the ==highlight== -> <mark> renderer rule (#162).

Drives python-markdown with the renderer's MD_EXTENSIONS through the same loader
convert() uses. Pure, no Chromium. The pdf-to-markdown side emits ==text== from
PDF highlight annotations; this closes the round trip on the render side without
pulling in pymdown-extensions.
"""
from __future__ import annotations

from app.services.packages_loader import md_to_pdf_module

mod = md_to_pdf_module()


def _render(md_text: str) -> str:
    return mod.markdown.markdown(md_text, extensions=mod.MD_EXTENSIONS, output_format="html5")


def test_double_equals_renders_mark():
    assert "<mark>highlight</mark>" in _render("a ==highlight== b")


def test_emphasis_nests_inside_mark():
    out = _render("==**bold** text==")
    assert "<mark>" in out and "</mark>" in out
    assert "<strong>bold</strong>" in out


def test_single_equals_is_left_literal():
    # A lone `=` pair is not a mark; `x = y` must not sprout a <mark>.
    assert "<mark>" not in _render("x = y and a == b needs two pairs")


def test_mark_not_parsed_inside_code_span():
    # Inline code is literal: ==x== inside backticks stays as text, no <mark>.
    out = _render("`==x==`")
    assert "<mark>" not in out
    assert "==x==" in out
