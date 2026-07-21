"""Real-PDF integration coverage for opt-in nested ordered lists (#194)."""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import pymupdf
import pytest
from app.schemas.convert import PdfToMdOptions
from app.services.packages_loader import md_to_pdf_module, pdf_to_md_module
from app.services.pdf_to_md import convert_pdf_bytes

WIN_TEMPDIR_LOCK = pytest.mark.skipif(
    sys.platform == "win32",
    reason="convert_pdf_bytes holds the source PDF while its tempdir exits on Windows.",
)

# Level-0 items sit at x=72, the sublist at x=90 (one 18pt indent step), so the
# profile reads the sublist as nesting level 1. The sublist starts at "3." to
# exercise start preservation, not just the indent.
_ROWS = (
    (100, 72, "1. First point"),
    (124, 72, "2. Second point"),
    (148, 90, "3. Sub point three"),
    (172, 90, "4. Sub point four"),
    (196, 72, "3. Third point"),
)


def _build_pdf() -> bytes:
    doc = pymupdf.open()
    page = doc.new_page(width=612, height=500)
    for y, x, text in _ROWS:
        page.insert_text((x, y), text, fontsize=12)
    try:
        return doc.tobytes()
    finally:
        doc.close()


def _convert(pdf_bytes: bytes, *, enabled: bool | None = None) -> str:
    mod = pdf_to_md_module()
    with tempfile.TemporaryDirectory(prefix="nested-ol-", ignore_cleanup_errors=True) as raw:
        source, output = Path(raw) / "lists.pdf", Path(raw) / "lists.md"
        source.write_bytes(pdf_bytes)
        kwargs = {"nested_ordered_lists": enabled} if enabled is not None else {}
        mod.convert_document(source, output, front_matter=False, **kwargs)
        return output.read_text(encoding="utf-8")


def test_default_and_explicit_off_keep_flat_numbering_byte_identical():
    pdf = _build_pdf()
    omitted = _convert(pdf)
    disabled = _convert(pdf, enabled=False)
    assert omitted == disabled
    # Legacy: the sublist flattens to `1.` at a 2-space indent.
    assert "1. Second point\n  1. Sub point three\n  1. Sub point four\n1. Third point" in disabled


def test_enabled_preserves_sublist_start_and_indents_to_nest():
    enabled = _convert(_build_pdf(), enabled=True)
    assert (
        "1. Second point\n    3. Sub point three\n    1. Sub point four\n1. Third point"
        in enabled
    )


def test_enabled_output_round_trips_to_a_nested_ol():
    enabled = _convert(_build_pdf(), enabled=True)
    md_mod = md_to_pdf_module()
    html = md_mod.markdown.markdown(
        enabled, extensions=md_mod.MD_EXTENSIONS, output_format="html5"
    )
    assert html.count("<ol") == 2  # outer list + nested sublist
    assert 'start="3"' in html


@WIN_TEMPDIR_LOCK
def test_api_option_forwards_to_the_converter():
    # The flag must reach the production read path (convert_pdf_bytes), not only
    # the CLI/convert_document signature (#194, Pattern 15).
    response = convert_pdf_bytes(
        _build_pdf(),
        filename="nested-ol.pdf",
        options=PdfToMdOptions(front_matter=False, nested_ordered_lists=True),
    )
    assert "    3. Sub point three" in response.md
