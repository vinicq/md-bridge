"""Unit coverage for the theme registry (#23). Pure, no Chromium."""
from __future__ import annotations

from pathlib import Path

import pytest
from app.services import themes


def test_registry_lists_default_first_and_known_slugs_present():
    slugs = [t.slug for t in themes.list_themes()]
    assert slugs[0] == "default"
    # Core themes shipped from the start must always be present.
    for expected in ("academic", "business", "minimal"):
        assert expected in slugs, f"expected theme slug '{expected}' not found in registry"


def test_get_theme_returns_metadata():
    t = themes.get_theme("academic")
    assert t.slug == "academic"
    assert t.name == "Academic"
    assert t.family == "serif"
    assert t.css_path.name == "academic.css"


def test_unknown_slug_raises_unknown_theme_error():
    with pytest.raises(themes.UnknownThemeError) as exc:
        themes.get_theme("nope")
    assert exc.value.status_code == 400
    assert exc.value.code == "unknown_theme"
    assert exc.value.slug == "nope"


def test_css_paths_default_renders_base_alone():
    paths = themes.css_paths_for("default")
    assert [p.name for p in paths] == ["default.css"]


def test_css_paths_non_default_stacks_overlay_on_base():
    # A theme overlay always rides on top of the default base, so a placeholder
    # overlay still inherits a complete layout.
    paths = themes.css_paths_for("minimal")
    assert [p.name for p in paths] == ["default.css", "minimal.css"]


def test_metadata_loader_tolerates_missing_file(tmp_path: Path):
    # A bare <slug>.css with no sibling json still registers: name falls back to
    # the capitalised slug, the rest to safe defaults.
    meta = themes._load_metadata("fancy", tmp_path / "fancy.theme.json")
    assert meta["name"] == "Fancy"
    assert meta["family"] == "general"
    assert meta["version"] == "0.0.0"


def test_metadata_loader_tolerates_partial_json(tmp_path: Path):
    p = tmp_path / "p.theme.json"
    p.write_text('{"name": "Partial"}', encoding="utf-8")
    meta = themes._load_metadata("p", p)
    assert meta["name"] == "Partial"
    assert meta["description"] == ""  # missing optional field defaults, not crashes


def test_scan_without_default_is_a_500(tmp_path: Path):
    # The default base stylesheet is the renderer's one invariant; a templates
    # dir missing it is a deployment error, not a request error.
    (tmp_path / "academic.css").write_text("body{}", encoding="utf-8")
    with pytest.raises(themes.ApiError) as info:
        themes._scan(tmp_path)
    assert info.value.status_code == 500
    assert info.value.code == "missing_template"


def test_templates_directory_contains_default():
    from app.config import MD_TO_PDF_TEMPLATES

    assert (MD_TO_PDF_TEMPLATES / "default.css").exists()
