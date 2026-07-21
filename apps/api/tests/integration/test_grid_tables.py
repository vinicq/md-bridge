"""Real-PDF integration coverage for opt-in grid tables (#166)."""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import markdown
import pymupdf
import pytest
from app.schemas.convert import PdfToMdOptions
from app.services.packages_loader import md_to_pdf_module, pdf_to_md_module
from app.services.pdf_to_md import convert_pdf_bytes


def _grids_installed() -> bool:
    try:
        markdown.Markdown(extensions=["grids"])
    except Exception:
        return False
    return True


_GRIDS_AVAILABLE = _grids_installed()
WIN_TEMPDIR_LOCK = pytest.mark.skipif(
    sys.platform == "win32",
    reason="convert_pdf_bytes holds the source PDF while its tempdir exits on Windows.",
)


def _build_pdf() -> bytes:
    """A bordered 2x2 table whose second body cell holds two lines, plus a body
    paragraph so the page clears the sparse-text OCR gate (`convert_pdf_bytes`
    would otherwise OCR the scan on a host with Tesseract and lose the table)."""
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
    page.insert_text(
        (40, 220),
        "This paragraph gives the page a real text layer so the converter does "
        "not treat it as a scan that needs OCR before the table is read.",
        fontsize=11,
    )
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


def _build_pdf_with_dash_cell() -> bytes:
    """Same table but the multi-line cell carries an en-dash, so the smart-
    typography fold would lengthen the line if it ran after the grid was sized."""
    doc = pymupdf.open()
    page = doc.new_page(width=400, height=300)
    xs, ys = [40, 200, 360], [40, 110, 180]
    for x in xs:
        page.draw_line((x, ys[0]), (x, ys[-1]))
    for y in ys:
        page.draw_line((xs[0], y), (xs[-1], y))
    page.insert_text((48, 60), "Term", fontsize=11)
    page.insert_text((208, 60), "Definition", fontsize=11)
    page.insert_text((48, 130), "A", fontsize=11)
    page.insert_text((208, 130), "range 1–10", fontsize=11)  # en-dash
    page.insert_text((208, 150), "second line", fontsize=11)
    page.insert_text(
        (40, 220),
        "Body text so the page is not treated as a scan that needs OCR here.",
        fontsize=11,
    )
    try:
        return doc.tobytes()
    finally:
        doc.close()


def test_grid_survives_smart_typography_as_an_equal_length_table():
    # The typography fold must not run inside the grid after its borders are
    # sized: markdown-grids drops a table to plain text if any line length
    # differs, so a `-`/dash fold that lengthens a cell would destroy it (#166
    # review). The grid stays equal-length and still round-trips to a table.
    mod = pdf_to_md_module()
    with tempfile.TemporaryDirectory(prefix="grid-typo-", ignore_cleanup_errors=True) as raw:
        src, out = Path(raw) / "t.pdf", Path(raw) / "t.md"
        src.write_bytes(_build_pdf_with_dash_cell())
        mod.convert_document(
            src, out, front_matter=False,
            multiline_table_format="grid", smart_typography_dashes="ascii",
        )
        md = out.read_text(encoding="utf-8")
    grid_lines = [ln for ln in md.splitlines() if ln and ln[0] in "+|"]
    assert grid_lines, md
    assert len({len(ln) for ln in grid_lines}) == 1  # every line equal length
    if _GRIDS_AVAILABLE:
        md_mod = md_to_pdf_module()
        html = md_mod.markdown.markdown(md, extensions=md_mod.MD_EXTENSIONS, output_format="html5")
        assert "<table" in html


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
