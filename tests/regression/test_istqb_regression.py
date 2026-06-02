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


def test_istqb_output_is_pure_markdown(istqb_pdf, pdf_to_md_mod):
    # #141: the converter must not emit raw <small>/<sup> tags. The drift test
    # above tolerates 2% churn; this asserts the tag count is exactly zero on a
    # real, caption- and footnote-heavy document, so a reintroduced wrapper
    # fails loudly rather than hiding under the drift threshold.
    current = _convert(pdf_to_md_mod, istqb_pdf)
    assert "<small>" not in current
    assert "<sup>" not in current
    # The former-<small> page footers must stay standalone, not be fused into
    # the preceding paragraph by the wrapped-paragraph merge (#141 review).
    lines = current.splitlines()
    footer_lines = [ln for ln in lines if "Page 3 of 77" in ln]
    assert footer_lines, "expected the page-3 footer to survive in the output"
    assert all(ln.strip() == "v4.0 GA Page 3 of 77 2025/05/02" for ln in footer_lines), (
        f"page footer was fused into prose: {footer_lines}"
    )


def test_istqb_running_furniture_subtracted_when_flag_on(istqb_pdf, pdf_to_md_mod):
    # #187: the opt-in flag removes the recurring page footer. The default path
    # (test above) keeps it, so this proves the flag rather than a golden change.
    with tempfile.TemporaryDirectory(prefix="regress-furniture-") as raw:
        out = Path(raw) / f"{istqb_pdf.stem}.md"
        pdf_to_md_mod.convert_document(
            istqb_pdf,
            out,
            page_break=False,
            debug=False,
            extract_images=False,
            front_matter=True,
            subtract_running_furniture=True,
        )
        current = out.read_text(encoding="utf-8")

    assert "v4.0 GA Page 3 of 77 2025/05/02" not in current
    # The body survives the subtraction: the document still has its structure.
    assert current.count("\n#") > 20
