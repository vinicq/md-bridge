"""Integration coverage for a code block nested under a list item (#197).

Builds a real PDF with PyMuPDF (no mock): a numbered item, a monospace code
block indented past the marker, then a second item. The three land as separate
blocks. Without the continuation handling the code escapes to top level and
splits the list. The test re-parses the emitted Markdown with the shipped
`markdown` library and asserts the code renders as a <pre><code> inside the
first <li>, with the list intact. The assembly logic is covered cross-platform
by tests/unit/test_list_continuation.py.
"""
from __future__ import annotations

import sys

import markdown
import pymupdf
import pytest
from app.services.pdf_to_md import convert_pdf_bytes

MD_EXTENSIONS = ["extra", "sane_lists", "smarty", "toc", "md_in_html"]


def _pdf_with_code_in_item() -> bytes:
    doc = pymupdf.open()
    page = doc.new_page(width=612, height=792)
    page.insert_text((72, 120), "1. Run the snippet:", fontsize=11)
    # Courier marks the block as code; the indent past the marker makes it a
    # continuation of the first item.
    page.insert_text((110, 160), 'print("hello")', fontsize=11, fontname="cour")
    page.insert_text((110, 176), 'print("world")', fontsize=11, fontname="cour")
    page.insert_text((72, 220), "2. Read the output.", fontsize=11)
    try:
        return doc.tobytes()
    finally:
        doc.close()


@pytest.mark.skipif(
    sys.platform == "win32",
    reason=(
        "The vendored converter holds the PyMuPDF handle open, which locks the "
        "per-request tempdir on Windows during cleanup. POSIX unlinks open files, "
        "so CI exercises this; the assembly logic is covered cross-platform by "
        "tests/unit/test_list_continuation.py."
    ),
)
def test_code_block_nests_inside_list_item():
    pdf = _pdf_with_code_in_item()
    md = convert_pdf_bytes(pdf, filename="code-in-item.pdf").md
    html = markdown.markdown(md, extensions=MD_EXTENSIONS)

    assert html.count("<ol>") == 1
    assert html.count("<li>") == 2
    first_item = html.split("</li>")[0]
    assert "<pre><code>" in first_item
    assert 'print("hello")' in first_item
    # The second item is its own <li>, not swallowed into the first.
    assert "Read the output" not in first_item
