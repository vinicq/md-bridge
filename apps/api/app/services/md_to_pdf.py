"""Wrapper around the vendored markdown-to-pdf renderer.

Renders Markdown to a PDF via the existing Playwright-backed convert script.
Writes through tempfiles, returns the PDF bytes, cleans up everything.
"""
from __future__ import annotations

import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from app.config import MD_TO_PDF_TEMPLATES
from app.errors import ApiError
from app.schemas.convert import MdToPdfOptions
from app.services.packages_loader import md_to_pdf_module


def _default_css_paths() -> list[Path]:
    default_css = MD_TO_PDF_TEMPLATES / "default.css"
    if not default_css.exists():
        raise ApiError(
            500,
            "missing_template",
            f"default theme stylesheet not found at {default_css}",
        )
    return [default_css]


@contextmanager
def _tempdir() -> Iterator[Path]:
    with tempfile.TemporaryDirectory(prefix="md-bridge-md2pdf-") as raw:
        yield Path(raw)


def render_md_bytes(
    md_bytes: bytes,
    *,
    filename: str,
    options: MdToPdfOptions | None = None,
) -> bytes:
    opts = options or MdToPdfOptions()
    css_paths = _default_css_paths()
    mod = md_to_pdf_module()

    with _tempdir() as tmp:
        safe_stem = Path(filename).stem or "document"
        md_path = tmp / f"{safe_stem}.md"
        pdf_path = tmp / f"{safe_stem}.pdf"

        try:
            md_text = md_bytes.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ApiError(
                400,
                "invalid_markdown",
                "Uploaded file is not valid UTF-8 markdown.",
            ) from exc

        md_path.write_text(md_text, encoding="utf-8")

        try:
            mod.convert(md_path, pdf_path, css_paths, lang=opts.lang)
        except Exception as exc:
            raise ApiError(
                500,
                "render_failed",
                f"Markdown rendering failed: {exc.__class__.__name__}",
                detail=str(exc),
            ) from exc

        if not pdf_path.exists():
            raise ApiError(500, "render_failed", "Renderer produced no PDF output.")
        return pdf_path.read_bytes()
