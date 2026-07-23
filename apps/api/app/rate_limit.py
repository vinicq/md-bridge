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

The limiter is enforced in the access-control middleware (app.main) so an
over-quota request is rejected before its body is parsed and spooled.
"""
from __future__ import annotations

import time
from collections.abc import Callable

from fastapi import FastAPI


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
        self._last_prune: float | None = None

    def allow(self, key: str) -> bool:
        now = self._clock()
        start, count = self._hits.get(key, (now, 0))
        if now - start >= self._window:
            start, count = now, 0
        count += 1
        self._hits[key] = (start, count)
        # Sweep expired entries at most once per window (time-scheduled), not on
        # every request. A flood of distinct IPs keeps the map large, but the
        # O(N) sweep runs once per window rather than per request, so the
        # abuse-protection path stays O(1) amortized regardless of map size.
        if self._last_prune is None or now - self._last_prune >= self._window:
            self._prune(now)
            self._last_prune = now
        return count <= self._limit

    def _prune(self, now: float) -> None:
        expired = [k for k, (start, _) in self._hits.items() if now - start >= self._window]
        for k in expired:
            del self._hits[k]


def get_limiter(app: FastAPI) -> FixedWindowLimiter:
    limiter = getattr(app.state, "rate_limiter", None)
    if limiter is None:
        settings = app.state.settings
        limiter = FixedWindowLimiter(settings.rate_limit, settings.rate_window_seconds)
        app.state.rate_limiter = limiter
    return limiter
