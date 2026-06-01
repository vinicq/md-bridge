"""Unit coverage for the markdown-to-pdf YAML front matter parser (#150).

The hand-written split-on-colon loop flattened every value to a string and
dropped anything that was not a flat `key: value`. The parser now uses
`yaml.safe_load`, so list, nested-mapping, and block-scalar values survive.
These drive the pure `split_front_matter` / `build_html` helpers through the
package loader (no Playwright, no Chromium).

Per the issue QA note, one fixture per YAML shape guards against a future loader
swap silently regressing.
"""
from __future__ import annotations

from app.services.packages_loader import md_to_pdf_module

mod = md_to_pdf_module()


def test_flat_scalars_parse_as_strings():
    fm, body = mod.split_front_matter('---\ntitle: "My Doc"\nauthor: Ada\n---\nBody text.\n')
    assert fm == {"title": "My Doc", "author": "Ada"}
    assert body == "Body text.\n"


def test_flow_list_value_returns_a_list():
    fm, _ = mod.split_front_matter("---\nkeywords: [tag1, tag2, tag3]\n---\nBody\n")
    assert fm["keywords"] == ["tag1", "tag2", "tag3"]


def test_block_list_value_returns_a_list():
    fm, _ = mod.split_front_matter("---\nkeywords:\n  - tag1\n  - tag2\n---\nBody\n")
    assert fm["keywords"] == ["tag1", "tag2"]


def test_nested_mapping_returns_a_dict():
    fm, _ = mod.split_front_matter("---\nauthor:\n  name: Ada\n  email: a@x\n---\nBody\n")
    assert fm["author"] == {"name": "Ada", "email": "a@x"}


def test_literal_block_scalar_joins_lines():
    fm, _ = mod.split_front_matter("---\ndescription: |\n  Line one\n  Line two\n---\nBody\n")
    assert fm["description"] == "Line one\nLine two"


def test_no_front_matter_returns_empty_and_original_body():
    text = "No front matter here.\n\nJust a body."
    assert mod.split_front_matter(text) == ({}, text)


def test_malformed_yaml_warns_and_keeps_body(capsys):
    fm, body = mod.split_front_matter("---\nkey: [unclosed\n---\nKEEP THIS BODY")
    assert fm == {}
    assert body == "KEEP THIS BODY"
    assert "could not parse YAML front matter" in capsys.readouterr().err


def test_non_mapping_front_matter_is_ignored():
    # A bare scalar / list between the fences is not a key:value mapping.
    fm, body = mod.split_front_matter("---\njust a bare line\n---\nBody\n")
    assert fm == {}
    assert body == "Body\n"


def test_build_html_coerces_non_string_title():
    # safe_load can yield a date for `title: 2024-01-01`; escape_html needs str.
    html = mod.build_html("<p>x</p>", {"title": __import__("datetime").date(2024, 1, 1)}, "en", [])
    assert "<title>2024-01-01</title>" in html


def test_build_html_defaults_title_when_absent():
    html = mod.build_html("<p>x</p>", {}, "en", [])
    assert "<title>Document</title>" in html


# --- DoS hardening (#150 review): untrusted front matter must not crash or hang ---


def test_alias_bomb_is_rejected_and_body_survives(capsys):
    # A billion-laughs amplifier: safe_load alone would expand the aliases. The
    # no-alias loader rejects it, so it degrades to "no front matter".
    bomb = (
        "---\n"
        "a: &a [1,1,1,1,1,1,1,1,1]\n"
        "b: &b [*a,*a,*a,*a,*a,*a,*a,*a,*a]\n"
        "c: &c [*b,*b,*b,*b,*b,*b,*b,*b,*b]\n"
        "d: [*c,*c,*c,*c,*c,*c,*c,*c,*c]\n"
        "---\nKEEP THIS BODY"
    )
    fm, body = mod.split_front_matter(bomb)
    assert fm == {}
    assert body == "KEEP THIS BODY"
    assert "could not parse YAML front matter" in capsys.readouterr().err


def test_deep_nesting_recursionerror_is_caught_and_body_survives(capsys):
    # Deep nesting raises RecursionError, not YAMLError; the broadened except
    # must catch it so the document still renders.
    deep = "---\n" + ("[" * 600) + "\n---\nKEEP THIS BODY"
    fm, body = mod.split_front_matter(deep)
    assert fm == {}
    assert body == "KEEP THIS BODY"
    assert "could not parse YAML front matter" in capsys.readouterr().err


def test_oversized_front_matter_is_skipped_and_body_survives(capsys):
    big = "---\n" + ("k: v\n" * 20000) + "---\nKEEP THIS BODY"
    fm, body = mod.split_front_matter(big)
    assert fm == {}
    assert body == "KEEP THIS BODY"
    assert "exceeds" in capsys.readouterr().err
