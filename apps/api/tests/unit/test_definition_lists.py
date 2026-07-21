"""Unit coverage for opt-in definition-list detection (#161).

The detector is a pure pre-pass over assembled block items, so its guards are
covered here cross-platform; the real-PDF path is in
tests/integration/test_definition_lists.py.

Definition lists carry the highest false-positive risk of the Phase 7
heuristics, so most of these tests are NEGATIVE: they pin the guards that keep a
heading, a long line, a punctuated term, an un-indented paragraph, or a lone
pair from being mistaken for a definition list.
"""
from __future__ import annotations

from app.services.packages_loader import pdf_to_md_module

mod = pdf_to_md_module()


def _profile(*, enabled: bool) -> object:
    return mod.DocProfile(
        body_size=11.0,
        body_font="Body",
        heading_thresholds={1: 18.0, 2: 14.0, 3: 12.5},
        small_size=10.0,
        body_x0=72.0,
        detect_definition_lists=enabled,
    )


def _block(text: str, x0: float, *, size: float = 11.0, font: str = "Body"):
    bbox = (x0, 0.0, x0 + 200.0, 10.0)
    span = mod.Span(text=text, size=size, font=font, flags=0, bbox=bbox)
    return ("block", mod.Block(lines=[mod.Line(spans=[span], bbox=bbox)], bbox=bbox))


def _render(items, *, enabled: bool) -> str:
    return mod.assemble_markdown(items, _profile(enabled=enabled))


_GLOSSARY = [
    _block("HTML", 72.0),
    _block("HyperText Markup Language", 96.0),
    _block("CSS", 72.0),
    _block("Cascading Style Sheets", 96.0),
]


def test_two_pairs_emit_a_definition_list():
    assert _render(_GLOSSARY, enabled=True) == (
        "HTML\n: HyperText Markup Language\n\nCSS\n: Cascading Style Sheets"
    )


def test_off_is_byte_identical_plain_paragraphs():
    # Default path: the four blocks stay separate paragraphs, no `: ` marker.
    assert _render(_GLOSSARY, enabled=False) == (
        "HTML\n\nHyperText Markup Language\n\nCSS\n\nCascading Style Sheets"
    )


def test_single_pair_is_not_promoted():
    # The >= 2 consecutive-pairs guard: one pair stays plain paragraphs.
    items = [_block("HTML", 72.0), _block("HyperText Markup Language", 96.0)]
    assert ": " not in _render(items, enabled=True)


def test_term_with_trailing_punctuation_is_rejected():
    items = [
        _block("HTML:", 72.0),
        _block("HyperText Markup Language", 96.0),
        _block("CSS:", 72.0),
        _block("Cascading Style Sheets", 96.0),
    ]
    assert ": " not in _render(items, enabled=True)


def test_long_term_is_rejected():
    long_term = "A term far too long to be a glossary head " * 3  # > 80 chars
    items = [
        _block(long_term, 72.0),
        _block("definition one here", 96.0),
        _block(long_term, 72.0),
        _block("definition two here", 96.0),
    ]
    assert ": " not in _render(items, enabled=True)


def test_unindented_definition_is_rejected():
    # The definition must be indented past the term; at the same margin it reads
    # as a normal paragraph, not a definition.
    items = [
        _block("HTML", 72.0),
        _block("HyperText Markup Language", 72.0),
        _block("CSS", 72.0),
        _block("Cascading Style Sheets", 72.0),
    ]
    assert ": " not in _render(items, enabled=True)


def test_heading_sized_term_is_rejected():
    # A heading-sized first line classifies as a heading, never a term.
    items = [
        _block("Introduction", 72.0, size=20.0),
        _block("Body paragraph text that explains the section here.", 96.0),
        _block("Overview", 72.0, size=20.0),
        _block("Another body paragraph that stays a paragraph.", 96.0),
    ]
    out = _render(items, enabled=True)
    assert ": " not in out
    assert "# Introduction" in out
