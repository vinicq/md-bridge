"""Shared fixtures for the conversion-layer regression suite.

Loads the converter scripts under `packages/` through
`apps/api/app/services/packages_loader.py`. The same venv used for the API
(`apps/api/.venv`) hosts all dependencies.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "api"))


def pytest_addoption(parser):
    parser.addoption(
        "--update-golden",
        action="store_true",
        default=False,
        help="Rewrite golden snapshots instead of comparing against them.",
    )


@pytest.fixture
def update_golden(request) -> bool:
    return bool(request.config.getoption("--update-golden"))


@pytest.fixture(scope="session")
def golden_dir() -> Path:
    out = ROOT / "tests" / "golden"
    out.mkdir(parents=True, exist_ok=True)
    return out


@pytest.fixture(scope="session")
def istqb_pdf() -> Path:
    """Committed ISTQB CTAL-TA English syllabus, available on every clone."""
    p = ROOT / "apps" / "api" / "tests" / "fixtures" / "istqb-ctal-ta-syllabus-en.pdf"
    assert p.exists(), f"committed ISTQB fixture missing: {p}"
    return p


@pytest.fixture(scope="session")
def pdf_to_md_mod():
    from app.services.packages_loader import pdf_to_md_module

    return pdf_to_md_module()


@pytest.fixture(scope="session")
def md_to_pdf_mod():
    from app.services.packages_loader import md_to_pdf_module

    return md_to_pdf_module()
