"""Input caps enforced before a conversion consumes a concurrency slot."""
from __future__ import annotations

import asyncio

import pymupdf

from app.errors import ApiError


def _page_count(pdf_bytes: bytes) -> int | None:
    try:
        with pymupdf.open(stream=pdf_bytes, filetype="pdf") as doc:
            return doc.page_count
    except Exception:  # noqa: BLE001 - malformed PDF: let the converter report it
        return None


async def enforce_pdf_page_cap(pdf_bytes: bytes, max_pages: int) -> None:
    """Reject a PDF whose page count exceeds max_pages (0 disables the cap).

    Runs before the concurrency gate so an oversized document does not occupy a
    slot. Parsing the page tree (no rendering) is cheap, but a large or
    adversarial PDF could still block the single-worker event loop, so it runs
    in a worker thread. A PDF that fails to open is left for the converter to
    report; this guard only rejects well-formed PDFs that are simply too long.
    """
    if max_pages <= 0:
        return
    pages = await asyncio.to_thread(_page_count, pdf_bytes)
    if pages is not None and pages > max_pages:
        raise ApiError(
            422,
            "too_many_pages",
            f"PDF has {pages} pages; the limit is {max_pages}.",
        )
