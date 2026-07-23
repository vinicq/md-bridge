"""Optional API-key access control on the expensive conversion routes.

Auth is off by default (no token): the existing suite is the regression guard
that today's behavior is unchanged. With a token set, the four expensive routes
require a matching X-API-Key; health, themes, and formats stay open so the
container healthcheck and the same-origin UI keep working.
"""
from __future__ import annotations

SMALL_MD = ("doc.md", b"# Title\n\nBody.\n", "text/markdown")


def test_conversion_open_when_no_token(client):
    resp = client.post("/api/md-to-docx", files={"file": SMALL_MD})
    assert resp.status_code == 200, resp.text


def test_missing_key_is_rejected_when_token_set(client_factory):
    client = client_factory(api_token="s3cret")
    resp = client.post("/api/md-to-docx", files={"file": SMALL_MD})
    assert resp.status_code == 401, resp.text
    assert resp.json()["error"]["code"] == "unauthorized"


def test_wrong_key_is_rejected_when_token_set(client_factory):
    client = client_factory(api_token="s3cret")
    resp = client.post(
        "/api/md-to-docx",
        files={"file": SMALL_MD},
        headers={"X-API-Key": "nope"},
    )
    assert resp.status_code == 401, resp.text
    assert resp.json()["error"]["code"] == "unauthorized"


def test_correct_key_is_accepted_when_token_set(client_factory):
    client = client_factory(api_token="s3cret")
    resp = client.post(
        "/api/md-to-docx",
        files={"file": SMALL_MD},
        headers={"X-API-Key": "s3cret"},
    )
    assert resp.status_code == 200, resp.text


def test_health_stays_open_with_token_set(client_factory):
    # The compose healthcheck sends no header; guarding /api/health would break it.
    client = client_factory(api_token="s3cret")
    resp = client.get("/api/health")
    assert resp.status_code == 200, resp.text


def test_themes_stay_open_with_token_set(client_factory):
    # The same-origin UI polls /api/themes with no header to render.
    client = client_factory(api_token="s3cret")
    resp = client.get("/api/themes")
    assert resp.status_code == 200, resp.text
