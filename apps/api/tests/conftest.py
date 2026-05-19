"""Shared fixtures for API tests."""
from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app())


@pytest.fixture
def istqb_pdf() -> Path:
    """The canonical real-world fixture: an ISTQB syllabus committed to the repo
    so the suite is reproducible in CI and on fresh clones."""
    here = Path(__file__).resolve().parent
    p = here / "fixtures" / "istqb-ctal-ta-syllabus-en.pdf"
    assert p.exists(), f"committed fixture missing: {p}"
    return p
