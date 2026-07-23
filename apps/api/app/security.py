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
    # Starlette decodes request headers as latin-1, so `provided` is the raw
    # header bytes reinterpreted as latin-1. Encode both sides with latin-1 to
    # compare the original bytes. The configured token is validated ASCII at
    # startup (settings.load_settings), and ASCII is a subset of latin-1, so a
    # client sending the token's ASCII bytes matches exactly.
    return hmac.compare_digest(provided.encode("latin-1"), expected.encode("latin-1"))
