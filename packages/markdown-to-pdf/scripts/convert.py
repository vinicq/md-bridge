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
import sys
from pathlib import Path

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


def build_html(body_html: str, fm: dict, lang: str, css_blocks: list[str]) -> str:
    # safe_load can return non-string scalars (a date, a number) or even a list
    # for `title:`; coerce so escape_html always receives a string.
    title = fm.get("title") or "Document"
    if not isinstance(title, str):
        title = str(title)
    style = "\n".join(f"<style>\n{css}\n</style>" for css in css_blocks)
    return (
        '<!DOCTYPE html>\n'
        f'<html lang="{lang}">\n'
        '<head>\n'
        '  <meta charset="utf-8">\n'
        f'  <title>{escape_html(title)}</title>\n'
        f'{style}\n'
        '</head>\n'
        '<body>\n'
        f'{body_html}\n'
        '</body>\n'
        '</html>\n'
    )


def render_to_pdf(html: str, pdf_path: Path, base_url: Path) -> None:
    base_uri = base_url.resolve().as_uri() + "/"
    with sync_playwright() as p:
        browser = p.chromium.launch()
        try:
            page = browser.new_page()
            page.set_content(html, wait_until="networkidle")
            # Resolve relative URLs (for images) by injecting a <base>
            page.evaluate(
                "(href) => { let b = document.querySelector('base');"
                " if (!b) { b = document.createElement('base'); document.head.prepend(b); } b.href = href; }",
                base_uri,
            )
            page.pdf(
                path=str(pdf_path),
                format="A4",
                print_background=True,
                margin={"top": "2.5cm", "right": "2cm", "bottom": "2.5cm", "left": "2cm"},
                prefer_css_page_size=True,
            )
        finally:
            browser.close()


def convert(md_path: Path, pdf_path: Path, css_paths: list[Path], lang: str = "pt-BR") -> None:
    md_text = md_path.read_text(encoding="utf-8")
    fm, body_md = split_front_matter(md_text)
    body_html = markdown.markdown(body_md, extensions=MD_EXTENSIONS, output_format="html5")

    css_blocks: list[str] = []
    for css in css_paths:
        if css.exists():
            css_blocks.append(css.read_text(encoding="utf-8"))
        else:
            print(f"[warn] CSS not found: {css}", file=sys.stderr)

    html = build_html(body_html, fm, lang, css_blocks)
    render_to_pdf(html, pdf_path, base_url=md_path.parent)
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
    args = parser.parse_args()

    if not args.md_path.exists():
        print(f"File not found: {args.md_path}", file=sys.stderr)
        return 1

    css_paths = args.css if args.css else [default_css]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    convert(args.md_path, args.output, css_paths, lang=args.lang)
    return 0


if __name__ == "__main__":
    sys.exit(main())
