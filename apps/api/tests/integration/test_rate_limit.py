"""Per-IP rate limit and baseline security headers, through the real app."""
from __future__ import annotations

FILES = {"file": ("d.md", b"# Title\n\nBody.\n", "text/markdown")}


def test_rate_limit_blocks_after_the_limit(client_factory):
    client = client_factory(rate_limit=2, rate_window_seconds=60)
    assert client.post("/api/md-to-docx", files=FILES).status_code == 200
    assert client.post("/api/md-to-docx", files=FILES).status_code == 200
    resp = client.post("/api/md-to-docx", files=FILES)
    assert resp.status_code == 429, resp.text
    assert resp.json()["error"]["code"] == "rate_limited"


def test_no_rate_limit_by_default(client):
    for _ in range(5):
        assert client.post("/api/md-to-docx", files=FILES).status_code == 200


def test_security_headers_present(client):
    resp = client.get("/api/health")
    assert resp.headers["X-Content-Type-Options"] == "nosniff"
    assert resp.headers["Referrer-Policy"] == "no-referrer"
    assert resp.headers["X-Frame-Options"] == "DENY"


def test_unauthenticated_requests_do_not_consume_the_quota(client_factory):
    # Auth runs before the rate limiter, so rejected requests must not burn the
    # shared quota. With limit=1, five unauthenticated calls all 401 (not 429),
    # and a single keyed call then still succeeds.
    client = client_factory(api_token="s3cret", rate_limit=1, rate_window_seconds=60)
    for _ in range(5):
        resp = client.post("/api/md-to-docx", files=FILES)
        assert resp.status_code == 401, resp.text
    ok = client.post("/api/md-to-docx", files=FILES, headers={"X-API-Key": "s3cret"})
    assert ok.status_code == 200, ok.text
