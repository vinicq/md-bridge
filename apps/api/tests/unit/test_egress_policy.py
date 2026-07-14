"""Unit coverage for the md-to-pdf render egress policy (#363).

The renderer must stay offline: `egress_allowed` decides, by scheme, whether
Chromium may load a URL while rendering. data:/blob:/about: are inert and pass;
network schemes are denied; file: passes only inside the render tempdir. These
are pure decisions, so no Chromium is needed here (the real interception is
covered in tests/integration/test_md_to_pdf_egress.py).
"""
from __future__ import annotations

from pathlib import Path

from app.services.packages_loader import md_to_pdf_module

mod = md_to_pdf_module()


def test_inert_schemes_allowed(tmp_path):
    assert mod.egress_allowed("data:image/png;base64,AAAA", tmp_path) is True
    assert mod.egress_allowed("blob:abcd", tmp_path) is True
    assert mod.egress_allowed("about:blank", tmp_path) is True


def test_network_schemes_denied(tmp_path):
    assert mod.egress_allowed("http://example.com/x.png", tmp_path) is False
    assert mod.egress_allowed("https://169.254.169.254/latest/meta-data", tmp_path) is False
    assert mod.egress_allowed("ws://example.com/socket", tmp_path) is False
    assert mod.egress_allowed("ftp://example.com/file", tmp_path) is False


def test_file_inside_base_allowed(tmp_path):
    img = tmp_path / "pic.png"
    img.write_bytes(b"\x89PNG")
    assert mod.egress_allowed(img.resolve().as_uri(), tmp_path) is True


def test_file_outside_base_denied(tmp_path):
    outside = (tmp_path.parent / "secret.txt").resolve()
    assert mod.egress_allowed(outside.as_uri(), tmp_path) is False


def test_file_absolute_system_path_denied(tmp_path):
    # A crafted absolute file: URL (the classic LFI probe) must not resolve
    # inside a fresh render tempdir.
    probe = Path("/etc/passwd").resolve()
    assert mod.egress_allowed(probe.as_uri(), tmp_path) is False


class _FakeContext:
    """Records the routes the guard installs, so the wiring is checked without
    a real browser."""

    def __init__(self):
        self.request_handler = None
        self.ws_handler = None

    def route(self, pattern, handler):
        self.request_handler = handler

    def route_web_socket(self, pattern, handler):
        self.ws_handler = handler


class _FakeWsRoute:
    def __init__(self, url):
        self.url = url
        self.connected = False
        self.closed = False

    def connect_to_server(self):
        self.connected = True

    def close(self):
        self.closed = True


def test_guard_installs_request_and_websocket_routes(tmp_path):
    # page.route alone misses WebSockets and a popup's first navigation (#363
    # Codex review), so the guard must register a WebSocket route too.
    ctx = _FakeContext()
    mod._install_egress_guard(ctx, tmp_path)
    assert ctx.request_handler is not None
    assert ctx.ws_handler is not None


def test_websocket_guard_closes_network_socket(tmp_path):
    ctx = _FakeContext()
    mod._install_egress_guard(ctx, tmp_path)
    route = _FakeWsRoute("ws://127.0.0.1:9999/socket")
    ctx.ws_handler(route)
    assert route.closed is True
    assert route.connected is False


def test_guard_skipped_when_egress_opt_out(tmp_path, monkeypatch):
    monkeypatch.setenv("MD_BRIDGE_ALLOW_EGRESS", "1")
    ctx = _FakeContext()
    mod._install_egress_guard(ctx, tmp_path)
    assert ctx.request_handler is None
    assert ctx.ws_handler is None
