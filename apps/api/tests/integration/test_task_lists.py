"""End-to-end propagation of the task-list option through the real converter (#172).

Uses ASCII bracket items (`[ ]` / `[x]`) so text extraction is font-independent
and reliable; the glyph mapping itself is covered exhaustively in the unit test.
Converts via `convert_document` directly into a tempdir, mirroring the corpus
regression tests, so it runs on POSIX and Windows alike.
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import pymupdf
import pytest
from app.services.packages_loader import pdf_to_md_module

# convert_document keeps the PyMuPDF handle open, so the tempdir cannot be
# removed on Windows. CI (Linux) exercises this; the mapping itself is covered
# cross-platform by the unit test.
WIN_TEMPDIR_LOCK = pytest.mark.skipif(
    sys.platform == "win32",
    reason="convert_document holds the PDF handle open; tempdir cleanup fails on Windows",
)


def _pdf_with_pages(lines: list[str]) -> bytes:
    """One short line per page, so the converter never merges them into a
    single paragraph."""
    doc = pymupdf.open()
    try:
        for text in lines:
            page = doc.new_page(width=612, height=200)
            page.insert_text((72, 96), text, fontsize=14)
        return doc.tobytes()
    finally:
        doc.close()


def _convert(pdf_bytes: bytes, **kwargs) -> str:
    mod = pdf_to_md_module()
    with tempfile.TemporaryDirectory(prefix="tasklist-") as raw:
        pdf = Path(raw) / "in.pdf"
        out = Path(raw) / "out.md"
        pdf.write_bytes(pdf_bytes)
        mod.convert_document(pdf, out, front_matter=False, **kwargs)
        return out.read_text(encoding="utf-8")


@WIN_TEMPDIR_LOCK
def test_bracket_items_stay_literal_by_default():
    md = _convert(_pdf_with_pages(["[ ] Buy milk", "[x] Ship it"]))
    # The converter escapes literal brackets; off by default it must not become
    # task-list syntax.
    assert "Buy milk" in md
    assert "- [ ]" not in md


@WIN_TEMPDIR_LOCK
def test_bracket_items_become_task_list_when_enabled():
    md = _convert(
        _pdf_with_pages(["[ ] Buy milk", "[x] Ship it"]),
        detect_task_lists=True,
    )
    assert "- [ ] Buy milk" in md
    assert "- [x] Ship it" in md
