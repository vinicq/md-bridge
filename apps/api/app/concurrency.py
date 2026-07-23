"""In-process concurrency gate for heavy conversions.

A single global asyncio.Semaphore caps how many heavy conversions run at once.
MuPDF has global state and Chromium is memory-heavy, so concurrency stays low
and explicit. Requests over the cap wait up to a bound, then get 503 with
Retry-After; a per-request wall-clock timeout returns 504.

Named ceiling: the work runs in a worker thread (asyncio.to_thread), and a
thread cannot be cancelled. A timed-out or slow conversion keeps holding its
slot until it actually finishes; wait_for returns 504 to the client but the
thread runs to completion and only then frees the slot. A hard kill would need
per-subprocess isolation (SIGKILL), which is a separate hardening step.
# ponytail: thread cannot be cancelled; the slot is held until it completes.
"""
from __future__ import annotations

import asyncio
from collections.abc import Callable
from typing import Any

from fastapi import FastAPI

from app.errors import ApiError


class ConcurrencyGate:
    def __init__(
        self,
        max_concurrency: int,
        queue_max: int,
        queue_wait_seconds: float,
        timeout_seconds: float,
    ) -> None:
        self._sem = asyncio.Semaphore(max_concurrency)
        self._queue_max = queue_max
        self._queue_wait = queue_wait_seconds
        self._timeout = timeout_seconds
        self._waiters = 0  # requests currently blocked waiting for a slot

    def _busy_error(self) -> ApiError:
        retry_after = str(max(1, int(self._queue_wait)))
        return ApiError(
            503,
            "service_busy",
            "The service is at capacity. Retry shortly.",
            headers={"Retry-After": retry_after},
        )

    async def run[T](self, fn: Callable[..., T], *args: Any, **kwargs: Any) -> T:
        if self._sem.locked():
            # No slot free. Reject if the wait queue is full, else wait a bound.
            # The checks and counter update run without an await between them, so
            # on the single-threaded event loop they are atomic.
            if self._waiters >= self._queue_max:
                raise self._busy_error()
            self._waiters += 1
            try:
                await asyncio.wait_for(self._sem.acquire(), timeout=self._queue_wait)
            except TimeoutError:
                raise self._busy_error() from None
            finally:
                self._waiters -= 1
        else:
            # A slot is free: acquire it directly. On a semaphore with a free
            # permit, acquire() returns without suspending, so no other request
            # can take the permit between the check above and here.
            await self._sem.acquire()

        task = asyncio.ensure_future(asyncio.to_thread(fn, *args, **kwargs))

        def _on_done(finished: asyncio.Future) -> None:
            # Release only when the thread truly finishes, never on the success
            # path: a timed-out thread keeps running and must free its slot when
            # it completes, not when wait_for gives up.
            self._sem.release()
            # Retrieve the outcome so a detached (timed-out or cancelled) task
            # does not surface "Task exception was never retrieved" on the loop.
            if not finished.cancelled():
                finished.exception()

        task.add_done_callback(_on_done)

        # shield so cancelling the awaiting coroutine (a wait_for timeout, or an
        # ASGI host cancelling on client disconnect) does not cancel the task:
        # the thread keeps running regardless, and the slot must be released by
        # the done callback, never early.
        if self._timeout <= 0:
            # No gate deadline; worker exceptions (including a TimeoutError the
            # converter itself raises) propagate unchanged.
            return await asyncio.shield(task)
        try:
            return await asyncio.wait_for(asyncio.shield(task), timeout=self._timeout)
        except TimeoutError:
            if task.done():
                # The worker itself raised TimeoutError before the deadline;
                # propagate it rather than relabel it as the gate timeout.
                raise
            raise ApiError(
                504, "conversion_timeout", "The conversion took too long and was abandoned."
            ) from None


def get_gate(app: FastAPI) -> ConcurrencyGate:
    gate = getattr(app.state, "concurrency_gate", None)
    if gate is None:
        s = app.state.settings
        gate = ConcurrencyGate(
            s.max_concurrency, s.queue_max, s.queue_wait_seconds, s.convert_timeout_seconds
        )
        app.state.concurrency_gate = gate
    return gate


async def run_bounded[T](app: FastAPI, fn: Callable[..., T], *args: Any, **kwargs: Any) -> T:
    """Run a blocking conversion in a worker thread, under the app's gate."""
    return await get_gate(app).run(fn, *args, **kwargs)
