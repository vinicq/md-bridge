"""Runtime configuration. Paths and limits used across the API."""
from __future__ import annotations

from pathlib import Path

# Repo root is three levels up from this file: apps/api/app/config.py
REPO_ROOT = Path(__file__).resolve().parents[3]

PACKAGES_DIR = REPO_ROOT / "packages"
PDF_TO_MD_SCRIPT = PACKAGES_DIR / "pdf-to-markdown" / "scripts" / "convert.py"
PDF_INSPECT_SCRIPT = PACKAGES_DIR / "pdf-to-markdown" / "scripts" / "inspect_pdf.py"
MD_TO_PDF_SCRIPT = PACKAGES_DIR / "markdown-to-pdf" / "scripts" / "convert.py"
MD_TO_PDF_TEMPLATES = PACKAGES_DIR / "markdown-to-pdf" / "templates"
MD_TO_DOCX_SCRIPT = PACKAGES_DIR / "markdown-to-docx" / "scripts" / "convert.py"

# Upload limits
MAX_UPLOAD_BYTES = 500 * 1024 * 1024  # 500 MB

# CORS origins for local dev. Vite default + alt port.
CORS_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:4173",
]
