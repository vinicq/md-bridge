"""Golden-file regression for the pdf-to-markdown skill.

For every PDF in `Arquivos-pdf/Design Digital/`, run the heuristic converter
and diff line-by-line against the stored snapshot. Drift above 2% of total
golden lines fails the test. Run `pytest tests/ --update-golden` to refresh
all snapshots after a deliberate change.
"""
from __future__ import annotations

import difflib
import tempfile
from pathlib import Path

import pytest


TOLERANCE = 0.02  # 2% line drift


def _convert_pdf(pdf_to_md_mod, pdf_path: Path) -> str:
    with tempfile.TemporaryDirectory(prefix="regress-pdf2md-") as raw:
        out = Path(raw) / f"{pdf_path.stem}.md"
        pdf_to_md_mod.convert_document(
            pdf_path,
            out,
            page_break=False,
            debug=False,
            extract_images=False,
            front_matter=True,
        )
        return out.read_text(encoding="utf-8")


def _drift_ratio(golden: str, current: str) -> float:
    g_lines = golden.splitlines()
    c_lines = current.splitlines()
    if not g_lines:
        return 1.0 if c_lines else 0.0
    sm = difflib.SequenceMatcher(a=g_lines, b=c_lines, autojunk=False)
    changed = 0
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            continue
        changed += max(i2 - i1, j2 - j1)
    return changed / len(g_lines)


@pytest.mark.parametrize(
    "pdf_name",
    [
        "ddp-factsheet-en.pdf",
        "ddp-glossay-en-v1.2.1.pdf",
        "ddp_foundationlevel_syllabus_en_v2.0.2.pdf",
        "digital-design-manifesto_pt.pdf",
        "sustainability_survey_en.pdf",
    ],
)
def test_pdf_regression(
    pdf_name: str,
    fixtures_dir: Path,
    golden_dir: Path,
    pdf_to_md_mod,
    update_golden: bool,
):
    pdf = fixtures_dir / pdf_name
    if not pdf.exists():
        pytest.skip(f"fixture not available: {pdf}")
    golden = golden_dir / f"{pdf.stem}.md"
    current = _convert_pdf(pdf_to_md_mod, pdf)

    if update_golden or not golden.exists():
        golden.write_text(current, encoding="utf-8")
        if not golden.exists():
            pytest.skip(f"created baseline at {golden}")
        return

    expected = golden.read_text(encoding="utf-8")
    drift = _drift_ratio(expected, current)
    if drift > TOLERANCE:
        diff = "\n".join(
            difflib.unified_diff(
                expected.splitlines(),
                current.splitlines(),
                fromfile=str(golden),
                tofile=f"{pdf.name} (current)",
                lineterm="",
                n=2,
            )
        )
        pytest.fail(
            f"pdf-to-md drift {drift:.2%} > {TOLERANCE:.0%} for {pdf.name}\n"
            f"Run `pytest tests/ --update-golden` if the change is intentional.\n\n"
            f"{diff[:4000]}"
        )
