"""Unit coverage for normalize_span_text (#bug-special-chars).

Exercises the pure text normalizer through the packages loader. No PDF, no
subprocess — just the function itself against known Unicode artifacts emitted
by PyMuPDF.
"""
from __future__ import annotations

from app.services.packages_loader import pdf_to_md_module

mod = pdf_to_md_module()


def test_strips_bom_from_middle_of_string():
    # ﻿ is a BOM that PyMuPDF sometimes injects mid-span.
    assert mod.normalize_span_text("hello﻿world") == "helloworld"


def test_strips_zero_width_space():
    assert mod.normalize_span_text("a​b") == "ab"


def test_normalises_non_breaking_space_to_regular_space():
    assert mod.normalize_span_text("foo\xa0bar") == "foo bar"


def test_normalises_en_space_to_regular_space():
    assert mod.normalize_span_text("foo bar") == "foo bar"


def test_clean_string_passes_through_unchanged():
    s = "This is a normal string."
    assert mod.normalize_span_text(s) == s


def test_empty_string_returns_empty():
    assert mod.normalize_span_text("") == ""


def test_multiple_artifacts_in_one_span():
    # A BOM at the start plus an NBSP in the middle.
    assert mod.normalize_span_text("﻿hello\xa0world") == "hello world"
