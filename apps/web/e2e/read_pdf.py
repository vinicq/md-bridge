"""Read the first page of a PDF back with PyMuPDF for the page-setup honesty gate.

Prints a JSON line with the real page geometry (points) and the extracted text,
so the E2E spec can assert the panel's choices actually changed the rendered PDF
instead of trusting the request round-trip. Run with the API venv's Python so
`fitz` resolves (the same interpreter that boots the API in playwright.config.ts).
"""
import json
import sys

import fitz  # PyMuPDF

doc = fitz.open(sys.argv[1])
page = doc[0]
rect = page.rect
print(
    json.dumps(
        {
            "pages": doc.page_count,
            "width": round(rect.width, 1),
            "height": round(rect.height, 1),
            "text": page.get_text(),
        }
    )
)
