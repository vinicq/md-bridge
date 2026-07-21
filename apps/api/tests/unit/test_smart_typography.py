"""Unit tests for the smart-typography post-pass (#171).

The fold transforms and the protect-scanner are pure functions, covered here
cross-platform. End-to-end propagation through the converter is in
tests/integration/test_smart_typography.py.
"""
from __future__ import annotations

from app.services.packages_loader import pdf_to_md_module

ALL_ASCII = {"quotes": "ascii", "ellipsis": "ascii", "dashes": "ascii"}


def test_default_settings_are_a_noop():
    mod = pdf_to_md_module()
    src = "He said “hi”—wait… don’t."
    out = mod._smart_typography(src, quotes="preserve", ellipsis="preserve", dashes="preserve")
    assert out == src  # byte-identical default path


def test_quotes_fold_to_ascii_only_when_enabled():
    mod = pdf_to_md_module()
    src = "“double” and ‘single’"
    folded = mod._smart_typography(src, quotes="ascii", ellipsis="preserve", dashes="preserve")
    assert folded == "\"double\" and 'single'"
    assert mod._smart_typography(src, quotes="preserve", ellipsis="preserve", dashes="preserve") == src


def test_ellipsis_folds_to_three_dots():
    mod = pdf_to_md_module()
    out = mod._smart_typography("wait…", quotes="preserve", ellipsis="ascii", dashes="preserve")
    assert out == "wait..."


def test_dashes_fold_em_then_en():
    mod = pdf_to_md_module()
    out = mod._smart_typography("a—b and c–d", quotes="preserve", ellipsis="preserve", dashes="ascii")
    assert out == "a---b and c--d"


def test_code_is_never_touched():
    mod = pdf_to_md_module()
    src = "prose “x”\n\n`inline —code…`\n\n```\nfenced —“y”…\n```\n\n    indented —“z”"
    out = mod._smart_typography(src, **ALL_ASCII)
    assert 'prose "x"' in out  # prose folded
    assert "`inline —code…`" in out  # inline code untouched
    assert "fenced —“y”…" in out  # fenced code untouched
    assert "    indented —“z”" in out  # indented code untouched


def test_urls_are_never_touched():
    mod = pdf_to_md_module()
    # Inline link, autolink, and a reference-definition line all carry an
    # en-dash and a curly quote inside the URL; none may be folded (#171 review).
    src = "[a](http://x/a–b?q=“y”) text—here\n\n<http://x/c–d>\n\n[1]: http://x/e–f?z=“w”"
    out = mod._smart_typography(src, **ALL_ASCII)
    assert "http://x/a–b?q=“y”" in out  # inline-link URL intact
    assert "<http://x/c–d>" in out  # autolink intact
    assert "[1]: http://x/e–f?z=“w”" in out  # reference-definition URL intact
    assert "text---here" in out  # surrounding prose still folded


def test_prose_after_reference_definition_is_folded():
    # The reference-definition arm must stop at its own line (#322 Codex P2):
    # under re.DOTALL a greedy `.*$` would protect every later paragraph.
    mod = pdf_to_md_module()
    src = "[1]: http://x/a–b\n\nNext—paragraph here."
    out = mod._smart_typography(src, **ALL_ASCII)
    assert "[1]: http://x/a–b" in out  # definition URL intact
    assert "Next---paragraph here." in out  # prose after it still folds


def test_balanced_paren_link_destination_is_protected():
    # A link destination with balanced parens then a smart char must not be
    # half-folded (#322 Codex P2): the whole URL is protected.
    mod = pdf_to_md_module()
    src = "[x](http://e/Foo_(bar)–baz) and prose—here"
    out = mod._smart_typography(src, **ALL_ASCII)
    assert "http://e/Foo_(bar)–baz" in out  # URL en-dash intact
    assert "prose---here" in out  # surrounding prose folded


def test_linked_image_target_url_is_protected():
    # A click-through image `[![alt](src)](target)` (#170): the smart chars in
    # the external target URL must survive, or the link breaks. The prose around
    # it still folds.
    mod = pdf_to_md_module()
    src = "[![logo](http://cdn/l.png)](http://x/a–b?q=“y”) then prose—here"
    out = mod._smart_typography(src, **ALL_ASCII)
    assert "[![logo](http://cdn/l.png)](http://x/a–b?q=“y”)" in out  # whole wrapper intact
    assert "prose---here" in out  # surrounding prose folded


def test_linked_image_target_with_attr_list_is_protected():
    # The image may carry an attr-list (#165) between its `)` and the outer `]`;
    # the target URL past it is still protected whole.
    mod = pdf_to_md_module()
    src = "[![l](http://cdn/l.png){#fig-1 .figure}](http://x/c–d“z”)"
    out = mod._smart_typography(src, **ALL_ASCII)
    assert out == src


def test_is_idempotent():
    mod = pdf_to_md_module()
    src = "a—b…“x” `keep —this`"
    once = mod._smart_typography(src, **ALL_ASCII)
    twice = mod._smart_typography(once, **ALL_ASCII)
    assert once == twice
