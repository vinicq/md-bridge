"""Regression tests for the vendored pdf-to-markdown link annotator."""
from __future__ import annotations

from app.services.packages_loader import pdf_to_md_module


def _make_block(mod):
    span = mod.Span(
        text="hello",
        size=11.0,
        font="Body",
        flags=0,
        bbox=(10.0, 10.0, 50.0, 20.0),
    )
    line = mod.Line(spans=[span], bbox=(10.0, 10.0, 50.0, 20.0))
    block = mod.Block(lines=[line], bbox=(10.0, 10.0, 50.0, 20.0))
    return block, span


def test_annotate_spans_with_links_handles_string_page_destination():
    # PyMuPDF returns link["page"] as a str when a named destination cannot be
    # resolved to a numeric page index. The old code did `page_dest >= 0`
    # against the string and crashed with TypeError. The fix coerces safely
    # and skips the link.
    mod = pdf_to_md_module()
    block, span = _make_block(mod)
    page_links = [{"from": (5.0, 5.0, 60.0, 25.0), "page": "Chapter1"}]

    mod.annotate_spans_with_links([block], page_links)

    assert span.link is None


def test_annotate_spans_with_links_resolves_int_page_destination():
    mod = pdf_to_md_module()
    block, span = _make_block(mod)
    page_links = [{"from": (5.0, 5.0, 60.0, 25.0), "page": 3}]

    mod.annotate_spans_with_links([block], page_links)

    assert span.link == "#page-4"


def test_annotate_spans_with_links_ignores_negative_page():
    mod = pdf_to_md_module()
    block, span = _make_block(mod)
    page_links = [{"from": (5.0, 5.0, 60.0, 25.0), "page": -1}]

    mod.annotate_spans_with_links([block], page_links)

    assert span.link is None


# Bare-URL / email autolinking (#157). The pass is a pure function, so it is
# covered here cross-platform; the integration test that drives a real PDF is
# Windows-skipped by the same tempdir-lock constraint as the other converters.


def test_autolink_off_by_default_is_plain_escape():
    mod = pdf_to_md_module()
    text = "Visit https://example.com now and mail a@b.com"
    assert mod._autolink_escape(text, urls=False, emails=False) == mod.escape_markdown_inline(text)


def test_autolink_wraps_bare_url_and_email():
    mod = pdf_to_md_module()
    assert (
        mod._autolink_escape("Visit https://example.com for details", urls=True, emails=True)
        == "Visit <https://example.com> for details"
    )
    assert (
        mod._autolink_escape("Mail team@example.com anytime", urls=True, emails=True)
        == "Mail <team@example.com> anytime"
    )


def test_autolink_keeps_trailing_sentence_punctuation_outside_link():
    mod = pdf_to_md_module()
    assert (
        mod._autolink_escape("See https://example.com.", urls=True, emails=True)
        == "See <https://example.com>."
    )


def test_autolink_keeps_balanced_parens_in_path():
    # A Wikipedia-style path carries balanced parens; they belong to the URL.
    mod = pdf_to_md_module()
    url = "https://en.wikipedia.org/wiki/Foo_(bar)"
    assert (
        mod._autolink_escape(f"see {url} now", urls=True, emails=True) == f"see <{url}> now"
    )


def test_autolink_strips_wrapping_parens():
    # A URL written inside prose parens must not swallow the closing paren.
    mod = pdf_to_md_module()
    assert (
        mod._autolink_escape("(see https://example.com)", urls=True, emails=True)
        == "(see <https://example.com>)"
    )


def test_autolink_respects_per_type_flags():
    mod = pdf_to_md_module()
    # Emails off: the address is left as escaped prose, the URL still links.
    out = mod._autolink_escape("at https://x.io or a@b.com", urls=True, emails=False)
    assert "<https://x.io>" in out
    assert "<a@b.com>" not in out and "a@b.com" in out


def test_autolink_skips_code_span_and_existing_link():
    mod = pdf_to_md_module()
    # A mono span renders as a code span; autolink must never touch code.
    code = mod.Span(text="https://x.io", size=11.0, font="Body", flags=mod.FLAG_MONO, bbox=(0, 0, 1, 1))
    assert (
        mod.render_span(code, autolink_urls=True, autolink_emails=True) == "`https://x.io`"
    )
    # A span carrying a resolved link wraps as [text](link); autolink inside it
    # would double-wrap the URL.
    linked = mod.Span(text="https://x.io", size=11.0, font="Body", flags=0, bbox=(0, 0, 1, 1))
    linked.link = "https://x.io"
    assert (
        mod.render_span(linked, autolink_urls=True, autolink_emails=True)
        == "[https://x.io](https://x.io)"
    )


# Reference-style links for repeated URLs (#158). The post-pass is a pure
# str->str function, covered here cross-platform.


def test_reference_links_collapse_repeated_url():
    mod = pdf_to_md_module()
    md = "See [spec](https://x.io/s), [again](https://x.io/s), and [more](https://x.io/s)."
    out = mod._collapse_reference_links(md, 3)
    assert "[spec][1]" in out and "[again][1]" in out and "[more][1]" in out
    assert "(https://x.io/s)" not in out  # no inline copies remain
    assert out.rstrip().endswith("[1]: https://x.io/s")


def test_reference_links_leave_under_threshold_inline():
    mod = pdf_to_md_module()
    md = "[a](https://x.io/s) and [b](https://x.io/s)"  # only 2 occurrences
    assert mod._collapse_reference_links(md, 3) == md


def test_reference_links_threshold_zero_is_noop():
    mod = pdf_to_md_module()
    md = "[a](https://x.io/s) [b](https://x.io/s) [c](https://x.io/s)"
    assert mod._collapse_reference_links(md, 0) == md


def test_reference_links_skip_code_and_keep_rare_inline():
    mod = pdf_to_md_module()
    md = (
        "[d1](https://x.io/d) [d2](https://x.io/d) [d3](https://x.io/d) "
        "[rare](https://y.io/r) `[code](https://x.io/d)`"
    )
    out = mod._collapse_reference_links(md, 3)
    assert "[d1][1]" in out and "[d2][1]" in out and "[d3][1]" in out
    assert "`[code](https://x.io/d)`" in out  # code span untouched
    assert "[rare](https://y.io/r)" in out  # single-use stays inline
    assert out.rstrip().endswith("[1]: https://x.io/d")


def test_reference_links_ids_in_first_seen_order():
    mod = pdf_to_md_module()
    md = (
        "[a](https://x.io/1) [b](https://x.io/2) [c](https://x.io/1) "
        "[d](https://x.io/2) [e](https://x.io/1) [f](https://x.io/2)"
    )
    out = mod._collapse_reference_links(md, 3)
    assert "[a][1]" in out and "[b][2]" in out
    assert out.rstrip().split("\n")[-2:] == ["[1]: https://x.io/1", "[2]: https://x.io/2"]
