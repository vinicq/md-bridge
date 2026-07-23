"""FastAPI application factory."""
from __future__ import annotations

import logging

import pymupdf
from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
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

- Upload cap: **500 MB** per request.
- No persistence: every file is processed in a temporary directory and removed
  before the response is returned.
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

    app.add_middleware(
        CORSMiddleware,
        allow_origins=CORS_ORIGINS,
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )

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

    # Access control BEFORE the route runs, so a missing key or an over-quota
    # client is rejected before FastAPI parses and spools the multipart body.
    # A route dependency would run after body parsing and let the upload in.
    # Auth is checked before the rate limit so rejected traffic does not consume
    # the (per-instance, shared behind a proxy) quota.
    @app.middleware("http")
    async def _access_control(request, call_next):
        if request.method == "POST" and request.url.path in _GUARDED_POST_PATHS:
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

    app.add_exception_handler(ApiError, api_error_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)

    app.include_router(health.router)
    app.include_router(convert.router)
    app.include_router(inspect.router)

    return app


app = create_app()
