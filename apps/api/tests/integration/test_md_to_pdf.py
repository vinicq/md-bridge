from __future__ import annotations

import json

import pytest


SAMPLE_MD = b"""---
title: "Test Document"
---

# Heading One

This is a paragraph with **bold** and *italic*.

- bullet one
- bullet two

| col a | col b |
| --- | --- |
| 1 | 2 |
"""


@pytest.fixture(scope="module")
def chromium_ready():
    """Skip md-to-pdf tests if Playwright's Chromium isn't installed locally."""
    from playwright.sync_api import sync_playwright

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            browser.close()
    except Exception as exc:
        pytest.skip(f"Playwright chromium unavailable: {exc}")


def test_md_to_pdf_returns_pdf(client, chromium_ready):
    resp = client.post(
        "/api/md-to-pdf",
        files={"file": ("doc.md", SAMPLE_MD, "text/markdown")},
    )
    assert resp.status_code == 200, resp.text
    assert resp.headers["content-type"].startswith("application/pdf")
    assert resp.content[:5] == b"%PDF-"


def test_md_to_pdf_rejects_unknown_theme(client):
    resp = client.post(
        "/api/md-to-pdf",
        files={"file": ("doc.md", SAMPLE_MD, "text/markdown")},
        data={"options": json.dumps({"theme": "does-not-exist"})},
    )
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "unknown_theme"


def test_md_to_pdf_rejects_non_md(client):
    resp = client.post(
        "/api/md-to-pdf",
        files={"file": ("doc.txt", b"hello", "text/plain")},
    )
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "wrong_file_type"
