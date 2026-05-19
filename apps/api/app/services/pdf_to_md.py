"""Wrapper around the vendored pdf-to-markdown converter.

Deterministic, heuristic conversion. Reads a PDF from bytes, writes and reads
via tempfiles so the existing file-based `convert_document` function keeps
working without modification. Cleans up tempfiles in `finally`.
"""
from __future__ import annotations

import re
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from app.schemas.convert import (
    ConvertStats,
    FrontMatter,
    PdfToMdOptions,
    PdfToMdResponse,
)
from app.services.packages_loader import pdf_to_md_module

FRONT_MATTER_LINE = re.compile(r'^(\w[\w-]*):\s*(.*)$')
HEADING_RE = re.compile(r"^(#{1,6})\s+\S", re.MULTILINE)
TABLE_ROW_RE = re.compile(r"^\|.*\|\s*$", re.MULTILINE)
BULLET_RE = re.compile(r"^\s*[-*+]\s+\S", re.MULTILINE)


def _parse_front_matter(md: str) -> tuple[FrontMatter, str]:
    if not md.startswith("---\n"):
        return FrontMatter(), md
    end = md.find("\n---\n", 4)
    if end == -1:
        return FrontMatter(), md
    block = md[4:end]
    body = md[end + 5:]
    fields: dict[str, str | int] = {}
    for raw in block.splitlines():
        m = FRONT_MATTER_LINE.match(raw)
        if not m:
            continue
        key = m.group(1)
        val = m.group(2).strip().strip('"').strip("'")
        if key == "pages":
            try:
                fields[key] = int(val)
            except ValueError:
                continue
        else:
            fields[key] = val
    keep = {k: v for k, v in fields.items() if k in FrontMatter.model_fields}
    return FrontMatter(**keep), body


def _compute_stats(md_body: str) -> ConvertStats:
    headings = len(HEADING_RE.findall(md_body))
    table_lines = TABLE_ROW_RE.findall(md_body)
    # A table opens with header + separator + body rows; count the separators
    # (`| --- | --- |`) which appear once per table.
    table_count = sum(
        1
        for line in table_lines
        if re.fullmatch(r"\|\s*(:?-{2,}:?\s*\|\s*)+", line.strip())
    )
    bullets = len(BULLET_RE.findall(md_body))
    return ConvertStats(headings=headings, tables=table_count, bullets=bullets)


def _build_warnings(md_body: str, options: PdfToMdOptions, pages: int) -> list[str]:
    warnings: list[str] = []
    plain = re.sub(r"<small>.*?</small>", " ", md_body, flags=re.DOTALL)
    plain_chars = len(re.sub(r"\s+", "", plain))
    if plain_chars < max(80, pages * 40):
        warnings.append(
            "Very little text was extracted. The PDF may be scanned; "
            "run OCR (e.g. Tesseract) before converting."
        )
    if options.with_images:
        warnings.append(
            "Image extraction is enabled but images are not persisted by the API; "
            "the markdown references images that are not served back."
        )
    return warnings


@contextmanager
def _tempdir() -> Iterator[Path]:
    with tempfile.TemporaryDirectory(prefix="md-bridge-pdf2md-") as raw:
        yield Path(raw)


def convert_pdf_bytes(
    pdf_bytes: bytes,
    *,
    filename: str,
    options: PdfToMdOptions | None = None,
) -> PdfToMdResponse:
    opts = options or PdfToMdOptions()
    mod = pdf_to_md_module()

    with _tempdir() as tmp:
        safe_stem = Path(filename).stem or "document"
        pdf_path = tmp / f"{safe_stem}.pdf"
        md_path = tmp / f"{safe_stem}.md"
        pdf_path.write_bytes(pdf_bytes)

        # `extract_images=False` is forced. With_images=True would write to a
        # neighbour directory; we never want side effects outside the tempdir.
        mod.convert_document(
            pdf_path,
            md_path,
            page_break=opts.page_break,
            debug=False,
            extract_images=False,
            front_matter=opts.front_matter,
        )

        md_text = md_path.read_text(encoding="utf-8")

    if opts.front_matter:
        front, body = _parse_front_matter(md_text)
    else:
        front, body = FrontMatter(), md_text

    pages = front.pages or 1
    stats = _compute_stats(body)
    warnings = _build_warnings(body, opts, pages)

    return PdfToMdResponse(
        md=md_text,
        front_matter=front,
        warnings=warnings,
        stats=stats,
    )
