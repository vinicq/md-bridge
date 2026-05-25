"""Regression for code-block detection in pdf-to-md.

The fixture `apps/api/tests/fixtures/code-sample.pdf` carries a Python snippet
in Courier between two prose paragraphs in Helvetica. The committed golden
snapshot at `tests/golden/code-sample.md` locks the converter's exact output,
so any drift surfaces as a byte-level failure with pytest's automatic diff.

Single equality assertion: no conditional assertion paths, no parsing of the
output, no mocks. The `if update_golden` branch is the CLI-flag baseline-regen
path; in CI that flag is never set so the assertion path always runs.
"""
from __future__ import annotations

import tempfile
from pathlib import Path

import pytest


@pytest.fixture(scope="module")
def code_sample_pdf() -> Path:
    root = Path(__file__).resolve().parents[1]
    path = root.parent / "apps" / "api" / "tests" / "fixtures" / "code-sample.pdf"
    assert path.exists(), f"committed fixture missing: {path}"
    return path


def _convert(pdf_to_md_mod, pdf: Path) -> str:
    with tempfile.TemporaryDirectory(prefix="regress-codeblock-") as raw:
        out = Path(raw) / f"{pdf.stem}.md"
        pdf_to_md_mod.convert_document(
            pdf, out, page_break=False, debug=False, extract_images=False, front_matter=False
        )
        return out.read_text(encoding="utf-8")


def test_code_sample_matches_golden(
    pdf_to_md_mod, code_sample_pdf: Path, golden_dir: Path, update_golden: bool
):
    golden = golden_dir / "code-sample.md"
    current = _convert(pdf_to_md_mod, code_sample_pdf)

    if update_golden:
        golden.write_text(current, encoding="utf-8", newline="\n")
        return

    assert golden.exists(), (
        f"committed golden missing: {golden}. "
        f"Run `pytest tests/regression --update-golden` to seed."
    )
    expected = golden.read_text(encoding="utf-8")
    assert current == expected, (
        f"code-sample.pdf output drifted from {golden}. "
        f"If intentional, re-run with --update-golden."
    )
