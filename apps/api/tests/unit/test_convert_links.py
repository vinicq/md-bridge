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
