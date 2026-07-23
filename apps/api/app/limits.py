"""Input caps for conversions.

The page-cap check is synchronous and is called inside the gated worker thread
(via run_bounded), so it runs off the event loop AND under the concurrency
semaphore. That keeps a burst of adversarial PDFs from parsing unbounded, at
the cost of a rejected PDF briefly holding a slot for the (cheap) page-tree
parse before it is turned away.
"""
from __future__ import annotations

import pymupdf

from app.errors import ApiError


def check_pdf_page_cap(pdf_bytes: bytes, max_pages: int) -> None:
    """Raise 422 if the PDF has more than max_pages pages (0 disables the cap).

    Parses only the page tree (no rendering). A PDF that fails to open is left
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
