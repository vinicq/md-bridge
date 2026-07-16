"""Convert structured Markdown to PDF via HTML + CSS using Playwright (Chromium).

Stack:
  markdown (Python) → HTML + embedded CSS → headless Chromium → PDF

Usage:
  python convert.py <input.md> -o <output.pdf> [--css <theme.css>] [--css <override.css>]

Reads YAML front matter (if present) for document title, then renders the
body with the chosen CSS theme(s). Chromium gives us full @page, page
counters, page-break-* and modern CSS without any GTK / wkhtmltopdf binary.

Requires Playwright + Chromium installed. First-time setup:
  pip install playwright
  playwright install chromium
"""
from __future__ import annotations

import argparse
import io
import os
import re
import sys
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import url2pathname

import markdown
import yaml
from playwright.sync_api import sync_playwright

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

MD_EXTENSIONS = [
    "extra",         # tables, fenced code, attribute lists, abbreviations, def lists, footnotes
    "sane_lists",
    "smarty",
    "toc",
    "md_in_html",
]

# Front matter is metadata: a few hundred bytes in practice. Cap the block before
# parsing so a pathological document cannot make the YAML tokenizer chew through
# hundreds of MB of nesting. 64 KiB is far above any real front matter (#150).
_MAX_FRONT_MATTER_CHARS = 64 * 1024


class _FrontMatterLoader(yaml.SafeLoader):
    """SafeLoader that also refuses YAML anchors/aliases.

    `safe_load` blocks arbitrary-object construction (no RCE), but it still
    expands aliases — and that is a billion-laughs amplifier: a few hundred
    bytes of nested `&anchor`/`*alias` materialize millions of nodes and
    exhaust the worker. Front matter never legitimately uses anchors, and this
    parses untrusted uploads, so we reject aliases outright (#150).
    """

    def compose_node(self, parent, index):
        if self.check_event(yaml.events.AliasEvent):
            raise yaml.YAMLError("YAML anchors/aliases are not allowed in front matter")
        return super().compose_node(parent, index)


def split_front_matter(md_text: str) -> tuple[dict, str]:
    """Return (front_matter_dict, body_md). Empty dict if no front matter.

    The block is parsed with `yaml.safe_load`, so list, nested-mapping, and
    block-scalar (`|`, `>`) values survive instead of being flattened to a
    string or dropped by a hand-written split-on-colon loop (#150). A malformed
    block is tolerated the way the old loop tolerated bad lines: the delimiters
    are still stripped from the body, a warning goes to stderr, and parsing
    falls back to an empty mapping so the document still renders. A non-mapping
    top-level value (a bare scalar or list between the fences) is treated as no
    usable front matter.
    """
    for prefix, sep in (("---\n", "\n---\n"), ("---\r\n", "\r\n---\r\n")):
        if md_text.startswith(prefix):
            end = md_text.find(sep, len(prefix))
            if end != -1:
                fm_block = md_text[len(prefix):end]
                body = md_text[end + len(sep):]
                if len(fm_block) > _MAX_FRONT_MATTER_CHARS:
                    print(
                        f"[warn] front matter exceeds {_MAX_FRONT_MATTER_CHARS} chars; skipping it",
                        file=sys.stderr,
                    )
                    return {}, body
                try:
                    parsed = yaml.load(fm_block, Loader=_FrontMatterLoader)
                # Deep nesting raises RecursionError, not YAMLError; both (and an
                # OOM) must fall back to skipping front matter, not crash the
                # render — the body still has to come through (#150).
                except (yaml.YAMLError, RecursionError, MemoryError) as exc:
                    print(f"[warn] could not parse YAML front matter: {exc}", file=sys.stderr)
                    parsed = None
                fm = parsed if isinstance(parsed, dict) else {}
                return fm, body
    return {}, md_text


