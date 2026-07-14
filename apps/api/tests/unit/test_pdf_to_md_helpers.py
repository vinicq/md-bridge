"""Pure-function tests of pdf_to_md helpers (no skill, no fitz)."""
from __future__ import annotations

from app.schemas.convert import PdfToMdOptions
from app.services.pdf_to_md import (
    _build_warnings,
    _compute_stats,
    _parse_front_matter,
)


def test_parse_front_matter_returns_empty_when_no_marker():
    fm, body = _parse_front_matter("# Title\n\nbody")
    assert fm.title is None and fm.source is None
    assert body.startswith("# Title")


def test_parse_front_matter_reads_known_fields():
    md = (
        "---\n"
        'title: "Paper"\n'
        'author: "Alice"\n'
        'source: "paper.pdf"\n'
        "pages: 4\n"
        "---\n"
        "# Body\n"
    )
    fm, body = _parse_front_matter(md)
    assert fm.title == "Paper"
    assert fm.author == "Alice"
    assert fm.source == "paper.pdf"
    assert fm.pages == 4
    assert body.startswith("# Body")


def test_parse_front_matter_ignores_unknown_keys():
    md = '---\ntitle: "x"\nrogue: "y"\n---\nbody'
    fm, _ = _parse_front_matter(md)
    assert fm.title == "x"


def test_parse_front_matter_tolerates_bad_pages():
    md = '---\ntitle: "x"\npages: "not a number"\n---\nbody'
    fm, _ = _parse_front_matter(md)
    assert fm.pages is None


def test_compute_stats_counts_structure():
    md = (
        "# H1\n## H2\n\n"
        "- one\n- two\n- three\n\n"
        "| a | b |\n| --- | --- |\n| 1 | 2 |\n"
    )
    stats = _compute_stats(md)
    assert stats.headings == 2
    assert stats.bullets == 3
    assert stats.tables == 1


def test_compute_stats_empty_input():
    stats = _compute_stats("")
    assert stats.headings == 0 and stats.bullets == 0 and stats.tables == 0


def test_build_warnings_emits_needs_ocr_code_on_sparse_text():
    """Sparse text → `needs_ocr` code (not the English message).

    Regression for #40: the warning used to be a hardcoded English
    string, so the UI rendered English to PT and ES users. The
    backend now emits a stable code; the frontend dictionary owns
    the localised text.
    """
    warnings = _build_warnings(md_body="too short", options=PdfToMdOptions(), pages=10)
    assert warnings == ["needs_ocr"]


def test_build_warnings_silent_on_normal_text():
    body = "Lorem ipsum " * 100
    warnings = _build_warnings(md_body=body, options=PdfToMdOptions(), pages=2)
    assert warnings == []


def test_build_warnings_no_images_not_persisted_with_images():
    """with_images no longer warns: images are now inlined as data URIs (#372),
    so nothing is dropped and the old `images_not_persisted` code is gone."""
    body = "Lorem ipsum " * 100
    opts = PdfToMdOptions(with_images=True)
    warnings = _build_warnings(md_body=body, options=opts, pages=2)
    assert "images_not_persisted" not in warnings
