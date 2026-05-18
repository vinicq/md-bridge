"""Shared fixtures for API tests."""
from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import REPO_ROOT
from app.main import create_app


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app())


@pytest.fixture
def fixtures_dir() -> Path:
    return REPO_ROOT / "Arquivos-pdf" / "Design Digital"


@pytest.fixture
def small_pdf(fixtures_dir: Path) -> Path:
    """ddp-factsheet-en.pdf is the smallest fixture in the design-digital set."""
    p = fixtures_dir / "ddp-factsheet-en.pdf"
    if not p.exists():
        pytest.skip(f"missing fixture: {p}")
    return p


@pytest.fixture
def tagged_pdf() -> Path:
    """An IREB syllabus expected to be tagged (PDF/UA). Used to validate /api/inspect-pdf."""
    candidates = [
        REPO_ROOT / "Arquivos-pdf" / "Requisito" / "cpre_foundationlevel_syllabus_br_v.3.2.2.pdf",
        REPO_ROOT / "Arquivos-pdf" / "Requisito" / "ireb_cpre_re@agileprimersyllabusandstudyguide_pt_v1.4.pdf",
    ]
    for p in candidates:
        if p.exists():
            return p
    pytest.skip(f"no tagged-syllabus fixture available, tried: {candidates}")


@pytest.fixture
def istqb_pdf() -> Path:
    """The canonical real-world fixture: an ISTQB syllabus committed to the repo
    so the suite is reproducible in CI and on fresh clones."""
    here = Path(__file__).resolve().parent
    p = here / "fixtures" / "istqb-ctal-ta-syllabus-en.pdf"
    assert p.exists(), f"committed fixture missing: {p}"
    return p
