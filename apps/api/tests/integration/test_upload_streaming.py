"""Streaming-upload behavior for _read_upload (#365).

The refactor spools uploads to a temp file instead of growing a bytearray and
copying it into bytes. These lock the observable contract: the 413 cap still
fires, and a payload large enough to spill past the in-RAM threshold still
converts to the same result as a small in-RAM one.
"""
from __future__ import annotations

import io

from app.main import create_app
from docx import Document
from fastapi.testclient import TestClient


def _client() -> TestClient:
    return TestClient(create_app())


def _docx_text(body: bytes) -> str:
    return "\n".join(p.text for p in Document(io.BytesIO(body)).paragraphs)


def test_upload_over_cap_returns_413(monkeypatch):
    # Shrink the cap so a modest payload trips it without moving 500 MB around.
    monkeypatch.setattr("app.routes.convert.MAX_UPLOAD_BYTES", 64 * 1024)
    client = _client()
    big = b"# Heading\n\n" + b"filler text " * 20_000  # ~240 KB, over the 64 KB cap
    resp = client.post(
        "/api/md-to-docx",
        files={"file": ("big.md", big, "text/markdown")},
    )
    assert resp.status_code == 413, resp.text
    assert resp.json()["error"]["code"] == "payload_too_large"


def test_spooled_disk_path_matches_in_ram_path(monkeypatch):
    # Same input through the in-RAM spool and (with a tiny threshold) the
    # disk-backed spool must yield the same conversion, proving the refactor is
    # byte-faithful across the RAM/disk boundary.
    md = b"# Heading One\n\nA paragraph with **bold** and *italic*.\n\n- one\n- two\n"

    in_ram = _client().post(
        "/api/md-to-docx",
        files={"file": ("doc.md", md, "text/markdown")},
    )
    assert in_ram.status_code == 200, in_ram.text

    monkeypatch.setattr("app.routes.convert._UPLOAD_SPOOL_MAX_BYTES", 8)
    on_disk = _client().post(
        "/api/md-to-docx",
        files={"file": ("doc.md", md, "text/markdown")},
    )
    assert on_disk.status_code == 200, on_disk.text

    text = _docx_text(on_disk.content)
    assert "Heading One" in text
    assert _docx_text(in_ram.content) == text
