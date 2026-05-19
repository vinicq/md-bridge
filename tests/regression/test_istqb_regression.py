"""Regression for the ISTQB canonical fixture.

ISTQB syllabi are the target real-world documents for this project. This test
locks the heuristic converter's output against a stored snapshot so future
edits to the conversion layer surface drift on the most representative input.
"""
from __future__ import annotations

import difflib
import tempfile
from pathlib import Path

import pytest

TOLERANCE = 0.02


def _convert(pdf_to_md_mod, pdf: Path) -> str:
    with tempfile.TemporaryDirectory(prefix="regress-istqb-") as raw:
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


def test_istqb_regression(
    istqb_pdf: Path, golden_dir: Path, pdf_to_md_mod, update_golden: bool
):
    golden = golden_dir / f"{istqb_pdf.stem}.md"
    current = _convert(pdf_to_md_mod, istqb_pdf)

    if update_golden or not golden.exists():
        golden.write_text(current, encoding="utf-8")
        if not golden.exists():
            pytest.skip(f"created baseline at {golden}")
        return

    expected = golden.read_text(encoding="utf-8")
    drift = _drift(expected, current)
    if drift > TOLERANCE:
        pytest.fail(
            f"ISTQB drift {drift:.2%} > {TOLERANCE:.0%} on {istqb_pdf.name}. "
            f"Run `pytest tests/ --update-golden` if intentional."
        )
