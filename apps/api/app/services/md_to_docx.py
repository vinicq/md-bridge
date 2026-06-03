"""Wrapper around the vendored markdown-to-docx converter (#60).

Converts Markdown bytes to a deterministic .docx via the vendored skill script
and returns the bytes. The converter is pure Python (python-docx); no native
dependency and no tempfile dance needed since it works on bytes directly.
"""
from __future__ import annotations

from app.errors import ApiError
from app.schemas.convert import MdToDocxOptions
from app.services.packages_loader import md_to_docx_module


def render_md_to_docx_bytes(
    md_bytes: bytes,
    *,
    filename: str,
    options: MdToDocxOptions | None = None,
) -> bytes:
    _ = options or MdToDocxOptions()  # reserved; converter takes no tunables yet
    mod = md_to_docx_module()

    try:
        md_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ApiError(
            400,
            "invalid_markdown",
            "Uploaded file is not valid UTF-8 markdown.",
        ) from exc

    try:
        return mod.convert_bytes(md_bytes)
    except Exception as exc:  # noqa: BLE001 - surface any converter failure as 500
        raise ApiError(
            500,
            "convert_failed",
            f"Markdown to DOCX conversion failed: {exc.__class__.__name__}",
            detail=str(exc),
        ) from exc
