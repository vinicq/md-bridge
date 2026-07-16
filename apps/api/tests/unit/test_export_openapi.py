"""Unit tests for the OpenAPI export helper (#32).

The web client's types are generated from this schema, so the export must run
without a server and expose the response models the client consumes. The
byte-stability that the CI drift check relies on is asserted here too.
"""
from __future__ import annotations

import io
import json
from contextlib import redirect_stdout

from app.export_openapi import main


def _run_export() -> str:
    buffer = io.StringIO()
    with redirect_stdout(buffer):
        main()
    return buffer.getvalue()


def test_export_emits_the_documented_schemas_and_paths():
    schema = json.loads(_run_export())

    assert schema["openapi"].startswith("3.")
    assert "/api/pdf-to-md" in schema["paths"]
    assert "/api/inspect-pdf" in schema["paths"]

    components = schema["components"]["schemas"]
    for model in ("PdfToMdResponse", "InspectPdfResponse", "ThemeInfo", "FormatInfo"):
        assert model in components


def test_export_is_byte_stable():
    # The drift check regenerates and diffs, so two runs must be identical.
    assert _run_export() == _run_export()
