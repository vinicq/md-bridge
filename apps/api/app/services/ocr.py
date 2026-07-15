"""Optional Tesseract OCR pre-pass for scanned PDFs."""
from __future__ import annotations

import io
import os
import shutil

import pymupdf

from app.errors import ApiError

_TRUTHY = {"1", "true", "yes", "on"}
_FALSY = {"0", "false", "no", "off"}

# Multi-language Tesseract set so a scanned document is read without an
# operator configuring a per-document language. Tesseract scores each region
# across all three models, which is deterministic given the same input and the
# same installed traineddata. PT-PT and PT-BR share a single `por` model. A
# narrower per-document auto-detect (first-pass language ID) is a follow-up;
# `MD_BRIDGE_OCR_LANG` stays the override escape hatch. (#199)
DEFAULT_OCR_LANG = "eng+por+spa"


def get_lang() -> str:
    return os.getenv("MD_BRIDGE_OCR_LANG", DEFAULT_OCR_LANG)


# OCR rasterizes every page at 300 DPI (see `ocr_pdf_bytes`), so a very long
# scan is a memory/time bomb on a shared or hosted deployment. The cap is the
# guard the docstring already asks callers to enforce. Default 0 means "no cap":
# a self-hosted operator converting their own documents keeps the permissive
# behavior and byte-identical output, while a hosted demo sets the env var to a
# finite page budget. (#208)
DEFAULT_OCR_MAX_PAGES = 0


def get_max_pages() -> int:
    """Page budget for the OCR pre-pass; 0 (the default) disables the cap.

    A malformed or non-numeric `MD_BRIDGE_OCR_MAX_PAGES` falls back to the
    permissive default rather than failing the request.
    """
    raw = os.getenv("MD_BRIDGE_OCR_MAX_PAGES")
    if raw is None or not raw.strip():
        return DEFAULT_OCR_MAX_PAGES
    try:
        value = int(raw.strip())
    except ValueError:
        return DEFAULT_OCR_MAX_PAGES
    return value if value > 0 else DEFAULT_OCR_MAX_PAGES


# Per-page wall-clock budget for the Tesseract call. MD_BRIDGE_OCR_MAX_PAGES
# caps how many pages run, not how long one page may take, so a single dense
# page could pin the worker thread forever. The repo rule is that every
# subprocess invocation carries an explicit timeout (#364).
DEFAULT_OCR_PAGE_TIMEOUT = 60


def get_page_timeout() -> int:
    """Seconds a single page's Tesseract run may take before it is killed.

    A malformed or non-positive `MD_BRIDGE_OCR_PAGE_TIMEOUT` falls back to the
    default rather than failing the request.
    """
    raw = os.getenv("MD_BRIDGE_OCR_PAGE_TIMEOUT")
    if raw is None or not raw.strip():
        return DEFAULT_OCR_PAGE_TIMEOUT
    try:
        value = int(raw.strip())
    except ValueError:
        return DEFAULT_OCR_PAGE_TIMEOUT
    return value if value > 0 else DEFAULT_OCR_PAGE_TIMEOUT


def ocr_stack_available() -> bool:
    """True when both halves of the OCR stack are installed: the Tesseract
    binary on PATH and the `pytesseract` Python binding (the `[ocr]` extra)."""
    if shutil.which("tesseract") is None:
        return False
    try:
        import pytesseract  # noqa: F401
    except ImportError:
        return False
    return True


def is_enabled() -> bool:
    """Whether the OCR pre-pass should run for a scanned PDF.

    The default is automatic: OCR runs when the stack is actually installed,
    because installing the `[ocr]` extra or the `runtime-ocr` image *is* the
    act of opting in. A lean base install carries neither the binary nor the
    binding, so OCR stays off and a scanned PDF returns the same 422
    `ocr_required` as before. `MD_BRIDGE_OCR_ENABLED` overrides the auto
    decision either way: `1`/`true`/`yes`/`on` forces it on, `0`/`false`/`no`/
    `off` forces it off (e.g. to keep a slow OCR pass out of a hot path).
    """
    flag = os.getenv("MD_BRIDGE_OCR_ENABLED")
    if flag is not None and flag.strip():
        value = flag.strip().lower()
        if value in _TRUTHY:
            return True
        if value in _FALSY:
            return False
    return ocr_stack_available()


def ocr_pdf_bytes(pdf_bytes: bytes, lang: str = DEFAULT_OCR_LANG) -> bytes:
    """Return a new PDF with a searchable text layer over each rasterized page.

    This rasterizes every page at 300 DPI and can be memory/time heavy; callers
    should enforce upload or page-count limits before enabling OCR in production.
    """

    import pytesseract
    from PIL import Image

    timeout = get_page_timeout()
    src = pymupdf.open(stream=pdf_bytes, filetype="pdf")
    out = pymupdf.open()
    try:
        for page_index, page in enumerate(src):
            pix = page.get_pixmap(dpi=300)
            img = Image.open(io.BytesIO(pix.tobytes("png")))

            try:
                pdf_page_bytes = pytesseract.image_to_pdf_or_hocr(
                    img, lang=lang, extension="pdf", timeout=timeout
                )
            except RuntimeError as exc:
                # pytesseract raises RuntimeError when it kills a run that
                # exceeded the timeout. Name the page so the operator can raise
                # the budget or split the document (#364).
                raise ApiError(
                    500,
                    "ocr_failed",
                    f"OCR timed out on page {page_index + 1} after {timeout}s. "
                    "Raise MD_BRIDGE_OCR_PAGE_TIMEOUT or split the document.",
                    detail=str(exc),
                ) from exc
            page_pdf = pymupdf.open(stream=pdf_page_bytes, filetype="pdf")
            try:
                out.insert_pdf(page_pdf)
            finally:
                page_pdf.close()

        return out.tobytes()

    finally:
        out.close()
        src.close()
