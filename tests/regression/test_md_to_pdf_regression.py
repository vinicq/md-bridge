"""Smoke regression for the markdown-to-pdf skill.

PDF binaries are not stable byte-for-byte across runs (timestamps, fonts,
metadata), so the regression here is structural: each fixture markdown renders
to a non-empty PDF that starts with the `%PDF-` magic and is at least 1 KB.
Visual changes are caught by the per-PDF golden files of pdf-to-md round-trip
elsewhere in the suite.
"""
from __future__ import annotations

import tempfile
from pathlib import Path

import pytest


SAMPLE_MD = """---
title: "Regression Sample"
---

# Heading One

A paragraph with **bold** and *italic* text.

## Subheading

- item one
- item two

| col a | col b |
| --- | --- |
| 1 | 2 |
| 3 | 4 |
"""


@pytest.fixture(scope="module")
def chromium_ready():
    from playwright.sync_api import sync_playwright

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            browser.close()
    except Exception as exc:
        pytest.skip(f"Playwright chromium unavailable: {exc}")


def test_md_to_pdf_renders_minimal(md_to_pdf_mod, chromium_ready):
    from app.config import MD_TO_PDF_TEMPLATES

    css = MD_TO_PDF_TEMPLATES / "default.css"
    assert css.exists(), f"default.css missing at {css}"

    with tempfile.TemporaryDirectory(prefix="regress-md2pdf-") as raw:
        md_path = Path(raw) / "doc.md"
        pdf_path = Path(raw) / "doc.pdf"
        md_path.write_text(SAMPLE_MD, encoding="utf-8")
        md_to_pdf_mod.convert(md_path, pdf_path, [css], lang="pt-BR")
        data = pdf_path.read_bytes()

    assert data.startswith(b"%PDF-"), "output is not a PDF"
    assert len(data) > 1024, f"PDF too small to be plausible: {len(data)} bytes"
