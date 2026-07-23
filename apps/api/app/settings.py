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
    # Work limits (#437). Unlike the auth/rate-limit knobs above, concurrency
    # and the convert timeout default to a safe-for-production value rather than
    # off: unbounded concurrency is a resource footgun (two Chromium renders
    # already compete), not a feature, and #437's AC asks for a safe default.
    max_concurrency: int  # simultaneous heavy conversions; >= 1
    queue_max: int  # requests allowed to wait for a slot; 0 = reject when full
    queue_wait_seconds: int  # how long a request waits for a slot before 503
    convert_timeout_seconds: int  # wall-clock per request; 0 disables
    max_pdf_pages: int  # reject PDFs above this page count; 0 = unlimited

    @property
    def auth_enabled(self) -> bool:
        return bool(self.api_token)

    @property
    def rate_limit_enabled(self) -> bool:
        return self.rate_limit > 0


def load_settings() -> Settings:
    max_mb = _int_env("MD_BRIDGE_MAX_UPLOAD_MB", DEFAULT_MAX_UPLOAD_MB, minimum=1)
    token = os.environ.get("MD_BRIDGE_API_TOKEN", "").strip() or None
    if token is not None and not token.isascii():
        # HTTP header values are latin-1; a non-ASCII token cannot round-trip
        # reliably. Fail closed so the operator picks an ASCII token (hex/base64
        # tokens already are) instead of silently rejecting every valid request.
        raise ValueError("MD_BRIDGE_API_TOKEN must be ASCII")
    return Settings(
        max_upload_bytes=max_mb * 1024 * 1024,
        api_token=token,
        # rate_limit 0 disables; the window must be a positive number of
        # seconds or a positive limit could never block (every call would reset
        # its own window).
        rate_limit=_int_env("MD_BRIDGE_RATE_LIMIT", 0, minimum=0),
        rate_window_seconds=_int_env("MD_BRIDGE_RATE_WINDOW_SECONDS", 60, minimum=1),
        max_concurrency=_int_env("MD_BRIDGE_MAX_CONCURRENCY", 2, minimum=1),
        queue_max=_int_env("MD_BRIDGE_QUEUE_MAX", 8, minimum=0),
        queue_wait_seconds=_int_env("MD_BRIDGE_QUEUE_WAIT_SECONDS", 10, minimum=0),
        convert_timeout_seconds=_int_env("MD_BRIDGE_CONVERT_TIMEOUT_SECONDS", 300, minimum=0),
        max_pdf_pages=_int_env("MD_BRIDGE_MAX_PDF_PAGES", 0, minimum=0),
    )
