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


def test_is_idempotent():
    mod = pdf_to_md_module()
    src = "a—b…“x” `keep —this`"
    once = mod._smart_typography(src, **ALL_ASCII)
    twice = mod._smart_typography(once, **ALL_ASCII)
    assert once == twice
