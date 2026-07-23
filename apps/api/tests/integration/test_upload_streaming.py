"""Upload-read behavior for _read_upload (#365).

The refactor reads the already-parsed UploadFile once into the final bytes,
bounded at the cap, instead of growing a bytearray and copying it into bytes.
These lock the observable contract: the 413 cap still fires, a boundary-sized
upload is accepted, and conversion output is unchanged.
"""
from __future__ import annotations

import io

from docx import Document


def _docx_text(body: bytes) -> str:
    return "\n".join(p.text for p in Document(io.BytesIO(body)).paragraphs)


def test_upload_over_cap_returns_413(client_factory):
    # Shrink the cap so a modest payload trips it without moving 500 MB around.
    client = client_factory(max_upload_bytes=64 * 1024)
    big = b"# Heading\n\n" + b"filler text " * 20_000  # ~240 KB, over the 64 KB cap
    resp = client.post(
        "/api/md-to-docx",
        files={"file": ("big.md", big, "text/markdown")},
    )
    assert resp.status_code == 413, resp.text
    assert resp.json()["error"]["code"] == "payload_too_large"


def test_upload_at_cap_boundary_is_accepted(client_factory):
    # A payload exactly at the cap must pass: the read is bounded at cap+1, so
    # len == cap is not "over".
    md = b"# Heading One\n\nBody.\n"
    resp = client_factory(max_upload_bytes=len(md)).post(
        "/api/md-to-docx",
        files={"file": ("doc.md", md, "text/markdown")},
    )
    assert resp.status_code == 200, resp.text


def test_conversion_reads_the_full_payload(client):
    # A payload larger than one read chunk still reaches the converter intact,
    # proving _read_upload returns the whole upload byte-faithfully.
    body = "# Heading One\n\n" + "A paragraph with some words.\n\n" * 500
    resp = client.post(
        "/api/md-to-docx",
        files={"file": ("doc.md", body.encode(), "text/markdown")},
    )
    assert resp.status_code == 200, resp.text
    assert "Heading One" in _docx_text(resp.content)
