"""In-process, per-IP fixed-window rate limiter.

Off by default (MD_BRIDGE_RATE_LIMIT=0). No external store: counters live in
this process's memory, so the limit is per uvicorn worker. The shipped image
runs a single worker, so the count is exact for the default deploy; run with
`--workers N` or scale to N containers and the effective limit is N times the
configured value. A shared store (Redis) would fix that but is out of scope by
the no-external-state contract.

Client IP comes from `request.client.host`. Behind a reverse proxy, run uvicorn
with `--forwarded-allow-ips` so that resolves to the real client rather than the
proxy; the app does not parse X-Forwarded-For itself (spoofable when the app is
exposed directly).
"""
from __future__ import annotations

import time
from collections.abc import Callable

from fastapi import Request

from app.errors import ApiError


class FixedWindowLimiter:
    """Allow up to `limit` calls per `window_seconds` per key.

    Fixed window, not sliding: cheap and good enough here. The known ceiling is
    a burst of up to 2x the limit straddling a window boundary.
    # ponytail: fixed window; go sliding only if boundary bursts become a problem.
    """

    def __init__(
        self,
        limit: int,
        window_seconds: float,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._limit = limit
        self._window = window_seconds
        self._clock = clock
        # key -> (window_start, count)
        self._hits: dict[str, tuple[float, int]] = {}

    def allow(self, key: str) -> bool:
        now = self._clock()
        self._prune(now)
        start, count = self._hits.get(key, (now, 0))
        if now - start >= self._window:
            start, count = now, 0
        count += 1
        self._hits[key] = (start, count)
        return count <= self._limit

    def _prune(self, now: float) -> None:
        # Drop expired windows so an IP-spray does not grow the dict without
        # bound. ponytail: O(n) sweep on each call is fine at this scale; cap or
        # switch to an LRU only if the key space gets large.
        expired = [k for k, (start, _) in self._hits.items() if now - start >= self._window]
        for k in expired:
            del self._hits[k]


def _get_limiter(request: Request) -> FixedWindowLimiter:
    limiter = getattr(request.app.state, "rate_limiter", None)
    if limiter is None:
        settings = request.app.state.settings
        limiter = FixedWindowLimiter(settings.rate_limit, settings.rate_window_seconds)
        request.app.state.rate_limiter = limiter
    return limiter


async def enforce_rate_limit(request: Request) -> None:
    settings = request.app.state.settings
    if not settings.rate_limit_enabled:
        return
    limiter = _get_limiter(request)
    client_ip = request.client.host if request.client else "unknown"
    if not limiter.allow(client_ip):
        raise ApiError(429, "rate_limited", "Too many requests. Try again later.")
