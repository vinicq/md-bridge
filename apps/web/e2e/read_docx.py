"""Read a .docx back as a zip for the md-to-docx honesty gate (#276).

A .docx is an Office Open XML package: a ZIP container holding
`word/document.xml`. This prints a JSON line with the real zip facts and the
extracted body text, so the E2E spec can assert the downloaded artifact is a
genuine, non-empty Word document with the converted content, instead of trusting
the request round-trip. Uses only the stdlib (zipfile + re); no python-docx and
no native dependency, so it runs on the same interpreter as read_pdf.py.
"""
import json
import re
import sys
import zipfile

path = sys.argv[1]

# Zip magic up front: a valid .docx always starts with the local-file-header
# signature "PK\x03\x04". A truthful gate proves the bytes, not the MIME header.
with open(path, "rb") as fh:
    magic = fh.read(4)

with zipfile.ZipFile(path) as zf:
    names = zf.namelist()
    xml = zf.read("word/document.xml").decode("utf-8")

# Strip tags to recover the visible text. Word splits runs across <w:t> nodes,
# so collapse whitespace after dropping markup.
text = re.sub(r"<[^>]+>", "", xml)
text = re.sub(r"\s+", " ", text).strip()

print(
    json.dumps(
        {
            "zip_magic": magic.hex(),
            "has_document_xml": "word/document.xml" in names,
            "entry_count": len(names),
            "text": text,
        }
    )
)
