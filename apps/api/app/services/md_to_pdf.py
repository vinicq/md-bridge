"""Wrapper around the vendored markdown-to-pdf renderer.

Renders Markdown to a PDF via the existing Playwright-backed convert script.
Writes through tempfiles, returns the PDF bytes, cleans up everything.
"""
from __future__ import annotations

import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from app.config import MD_TO_PDF_TEMPLATES
from app.errors import ApiError
from app.schemas.convert import MdToPdfOptions
from app.services.skills_loader import md_to_pdf_module


def _css_paths_for_theme(theme_id: str) -> list[Path]:
    default_css = MD_TO_PDF_TEMPLATES / "default.css"
    if theme_id == "default":
        if not default_css.exists():
            raise ApiError(
                500,
                "missing_template",
                f"default theme stylesheet not found at {default_css}",
            )
        return [default_css]

    extra = MD_TO_PDF_TEMPLATES / f"{theme_id}.css"
    if not extra.exists():
        raise ApiError(
            400,
            "unknown_theme",
            f"theme '{theme_id}' not found",
            detail={"available": [p.stem for p in MD_TO_PDF_TEMPLATES.glob("*.css")]},
        )
    # Layer the chosen theme on top of the default so theme files only need
    # to override what they care about.
    return [default_css, extra] if default_css.exists() else [extra]


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
    css_paths = _css_paths_for_theme(opts.theme)
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
