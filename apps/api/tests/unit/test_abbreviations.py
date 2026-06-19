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
    folded = {
        mod._fold_heading(h)
        for h in (
            "List of Abbreviations and Acronyms",  # en
            "Lista de Siglas e Acrônimos",  # pt
            "Lista de Abreviaturas",  # pt/es
            "Acrónimos",  # es
        )
    }
    assert folded <= mod._ABBR_HEADING_TERMS
    # A prose definition list or an ISO numbered clause must NOT match.
    assert mod._fold_heading("Glossary") not in mod._ABBR_HEADING_TERMS
    assert mod._fold_heading("3 Terms, definitions and abbreviations") not in mod._ABBR_HEADING_TERMS


def test_looks_like_abbreviation_accepts_tokens_rejects_prose():
    mod = pdf_to_md_module()
    assert mod._looks_like_abbreviation("GQM") is True
    assert mod._looks_like_abbreviation("HTTP") is True
    assert mod._looks_like_abbreviation("EaT") is True  # mixed but mostly upper
    assert mod._looks_like_abbreviation("Goal") is False  # mostly lowercase
    assert mod._looks_like_abbreviation("Assertion Roulette") is False  # has a space
    assert mod._looks_like_abbreviation("A") is False  # too few letters
    assert mod._looks_like_abbreviation("ABCDEFGHIJK") is False  # over the length cap


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


def test_pair_two_columns_ignores_page_number_furniture():
    # A right-aligned page number (a lone far-right cell) must not become a
    # column anchor and steal the split (#321 Codex P2). The two populous
    # columns win and the furniture is pinned out.
    mod = pdf_to_md_module()
    cells = [
        (90.0, 100.0, "GQM"),
        (193.0, 100.0, "Goal Question Metric"),
        (90.0, 126.0, "MLM"),
        (193.0, 126.0, "Multivocal Literature Mapping"),
        (520.0, 800.0, "13"),  # page-number footer
    ]
    assert mod._pair_two_columns(cells) == {
        "GQM": "Goal Question Metric",
        "MLM": "Multivocal Literature Mapping",
    }


def test_inline_page_ok_rejects_low_density_body_page():
    # A body page with one stray acronym-led line must not read as a glossary
    # continuation (#321 Codex P2): one pair among many prose rows fails the
    # density gate, while a dense glossary page passes.
    mod = pdf_to_md_module()
    body_rows = [(85.0, float(100 + 24 * i), f"line {i}") for i in range(20)]
    one_pair = {"API": "calls the service and returns a payload"}
    assert mod._inline_page_ok(one_pair, body_rows) is False
    dense_rows = [(85.0, float(100 + 24 * i), "x") for i in range(4)]
    two_pairs = {"AR": "Assertion Roulette", "AST": "Abstract Syntax Tree"}
    assert mod._inline_page_ok(two_pairs, dense_rows) is True


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
