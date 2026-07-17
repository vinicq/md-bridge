"""Unit coverage for pymdownx-style custom containers (#164).

`::: name` blocks map onto the five base callout types and render through the
same machinery as the GFM alerts (#159). Pure, no Chromium.
"""
from __future__ import annotations

import pytest
from app.services.packages_loader import md_to_pdf_module

mod = md_to_pdf_module()


def _render(md_text: str, lang: str = "en") -> str:
    exts = [*mod.MD_EXTENSIONS, mod._CalloutExtension(lang=lang)]
    return mod.markdown.markdown(md_text, extensions=exts, output_format="html5")


def test_container_becomes_callout():
    out = _render("::: warning\nWatch out.\n:::")
    assert 'class="callout callout--warning"' in out
    assert ">Warning</div>" in out
    assert "<p>Watch out.</p>" in out
    assert ":::" not in out


@pytest.mark.parametrize(
    "name,kind",
    [
        ("note", "note"),
        ("info", "important"),
        ("important", "important"),
        ("tip", "tip"),
        ("hint", "tip"),
        ("success", "tip"),
        ("warning", "warning"),
        ("attention", "warning"),
        ("caution", "caution"),
        ("danger", "caution"),
        ("error", "caution"),
    ],
)
def test_name_maps_to_base_type(name: str, kind: str):
    out = _render(f"::: {name}\nBody.\n:::")
    assert f"callout callout--{kind}" in out


def test_unknown_name_falls_back_to_note():
    out = _render("::: foo\nGeneric.\n:::")
    assert "callout callout--note" in out


def test_body_markdown_and_multiple_paragraphs():
    out = _render("::: tip\nUse **bold**.\n\nSecond paragraph.\n:::")
    assert "<strong>bold</strong>" in out
    assert out.count("<p>") >= 2


def test_container_inside_code_fence_is_untouched():
    out = _render("```\n::: warning\ncode\n:::\n```")
    assert "callout" not in out
    assert "::: warning" in out


def test_stray_opener_without_closer_stays_literal():
    out = _render("::: warning\nno closing fence here")
    assert "callout" not in out
    assert "::: warning" in out


def test_localized_label_via_shared_machinery():
    assert ">Aviso</div>" in _render("::: warning\nx\n:::", lang="pt-BR")
    assert ">Precaución</div>" in _render("::: danger\nx\n:::", lang="es")