def escape_html(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def build_html(
    body_html: str, fm: dict, lang: str, css_blocks: list[str], base_uri: str = "",
    extra_head: str = "", body_tail: str = "",
) -> str:
    # safe_load can return non-string scalars (a date, a number) or even a list
    # for `title:`; coerce so escape_html always receives a string.
    title = fm.get("title") or "Document"
    if not isinstance(title, str):
        title = str(title)
    style = "\n".join(f"<style>\n{css}\n</style>" for css in css_blocks)
    # The <base> lives in <head> so relative URLs resolve at parse time against
    # the render tempdir, which is what the egress guard confines file: loads to
    # (#363). No base_uri (e.g. the unit tests) leaves the historic output.
    base_tag = f'  <base href="{escape_html(base_uri)}">\n' if base_uri else ""
    # Injected blocks (mermaid): empty by default, so the historic output is
    # byte-for-byte unchanged for documents without diagrams.
    head_extra = ("\n" + extra_head) if extra_head else ""
    body_extra = ("\n" + body_tail) if body_tail else ""
    return (
        '<!DOCTYPE html>\n'
        f'<html lang="{lang}">\n'
        '<head>\n'
        '  <meta charset="utf-8">\n'
        f'{base_tag}'
        f'  <title>{escape_html(title)}</title>\n'
        f'{style}{head_extra}\n'
        '</head>\n'
        '<body>\n'
        f'{body_html}{body_extra}\n'
        '</body>\n'
        '</html>\n'
    )


# Page-box presets and running-content engine (#243). Chromium ignores CSS
# @page margins and margin-box running headers/footers, so page geometry and
# headers/footers are driven through page.pdf() arguments instead.

# Margin presets in cm. `normal` reproduces the historic hardcoded margin, so
# the default render is byte-for-byte unchanged.
MARGIN_PRESETS = {
    "tight": {"top": "1.5cm", "right": "1.5cm", "bottom": "1.5cm", "left": "1.5cm"},
    "normal": {"top": "2.5cm", "right": "2cm", "bottom": "2.5cm", "left": "2cm"},
    "loose": {"top": "3.5cm", "right": "3cm", "bottom": "3.5cm", "left": "3cm"},
}
_DEFAULT_MARGIN = MARGIN_PRESETS["normal"]
# A running header/footer renders inside the top/bottom margin; too small a
# margin clips it silently. Clamp the relevant side to this floor when content
# is present (Chromium gives the template no room otherwise).
_RUNNING_MARGIN_FLOOR_CM = 1.5

PAGE_SIZES = ("A4", "Letter", "Legal")

# The running-content tokens, matched in a single pass so substituted values are
# never re-interpreted as tokens.
_RUNNING_TOKEN_RE = re.compile(r"\{\{(title|author|date|page|pages)\}\}")


def _cm_value(margin: str) -> float:
    return float(margin.rstrip("cm")) if margin.endswith("cm") else float(margin)


def _author_text(value: object) -> str:
    # Front matter `author` may be a mapping ({name, email}); prefer the name.
    if isinstance(value, dict):
        return str(value.get("name") or "")
    return "" if value is None else str(value)


def build_running_template(slots: dict, fm: dict) -> str | None:
    """Build a Chromium header/footer template from the three slots, or None.

    Tokens: {{title}}/{{author}}/{{date}} are substituted server-side from the
    front matter (escaped), so the print clock is never used; {{page}}/{{pages}}
    become Chromium's pageNumber/totalPages spans, filled at render time. The
    native `.date`/`.title`/`.url` classes are deliberately never emitted — they
    would pull the non-deterministic print date.
    """
    left = (slots or {}).get("left", "") or ""
    center = (slots or {}).get("center", "") or ""
    right = (slots or {}).get("right", "") or ""
    if not (left or center or right):
        return None

    subs = {
        "title": escape_html(str(fm.get("title") or "")),
        "author": escape_html(_author_text(fm.get("author"))),
        "date": escape_html(str(fm.get("date") or "")),
        "page": '<span class="pageNumber"></span>',
        "pages": '<span class="totalPages"></span>',
    }

    def render(text: str) -> str:
        # Single pass: escape the literal slot text, then replace every token in
        # one left-to-right sweep. Substituted values are NOT re-scanned, so a
        # front-matter value that itself contains e.g. `{{page}}` stays literal
        # text and cannot forge a page counter into a title slot (#243 review).
        escaped = escape_html(text)
        return _RUNNING_TOKEN_RE.sub(lambda m: subs[m.group(1)], escaped)

    return (
        '<div style="font-size:9px;width:100%;color:#888;'
        'font-family:Arial,Helvetica,sans-serif;padding:0 2cm;'
        'display:flex;justify-content:space-between;">'
        f'<span style="text-align:left;">{render(left)}</span>'
        f'<span style="text-align:center;">{render(center)}</span>'
        f'<span style="text-align:right;">{render(right)}</span>'
        '</div>'
    )


def resolve_pdf_kwargs(page_setup: dict | None, fm: dict) -> dict:
    """Map the page-setup options onto page.pdf() arguments.

    `None` reproduces the historic call exactly (A4, normal margins, no
    header/footer), so existing renders and goldens do not move. Pure function:
    no Chromium, unit-tested.
    """
    if not page_setup:
        return {
            "format": "A4",
            "print_background": True,
            "margin": dict(_DEFAULT_MARGIN),
            "prefer_css_page_size": True,
        }

    page_size = page_setup.get("page_size", "A4")
    if page_size not in PAGE_SIZES:
        page_size = "A4"
    margin = dict(MARGIN_PRESETS.get(page_setup.get("margins", "normal"), _DEFAULT_MARGIN))

    header_html = build_running_template(page_setup.get("header") or {}, fm)
    footer_html = build_running_template(page_setup.get("footer") or {}, fm)

    # Clamp the margin side that hosts running content so Chromium does not clip
    # it. Silent + correct: the PDF is still valid, just with room for the band.
    if header_html and _cm_value(margin["top"]) < _RUNNING_MARGIN_FLOOR_CM:
        margin["top"] = f"{_RUNNING_MARGIN_FLOOR_CM}cm"
    if footer_html and _cm_value(margin["bottom"]) < _RUNNING_MARGIN_FLOOR_CM:
        margin["bottom"] = f"{_RUNNING_MARGIN_FLOOR_CM}cm"

    kwargs: dict = {
        "format": page_size,
        "print_background": True,
        "margin": margin,
        "prefer_css_page_size": True,
    }
    if header_html or footer_html:
        kwargs["display_header_footer"] = True
        kwargs["header_template"] = header_html or "<span></span>"
        kwargs["footer_template"] = footer_html or "<span></span>"
    return kwargs


# Egress policy for the render sandbox (#363). The renderer must stay offline
# and deterministic (identity contract): a user document that references an
# external URL must not make Chromium reach the network (SSRF on a hosted
# instance), and a file: URL must not escape the render tempdir (local file
# disclosure). The policy decides by scheme; it is orthogonal to which HTML tags
# are allowed, so renderer features (#143/#159/#164) widen a tag allowlist, never
# this egress policy.
_INERT_SCHEMES = frozenset({"data", "blob", "about", ""})


def egress_allowed(url: str, base_dir: Path) -> bool:
    """True if Chromium may load `url` while rendering. data:/blob:/about: are
    inert and always allowed; file: is allowed only inside base_dir; every
    network scheme (http, https, ws, ftp, ...) is denied."""
    parsed = urlparse(url)
    scheme = parsed.scheme.lower()
    if scheme in _INERT_SCHEMES:
        return True
    if scheme == "file":
        try:
            target = Path(url2pathname(parsed.path)).resolve()
        except (ValueError, OSError):
            return False
        base = base_dir.resolve()
        return target == base or base in target.parents
    return False


def _install_egress_guard(context, base_dir: Path) -> None:
    """Abort every request and WebSocket the egress policy denies. Installed on
    the browser context, not a single page: page.route misses a popup's first
    navigation and does not see WebSocket traffic at all, so a script that opens
    a popup or a ws:// socket would otherwise slip past. Opt out with
    MD_BRIDGE_ALLOW_EGRESS=1 for a self-hoster who wants the old fetching."""
    if os.environ.get("MD_BRIDGE_ALLOW_EGRESS") == "1":
        return

    def _guard(route):
        if egress_allowed(route.request.url, base_dir):
            route.continue_()
        else:
            route.abort()

    def _ws_guard(ws):
        # A WebSocketRoute reaches the server only if we connect it. Every ws://
        # and wss:// is a network scheme the policy denies, so this closes them
        # all without ever opening the upstream connection.
        if egress_allowed(ws.url, base_dir):
            ws.connect_to_server()
        else:
            ws.close()

    context.route("**/*", _guard)
    context.route_web_socket("**/*", _ws_guard)


def render_to_pdf(
    html: str,
    pdf_path: Path,
    base_url: Path,
    pdf_kwargs: dict | None = None,
    ready_flag: str | None = None,
) -> None:
    kwargs = pdf_kwargs if pdf_kwargs is not None else resolve_pdf_kwargs(None, {})
    with sync_playwright() as p:
        browser = p.chromium.launch()
        try:
            context = browser.new_context()
            _install_egress_guard(context, base_url)
            page = context.new_page()
            # <base href> already lives in <head> (build_html), so relative URLs
            # resolve at parse time. With egress blocked, "load" is the
            # deterministic wait: aborted requests settle it without the extra
            # networkidle timer, and a runaway inline script trips the timeout
            # instead of hanging the worker forever.
            page.set_content(html, wait_until="load", timeout=30000)
            if ready_flag:
                # Mermaid renders asynchronously; wait for the init script to
                # flag completion so no diagram is captured half-drawn. The init
                # always raises the flag (even on failure or a missing bundle),
                # so this cannot hang past the timeout.
                page.wait_for_function(f"window['{ready_flag}'] === true", timeout=20000)
            page.pdf(path=str(pdf_path), **kwargs)
        finally:
            browser.close()


def _load_mermaid_render():
    """Import the sibling mermaid_render module by path.

    A plain `import mermaid_render` only works when scripts/ is on sys.path (the
    CLI case). The API loads this file via importlib without adding scripts/ to
    the path, so resolve the sibling module from __file__ instead. Loaded lazily
    so a document without diagrams never pays for it.
    """
    import importlib.util

    mm_path = Path(__file__).resolve().parent / "mermaid_render.py"
    spec = importlib.util.spec_from_file_location("md_bridge_mermaid_render", mm_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load mermaid_render from {mm_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def convert(
    md_path: Path,
    pdf_path: Path,
    css_paths: list[Path],
    lang: str = "pt-BR",
    page_setup: dict | None = None,
    render_mermaid: bool = False,
) -> None:
    md_text = md_path.read_text(encoding="utf-8")
    fm, body_md = split_front_matter(md_text)
    body_html = markdown.markdown(body_md, extensions=MD_EXTENSIONS, output_format="html5")

    css_blocks: list[str] = []
    for css in css_paths:
        if css.exists():
            css_blocks.append(css.read_text(encoding="utf-8"))
        else:
            print(f"[warn] CSS not found: {css}", file=sys.stderr)

    # Mermaid (opt-in, #394): rewrite mermaid fences and inject the vendored
    # bundle so Chromium renders diagrams before printing. Off by default, and a
    # no-op for documents without a mermaid block, so existing output is
    # unchanged either way.
    extra_head = body_tail = ""
    ready_flag = None
    if render_mermaid:
        mermaid_render = _load_mermaid_render()
        body_html, mmd_count = mermaid_render.transform_blocks(body_html)
        if mmd_count:
            extra_head, body_tail = mermaid_render.assets()
            ready_flag = mermaid_render.READY_FLAG
            if not mermaid_render.MERMAID_JS.exists():
                print(
                    "[warn] mermaid blocks found but vendor/mermaid.min.js is missing; "
                    "diagram source will render as plain text",
                    file=sys.stderr,
                )

    base_dir = md_path.parent
    base_uri = base_dir.resolve().as_uri() + "/"
    html = build_html(
        body_html, fm, lang, css_blocks, base_uri=base_uri,
        extra_head=extra_head, body_tail=body_tail,
    )
    # Token substitution for header/footer reads the same front matter, so the
    # print clock is never consulted (#243). page_setup=None keeps the historic
    # page geometry exactly.
    pdf_kwargs = resolve_pdf_kwargs(page_setup, fm)
    render_to_pdf(html, pdf_path, base_url=base_dir, pdf_kwargs=pdf_kwargs, ready_flag=ready_flag)
    print(f"Wrote {pdf_path}")


def main() -> int:
    default_css = Path(__file__).resolve().parent.parent / "templates" / "default.css"

    parser = argparse.ArgumentParser(description="Convert Markdown → PDF via Chromium (Playwright).")
    parser.add_argument("md_path", type=Path)
    parser.add_argument("-o", "--output", type=Path, required=True)
    parser.add_argument(
        "--css",
        type=Path,
        action="append",
        default=None,
        help="CSS stylesheet (repeat to stack multiple). Defaults to templates/default.css.",
    )
    parser.add_argument("--lang", default="pt-BR", help="HTML lang attribute (default: pt-BR).")
    parser.add_argument(
        "--mermaid",
        action="store_true",
        help="Render mermaid code fences to diagrams using the vendored bundle (opt-in).",
    )
    args = parser.parse_args()

    if not args.md_path.exists():
        print(f"File not found: {args.md_path}", file=sys.stderr)
        return 1

    css_paths = args.css if args.css else [default_css]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    convert(args.md_path, args.output, css_paths, lang=args.lang, render_mermaid=args.mermaid)
    return 0


if __name__ == "__main__":
    sys.exit(main())
