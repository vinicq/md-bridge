"""Unit coverage for the HTML emission allow-list helper (#154).

The converter emits pure Markdown by default; `emit_html` is the single gate
any future raw-HTML emission must route through. These tests pin its behavior
and the security cap, and assert the converter-side cap matches the schema cap.
"""
from __future__ import annotations

import logging

from app.schemas.convert import ALLOWED_HTML_TAGS as SCHEMA_CAP
from app.services.packages_loader import pdf_to_md_module

mod = pdf_to_md_module()


def test_emit_html_empty_allowset_drops_tag_and_warns(caplog):
    with caplog.at_level(logging.WARNING):
        out = mod.emit_html("sup", "x", frozenset())
    assert out == "x"
    assert any("sup" in r.message for r in caplog.records)


def test_emit_html_allowed_tag_wraps(caplog):
    with caplog.at_level(logging.WARNING):
        out = mod.emit_html("sup", "x", frozenset({"sup"}))
    assert out == "<sup>x</sup>"
    assert not caplog.records


def test_emit_html_rejects_tag_outside_cap_even_if_allowed(caplog):
    # The hard cap beats the caller: a forced "script" never wraps.
    with caplog.at_level(logging.WARNING):
        out = mod.emit_html("script", "x", frozenset({"script"}))
    assert out == "x"
    assert any("script" in r.message for r in caplog.records)


def test_emit_html_tag_in_cap_but_not_requested_drops():
    assert mod.emit_html("sub", "x", frozenset({"sup"})) == "x"


def test_converter_cap_matches_schema_cap():
    assert mod.ALLOWED_HTML_TAGS == SCHEMA_CAP
