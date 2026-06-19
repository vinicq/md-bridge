"""Unit tests for the image-caption alt-text sanitizer (#149).

`_caption_alt` is a pure function; the image/caption pairing that depends on
page geometry is covered end-to-end in
tests/integration/test_caption_alt.py.
"""
from __future__ import annotations

from app.services.packages_loader import pdf_to_md_module


def test_collapses_internal_whitespace():
    mod = pdf_to_md_module()
    assert mod._caption_alt("Figure 1:   Architecture   overview\n") == "Figure 1: Architecture overview"


def test_strips_surrounding_quotes():
    mod = pdf_to_md_module()
    assert mod._caption_alt('“A quoted caption”') == "A quoted caption"
    assert mod._caption_alt('"plain quotes"') == "plain quotes"


def test_escapes_closing_bracket():
    mod = pdf_to_md_module()
    # A raw ] in alt text would close the ![...] early; escape it.
    assert mod._caption_alt("see [ref] here") == "see [ref\\] here"


def test_empty_or_blank_caption_returns_empty():
    mod = pdf_to_md_module()
    assert mod._caption_alt("   ") == ""
    assert mod._caption_alt("") == ""
