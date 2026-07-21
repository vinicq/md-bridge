"""Real-PDF integration coverage for opt-in grid tables (#166)."""
from __future__ import annotations

import importlib.util
import sys
import tempfile
from pathlib import Path

import pymupdf
import pytest
from app.schemas.convert import PdfToMdOptions
from app.services.packages_loader import md_to_pdf_module, pdf_to_md_module
from app.services.pdf_to_md import convert_pdf_bytes

_GRIDS_AVAILABLE = importlib.util.find_spec("markdown_grids") is not None
WIN_TEMPDIR_LOCK = pytest.mark.skipif(
    sys.platform == "win32",
    reason="convert_pdf_bytes holds the source PDF while its tempdir exits on Windows.",
)


def _build_pdf() -> bytes:
    """A bordered 2x2 table whose second body cell holds two lines."""
    doc = pymupdf.open()
    page = doc.new_page(width=400, height=300)
    xs, ys = [40, 160, 340], [40, 110, 180]
    for x in xs:
        page.draw_line((x, ys[0]), (x, ys[-1]))
    for y in ys:
        page.draw_line((xs[0], y), (xs[-1], y))
    page.insert_text((48, 60), "Term", fontsize=11)
    page.insert_text((168, 60), "Definition", fontsize=11)
    page.insert_text((48, 130), "A", fontsize=11)
    page.insert_text((168, 130), "line one", fontsize=11)
    page.insert_text((168, 150), "line two", fontsize=11)
    try:
        return doc.tobytes()
    finally:
        doc.close()


def _convert(pdf_bytes: bytes, *, fmt: str | None = None) -> str:
    mod = pdf_to_md_module()
    with tempfile.TemporaryDirectory(prefix="grid-", ignore_cleanup_errors=True) as raw:
        src, out = Path(raw) / "t.pdf", Path(raw) / "t.md"
        src.write_bytes(pdf_bytes)
        kwargs = {"multiline_table_format": fmt} if fmt is not None else {}
        mod.convert_document(src, out, front_matter=False, **kwargs)
        return out.read_text(encoding="utf-8")


def test_default_and_pipe_flatten_the_multiline_cell_identically():
    pdf = _build_pdf()
    default_md = _convert(pdf)
    pipe_md = _convert(pdf, fmt="pipe")
    assert default_md == pipe_md
    assert "line one line two" in default_md  # collapsed onto one pipe row
    assert "+---" not in default_md


def test_grid_format_preserves_the_multiline_cell():
    grid_md = _convert(_build_pdf(), fmt="grid")
    assert "+======" in grid_md or "+====" in grid_md
    assert "| line one" in grid_md
    assert "| line two" in grid_md


@pytest.mark.skipif(not _GRIDS_AVAILABLE, reason="grid-tables extra (markdown-grids) not installed")
def test_grid_output_round_trips_through_the_renderer():
    grid_md = _convert(_build_pdf(), fmt="grid")
    md_mod = md_to_pdf_module()
    html = md_mod.markdown.markdown(
        grid_md, extensions=md_mod.MD_EXTENSIONS, output_format="html5"
    )
    assert "<table" in html
    assert "line one" in html and "line two" in html


@WIN_TEMPDIR_LOCK
def test_api_option_forwards_to_the_converter():
    # The flag must reach the production read path (convert_pdf_bytes), not only
    # the CLI/convert_document signature (#166, Pattern 15).
    response = convert_pdf_bytes(
        _build_pdf(),
        filename="grid.pdf",
        options=PdfToMdOptions(front_matter=False, multiline_table_format="grid"),
    )
    assert "| line two" in response.md
