"""Integration coverage for opt-in GFM table column alignment (#175)."""
from __future__ import annotations

import tempfile
from pathlib import Path

import pymupdf
from app.services.packages_loader import pdf_to_md_module


def _build_pdf() -> bytes:
    doc = pymupdf.open()
    page = doc.new_page(width=420, height=300)
    x0, y0, column_width, row_height = 50, 80, 100, 35
    for row in range(4):
        y = y0 + row * row_height
        page.draw_line((x0, y), (x0 + 3 * column_width, y))
    for column in range(4):
        x = x0 + column * column_width
        page.draw_line((x, y0), (x, y0 + 3 * row_height))

    page.insert_text((58, 103), "Name", fontsize=10)
    page.insert_text((x0 + 150 - pymupdf.get_text_length("Status", fontsize=10) / 2, 103), "Status", fontsize=10)
    page.insert_text((x0 + 300 - pymupdf.get_text_length("Amount", fontsize=10) - 8, 103), "Amount", fontsize=10)
    page.insert_text((58, 138), "Alpha", fontsize=10)
    page.insert_text((x0 + 150 - pymupdf.get_text_length("Open", fontsize=10) / 2, 138), "Open", fontsize=10)
    page.insert_text((x0 + 300 - pymupdf.get_text_length("123.45", fontsize=10) - 8, 138), "123.45", fontsize=10)
    page.insert_text((58, 173), "Beta", fontsize=10)
    page.insert_text((x0 + 150 - pymupdf.get_text_length("Closed", fontsize=10) / 2, 173), "Closed", fontsize=10)
    page.insert_text((x0 + 300 - pymupdf.get_text_length("67.89", fontsize=10) - 8, 173), "67.89", fontsize=10)
    try:
        return doc.tobytes()
    finally:
        doc.close()


def _convert(pdf_bytes: bytes, *, table_column_align: bool | None = None) -> str:
    mod = pdf_to_md_module()
    with tempfile.TemporaryDirectory(prefix="table-align-", ignore_cleanup_errors=True) as raw:
        source = Path(raw) / "table.pdf"
        output = Path(raw) / "table.md"
        source.write_bytes(pdf_bytes)
        kwargs = {"table_column_align": table_column_align} if table_column_align is not None else {}
        mod.convert_document(source, output, front_matter=False, **kwargs)
        return output.read_text(encoding="utf-8")


def test_opt_in_detects_left_center_and_right_alignment():
    markdown = _convert(_build_pdf(), table_column_align=True)
    assert "| :--- | :---: | ---: |" in markdown


def test_default_keeps_plain_table_separators():
    pdf = _build_pdf()
    omitted_markdown = _convert(pdf)
    default_markdown = _convert(pdf, table_column_align=False)
    aligned_markdown = _convert(pdf, table_column_align=True)
    plain_separator = "| --- | --- | --- |"
    aligned_separator = "| :--- | :---: | ---: |"

    assert plain_separator in default_markdown
    assert ":---" not in default_markdown
    assert "---:" not in default_markdown
    assert omitted_markdown == default_markdown
    # The opt-in changes only the table separator. With the default off, the
    # converter keeps the same body text, order, and spacing as its baseline.
    assert default_markdown.replace(plain_separator, aligned_separator) == aligned_markdown
    assert default_markdown == """| Name | Status | Amount |
| --- | --- | --- |
| Alpha | Open | 123.45 |
| Beta | Closed | 67.89 |"""
