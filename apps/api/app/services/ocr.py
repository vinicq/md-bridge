"""Optional Tesseract OCR pre-pass for scanned PDFs."""
from __future__ import annotations

import io
import os

import pymupdf

DEFAULT_OCR_LANG = "eng+por"


def is_enabled() -> bool:
    return os.getenv("MD_BRIDGE_OCR_ENABLED") == "1"


def ocr_pdf_bytes(pdf_bytes: bytes, lang: str = DEFAULT_OCR_LANG) -> bytes:
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
