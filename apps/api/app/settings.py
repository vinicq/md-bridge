"""Runtime settings read from the environment at app-creation time.

Kept separate from config.py (which holds static repo paths) because these are
read per `create_app()` call, not at import: a test builds a fresh app with
different env and gets a fresh Settings, and nothing here is a module-level
constant a route could capture at import time.

Every knob defaults to today's behavior: no token (auth off), no rate limit,
the 500 MB upload cap. Setting an env var opts in.
"""
from __future__ import annotations

import os
from dataclasses import dataclass

DEFAULT_MAX_UPLOAD_MB = 500


def _int_env(name: str, default: int, *, minimum: int) -> int:
    """Read an int env var, failing loudly on a bad value.

    A security knob that silently falls back to its default on a typo fails
    open: `MD_BRIDGE_RATE_LIMIT=6O` (letter O) would disable the limiter the
    operator meant to turn on. Raise instead, so a misconfigured opt-in stops
    startup rather than quietly dropping the protection.
    """
    raw = os.environ.get(name, "").strip()
    if not raw:
        return default
    try:
        value = int(raw)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer, got {raw!r}") from exc
    if value < minimum:
        raise ValueError(f"{name} must be >= {minimum}, got {value}")
    return value


@dataclass(frozen=True)
class Settings:
    max_upload_bytes: int
    api_token: str | None
    rate_limit: int  # requests per window per client IP; 0 disables the limiter
    rate_window_seconds: int

    @property
    def auth_enabled(self) -> bool:
        return bool(self.api_token)

    @property
    def rate_limit_enabled(self) -> bool:
        return self.rate_limit > 0


def load_settings() -> Settings:
    max_mb = _int_env("MD_BRIDGE_MAX_UPLOAD_MB", DEFAULT_MAX_UPLOAD_MB, minimum=1)
    token = os.environ.get("MD_BRIDGE_API_TOKEN", "").strip() or None
    return Settings(
        max_upload_bytes=max_mb * 1024 * 1024,
        api_token=token,
        # rate_limit 0 disables; the window must be a positive number of
        # seconds or a positive limit could never block (every call would reset
        # its own window).
        rate_limit=_int_env("MD_BRIDGE_RATE_LIMIT", 0, minimum=0),
        rate_window_seconds=_int_env("MD_BRIDGE_RATE_WINDOW_SECONDS", 60, minimum=1),
    )
