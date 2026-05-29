"""FastAPI application factory."""
from __future__ import annotations

import logging

import pymupdf
from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.config import CORS_ORIGINS
from app.errors import (
    ApiError,
    api_error_handler,
    http_exception_handler,
    validation_exception_handler,
)
from app.logging_filters import install_health_access_filter
from app.routes import convert, health, inspect

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

    app.add_middleware(
        CORSMiddleware,
        allow_origins=CORS_ORIGINS,
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )

    app.add_exception_handler(ApiError, api_error_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)

    app.include_router(health.router)
    app.include_router(convert.router)
    app.include_router(inspect.router)

    return app


app = create_app()
