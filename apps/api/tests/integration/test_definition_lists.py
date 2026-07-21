"""Real-PDF integration coverage for opt-in definition lists (#161)."""
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

_BODY = (
    "This introductory paragraph gives the page a real text layer so the "
    "converter does not treat it as a scan that needs OCR before the glossary."
)


def _glossary_pdf() -> bytes:
    """A body paragraph plus a term/definition glossary (terms at the margin,
    definitions indented 24pt, all at body size and font)."""
    doc = pymupdf.open()
    page = doc.new_page(width=420, height=440)
    page.insert_text((72, 60), _BODY[:70], fontsize=11)
    page.insert_text((72, 74), _BODY[70:], fontsize=11)
    rows = [
        ("HTML", 72, 120),
        ("HyperText Markup Language", 96, 134),
        ("CSS", 72, 160),
        ("Cascading Style Sheets", 96, 174),
        ("API", 72, 200),
        ("Application Programming Interface", 96, 214),
    ]
    for text, x, y in rows:
        page.insert_text((x, y), text, fontsize=11)
    try:
        return doc.tobytes()
    finally:
        doc.close()


def _heading_para_pdf() -> bytes:
    """A heading followed by an indented paragraph: must NOT become a `<dl>`."""
    doc = pymupdf.open()
    page = doc.new_page(width=420, height=440)
    page.insert_text((72, 60), _BODY[:70], fontsize=11)
    page.insert_text((72, 74), _BODY[70:], fontsize=11)
    page.insert_text((72, 120), "Introduction", fontsize=20)
    page.insert_text((96, 142), "The opening section describes the goals of the work here.", fontsize=11)
    page.insert_text((72, 180), "Overview", fontsize=20)
    page.insert_text((96, 202), "The second section summarizes the approach in a paragraph.", fontsize=11)
    try:
        return doc.tobytes()
    finally:
        doc.close()


def _convert(pdf_bytes: bytes, *, enabled: bool | None = None) -> str:
    mod = pdf_to_md_module()
    with tempfile.TemporaryDirectory(prefix="deflist-", ignore_cleanup_errors=True) as raw:
        src, out = Path(raw) / "t.pdf", Path(raw) / "t.md"
        src.write_bytes(pdf_bytes)
        kwargs = {"detect_definition_lists": enabled} if enabled is not None else {}
        mod.convert_document(src, out, front_matter=False, **kwargs)
        return out.read_text(encoding="utf-8")


def _html(md: str) -> str:
    md_mod = md_to_pdf_module()
    return md_mod.markdown.markdown(md, extensions=md_mod.MD_EXTENSIONS, output_format="html5")


def test_glossary_emits_a_definition_list_when_enabled():
    md = _convert(_glossary_pdf(), enabled=True)
    assert "HTML\n: HyperText Markup Language" in md
    assert "CSS\n: Cascading Style Sheets" in md


def test_default_and_explicit_off_keep_plain_paragraphs_byte_identical():
    pdf = _glossary_pdf()
    omitted = _convert(pdf)
    disabled = _convert(pdf, enabled=False)
    assert omitted == disabled
    assert ": HyperText" not in disabled  # no definition marker


def test_heading_and_paragraph_never_become_a_definition_list():
    md = _convert(_heading_para_pdf(), enabled=True)
    assert ": " not in md
    assert "# Introduction" in md
    assert "<dl>" not in _html(md)


def test_enabled_glossary_round_trips_to_dl_dt_dd():
    md = _convert(_glossary_pdf(), enabled=True)
    html = _html(md)
    assert "<dl>" in html
    assert html.count("<dt>") == 3
    assert html.count("<dd>") == 3


@WIN_TEMPDIR_LOCK
def test_api_option_forwards_to_the_converter():
    # The flag must reach the production read path (convert_pdf_bytes), not only
    # the CLI/convert_document signature (#161, Pattern 15).
    response = convert_pdf_bytes(
        _glossary_pdf(),
        filename="glossary.pdf",
        options=PdfToMdOptions(front_matter=False, detect_definition_lists=True),
    )
    assert "HTML\n: HyperText Markup Language" in response.md
