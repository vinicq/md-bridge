"""Integration coverage for corrupt/non-PDF uploads (#360).

A malformed upload is a client error, so both PDF-consuming endpoints must
answer with the documented 422 `{error:{code,message}}` envelope instead of the
plain-text 500 PyMuPDF's FileDataError produced before the guard. Hits the real
inspector (no mock), which is where fitz.open rejects the bytes.
"""
from __future__ import annotations

GARBAGE = b"this is not a pdf at all, just some plain text\n" * 4


def test_pdf_to_md_rejects_corrupt_pdf_with_422(client):
    resp = client.post(
        "/api/pdf-to-md",
        files={"file": ("broken.pdf", GARBAGE, "application/pdf")},
    )
    assert resp.status_code == 422, resp.text
    body = resp.json()
    assert body["error"]["code"] == "invalid_pdf"
    assert body["error"]["message"]


def test_inspect_pdf_rejects_corrupt_pdf_with_422(client):
    resp = client.post(
        "/api/inspect-pdf",
        files={"file": ("broken.pdf", GARBAGE, "application/pdf")},
    )
    assert resp.status_code == 422, resp.text
    assert resp.json()["error"]["code"] == "invalid_pdf"
