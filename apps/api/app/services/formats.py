"""Format-pair registry (#60).

A single source of truth for the conversion pairs md-bridge knows about. Shipped
pairs carry an `endpoint`; roadmap/wanted pairs are metadata only, so the web
format hub can render the full matrix (with status pills) and link the empty
cells to a feature request. Adding a pair is a one-entry change here.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from app.errors import ApiError

Status = Literal["shipped", "in-pr", "roadmap", "wanted"]

MIME_PDF = "application/pdf"
MIME_MD = "text/markdown"
MIME_DOCX = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
MIME_EPUB = "application/epub+zip"
MIME_HTML = "text/html"
MIME_RTF = "application/rtf"


@dataclass(frozen=True)
class Format:
    slug: str  # e.g. "md-to-docx"
    label: str  # human label, e.g. "Markdown → DOCX"
    source: str  # short source token, e.g. "md"
    target: str  # short target token, e.g. "docx"
    input_mime: str
    output_mime: str
    status: Status
    endpoint: str | None  # the POST route, or None when not shipped

    def to_dict(self) -> dict[str, str | None]:
        return {
            "slug": self.slug,
            "label": self.label,
            "source": self.source,
            "target": self.target,
            "input_mime": self.input_mime,
            "output_mime": self.output_mime,
            "status": self.status,
            "endpoint": self.endpoint,
        }


class UnknownFormatError(ApiError):
    """Raised when a request references a format slug that is not registered."""

    def __init__(self, slug: str) -> None:
        super().__init__(400, "unknown_format", f"Format '{slug}' is not registered.")
        self.slug = slug


# The registry. Shipped pairs first (they have a live endpoint), then the
# roadmap/wanted pairs the hub shows as empty cells.
_FORMATS: tuple[Format, ...] = (
    Format("pdf-to-md", "PDF → Markdown", "pdf", "md", MIME_PDF, MIME_MD, "shipped", "/api/pdf-to-md"),
    Format("md-to-pdf", "Markdown → PDF", "md", "pdf", MIME_MD, MIME_PDF, "shipped", "/api/md-to-pdf"),
    Format("md-to-docx", "Markdown → DOCX", "md", "docx", MIME_MD, MIME_DOCX, "shipped", "/api/md-to-docx"),
    Format("md-to-html", "Markdown → HTML", "md", "html", MIME_MD, MIME_HTML, "roadmap", None),
    Format("md-to-epub", "Markdown → EPUB", "md", "epub", MIME_MD, MIME_EPUB, "roadmap", None),
    Format("docx-to-md", "DOCX → Markdown", "docx", "md", MIME_DOCX, MIME_MD, "wanted", None),
)


def list_formats() -> list[Format]:
    """All registered format pairs, in registry order."""
    return list(_FORMATS)


def get_format(slug: str) -> Format:
    """Return the format for `slug` or raise UnknownFormatError."""
    for fmt in _FORMATS:
        if fmt.slug == slug:
            return fmt
    raise UnknownFormatError(slug)
