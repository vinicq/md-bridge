from __future__ import annotations

from pathlib import Path


def test_inspect_pdf_returns_diagnostics(client, istqb_pdf: Path):
    with istqb_pdf.open("rb") as fh:
        resp = client.post(
            "/api/inspect-pdf",
            files={"file": (istqb_pdf.name, fh, "application/pdf")},
        )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["pages"] >= 1
    assert body["body_size_pt"] > 0
    assert isinstance(body["heading_sizes_pt"], list)
    assert isinstance(body["fonts"], list)
    assert body["fonts"], "expected at least one font in a digitally-generated PDF"
    assert isinstance(body["tagged"], bool)
    assert isinstance(body["needs_ocr"], bool)


def test_inspect_pdf_rejects_non_pdf(client):
    resp = client.post(
        "/api/inspect-pdf",
        files={"file": ("notes.txt", b"hello", "text/plain")},
    )
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "wrong_file_type"
