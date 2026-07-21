"""Unit coverage for opt-in Pandoc grid tables (#166).

`render_table` and the grid emitter are pure over a table's extracted rows, so
they are covered here cross-platform; the real-PDF path (PyMuPDF table
detection through `convert_document`) is in tests/integration/test_grid_tables.py.
"""
from __future__ import annotations

import importlib.util

import pytest
from app.services.packages_loader import md_to_pdf_module, pdf_to_md_module

mod = pdf_to_md_module()

_GRIDS_AVAILABLE = importlib.util.find_spec("markdown_grids") is not None


class _Table:
    def __init__(self, rows):
        self._rows = rows

    def extract(self):
        return self._rows


def _profile(fmt: str) -> object:
    return mod.DocProfile(
        body_size=11.0,
        body_font="Body",
        heading_thresholds={1: 18.0, 2: 14.0, 3: 12.5},
        small_size=10.0,
        multiline_table_format=fmt,
    )


_MULTILINE = _Table([["Term", "Definition"], ["A", "line one\nline two"], ["B", "single"]])
_SINGLE_LINE = _Table([["H1", "H2"], ["a", "b"], ["c", "d"]])


def test_default_flattens_a_multiline_cell_to_a_pipe_table():
    # No profile: the legacy pipe path collapses the newline to a space.
    out = mod.render_table(_MULTILINE)
    assert out.splitlines()[0] == "| Term | Definition |"
    assert "| A | line one line two |" in out
    assert "+" not in out  # not a grid table


def test_pipe_format_is_byte_identical_to_no_profile():
    # An explicit pipe profile matches the profile-less default.
    assert mod.render_table(_MULTILINE, _profile("pipe")) == mod.render_table(_MULTILINE)


def test_grid_format_promotes_a_multiline_cell():
    out = mod.render_table(_MULTILINE, _profile("grid"))
    assert out.startswith("+")
    assert "+======" in out or "+====" in out  # header separator uses '='
    # The two source lines land on two physical rows inside one cell.
    assert "| line one" in out
    assert "| line two" in out


def test_grid_format_keeps_single_line_tables_as_pipe():
    # Grid mode only promotes when a cell actually spans lines; an all-single-line
    # table stays a pipe table, so grid mode does not churn the common case.
    assert mod.render_table(_SINGLE_LINE, _profile("grid")) == mod.render_table(_SINGLE_LINE)
    assert "+" not in mod.render_table(_SINGLE_LINE, _profile("grid"))


@pytest.mark.skipif(not _GRIDS_AVAILABLE, reason="grid-tables extra (markdown-grids) not installed")
def test_grid_output_round_trips_to_a_table_with_both_lines():
    grid = mod.render_table(_MULTILINE, _profile("grid"))
    md_mod = md_to_pdf_module()
    html = md_mod.markdown.markdown(
        grid, extensions=md_mod.MD_EXTENSIONS, output_format="html5"
    )
    assert "<table" in html
    assert "line one" in html and "line two" in html
    # Header + two body rows.
    assert html.count("<tr") == 3
