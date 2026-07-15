"""Route-level regression for malformed `options` handling (#361)."""
from __future__ import annotations

import json

from app.main import create_app
from fastapi.testclient import TestClient


def test_invalid_allow_html_through_route_returns_422():
    # An allow_html value the field_validator rejects must surface as the
    # documented 422 invalid_options. Before the fix the ValueError embedded in
    # the Pydantic v2 error ctx was not JSON serializable, so the error handler
    # itself raised a 500 while rendering the envelope.
    client = TestClient(create_app())
    resp = client.post(
        "/api/pdf-to-md",
        files={"file": ("doc.pdf", b"%PDF-1.4 fake", "application/pdf")},
        data={"options": json.dumps({"allow_html": ["script"]})},
    )
    assert resp.status_code == 422, resp.text
    body = resp.json()
    assert body["error"]["code"] == "invalid_options"
    # The detail carries the serialized validation errors, not a crash.
    assert body["error"]["detail"], body
