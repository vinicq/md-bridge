"""PDF↔Markdown conversion routes."""
from __future__ import annotations

import asyncio
import json
import logging
import time

from fastapi import APIRouter, File, Form, Query, UploadFile
from fastapi.responses import Response
from pydantic import ValidationError

from app.config import MAX_UPLOAD_BYTES
from app.errors import ApiError
from app.schemas.convert import MdToPdfOptions, PdfToMdOptions, PdfToMdResponse
from app.services.md_to_pdf import render_md_bytes
from app.services.pdf_to_md import convert_pdf_bytes

router = APIRouter(tags=["convert"])
log = logging.getLogger(__name__)


PDF_TO_MD_DESCRIPTION = """
Extract a structured Markdown document from a PDF.

The conversion is deterministic and heuristic. Headings are detected from
font size and the PDF outline, lists from bullet glyphs, tables from
PyMuPDF's table finder.

### Request

`multipart/form-data` with two fields:

| field | required | description |
|---|---|---|
| `file` | yes | A `.pdf` file (max 500 MB). |
| `options` | no | JSON string with the keys below. |

```json
{
  "page_break": false,
  "with_images": false,
  "front_matter": true,
  "lang": "en"
}
```

### Quick curl example

```bash
curl -X POST http://localhost:8000/api/pdf-to-md \\
  -F "file=@whitepaper.pdf" \\
  -F 'options={"front_matter": true}'
```

### Error envelope

Every failure returns:

```json
{ "error": { "code": "<machine_readable>", "message": "<human>", "detail": <optional> } }
```
"""

MD_TO_PDF_DESCRIPTION = """
Render a Markdown file (UTF-8) into a PDF through headless Chromium.

The rendering uses a bundled A4 CSS theme
(`packages/markdown-to-pdf/templates/default.css`).

### Request

`multipart/form-data`:

| field | required | description |
|---|---|---|
| `file` | yes | A `.md` file (max 500 MB), UTF-8. |
| `options` | no | JSON: `{ "lang": "en" }`. |

### Response

Binary `application/pdf`. The `Content-Disposition` header carries a
`attachment; filename="<name>.pdf"` hint.

### Quick curl example

```bash
curl -X POST http://localhost:8000/api/md-to-pdf \\
  -F "file=@notes.md" \\
  --output notes.pdf
```
"""


_PDF_TO_MD_RESPONSE_EXAMPLE = {
    "md": "---\\ntitle: \"Whitepaper\"\\npages: 4\\n---\\n\\n# Introduction\\n\\nFirst paragraph...",
    "front_matter": {
        "title": "Whitepaper",
        "author": "Author Name",
        "date": "2026-04-12",
        "source": "whitepaper.pdf",
        "pages": 4,
    },
    "warnings": [],
    "stats": {"headings": 6, "tables": 1, "bullets": 14},
}


def _read_options(raw: str | None, model):
    if not raw:
        return model()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ApiError(
            422, "invalid_options", "options field is not valid JSON", detail=str(exc)
        ) from exc
    try:
        return model.model_validate(data)
    except ValidationError as exc:
        raise ApiError(
            422,
            "invalid_options",
            "options payload failed validation",
            detail=exc.errors(),
        ) from exc


async def _read_upload(upload: UploadFile, expected_suffix: str, expected_label: str) -> bytes:
    name = upload.filename or ""
    if not name.lower().endswith(expected_suffix):
        raise ApiError(
            400,
            "wrong_file_type",
            f"Expected a {expected_label} file (.{expected_suffix.lstrip('.')}) but got: {name or 'unnamed upload'}",
        )

    data = bytearray()
    while True:
        chunk = await upload.read(1024 * 1024)
        if not chunk:
            break
        data.extend(chunk)
        if len(data) > MAX_UPLOAD_BYTES:
            raise ApiError(
                413,
                "payload_too_large",
                f"Upload exceeds {MAX_UPLOAD_BYTES // (1024 * 1024)} MB limit.",
            )
    return bytes(data)


