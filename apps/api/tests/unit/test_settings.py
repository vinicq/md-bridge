"""Settings fail closed on an invalid security knob rather than silently
dropping the protection the operator opted into."""
from __future__ import annotations

import pytest
from app.settings import load_settings


def test_non_integer_rate_limit_raises(monkeypatch):
    monkeypatch.setenv("MD_BRIDGE_RATE_LIMIT", "6O")  # letter O, not zero
    with pytest.raises(ValueError):
        load_settings()


def test_zero_window_raises(monkeypatch):
    monkeypatch.setenv("MD_BRIDGE_RATE_WINDOW_SECONDS", "0")
    with pytest.raises(ValueError):
        load_settings()


def test_negative_upload_cap_raises(monkeypatch):
    monkeypatch.setenv("MD_BRIDGE_MAX_UPLOAD_MB", "-1")
    with pytest.raises(ValueError):
        load_settings()


def test_non_ascii_token_raises(monkeypatch):
    monkeypatch.setenv("MD_BRIDGE_API_TOKEN", "señor")
    with pytest.raises(ValueError):
        load_settings()


def test_defaults_are_safe(monkeypatch):
    for var in (
        "MD_BRIDGE_RATE_LIMIT",
        "MD_BRIDGE_RATE_WINDOW_SECONDS",
        "MD_BRIDGE_MAX_UPLOAD_MB",
        "MD_BRIDGE_API_TOKEN",
    ):
        monkeypatch.delenv(var, raising=False)
    s = load_settings()
    assert s.rate_limit == 0  # off
    assert s.rate_window_seconds == 60
    assert s.max_upload_bytes == 500 * 1024 * 1024
    assert s.api_token is None
