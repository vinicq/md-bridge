"""API-key check.

Enforced in the access-control middleware (app.main), not as a route
dependency: FastAPI parses and spools the multipart body before route
dependencies run, so a dependency-based check would let an unauthenticated
upload be ingested before the 401. The middleware runs before body parsing.
"""
from __future__ import annotations

import hmac


def api_key_ok(expected: str, provided: str | None) -> bool:
    if not provided:
        return False
    # Compare as bytes: hmac.compare_digest's str form is ASCII-only and raises
    # TypeError on a non-ASCII key or header, which would surface as a 500.
    return hmac.compare_digest(provided.encode("utf-8"), expected.encode("utf-8"))
