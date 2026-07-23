"""Optional API-key access control.

Off by default: with no MD_BRIDGE_API_TOKEN set, `require_api_key` is a no-op
and the service behaves exactly as before. Set the token and the expensive
conversion routes require a matching `X-API-Key` header.

This guards programmatic clients (curl, CI). It does NOT gate the bundled
same-origin web UI, since an anonymous browser has no token to send: to lock
the whole surface including the HTML, put basic-auth or SSO at the Caddy edge
(documented in the deploy guide), not here.
"""
from __future__ import annotations

import hmac

from fastapi import Request, Security
from fastapi.security import APIKeyHeader

from app.errors import ApiError

_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def require_api_key(
    request: Request, key: str | None = Security(_api_key_header)
) -> None:
    settings = request.app.state.settings
    if not settings.auth_enabled:
        return
    # compare_digest is constant-time; guard the empty-header case first so we
    # never call it with None.
    if not key or not hmac.compare_digest(key, settings.api_token):
        raise ApiError(401, "unauthorized", "Missing or invalid API key.")
