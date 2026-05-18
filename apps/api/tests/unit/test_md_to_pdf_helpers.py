"""Pure-function tests of md_to_pdf service helpers (no playwright, no IO)."""
from __future__ import annotations

import pytest

from app.config import MD_TO_PDF_TEMPLATES
from app.errors import ApiError
from app.services.md_to_pdf import _css_paths_for_theme


def test_default_theme_returns_default_css_only():
    paths = _css_paths_for_theme("default")
    assert len(paths) == 1
    assert paths[0].name == "default.css"
    assert paths[0].exists(), f"default.css must exist at {paths[0]}"


def test_unknown_theme_raises_api_error_with_available_list():
    with pytest.raises(ApiError) as info:
        _css_paths_for_theme("does-not-exist")
    err = info.value
    assert err.status_code == 400
    assert err.code == "unknown_theme"
    assert isinstance(err.extra_detail, dict)
    assert "available" in err.extra_detail
    assert "default" in err.extra_detail["available"]


def test_custom_theme_layered_on_top_of_default(tmp_path):
    """A theme file dropped next to default.css should be layered on top
    of the default so the custom file only has to override what it cares
    about. This drops a real theme file into the real templates folder for
    the duration of the test, exercising the resolver against the actual
    filesystem rather than patched internals.
    """
    extra = MD_TO_PDF_TEMPLATES / "tmp-theme-for-test.css"
    extra.write_text("body{color:red}", encoding="utf-8")
    try:
        paths = _css_paths_for_theme(extra.stem)
        assert [p.name for p in paths] == ["default.css", "tmp-theme-for-test.css"]
    finally:
        extra.unlink(missing_ok=True)


def test_templates_directory_contains_default():
    assert (MD_TO_PDF_TEMPLATES / "default.css").exists()
