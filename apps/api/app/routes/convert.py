"""PDF↔Markdown conversion routes."""
from __future__ import annotations

import json
import logging
import re
import time
from urllib.parse import quote

from fastapi import APIRouter, File, Form, Query, Request, UploadFile
from fastapi.encoders import jsonable_encoder
from fastapi.responses import Response
from pydantic import ValidationError

from app.concurrency import run_bounded
from app.errors import ApiError
from app.schemas.convert import (
    FormatInfo,
    MdToDocxOptions,
    MdToPdfOptions,
    PdfToMdOptions,
    PdfToMdResponse,
    ThemeInfo,
)
from app.services.formats import list_formats
from app.services.md_to_docx import render_md_to_docx_bytes
from app.services.md_to_pdf import render_md_bytes
from app.services.pdf_to_md import convert_pdf_bytes
from app.services.themes import get_theme, list_themes

DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

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
| `file` | yes | A `.pdf` file, up to the configured cap (default 500 MB). |
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
| `file` | yes | A `.md` file up to the configured cap (default 500 MB), UTF-8. |
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
        # A field_validator that raises ValueError leaves that exception object
        # in each error's `ctx` on Pydantic v2, and json.dumps cannot serialize
        # it: passing exc.errors() straight through made the error handler itself
        # 500 (#361). jsonable_encoder coerces the ctx to strings.
        raise ApiError(
            422,
            "invalid_options",
            "options payload failed validation",
            detail=jsonable_encoder(exc.errors()),
        ) from exc


async def _read_upload(
    upload: UploadFile, expected_suffix: str, expected_label: str, max_bytes: int
) -> bytes:
    name = upload.filename or ""
    if not name.lower().endswith(expected_suffix):
        raise ApiError(
            400,
            "wrong_file_type",
            f"Expected a {expected_label} file (.{expected_suffix.lstrip('.')}) but got: {name or 'unnamed upload'}",
        )

    # FastAPI has already parsed the body into an UploadFile (Starlette spools it
    # to a temp file past its own threshold), so read it once into the final
    # bytes instead of growing a bytearray and copying it into bytes (the old 2x
    # peak, #365) or mirroring it into a second temp file. Bounding the read at
    # cap+1 enforces the upload limit without pulling an over-cap upload fully
    # into memory: a file at or under the cap comes back whole, a larger one
    # yields cap+1 bytes and trips the 413.
    data = await upload.read(max_bytes + 1)
    if len(data) > max_bytes:
        raise ApiError(
            413,
            "payload_too_large",
            f"Upload exceeds {max_bytes // (1024 * 1024)} MB limit.",
        )
    return data


# Chars that would corrupt a Content-Disposition value if left in the filename:
# a double quote closes the quoted-string early, CR/LF split the header, and
# path separators let an upload name reach outside the intended stem (#362).
_UNSAFE_FILENAME = re.compile(r'[\r\n"\\/]')


