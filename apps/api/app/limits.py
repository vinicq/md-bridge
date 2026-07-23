"""Input caps enforced before a conversion consumes a concurrency slot."""
from __future__ import annotations

import pymupdf

from app.errors import ApiError


def enforce_pdf_page_cap(pdf_bytes: bytes, max_pages: int) -> None:
    """Reject a PDF whose page count exceeds max_pages (0 disables the cap).

    Parses only the page tree (no rendering), so it is cheap relative to the
    conversion it guards, and it runs before the concurrency gate so an
    oversized document does not occupy a slot. A PDF that fails to open is left
    for the converter to report; this guard only rejects well-formed PDFs that
    are simply too long.
    """
    if max_pages <= 0:
        return
    try:
        with pymupdf.open(stream=pdf_bytes, filetype="pdf") as doc:
            pages = doc.page_count
    except Exception:  # noqa: BLE001 - malformed PDF: let the converter report it
        return
    if pages > max_pages:
        raise ApiError(
            422,
            "too_many_pages",
            f"PDF has {pages} pages; the limit is {max_pages}.",
        )
