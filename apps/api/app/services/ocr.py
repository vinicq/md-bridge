"""Optional Tesseract OCR pre-pass for scanned PDFs."""
from __future__ import annotations

import io
import os

import pymupdf

DEFAULT_OCR_LANG = "eng+por"


def get_lang() -> str:
    return os.getenv("MD_BRIDGE_OCR_LANG", DEFAULT_OCR_LANG)


def is_enabled() -> bool:
    return os.getenv("MD_BRIDGE_OCR_ENABLED") == "1"


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
