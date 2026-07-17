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
from xml.etree.ElementTree import SubElement

import markdown
import yaml
from markdown.extensions import Extension
from markdown.inlinepatterns import SimpleTagInlineProcessor
from markdown.preprocessors import Preprocessor
from markdown.treeprocessors import Treeprocessor
from playwright.sync_api import sync_playwright

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")


class _MarkExtension(Extension):
    """`==text==` -> ``<mark>text</mark>`` (pymdownx-mark syntax, #162).

    python-markdown core ships no highlight/mark rule and the vendored install
    stays lean (no pymdown-extensions dependency), so this registers the single
    inline pattern directly. `pdf-to-markdown` emits this syntax from PDF
    highlight annotations; rendering it here closes the round trip. Emphasis
    inside the marked span still parses (`==**x**==` nests correctly). This
    widens the tag surface only; it never touches the egress policy (#363).
    """

    def extendMarkdown(self, md: markdown.Markdown) -> None:
        md.inlinePatterns.register(
            SimpleTagInlineProcessor(r"(==)(.+?)==", "mark"), "md_bridge_mark", 175
        )


# GFM alert callouts (#159). `> [!NOTE]` and the four siblings render as the
# designer's `.callout` box: a 1px + 4px-left border, an icon+label head, and a
# body. Labels are localized; the marker must sit alone on the blockquote's first
# line, matching GitHub. Colors live in default.css.
_ALERT_RE = re.compile(r"^\[!(NOTE|TIP|IMPORTANT|WARNING|CAUTION)\][ \t]*(?:\n|$)", re.IGNORECASE)

_CALLOUT_LABELS = {
    "en": {"note": "Note", "tip": "Tip", "important": "Important", "warning": "Warning", "caution": "Caution"},
    "pt": {"note": "Nota", "tip": "Dica", "important": "Importante", "warning": "Aviso", "caution": "Atenção"},
    "es": {"note": "Nota", "tip": "Consejo", "important": "Importante", "warning": "Advertencia", "caution": "Precaución"},
}

# One silhouette per type, mirrored from the designer prototype (info circle,
# lightbulb, speech bubble, triangle, octagon). Each entry is (svg-child-tag, attrs).
_CALLOUT_ICONS = {
    "note": [("circle", {"cx": "12", "cy": "12", "r": "9"}), ("path", {"d": "M12 8h.01"}), ("path", {"d": "M11 12h1v4h1"})],
    "tip": [("path", {"d": "M9 18h6"}), ("path", {"d": "M10 22h4"}), ("path", {"d": "M12 2a7 7 0 0 0-4 12.7c.6.5 1 1.2 1 2.3h6c0-1.1.4-1.8 1-2.3A7 7 0 0 0 12 2z"})],
    "important": [("path", {"d": "M21 15a2 2 0 0 1-2 2H8l-5 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"}), ("path", {"d": "M12 8v3"}), ("path", {"d": "M12 14h.01"})],
    "warning": [("path", {"d": "M10.3 4 2 18a2 2 0 0 0 1.7 3h16.6a2 2 0 0 0 1.7-3L13.7 4a2 2 0 0 0-3.4 0z"}), ("path", {"d": "M12 9v4"}), ("path", {"d": "M12 17h.01"})],
    "caution": [("path", {"d": "M8 2h8l6 6v8l-6 6H8l-6-6V8z"}), ("path", {"d": "M12 8v4"}), ("path", {"d": "M12 16h.01"})],
}

_SVG_ATTRS = {
    "class": "callout__icon", "viewBox": "0 0 24 24", "fill": "none",
    "stroke": "currentColor", "stroke-width": "2",
    "stroke-linecap": "round", "stroke-linejoin": "round",
}


def _callout_lang(lang: str) -> str:
    low = lang.lower()
    if low.startswith("pt"):
        return "pt"
    if low.startswith("es"):
        return "es"
    return "en"  # en + de/fr/it fall back to the English label


class _CalloutTreeprocessor(Treeprocessor):
    """Rewrite a GFM alert blockquote into the designer's `.callout` div (#159).

    Runs after block + inline parsing, so the blockquote body is already
    formatted. Reads the `[!TYPE]` marker off the first line, strips it, and
    rebuilds the element as `<div class="callout callout--TYPE">` with an
    icon+label head and a body carrying the rest. A plain blockquote with no
    marker is left untouched. Builds real elements (no raw HTML), so the emit
    gate and the render egress policy (#363) are untouched.
    """

    def __init__(self, md: markdown.Markdown, lang: str):
        super().__init__(md)
        self.lang = _callout_lang(lang)

    def run(self, root):
        for bq in list(root.iter("blockquote")):
            if len(bq) == 0:
                continue
            first = bq[0]
            m = _ALERT_RE.match(first.text or "")
            if m is None:
                continue
            kind = m.group(1).lower()
            first.text = (first.text or "")[m.end():]
            body_children = list(bq)
            # Drop the first paragraph if the marker was all it held.
            if len(first) == 0 and not (first.text and first.text.strip()):
                body_children = body_children[1:]
            self._rebuild(bq, kind, body_children)

    def _rebuild(self, el, kind: str, body_children: list) -> None:
        _build_callout(el, kind, self.lang, body_children)


