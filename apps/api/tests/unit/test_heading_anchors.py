"""Unit tests for deterministic heading anchors (#152).

The slugger and the heading post-pass are pure functions, covered here
cross-platform.
"""
from __future__ import annotations

from app.services.packages_loader import pdf_to_md_module


def test_slugify_folds_unicode_and_punctuation():
    mod = pdf_to_md_module()
    assert mod._slugify_heading("Café Über") == "cafe-uber"
    assert mod._slugify_heading("Hello, World!") == "hello-world"
    assert mod._slugify_heading("  Spaced   Out  ") == "spaced-out"


def test_slugify_empty_when_nothing_alphanumeric():
    mod = pdf_to_md_module()
    assert mod._slugify_heading("***") == ""
    assert mod._slugify_heading("!?-") == ""


def test_slugify_truncates_to_64_chars():
    mod = pdf_to_md_module()
    assert len(mod._slugify_heading("a" * 100)) == 64


def test_heading_anchors_added_for_every_level():
    mod = pdf_to_md_module()
    md = "\n".join(f"{'#' * n} Title {n}" for n in range(1, 7))
    out = mod._emit_heading_anchors(md)
    for n in range(1, 7):
        assert f"{'#' * n} Title {n} {{#title-{n}}}" in out


def test_heading_anchors_dedup_in_emission_order():
    mod = pdf_to_md_module()
    md = "## Summary\n\nbody\n\n## Summary\n\nmore\n\n## Summary"
    out = mod._emit_heading_anchors(md)
    assert "## Summary {#summary}" in out
    assert "## Summary {#summary-2}" in out
    assert "## Summary {#summary-3}" in out


def test_heading_anchors_dedup_against_suffixed_collision():
    # A base that collides with an already-suffixed slug must skip past it:
    # `Foo`, `Foo 2`, `Foo` -> foo, foo-2, foo-3 (never two `#foo-2`).
    mod = pdf_to_md_module()
    md = "# Foo\n\n## Foo 2\n\n### Foo"
    out = mod._emit_heading_anchors(md)
    anchors = [line.split("{#")[1].rstrip("}") for line in out.split("\n") if "{#" in line]
    assert anchors == ["foo", "foo-2", "foo-3"]
    assert len(anchors) == len(set(anchors))  # all distinct


def test_heading_anchors_skip_fenced_code_and_existing_anchor():
    mod = pdf_to_md_module()
    md = "# Real\n\n```\n# not a heading\n```\n\n## Done {#custom}"
    out = mod._emit_heading_anchors(md)
    assert "# Real {#real}" in out
    assert "# not a heading\n" in out  # left intact inside the fence
    assert "{#not-a-heading}" not in out
    assert "## Done {#custom}" in out  # already anchored, not doubled


def test_heading_anchors_empty_text_falls_back_to_section():
    mod = pdf_to_md_module()
    assert mod._emit_heading_anchors("### ***") == "### *** {#section}"
