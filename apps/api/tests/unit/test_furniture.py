"""Unit coverage for recurrent header/footer subtraction (#187).

Exercises the pure helpers through the API loader: normalization, recurrence
selection, and the band test. No PDF, no subprocess.
"""
from __future__ import annotations

from app.services.packages_loader import pdf_to_md_module

mod = pdf_to_md_module()


def test_normalize_furniture_masks_digits_and_case():
    assert mod.normalize_furniture("Page 3 of 77") == "page # of #"
    assert mod.normalize_furniture("Page 4 of 77") == "page # of #"
    assert mod.normalize_furniture("  v4.0   GA  ") == "v#.# ga"


def test_recurring_header_is_selected():
    header = mod.normalize_furniture("ISTQB Syllabus")
    pages = [{header} for _ in range(5)]
    assert header in mod.select_recurring(pages, 5)


def test_one_off_band_line_is_kept():
    header = mod.normalize_furniture("Running Header")
    oneoff = mod.normalize_furniture("A unique cover note")
    pages = [{header}, {header}, {header}, {header}, {header, oneoff}]
    recurring = mod.select_recurring(pages, 5)
    assert header in recurring
    assert oneoff not in recurring


def test_page_number_with_varying_digits_matches():
    pages = [{mod.normalize_furniture(f"Page {i} of 9")} for i in range(1, 6)]
    assert "page # of #" in mod.select_recurring(pages, 5)


def test_short_doc_subtracts_nothing():
    header = mod.normalize_furniture("Header")
    assert mod.select_recurring([{header}, {header}], 2) == frozenset()


def test_threshold_needs_three_absolute_occurrences():
    header = mod.normalize_furniture("Header")
    # 2 of 5 pages -> below the floor of 3 absolute occurrences
    assert header not in mod.select_recurring([{header}, {header}, set(), set(), set()], 5)
    # 3 of 5 -> selected
    assert header in mod.select_recurring([{header}, {header}, {header}, set(), set()], 5)


def test_select_recurring_is_deterministic():
    pages = [{"a", "b"}, {"a"}, {"a", "b"}, {"a"}, {"a", "b"}]
    outs = [mod.select_recurring(pages, 5) for _ in range(5)]
    assert all(o == outs[0] for o in outs)


def test_in_furniture_band():
    # page height 800: top band <= 56, bottom band >= 744.
    assert mod.in_furniture_band((72.0, 10.0, 300.0, 30.0), 800.0)  # top
    assert mod.in_furniture_band((72.0, 760.0, 300.0, 780.0), 800.0)  # bottom
    assert not mod.in_furniture_band((72.0, 400.0, 300.0, 420.0), 800.0)  # middle
