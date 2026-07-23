#!/usr/bin/env python3
"""Post-deploy smoke test: exercise a running md-bridge over real HTTP.

Reads SMOKE_BASE_URL and checks the two things a live deploy has to get
right: the API answers `GET /api/health`, and `POST /api/md-to-pdf`
returns a real PDF. Both go over the wire against the given origin, so a
broken reverse proxy, a dead API, or a crashed renderer all fail here.
No TestClient, no monkeypatch, no mocks.

Usage:
    SMOKE_BASE_URL=http://localhost:5173 python3 scripts/smoke.py   # compose
    SMOKE_BASE_URL=https://your.domain   python3 scripts/smoke.py   # live VM

Exit 0 = healthy and converts. Exit 1 = SMOKE_BASE_URL missing or a check
failed.
"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request

# ponytail: fixed 60s ceiling to absorb container start; a stack that is
# not answering health in 60s is broken, not slow.
HEALTH_TIMEOUT_S = 60
SAMPLE_MD = b"# Smoke\n\nHello **md-bridge**.\n"


def _fail(msg: str) -> None:
    print(f"smoke: FAIL - {msg}", file=sys.stderr)
    sys.exit(1)


def _wait_healthy(base: str) -> None:
    url = f"{base}/api/health"
    deadline = time.monotonic() + HEALTH_TIMEOUT_S
    last = "no response"
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=5) as resp:
                body = resp.read().decode("utf-8", "replace")
                try:
                    status = json.loads(body).get("status")
                except json.JSONDecodeError:
                    status = None
                if resp.status == 200 and status == "ok":
                    print(f"smoke: health ok - {body.strip()}")
                    return
                last = f"status={resp.status} body={body.strip()!r}"
        except (urllib.error.URLError, OSError) as exc:
            last = str(exc)
        time.sleep(2)
    _fail(f"/api/health not ok within {HEALTH_TIMEOUT_S}s: {last}")


def _check_md_to_pdf(base: str) -> None:
    boundary = "smoke0boundary0md0bridge"
    body = (
        f"--{boundary}\r\n"
        'Content-Disposition: form-data; name="file"; filename="smoke.md"\r\n'
        "Content-Type: text/markdown\r\n\r\n"
    ).encode() + SAMPLE_MD + f"\r\n--{boundary}--\r\n".encode()
    req = urllib.request.Request(
        f"{base}/api/md-to-pdf",
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            if resp.status != 200:
                _fail(f"md-to-pdf returned status {resp.status}")
            head = resp.read(5)
    except (urllib.error.URLError, OSError) as exc:
        _fail(f"md-to-pdf request failed: {exc}")
    if not head.startswith(b"%PDF"):
        _fail(f"md-to-pdf did not return a PDF (first bytes: {head!r})")
    print("smoke: md-to-pdf ok - response starts with %PDF")


def _check_web_ui(base: str) -> None:
    try:
        with urllib.request.urlopen(f"{base}/", timeout=10) as resp:
            if resp.status != 200:
                _fail(f"web UI returned status {resp.status}")
            body = resp.read(4096).decode("utf-8", "replace").lower()
    except (urllib.error.URLError, OSError) as exc:
        _fail(f"web UI request failed: {exc}")
    if "<!doctype html" not in body and "<html" not in body:
        _fail("web UI did not return an HTML document")
    print("smoke: web UI ok - / returns HTML")


def main() -> None:
    base = os.environ.get("SMOKE_BASE_URL", "").rstrip("/")
    if not base:
        _fail("SMOKE_BASE_URL is not set (e.g. http://localhost:5173)")
    print(f"smoke: target {base}")
    _wait_healthy(base)
    _check_web_ui(base)
    _check_md_to_pdf(base)
    print("smoke: PASS")


if __name__ == "__main__":
    main()
