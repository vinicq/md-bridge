"""One-shot generator for the malformed-PDF fixture used by #133 tests.

Builds a minimal PDF whose page content stream invokes an XObject (`/Fm0 Do`)
that is absent from the page's /XObject resource dict. PyMuPDF parses the page
fine but its C runtime emits a non-fatal warning
("cannot find XObject resource 'Fm0'"), which is exactly the noise #133 fixes.

Run once with the API venv to (re)produce the binary fixture; not committed as
part of the test run, only the resulting .pdf is.
"""
from __future__ import annotations

from pathlib import Path

import pymupdf

OUT = Path(__file__).with_name("malformed-missing-xobject.pdf")


def build() -> bytes:
    objects: list[bytes] = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        (
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 200 200] "
            b"/Resources << /XObject << >> >> /Contents 4 0 R >>"
        ),
    ]
    # The page is otherwise valid (it strokes a rectangle) but invokes XObject
    # /Fm0, which the empty /XObject dict above does not define. Keeping the page
    # valid means MuPDF warns about the missing resource without flagging the
    # whole page as broken, so it does not hold the file open for repair (which
    # would lock the tempfile on Windows during conversion cleanup).
    stream = b"q 1 0 0 RG 10 10 100 100 re S /Fm0 Do Q\n"
    objects.append(b"<< /Length %d >>\nstream\n%s\nendstream" % (len(stream), stream))

    header = b"%PDF-1.4\n"
    body = bytearray(header)
    offsets: list[int] = []
    for i, obj in enumerate(objects, start=1):
        offsets.append(len(body))
        body += b"%d 0 obj\n%s\nendobj\n" % (i, obj)

    xref_pos = len(body)
    n = len(objects) + 1
    body += b"xref\n0 %d\n" % n
    body += b"0000000000 65535 f \n"
    for off in offsets:
        body += b"%010d 00000 n \n" % off
    body += b"trailer\n<< /Size %d /Root 1 0 R >>\n" % n
    body += b"startxref\n%d\n%%%%EOF\n" % xref_pos
    return bytes(body)


def main() -> None:
    data = build()
    OUT.write_bytes(data)

    # Verify the fixture opens and triggers a captured MuPDF warning.
    pymupdf.TOOLS.reset_mupdf_warnings()
    with pymupdf.open(OUT) as doc:
        for page in doc:
            page.get_text("dict")
    buf = pymupdf.TOOLS.mupdf_warnings(reset=True)
    print(f"wrote {OUT.name} ({len(data)} bytes)")
    print(f"warning buffer non-empty: {bool(buf)}")
    print(buf or "<empty>")


if __name__ == "__main__":
    main()
