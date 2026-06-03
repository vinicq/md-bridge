"""Integration coverage for the theme API (#23)."""
from __future__ import annotations

import json

import pytest

SAMPLE_MD = b"""---
title: "Theme Test"
---

# Heading

A paragraph with **bold** text.
"""


@pytest.fixture(scope="module")
def chromium_ready():
    from playwright.sync_api import sync_playwright

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            browser.close()
    except Exception as exc:
        pytest.skip(f"Playwright chromium unavailable: {exc}")


def test_get_themes_returns_the_catalogue(client):
    resp = client.get("/api/themes")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    slugs = [t["slug"] for t in body]
    assert slugs[0] == "default"
    assert {"default", "academic", "business", "minimal"} <= set(slugs)
    for t in body:
        assert set(t.keys()) == {"slug", "name", "description", "family"}


def test_get_theme_css_returns_raw_css(client):
    resp = client.get("/api/themes/default/css")
    assert resp.status_code == 200, resp.text
    assert resp.headers["content-type"].startswith("text/css")
    css = resp.text
    assert css.strip(), "css should not be empty"
    assert "{" in css and "}" in css, "expected CSS rules, not arbitrary text"


def test_get_theme_css_unknown_slug_returns_400(client):
    resp = client.get("/api/themes/nope/css")
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "unknown_theme"


def test_md_to_pdf_with_selected_theme_renders(client, chromium_ready):
    resp = client.post(
        "/api/md-to-pdf",
        files={"file": ("doc.md", SAMPLE_MD, "text/markdown")},
        data={"options": json.dumps({"theme": "academic"})},
    )
    assert resp.status_code == 200, resp.text
    assert resp.content[:5] == b"%PDF-"
