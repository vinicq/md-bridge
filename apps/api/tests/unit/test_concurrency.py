"""Concurrency gate: cap, bounded-wait 503, timeout 504, and the named
ceiling that a timed-out thread keeps its slot until it finishes.

Driven with asyncio.run and a threading.Event so the ordering is deterministic
(no fixed sleeps for the assertions)."""
from __future__ import annotations

import asyncio
import threading

import pytest
from app.concurrency import ConcurrencyGate
from app.errors import ApiError


def test_returns_the_result_under_cap():
    async def scenario():
        gate = ConcurrencyGate(max_concurrency=2, queue_max=8, queue_wait_seconds=5, timeout_seconds=0)
        assert await gate.run(lambda: "ok") == "ok"

    asyncio.run(scenario())


def test_rejects_immediately_when_full_and_queue_is_zero():
    async def scenario():
        gate = ConcurrencyGate(max_concurrency=1, queue_max=0, queue_wait_seconds=5, timeout_seconds=0)
        release = threading.Event()
        started = threading.Event()

        def blocker():
            started.set()
            release.wait(2)
            return "done"

        first = asyncio.ensure_future(gate.run(blocker))
        await asyncio.to_thread(started.wait, 2)  # slot is now held

        with pytest.raises(ApiError) as exc:
            await gate.run(lambda: "x")
        assert exc.value.status_code == 503
        assert exc.value.code == "service_busy"
        assert exc.value.headers.get("Retry-After")

        release.set()
        assert await first == "done"

    asyncio.run(scenario())


def test_waits_then_runs_when_a_slot_frees():
    async def scenario():
        gate = ConcurrencyGate(max_concurrency=1, queue_max=4, queue_wait_seconds=5, timeout_seconds=0)
        release = threading.Event()
        started = threading.Event()

        def blocker():
            started.set()
            release.wait(2)
            return "first"

        first = asyncio.ensure_future(gate.run(blocker))
        await asyncio.to_thread(started.wait, 2)
        # second call waits for the slot (queue has room), does not 503
        second = asyncio.ensure_future(gate.run(lambda: "second"))
        release.set()
        assert await first == "first"
        assert await second == "second"

    asyncio.run(scenario())


def test_timeout_returns_504_and_holds_the_slot_until_done():
    async def scenario():
        gate = ConcurrencyGate(
            max_concurrency=1, queue_max=0, queue_wait_seconds=5, timeout_seconds=0.05
        )
        release = threading.Event()
        started = threading.Event()

        def blocker():
            started.set()
            release.wait(2)
            return "late"

        with pytest.raises(ApiError) as exc:
            await gate.run(blocker)
        assert exc.value.status_code == 504
        assert exc.value.code == "conversion_timeout"

        # The orphaned thread still holds the slot, so a new call is rejected.
        await asyncio.to_thread(started.wait, 2)
        with pytest.raises(ApiError) as exc2:
            await gate.run(lambda: "x")
        assert exc2.value.status_code == 503

        release.set()  # let the orphan finish and free its slot
        await asyncio.to_thread(release.wait, 2)
        await asyncio.sleep(0.05)  # let the done callback release the slot

    asyncio.run(scenario())
