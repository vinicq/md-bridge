"""End-to-end coverage with an ISTQB syllabus PDF, the project's canonical
real-world document. Verifies that the routes correctly handle a multi-page,
structurally rich syllabus the way the project's target users would submit it.
"""
from __future__ import annotations

import re
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
    assert len(body["fonts"]) >= 1, "syllabus must declare at least one font"
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


def test_istqb_ordered_lists_stay_contiguous(client, istqb_pdf: Path):
    # Regression for #144: numbered items used to be emitted one paragraph apart,
    # so CommonMark read each as its own single-item list. They must now sit on
    # consecutive lines with no blank line between them.
    with istqb_pdf.open("rb") as fh:
        resp = client.post(
            "/api/pdf-to-md",
            files={"file": (istqb_pdf.name, fh, "application/pdf")},
        )
    assert resp.status_code == 200, resp.text
    md = resp.json()["md"]

    collapsed = re.findall(r"(?m)^\s*\d+\..*\n\n\s*\d+\.\s", md)
    assert not collapsed, f"ordered-list items separated by a blank line: {collapsed}"

    # A genuine contiguous list is a run of 2+ numbered lines with no blank line
    # between them; unrelated paragraphs that happen to start with "N." are
    # separated by a blank line and so never form a run.
    marker = re.compile(r"^\s*\d+\.\s")
    longest_run = run = 0
    for line in md.splitlines():
        run = run + 1 if marker.match(line) else 0
        longest_run = max(longest_run, run)
    assert longest_run >= 2, "expected at least one contiguous ordered list (2+ consecutive items)"
