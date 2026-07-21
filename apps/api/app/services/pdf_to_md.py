"""Wrapper around the vendored pdf-to-markdown converter.

Deterministic, heuristic conversion. Reads a PDF from bytes, writes and reads
via tempfiles so the existing file-based `convert_document` function keeps
working without modification. Cleans up tempfiles in `finally`.
"""
from __future__ import annotations

import logging
import re
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from app.errors import ApiError
from app.schemas.convert import (
    ConvertStats,
    FrontMatter,
    PdfToMdOptions,
    PdfToMdResponse,
)
from app.services.inspect import inspect_pdf_bytes
from app.services.mupdf_log import capture_mupdf_warnings
from app.services.ocr import get_lang as ocr_lang
from app.services.ocr import get_max_pages as ocr_max_pages
from app.services.ocr import is_enabled as ocr_enabled
from app.services.ocr import ocr_pdf_bytes
from app.services.packages_loader import pdf_to_md_module

log = logging.getLogger(__name__)

# Linked from the 422 ocr_required payload so the UI can point the user at the
# OCR setup instructions instead of handing back near-empty markdown.
OCR_DOCS_URL = "https://vinicq.github.io/md-bridge/getting-started/#limits-worth-knowing-about"

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
    """Emit warning *codes*, not human strings.

    The frontend translates each code via `dictionaries.ts` so the warning
    text follows the active UI locale. Codes stay stable across locales
    and across releases; adding a new code means adding three dictionary
    entries (en, pt, es).
    """
    warnings: list[str] = []
    # The converter no longer wraps small-font text in <small> (#141), so there
    # is nothing to strip first; small-font captions/footnotes are real content
    # and now count toward the char total. The hard 422 ocr_required gate lives
    # in inspect.py and reads raw PDF chars, independent of this informational
    # warning, so dropping the strip does not move the OCR boundary.
    #
    # Drop image markdown before counting: an inline base64 data URI (#372) adds
    # thousands of non-whitespace characters that are not extractable text, and
    # would otherwise mask a sparse-text scan and suppress the needs_ocr warning.
    text_only = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", md_body)
    plain_chars = len(re.sub(r"\s+", "", text_only))
    if plain_chars < max(80, pages * 40):
        warnings.append("needs_ocr")
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
    force: bool = False,
) -> PdfToMdResponse:
    opts = options or PdfToMdOptions()
    mod = pdf_to_md_module()

    # Always inspect first: a pure scan (no text layer) cannot be converted by
    # the heuristic pipeline and would return near-empty markdown with a 200,
    # which reads as "the tool is broken". When OCR is available we apply it;
    # when it is not, we block with a 422 so the user gets an actionable error
    # instead of an empty file. `force=True` is the explicit escape hatch for
    # the false positive (e.g. an image-only cover that the user wants anyway).
    ocr_applied = False
    diagnostics = inspect_pdf_bytes(pdf_bytes, filename)
    if diagnostics.needs_ocr:
        # OCR rasterizes every page at 300 DPI, so a scan past the configured
        # page budget is a memory/time risk on a shared or hosted deployment.
        # The cap gates the OCR pre-pass, not conversion itself: over the cap we
        # take the same not-OCR path as a lean install, so `force=True` still
        # yields a raw conversion instead of a hard 413. Default budget 0 =
        # unlimited, so self-hosted conversion stays byte-identical. (#208)
        cap = ocr_max_pages()
        over_cap = ocr_enabled() and bool(cap) and diagnostics.pages > cap
        if ocr_enabled() and not over_cap:
            # A partial OCR install (binary present but the language traineddata
            # missing) raises pytesseract's TesseractError; surface it as a typed
            # error instead of a code-less 500. The shipped runtime-ocr image is
            # complete, so this guards hand-rolled installs.
            try:
                pdf_bytes = ocr_pdf_bytes(pdf_bytes, lang=ocr_lang())
            except ApiError:
                # ocr_pdf_bytes already raised a typed error (e.g. the per-page
                # timeout naming the page, #364); let it through unwrapped.
                raise
            except Exception as exc:
                raise ApiError(
                    500,
                    "ocr_failed",
                    "OCR pre-pass failed. Check that the Tesseract binary and "
                    "the language data for the document are installed.",
                    detail=str(exc),
                ) from exc
            ocr_applied = True
        elif not force:
            if over_cap:
                raise ApiError(
                    413,
                    "ocr_too_many_pages",
                    f"This scan has {diagnostics.pages} pages, over the OCR cap "
                    f"of {cap}. Raise or unset MD_BRIDGE_OCR_MAX_PAGES, or retry "
                    "with force to convert it without OCR.",
                    detail={"pages": diagnostics.pages, "max_pages": cap},
                )
            raise ApiError(
                422,
                "ocr_required",
                "This PDF has no extractable text layer (it looks scanned). "
                "Enable OCR to convert it, or retry with force to convert anyway.",
                detail={"docs": OCR_DOCS_URL},
            )
        # force=True with OCR unavailable or the scan over the cap falls through
        # to a raw conversion: near-empty markdown is the caller's explicit choice.
    with _tempdir() as tmp:
        safe_stem = Path(filename).stem or "document"
        pdf_path = tmp / f"{safe_stem}.pdf"
        md_path = tmp / f"{safe_stem}.md"
        pdf_path.write_bytes(pdf_bytes)

        # `extract_images=False` stays forced: writing image files to a
        # neighbour directory is a side effect we never want on the server. When
        # the caller asks for images, we inline them as base64 data URIs instead
        # (#372), which keeps the .md self-contained and touches no disk outside
        # the tempdir. The MuPDF C runtime logs non-fatal resource warnings while
        # parsing malformed PDFs; capture them onto the logger, not bare stderr.
        with capture_mupdf_warnings(log, filename=filename):
            mod.convert_document(
                pdf_path,
                md_path,
                page_break=opts.page_break,
                debug=False,
                extract_images=False,
                inline_images=opts.with_images,
                front_matter=opts.front_matter,
                detect_blockquotes=opts.detect_blockquotes,
                cluster_headings=opts.cluster_headings,
                subtract_running_furniture=opts.subtract_running_furniture,
                allow_html=frozenset(opts.allow_html),
                preserve_line_breaks=opts.preserve_line_breaks,
                max_heading_level=opts.max_heading_level,
                footnote_pairing=opts.footnote_pairing,
                autolink_urls=opts.autolink_urls,
                autolink_emails=opts.autolink_emails,
                reference_link_threshold=opts.reference_link_threshold,
                emit_heading_anchors=opts.emit_heading_anchors,
                pair_quote_attribution=opts.pair_quote_attribution,
                extract_abbreviations=opts.extract_abbreviations,
                smart_typography_quotes=opts.smart_typography_quotes,
                smart_typography_ellipsis=opts.smart_typography_ellipsis,
                smart_typography_dashes=opts.smart_typography_dashes,
                caption_alt_text=opts.caption_alt_text,
                detect_task_lists=opts.detect_task_lists,
                task_list_extended=opts.task_list_extended,
                extract_highlights=opts.extract_highlights,
                emit_figure_anchors=opts.emit_figure_anchors,
                image_width_hints=opts.image_width_hints,
                table_column_align=opts.table_column_align,
                tight_loose_lists=opts.tight_loose_lists,
                list_loose_threshold=opts.list_loose_threshold,
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
        ocr_applied=ocr_applied,
    )
