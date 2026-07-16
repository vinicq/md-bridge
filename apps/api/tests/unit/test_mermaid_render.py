"""Unit coverage for the Mermaid transform (#394). Pure, no Chromium.

The module is loaded through the same lazy path convert() uses, so the test also
exercises that the sibling module resolves when the package is imported via the
loader (not just as a CLI on sys.path).
"""
from __future__ import annotations

from app.services.packages_loader import md_to_pdf_module


def _mermaid():
    return md_to_pdf_module()._load_mermaid_render()


def test_transform_rewrites_fence_and_keeps_escaping():
    mm = _mermaid()
    # A bidirectional edge: markdown escaped the `<` and `>` as entities. They
    # must stay escaped so HTML parsing does not swallow `<-->` before Mermaid
    # reads the block through .textContent.
    html = '<pre><code class="language-mermaid">flowchart LR\n  A &lt;--&gt; B</code></pre>'
    out, count = mm.transform_blocks(html)
    assert count == 1
    assert '<pre class="mermaid">' in out
    assert "language-mermaid" not in out
    assert "&lt;--&gt;" in out  # escaping preserved; Mermaid decodes it itself
    assert "<--> B" not in out  # never inserted raw into the DOM


def test_transform_is_a_noop_without_a_diagram():
    mm = _mermaid()
    html = "<p>Plain document, no diagrams.</p>"
    out, count = mm.transform_blocks(html)
    assert count == 0
    assert out == html  # byte-identical: the historic output is preserved


def test_has_mermaid_matches_both_class_forms():
    mm = _mermaid()
    assert mm.has_mermaid('<pre><code class="mermaid">x</code></pre>')
    assert mm.has_mermaid('<pre><code class="language-mermaid">x</code></pre>')
    assert not mm.has_mermaid("<p>no diagram</p>")


def test_assets_inline_the_vendored_bundle_and_raise_the_ready_flag():
    mm = _mermaid()
    head, tail = mm.assets()
    assert ".mermaid" in head  # container css
    assert mm.READY_FLAG in tail  # render always flags completion
    if mm.MERMAID_JS.exists():
        # The committed bundle is inlined with a deterministic init.
        assert "mermaid.initialize" in tail
        assert "deterministicIds" in tail