def _build_callout(el, kind: str, lang: str, body_children: list) -> None:
    """Turn `el` into a `.callout` box of `kind`: clear it, set the class, add an
    icon+label head and a body carrying `body_children`. Shared by the GFM-alert
    treeprocessor (#159) and the `:::` container block processor (#164)."""
    el.tag = "div"
    el.attrib.clear()
    el.set("class", f"callout callout--{kind}")
    el.text = None
    for child in list(el):
        el.remove(child)
    head = SubElement(el, "div", {"class": "callout__head"})
    svg = SubElement(head, "svg", dict(_SVG_ATTRS))
    for tag, attrs in _CALLOUT_ICONS[kind]:
        SubElement(svg, tag, attrs)
    svg.tail = _CALLOUT_LABELS[lang][kind]
    body = SubElement(el, "div", {"class": "callout__body"})
    for child in body_children:
        body.append(child)


# pymdownx-style custom containers (#164): `::: warning` ... `:::`. Docs sites
# (MkDocs, VuePress, Hugo) use these for admonitions. We map the common names
# onto the five base callout types and rewrite the block into GFM alert syntax,
# so it flows through the same callout treeprocessor and CSS as #159 - one visual
# vocabulary, no pymdown-extensions dependency, no extra CSS.
_CONTAINER_ALIASES = {
    "note": "note",
    "info": "important", "important": "important",
    "tip": "tip", "hint": "tip", "success": "tip",
    "warning": "warning", "warn": "warning", "attention": "warning",
    "caution": "caution", "danger": "caution", "error": "caution",
}
_CONTAINER_OPEN = re.compile(r"^ {0,3}:{3,}[ \t]*([A-Za-z][\w-]*)[ \t]*$")
_CONTAINER_CLOSE = re.compile(r"^ {0,3}:{3,}[ \t]*$")


class _ContainerPreprocessor(Preprocessor):
    """Rewrite `::: name` ... `:::` blocks into GFM alert syntax (#164).

    A recognized name maps to one of the five base types; an unrecognized name in
    an otherwise well-formed block falls back to a note. Only a block that has a
    matching closing fence is rewritten, so a stray `:::` line is left alone. The
    rewrite emits `> [!TYPE]` + quoted body, which the callout treeprocessor then
    renders, so containers and GFM alerts share one look. Runs after the fenced-
    code preprocessor, so `:::` inside a code fence is not touched.
    """

    def run(self, lines: list[str]) -> list[str]:
        out: list[str] = []
        i = 0
        while i < len(lines):
            m = _CONTAINER_OPEN.match(lines[i])
            if m:
                j = i + 1
                while j < len(lines) and not _CONTAINER_CLOSE.match(lines[j]):
                    j += 1
                if j < len(lines):  # matching closer found: it is a container
                    kind = _CONTAINER_ALIASES.get(m.group(1).lower(), "note")
                    out.append(f"> [!{kind.upper()}]")
                    for body_line in lines[i + 1:j]:
                        out.append(f"> {body_line}" if body_line.strip() else ">")
                    out.append("")  # blank line terminates the synthesized blockquote
                    i = j + 1
                    continue
            out.append(lines[i])
            i += 1
        return out


class _CalloutExtension(Extension):
    """Register the callout preprocessor + treeprocessor with the label language."""

    def __init__(self, **kwargs):
        self.config = {"lang": ["pt-BR", "Document language for callout labels"]}
        super().__init__(**kwargs)

    def extendMarkdown(self, md: markdown.Markdown) -> None:
        # Run just below the fenced-code preprocessor (25) so code fences are
        # already stashed and a `:::` inside one is not rewritten.
        md.preprocessors.register(_ContainerPreprocessor(md), "md_bridge_container", 24)
        md.treeprocessors.register(
            _CalloutTreeprocessor(md, self.getConfig("lang")), "md_bridge_callout", 15
        )


MD_EXTENSIONS = [
    "extra",         # tables, fenced code, attribute lists, abbreviations, def lists, footnotes
    "sane_lists",
    "smarty",
    "toc",
    "md_in_html",
    _MarkExtension(),  # ==highlight== -> <mark> (#162)
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
    custom_css: str = "",
) -> None:
    md_text = md_path.read_text(encoding="utf-8")
    fm, body_md = split_front_matter(md_text)
    # The callout extension carries the document language for its labels (#159),
    # so it is built per call rather than kept in the static MD_EXTENSIONS list.
    extensions = [*MD_EXTENSIONS, _CalloutExtension(lang=lang)]
    body_html = markdown.markdown(body_md, extensions=extensions, output_format="html5")

    css_blocks: list[str] = []
    for css in css_paths:
        if css.exists():
            css_blocks.append(css.read_text(encoding="utf-8"))
        else:
            print(f"[warn] CSS not found: {css}", file=sys.stderr)

    # User custom CSS (#395) stacks last so it overrides the theme, mirroring how
    # the live preview layers it. Empty by default, so output stays byte-for-byte
    # unchanged. It is inlined as a <style> block (never fetched), and the egress
    # guard still blocks any url()/@import to a network scheme (#363).
    if custom_css.strip():
        css_blocks.append(custom_css)

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
