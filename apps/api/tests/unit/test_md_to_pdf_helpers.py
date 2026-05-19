"""Pure-function tests of md_to_pdf service helpers (no playwright, no IO)."""
from __future__ import annotations

import pytest
from app.config import MD_TO_PDF_TEMPLATES
from app.errors import ApiError
from app.services.md_to_pdf import _default_css_paths


def test_default_css_paths_returns_default_css_only():
    paths = _default_css_paths()
    assert len(paths) == 1
    assert paths[0].name == "default.css"
    assert paths[0].exists(), f"default.css must exist at {paths[0]}"


def test_default_css_paths_raises_when_template_missing(monkeypatch, tmp_path):
    # Point the templates dir at an empty folder so default.css is missing.
    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()
    monkeypatch.setattr("app.services.md_to_pdf.MD_TO_PDF_TEMPLATES", empty_dir)
    with pytest.raises(ApiError) as info:
        _default_css_paths()
    assert info.value.status_code == 500
    assert info.value.code == "missing_template"


def test_templates_directory_contains_default():
    assert (MD_TO_PDF_TEMPLATES / "default.css").exists()
