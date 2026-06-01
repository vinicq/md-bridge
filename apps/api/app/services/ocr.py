"""Optional Tesseract OCR pre-pass for scanned PDFs."""
from __future__ import annotations

import io
import os
import shutil

import pymupdf

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

    src = pymupdf.open(stream=pdf_bytes, filetype="pdf")
    out = pymupdf.open()
    try:
        for page in src:
            pix = page.get_pixmap(dpi=300)
            img = Image.open(io.BytesIO(pix.tobytes("png")))

            pdf_page_bytes = pytesseract.image_to_pdf_or_hocr(
                img, lang=lang, extension="pdf"
            )
            page_pdf = pymupdf.open(stream=pdf_page_bytes, filetype="pdf")
            try:
                out.insert_pdf(page_pdf)
            finally:
                page_pdf.close()

        return out.tobytes()

    finally:
        out.close()
        src.close()
