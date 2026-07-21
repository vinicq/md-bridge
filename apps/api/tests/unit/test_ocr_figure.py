"""Unit coverage for the `::: ocr` provenance figure in the renderer (#140).

Drives python-markdown with the renderer extensions plus the callout extension
(which registers the OCR preprocessor). Pure, no Chromium.
"""
from __future__ import annotations

import pytest
from app.services.packages_loader import md_to_pdf_module

mod = md_to_pdf_module()


def _render(md_text: str, lang: str = "pt-BR") -> str:
    exts = [*mod.MD_EXTENSIONS, mod._CalloutExtension(lang=lang)]
    return mod.markdown.markdown(md_text, extensions=exts, output_format="html5")


def test_ocr_container_becomes_a_figure_not_a_callout():
    out = _render("::: ocr\nlinha 1\nlinha 2\n:::")
    assert '<figure class="ocr">' in out
    assert 'class="ocr__label"' in out and 'class="ocr__body"' in out
    assert "linha 1\nlinha 2" in out  # OCR line breaks preserved verbatim
    # Guard: the generic container preprocessor did not swallow `ocr` into a NOTE.
    assert "[!NOTE]" not in out and "callout" not in out


def test_ocr_body_is_literal_not_reparsed_markdown():
    out = _render("::: ocr\n# not a heading\n- not a list\n:::", lang="en")
    assert "<h1" not in out and "<li>" not in out
    assert "# not a heading\n- not a list" in out


def test_ocr_body_is_html_escaped():
    out = _render("::: ocr\n<script>x</script> & <b>\n:::", lang="es")
    assert "<script>" not in out
    assert "&lt;script&gt;" in out and "&amp;" in out


@pytest.mark.parametrize(
    ("lang", "label"),
    [("pt-BR", "Texto reconhecido (OCR)"), ("en", "Recognized text (OCR)"), ("es", "Texto reconocido (OCR)")],
)
def test_ocr_label_is_localized(lang: str, label: str):
    assert label in _render("::: ocr\nx\n:::", lang=lang)
