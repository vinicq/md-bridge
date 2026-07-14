"""Integration coverage for the md-to-pdf render egress block (#363).

Renders through the real API + Chromium with a document that embeds an external
`<img>`, and asserts the renderer never reaches the network: a counting HTTP
server on 127.0.0.1 records zero hits, and a valid PDF still comes back. This
test fails on main (the old renderer used wait_until="networkidle" and fetched
the image) and passes once the egress guard aborts network requests.

Hermetic: the "external" server is a local loopback listener that the guard is
expected to block, so nothing leaves the machine.
"""
from __future__ import annotations

import http.server
import threading

import pytest


@pytest.fixture(scope="module")
def chromium_ready():
    """Skip if Playwright's Chromium isn't installed locally."""
    from playwright.sync_api import sync_playwright

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            browser.close()
    except Exception as exc:  # noqa: BLE001 - any launch failure means skip
        pytest.skip(f"Playwright chromium unavailable: {exc}")


class _CountingHandler(http.server.BaseHTTPRequestHandler):
    hits = 0

    def do_GET(self):  # noqa: N802 - BaseHTTPRequestHandler API
        type(self).hits += 1
        self.send_response(200)
        self.send_header("Content-Type", "image/png")
        self.end_headers()
        self.wfile.write(b"\x89PNG\r\n\x1a\n")

    def log_message(self, *args):  # silence the default stderr logging
        pass


def test_external_image_is_not_fetched(client, chromium_ready):
    _CountingHandler.hits = 0
    server = http.server.HTTPServer(("127.0.0.1", 0), _CountingHandler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        md = (
            f"# External image\n\n"
            f'<img src="http://127.0.0.1:{port}/pixel.png" alt="tracker">\n'
        ).encode()
        resp = client.post(
            "/api/md-to-pdf",
            files={"file": ("doc.md", md, "text/markdown")},
        )
    finally:
        server.shutdown()
        thread.join(timeout=5)
        server.server_close()

    assert resp.status_code == 200, resp.text
    assert resp.content[:5] == b"%PDF-"
    assert _CountingHandler.hits == 0, "renderer reached the external image server"
