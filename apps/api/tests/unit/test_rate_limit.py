"""Fixed-window limiter, driven by an injected clock so there is no sleep."""
from __future__ import annotations

from app.rate_limit import FixedWindowLimiter


def test_allows_up_to_limit_then_blocks():
    now = [1000.0]
    lim = FixedWindowLimiter(limit=2, window_seconds=60, clock=lambda: now[0])
    assert lim.allow("ip") is True
    assert lim.allow("ip") is True
    assert lim.allow("ip") is False


def test_window_reset_allows_again():
    now = [1000.0]
    lim = FixedWindowLimiter(limit=1, window_seconds=60, clock=lambda: now[0])
    assert lim.allow("ip") is True
    assert lim.allow("ip") is False
    now[0] += 61  # cross the window boundary
    assert lim.allow("ip") is True


def test_keys_are_independent():
    now = [0.0]
    lim = FixedWindowLimiter(limit=1, window_seconds=60, clock=lambda: now[0])
    assert lim.allow("a") is True
    assert lim.allow("b") is True
    assert lim.allow("a") is False
