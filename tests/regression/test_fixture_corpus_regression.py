"""Regression over the broadened PDF fixture corpus (#28).

Each fixture spans a distinct PDF generation path (pdfTeX vs Chromium-rendered)
and content shape (tables, deep heading trees, CJK), documented in
`apps/api/tests/fixtures/SOURCES.md`. Two guards per fixture:

- a structural assertion (non-empty markdown with at least one heading, bullet,
  or table) that catches a class-wide flattening regardless of platform;
- a golden snapshot with the same 2% drift tolerance as the ISTQB test, so a
  per-document heuristic change surfaces without failing on incidental churn.

Goldens are generated with `pytest tests/ --update-golden`. Conversion runs
through `convert_document` directly (not the API tempdir path), so it behaves
identically on POSIX and Windows.
"""
from __future__ import annotations

import difflib
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
FIXTURES_DIR = ROOT / "apps" / "api" / "tests" / "fixtures"
TOLERANCE = 0.02

FIXTURE_CORPUS = [
    "wikipedia-markdown-en",
    "wikipedia-pdf-en",
    "wikipedia-markdown-ja",
    "arxiv-2207.09238-formal-algorithms-transformers",
]


def _convert(pdf_to_md_mod, pdf: Path) -> str:
    with tempfile.TemporaryDirectory(prefix="regress-corpus-") as raw:
        out = Path(raw) / f"{pdf.stem}.md"
        pdf_to_md_mod.convert_document(
            pdf, out, page_break=False, debug=False, extract_images=False, front_matter=True
        )
        return out.read_text(encoding="utf-8")


def _drift(golden: str, current: str) -> float:
    g = golden.splitlines()
    c = current.splitlines()
    if not g:
        return 1.0 if c else 0.0
    sm = difflib.SequenceMatcher(a=g, b=c, autojunk=False)
    changed = sum(
        max(i2 - i1, j2 - j1) for tag, i1, i2, j1, j2 in sm.get_opcodes() if tag != "equal"
    )
    return changed / len(g)


@pytest.fixture(params=FIXTURE_CORPUS)
def corpus_pdf(request) -> Path:
    p = FIXTURES_DIR / f"{request.param}.pdf"
    assert p.exists(), f"missing corpus fixture: {p}"
    return p


def test_corpus_fixture_has_structure(corpus_pdf: Path, pdf_to_md_mod):
    md = _convert(pdf_to_md_mod, corpus_pdf)
    body = md.split("\n---\n", 1)[-1] if md.startswith("---\n") else md
    assert body.strip(), f"{corpus_pdf.name}: markdown should not be empty"
    headings = sum(1 for ln in body.splitlines() if ln.lstrip().startswith("#"))
    bullets = sum(1 for ln in body.splitlines() if ln.lstrip()[:2] in ("- ", "* ", "+ "))
    tables = sum(1 for ln in body.splitlines() if ln.strip().startswith("|"))
    assert headings + bullets + tables > 0, (
        f"{corpus_pdf.name}: expected some structure (H={headings} B={bullets} T={tables})"
    )


def test_corpus_fixture_regression(corpus_pdf: Path, golden_dir: Path, pdf_to_md_mod, update_golden: bool):
    golden = golden_dir / f"{corpus_pdf.stem}.md"
    current = _convert(pdf_to_md_mod, corpus_pdf)

    if update_golden or not golden.exists():
        golden.write_text(current, encoding="utf-8")
        if not golden.exists():
            pytest.skip(f"created baseline at {golden}")
        return

    expected = golden.read_text(encoding="utf-8")
    drift = _drift(expected, current)
    if drift > TOLERANCE:
        pytest.fail(
            f"corpus drift {drift:.2%} > {TOLERANCE:.0%} on {corpus_pdf.name}. "
            f"Run `pytest tests/ --update-golden` if intentional."
        )
