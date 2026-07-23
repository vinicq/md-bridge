"""FastAPI application factory."""
from __future__ import annotations

import logging

import pymupdf
from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse

from app import __version__
from app.config import CORS_ORIGINS
from app.errors import (
    ApiError,
    api_error_handler,
    http_exception_handler,
    validation_exception_handler,
)
from app.logging_filters import install_health_access_filter
from app.rate_limit import get_limiter
from app.routes import convert, health, inspect
from app.security import api_key_ok
from app.settings import load_settings

# Expensive routes that spool an upload and drive Chromium/PyMuPDF. Auth and
# rate limiting guard these; health, themes, and formats stay open.
_GUARDED_POST_PATHS = frozenset(
    {"/api/pdf-to-md", "/api/md-to-pdf", "/api/md-to-docx", "/api/inspect-pdf"}
)


def _error_response(status: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(status_code=status, content={"error": {"code": code, "message": message}})

API_DESCRIPTION = """
**md-bridge** is a small, opinionated HTTP service that converts between PDF
and Markdown using hand-written heuristics. No external calls, deterministic
output: same input, same output, every run.

## What it does

- **`POST /api/pdf-to-md`**: extract structured Markdown from a PDF.
- **`POST /api/md-to-pdf`**: render a Markdown file to PDF through Chromium.
- **`POST /api/inspect-pdf`**: return diagnostics about a PDF (fonts, sizes, tagged-PDF check).
- **`GET  /api/health`**: liveness probe.

## Try it out

The interactive docs you are reading right now (powered by Swagger UI) let
you call any endpoint with a real file. Click **Try it out**, attach a file,
press **Execute**.

A walkthrough with `curl` examples lives in
[docs/API.md](https://github.com/vinicq/md-bridge/blob/main/docs/API.md).

## Limits

- Upload cap: deployment-configurable via `MD_BRIDGE_MAX_UPLOAD_MB` (default 500 MB).
- No persistence: every file is processed in a temporary directory and removed
  when the conversion finishes, before the response in the normal case. The one
  exception is a conversion that hits `MD_BRIDGE_CONVERT_TIMEOUT_SECONDS`: the
  504 returns while the abandoned worker still holds its temp directory, which
  is removed when that worker exits.
- No OCR (v1): scanned PDFs need Tesseract before being submitted.
"""


def create_app() -> FastAPI:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s :: %(message)s",
    )

    # Silence MuPDF's native stderr once for the whole process. The C runtime
    # otherwise writes non-fatal warnings (missing Shading/XObject resources in
    # malformed PDFs) straight to fd 2, unstructured and level-less. The flag is
    # process-global by design in PyMuPDF; services drain the captured buffer
    # through `app.services.mupdf_log` and re-emit it on the Python logger.
    pymupdf.TOOLS.mupdf_display_errors(False)

    # Drop the ~1/s healthcheck probes from the uvicorn access log so real
    # requests stay visible (opt out with MD_BRIDGE_LOG_HEALTH=true).
    install_health_access_filter()

    app = FastAPI(
        title="md-bridge API",
        version=__version__,
        summary="Deterministic, heuristic conversions between PDF and Markdown.",
        description=API_DESCRIPTION,
        contact={
            "name": "md-bridge",
            "url": "https://github.com/vinicq/md-bridge",
        },
        license_info={"name": "MIT", "url": "https://opensource.org/licenses/MIT"},
        openapi_tags=[
            {"name": "health", "description": "Service liveness."},
            {
                "name": "convert",
                "description": "Conversion endpoints between PDF and Markdown.",
            },
            {
                "name": "inspect",
                "description": "Read-only diagnostics about an uploaded PDF.",
            },
        ],
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Read env-driven settings once per app instance (not at import), so a test
    # can build a fresh app with different env and every route sees it via
    # request.app.state.settings.
    app.state.settings = load_settings()

    # Middleware is registered inner-to-outer: the LAST added wraps the others.
    # Add access control FIRST so it is innermost, then security headers, then
    # CORS last (outermost). That order still runs access control before the
    # route (so before body parsing), while letting its early 401/429 responses
    # travel back out through the header and CORS wrappers.

    # Access control BEFORE the route runs, so a missing key or an over-quota
    # client is rejected before FastAPI parses and spools the multipart body.
    # A route dependency would run after body parsing and let the upload in.
    # Auth is checked before the rate limit so rejected traffic does not consume
    # the (per-instance, shared behind a proxy) quota.
    @app.middleware("http")
    async def _access_control(request, call_next):
        # Match on the root-path-relative path: under a mount prefix or uvicorn
        # --root-path, request.url.path can carry that prefix while routing
        # strips it, which would otherwise slip a prefixed request past the
        # guard. Stripping is a no-op when root_path is empty (the shipped case).
        path = request.url.path
        root = request.scope.get("root_path", "")
        if root and path.startswith(root):
            path = path[len(root):] or "/"
        if request.method == "POST" and path in _GUARDED_POST_PATHS:
            settings = request.app.state.settings
            if settings.auth_enabled and not api_key_ok(
                settings.api_token, request.headers.get("X-API-Key")
            ):
                return _error_response(401, "unauthorized", "Missing or invalid API key.")
            if settings.rate_limit_enabled:
                limiter = get_limiter(request.app)
                client_ip = request.client.host if request.client else "unknown"
                if not limiter.allow(client_ip):
                    return _error_response(
                        429, "rate_limited", "Too many requests. Try again later."
                    )
        return await call_next(request)

    # Baseline security headers on every API response. HSTS and a full CSP for
    # the HTML belong at the TLS-terminating proxy (Caddy), not here where there
    # is no TLS context; these three travel with the app on any deploy.
    @app.middleware("http")
    async def _security_headers(request, call_next):
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("Referrer-Policy", "no-referrer")
        response.headers.setdefault("X-Frame-Options", "DENY")
        return response

    app.add_middleware(
        CORSMiddleware,
        allow_origins=CORS_ORIGINS,
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
        # So a cross-origin browser client can read Retry-After on a 503.
        expose_headers=["Retry-After"],
    )

    app.add_exception_handler(ApiError, api_error_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)

    app.include_router(health.router)
    app.include_router(convert.router)
    app.include_router(inspect.router)

    # Document the X-API-Key scheme in OpenAPI as OPTIONAL. Enforcement lives in
    # the middleware above, not a dependency, so the schema is not generated
    # automatically. Declaring it optional (an empty requirement alongside the
    # key) gives /docs an Authorize control and tells generated clients about
    # the header, without claiming auth is mandatory on an open default deploy.
    def _custom_openapi() -> dict:
        if app.openapi_schema:
            return app.openapi_schema
        schema = get_openapi(
            title=app.title,
            version=app.version,
            summary=app.summary,
            description=app.description,
            routes=app.routes,
            tags=app.openapi_tags,
            contact=app.contact,
            license_info=app.license_info,
        )
        schema.setdefault("components", {}).setdefault("securitySchemes", {})["APIKeyHeader"] = {
            "type": "apiKey",
            "in": "header",
            "name": "X-API-Key",
            "description": (
                "Required only when the server sets MD_BRIDGE_API_TOKEN. "
                "Omit it on an open deployment."
            ),
        }
        error_content = {
            "application/json": {
                "schema": {
                    "type": "object",
                    "properties": {
                        "error": {
                            "type": "object",
                            "properties": {
                                "code": {"type": "string"},
                                "message": {"type": "string"},
                            },
                            "required": ["code", "message"],
                        }
                    },
                    "required": ["error"],
                }
            }
        }
        guarded_responses = {
            "401": {
                "description": "Missing or invalid API key (when MD_BRIDGE_API_TOKEN is set).",
                "content": error_content,
            },
            "429": {
                "description": "Rate limit exceeded (when MD_BRIDGE_RATE_LIMIT is set).",
                "content": error_content,
            },
            "503": {
                "description": "Service at capacity.",
                "headers": {
                    "Retry-After": {
                        "schema": {"type": "string"},
                        "description": "Seconds to wait before retrying.",
                    }
                },
                "content": error_content,
            },
            "504": {
                "description": "Conversion exceeded MD_BRIDGE_CONVERT_TIMEOUT_SECONDS.",
                "content": error_content,
            },
        }
        for path in _GUARDED_POST_PATHS:
            operation = schema.get("paths", {}).get(path, {}).get("post")
            if operation is not None:
                operation["security"] = [{}, {"APIKeyHeader": []}]
                responses = operation.setdefault("responses", {})
                for status, body in guarded_responses.items():
                    responses.setdefault(status, body)
                # The app's 422 handler returns the same error envelope, not
                # FastAPI's default HTTPValidationError, so override it to match
                # (covers invalid options and rejected input like too_many_pages).
                responses["422"] = {
                    "description": "Invalid options or a rejected input (e.g. too many pages).",
                    "content": error_content,
                }
        app.openapi_schema = schema
        return schema

    app.openapi = _custom_openapi

    return app


app = create_app()
