from __future__ import annotations

import json
import shutil
import sys
import tempfile
from pathlib import Path

import pytest


def test_pdf_to_md_returns_markdown(client, istqb_pdf: Path):
    with istqb_pdf.open("rb") as fh:
        resp = client.post(
            "/api/pdf-to-md",
            files={"file": (istqb_pdf.name, fh, "application/pdf")},
        )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert "md" in body
    assert body["md"].strip(), "markdown should not be empty"
    assert body["front_matter"]["source"] == istqb_pdf.name
    assert isinstance(body["warnings"], list)
    stats = body["stats"]
    assert stats["headings"] + stats["bullets"] + stats["tables"] > 0, "expected some structure"


# Real-world fixture corpus (#28). Each spans a distinct PDF generation path;
# provenance and licences are documented in apps/api/tests/fixtures/SOURCES.md.
FIXTURE_CORPUS = [
    "wikipedia-markdown-en",
    "wikipedia-pdf-en",
    "wikipedia-markdown-ja",
    "arxiv-2207.09238-formal-algorithms-transformers",
]


@pytest.mark.parametrize("stem", FIXTURE_CORPUS)
def test_pdf_to_md_corpus_has_structure(client, stem: str):
    # No silent skips: every committed fixture must convert to non-empty
    # markdown that carries at least one structural element. A heuristic change
    # that flattens a whole class of inputs fails here, not in production.
    pdf = Path(__file__).resolve().parents[1] / "fixtures" / f"{stem}.pdf"
    assert pdf.exists(), f"missing corpus fixture: {pdf}"
    with pdf.open("rb") as fh:
        resp = client.post(
            "/api/pdf-to-md",
            files={"file": (pdf.name, fh, "application/pdf")},
        )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["md"].strip(), f"{stem}: markdown should not be empty"
    stats = body["stats"]
    assert stats["headings"] + stats["bullets"] + stats["tables"] > 0, (
        f"{stem}: expected some structure, got {stats}"
    )


def test_pdf_to_md_rejects_non_pdf(client):
    resp = client.post(
        "/api/pdf-to-md",
        files={"file": ("notes.txt", b"hello", "text/plain")},
    )
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "wrong_file_type"


def test_pdf_to_md_rejects_invalid_options(client, istqb_pdf: Path):
    with istqb_pdf.open("rb") as fh:
        resp = client.post(
            "/api/pdf-to-md",
            files={"file": (istqb_pdf.name, fh, "application/pdf")},
            data={"options": json.dumps({"page_break": "yes please"})},
        )
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "invalid_options"


def test_pdf_to_md_rejects_oversize(client):
    # Real payload above the 500 MB cap so the route returns 413 the same way
    # it would in production. No patching of internal constants. The test is
    # slow on purpose: short of patching the constant, this is the only way
    # to drive the actual limit check inside `_read_upload`.
    from app.config import MAX_UPLOAD_BYTES

    payload = b"%PDF-1.4\n" + b"0" * (MAX_UPLOAD_BYTES + 1)
    resp = client.post(
        "/api/pdf-to-md",
        files={"file": ("big.pdf", payload, "application/pdf")},
    )
    assert resp.status_code == 413
    assert resp.json()["error"]["code"] == "payload_too_large"


def test_pdf_to_md_cleans_up_tempdirs(client, istqb_pdf: Path):
    tmp_root = Path(tempfile.gettempdir())
    before = {p.name for p in tmp_root.glob("md-bridge-pdf2md-*")}
    with istqb_pdf.open("rb") as fh:
        resp = client.post(
            "/api/pdf-to-md",
            files={"file": (istqb_pdf.name, fh, "application/pdf")},
        )
    assert resp.status_code == 200
    after = {p.name for p in tmp_root.glob("md-bridge-pdf2md-*")}
    leaked = after - before
    assert not leaked, f"pdf-to-md leaked tempdirs: {leaked}"

