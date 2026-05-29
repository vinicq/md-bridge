"""Unit coverage for the MuPDF warning-capture helper (#133).

Drives the real PyMuPDF runtime against committed fixtures rather than mocking
it: the helper's whole job is to drain MuPDF's process-global buffer, so a mock
would assert nothing real. The warning *text* is never asserted (it can drift
across PyMuPDF patch releases); only the contract is: a non-empty buffer yields
one WARNING with a positive count, an empty buffer yields nothing.
"""
from __future__ import annotations

import logging
from pathlib import Path

import fitz
import pytest
from app.services.mupdf_log import capture_mupdf_warnings

log = logging.getLogger("test.mupdf_log")


def test_logs_warning_with_count_for_malformed_pdf(
    malformed_pdf: Path, caplog: pytest.LogCaptureFixture
) -> None:
    with caplog.at_level(logging.WARNING, logger="test.mupdf_log"):
        with capture_mupdf_warnings(log, filename="bad.pdf"), fitz.open(malformed_pdf) as doc:
            for page in doc:
                page.get_text("dict")

    records = [r for r in caplog.records if r.levelno == logging.WARNING]
    assert len(records) == 1
    record = records[0]
    assert "bad.pdf" in record.getMessage()
    assert record.warning_count > 0
    # The raw buffer is attached for operators but its text stays unasserted.
    assert record.mupdf_warnings


def test_no_warning_for_clean_pdf(
    istqb_pdf: Path, caplog: pytest.LogCaptureFixture
) -> None:
    with caplog.at_level(logging.WARNING, logger="test.mupdf_log"):
        with capture_mupdf_warnings(log, filename="clean.pdf"), fitz.open(istqb_pdf) as doc:
            for page in doc:
                page.get_text("dict")

    assert [r for r in caplog.records if r.levelno == logging.WARNING] == []


def test_buffer_resets_between_calls(
    malformed_pdf: Path, istqb_pdf: Path, caplog: pytest.LogCaptureFixture
) -> None:
    # A malformed run followed by a clean run must not leak warnings into the
    # clean call: the helper resets the global buffer on entry.
    with capture_mupdf_warnings(log, filename="bad.pdf"), fitz.open(malformed_pdf) as doc:
        for page in doc:
            page.get_text("dict")

    # Drop the malformed run's record so the assertion below only sees what the
    # clean run produced.
    caplog.clear()
    with caplog.at_level(logging.WARNING, logger="test.mupdf_log"):
        with capture_mupdf_warnings(log, filename="clean.pdf"), fitz.open(istqb_pdf) as doc:
            for page in doc:
                page.get_text("dict")

    assert [r for r in caplog.records if r.levelno == logging.WARNING] == []
