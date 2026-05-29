"""Route PyMuPDF's process-global warning buffer to the Python logger.

MuPDF's C runtime writes non-fatal warnings (missing Shading/XObject resources
in malformed PDFs, common in old Word exports) straight to file descriptor 2.
We silence that native display once at app startup
(`pymupdf.TOOLS.mupdf_display_errors(False)` in `create_app`) and drain the
internal buffer here, so the warnings reach the configured logger with context
instead of polluting container stderr with unstructured, level-less lines.

The display flag and the warning buffer are PROCESS-GLOBAL in PyMuPDF: there is
no per-document or thread-local sink in 1.27.x. Under concurrent conversions
(`asyncio.to_thread`) two interleaved documents share one buffer, so the
per-file `warning_count` logged here is approximate. That is an accepted
trade-off for a self-hosted, low-concurrency service: the operational signal we
want is "this request touched a malformed PDF", not an exact per-file tally.
"""
from __future__ import annotations

import logging
from collections.abc import Iterator
from contextlib import contextmanager

import pymupdf


@contextmanager
def capture_mupdf_warnings(logger: logging.Logger, *, filename: str) -> Iterator[None]:
    """Drain MuPDF's warning buffer around a block and log it as one WARNING.

    Resets the buffer on entry so stale warnings from an earlier call are not
    misattributed, then on exit drains whatever the wrapped MuPDF work produced.
    A WARNING record is emitted only when the buffer is non-empty.
    """
    pymupdf.TOOLS.reset_mupdf_warnings()
    try:
        yield
    finally:
        buf = pymupdf.TOOLS.mupdf_warnings(reset=True)
        if buf:
            count = len(buf.splitlines())
            logger.warning(
                "mupdf-warnings filename=%s warning_count=%d",
                filename,
                count,
                # Structured context for log processors: the count and the raw
                # buffer ride along as record attributes, not just in the text.
                extra={"warning_count": count, "mupdf_warnings": buf},
            )