def test_pdf_to_md_scanned_pdf_returns_422_when_ocr_disabled(
    client,
    scanned_pdf_bytes: bytes,
    monkeypatch,
):
    # A pure scan with OCR off used to return 200 with near-empty markdown and a
    # discreet warning (#139). It now blocks with 422 ocr_required so the user
    # gets an actionable error instead of an empty file. The 422 fires right
    # after inspection, before any conversion, so no tempdir is created.
    # Force OCR off explicitly: the default is now auto-on when the Tesseract
    # stack is installed (which it is on CI), so we pin the off path here.
    monkeypatch.setenv("MD_BRIDGE_OCR_ENABLED", "0")

    resp = client.post(
        "/api/pdf-to-md",
        files={"file": ("scanned.pdf", scanned_pdf_bytes, "application/pdf")},
    )

    assert resp.status_code == 422, resp.text
    body = resp.json()
    assert body["error"]["code"] == "ocr_required"
    assert body["error"]["detail"]["docs"]


@pytest.mark.skipif(
    sys.platform == "win32",
    reason=(
        "force converts the scanned PDF, and the vendored converter holds the "
        "PyMuPDF handle open while repairing the text-less page, which locks the "
        "per-request tempdir on Windows. POSIX unlinks open files, so CI runs it."
    ),
)
def test_pdf_to_md_force_bypasses_ocr_gate(
    client,
    scanned_pdf_bytes: bytes,
    monkeypatch,
):
    # Pin OCR off so force exercises the gate-bypass path, not the auto-on OCR
    # path (the default now auto-enables when the stack is installed).
    monkeypatch.setenv("MD_BRIDGE_OCR_ENABLED", "0")

    resp = client.post(
        "/api/pdf-to-md?force=true",
        files={"file": ("scanned.pdf", scanned_pdf_bytes, "application/pdf")},
    )

    # With force, the gate is bypassed and the (near-empty) conversion succeeds.
    assert resp.status_code == 200, resp.text
    assert resp.json()["ocr_applied"] is False


def test_pdf_to_md_applies_ocr_when_enabled(client, scanned_pdf_bytes: bytes, monkeypatch):
    pytest.importorskip("pytesseract")
    if shutil.which("tesseract") is None:
        pytest.skip("tesseract binary is not installed")

    monkeypatch.setenv("MD_BRIDGE_OCR_ENABLED", "1")
    monkeypatch.setenv("MD_BRIDGE_OCR_LANG", "eng")

    resp = client.post(
        "/api/pdf-to-md",
        files={"file": ("scanned.pdf", scanned_pdf_bytes, "application/pdf")},
    )

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["ocr_applied"] is True
    assert body["md"].strip()
    assert "OCR" in body["md"].upper()


def test_pdf_to_md_ocr_runs_by_default_when_stack_installed(
    client, scanned_pdf_bytes: bytes, monkeypatch
):
    # The headline of the auto-default change: with no MD_BRIDGE_OCR_ENABLED set,
    # a scanned PDF is OCR'd automatically because the stack is installed. Hits
    # the real probe and the real Tesseract binary (no mock), so it exercises
    # the new default end to end rather than a patched flag.
    pytest.importorskip("pytesseract")
    if shutil.which("tesseract") is None:
        pytest.skip("tesseract binary is not installed")

    monkeypatch.delenv("MD_BRIDGE_OCR_ENABLED", raising=False)
    monkeypatch.delenv("MD_BRIDGE_OCR_LANG", raising=False)

    resp = client.post(
        "/api/pdf-to-md",
        files={"file": ("scanned.pdf", scanned_pdf_bytes, "application/pdf")},
    )

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["ocr_applied"] is True
    assert "OCR" in body["md"].upper()


def test_pdf_to_md_skips_ocr_for_textual_pdf_when_enabled(
    client,
    istqb_pdf: Path,
    monkeypatch,
):
    monkeypatch.setenv("MD_BRIDGE_OCR_ENABLED", "1")
    monkeypatch.setenv("MD_BRIDGE_OCR_LANG", "eng")

    with istqb_pdf.open("rb") as fh:
        resp = client.post(
            "/api/pdf-to-md",
            files={"file": (istqb_pdf.name, fh, "application/pdf")},
        )

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["ocr_applied"] is False
    assert body["md"].strip()
