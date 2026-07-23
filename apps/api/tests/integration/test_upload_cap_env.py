"""The public upload cap is env-driven (MD_BRIDGE_MAX_UPLOAD_MB), read at
create_app() time. The code default stays 500 MB so a bare local deploy keeps
today's behavior; the public recipe lowers it via env.
"""
from __future__ import annotations

from app.main import create_app
from app.settings import load_settings
from fastapi.testclient import TestClient


def test_env_var_lowers_the_upload_cap(monkeypatch):
    monkeypatch.setenv("MD_BRIDGE_MAX_UPLOAD_MB", "1")
    client = TestClient(create_app())
    over = b"# x\n\n" + b"a" * (1 * 1024 * 1024 + 1)  # just over 1 MB
    resp = client.post(
        "/api/md-to-docx",
        files={"file": ("big.md", over, "text/markdown")},
    )
    assert resp.status_code == 413, resp.text
    assert resp.json()["error"]["code"] == "payload_too_large"


def test_default_cap_is_500_mb(monkeypatch):
    monkeypatch.delenv("MD_BRIDGE_MAX_UPLOAD_MB", raising=False)
    assert load_settings().max_upload_bytes == 500 * 1024 * 1024
