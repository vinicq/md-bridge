"""Unit coverage for GFM alert callouts (#159).

Drives python-markdown with the renderer's extensions plus the callout extension
through the loader convert() uses. Pure, no Chromium. The transform runs entirely
at the HTML stage, so this exercises the whole feature short of the PDF print.
"""
from __future__ import annotations

import pytest
from app.services.packages_loader import md_to_pdf_module

mod = md_to_pdf_module()

TYPES = ["note", "tip", "important", "warning", "caution"]


def _render(md_text: str, lang: str = "en") -> str:
    exts = [*mod.MD_EXTENSIONS, mod._CalloutExtension(lang=lang)]
    return mod.markdown.markdown(md_text, extensions=exts, output_format="html5")


@pytest.mark.parametrize("kind", TYPES)
def test_each_alert_becomes_a_callout(kind: str):
    out = _render(f"> [!{kind.upper()}]\n> Body text.")
    assert f'class="callout callout--{kind}"' in out
    assert 'class="callout__head"' in out
    assert 'class="callout__icon"' in out
    assert 'class="callout__body"' in out
    assert "<p>Body text.</p>" in out
    # The marker itself must not leak into the rendered body.
    assert f"[!{kind.upper()}]" not in out


def test_english_labels():
    labels = {"note": "Note", "tip": "Tip", "important": "Important", "warning": "Warning", "caution": "Caution"}
    for kind, label in labels.items():
        out = _render(f"> [!{kind.upper()}]\n> x")
        assert f">{label}</div>" in out


def test_portuguese_and_spanish_labels():
    assert ">Aviso</div>" in _render("> [!WARNING]\n> x", lang="pt-BR")
    assert ">Atenção</div>" in _render("> [!CAUTION]\n> x", lang="pt-BR")
    assert ">Consejo</div>" in _render("> [!TIP]\n> x", lang="es")
    # An unmapped locale (de/fr/it) falls back to English.
    assert ">Note</div>" in _render("> [!NOTE]\n> x", lang="de")


def test_body_markdown_is_preserved():
    out = _render("> [!TIP]\n> Use **bold** and a [link](https://x.test).")
    assert "<strong>bold</strong>" in out
    assert '<a href="https://x.test">link</a>' in out


def test_multi_paragraph_body():
    out = _render("> [!NOTE]\n> First para.\n>\n> Second para.")
    assert out.count("<p>") >= 2
    assert "First para." in out and "Second para." in out


def test_plain_blockquote_is_untouched():
    out = _render("> just a normal quote")
    assert "<blockquote>" in out
    assert "callout" not in out


def test_marker_with_inline_text_is_not_an_alert():
    # GitHub only treats `[!TYPE]` as an alert when it sits alone on the first
    # line; text on the same line keeps it a plain blockquote.
    out = _render("> [!TIP] some inline text")
    assert "<blockquote>" in out
    assert "callout" not in out


def test_case_insensitive_marker():
    assert 'callout--warning' in _render("> [!warning]\n> x")


def test_icon_is_inline_svg_stroke_currentcolor():
    out = _render("> [!CAUTION]\n> x")
    assert '<svg class="callout__icon"' in out
    assert 'stroke="currentColor"' in out
