"""Unit coverage for renderer strikethrough + task lists (#143).

Drives python-markdown with the renderer's extensions through the loader
convert() uses. Pure, no Chromium.
"""
from __future__ import annotations

from app.services.packages_loader import md_to_pdf_module

mod = md_to_pdf_module()


def _render(md_text: str) -> str:
    return mod.markdown.markdown(md_text, extensions=mod.MD_EXTENSIONS, output_format="html5")


def test_strikethrough_renders_del():
    assert "<del>deprecated</del>" in _render("This is ~~deprecated~~ now.")


def test_single_tilde_is_not_strikethrough():
    assert "<del>" not in _render("a ~ b ~ c")


def test_strikethrough_wraps_emphasis():
    out = _render("~~**gone**~~")
    assert "<del>" in out and "<strong>gone</strong>" in out


def test_unchecked_task_item():
    out = _render("- [ ] todo")
    assert 'class="task-list-item"' in out
    assert 'type="checkbox"' in out
    assert "disabled" in out
    assert "checked" not in out
    assert "todo" in out


def test_checked_task_item():
    out = _render("- [x] done")
    assert 'class="task-list-item"' in out
    assert "checked" in out
    assert "done" in out


def test_uppercase_checked_marker():
    assert "checked" in _render("- [X] done")


def test_plain_list_item_is_untouched():
    out = _render("- normal item")
    assert "task-list-item" not in out
    assert "checkbox" not in out


def test_task_item_keeps_inline_markup():
    out = _render("- [x] finish **bold** part")
    assert "task-list-item" in out
    assert "<strong>bold</strong>" in out


def test_mixed_list_marks_only_task_items():
    out = _render("- [ ] task\n- plain")
    assert out.count("task-list-item") == 1
