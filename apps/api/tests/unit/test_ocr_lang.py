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


# --- is_enabled: OCR runs by default when the stack is installed (#199 follow-on) ---


def test_is_enabled_env_forces_on(monkeypatch):
    # The flag wins over stack detection: forced on even if the stack is absent.
    monkeypatch.setattr(ocr, "ocr_stack_available", lambda: False)
    for value in ("1", "true", "YES", "on"):
        monkeypatch.setenv("MD_BRIDGE_OCR_ENABLED", value)
        assert ocr.is_enabled() is True


def test_is_enabled_env_forces_off(monkeypatch):
    # Forced off even when the stack is present (keep slow OCR out of a hot path).
    monkeypatch.setattr(ocr, "ocr_stack_available", lambda: True)
    for value in ("0", "false", "NO", "off"):
        monkeypatch.setenv("MD_BRIDGE_OCR_ENABLED", value)
        assert ocr.is_enabled() is False


def test_is_enabled_default_follows_stack_availability(monkeypatch):
    # Unset (or blank) → auto: on when the stack is installed, off otherwise.
    monkeypatch.delenv("MD_BRIDGE_OCR_ENABLED", raising=False)
    monkeypatch.setattr(ocr, "ocr_stack_available", lambda: True)
    assert ocr.is_enabled() is True
    monkeypatch.setattr(ocr, "ocr_stack_available", lambda: False)
    assert ocr.is_enabled() is False


def test_ocr_stack_available_false_without_tesseract(monkeypatch):
    monkeypatch.setattr(ocr.shutil, "which", lambda _name: None)
    assert ocr.ocr_stack_available() is False
