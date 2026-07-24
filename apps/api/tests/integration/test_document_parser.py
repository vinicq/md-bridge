"""Integration coverage for the LLM document parser (#457) against a real HTTP
endpoint: an in-process OpenAI-compatible stub on 127.0.0.1. This exercises the
real request serialization, status handling, JSON parse, and the auth header,
without any live network or a urlopen monkeypatch.
"""
from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest


class _StubState:
    last_auth: str | None = None
    last_model: str | None = None


@pytest.fixture
def openai_stub():
    state = _StubState()

    class _Handler(BaseHTTPRequestHandler):
        def log_message(self, *_a):  # silence
            pass

        def do_POST(self):  # noqa: N802
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length) or b"{}")
            state.last_auth = self.headers.get("Authorization")
            state.last_model = payload.get("model")
            body = json.dumps(
                {"choices": [{"message": {"content": "# Parsed by the model\n\nBody text."}}]}
            ).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    server = HTTPServer(("127.0.0.1", 0), _Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        host, port = server.server_address
        yield f"http://{host}:{port}/v1", state
    finally:
        server.shutdown()
        server.server_close()


def test_custom_parser_returns_model_markdown(client, scanned_pdf_bytes: bytes, monkeypatch, openai_stub):
    url, state = openai_stub
    monkeypatch.setenv("MD_BRIDGE_OCR_PROVIDER", "custom")
    monkeypatch.setenv("MD_BRIDGE_OCR_CUSTOM_URL", url)
    monkeypatch.setenv("MD_BRIDGE_OCR_CUSTOM_MODEL", "org/model")
    monkeypatch.setenv("MD_BRIDGE_OCR_CUSTOM_KEY", "secret-token")

    resp = client.post(
        "/api/pdf-to-md",
        files={"file": ("scanned.pdf", scanned_pdf_bytes, "application/pdf")},
    )

    assert resp.status_code == 200, resp.text
    body = resp.json()
    # The document parser returned the model's Markdown, superseding the pipeline.
    assert "Parsed by the model" in body["md"]
    assert body["ocr_applied"] is True
    assert body["ocr"]["provider"] == "custom"
    # No secret leaks into the response.
    assert "secret-token" not in resp.text
    assert body["ocr"].get("lang") is None
    # The stub actually received the configured model and the Bearer auth header.
    assert state.last_model == "org/model"
    assert state.last_auth == "Bearer secret-token"


def test_unavailable_custom_provider_returns_503(client, scanned_pdf_bytes: bytes, monkeypatch):
    # Selected but no URL configured: a typed 503 at the API layer, no silent
    # fallback to tesseract.
    monkeypatch.setenv("MD_BRIDGE_OCR_PROVIDER", "custom")
    monkeypatch.delenv("MD_BRIDGE_OCR_CUSTOM_URL", raising=False)
    resp = client.post(
        "/api/pdf-to-md",
        files={"file": ("scanned.pdf", scanned_pdf_bytes, "application/pdf")},
    )
    assert resp.status_code == 503, resp.text
    assert resp.json()["error"]["code"] == "ocr_provider_unavailable"
