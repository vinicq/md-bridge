"""Integration coverage for #133: MuPDF native stderr stays clean and its
non-fatal warnings reach the Python logger instead.

Runs the real PyMuPDF runtime through the live endpoints (no subprocess/binary
mock, per the project's integration rule). `capfd` captures at the file
descriptor level because MuPDF writes straight to fd 2; `capsys` would miss it.
The warning text is never asserted (it drifts across PyMuPDF releases); the
contract is: fd 2 carries no `MuPDF error` line, and a WARNING record reports a
positive `warning_count`.
"""
from __future__ import annotations

import logging
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


def _warning_records(caplog: pytest.LogCaptureFixture) -> list[logging.LogRecord]:
    return [
        r
        for r in caplog.records
        if r.levelno == logging.WARNING and "mupdf-warnings" in r.getMessage()
    ]


# The pdf-to-md endpoint is not exercised with the malformed fixture here. The
# vendored converter holds the PyMuPDF handle open while repairing a page flagged
# "may not be correct", which locks the file in the per-request TemporaryDirectory
# on Windows (POSIX unlinks open files, so CI would pass, but the suite must be
# green on the maintainer's machine too). The convert path silences stderr through
# the same process-global `mupdf_display_errors(False)` and drains the buffer with
# the same `capture_mupdf_warnings` helper, covered by the unit tests and by the
# inspect endpoint below.


def test_inspect_pdf_silences_native_stderr_and_logs_warning(
    client: TestClient,
    malformed_pdf: Path,
    capfd: pytest.CaptureFixture[str],
    caplog: pytest.LogCaptureFixture,
) -> None:
    with caplog.at_level(logging.WARNING):
        resp = client.post(
            "/api/inspect-pdf",
            files={"file": (malformed_pdf.name, malformed_pdf.read_bytes(), "application/pdf")},
        )
    assert resp.status_code == 200, resp.text

    captured = capfd.readouterr()
    assert "MuPDF error" not in captured.err

    records = _warning_records(caplog)
    assert len(records) >= 1
    assert all(r.warning_count > 0 for r in records)


def test_clean_pdf_emits_no_mupdf_warning(
    client: TestClient,
    istqb_pdf: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    with caplog.at_level(logging.WARNING):
        resp = client.post(
            "/api/inspect-pdf",
            files={"file": (istqb_pdf.name, istqb_pdf.read_bytes(), "application/pdf")},
        )
    assert resp.status_code == 200, resp.text
    assert _warning_records(caplog) == []
