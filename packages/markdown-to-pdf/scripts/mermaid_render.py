"""Mermaid diagram support for markdown-to-pdf.

Turns mermaid code fences into inline SVG at render time using a LOCALLY
VENDORED mermaid bundle. The render sandbox blocks all network egress (see
_install_egress_guard in convert.py), so a CDN is not an option -- and vendoring
keeps the converter local-first and deterministic.

Determinism: mermaid is initialised with deterministicIds, so generated SVG node
ids are stable across runs. This preserves md-bridge's "same input, same output"
contract and keeps the regression goldens valid. Documents WITHOUT a mermaid
block are untouched: transform_blocks returns the HTML unchanged and no
script/CSS is injected, so existing renders stay byte-for-byte identical.
"""
from __future__ import annotations

import re
from pathlib import Path

# The vendored UMD bundle, committed under packages/markdown-to-pdf/vendor/.
# See vendor/README.md for how to fetch and pin it. It is inlined as text, never
# loaded over file:// (which the egress guard would confine to the tempdir).
VENDOR_DIR = Path(__file__).resolve().parent.parent / "vendor"
MERMAID_JS = VENDOR_DIR / "mermaid.min.js"

# Set by the init script once every diagram has rendered (or immediately when the
# bundle is missing). render_to_pdf waits on this before printing.
READY_FLAG = "__md_bridge_mermaid_ready"

# markdown(fenced_code) emits a mermaid fence as
#   <pre><code class="language-mermaid">ESCAPED SOURCE</code></pre>
# (some configs use class="mermaid"). Match both and capture the escaped body.
_BLOCK_RE = re.compile(
    r'<pre><code class="(?:language-)?mermaid">(.*?)</code></pre>',
    re.DOTALL,
)

_CONTAINER_CSS = (
    "<style>"
    ".mermaid{margin:1em 0;text-align:center;page-break-inside:avoid;break-inside:avoid;}"
    ".mermaid svg{max-width:100%;height:auto;}"
    "</style>"
)

# Deterministic init: fixed ids, strict security (untrusted upload), SVG text
# labels (print-safe). Real newlines here become real newlines in the injected
# <script>; no runtime escaping needed.
_INIT_JS = """
(async () => {
  try {
    mermaid.initialize({
      startOnLoad: false,
      deterministicIds: true,
      securityLevel: 'strict',
      theme: 'neutral',
      flowchart: { htmlLabels: false }
    });
    await mermaid.run({ querySelector: '.mermaid' });
  } catch (e) {
    /* leave the diagram source visible on failure */
  } finally {
    window['__md_bridge_mermaid_ready'] = true;
  }
})();
"""


def has_mermaid(html: str) -> bool:
    """True if the rendered HTML contains at least one mermaid code block."""
    return bool(_BLOCK_RE.search(html))


def transform_blocks(html: str) -> tuple[str, int]:
    """Rewrite mermaid code fences into <pre class="mermaid"> containers.

    The source stays HTML-escaped exactly as markdown emitted it. Mermaid reads
    the block through `.textContent`, which decodes entities for us, so keeping
    the escaping is what preserves the original diagram source: a raw insert
    would let markup-looking source (e.g. a bidirectional edge `A <--> B`, or a
    label containing `<`) be swallowed by HTML parsing before Mermaid sees it.

    Returns (html, count). count == 0 leaves the HTML unchanged.
    """
    count = 0

    def repl(m: re.Match[str]) -> str:
        nonlocal count
        count += 1
        return '<pre class="mermaid">' + m.group(1) + "</pre>"

    return _BLOCK_RE.sub(repl, html), count


def assets() -> tuple[str, str]:
    """Return (extra_head, body_tail) HTML to inject when the document has diagrams.

    extra_head is container CSS for <head>; body_tail is the vendored bundle plus
    the init script that renders diagrams and raises READY_FLAG. If the bundle is
    missing, body_tail only raises the flag so the render still completes and the
    diagram source stays visible as plain text.
    """
    if not MERMAID_JS.exists():
        return _CONTAINER_CSS, "<script>window['" + READY_FLAG + "']=true;</script>"

    lib = MERMAID_JS.read_text(encoding="utf-8")
    init = "<script>\n" + lib + "\n" + _INIT_JS + "</script>"
    return _CONTAINER_CSS, init
