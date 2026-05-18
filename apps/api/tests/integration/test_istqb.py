"""End-to-end coverage with an ISTQB syllabus PDF — the project's canonical
real-world document. Verifies that the routes correctly handle a multi-page,
structurally rich syllabus the way the project's target users would submit it.
"""
from __future__ import annotations

from pathlib import Path


def test_istqb_pdf_inspects(client, istqb_pdf: Path):
    with istqb_pdf.open("rb") as fh:
        resp = client.post(
            "/api/inspect-pdf",
            files={"file": (istqb_pdf.name, fh, "application/pdf")},
        )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["pages"] >= 10, "ISTQB syllabi are long; expected at least 10 pages"
    assert body["body_size_pt"] > 0
    assert body["fonts"], "syllabus must declare at least one font"
    assert body["needs_ocr"] is False, "ISTQB syllabi are born digital, not scanned"


def test_istqb_pdf_to_md_extracts_structure(client, istqb_pdf: Path):
    with istqb_pdf.open("rb") as fh:
        resp = client.post(
            "/api/pdf-to-md",
            files={"file": (istqb_pdf.name, fh, "application/pdf")},
        )
    assert resp.status_code == 200, resp.text
    body = resp.json()

    assert body["md"].strip(), "non-empty markdown"
    assert body["md"].startswith("---"), "front matter expected by default"

    # ISTQB syllabi all have a contents page and chapter headings.
    stats = body["stats"]
    assert stats["headings"] >= 5, f"expected several headings, got {stats['headings']}"

    fm = body["front_matter"]
    assert fm["source"] == istqb_pdf.name
    assert fm["pages"] and fm["pages"] >= 10
