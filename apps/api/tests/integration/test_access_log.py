"""The /api access log records every request - including failures - with
status and duration, and never the document content."""
from __future__ import annotations

import logging


def test_logs_a_failed_request_with_status(client, caplog):
    with caplog.at_level(logging.INFO, logger="app.access"):
        # Wrong file type -> 400 before the converter runs; the route's success
        # log never fires, so only the access middleware records this.
        resp = client.post(
            "/api/md-to-pdf",
            files={"file": ("notes.txt", b"secret document body", "text/plain")},
        )
    assert resp.status_code == 400
    lines = [r.getMessage() for r in caplog.records if r.name == "app.access"]
    assert any("path=/api/md-to-pdf" in m and "status=400" in m for m in lines)
    # duration is recorded, document content is not
    assert any("duration_ms=" in m for m in lines)
    assert not any("secret document body" in m for m in lines)


def test_logs_a_successful_request(client, caplog):
    with caplog.at_level(logging.INFO, logger="app.access"):
        resp = client.post(
            "/api/md-to-docx",
            files={"file": ("d.md", b"# Title\n\nBody.\n", "text/markdown")},
        )
    assert resp.status_code == 200
    lines = [r.getMessage() for r in caplog.records if r.name == "app.access"]
    assert any("path=/api/md-to-docx" in m and "status=200" in m for m in lines)


def test_health_is_not_access_logged(client, caplog):
    with caplog.at_level(logging.INFO, logger="app.access"):
        client.get("/api/health")
    assert not [r for r in caplog.records if r.name == "app.access"]