def _download_headers(source_name: str | None, ext: str) -> dict[str, str]:
    """Build a well-formed Content-Disposition for a converted download.

    The source name is client-supplied, so sanitize the stem for the ASCII
    `filename=` and add an RFC 5987 `filename*` so non-ASCII names survive
    without breaking the header for older clients.
    """
    stem = (source_name or "document").rsplit(".", 1)[0]
    safe = _UNSAFE_FILENAME.sub("", stem).strip() or "document"
    name = f"{safe}{ext}"
    # Build the ASCII fallback from the stem, not the whole name: for an
    # all-non-ASCII stem (e.g. `レポート`) encoding the full name would leave
    # only the extension, so clients that ignore `filename*` would save a
    # hidden `.pdf`. Fall back to `document` when the ASCII stem is empty.
    ascii_stem = safe.encode("ascii", "ignore").decode().strip() or "document"
    ascii_name = f"{ascii_stem}{ext}"
    disposition = f"attachment; filename=\"{ascii_name}\"; filename*=UTF-8''{quote(name)}"
    return {"Content-Disposition": disposition}


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
            "description": "Upload exceeds the configured cap.",
            "content": {
                "application/json": {
                    "example": {
                        "error": {
                            "code": "payload_too_large",
                            "message": "Upload exceeds the configured limit.",
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
    request: Request,
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
    pdf_bytes = await _read_upload(
        file, ".pdf", "PDF", request.app.state.settings.max_upload_bytes
    )
    started = time.perf_counter()
    result = await run_bounded(request.app,
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
        413: {"description": "Upload exceeds the configured cap."},
        422: {"description": "Malformed `options` payload."},
        500: {"description": "Renderer failed (Chromium crashed, missing template, etc)."},
    },
)
async def md_to_pdf(
    request: Request,
    file: UploadFile = File(..., description="The Markdown file to render."),
    options: str | None = Form(
        default=None,
        description='Optional JSON string. Example: `{"lang": "en"}`.',
    ),
) -> Response:
    opts = _read_options(options, MdToPdfOptions)
    md_bytes = await _read_upload(
        file, ".md", "Markdown", request.app.state.settings.max_upload_bytes
    )
    started = time.perf_counter()
    pdf_bytes = await run_bounded(request.app,
        render_md_bytes, md_bytes, filename=file.filename or "document.md", options=opts
    )
    elapsed_ms = int((time.perf_counter() - started) * 1000)
    log.info(
        "md-to-pdf filename=%s bytes=%d duration_ms=%d",
        file.filename,
        len(md_bytes),
        elapsed_ms,
    )
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers=_download_headers(file.filename, ".pdf"),
    )


@router.get(
    "/api/themes",
    response_model=list[ThemeInfo],
    summary="List the Markdown → PDF themes",
    description=(
        "Returns every registered theme as `{slug, name, description, family}`. "
        "Pass a slug as `options.theme` on `POST /api/md-to-pdf` to select it."
    ),
)
async def get_themes() -> list[ThemeInfo]:
    return [ThemeInfo(**t.to_dict()) for t in list_themes()]


@router.get(
    "/api/themes/{slug}/css",
    summary="Get a theme's raw CSS",
    description="Returns the theme's own stylesheet as `text/css` for inline display.",
    responses={
        200: {"description": "The theme stylesheet.", "content": {"text/css": {}}},
        400: {
            "description": "Unknown theme slug.",
            "content": {
                "application/json": {
                    "example": {
                        "error": {
                            "code": "unknown_theme",
                            "message": "Theme 'whatever' is not registered.",
                        }
                    }
                }
            },
        },
    },
)
async def get_theme_css(slug: str) -> Response:
    theme = get_theme(slug)  # raises 400 unknown_theme for an unregistered slug
    css = theme.css_path.read_text(encoding="utf-8")
    return Response(content=css, media_type="text/css; charset=utf-8")


@router.post(
    "/api/md-to-docx",
    summary="Render a Markdown file into a Word document (.docx)",
    description=(
        "Converts Markdown to a deterministic .docx: headings, bold/italic/inline "
        "code, lists, block quotes, fenced code, and tables map onto Word "
        "elements. Same input, same bytes, every run."
    ),
    response_description="A binary DOCX (Office Open XML).",
    responses={
        200: {
            "description": "Rendered DOCX.",
            "content": {DOCX_MIME: {"schema": {"type": "string", "format": "binary"}}},
        },
        400: {"description": "Wrong file type or non-UTF-8 markdown."},
        413: {"description": "Upload exceeds the configured cap."},
        422: {"description": "Malformed `options` payload."},
        500: {"description": "Conversion failed."},
    },
)
async def md_to_docx(
    request: Request,
    file: UploadFile = File(..., description="The Markdown file to convert."),
    options: str | None = Form(
        default=None,
        description='Optional JSON string. Example: `{"lang": "en"}`.',
    ),
) -> Response:
    opts = _read_options(options, MdToDocxOptions)
    md_bytes = await _read_upload(
        file, ".md", "Markdown", request.app.state.settings.max_upload_bytes
    )
    started = time.perf_counter()
    docx_bytes = await run_bounded(request.app,
        render_md_to_docx_bytes, md_bytes, filename=file.filename or "document.md", options=opts
    )
    elapsed_ms = int((time.perf_counter() - started) * 1000)
    log.info(
        "md-to-docx filename=%s bytes=%d duration_ms=%d",
        file.filename,
        len(md_bytes),
        elapsed_ms,
    )
    return Response(
        content=docx_bytes,
        media_type=DOCX_MIME,
        headers=_download_headers(file.filename, ".docx"),
    )


@router.get(
    "/api/formats",
    response_model=list[FormatInfo],
    summary="List the conversion format pairs",
    description=(
        "Returns every format pair md-bridge knows about, shipped or planned, "
        "as `{slug, label, source, target, input_mime, output_mime, status, "
        "endpoint}`. Shipped pairs carry an `endpoint`; planned pairs have "
        "`endpoint: null` and a `status` of `roadmap` or `wanted`."
    ),
)
async def get_formats() -> list[FormatInfo]:
    return [FormatInfo(**f.to_dict()) for f in list_formats()]
