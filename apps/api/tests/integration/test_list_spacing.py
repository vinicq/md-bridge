"""Real-PDF integration coverage for opt-in tight and loose lists (#168)."""
from __future__ import annotations

import tempfile
from pathlib import Path

import pymupdf
from app.services.packages_loader import pdf_to_md_module


def _build_pdf() -> bytes:
    doc = pymupdf.open()
    page = doc.new_page(width=612, height=500)
    for y, text in ((100, "1. Tight one"), (124, "2. Tight two"), (148, "3. Tight three"), (190, "Between lists."), (240, "1. Loose one"), (292, "2. Loose two"), (344, "3. Loose three")):
        page.insert_text((72, y), text, fontsize=12)
    try:
        return doc.tobytes()
    finally:
        doc.close()


def _convert(pdf_bytes: bytes, *, enabled: bool | None = None) -> str:
    mod = pdf_to_md_module()
    with tempfile.TemporaryDirectory(prefix="list-spacing-", ignore_cleanup_errors=True) as raw:
        source, output = Path(raw) / "lists.pdf", Path(raw) / "lists.md"
        source.write_bytes(pdf_bytes)
        kwargs = {"tight_loose_lists": enabled} if enabled is not None else {}
        mod.convert_document(source, output, front_matter=False, **kwargs)
        return output.read_text(encoding="utf-8")


def test_real_pdf_preserves_tight_and_loose_lists_when_enabled():
    pdf = _build_pdf()
    omitted = _convert(pdf)
    disabled = _convert(pdf, enabled=False)
    enabled = _convert(pdf, enabled=True)

    assert omitted == disabled
    assert "1. Tight one\n1. Tight two\n1. Tight three" in enabled
    assert "1. Loose one\n\n1. Loose two\n\n1. Loose three" in enabled
