"""Unit tests for abbreviation-glossary extraction (#163).

The folding, the abbreviation guard, the two-column pairer, the inline pairer,
and the tail renderer are pure functions, covered here cross-platform. The
document-level scan (which needs a real PDF) is covered end-to-end in
tests/integration/test_abbreviations.py.
"""
from __future__ import annotations

from app.services.packages_loader import pdf_to_md_module


def test_fold_heading_strips_accents_case_and_space():
    mod = pdf_to_md_module()
    assert mod._fold_heading("Lista de Siglas e Acrônimos") == "lista de siglas e acronimos"
    assert mod._fold_heading("  LIST OF   ABBREVIATIONS  ") == "list of abbreviations"


def test_locale_heading_terms_cover_en_pt_es():
    mod = pdf_to_md_module()
    for heading in (
        "List of Abbreviations and Acronyms",  # en
        "Lista de Siglas e Acrônimos",  # pt
        "Lista de Abreviaturas",  # pt/es
        "Acrónimos",  # es
    ):
        assert mod._fold_heading(heading) in mod._ABBR_HEADING_TERMS
    # A prose definition list or an ISO numbered clause must NOT match.
    assert mod._fold_heading("Glossary") not in mod._ABBR_HEADING_TERMS
    assert mod._fold_heading("3 Terms, definitions and abbreviations") not in mod._ABBR_HEADING_TERMS


def test_looks_like_abbreviation_accepts_tokens_rejects_prose():
    mod = pdf_to_md_module()
    assert mod._looks_like_abbreviation("GQM")
    assert mod._looks_like_abbreviation("HTTP")
    assert mod._looks_like_abbreviation("EaT")  # mixed but mostly upper
    assert not mod._looks_like_abbreviation("Goal")  # mostly lowercase
    assert not mod._looks_like_abbreviation("Assertion Roulette")  # has a space
    assert not mod._looks_like_abbreviation("A")  # too few letters
    assert not mod._looks_like_abbreviation("ABCDEFGHIJK")  # over the length cap


def test_pair_two_columns_pairs_by_baseline():
    mod = pdf_to_md_module()
    cells = [
        (90.0, 100.0, "GQM"),
        (193.0, 100.2, "Goal Question Metric"),
        (90.0, 126.0, "MLM"),
        (193.0, 126.1, "Multivocal Literature Mapping"),
    ]
    assert mod._pair_two_columns(cells) == {
        "GQM": "Goal Question Metric",
        "MLM": "Multivocal Literature Mapping",
    }


def test_pair_two_columns_rejects_single_column():
    mod = pdf_to_md_module()
    # No horizontal gap: not a two-column layout.
    cells = [(90.0, 100.0, "GQM"), (90.0, 126.0, "MLM"), (90.0, 152.0, "NLP")]
    assert mod._pair_two_columns(cells) == {}


def test_pair_two_columns_requires_minimum_pairs():
    mod = pdf_to_md_module()
    cells = [(90.0, 100.0, "GQM"), (193.0, 100.0, "Goal Question Metric")]
    # A single row is below the floor; the pairer needs at least two columns'
    # worth of rows on each side.
    assert mod._pair_two_columns(cells) == {}


def test_pair_inline_rows_splits_leading_token():
    mod = pdf_to_md_module()
    rows = [
        (85.0, 100.0, "AR Assertion Roulette"),
        (85.0, 126.0, "AST Abstract Syntax Tree"),
        (85.0, 152.0, "Steel teST smEll dEtection tooL"),  # subtitle, not a pair
        (85.0, 178.0, "This sentence is ordinary prose."),  # prose, not a pair
    ]
    assert mod._pair_inline_rows(rows) == {
        "AR": "Assertion Roulette",
        "AST": "Abstract Syntax Tree",
    }


def test_render_abbreviation_tail_is_sorted():
    mod = pdf_to_md_module()
    defs = {"NLP": "Natural Language Processing", "GQM": "Goal Question Metric"}
    assert mod.render_abbreviation_tail(defs) == (
        "*[GQM]: Goal Question Metric\n*[NLP]: Natural Language Processing"
    )


def test_first_token_wins_on_collision():
    mod = pdf_to_md_module()
    rows = [
        (85.0, 100.0, "DA Duplicate Assert"),
        (85.0, 126.0, "DA Different Acronym"),
    ]
    assert mod._pair_inline_rows(rows) == {"DA": "Duplicate Assert"}
