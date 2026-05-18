"""Pure-function tests of the themes route's human-naming map."""
from __future__ import annotations

from app.routes.themes import _HUMAN_NAMES


def test_human_names_covers_known_themes():
    assert _HUMAN_NAMES["default"] == "Default A4"
    assert _HUMAN_NAMES["editorial"] == "Editorial"
    assert _HUMAN_NAMES["brand-edge"] == "Brand EDGE"


def test_human_names_keys_are_lowercase_css_stems():
    for key in _HUMAN_NAMES:
        assert key == key.lower()
        assert " " not in key
