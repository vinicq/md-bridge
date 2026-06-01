"""Unit coverage for the OCR default language set (#199).

`get_lang` is a plain env read (no Tesseract, no pytesseract), so these run
cross-platform. The default now carries English, Portuguese, and Spanish so a
scanned document is read without per-document configuration; the env override
still wins.
"""
from __future__ import annotations

from app.services import ocr


def test_default_lang_covers_en_pt_es(monkeypatch):
    monkeypatch.delenv("MD_BRIDGE_OCR_LANG", raising=False)
    assert ocr.get_lang() == "eng+por+spa"
    # Portuguese covers both PT-PT and PT-BR — Tesseract ships a single `por`.
    assert {"eng", "por", "spa"} == set(ocr.DEFAULT_OCR_LANG.split("+"))


def test_env_override_still_wins(monkeypatch):
    monkeypatch.setenv("MD_BRIDGE_OCR_LANG", "deu")
    assert ocr.get_lang() == "deu"
