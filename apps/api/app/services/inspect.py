"""PDF diagnostics for the inspect endpoint.

Reuses `check_tagged` from the vendored inspector. Everything else (sizes,
fonts, OCR heuristic) is computed directly with PyMuPDF to keep the result
shape stable.
"""
from __future__ import annotations

import logging
import tempfile
from collections import Counter
from pathlib import Path

import fitz

from app.schemas.convert import FontUsage, InspectPdfResponse
from app.services.mupdf_log import capture_mupdf_warnings
from app.services.packages_loader import pdf_inspect_module

log = logging.getLogger(__name__)


def inspect_pdf_bytes(pdf_bytes: bytes, filename: str) -> InspectPdfResponse:
    tmp_dir = Path(tempfile.mkdtemp(prefix="md-bridge-inspect-"))
    tmp_path = tmp_dir / "input.pdf"
    tmp_path.write_bytes(pdf_bytes)
    try:
        with capture_mupdf_warnings(log, filename=filename), fitz.open(tmp_path) as doc:
            size_counter: Counter[float] = Counter()
            font_counter: Counter[tuple[float, str]] = Counter()
            samples: dict[tuple[float, str], str] = {}

            for page in doc:
                data = page.get_text("dict")
                for raw_block in data.get("blocks", []):
                    if raw_block.get("type") != 0:
                        continue
                    for line in raw_block.get("lines", []):
                        for span in line.get("spans", []):
                            text = span["text"].strip()
                            if not text:
                                continue
                            size = round(float(span["size"]), 1)
                            font = str(span["font"])
                            chars = len(text)
                            size_counter[size] += chars
                            key = (size, font)
                            font_counter[key] += chars
                            if key not in samples:
                                samples[key] = text[:80]

            page_count = doc.page_count
            total_chars = sum(size_counter.values())

        if size_counter:
            body_size = float(size_counter.most_common(1)[0][0])
        else:
            body_size = 0.0
        heading_sizes = sorted(
            (s for s in size_counter if s > body_size + 0.5),
            reverse=True,
        )[:5]
        fonts = [
            FontUsage(name=name, size=size, count=count, sample=samples[(size, name)])
            for (size, name), count in font_counter.most_common(20)
        ]

        # Tagged-PDF check via the vendored inspector helper (works on a path).
        tag_info = pdf_inspect_module().check_tagged(tmp_path)
        tagged = bool(tag_info.get("tagged"))

        # Needs-OCR heuristic: fewer than ~40 extractable chars per page on
        # average is a strong signal the PDF is image-only.
        needs_ocr = page_count > 0 and (total_chars / page_count) < 40.0

        return InspectPdfResponse(
            pages=page_count,
            body_size_pt=body_size,
            heading_sizes_pt=heading_sizes,
            fonts=fonts,
            tagged=tagged,
            needs_ocr=needs_ocr,
        )
    finally:
        try:
            tmp_path.unlink(missing_ok=True)
        except OSError:
            # Best-effort temp cleanup; the OS will reap stale files.
            pass
        try:
            tmp_dir.rmdir()
        except OSError:
            # Best-effort temp cleanup; the OS will reap stale dirs.
            pass