@router.post(
    "/api/pdf-to-md",
    response_model=PdfToMdResponse,
    summary="Convert a PDF to structured Markdown",
    description=PDF_TO_MD_DESCRIPTION,
    response_description="The extracted Markdown plus front matter, warnings and stats.",
    responses={
        200: {
            "description": "Successful conversion.",
            "content": {"application/json": {"example": _PDF_TO_MD_RESPONSE_EXAMPLE}},
        },
        400: {
            "description": "Upload is not a PDF.",
            "content": {
                "application/json": {
                    "example": {
                        "error": {
                            "code": "wrong_file_type",
                            "message": "Expected a PDF file (.pdf) but got: notes.txt",
                        }
                    }
                }
            },
        },
        413: {
            "description": "Upload exceeds the 500 MB cap.",
            "content": {
                "application/json": {
                    "example": {
                        "error": {
                            "code": "payload_too_large",
                            "message": "Upload exceeds 500 MB limit.",
                        }
                    }
                }
            },
        },
        422: {
            "description": "Malformed `options` payload.",
            "content": {
                "application/json": {
                    "example": {
                        "error": {
                            "code": "invalid_options",
                            "message": "options payload failed validation",
                            "detail": [{"loc": ["page_break"], "msg": "Input should be a valid boolean"}],
                        }
                    }
                }
            },
        },
    },
)
async def pdf_to_md(
    file: UploadFile = File(..., description="The PDF to convert."),
    options: str | None = Form(
        default=None,
        description='Optional JSON string. Example: `{"page_break": false, "with_images": false, "front_matter": true, "lang": "en"}`.',
    ),
    force: bool = Query(
        default=False,
        description=(
            "Convert even when the PDF has no extractable text layer. Without "
            "this, a scanned PDF returns 422 `ocr_required` instead of empty "
            "markdown. Use it to bypass a false positive (e.g. an image-only cover)."
        ),
    ),
) -> PdfToMdResponse:
    opts = _read_options(options, PdfToMdOptions)
    pdf_bytes = await _read_upload(file, ".pdf", "PDF")
    started = time.perf_counter()
    result = await asyncio.to_thread(
        convert_pdf_bytes,
        pdf_bytes,
        filename=file.filename or "document.pdf",
        options=opts,
        force=force,
    )
    elapsed_ms = int((time.perf_counter() - started) * 1000)
    log.info(
        "pdf-to-md filename=%s bytes=%d duration_ms=%d headings=%d tables=%d bullets=%d",
        file.filename,
        len(pdf_bytes),
        elapsed_ms,
        result.stats.headings,
        result.stats.tables,
        result.stats.bullets,
    )
    return result


@router.post(
    "/api/md-to-pdf",
    summary="Render a Markdown file into a PDF",
    description=MD_TO_PDF_DESCRIPTION,
    response_description="A binary PDF (application/pdf).",
    responses={
        200: {
            "description": "Rendered PDF.",
            "content": {"application/pdf": {"schema": {"type": "string", "format": "binary"}}},
        },
        400: {
            "description": "Wrong file type.",
            "content": {
                "application/json": {
                    "example": {
                        "error": {
                            "code": "wrong_file_type",
                            "message": "Expected a Markdown file (.md) but got: notes.txt",
                        }
                    }
                }
            },
        },
        413: {"description": "Upload exceeds the 500 MB cap."},
        422: {"description": "Malformed `options` payload."},
        500: {"description": "Renderer failed (Chromium crashed, missing template, etc)."},
    },
)
async def md_to_pdf(
    file: UploadFile = File(..., description="The Markdown file to render."),
    options: str | None = Form(
        default=None,
        description='Optional JSON string. Example: `{"lang": "en"}`.',
    ),
) -> Response:
    opts = _read_options(options, MdToPdfOptions)
    md_bytes = await _read_upload(file, ".md", "Markdown")
    started = time.perf_counter()
    pdf_bytes = await asyncio.to_thread(
        render_md_bytes, md_bytes, filename=file.filename or "document.md", options=opts
    )
    elapsed_ms = int((time.perf_counter() - started) * 1000)
    log.info(
        "md-to-pdf filename=%s bytes=%d duration_ms=%d",
        file.filename,
        len(md_bytes),
        elapsed_ms,
    )
    out_name = (file.filename or "document.md").rsplit(".", 1)[0] + ".pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{out_name}"'},
    )
