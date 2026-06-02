from __future__ import annotations

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


def test_md_to_pdf_unknown_theme_returns_400(client):
    # An unknown theme is rejected at the service before any rendering, so this
    # needs no Chromium. Uses the documented error envelope.
    import json

    resp = client.post(
        "/api/md-to-pdf",
        files={"file": ("doc.md", SAMPLE_MD, "text/markdown")},
        data={"options": json.dumps({"theme": "no-such-theme"})},
    )
    assert resp.status_code == 400, resp.text
    assert resp.json()["error"]["code"] == "unknown_theme"


def test_md_to_pdf_rejects_non_md(client):
    resp = client.post(
        "/api/md-to-pdf",
        files={"file": ("doc.txt", b"hello", "text/plain")},
    )
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "wrong_file_type"


# A YAML billion-laughs payload in front matter (#150 review): the parser must
# reject the aliases and still render the body, so the endpoint returns 200 with
# a PDF, not a 500. Confirms the malformed-front-matter contract end to end.
BOMB_MD = b"""---
a: &a [1,1,1,1,1,1,1,1,1]
b: &b [*a,*a,*a,*a,*a,*a,*a,*a,*a]
c: &c [*b,*b,*b,*b,*b,*b,*b,*b,*b]
d: [*c,*c,*c,*c,*c,*c,*c,*c,*c]
---

# Body still renders

A paragraph after a hostile front matter block.
"""


def test_md_to_pdf_survives_yaml_bomb_front_matter(client, chromium_ready):
    resp = client.post(
        "/api/md-to-pdf",
        files={"file": ("bomb.md", BOMB_MD, "text/markdown")},
    )
    assert resp.status_code == 200, resp.text
    assert resp.content[:5] == b"%PDF-"
