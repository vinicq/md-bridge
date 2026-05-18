from __future__ import annotations

import json
import tempfile
from pathlib import Path


def test_pdf_to_md_returns_markdown(client, small_pdf: Path):
    with small_pdf.open("rb") as fh:
        resp = client.post(
            "/api/pdf-to-md",
            files={"file": (small_pdf.name, fh, "application/pdf")},
        )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert "md" in body
    assert body["md"].strip(), "markdown should not be empty"
    assert body["front_matter"]["source"] == small_pdf.name
    assert isinstance(body["warnings"], list)
    stats = body["stats"]
    assert stats["headings"] + stats["bullets"] + stats["tables"] > 0, "expected some structure"


def test_pdf_to_md_rejects_non_pdf(client):
    resp = client.post(
        "/api/pdf-to-md",
        files={"file": ("notes.txt", b"hello", "text/plain")},
    )
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "wrong_file_type"


def test_pdf_to_md_rejects_invalid_options(client, small_pdf: Path):
    with small_pdf.open("rb") as fh:
        resp = client.post(
            "/api/pdf-to-md",
            files={"file": (small_pdf.name, fh, "application/pdf")},
            data={"options": json.dumps({"page_break": "yes please"})},
        )
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "invalid_options"


def test_pdf_to_md_rejects_oversize(client):
    # Send a real payload above the 50 MB cap so the route returns 413 the
    # same way it would in production. No patching of internal constants.
    from app.config import MAX_UPLOAD_BYTES

    payload = b"%PDF-1.4\n" + b"0" * (MAX_UPLOAD_BYTES + 1)
    resp = client.post(
        "/api/pdf-to-md",
        files={"file": ("big.pdf", payload, "application/pdf")},
    )
    assert resp.status_code == 413
    assert resp.json()["error"]["code"] == "payload_too_large"


def test_pdf_to_md_cleans_up_tempdirs(client, small_pdf: Path):
    tmp_root = Path(tempfile.gettempdir())
    before = {p.name for p in tmp_root.glob("md-bridge-pdf2md-*")}
    with small_pdf.open("rb") as fh:
        resp = client.post(
            "/api/pdf-to-md",
            files={"file": (small_pdf.name, fh, "application/pdf")},
        )
    assert resp.status_code == 200
    after = {p.name for p in tmp_root.glob("md-bridge-pdf2md-*")}
    leaked = after - before
    assert not leaked, f"pdf-to-md leaked tempdirs: {leaked}"
