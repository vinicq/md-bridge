"""Work limits through the real app and real converter (no mocks).

The gate's cap/timeout logic is unit-tested deterministically in
tests/unit/test_concurrency.py; here we prove the routes are wired to it and
that a real over-capacity burst is rejected. Uses pdf-to-md (MuPDF) so it runs
without a browser; the gate is the same for every heavy route.
"""
from __future__ import annotations

import asyncio
from dataclasses import replace
from pathlib import Path

import httpx
from app.main import create_app


def _app_with(**overrides):
    app = create_app()
    app.state.settings = replace(app.state.settings, **overrides)
    return app


def test_pdf_to_md_ok_through_the_gate(client, istqb_pdf: Path):
    with istqb_pdf.open("rb") as fh:
        resp = client.post(
            "/api/pdf-to-md", files={"file": ("s.pdf", fh.read(), "application/pdf")}
        )
    assert resp.status_code == 200, resp.text


def test_concurrent_requests_over_cap_get_503(istqb_pdf: Path):
    # One slot, no queue: two concurrent real conversions -> one runs, one is
    # busy. The istqb syllabus is large enough that the first holds the slot
    # while the second arrives.
    app = _app_with(max_concurrency=1, queue_max=0, queue_wait_seconds=0)
    pdf = istqb_pdf.read_bytes()

    async def scenario():
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://t", timeout=60) as ac:
            files = {"file": ("s.pdf", pdf, "application/pdf")}
            r1, r2 = await asyncio.gather(
                ac.post("/api/pdf-to-md", files=files),
                ac.post("/api/pdf-to-md", files=files),
            )
            codes = sorted([r1.status_code, r2.status_code])
            assert codes == [200, 503], codes
            busy = r1 if r1.status_code == 503 else r2
            assert busy.headers.get("Retry-After") is not None
            assert busy.json()["error"]["code"] == "service_busy"

    asyncio.run(scenario())
