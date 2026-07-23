"""PDF diagnostics route."""
from __future__ import annotations

import asyncio
import logging
import time

from fastapi import APIRouter, Depends, File, Request, UploadFile

from app.errors import ApiError
from app.rate_limit import enforce_rate_limit
from app.schemas.convert import InspectPdfResponse
from app.security import require_api_key
from app.services.inspect import inspect_pdf_bytes

router = APIRouter(tags=["inspect"])
log = logging.getLogger(__name__)


INSPECT_DESCRIPTION = """
Run cheap diagnostics on a PDF without converting it.

Useful as a pre-flight check before `/api/pdf-to-md` so the UI can warn the
user about scanned PDFs (which need OCR first), show the inferred body font
size, detect PDF/UA tagging, and list the fonts in use.

### Quick curl example

```bash
curl -X POST http://localhost:8000/api/inspect-pdf \\
  -F "file=@whitepaper.pdf"
```

### Response

```json
{
  "pages": 4,
  "body_size_pt": 11.0,
  "heading_sizes_pt": [18.0, 14.0, 12.5],
  "fonts": [{"name": "InterRegular", "size": 11.0, "count": 12048, "sample": "Lorem ipsum..."}],
  "tagged": true,
  "needs_ocr": false
}
```

`needs_ocr=true` means PyMuPDF extracted very little text per page. The PDF
is almost certainly scanned, so run Tesseract before submitting.
"""


_INSPECT_EXAMPLE = {
    "pages": 4,
    "body_size_pt": 11.0,
    "heading_sizes_pt": [18.0, 14.0, 12.5],
    "fonts": [
        {"name": "InterRegular", "size": 11.0, "count": 12048, "sample": "Lorem ipsum..."},
        {"name": "InterBold", "size": 18.0, "count": 320, "sample": "Introduction"},
    ],
    "tagged": True,
    "needs_ocr": False,
}


@router.post(
    "/api/inspect-pdf",
    response_model=InspectPdfResponse,
    dependencies=[Depends(enforce_rate_limit), Depends(require_api_key)],
    summary="Inspect a PDF (fonts, sizes, tagged, OCR hint)",
    description=INSPECT_DESCRIPTION,
    response_description="Diagnostics about the uploaded PDF.",
    responses={
        200: {"content": {"application/json": {"example": _INSPECT_EXAMPLE}}},
        400: {"description": "Upload is not a PDF."},
        413: {"description": "Upload exceeds the 500 MB cap."},
    },
)
async def inspect_pdf(
    request: Request,
    file: UploadFile = File(..., description="The PDF to inspect."),
) -> InspectPdfResponse:
    max_upload_bytes = request.app.state.settings.max_upload_bytes
    name = file.filename or ""
    if not name.lower().endswith(".pdf"):
        raise ApiError(
            400,
            "wrong_file_type",
            f"Expected a PDF (.pdf), got: {name or 'unnamed upload'}",
        )

    data = bytearray()
    while True:
        chunk = await file.read(1024 * 1024)
        if not chunk:
            break
        data.extend(chunk)
        if len(data) > max_upload_bytes:
            raise ApiError(
                413,
                "payload_too_large",
                f"Upload exceeds {max_upload_bytes // (1024 * 1024)} MB limit.",
            )

    started = time.perf_counter()
    result = await asyncio.to_thread(inspect_pdf_bytes, bytes(data), name)
    elapsed_ms = int((time.perf_counter() - started) * 1000)
    log.info(
        "inspect-pdf filename=%s bytes=%d duration_ms=%d pages=%d tagged=%s",
        name,
        len(data),
        elapsed_ms,
        result.pages,
        result.tagged,
    )
    return result
