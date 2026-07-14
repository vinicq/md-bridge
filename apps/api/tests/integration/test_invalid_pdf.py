"""Integration coverage for corrupt/non-PDF uploads (#360).

A malformed upload is a client error, so both PDF-consuming endpoints must
answer with the documented 422 `{error:{code,message}}` envelope instead of the
plain-text 500 PyMuPDF's FileDataError produced before the guard. Hits the real
inspector (no mock), which is where fitz.open rejects the bytes.
"""
from __future__ import annotations

import base64

GARBAGE = b"this is not a pdf at all, just some plain text\n" * 4

# A valid 1x1 PNG. PyMuPDF opens it as an image document without raising, so a
# suffix-only check would pass it through; the is_pdf guard must still reject it.
PNG_1X1 = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+M8AAAMBAQDJ/pLvAAAAAElFTkSuQmCC"
)


def test_pdf_to_md_rejects_corrupt_pdf_with_422(client):
    resp = client.post(
        "/api/pdf-to-md",
        files={"file": ("broken.pdf", GARBAGE, "application/pdf")},
    )
    assert resp.status_code == 422, resp.text
    body = resp.json()
    assert body["error"]["code"] == "invalid_pdf"
    assert body["error"]["message"]


def test_pdf_to_md_rejects_non_pdf_image_with_422(client):
    # A PNG renamed to .pdf: PyMuPDF opens it (no FileDataError), so only the
    # is_pdf check keeps it out of the PDF pipeline.
    resp = client.post(
        "/api/pdf-to-md",
        files={"file": ("image.pdf", PNG_1X1, "application/pdf")},
    )
    assert resp.status_code == 422, resp.text
    assert resp.json()["error"]["code"] == "invalid_pdf"


def test_inspect_pdf_rejects_non_pdf_image_with_422(client):
    resp = client.post(
        "/api/inspect-pdf",
        files={"file": ("image.pdf", PNG_1X1, "application/pdf")},
    )
    assert resp.status_code == 422, resp.text
    assert resp.json()["error"]["code"] == "invalid_pdf"


def test_inspect_pdf_rejects_corrupt_pdf_with_422(client):
    resp = client.post(
        "/api/inspect-pdf",
        files={"file": ("broken.pdf", GARBAGE, "application/pdf")},
    )
    assert resp.status_code == 422, resp.text
    assert resp.json()["error"]["code"] == "invalid_pdf"
