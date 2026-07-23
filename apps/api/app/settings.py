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


def _int_env(name: str, default: int) -> int:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


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
    max_mb = _int_env("MD_BRIDGE_MAX_UPLOAD_MB", DEFAULT_MAX_UPLOAD_MB)
    token = os.environ.get("MD_BRIDGE_API_TOKEN", "").strip() or None
    return Settings(
        max_upload_bytes=max_mb * 1024 * 1024,
        api_token=token,
        rate_limit=_int_env("MD_BRIDGE_RATE_LIMIT", 0),
        rate_window_seconds=_int_env("MD_BRIDGE_RATE_WINDOW_SECONDS", 60),
    )
