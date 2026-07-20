"""Convert a digitally-generated PDF to structured Markdown.

Heuristic, no-AI. Uses PyMuPDF for text + font metadata and table detection.

Usage: python convert.py <input.pdf> -o <output.md> [--debug]

Detects:
  - Headings (H1/H2/H3) by relative font size
  - Bold/italic inline by font flags + font name
  - Bulleted lists (▪, •, -, *, o, ●) and numbered lists (1., 1), a))
  - Tables (PyMuPDF page.find_tables)
  - Code blocks and inline code (monospace font flag / deep indent)
  - Paragraph breaks (block boundaries)
  - Page breaks (--- between pages, optional)
"""
from __future__ import annotations

import argparse
import base64
import io
import logging
import re
import sys
import unicodedata
from collections import Counter
from dataclasses import dataclass, field
from math import ceil
from pathlib import Path

import fitz  # PyMuPDF

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

log = logging.getLogger(__name__)

FLAG_SUPERSCRIPT = 1 << 0
FLAG_ITALIC = 1 << 1
FLAG_SERIF = 1 << 2
FLAG_MONO = 1 << 3
FLAG_BOLD = 1 << 4

# Strikethrough is not a font flag: PDFs draw it as a line over the glyphs.
# PyMuPDF surfaces it on the span's `char_flags` bit 0, but only when the page
# is extracted with TEXT_COLLECT_STYLES (mupdf then correlates the drawn line
# with the text). Both the flag and char_flags are recent; gate with getattr so
# older PyMuPDF degrades to "no strikethrough" deterministically (#142).
CHAR_FLAG_STRIKEOUT = 1 << 0
_STYLE_FLAGS = getattr(fitz, "TEXT_COLLECT_STYLES", 0)
_DICT_FLAGS = getattr(fitz, "TEXTFLAGS_DICT", 0)

# mupdf's strikeout bit fires for any horizontal line crossing the text at
# mid-height, including a full-width page rule that merely overlaps a line of
# text. A genuine strike spans roughly the struck text; a rule overruns the
# span toward the margins. We cross-check the drawn-line geometry and clear the
# flag when only an overrunning stroke crosses the span (#202). A stroke counts
# as a strike when it stays within the span x-range give or take this many
# points on each side.
STRIKETHROUGH_OVERRUN_TOL = 6.0


def page_text_dict(page: fitz.Page) -> dict:
    """`page.get_text("dict")` with style collection when the build supports it.

    Style collection is what populates `char_flags` with the strikeout bit. When
    the running PyMuPDF lacks the constants, fall back to the plain call so the
    converter still works (strikethrough simply stays undetected).
    """
    if _STYLE_FLAGS and _DICT_FLAGS:
        return page.get_text("dict", flags=_DICT_FLAGS | _STYLE_FLAGS)
    return page.get_text("dict")

BULLET_CHARS = {"▪", "•", "●", "◦", "‣", "⁃", "∙"}
NUMBERED_RE = re.compile(r"^\s*(\d{1,3}|[a-zA-Z])[.)]\s+")

# Strip invisible zero-width characters (BOM, ZWNBSP, zero-width joiners) that
# PDFs embed as empty glyph runs. These surface as `**﻿**` or `### ﻿` in the
# output — headings or bold spans containing nothing visible (#text-artifacts).
# Also normalise unusual Unicode spaces (NBSP, en-space, thin-space, etc.) to
# regular ASCII space so word boundaries work in downstream tools. This set
# includes U+2007 figure space on purpose: tabular figures lose their alignment
# in plain Markdown anyway, so a normal space reads better than a stray glyph.
_ZERO_WIDTH_RE = re.compile(
    "[﻿​‌‍⁠￾]"
)
_UNUSUAL_SPACE_RE = re.compile(
    "[\xa0         ]"
)


def normalize_span_text(text: str) -> str:
    """Remove invisible zero-width marks and normalise unusual whitespace."""
    text = _ZERO_WIDTH_RE.sub("", text)
    text = _UNUSUAL_SPACE_RE.sub(" ", text)
    return text

# CommonMark inline punctuation that changes meaning anywhere in body text:
# a backslash, code backticks, emphasis markers, and link brackets. Escaping
# these keeps literal prose (`5 * 3`, `my_file.txt`, `[NOTE]`) from being parsed
# as emphasis, code, or a link downstream. Line-start-only specials (`#`, `-`,
# `>`, ordered-list `.`) are intentionally not handled here: a span has no line
# position, so those belong to line-level assembly, not span rendering (#192).
_MD_INLINE_ESCAPE = re.compile(r"([\\`*_\[\]])")


def escape_markdown_inline(text: str) -> str:
    """Backslash-escape inline Markdown punctuation in literal body text."""
    return _MD_INLINE_ESCAPE.sub(r"\\\1", text)


# Bare-URI and email autolinking (#157). Opt-in: off by default so existing
# conversions stay byte-identical. The URL grabs every non-space, non-angle char
# and `_trim_autolink_url` then peels trailing sentence punctuation, so
# `see https://x.` links `https://x` and a Wikipedia-style path
# `https://en.wikipedia.org/wiki/Foo_(bar)` keeps its balanced parens. CommonMark
# autolink syntax (`<...>`) renders the literal URI without inline escaping, so a
# URL with `_` or `~` survives intact.
_AUTOLINK_SCAN_RE = re.compile(
    r"(?P<url>\bhttps?://[^\s<>]+)"
    r"|(?P<email>\b[\w.+-]+@[\w-]+\.[\w.-]+\b)"
)


def _trim_autolink_url(url: str) -> str:
    """Peel trailing characters that read as sentence punctuation, not URL.

    Mirrors the GFM autolink-extension trailing rules: drop a run of
    `?!.,:;*_~'"` from the end, and drop a closing `)` only when the URL holds
    more `)` than `(`. A balanced `..._(bar)` keeps its parens; a URL written
    inside prose parens does not swallow the closing one.
    """
    while url:
        last = url[-1]
        if last in "?!.,:;*_~'\"":
            url = url[:-1]
            continue
        if last == ")" and url.count(")") > url.count("("):
            url = url[:-1]
            continue
        break
    return url


def _autolink_escape(text: str, *, urls: bool, emails: bool) -> str:
    """Escape literal prose, but wrap bare URLs/emails in CommonMark autolinks.

    With both flags off this is exactly `escape_markdown_inline`, so the default
    output stays byte-identical. A matched URI becomes `<uri>`, except a URL that
    carries `*` (which the angle form would italicize) falls back to `[u](u)`.
    Text between matches is escaped as normal prose. Callers gate this to literal
    spans only, so code spans and pre-annotated links never reach it.
    """
    if not (urls or emails):
        return escape_markdown_inline(text)
    out: list[str] = []
    pos = 0
    for m in _AUTOLINK_SCAN_RE.finditer(text):
        is_url = m.lastgroup == "url"
        if (is_url and not urls) or (not is_url and not emails):
            continue  # type disabled: leave the token to be escaped as prose
        token = _trim_autolink_url(m.group(0)) if is_url else m.group(0)
        if not token:
            continue  # whole match was trailing punctuation; treat as prose
        out.append(escape_markdown_inline(text[pos:m.start()]))
        out.append(f"[{token}]({token})" if is_url and "*" in token else f"<{token}>")
        pos = m.start() + len(token)
    out.append(escape_markdown_inline(text[pos:]))
    return "".join(out)


# Reference-style links for repeated URLs (#158). A document-level post-pass:
# count inline `[text](url)` call sites, and for any URL at or above the
# threshold rewrite the call sites to `[text][id]` and append a definitions
# block. Off by default (threshold 0) so existing output stays byte-identical.
# The scan skips fenced code, indented (4-space/tab) code, inline code, and
# images so a `[x](y)` inside any code is never collapsed. The link
# destination allows one level of balanced parens, so a Wikipedia-style
# `.../Foo_(bar)` is captured whole instead of truncating at the first `)`.
# Autolinks (`<url>`, #157) are a different syntax and are left untouched.
_REF_LINK_TOKEN_RE = re.compile(
    r"(?P<fence>^(?P<fence_marker>```|~~~)[^\n]*\n.*?^(?P=fence_marker)[^\n]*$)"
    r"|(?P<indented>^(?: {4}|\t)[^\n]*$)"
    r"|(?P<code>`+[^`]*`+)"
    r"|(?P<image>!\[[^\]]*\]\([^)]*\))"
    r"|(?P<link>\[(?P<link_text>[^\]]*)\]\((?P<link_url>(?:[^()\s]|\([^()\s]*\))+)\))",
    re.MULTILINE | re.DOTALL,
)


def _collapse_reference_links(md: str, threshold: int) -> str:
    """Rewrite inline links whose URL repeats >= threshold times into
    reference style, appending one `[id]: url` definition per collapsed URL.

    Deterministic: ids are assigned in first-seen order, no hashing. With
    threshold <= 0 the text is returned unchanged. Fenced/inline code and
    images are matched by the scanner so their contents are never rewritten.
    """
    if threshold <= 0:
        return md
    counts: dict[str, int] = {}
    order: list[str] = []
    for m in _REF_LINK_TOKEN_RE.finditer(md):
        if m.group("link") is None:
            continue
        url = m.group("link_url")
        if url not in counts:
            counts[url] = 0
            order.append(url)
        counts[url] += 1
    ids: dict[str, str] = {}
    for url in order:
        if counts[url] >= threshold:
            ids[url] = str(len(ids) + 1)
    if not ids:
        return md

    def _rewrite(m: re.Match[str]) -> str:
        if m.group("link") is None:
            return m.group(0)
        rid = ids.get(m.group("link_url"))
        if rid is None:
            return m.group(0)
        return f"[{m.group('link_text')}][{rid}]"

    body = _REF_LINK_TOKEN_RE.sub(_rewrite, md)
    defs = "\n".join(f"[{ids[url]}]: {url}" for url in order if url in ids)
    return f"{body.rstrip()}\n\n{defs}\n"


# Smart typography (#171). A document-level post-pass that folds Unicode
# typography back to ASCII: curly quotes -> straight, ellipsis -> ..., en/em
# dash -> --/---. Every option defaults to preserving the source glyph, so the
# default path is a no-op and output stays byte-identical. The transforms only
# ever remove a Unicode source character, so re-running the pass is idempotent.
# NBSP handling is intentionally out of scope: the converter normalizes a
# non-breaking space to a regular space upstream, so by the time this pass runs
# there is no NBSP left to reshape; preserving it needs an upstream change and
# is left as a follow-up.
#
# Typography must never touch code or a URL. This protect-scanner matches
# fenced/indented/inline code, images, inline links, autolinks, AND
# reference-style definition lines (`[id]: url`), emitting each verbatim; the
# transforms apply only to the prose between matches. (Reference-definition
# lines are appended by `_collapse_reference_links` and are NOT covered by its
# own tokenizer, so they are protected explicitly here, #171 review.)
_TYPO_PROTECT_RE = re.compile(
    # Only the fenced-code arm spans lines (DOTALL); every other arm is
    # line-bounded with [^\n] so DOTALL's `.` cannot run past the line. The
    # link/image destinations allow one level of balanced parens, mirroring
    # `_REF_LINK_TOKEN_RE`, so a URL like `Foo_(bar)` is captured whole (#171).
    r"(?P<fence>^(?P<fence_marker>```|~~~)[^\n]*\n.*?^(?P=fence_marker)[^\n]*$)"
    r"|(?P<indented>^(?: {4}|\t)[^\n]*$)"
    r"|(?P<refdef>^ {0,3}\[[^\]]+\]:[^\n]+$)"
    r"|(?P<code>`+[^`]*`+)"
    r"|(?P<image>!\[[^\]]*\]\((?:[^()\s]|\([^()\s]*\))+\))"
    r"|(?P<link>\[[^\]]*\]\((?:[^()\s]|\([^()\s]*\))+\))"
    r"|(?P<autolink><[^>\s]+>)",
    re.MULTILINE | re.DOTALL,
)


def _fold_typography(text: str, *, quotes: str, ellipsis: str, dashes: str) -> str:
    """Apply the enabled ASCII-folding transforms to one prose segment."""
    if dashes == "ascii":
        # Em-dash before en-dash; both sources vanish, so the pass is idempotent.
        text = text.replace("—", "---").replace("–", "--")
    if ellipsis == "ascii":
        text = text.replace("…", "...")
    if quotes == "ascii":
        text = (
            text.replace("“", '"').replace("”", '"')
            .replace("‘", "'").replace("’", "'")
        )
    return text


def _smart_typography(md: str, *, quotes: str, ellipsis: str, dashes: str) -> str:
    """Fold Unicode typography to ASCII in prose, never inside code or a URL.

    With every option at its default the pass returns the text unchanged. Code
    spans/blocks, images, links, autolinks, and reference-definition lines are
    matched and re-emitted verbatim so a quote or dash inside a URL or a code
    sample is never rewritten (#171)."""
    if quotes == "preserve" and ellipsis == "preserve" and dashes == "preserve":
        return md
    out: list[str] = []
    pos = 0
    for m in _TYPO_PROTECT_RE.finditer(md):
        out.append(_fold_typography(md[pos:m.start()], quotes=quotes, ellipsis=ellipsis, dashes=dashes))
        out.append(m.group(0))
        pos = m.end()
    out.append(_fold_typography(md[pos:], quotes=quotes, ellipsis=ellipsis, dashes=dashes))
    return "".join(out)


# GFM task-list normalization (#172). A document-tail post-pass that maps
# checkbox glyphs and OCR bracket sequences to `- [ ]` / `- [x]`. Only the
# unambiguous checkbox glyphs are mapped; the bullet glyphs the converter
# already uses as list markers (`■`, `▪`, `•`, ...) are deliberately excluded so
# a plain bullet list is never mistaken for a checklist. Off by default so the
# output stays byte-identical.
_TASK_UNCHECKED = frozenset({"☐", "□", "▢"})
_TASK_CHECKED = frozenset({"☑", "☒", "✓", "✔", "✗", "✘"})
# Leading indent is capped at 3 spaces: 4+ spaces (or a tab) is a Markdown
# indented code block, which must never be rewritten. The optional list marker
# may be raw (`- `, converter-emitted) or backslash-escaped (`\- `, from a
# source hyphen the converter escaped because it classified the line as prose).
_TASK_INDENT = r"(?P<indent> {0,3})(?:\\?[-*+]\s+)?"
_TASK_GLYPH_RE = re.compile(
    r"^" + _TASK_INDENT
    + r"(?P<box>[" + re.escape("".join(_TASK_UNCHECKED | _TASK_CHECKED)) + r"])"
    + r"\s+(?P<rest>\S.*)$"
)
# OCR / plain-text bracket form: `[ ]`, `[x]`, `[X]`, or `[-]` (in-progress,
# extended mode only). The brackets may arrive backslash-escaped: the converter
# escapes literal `[`/`]` in body text, so an OCR'd `[ ]` reaches this post-pass
# as `\[ \]`.
_TASK_BRACKET_RE = re.compile(
    r"^" + _TASK_INDENT + r"\\?\[(?P<mark>[ xX-])\\?\]\s+(?P<rest>\S.*)$"
)
# 3+ backticks or tildes; the fence is closed only by the same character type,
# so a `~~~` line inside a ``` block stays literal content.
_FENCE_RE = re.compile(r"^\s*(?P<fence>`{3,}|~{3,})")


def _normalize_task_lists(md: str, *, extended: bool) -> str:
    """Rewrite checkbox glyphs and bracket sequences into GFM task-list items.

    Idempotent: an already-canonical `- [ ]` / `- [x]` line maps to itself. Lines
    inside fenced code blocks (matched by opening marker type), indented code
    (4+ spaces), blockquotes, and tables are left untouched. The todo-md `[-]`
    in-progress marker is recognized only when `extended` is set; otherwise it is
    left as literal text.
    """
    lines = md.split("\n")
    fence_char: str | None = None
    for i, line in enumerate(lines):
        fm = _FENCE_RE.match(line)
        if fm:
            marker = fm.group("fence")[0]
            if fence_char is None:
                fence_char = marker
            elif marker == fence_char:
                fence_char = None
            # a different marker while inside a fence is code content, not a close
            continue
        if fence_char is not None:
            continue
        glyph = _TASK_GLYPH_RE.match(line)
        if glyph:
            mark = "x" if glyph.group("box") in _TASK_CHECKED else " "
            lines[i] = f"{glyph.group('indent')}- [{mark}] {glyph.group('rest')}"
            continue
        bracket = _TASK_BRACKET_RE.match(line)
        if bracket:
            raw = bracket.group("mark")
            if raw == "-" and not extended:
                continue
            mark = raw.lower() if raw != " " else " "
            lines[i] = f"{bracket.group('indent')}- [{mark}] {bracket.group('rest')}"
    return "\n".join(lines)


# Deterministic heading anchors (#152). A document-level post-pass appends a
# Pandoc/mkdocs `{#slug}` attribute to each ATX heading so the same heading
# lands at the same anchor across renderers. Off by default so existing output
# stays byte-identical; renderers that do not parse the attribute show it as
# literal trailing text (acceptable degradation).
_HEADING_RE = re.compile(r"^(?P<hashes>#{1,6})\s+(?P<text>.*\S)\s*$")
_ALREADY_ANCHORED_RE = re.compile(r"\{#[^}]+\}\s*$")


def _slugify_heading(text: str) -> str:
    """Lowercase, ASCII-fold, and dash-join a heading into a stable slug.

    NFKD normalize then drop combining marks (so `Café` -> `cafe`), collapse
    every run of non-alphanumeric characters to a single `-`, strip framing
    `-`, and cap at 64 chars. Returns "" when nothing alphanumeric survives;
    the caller substitutes a fallback so the anchor is never empty.
    """
    folded = unicodedata.normalize("NFKD", text)
    ascii_text = "".join(c for c in folded if not unicodedata.combining(c)).lower()
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_text).strip("-")
    return slug[:64].rstrip("-")


def _emit_heading_anchors(md: str) -> str:
    """Append a deduplicated `{#slug}` to each ATX heading outside code fences.

    Slugs collide-suffix in emission order (`summary`, `summary-2`, ...). A
    heading that already carries a `{#...}` attribute is left untouched, and a
    `#` line inside a fenced code block is not treated as a heading.
    """
    seen: dict[str, int] = {}
    # Seed the registry with ids already emitted as attr-lists elsewhere - figure
    # anchors `{#fig-N}` (#165) live on image lines - so a heading whose slug
    # collides with one gets suffixed instead of emitting a duplicate id (#415).
    used: set[str] = set(re.findall(r"\{#([^}\s]+)", md))
    out: list[str] = []
    in_fence = False
    fence_marker = ""
    for line in md.split("\n"):
        stripped = line.lstrip()
        if not in_fence and (stripped.startswith("```") or stripped.startswith("~~~")):
            in_fence, fence_marker = True, stripped[:3]
            out.append(line)
            continue
        if in_fence:
            if stripped.startswith(fence_marker):
                in_fence = False
            out.append(line)
            continue
        m = _HEADING_RE.match(line)
        if not m or _ALREADY_ANCHORED_RE.search(line):
            out.append(line)
            continue
        text = m.group("text")
        base = _slugify_heading(text) or "section"
        # Suffix against the final emitted slugs, not just the base count, so a
        # base that collides with an already-suffixed slug (`Foo`, `Foo 2`,
        # `Foo` -> foo, foo-2, foo-3) never emits a duplicate anchor.
        n = seen.get(base, 0) + 1
        slug = base if n == 1 else f"{base}-{n}"
        while slug in used:
            n += 1
            slug = f"{base}-{n}"
        seen[base] = n
        used.add(slug)
        out.append(f"{m.group('hashes')} {text} {{#{slug}}}")
    return "\n".join(out)


# Quote attribution pairing (#173). A blockquote followed by a short
# dash-introduced line ("> quote" then "- Author") loses the pairing: the
# attribution lands as a separate paragraph. This post-pass folds that line
# back into the blockquote as a trailing paragraph. Off by default; it only
# ever fires after a `>` block, which the converter emits solely under
# detect_blockquotes, so default output stays byte-identical.
_ATTRIBUTION_RE = re.compile("^\\s*(?:—|–|―|--)\\s*\\S")
# A thematic break / page separator (`---`, `***`, `___`, `- - -`) starts with a
# dash run too, so it must be excluded from attribution binding or a page break
# emitted by --page-break would be swallowed into the quote above it.
_THEMATIC_BREAK_RE = re.compile(r"^\s*([-*_])(?:\s*\1){2,}\s*$")


def _pair_quote_attribution(md: str) -> str:
    """Fold a standalone dash-introduced attribution line into the blockquote
    immediately above it, as a trailing `>` paragraph. Skips fenced code (a `>`
    line inside a fence is a code sample, not a quote) and never binds a
    thematic break or page separator."""
    lines = md.split("\n")
    out: list[str] = []
    n = len(lines)
    i = 0
    in_fence = False
    fence_marker = ""
    while i < n:
        stripped = lines[i].lstrip()
        if not in_fence and (stripped.startswith("```") or stripped.startswith("~~~")):
            in_fence, fence_marker = True, stripped[:3]
            out.append(lines[i])
            i += 1
            continue
        if in_fence:
            if stripped.startswith(fence_marker):
                in_fence = False
            out.append(lines[i])
            i += 1
            continue
        if not lines[i].startswith(">"):
            out.append(lines[i])
            i += 1
            continue
        start = i
        while i < n and lines[i].startswith(">"):
            i += 1
        quote = lines[start:i]
        # A single blank line then a one-line dash attribution (itself followed
        # by a blank or EOF, and not a thematic break) binds to the quote above.
        attr = lines[i + 1] if i + 1 < n else ""
        if (
            i + 1 < n
            and lines[i].strip() == ""
            and _ATTRIBUTION_RE.match(attr)
            and not _THEMATIC_BREAK_RE.match(attr)
            and (i + 2 >= n or lines[i + 2].strip() == "")
        ):
            quote.append(">")
            quote.append(f"> {attr.strip()}")
            out.extend(quote)
            i += 2
            continue
        out.extend(quote)
    return "\n".join(out)


# Line-start-only CommonMark block markers (#192). These only change meaning at
# the very start of a line, so the span pass above cannot handle them (a span
# has no line position). Applied at line-level assembly to a paragraph that was
# classified as prose, never to a detected heading/list/quote (those carry the
# real marker we just synthesized). Optional leading spaces are tolerated since
# CommonMark allows up to three before a block marker.
#   ATX heading:    `#`..`######` followed by a space or end of line
#   bullet list:    `-`, `+`, `*` followed by a space (or bare, a thematic-break edge)
#   blockquote:     `>`
#   ordered list:   a 1-9 digit run followed by `.` or `)` and a space/EOL
_MD_LINE_START_SPECIAL = re.compile(
    r"^(?P<indent> {0,3})"
    r"(?P<marker>#{1,6}(?=\s|$)|[-+*](?=\s|$)|>|\d{1,9}(?=[.)](?:\s|$)))"
)


def escape_line_start_specials(text: str) -> str:
    """Backslash-escape a leading block marker on each line of literal prose.

    Operates per physical line so a hard-broken paragraph (#156) is covered too.
    Only the single leading marker is escaped; the rest of the line is left as
    the span pass rendered it. A line with no leading marker is returned
    unchanged, so the default path stays byte-identical for ordinary prose.

    The ordered-list case escapes only the trailing punctuation of the marker
    (`1\\. text`), which is the minimal escape CommonMark needs to stop a list
    from forming while keeping the digit visible.
    """

    def _escape_one(line: str) -> str:
        m = _MD_LINE_START_SPECIAL.match(line)
        if not m:
            return line
        marker = m.group("marker")
        rest = line[m.end():]
        if marker.isdigit():
            # `12) ...` / `12. ...`: escape the `.`/`)` that triggers the list.
            sep, rest = rest[0], rest[1:]
            return f"{m.group('indent')}{marker}\\{sep}{rest}"
        return f"{m.group('indent')}\\{marker}{rest}"

    return "\n".join(_escape_one(line) for line in text.split("\n"))


# Inline, semantic, non-scripting tags the allow-list may ever contain (#154).
# Kept identical to the schema cap in apps/api/app/schemas/convert.py; a test
# asserts they match. Anything else (script/style/iframe/a/img/...) is never
# emittable, so an opt-in HTML policy can never become a script-injection hole.
ALLOWED_HTML_TAGS = frozenset({"sup", "sub", "small", "kbd", "abbr"})


def emit_html(tag: str, inner: str, allow_html: frozenset[str]) -> str:
    """Single sanctioned chokepoint for any raw HTML the converter might emit.

    Returns `<tag>inner</tag>` only when `tag` is both requested in `allow_html`
    AND inside the hard `ALLOWED_HTML_TAGS` cap. Otherwise it drops the tag,
    returns `inner` unchanged, and logs a warning.

    The converter emits pure Markdown by default (#141/#142), so there is no
    production caller yet (#154): this reserves the contract and the one place
    a future tag-with-no-Markdown-equivalent must route through. The cap is
    re-checked here so a direct script/CLI call cannot smuggle a tag past the
    API-layer validator.
    """
    if tag in allow_html and tag in ALLOWED_HTML_TAGS:
        return f"<{tag}>{inner}</{tag}>"
    log.warning("dropped disallowed HTML tag <%s> (not in allow_html)", tag)
    return inner


def normalize_ordered_marker(text: str, *, first: bool) -> tuple[str, str]:
    """Map a source list marker (`1.`, `a)`, `i.`, `7)`) to a canonical `1.`.

    CommonMark renumbers an ordered list from its first marker, so only the
    first item carries a non-1 start (preserved when the source marker is a
    digit); the rest emit `1.` and the renderer increments. Returns
    `(marker, content)`; when no marker is recognized, marker is `""` and the
    text is returned unchanged.
    """
    m = NUMBERED_RE.match(text)
    if not m:
        return "", text
    token = m.group(1)
    content = text[m.end():].strip()
    if first and token.isdigit():
        return f"{int(token)}.", content
    return "1.", content


HEADING_DOTS_RE = re.compile(r"\s*\.{3,}\s*\d+\s*$")  # "Title ........ 8" (TOC dot leaders)

# Code-block detection
MONO_FONT_HINTS = (
    "Mono", "Courier", "Consolas", "Menlo", "Inconsolata", "Hack",
    "JetBrains", "FiraCode", "SourceCode", "PlexMono", "RobotoMono",
)
MONO_RATIO_THRESHOLD = 0.7
SQL_RE = re.compile(r"\bSELECT\b.*?\bFROM\b", re.IGNORECASE | re.DOTALL)

# A paragraph that continues a list item is indented past the item's marker
# edge. CommonMark keeps such a paragraph inside the <li> when it aligns with
# the item content and sits on a blank line (spec 5.2). We treat a paragraph
# block indented at least this many points past the open item's marker x0 as a
# continuation of that item (#167). 6 pt sits below the smallest real content
# offset (a bullet glyph plus its trailing space) yet above bbox jitter.
LIST_CONTINUATION_MIN_INDENT = 6.0


@dataclass
class Span:
    text: str
    size: float
    font: str
    flags: int
    bbox: tuple[float, float, float, float] = (0.0, 0.0, 0.0, 0.0)
    link: str | None = None
    # Set from char_flags (see page_text_dict); not derivable from `flags`.
    is_strikethrough: bool = False
    # Set from a PDF text-highlight annotation covering this span (#162).
    is_highlight: bool = False

    @property
    def is_bold(self) -> bool:
        return bool(self.flags & FLAG_BOLD) or "Bold" in self.font

    @property
    def is_italic(self) -> bool:
        return bool(self.flags & FLAG_ITALIC) or "Italic" in self.font or "Oblique" in self.font

    @property
    def is_superscript(self) -> bool:
        return bool(self.flags & FLAG_SUPERSCRIPT)


@dataclass
class Line:
    spans: list[Span]
    bbox: tuple[float, float, float, float]

    @property
    def text(self) -> str:
        return "".join(s.text for s in self.spans)

    @property
    def dominant_size(self) -> float:
        # Size with the most characters in this line
        sizes: Counter[float] = Counter()
        for s in self.spans:
            sizes[round(s.size, 1)] += len(s.text)
        return sizes.most_common(1)[0][0] if sizes else 0.0


@dataclass
class Block:
    lines: list[Line]
    bbox: tuple[float, float, float, float]

    @property
    def text(self) -> str:
        return " ".join(line.text.strip() for line in self.lines if line.text.strip())

    @property
    def dominant_size(self) -> float:
        sizes: Counter[float] = Counter()
        for line in self.lines:
            for s in line.spans:
                sizes[round(s.size, 1)] += len(s.text)
        return sizes.most_common(1)[0][0] if sizes else 0.0


@dataclass
class DocProfile:
    body_size: float
    body_font: str  # dominant font at body size
    heading_thresholds: dict[int, float]  # level -> min size
    small_size: float  # captions/footnotes upper bound
    body_x0: float = 72.0  # typical paragraph left margin (PDF points)
    list_base_x0: float = 72.0  # typical first-level bullet/numbered left margin
    indent_unit: float = 18.0  # nesting indent step
    detect_blockquotes: bool = False  # opt-in: sustained-indent body block -> quote (#147)
    cluster_headings: bool = False  # opt-in: gap-partition font sizes into heading bands (#188)
    allow_html: frozenset = frozenset()  # opt-in HTML tags the emitter may keep (#154)
    preserve_line_breaks: bool = False  # opt-in: keep intentional layout line breaks (#156)
    footnote_pairing: bool = False  # opt-in: pair footer footnote blocks with body refs (#148)
    footnote_numbers: frozenset = frozenset()  # collected footnote numbers to rewrite as [^N] (#148)
    autolink_urls: bool = False  # opt-in: wrap bare http(s) URLs in body text as autolinks (#157)
    extract_highlights: bool = False  # opt-in: emit ==text== from PDF text-highlight annotations (#162)
    emit_figure_anchors: bool = False  # opt-in: emit {#fig-N .figure} on captioned figures (#165)
    figure_ids_used: set = field(default_factory=set)  # doc-level dedupe for fig-N ids (#165)
    autolink_emails: bool = False  # opt-in: wrap bare email addresses in body text as autolinks (#157)
    extract_abbreviations: bool = False  # opt-in: emit *[ABBR]: defs from a glossary section (#163)
    caption_alt_text: bool = False  # opt-in: use a caption line below an image as its alt text (#149)
    table_column_align: bool = False  # opt-in: detect cell alignment and emit GFM markers in separator row (#175)
    tight_loose_lists: bool = False  # opt-in: preserve list spacing as CommonMark tight/loose lists (#168)
    list_loose_threshold: float = 1.5
    size_histogram: dict = field(default_factory=dict)  # rounded size -> char count, for clustering

    def heading_level(self, size: float) -> int | None:
        # Iterate the actual threshold keys so a legacy {1,2,3} dict behaves
        # exactly as before and a clustered {1..6} dict (#146) reaches H4-H6.
        for level in sorted(self.heading_thresholds):
            if size >= self.heading_thresholds[level]:
                return level
        return None

    def nesting_level(self, x0: float) -> int:
        if self.indent_unit <= 0:
            return 0
        n = int(round(max(0.0, x0 - self.list_base_x0) / self.indent_unit))
        return min(max(n, 0), 5)


def cluster_heading_bands(
    size_histogram: dict[float, int], body_size: float, *, max_level: int = 3
) -> dict[int, float]:
    """Map font sizes above body to H1..H{max_level} thresholds by partitioning
    the distinct sizes at their largest gaps (#188, #146).

    Deterministic by construction: no RNG, no dependency. Sizes close together
    (a tiny gap) land in the same band instead of being split by a fixed
    cutoff, which is what fixes sibling heading sizes getting mislabeled. A
    band's threshold is the midpoint to the next band's ceiling, so the cut
    sits in the real empty space between size clusters. `max_level` caps how
    many bands (heading levels) the partition may produce; a flat histogram
    yields fewer levels naturally and they are never synthesized (#146).
    """
    candidates = sorted({s for s in size_histogram if s > body_size + 0.5}, reverse=True)
    if not candidates:
        # No heading-size text: keep the legacy fallback ladder (always 3).
        h1, h2, h3 = body_size + 6, body_size + 3, body_size + 1.5
        return {1: h1 - 0.5, 2: h2 - 0.5, 3: h3 - 0.5}

    # Partition the sorted-desc distinct sizes into at most `max_level` bands by
    # cutting at the most significant gaps. A gap counts as significant only if
    # it stands out from the largest gap, so close siblings never cut.
    bands: list[list[float]] = [candidates]
    if len(candidates) > 1:
        gaps = sorted(
            ((candidates[i] - candidates[i + 1], i) for i in range(len(candidates) - 1)),
            key=lambda g: (-g[0], g[1]),  # largest gap first; tie -> lower index (larger size)
        )
        significant = max(0.5, gaps[0][0] * 0.25)
        cut_after = sorted(i for gap, i in gaps[: max_level - 1] if gap >= significant)
        if cut_after:
            bands = []
            start = 0
            for ci in cut_after:
                bands.append(candidates[start:ci + 1])
                start = ci + 1
            bands.append(candidates[start:])

    unreachable = candidates[0] + 100.0
    thresholds: dict[int, float] = {}
    for level in range(1, max_level + 1):
        if level <= len(bands):
            floor = min(bands[level - 1])
            if level < len(bands):
                thresholds[level] = (floor + max(bands[level])) / 2
            else:
                thresholds[level] = floor - 0.5
        else:
            thresholds[level] = unreachable  # fewer bands than max_level: level never matches
    return thresholds


def build_profile(doc: fitz.Document) -> DocProfile:
    sizes: Counter[float] = Counter()
    fonts_at_body: Counter[str] = Counter()
    for page in doc:
        for block in page.get_text("dict").get("blocks", []):
            if block.get("type") != 0:
                continue
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    text = span["text"].strip()
                    if text:
                        sz = round(span["size"], 1)
                        sizes[sz] += len(text)

    if not sizes:
        return DocProfile(
            body_size=11.0, body_font="", heading_thresholds={1: 18.0, 2: 14.0, 3: 12.5}, small_size=9.5
        )

    body_size = sizes.most_common(1)[0][0]

    # Find the dominant font at body size (the actual body font, not stylistic mono labels)
    for page in doc:
        for block in page.get_text("dict").get("blocks", []):
            if block.get("type") != 0:
                continue
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    if round(span["size"], 1) == body_size and span["text"].strip():
                        fonts_at_body[span["font"]] += len(span["text"])
    body_font = fonts_at_body.most_common(1)[0][0] if fonts_at_body else ""

    larger = sorted({s for s in sizes if s > body_size + 0.5}, reverse=True)
    h1 = larger[0] if len(larger) >= 1 else body_size + 6
    h2 = larger[1] if len(larger) >= 2 else (h1 - 4 if h1 - 4 > body_size else body_size + 3)
    h3 = larger[2] if len(larger) >= 3 else (h2 - 2 if h2 - 2 > body_size else body_size + 1.5)

    # Estimate body left margin and the typical first-level list indent.
    paragraph_x0: Counter[int] = Counter()
    list_x0: Counter[int] = Counter()
    for page in doc:
        for raw_block in page.get_text("dict").get("blocks", []):
            if raw_block.get("type") != 0:
                continue
            lines = raw_block.get("lines", [])
            if not lines:
                continue
            spans0 = lines[0].get("spans", [])
            if not spans0:
                continue
            first_text = spans0[0].get("text", "").lstrip()
            avg_sz = sum(s["size"] for s in spans0) / len(spans0)
            if abs(avg_sz - body_size) >= 0.5:
                continue
            x0 = raw_block.get("bbox", [0, 0, 0, 0])[0]
            is_bullet = bool(first_text) and first_text[0] in BULLET_CHARS
            is_numbered = bool(NUMBERED_RE.match(first_text))
            if is_bullet or is_numbered:
                list_x0[int(round(x0))] += 1
            else:
                paragraph_x0[int(round(x0))] += 1
    body_x0 = float(paragraph_x0.most_common(1)[0][0]) if paragraph_x0 else 72.0
    list_base_x0 = float(list_x0.most_common(1)[0][0]) if list_x0 else body_x0

    return DocProfile(
        body_size=body_size,
        body_font=body_font,
        heading_thresholds={1: h1 - 0.5, 2: h2 - 0.5, 3: h3 - 0.5},
        small_size=body_size - 1.0,
        body_x0=body_x0,
        list_base_x0=list_base_x0,
        indent_unit=18.0,
        size_histogram=dict(sizes),
    )


def parse_block(raw_block: dict) -> Block | None:
    lines: list[Line] = []
    for raw_line in raw_block.get("lines", []):
        spans = []
        for raw_span in raw_line.get("spans", []):
            text = normalize_span_text(raw_span["text"])
            if not text:
                continue
            # char_flags carries the strikeout bit only when the page was read
            # with style collection; gate on _STYLE_FLAGS so a plain read (or an
            # older PyMuPDF) never reports a false strikethrough.
            struck = bool(_STYLE_FLAGS) and bool(
                raw_span.get("char_flags", 0) & CHAR_FLAG_STRIKEOUT
            )
            spans.append(
                Span(
                    text=text,
                    size=raw_span["size"],
                    font=raw_span["font"],
                    flags=raw_span["flags"],
                    bbox=tuple(raw_span.get("bbox", (0.0, 0.0, 0.0, 0.0))),
                    is_strikethrough=struck,
                )
            )
        if not spans:
            continue
        bbox = tuple(raw_line["bbox"])
        lines.append(Line(spans=spans, bbox=bbox))
    if not lines:
        return None
    bbox = tuple(raw_block["bbox"])
    return Block(lines=lines, bbox=bbox)


def annotate_spans_with_links(blocks: list[Block], page_links: list[dict]) -> None:
    """Attach link URIs to spans whose bbox falls inside a link's bbox."""
    if not page_links:
        return
    targets = []
    for link in page_links:
        rect = link.get("from")
        if rect is None:
            continue
        try:
            tx0, ty0, tx1, ty1 = float(rect[0]), float(rect[1]), float(rect[2]), float(rect[3])
        except (TypeError, ValueError, IndexError):
            continue
        uri = link.get("uri")
        if not uri:
            page_dest = link.get("page")
            try:
                page_idx = int(page_dest) if page_dest is not None else -1
            except (TypeError, ValueError):
                page_idx = -1
            if page_idx >= 0:
                uri = f"#page-{page_idx + 1}"
        if not uri:
            continue
        targets.append((tx0, ty0, tx1, ty1, uri))
    if not targets:
        return
    for block in blocks:
        for line in block.lines:
            for span in line.spans:
                sx0, sy0, sx1, sy1 = span.bbox
                scx = (sx0 + sx1) / 2
                scy = (sy0 + sy1) / 2
                for tx0, ty0, tx1, ty1, uri in targets:
                    if tx0 - 1 <= scx <= tx1 + 1 and ty0 - 1 <= scy <= ty1 + 1:
                        span.link = uri
                        break


# PyMuPDF's numeric type for a text-highlight annotation. getattr-gated so an
# older build without the constant degrades to "no highlights" deterministically.
_PDF_ANNOT_HIGHLIGHT = getattr(fitz, "PDF_ANNOT_HIGHLIGHT", 8)
# A span counts as highlighted only when a highlight quad covers at least this
# fraction of the span's WIDTH (the two share the line's vertical band, so width
# coverage, not area, is the meaningful signal: a span's glyph box is taller than
# the tight highlight quad, which would dilute an area ratio). A highlight over
# most of a span marks it; one grazing a few characters does not (#162).
# ponytail: coarse span granularity - a highlight over PART of a single extracted
# span marks the whole span (PyMuPDF does not split a span at an annotation
# boundary). Char-level splitting via rawdict is the upgrade path if sub-span
# fidelity is ever needed; whole-span marking preserves the user's highlight.
_HIGHLIGHT_MIN_OVERLAP = 0.5


def _highlight_rects(annot: fitz.Annot) -> list[tuple[float, float, float, float]]:
    """Rectangles a highlight annotation covers.

    A multi-line highlight stores one quad per line in `annot.vertices` (4 points
    each, PDF quadpoints); using those instead of the union `annot.rect` keeps a
    highlight that skips the short tail of a line from marking the blank gap. Fall
    back to `annot.rect` when quad geometry is unavailable.
    """
    rects: list[tuple[float, float, float, float]] = []
    try:
        verts = annot.vertices
    except Exception:
        verts = None
    if verts:
        for i in range(0, len(verts) - 3, 4):
            quad = verts[i:i + 4]
            xs = [float(p[0]) for p in quad]
            ys = [float(p[1]) for p in quad]
            rects.append((min(xs), min(ys), max(xs), max(ys)))
    if not rects:
        try:
            r = annot.rect
            rects.append((r.x0, r.y0, r.x1, r.y1))
        except Exception:
            # A malformed annotation with no usable rect contributes no highlight
            # geometry; skip it rather than fail the page (degrade deterministically).
            pass
    return rects


def _highlight_width_coverage(
    span_bbox: tuple[float, float, float, float],
    rect: tuple[float, float, float, float],
) -> float:
    """Fraction of the span's width a highlight rect covers, or 0 if they do not
    share the line's vertical band. Width, not area: the two overlap on one line,
    so horizontal coverage is what says whether the text was highlighted."""
    sx0, sy0, sx1, sy1 = span_bbox
    rx0, ry0, rx1, ry1 = rect
    if min(sy1, ry1) - max(sy0, ry0) <= 0:
        return 0.0  # different lines
    span_w = sx1 - sx0
    if span_w <= 0:
        return 0.0
    xcov = min(sx1, rx1) - max(sx0, rx0)
    return xcov / span_w if xcov > 0 else 0.0


def annotate_spans_with_highlights(blocks: list[Block], page: fitz.Page) -> None:
    """Flag spans covered by a PDF text-highlight annotation (#162).

    A highlight carries geometry and a colour, never the text itself: the marked
    words are whatever glyphs sit under its quads. We collect every highlight
    quad on the page, then mark a span when at least half its width falls inside
    one, so `render_span` wraps it in `==...==`. Robust to older PyMuPDF builds
    and malformed annotations: any failure degrades to leaving spans unmarked.

    Table cells are out of scope here: `convert_page` removes table-contained
    blocks before this runs and `render_table` renders cells straight from the
    table extractor, so a highlight inside a table cell is not yet emitted (#413).
    """
    try:
        annots = page.annots()
    except Exception:
        return
    if annots is None:
        return
    rects: list[tuple[float, float, float, float]] = []
    for annot in annots:
        try:
            is_highlight = annot.type[0] == _PDF_ANNOT_HIGHLIGHT
        except Exception:
            continue
        if is_highlight:
            rects.extend(_highlight_rects(annot))
    if not rects:
        return
    for block in blocks:
        for line in block.lines:
            for span in line.spans:
                if any(_highlight_width_coverage(span.bbox, r) >= _HIGHLIGHT_MIN_OVERLAP for r in rects):
                    span.is_highlight = True


def horizontal_strokes(page: fitz.Page) -> list[tuple[float, float, float]]:
    """Return (y, x0, x1) for each near-horizontal rule drawn on the page.

    Covers both shapes a PDF uses for a rule or a strike: a line item (`"l"`)
    and a thin filled rectangle (`"re"`, e.g. a divider drawn as a 1-3 pt tall
    box). A tall rectangle is a fill/box, not a rule, so only thin ones count.
    """
    strokes: list[tuple[float, float, float]] = []
    try:
        drawings = page.get_drawings()
    except Exception:
        return strokes
    for drawing in drawings:
        for item in drawing.get("items", []):
            if not item:
                continue
            if item[0] == "l":
                p1, p2 = item[1], item[2]
                if abs(p1.y - p2.y) <= 1.5:
                    strokes.append(((p1.y + p2.y) / 2, min(p1.x, p2.x), max(p1.x, p2.x)))
            elif item[0] == "re":
                rect = item[1]
                if abs(rect.y1 - rect.y0) <= 3.0:
                    strokes.append(((rect.y0 + rect.y1) / 2, rect.x0, rect.x1))
    return strokes


def strikethrough_confirmed(
    span_bbox: tuple[float, float, float, float],
    strokes: list[tuple[float, float, float]],
) -> bool:
    """Whether a strikeout char_flag is backed by a real strike line (#202).

    True when a horizontal stroke crosses the span's vertical band and stays
    within the span x-range (a genuine strike), or when no stroke geometry is
    available (trust the flag). False when the only strokes crossing the span
    overrun it toward the margins — a page rule misread as a strike.
    """
    sx0, sy0, sx1, sy1 = span_bbox
    crossing = [
        (x0, x1)
        for (y, x0, x1) in strokes
        if sy0 - 2 <= y <= sy1 + 2 and x0 <= sx1 and x1 >= sx0
    ]
    if not crossing:
        return True
    tol = STRIKETHROUGH_OVERRUN_TOL
    return any(x0 >= sx0 - tol and x1 <= sx1 + tol for (x0, x1) in crossing)


def drop_rule_strikethroughs(blocks: list[Block], page: fitz.Page) -> None:
    """Clear is_strikethrough on spans crossed only by an overrunning page rule.

    Runs the geometry cross-check (#202) lazily: pages with no struck spans —
    the overwhelming majority — pay nothing, since `get_drawings` is only called
    when at least one span carries the strikeout flag.
    """
    struck = [s for b in blocks for line in b.lines for s in line.spans if s.is_strikethrough]
    if not struck:
        return
    strokes = horizontal_strokes(page)
    for span in struck:
        if not strikethrough_confirmed(span.bbox, strokes):
            span.is_strikethrough = False


def render_span(
    span: Span,
    footnote_numbers: frozenset[int] = frozenset(),
    *,
    autolink_urls: bool = False,
    autolink_emails: bool = False,
) -> str:
    text = span.text
    if not text.strip():
        return text
    # Skip wrapping for bullet glyphs themselves
    if text.strip() in BULLET_CHARS:
        return text
    out = text
    bold = span.is_bold
    italic = span.is_italic
    sup = span.is_superscript
    mono = is_mono_span(span)
    leading = len(out) - len(out.lstrip())
    trailing = len(out) - len(out.rstrip())
    core = out[leading: len(out) - trailing] if trailing else out[leading:]
    # A superscript that is a bare number matching a collected footnote becomes
    # a GFM footnote reference (#148): a leaf token, no emphasis/link wrapping.
    # An empty set (the flag-off default) leaves the `^N^` path below untouched.
    if sup and footnote_numbers and core.strip().isdigit() and int(core.strip()) in footnote_numbers:
        ref = f"[^{int(core.strip())}]"
        return out[:leading] + ref + (out[len(out) - trailing:] if trailing else "")
    if core:
        if mono and "`" not in core:
            # Code spans render their content literally, so do not escape inside
            # the backticks. Every other case is literal prose that must be
            # escaped before we add our own emphasis/link markers.
            core = f"`{core}`"
        elif span.link:
            # A pre-annotated link wraps the whole core as [core](link) below;
            # autolinking inside it would double-wrap the URL. Escape only.
            core = escape_markdown_inline(core)
        else:
            core = _autolink_escape(core, urls=autolink_urls, emails=autolink_emails)
        if sup:
            # Pandoc/pymdownx superscript (`^x^`) instead of raw <sup>, to keep
            # output pure Markdown (#141). A caret-unaware renderer shows the
            # carets literally, which is acceptable; `^` is inert punctuation in
            # the shipped renderer, so we do not escape literal prose carets.
            core = f"^{core}^"
        if bold and italic:
            core = f"***{core}***"
        elif bold:
            core = f"**{core}**"
        elif italic:
            core = f"*{core}*"
        # GFM strikethrough wraps the emphasis, giving the canonical nested
        # order `~~**text**~~` so output is stable across runs (#142).
        if span.is_strikethrough:
            core = f"~~{core}~~"
        # Highlight wraps the strikethrough/emphasis stack, so the nested order is
        # stable as `==~~**text**~~==` and the pymdownx-mark syntax stays outermost
        # of the inline markers, just inside a link (#162). `==` is the delimiter,
        # so a core that itself contains `==` (the equality operator in `x == y`,
        # or a code span holding one) would break the pair - the renderer's
        # non-greedy match closes at the inner `==`. There is no backslash escape
        # for `=` in the shipped renderer, so leave such a span unmarked rather
        # than emit corrupt markdown (Codex #411).
        if span.is_highlight and "==" not in core:
            core = f"=={core}=="
        if span.link:
            core = f"[{core}]({span.link})"
    return out[:leading] + core + (out[len(out) - trailing:] if trailing else "")


def render_line(
    line: Line,
    footnote_numbers: frozenset[int] = frozenset(),
    *,
    autolink_urls: bool = False,
    autolink_emails: bool = False,
) -> str:
    # Merge adjacent spans with same style to avoid `**a****b**` artifacts
    merged: list[Span] = []
    for s in line.spans:
        if (
            merged
            and merged[-1].is_bold == s.is_bold
            and merged[-1].is_italic == s.is_italic
            and merged[-1].is_strikethrough == s.is_strikethrough
            # Keep a highlighted span separate from an unhighlighted neighbour, or
            # one `==...==` would swallow the unmarked text (mirrors strike, #162).
            and merged[-1].is_highlight == s.is_highlight
            # Under footnote pairing, keep a superscript span separate so a
            # footnote digit is rewritten on its own rather than fused into
            # adjacent body text (#148). With the flag off (empty set) the
            # equality is skipped, so the default merge stays byte-identical.
            and (not footnote_numbers or merged[-1].is_superscript == s.is_superscript)
            and is_mono_span(merged[-1]) == is_mono_span(s)
        ):
            merged[-1] = Span(
                text=merged[-1].text + s.text,
                size=merged[-1].size,
                font=merged[-1].font,
                flags=merged[-1].flags,
                is_strikethrough=merged[-1].is_strikethrough,
                is_highlight=merged[-1].is_highlight,
            )
        else:
            merged.append(s)
    return "".join(
        render_span(s, footnote_numbers, autolink_urls=autolink_urls, autolink_emails=autolink_emails)
        for s in merged
    )


def dominant_font(block: Block) -> str:
    fonts: Counter[str] = Counter()
    for line in block.lines:
        for s in line.spans:
            fonts[s.font] += len(s.text)
    return fonts.most_common(1)[0][0] if fonts else ""


def is_mono_span(span: Span) -> bool:
    # GlyphLessFont is PyMuPDF's internal placeholder for glyphs unavailable in
    # the embedded font. It carries FLAG_MONO but is not real monospace content;
    # treating it as mono would misclassify any prose paragraph whose font can't
    # be resolved on the host (e.g. unembedded Helvetica on a minimal Linux CI).
    # Note: "GlyphLessFont" is a mupdf implementation detail, not a public API;
    # see pymupdf source (fitz/__init__.py) and mupdf glyph substitution code.
    if span.font == "GlyphLessFont":
        return False
    if span.flags & FLAG_MONO:
        return True
    return any(hint in span.font for hint in MONO_FONT_HINTS)


def mono_ratio(block: Block) -> float:
    mono_chars = 0
    total_chars = 0
    for line in block.lines:
        for s in line.spans:
            stripped = len(s.text.strip())
            if not stripped:
                continue
            total_chars += stripped
            if is_mono_span(s):
                mono_chars += stripped
    if total_chars == 0:
        return 0.0
    return mono_chars / total_chars


def detect_language(text: str) -> str:
    """Best-effort language hint for a fenced code block.

    Conservative: returns '' when no rule matches so the fence is languageless
    rather than mislabelled.
    """
    if not text:
        return ""
    head = text.lstrip()
    if head.startswith(("<!DOCTYPE", "<html")):
        return "html"
    if head.startswith("{") and '":' in head:
        return "json"
    if SQL_RE.search(text):
        return "sql"
    if re.search(r"^\s*(def |class |import |from \S+ import )", text, re.MULTILINE):
        return "python"
    # The rules below stay conservative: each keys off a high-signal, line-
    # anchored construct (a shebang, a declaration keyword, a document marker),
    # never a bare word that also reads as prose, so a misdetect mislabels at
    # most one fence rather than firing on ordinary text (#145). Language-
    # specific declarations are checked before the looser JavaScript rule so a
    # Rust `let mut` or a Go `func` is not stolen by JavaScript's `let`/`func`.
    # Bash: a shebang or a visible shell prompt. Bare builtins (cd, rm, echo)
    # are deliberately not matched.
    if re.search(r"^#!\s*(?:/usr/bin/env\s+|/bin/)?(?:bash|sh|zsh)\b", text, re.MULTILINE):
        return "bash"
    if re.search(r"^\s*\$\s+[a-zA-Z]", text, re.MULTILINE):
        return "bash"
    # Dockerfile: the defining FROM plus at least one more instruction.
    if re.search(r"^\s*FROM\s+\S+", text, re.MULTILINE) and re.search(
        r"^\s*(RUN|CMD|COPY|ADD|ENTRYPOINT|WORKDIR|ENV|EXPOSE|VOLUME)\s", text, re.MULTILINE
    ):
        return "dockerfile"
    # Go: a package line or a func definition. (An `import (` block is not used
    # as a signal: Python's `import ` rule above already claims that line.)
    if re.search(r"^\s*package\s+\w+\s*$|^\s*func\s+\w+\s*\(", text, re.MULTILINE):
        return "go"
    # Rust: declaration keywords at line start (fn/impl/struct/enum/let mut/use path).
    if re.search(
        r"^\s*(pub\s+)?(fn\s+\w+|impl\s+\w|struct\s+\w+|enum\s+\w+|let\s+mut\s|use\s+\w+::)",
        text,
        re.MULTILINE,
    ):
        return "rust"
    # TypeScript: an interface body or a type alias (the brace / `=` keeps the
    # keyword from matching prose like "interface with the system").
    if re.search(r"^\s*interface\s+\w+\s*\{|^\s*type\s+\w+\s*=", text, re.MULTILINE):
        return "typescript"
    if re.search(r"^\s*(function\s|const\s|let\s|var\s|=>\s)", text, re.MULTILINE):
        return "javascript"
    # YAML: a document marker, or two or more `key: value` lines. Checked after
    # the typed languages so an interface body's `name: type` lines do not read
    # as YAML.
    if re.search(r"^---\s*$", text, re.MULTILINE) or len(
        re.findall(r"^[\w.-]+:\s+\S", text, re.MULTILINE)
    ) >= 2:
        return "yaml"
    return ""


def is_all_bold(block: Block) -> bool:
    has_any = False
    for line in block.lines:
        for s in line.spans:
            if s.text.strip():
                has_any = True
                if not s.is_bold:
                    return False
    return has_any


def is_blockquote(block: Block, profile: DocProfile) -> bool:
    """A pull-quote candidate: body-size text indented past the deeper of the
    body and list margins on EVERY non-empty line (sustained indent).

    The sustained-indent rule is deliberate. A normal paragraph indents only
    its first line, and a list continuation indents under the item marker; both
    are excluded here so the only thing left is a block that sits wholly inset
    from the margin, which is how PDFs render quoted passages (#147).
    """
    size = block.dominant_size
    if size < profile.body_size - 0.5:
        return False  # captions / footnotes are not quotes
    if profile.heading_level(size):
        return False
    lines = [ln for ln in block.lines if ln.text.strip()]
    if not lines:
        return False
    threshold = max(profile.body_x0, profile.list_base_x0) + profile.indent_unit
    return all(ln.bbox[0] >= threshold for ln in lines)


def classify_block(block: Block, profile: DocProfile) -> str:
    """Return one of: heading1, heading2, heading3, bullet, numbered, code, blockquote, paragraph, small."""
    size = block.dominant_size
    text = block.text.strip()

    if not text:
        return "empty"

    first_line_raw = block.lines[0].text.lstrip()
    if first_line_raw and first_line_raw[0] in BULLET_CHARS:
        return "bullet"

    if NUMBERED_RE.match(first_line_raw):
        return "numbered"

    level = profile.heading_level(size)
    if level:
        return f"heading{level}"

    if mono_ratio(block) >= MONO_RATIO_THRESHOLD:
        return "code"

    # Pull-quote: a body-size block inset from the margin on every line. Off by
    # default (#147); list continuations (#167/#197) are also indented body
    # blocks, so precedence is resolved in assemble_markdown where the open-list
    # context is known. Here we only label the candidate.
    if profile.detect_blockquotes and is_blockquote(block, profile):
        return "blockquote"

    # Section-label heuristic: short block (<= 2 lines, <= 80 chars), at body size,
    # using a font different from the body font → likely a styled section label (H3).
    if (
        size == profile.body_size
        and profile.body_font
        and dominant_font(block) != profile.body_font
        and len(block.lines) <= 2
        and len(text) <= 80
        and not text.endswith((".", ":", "?", "!"))
    ):
        return "heading3"

    # Bold-only short standalone line → subheading
    if (
        is_all_bold(block)
        and len(block.lines) == 1
        and len(text) <= 60
        and not text.endswith((".", "?", "!"))
    ):
        return "heading3"

    if size <= profile.small_size:
        return "small"

    return "paragraph"


_TABLE_ALIGN_CELL_TOLERANCE = 1.0
_TABLE_ALIGN_EDGE_RATIO = 0.20
_TABLE_ALIGN_CENTER_RATIO = 0.08
_TABLE_ALIGN_MIN_VOTES = 2


def _table_cells_by_column(table, column_count: int) -> list[list[tuple[float, float, float, float]]]:
    """Return non-spanning table-cell bounds grouped by extracted column.

    ``Table.cells`` is a flat, geometry-only view. ``Table.rows`` retains the
    extracted column index, which lets alignment survive PyMuPDF's occasional
    empty-column and duplicate-column artifacts. A cell that reaches into the
    following column is deliberately ignored: its content cannot safely tell
    us how either logical column is aligned.
    """
    by_column: list[list[tuple[float, float, float, float]]] = [[] for _ in range(column_count)]
    try:
        rows = list(table.rows)
    except Exception:
        return by_column

    column_lefts: list[float | None] = []
    for column_index in range(column_count):
        lefts: list[float] = []
        for row in rows:
            try:
                cell = row.cells[column_index]
            except (AttributeError, IndexError, TypeError):
                continue
            if cell is not None:
                lefts.append(float(cell[0]))
        column_lefts.append(sorted(lefts)[len(lefts) // 2] if lefts else None)

    for row in rows:
        for column_index in range(column_count):
            try:
                cell = row.cells[column_index]
            except (AttributeError, IndexError, TypeError):
                continue
            if cell is None:
                continue
            try:
                x0, y0, x1, y1 = (float(value) for value in cell)
            except (TypeError, ValueError):
                continue
            if x1 <= x0 or y1 <= y0:
                continue
            next_left = next((left for left in column_lefts[column_index + 1 :] if left is not None), None)
            if next_left is not None and x1 > next_left + _TABLE_ALIGN_CELL_TOLERANCE:
                continue  # horizontal spanning cell: no reliable logical-column alignment
            by_column[column_index].append((x0, y0, x1, y1))
    return by_column


def _span_alignment(span_bbox: tuple[float, float, float, float], cell_bbox: tuple[float, float, float, float]) -> str:
    """Return a conservative GFM alignment vote for one span inside one cell."""
    sx0, _, sx1, _ = span_bbox
    x0, _, x1, _ = cell_bbox
    cell_width = x1 - x0
    text_width = sx1 - sx0
    if cell_width <= 0 or text_width <= 0 or text_width > cell_width:
        return ""

    left_gap = sx0 - x0
    right_gap = x1 - sx1
    if left_gap < 0 or right_gap < 0:
        return ""
    delta = right_gap - left_gap
    edge_threshold = max(4.0, cell_width * _TABLE_ALIGN_EDGE_RATIO)
    center_threshold = max(3.0, cell_width * _TABLE_ALIGN_CENTER_RATIO)

    # A short span with similarly sized side gaps is genuinely centered. Long
    # prose often fills a left-aligned cell and can look centered by accident.
    if (
        abs(delta) <= center_threshold
        and min(left_gap, right_gap) >= cell_width * _TABLE_ALIGN_EDGE_RATIO
        and text_width <= cell_width * 0.70
    ):
        return "c"
    if delta >= edge_threshold and left_gap <= cell_width * 0.25:
        return "l"
    if -delta >= edge_threshold and right_gap <= cell_width * 0.25:
        return "r"
    return ""


def detect_column_alignment(table, page_text: dict, column_count: int) -> list[str]:
    """Detect alignment votes for the extracted table columns.

    Spans must sit entirely inside an individual non-spanning cell. The helper
    returns empty entries when the page lacks enough unambiguous evidence, so
    callers retain a plain GFM separator instead of guessing.
    """
    if column_count <= 0:
        return []
    cells_by_column = _table_cells_by_column(table, column_count)
    votes: list[list[str]] = [[] for _ in range(column_count)]

    for block in page_text.get("blocks", []):
        if block.get("type") != 0:
            continue
        for line in block.get("lines", []):
            spans_by_cell: dict[tuple[int, tuple[float, float, float, float]], list[tuple[float, float, float, float]]] = {}
            for span in line.get("spans", []):
                bbox = span.get("bbox")
                if not isinstance(bbox, (list, tuple)) or len(bbox) != 4:
                    continue
                try:
                    sx0, sy0, sx1, sy1 = (float(value) for value in bbox)
                except (TypeError, ValueError):
                    continue
                center_x = (sx0 + sx1) / 2
                center_y = (sy0 + sy1) / 2
                for column_index, cells in enumerate(cells_by_column):
                    match = next(
                        (
                            cell
                            for cell in cells
                            if (
                                cell[0] - _TABLE_ALIGN_CELL_TOLERANCE <= center_x <= cell[2] + _TABLE_ALIGN_CELL_TOLERANCE
                                and cell[1] - _TABLE_ALIGN_CELL_TOLERANCE <= center_y <= cell[3] + _TABLE_ALIGN_CELL_TOLERANCE
                            )
                        ),
                        None,
                    )
                    if match is None:
                        continue
                    spans_by_cell.setdefault((column_index, match), []).append((sx0, sy0, sx1, sy1))
                    break
            for (column_index, cell), matching_spans in spans_by_cell.items():
                extent = (
                    min(span[0] for span in matching_spans),
                    min(span[1] for span in matching_spans),
                    max(span[2] for span in matching_spans),
                    max(span[3] for span in matching_spans),
                )
                vote = _span_alignment(extent, cell)
                if vote:
                    votes[column_index].append(vote)

    alignment: list[str] = []
    for column_votes in votes:
        if len(column_votes) < _TABLE_ALIGN_MIN_VOTES:
            alignment.append("")
            continue
        counts: Counter[str] = Counter(column_votes)
        winner, winner_count = counts.most_common(1)[0]
        if winner_count == len(column_votes) or winner_count > len(column_votes) / 2:
            alignment.append(winner)
        else:
            alignment.append("")
    return alignment


def _merge_column_alignment(current: str, incoming: str) -> str:
    """Keep an alignment hint only when duplicate extracted columns agree."""
    if current and incoming and current == incoming:
        return current
    return ""


def _render_table_separators(alignment: list[str], column_count: int) -> str:
    """Render GFM separator markers, falling back to plain separators."""
    marker = {"l": ":---", "c": ":---:", "r": "---:"}
    return "| " + " | ".join(marker.get(alignment[i], "---") for i in range(column_count)) + " |"


def render_table(table, profile: DocProfile | None = None, page_text: dict | None = None) -> str:
    """Render a PyMuPDF Table to a Markdown table.

    Drops columns that are empty across all rows, merges duplicate adjacent
    columns (PyMuPDF sometimes splits a single header cell into two), and
    merges rows that look like wrapped continuations of the previous row.
    """
    try:
        rows = table.extract()
    except Exception:
        return ""
    if not rows:
        return ""

    rows = [[normalize_span_text((c or "").replace("\n", " ")).strip() for c in row] for row in rows]
    width = max(len(r) for r in rows)
    rows = [r + [""] * (width - len(r)) for r in rows]
    raw_alignment = (
        detect_column_alignment(table, page_text, width)
        if profile is not None and profile.table_column_align and page_text is not None
        else [""] * width
    )

    # Drop columns that are entirely empty
    keep_cols = [i for i in range(width) if any(r[i] for r in rows)]
    if not keep_cols:
        return ""
    rows = [[r[i] for i in keep_cols] for r in rows]
    width = len(keep_cols)
    alignment = [raw_alignment[i] for i in keep_cols]

    # Merge duplicate adjacent columns: when two adjacent columns hold the same
    # value in every row (or one is always blank when the other isn't), collapse them.
    merged_cols: list[list[str]] = [[r[0] for r in rows]]
    merged_alignment: list[str] = [alignment[0]]
    for ci in range(1, width):
        col = [r[ci] for r in rows]
        prev = merged_cols[-1]
        # collapse if identical or one side always empty/duplicate
        identical_or_subset = all(
            (a == b) or (not a) or (not b)
            for a, b in zip(prev, col, strict=False)
        )
        if identical_or_subset and any(a == b and a for a, b in zip(prev, col, strict=False)):
            merged_cols[-1] = [a or b for a, b in zip(prev, col, strict=False)]
            merged_alignment[-1] = _merge_column_alignment(merged_alignment[-1], alignment[ci])
        else:
            merged_cols.append(col)
            merged_alignment.append(alignment[ci])
    rows = [list(t) for t in zip(*merged_cols, strict=False)]
    if not rows:
        return ""

    # Merge rows where the first cell is empty (wrapped continuation of prior row)
    cleaned: list[list[str]] = []
    for r in rows:
        if cleaned and not r[0] and any(r):
            for i, cell in enumerate(r):
                if cell:
                    cleaned[-1][i] = (cleaned[-1][i] + " " + cell).strip()
        else:
            cleaned.append(list(r))
    rows = cleaned

    header = rows[0]
    body = rows[1:] if len(rows) > 1 else []

    def esc(cell: str) -> str:
        return cell.replace("|", "\\|")

    out = ["| " + " | ".join(esc(c) for c in header) + " |"]
    out.append(_render_table_separators(merged_alignment, len(header)))
    for row in body:
        out.append("| " + " | ".join(esc(c) for c in row) + " |")
    return "\n".join(out)


def block_in_any_bbox(block_bbox: tuple, table_bboxes: list[tuple]) -> bool:
    bx0, by0, bx1, by1 = block_bbox
    bcx = (bx0 + bx1) / 2
    bcy = (by0 + by1) / 2
    for tx0, ty0, tx1, ty1 in table_bboxes:
        if tx0 <= bcx <= tx1 and ty0 <= bcy <= ty1:
            return True
    return False


def is_header_footer(bbox: tuple, page_height: float, page_width: float) -> bool:
    """Heuristic: top 4% or bottom 4% of page is header/footer."""
    _, y0, _, y1 = bbox
    return y1 < page_height * 0.05 or y0 > page_height * 0.96


# Recurrent header/footer subtraction (#187). Opt-in, additive: the blunt
# is_header_footer strip above stays the default; this removes furniture that
# leaks OUTSIDE the narrow blunt band (e.g. a running "Page N of M" footer that
# sits above the bottom 4%) by detecting text that recurs across pages.
FURNITURE_BAND_RATIO = 0.10  # top/bottom band scanned for running furniture
# 10%, not the issue's "~7%": real footers (e.g. the ISTQB syllabus) sit around
# 9% of page height. The band only feeds the recurrence filter, and a one-off
# line in it is always kept, so a generous band is safe: only lines that recur
# across pages are subtracted.
FURNITURE_RECURRENCE = 0.60  # a line is furniture if it recurs on >= 60% of pages
FURNITURE_MIN_PAGES = 3  # never subtract on docs shorter than this (no cover-title nuke)


def normalize_furniture(text: str) -> str:
    """Normalize a band line for cross-page matching: lowercase, collapse
    whitespace, mask digit runs so "Page 3 of 77" and "Page 4 of 77" both
    become "page # of #" and count as the same recurring line.
    """
    s = re.sub(r"\s+", " ", text.strip().lower())
    return re.sub(r"\d+", "#", s)


def in_furniture_band(bbox: tuple, page_height: float) -> bool:
    _, y0, _, y1 = bbox
    return y1 <= page_height * FURNITURE_BAND_RATIO or y0 >= page_height * (1 - FURNITURE_BAND_RATIO)


def select_recurring(page_line_sets: list[set[str]], page_count: int) -> frozenset[str]:
    """Given the set of normalized band lines per page, return the lines that
    recur on enough pages to be furniture. Deterministic (Counter + frozenset,
    membership-tested downstream). Short docs subtract nothing.
    """
    if page_count < FURNITURE_MIN_PAGES:
        return frozenset()
    counts: Counter[str] = Counter()
    for page_set in page_line_sets:
        counts.update(page_set)
    threshold = max(FURNITURE_MIN_PAGES, ceil(page_count * FURNITURE_RECURRENCE))
    return frozenset(text for text, count in counts.items() if count >= threshold)


def find_recurring_furniture(doc: fitz.Document) -> frozenset[str]:
    """Scan the top/bottom band of every page, collect the normalized lines,
    and return the ones that recur often enough to be running headers/footers.
    A line that appears on only one page (a cover title, a one-off note in the
    band) never qualifies, so it survives conversion.
    """
    page_line_sets: list[set[str]] = []
    for page in doc:
        page_height = page.rect.height
        band: set[str] = set()
        for block in page.get_text("dict").get("blocks", []):
            if block.get("type") != 0:
                continue
            for line in block.get("lines", []):
                lbbox = line.get("bbox")
                if not lbbox or not in_furniture_band(lbbox, page_height):
                    continue
                norm = normalize_furniture("".join(s.get("text", "") for s in line.get("spans", [])))
                if norm:
                    band.add(norm)
        page_line_sets.append(band)
    return select_recurring(page_line_sets, doc.page_count)


# Footnote pairing (#148). A definition block sits in the bottom band at small
# font and opens with the number followed by prose.
FOOTNOTE_DEF_RE = re.compile(r"^\s*(\d{1,3})[.)]?\s+(\S.*)$", re.DOTALL)
FOOTNOTE_MIN_DEF_CHARS = 12
FOOTNOTE_BAND_RATIO = 0.80


def parse_footnote_definition(
    block: Block, profile: DocProfile, page_height: float
) -> tuple[int, str] | None:
    """A small-font block in the bottom band opening with `N <prose>` is a
    footnote definition; returns (number, text), else None. The geometry +
    small-font gates exclude body-size numbered-list items, and the prose-length
    and page-furniture guards exclude bare page numbers like "Page 3" (#148).

    Known limitation: a numbered-list item that is itself small-font AND lands in
    the bottom band is indistinguishable from a footnote by these gates and is
    treated as one. The geometry gate is the sole list/footnote discriminator, so
    a small-font ordered list at the foot of a page misfires. This is the reason
    the whole feature is opt-in; the common case (body-size lists, body-size
    bottom content) is unaffected because the small-font gate rejects it."""
    if block.bbox[1] <= page_height * FOOTNOTE_BAND_RATIO:
        return None
    if block.dominant_size > profile.small_size:
        return None
    text = block.text.strip()
    if looks_like_page_furniture(text):
        return None
    m = FOOTNOTE_DEF_RE.match(text)
    if not m:
        return None
    body = m.group(2).strip()
    if len(body) < FOOTNOTE_MIN_DEF_CHARS:
        return None
    return int(m.group(1)), body


def collect_footnote_definitions(doc: fitz.Document, profile: DocProfile) -> dict[int, str]:
    """One pass over the document gathering footnote definitions from bottom-band
    small-font blocks; the first definition of a number wins (#148)."""
    definitions: dict[int, str] = {}
    for page in doc:
        page_height = page.rect.height
        for raw_block in page.get_text("dict").get("blocks", []):
            if raw_block.get("type") != 0:
                continue
            block = parse_block(raw_block)
            if block is None:
                continue
            parsed = parse_footnote_definition(block, profile, page_height)
            if parsed is None:
                continue
            n, body = parsed
            if n in definitions:
                log.warning("footnote %d defined more than once; keeping the first", n)
                continue
            definitions[n] = body
    return definitions


def render_footnote_tail(definitions: dict[int, str]) -> str:
    """Document-tail block of `[^N]: text` for every collected definition,
    sorted ascending for determinism (#148). A definition whose body superscript
    was not detected still emits here as an (unreferenced) GFM footnote, which
    is valid Markdown and avoids dropping the footnote text."""
    return "\n".join(f"[^{n}]: {definitions[n]}" for n in sorted(definitions))


# Abbreviation glossary extraction (#163). Technical PDFs carry a "List of
# Abbreviations / Acronyms / Siglas / Abreviaturas" page laid out as two
# columns: a short token on the left, its expansion on the right, sharing a
# baseline. A pre-scan finds that section by its locale-aware heading and
# clusters the two columns into `*[ABBR]: expansion` lines, which the
# markdown-to-pdf renderer's `abbr` extension expands wherever the token
# appears later. Off by default so output stays byte-identical; the raw
# glossary is left in the body untouched, so the feature is purely additive.
#
# Folded (accent-stripped, lowercased) headings that introduce a glossary. A
# bare "Glossary"/"Definitions" heading is deliberately absent: those are prose
# definition lists, not two-column abbreviation tables, and an ISO-style
# numbered "3 Terms, definitions and abbreviations" clause never folds to an
# exact term either, so neither triggers detection.
_ABBR_HEADING_TERMS = frozenset(
    {
        # English
        "abbreviations",
        "acronyms",
        "abbreviations and acronyms",
        "list of abbreviations",
        "list of acronyms",
        "list of abbreviations and acronyms",
        # Portuguese
        "abreviaturas",
        "siglas",
        "abreviacoes",
        "abreviaturas e siglas",
        "siglas e abreviaturas",
        "lista de abreviaturas",
        "lista de siglas",
        "lista de abreviacoes",
        "lista de abreviaturas e siglas",
        "lista de siglas e abreviaturas",
        "lista de siglas e acronimos",
        "lista de abreviaturas e acronimos",
        # Spanish
        "acronimos",
        "abreviaciones",
        "siglas y acronimos",
        "lista de acronimos",
        "lista de abreviaciones",
        "lista de siglas y acronimos",
    }
)
_ABBR_MAX_TOKEN_LEN = 10  # longest left-column token treated as an abbreviation
_ABBR_MIN_PAIRS = 2  # a lone row is detection noise; require a real table
_ABBR_COL_GAP_MIN = 24.0  # min x-gap (pt) between the two columns
_ABBR_COL_TOL = 6.0  # x tolerance (pt) when pinning a row to the modal column
_ABBR_MAX_PAGES = 6  # a glossary rarely spans more pages; bounds the scan
_ABBR_INLINE_MIN_DENSITY = 0.5  # inline pages must be mostly entries, not prose


def _fold_heading(text: str) -> str:
    """Lowercase, strip accents (NFKD drop combining), collapse whitespace."""
    folded = unicodedata.normalize("NFKD", text)
    ascii_text = "".join(c for c in folded if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", ascii_text).strip().lower()


def _looks_like_abbreviation(token: str) -> bool:
    """A single whitespace-free token, <= max length, mostly uppercase.

    The whitespace and length gates reject a prose line that lands in the left
    column (e.g. a paragraph after the table, or a TOC entry title); the
    uppercase ratio rejects an ordinary lowercase word."""
    if not token or " " in token or len(token) > _ABBR_MAX_TOKEN_LEN:
        return False
    letters = [c for c in token if c.isalpha()]
    if len(letters) < 2:
        return False
    upper = sum(1 for c in letters if c.isupper())
    return upper / len(letters) >= 0.6


def _pair_two_columns(cells: list[tuple[float, float, str]]) -> dict[str, str]:
    """Split same-section lines into two columns and pair them by baseline.

    `cells` is `(x0, y, text)` per line. The columns are separated at the widest
    horizontal gap (>= _ABBR_COL_GAP_MIN); each side must hold at least
    _ABBR_MIN_PAIRS lines. Rows are pinned to the modal column x (within
    _ABBR_COL_TOL) so a stray wide line does not pair, then grouped by rounded
    baseline into (token, expansion). First token wins on a collision."""
    if len(cells) < 2 * _ABBR_MIN_PAIRS:
        return {}
    # Column anchors are the two most populated x positions, not the widest gap:
    # a glossary's token and expansion columns each repeat on every row, whereas
    # page furniture (a lone right-aligned page number, a running header) forms
    # no populous column. Picking by frequency keeps furniture from hijacking the
    # split and pins it out below.
    x_counts = Counter(round(x) for x, _, _ in cells)
    populous = [x for x, n in x_counts.most_common() if n >= _ABBR_MIN_PAIRS]
    if len(populous) < 2:
        return {}
    modal_left, modal_right = sorted(populous[:2])
    if modal_right - modal_left < _ABBR_COL_GAP_MIN:
        return {}
    split = (modal_left + modal_right) / 2

    rows: dict[int, dict[str, list[tuple[float, str]]]] = {}
    for x, y, text in cells:
        if x < split and abs(round(x) - modal_left) <= _ABBR_COL_TOL:
            rows.setdefault(round(y), {"l": [], "r": []})["l"].append((x, text))
        elif x >= split and abs(round(x) - modal_right) <= _ABBR_COL_TOL:
            rows.setdefault(round(y), {"l": [], "r": []})["r"].append((x, text))

    defs: dict[str, str] = {}
    for key in sorted(rows):
        left_cells = rows[key]["l"]
        right_cells = rows[key]["r"]
        if not left_cells or not right_cells:
            continue
        token = " ".join(t for _, t in sorted(left_cells)).strip()
        expansion = " ".join(t for _, t in sorted(right_cells)).strip()
        _add_pair(defs, token, expansion)
    return defs


def _add_pair(defs: dict[str, str], token: str, expansion: str) -> None:
    """Validate (token, expansion) and record it; first token wins."""
    if not _looks_like_abbreviation(token):
        return
    if len(expansion) <= len(token) or not any(c.isalpha() for c in expansion):
        return
    defs.setdefault(token, expansion)


def _pair_inline_rows(rows: list[tuple[float, float, str]]) -> dict[str, str]:
    """Pair the other common glossary layout: one line per entry, the
    abbreviation as the leading token and the expansion as the rest of the same
    line (`AR Assertion Roulette`). Split on the first whitespace; the
    abbreviation guards reject ordinary prose (a sentence opens with a
    Capitalized word that is mostly lowercase, so its first token fails)."""
    defs: dict[str, str] = {}
    for _, _, text in rows:
        parts = text.split(None, 1)
        if len(parts) == 2:
            _add_pair(defs, parts[0], parts[1].strip())
    return defs


def _inline_page_ok(defs: dict[str, str], rows: list[tuple[float, float, str]]) -> bool:
    """An inline glossary page must hold at least the floor of pairs and be
    mostly entries (a running header or page number is the only non-entry on a
    real page; a body page is mostly prose and fails the density gate)."""
    return len(defs) >= _ABBR_MIN_PAIRS and len(defs) >= _ABBR_INLINE_MIN_DENSITY * max(1, len(rows))


def collect_abbreviation_definitions(doc: fitz.Document, profile: DocProfile) -> dict[str, str]:
    """Find a two-column abbreviation glossary and return {token: expansion}.

    Pairing is done per page: a glossary page carries only the two columns, so
    the column gap survives, whereas a body page mixes x positions and yields no
    pairs. The scan starts at a heading whose folded text is a locale
    abbreviation term and walks following pages until one stops yielding pairs.
    A table-of-contents entry like "Lista de Siglas" (whose page holds section
    titles, not abbreviations) yields nothing and is skipped in favour of the
    real glossary later (#163). Returns {} when no heading qualifies."""
    pages_lines: list[list[tuple[float, float, float, str]]] = []  # per page: (x0, y0, size, text)
    for page in doc:
        lines: list[tuple[float, float, float, str]] = []
        for raw_block in page.get_text("dict").get("blocks", []):
            if raw_block.get("type") != 0:
                continue
            block = parse_block(raw_block)
            if block is None:
                continue
            for line in block.lines:
                text = line.text.strip()
                if text:
                    lines.append((line.bbox[0], round(line.bbox[1], 1), line.dominant_size, text))
        pages_lines.append(lines)

    def rows_of(page_idx: int, above_y: float | None) -> list[tuple[float, float, str]]:
        out: list[tuple[float, float, str]] = []
        for x0, y0, size, text in pages_lines[page_idx]:
            if above_y is not None and y0 <= above_y:
                continue  # skip the heading line and anything over it
            if profile.heading_level(size) is not None:
                continue  # a later section heading is not a glossary row
            out.append((x0, y0, text))
        return out

    for pi, lines in enumerate(pages_lines):
        for _x0, heading_y, _, text in lines:
            if _fold_heading(text) not in _ABBR_HEADING_TERMS:
                continue
            # The first page after the heading must itself yield a real table,
            # which both rejects a table-of-contents entry and fixes the layout
            # mode. Two real layouts exist: side-by-side columns, or one line
            # per entry with the abbreviation as the leading token. The chosen
            # extractor is then the only one applied to continuation pages, so a
            # body page (where the columnar gap is gone but a stray line could
            # still parse inline) cannot leak rows into the glossary.
            first_rows = rows_of(pi, heading_y)
            two_col = _pair_two_columns(first_rows)
            if len(two_col) >= _ABBR_MIN_PAIRS:
                extractor, defs = _pair_two_columns, dict(two_col)
            else:
                inline = _pair_inline_rows(first_rows)
                if not _inline_page_ok(inline, first_rows):
                    continue  # not a glossary (e.g. a TOC entry for "Lista de Siglas")
                extractor, defs = _pair_inline_rows, dict(inline)
            for offset in range(1, _ABBR_MAX_PAGES):
                page_idx = pi + offset
                if page_idx >= len(pages_lines):
                    break
                rows = rows_of(page_idx, None)
                page_defs = extractor(rows)
                # A continuation page must still read as a glossary. For the
                # inline layout that also means mostly-entries, so a body page
                # with a stray acronym-led line (e.g. "API calls ...") cannot
                # leak a bogus definition into the tail.
                if len(page_defs) < _ABBR_MIN_PAIRS:
                    break
                if extractor is _pair_inline_rows and not _inline_page_ok(page_defs, rows):
                    break
                for token, expansion in page_defs.items():
                    defs.setdefault(token, expansion)
            return defs
    return {}


def render_abbreviation_tail(definitions: dict[str, str]) -> str:
    """Document-tail block of python-markdown `*[TOKEN]: expansion` lines, sorted
    by token for determinism (#163). The `abbr` extension treats these as
    position-independent, so the tail placement is idiomatic, not a compromise."""
    return "\n".join(f"*[{token}]: {definitions[token]}" for token in sorted(definitions))


def convert_page(
    page: fitz.Page,
    profile: DocProfile,
    *,
    images_dir: Path | None = None,
    pdf_stem: str = "",
    inline_images: bool = False,
    skip_header_footer: bool = True,
    recurring_furniture: frozenset[str] = frozenset(),
) -> str:
    text_dict = page_text_dict(page)
    table_finder = page.find_tables()
    tables = list(table_finder)
    table_bboxes = [tuple(t.bbox) for t in tables]
    rendered_tables = {tuple(t.bbox): render_table(t, profile, text_dict) for t in tables}

    page_height = page.rect.height
    page_width = page.rect.width

    page_links: list[dict] = []
    try:
        page_links = page.get_links() or []
    except Exception:
        page_links = []

    image_items: list[tuple[float, float, str]] = []
    if images_dir is not None or inline_images:
        image_items = extract_page_images(page, images_dir, pdf_stem, inline=inline_images)

    items: list[tuple[float, str, object]] = []
    for t in tables:
        items.append((t.bbox[1], "table", t))

    parsed_blocks: list[Block] = []
    for raw_block in text_dict.get("blocks", []):
        if raw_block.get("type") != 0:
            continue
        block = parse_block(raw_block)
        if block is None:
            continue
        if skip_header_footer and is_header_footer(block.bbox, page_height, page_width):
            continue
        if (
            recurring_furniture
            and in_furniture_band(block.bbox, page_height)
            and any(normalize_furniture(line.text) in recurring_furniture for line in block.lines)
        ):
            continue  # running header/footer detected by cross-page recurrence (#187)
        if profile.footnote_pairing and parse_footnote_definition(block, profile, page_height) is not None:
            continue  # footnote definition: emitted in the document-tail block, not inline (#148)
        if block_in_any_bbox(block.bbox, table_bboxes):
            continue
        parsed_blocks.append(block)

    annotate_spans_with_links(parsed_blocks, page_links)
    if profile.extract_highlights:
        annotate_spans_with_highlights(parsed_blocks, page)
    drop_rule_strikethroughs(parsed_blocks, page)

    # Pair each image with a small-font caption line just below it and use that
    # text as the image's alt (#149). Off by default: alt stays empty and the
    # caption line is emitted as ordinary prose, so --with-images output is
    # unchanged. A caption is claimed by at most one image.
    caption_blocks: set[int] = set()   # consumed as alt: not re-emitted as prose
    anchor_claimed: set[int] = set()    # used for a figure anchor: still emitted as prose
    for top_y, bottom_y, left_x, right_x, rel in image_items:
        alt = ""
        attr = ""
        # The caption line below the image feeds both the alt text (#149) and the
        # figure anchor id (#165), so find it once when either option is on.
        if profile.caption_alt_text or profile.emit_figure_anchors:
            best: Block | None = None
            best_gap = CAPTION_MAX_GAP
            for block in parsed_blocks:
                # A caption already taken by another image (as alt or as an
                # anchor) is not available again, so one compound-figure caption
                # cannot anchor two images (#415 Codex).
                if (
                    id(block) in caption_blocks
                    or id(block) in anchor_claimed
                    or block.dominant_size > profile.small_size
                ):
                    continue
                # Require horizontal overlap so a side-by-side figure or column
                # cannot steal its neighbor's caption (#323 Codex review).
                if block.bbox[0] >= right_x or block.bbox[2] <= left_x:
                    continue
                gap = block.bbox[1] - bottom_y
                if 0 <= gap <= best_gap:
                    best, best_gap = block, gap
            if best is not None:
                # Anchor id from the caption number (#165). Reads the caption but
                # does NOT consume it, so a numbered figure keeps its visible
                # caption line and also gains an `{#fig-N}` cross-reference target.
                if profile.emit_figure_anchors:
                    fid = _figure_anchor_id(best.text, profile.figure_ids_used)
                    if fid:
                        attr = f"{{#{fid} .figure}}"
                        anchor_claimed.add(id(best))
                # Alt text from the caption (#149) consumes the caption line so it
                # is not also emitted as prose below the image.
                if profile.caption_alt_text:
                    candidate = _caption_alt(best.text)
                    if candidate:
                        alt = candidate
                        caption_blocks.add(id(best))
        items.append((top_y, "image", f"![{alt}]({rel}){attr}"))

    for block in parsed_blocks:
        if id(block) in caption_blocks:
            continue  # consumed as an image alt; do not also emit as prose
        items.append((block.bbox[1], "block", block))

    items.sort(key=lambda it: it[0])

    typed_items: list[tuple[str, object]] = []
    for _, kind, payload in items:
        if kind == "table":
            typed_items.append(("table", rendered_tables[tuple(payload.bbox)]))
        elif kind == "image":
            typed_items.append(("image", payload))
        else:
            typed_items.append(("block", payload))

    return assemble_markdown(typed_items, profile)


def render_blockquote(block: Block, profile: DocProfile) -> str:
    """Render ONE block as a single quoted paragraph: `> ` on each non-empty
    line. Framing blank lines come from the outer join. Multi-paragraph quotes
    are assembled in `assemble_markdown`, which joins consecutive quote blocks
    with a bare `>` separator line (#174).
    """
    quoted = [
        f"> {render_line(line, autolink_urls=profile.autolink_urls, autolink_emails=profile.autolink_emails).strip()}"
        for line in block.lines
        if line.text.strip()
    ]
    return "\n".join(quoted)


LINE_BREAK_MAX_LEN = 60.0  # a source line shorter than this can be an intentional break (#156)


def _dominant_line_font(line: Line) -> str:
    fonts: Counter[str] = Counter()
    for s in line.spans:
        fonts[s.font] += len(s.text)
    return fonts.most_common(1)[0][0] if fonts else ""


def _is_hard_break(prev_line: Line, next_line: Line, prev_rendered: str) -> bool:
    """A line break is intentional (poetry, postal address) when the two lines
    share font, size and left indent, the earlier line is short, and the next
    line does not read as a wrap continuation (#156)."""
    if len(prev_rendered) >= LINE_BREAK_MAX_LEN:
        return False  # long line: a wrap, not a deliberate break
    if _dominant_line_font(prev_line) != _dominant_line_font(next_line):
        return False
    if abs(prev_line.dominant_size - next_line.dominant_size) > 0.5:
        return False
    if abs(prev_line.bbox[0] - next_line.bbox[0]) > 2.0:
        return False
    # _should_merge_into_previous is True exactly when the next line continues a
    # wrapped sentence (lowercase start, leading and/or/but, prev trailing
    # comma/hyphen) -- the case where a break is NOT intentional.
    if _should_merge_into_previous(prev_rendered, render_line(next_line).strip()):
        return False
    return True


def render_paragraph(block: Block, profile: DocProfile) -> str:
    """Space-join the block's rendered lines (default), or insert CommonMark
    hard breaks (`  \\n`) between intentional same-font, same-indent short lines
    when `profile.preserve_line_breaks` is on. Off by default keeps output
    byte-identical (#156)."""
    lines = [ln for ln in block.lines if ln.text.strip()]
    rendered = [
        render_line(
            ln,
            profile.footnote_numbers,
            autolink_urls=profile.autolink_urls,
            autolink_emails=profile.autolink_emails,
        ).strip()
        for ln in lines
    ]
    if not profile.preserve_line_breaks:
        return " ".join(rendered).strip()
    parts: list[str] = []
    for i, text in enumerate(rendered):
        parts.append(text)
        if i + 1 < len(rendered):
            parts.append("  \n" if _is_hard_break(lines[i], lines[i + 1], text) else " ")
    return "".join(parts).strip()


def assemble_markdown(items: list[tuple[str, object]], profile: DocProfile) -> str:
    """Join page items (tables, images, text blocks) into Markdown.

    Pure assembly over items already in reading order, where each item is
    ("table", md), ("image", md), or ("block", Block). No page I/O, so the
    list / heading / paragraph state machine is unit-testable cross-platform.

    Tracks the open list item: a paragraph block indented past that item's
    marker edge is emitted as a continuation paragraph inside the item, not as
    a sibling block (#167). Consecutive numbered blocks are buffered into one
    contiguous list so an ordered list does not collapse into one single-item
    list per line (#144).
    """
    out_parts: list[str] = []
    numbered_run: list[str] = []
    numbered_loose = False
    numbered_last_bottom: float | None = None
    bullet_run: list[str] = []
    bullet_loose = False
    bullet_last_bottom: float | None = None
    # x0 of the open list item's marker, or None when not inside a list.
    list_marker_x0: float | None = None
    # Leading-space indent that nests a continuation under the item. The
    # shipped renderer (python-markdown) is not CommonMark: it needs a full
    # 4-space indent to bind a continuation paragraph to the item, not the
    # 2 spaces that align with a `- ` marker. We honor the renderer.
    list_cont_indent = ""
    # When a numbered item gained a continuation, the next item must sit on a
    # blank line or the renderer folds it into the continuation paragraph.
    numbered_loose_pending = False

    def flush_numbered() -> None:
        nonlocal numbered_loose_pending, numbered_loose, numbered_last_bottom
        if numbered_run:
            out_parts.append(("\n\n" if numbered_loose else "\n").join(numbered_run))
            numbered_run.clear()
        numbered_loose_pending = False
        numbered_loose = False
        numbered_last_bottom = None

    def flush_bullets() -> None:
        nonlocal bullet_loose, bullet_last_bottom
        if bullet_run:
            out_parts.append(("\n\n" if bullet_loose else "\n").join(bullet_run))
            bullet_run.clear()
        bullet_loose = False
        bullet_last_bottom = None

    def is_loose_gap(previous_bottom: float | None, current_top: float) -> bool:
        return previous_bottom is not None and current_top - previous_bottom > profile.list_loose_threshold * profile.body_size

    # Consecutive blockquote blocks are one quote with multiple paragraphs
    # (#174). Each PDF paragraph is its own Block, so we buffer the rendered
    # paragraphs and join them with a bare `>` line (CommonMark 5.1) on flush,
    # emitting one <blockquote> instead of several.
    blockquote_run: list[str] = []

    def flush_blockquote() -> None:
        if blockquote_run:
            out_parts.append("\n>\n".join(blockquote_run))
            blockquote_run.clear()

    # Consecutive heading blocks of the same level merge into one heading
    # (#188), so a heading split across PDF blocks on one page is rejoined.
    # Only active under cluster_headings; otherwise each heading emits alone.
    heading_run: list[str] = []
    heading_run_level = 0

    def flush_heading() -> None:
        nonlocal heading_run_level
        if heading_run:
            out_parts.append(f"{'#' * heading_run_level} {' '.join(heading_run)}")
            heading_run.clear()
        heading_run_level = 0

    for kind, payload in items:
        if kind == "table":
            flush_numbered()
            flush_bullets()
            flush_blockquote()
            flush_heading()
            list_marker_x0 = None
            if payload:
                out_parts.append(payload)
            continue
        if kind == "image":
            flush_numbered()
            flush_bullets()
            flush_blockquote()
            flush_heading()
            list_marker_x0 = None
            out_parts.append(payload)
            continue

        block: Block = payload
        cls = classify_block(block, profile)

        if cls == "code":
            code_lines = [line.text.rstrip() for line in block.lines if line.text.strip()]
            if not code_lines:
                continue
            # A code block indented past the open item's marker continues that
            # item (#197). The shipped renderer (python-markdown) nests code
            # under a list item only as an INDENTED block, not a fence: a fence
            # at the content column degrades to an inline code span. So we emit
            # the lines indented to the item content column plus 4, which drops
            # the language hint for the continuation; top-level code keeps its
            # fence and language.
            if (
                list_marker_x0 is not None
                and block.bbox[0] >= list_marker_x0 + LIST_CONTINUATION_MIN_INDENT
            ):
                flush_blockquote()
                flush_heading()
                indent = list_cont_indent + "    "
                cont_block = "\n".join(indent + ln for ln in code_lines)
                if numbered_run:
                    numbered_run.append("")
                    numbered_run.append(cont_block)
                    numbered_loose_pending = True
                    if profile.tight_loose_lists:
                        numbered_loose = True
                elif profile.tight_loose_lists and bullet_run:
                    bullet_run.extend(["", cont_block])
                    bullet_loose = True
                else:
                    out_parts.append(cont_block)
                continue
            flush_numbered()
            flush_bullets()
            flush_blockquote()
            flush_heading()
            list_marker_x0 = None
            code_body = "\n".join(code_lines)
            lang = detect_language(code_body)
            out_parts.append(f"```{lang}\n{code_body}\n```")
            continue

        text_rendered = " ".join(
            render_line(
                line,
                profile.footnote_numbers,
                autolink_urls=profile.autolink_urls,
                autolink_emails=profile.autolink_emails,
            ).strip()
            for line in block.lines
            if line.text.strip()
        ).strip()
        if not text_rendered:
            continue

        text_clean = HEADING_DOTS_RE.sub("", text_rendered)
        # Hard-break-aware text for STANDALONE paragraph/small blocks only (#156).
        # List continuations, headings, bullets and numbered items keep the
        # space-joined text_clean: a layout line break inside a list item would
        # push later lines out of the <li>. Identical to text_clean when the
        # flag is off, so the default path and the golden stay byte-identical.
        para_clean = (
            HEADING_DOTS_RE.sub("", render_paragraph(block, profile))
            if profile.preserve_line_breaks
            else text_clean
        )

        # A paragraph (or a blockquote candidate) indented past the open item's
        # marker continues that item. Continuation WINS over a quote: an
        # indented body block under an open list is item content, not a pull
        # quote (#147 precedence vs #167/#197). Emit it aligned to the item
        # content; a blank line (the run's internal blank, or the outer "\n\n"
        # join for bullets) makes the item loose so the renderer nests the
        # paragraph inside the <li> (#167).
        if (
            cls in ("paragraph", "blockquote")
            and list_marker_x0 is not None
            and block.bbox[0] >= list_marker_x0 + LIST_CONTINUATION_MIN_INDENT
        ):
            # A pending quote run cut off by a list continuation must close
            # first, or the next consecutive quote would fuse across the list
            # boundary (#174 state-corruption guard).
            flush_blockquote()
            flush_heading()
            cont_line = list_cont_indent + escape_line_start_specials(text_clean)
            if numbered_run:
                numbered_run.append("")
                numbered_run.append(cont_line)
                numbered_loose_pending = True
                if profile.tight_loose_lists:
                    numbered_loose = True
            elif profile.tight_loose_lists and bullet_run:
                bullet_run.extend(["", cont_line])
                bullet_loose = True
            else:
                out_parts.append(cont_line)
            continue

        # Any non-numbered block ends the current ordered-list run; any
        # non-quote block ends the current blockquote run. A consecutive quote
        # must NOT self-flush (it accumulates), hence the guard.
        if cls != "numbered":
            flush_numbered()
        if cls != "bullet":
            flush_bullets()
        if cls != "blockquote":
            flush_blockquote()
        if not cls.startswith("heading"):
            flush_heading()

        if cls.startswith("heading"):
            list_marker_x0 = None
            level = int(cls[-1])
            heading_text = re.sub(r"\*+", "", text_clean).strip()
            if profile.cluster_headings:
                # Merge a heading split across consecutive same-level blocks on
                # one page into a single heading (#188). A different level or
                # any non-heading block (above) flushes the open run first.
                if heading_run and heading_run_level == level:
                    heading_run.append(heading_text)
                else:
                    flush_heading()
                    heading_run_level = level
                    heading_run.append(heading_text)
            else:
                out_parts.append(f"{'#' * level} {heading_text}")
        elif cls == "bullet":
            stripped = text_clean.lstrip()
            for ch in BULLET_CHARS:
                if stripped.startswith(ch):
                    stripped = stripped[len(ch):].lstrip()
                    break
            nesting = profile.nesting_level(block.bbox[0])
            item = f"{'  ' * nesting}- {stripped}"
            if profile.tight_loose_lists:
                if is_loose_gap(bullet_last_bottom, block.bbox[1]):
                    bullet_loose = True
                bullet_run.append(item)
                bullet_last_bottom = block.bbox[3]
            else:
                out_parts.append(item)
            list_marker_x0 = block.bbox[0]
            list_cont_indent = "  " * nesting + "    "
        elif cls == "numbered":
            nesting = profile.nesting_level(block.bbox[0])
            marker, content = normalize_ordered_marker(text_clean, first=not numbered_run)
            if numbered_loose_pending:
                numbered_run.append("")
                numbered_loose_pending = False
            if profile.tight_loose_lists and is_loose_gap(numbered_last_bottom, block.bbox[1]):
                numbered_loose = True
            if marker:
                numbered_run.append(f"{'  ' * nesting}{marker} {content}")
            else:
                # Classified numbered but no recognizable marker: keep as-is.
                numbered_run.append(f"{'  ' * nesting}{text_clean}")
            list_cont_indent = "  " * nesting + "    "
            list_marker_x0 = block.bbox[0]
            numbered_last_bottom = block.bbox[3]
        elif cls == "blockquote":
            # Accumulate into the current quote run; consecutive quote blocks
            # become one <blockquote> with multiple paragraphs (#174). The run
            # is flushed by any non-quote block (above) or at end of items.
            list_marker_x0 = None
            blockquote_run.append(render_blockquote(block, profile))
        elif cls == "small":
            # Markdown has no clean small-text semantic, and raw <small> breaks
            # pure-Markdown consumers (RAG, plain viewers, indexers). Emit the
            # text as a plain paragraph and drop the size hint (#141). Opt-in
            # raw-HTML preservation is the job of the allow-list policy (#154).
            list_marker_x0 = None
            out_parts.append(escape_line_start_specials(para_clean))
        else:
            list_marker_x0 = None
            # Plain prose: escape a leading block marker so a paragraph that
            # genuinely starts with `#`, a bullet glyph, `>`, or `N.` is not
            # reinterpreted as a heading/list/quote on round-trip (#192).
            out_parts.append(escape_line_start_specials(para_clean))

    flush_numbered()
    flush_bullets()
    flush_blockquote()
    flush_heading()
    return "\n\n".join(out_parts)


# Caption-as-alt pairing (#149). A figure caption usually sits in a small-font
# line within ~two body lines below the image; that line is the natural alt
# text. Opt-in, and only relevant under --with-images (the default path extracts
# no images, so output stays unchanged).
CAPTION_MAX_GAP = 24.0  # pt below the image bottom to look for a caption line


def _caption_alt(text: str) -> str:
    """Sanitize a caption line into image alt text: collapse whitespace, strip
    surrounding quotes, and escape `]` so the `![...]()` syntax stays intact."""
    alt = re.sub(r"\s+", " ", text).strip()
    alt = alt.strip("\"'“”‘’").strip()
    return alt.replace("]", "\\]")


# Figure-anchor detection (#165). A figure caption opens with a numbered label:
# EN "Figure 3" / "Fig. 3", PT/ES "Figura 3". Tables are out of scope: attr_list
# cannot attach an id to a rendered <table> and raw HTML would breach the
# no-raw-HTML contract (tracked in a follow-up). The number becomes the id (dot
# -> hyphen), so "Figure 2.1" -> `fig-2-1`.
_FIGURE_CAPTION_RE = re.compile(
    r"^\s*(?:Figure|Fig\.?|Figura)\s*(\d+(?:\.\d+)*)\b",
    re.IGNORECASE,
)


def _figure_anchor_id(caption: str, used: set[str]) -> str | None:
    """Deterministic `fig-N` id from a numbered figure caption, or None.

    Dedupes against `used` the way heading anchors do (#152): a repeated number
    gets a `-2`, `-3` suffix so two figures never share an id. Mutates `used`.
    """
    m = _FIGURE_CAPTION_RE.match(caption)
    if not m:
        return None
    base = "fig-" + m.group(1).replace(".", "-")
    slug = base
    n = 1
    while slug in used:
        n += 1
        slug = f"{base}-{n}"
    used.add(slug)
    return slug


def extract_page_images(
    page: fitz.Page, images_dir: Path | None, pdf_stem: str, inline: bool = False
) -> list[tuple[float, float, float, float, str]]:
    """Return [(top_y, bottom_y, left_x, right_x, ref), ...] for each image on the
    page, in reading order. The bottom edge and x-span let the caller pair a
    caption line that sits just below AND horizontally overlaps the image (#149).

    `ref` is either a relative file path (default: image is written to
    <images_dir>/<pdf_stem>/p{N}_img{I}.<ext>) or, when `inline` is set, a base64
    `data:` URI so the Markdown carries the image with no external file (#372).
    Inline needs no images_dir and writes nothing to disk."""
    out: list[tuple[float, float, float, float, str]] = []
    doc = page.parent
    page_no = page.number + 1
    try:
        infos = page.get_image_info(hashes=False, xrefs=True)
    except TypeError:
        infos = page.get_image_info()
    for idx, info in enumerate(infos):
        xref = info.get("xref", 0)
        if not xref:
            continue
        try:
            img = doc.extract_image(xref)
        except Exception:
            continue
        if not img:
            continue
        ext = img.get("ext", "png")
        bbox = info.get("bbox", (0.0, 0.0, 0.0, 0.0))
        try:
            top_y = float(bbox[1])
            bottom_y = float(bbox[3])
            left_x = float(bbox[0])
            right_x = float(bbox[2])
        except (TypeError, IndexError, ValueError):
            top_y = bottom_y = left_x = right_x = 0.0
        if inline:
            b64 = base64.b64encode(img["image"]).decode("ascii")
            ref = f"data:image/{ext};base64,{b64}"
        else:
            filename = f"p{page_no}_img{idx + 1}.{ext}"
            target_dir = images_dir / pdf_stem
            target_dir.mkdir(parents=True, exist_ok=True)
            (target_dir / filename).write_bytes(img["image"])
            ref = f"images/{pdf_stem}/{filename}".replace("\\", "/")
        out.append((top_y, bottom_y, left_x, right_x, ref))
    return out


def convert_document(
    pdf_path: Path,
    output_path: Path,
    *,
    page_break: bool = False,
    debug: bool = False,
    extract_images: bool = False,
    inline_images: bool = False,
    front_matter: bool = True,
    detect_blockquotes: bool = False,
    cluster_headings: bool = False,
    subtract_running_furniture: bool = False,
    allow_html: frozenset[str] = frozenset(),
    preserve_line_breaks: bool = False,
    max_heading_level: int = 3,
    footnote_pairing: bool = False,
    autolink_urls: bool = False,
    autolink_emails: bool = False,
    reference_link_threshold: int = 0,
    emit_heading_anchors: bool = False,
    pair_quote_attribution: bool = False,
    extract_abbreviations: bool = False,
    extract_highlights: bool = False,
    smart_typography_quotes: str = "preserve",
    smart_typography_ellipsis: str = "preserve",
    smart_typography_dashes: str = "preserve",
    caption_alt_text: bool = False,
    detect_task_lists: bool = False,
    task_list_extended: bool = False,
    emit_figure_anchors: bool = False,
    table_column_align: bool = False,
    tight_loose_lists: bool = False,
    list_loose_threshold: float = 1.5,
) -> None:
    doc = fitz.open(pdf_path)
    profile = build_profile(doc)
    profile.caption_alt_text = caption_alt_text
    profile.detect_blockquotes = detect_blockquotes
    profile.cluster_headings = cluster_headings
    profile.allow_html = allow_html
    profile.preserve_line_breaks = preserve_line_breaks
    profile.footnote_pairing = footnote_pairing
    profile.autolink_urls = autolink_urls
    profile.autolink_emails = autolink_emails
    profile.extract_highlights = extract_highlights
    profile.emit_figure_anchors = emit_figure_anchors
    profile.table_column_align = table_column_align
    profile.tight_loose_lists = tight_loose_lists
    profile.list_loose_threshold = list_loose_threshold
    footnote_defs: dict[int, str] = {}
    if footnote_pairing:
        footnote_defs = collect_footnote_definitions(doc, profile)
        # Rewrite a body superscript to [^N] only when there is a matching
        # definition; a ref with no definition stays a literal `^N^`.
        profile.footnote_numbers = frozenset(footnote_defs)
    if cluster_headings:
        # Replace the fixed-cutoff thresholds with gap-partitioned size bands,
        # capped at max_heading_level (deeper levels only exist here, #146).
        profile.heading_thresholds = cluster_heading_bands(
            profile.size_histogram, profile.body_size, max_level=max_heading_level
        )
    abbreviation_defs: dict[str, str] = {}
    if extract_abbreviations:
        # Pre-scan for a two-column glossary; emitted as a tail block below so
        # the `abbr` extension expands the tokens wherever they appear (#163).
        abbreviation_defs = collect_abbreviation_definitions(doc, profile)

    recurring_furniture = find_recurring_furniture(doc) if subtract_running_furniture else frozenset()
    toc = doc.get_toc()

    if debug:
        print(f"[debug] body={profile.body_size}pt thresholds={profile.heading_thresholds} small<={profile.small_size}")
        print(f"[debug] body_x0={profile.body_x0} indent_unit={profile.indent_unit}")
        print(f"[debug] TOC entries: {len(toc)}")

    pdf_stem = pdf_path.stem
    images_dir = output_path.parent / "images" if extract_images else None
    if images_dir is not None:
        # Clean stale images from any prior run on the same PDF.
        target = images_dir / pdf_stem
        if target.exists():
            for f in target.iterdir():
                if f.is_file():
                    f.unlink()
            try:
                target.rmdir()
            except OSError:
                # Directory may not be empty (extra files dropped by a
                # custom hook). Leftover is harmless; keep going.
                pass

    out_pages: list[str] = []
    for page in doc:
        page_md = convert_page(
            page, profile, images_dir=images_dir, pdf_stem=pdf_stem,
            inline_images=inline_images,
            recurring_furniture=recurring_furniture,
        )
        if page_md.strip():
            out_pages.append(page_md)

    # Remove the images dir if nothing was extracted (no leftover empty folder).
    if images_dir is not None:
        target = images_dir / pdf_stem
        if target.exists() and not any(target.iterdir()):
            target.rmdir()
        if images_dir.exists() and not any(images_dir.iterdir()):
            images_dir.rmdir()

    sep = "\n\n---\n\n" if page_break else "\n\n"
    full = sep.join(out_pages)
    full = merge_wrapped_headings(full)
    full = merge_continued_paragraphs(full)
    full = normalize_headings_from_toc(full, toc)
    full = drop_orphan_heading_fragments(full)

    if footnote_pairing:
        # Append the GFM footnote definitions at the document tail, after the
        # wrapped-paragraph/heading post-passes so they never fuse `[^N]:` into
        # prose (#148).
        tail = render_footnote_tail(footnote_defs)
        if tail:
            full = full + "\n\n" + tail

    # Collapse repeated inline links to reference style (#158), after every
    # body post-pass and the footnote tail so the appended `[id]:` definitions
    # land at the true document end. Off by default (threshold 0).
    full = _collapse_reference_links(full, reference_link_threshold)

    # Append deterministic `{#slug}` anchors to headings (#152). Runs on the
    # assembled body so slug dedup is document-wide, not per-page. Off by default.
    if emit_heading_anchors:
        full = _emit_heading_anchors(full)

    # Fold a dash-introduced attribution line into the blockquote above it
    # (#173). Off by default; no-op unless detect_blockquotes produced a `>`.
    if pair_quote_attribution:
        full = _pair_quote_attribution(full)

    # Append `*[TOKEN]: expansion` definitions from a detected glossary (#163).
    # Position-independent for the `abbr` extension, so the document tail is the
    # idiomatic spot. Off by default; empty when no glossary qualified.
    if abbreviation_defs:
        tail = render_abbreviation_tail(abbreviation_defs)
        if tail:
            full = full + "\n\n" + tail

    # Map checkbox glyphs / bracket sequences to GFM task-list items (#172).
    # Runs on the assembled body before typography folding; off by default.
    if detect_task_lists:
        full = _normalize_task_lists(full, extended=task_list_extended)

    # Fold Unicode typography to ASCII in prose (#171). Runs last so it also
    # normalizes any appended tail blocks; protects code and URLs (including the
    # reference-definition lines added above). No-op at the default settings.
    full = _smart_typography(
        full,
        quotes=smart_typography_quotes,
        ellipsis=smart_typography_ellipsis,
        dashes=smart_typography_dashes,
    )

    if front_matter:
        fm = build_front_matter(pdf_path, doc)
        full = fm + "\n\n" + full

    output_path.write_text(full, encoding="utf-8")
    print(f"Wrote {output_path}  ({len(out_pages)} non-empty pages)")


def _yaml_escape(s: str) -> str:
    return s.replace("\\", "\\\\").replace('"', '\\"')


def build_front_matter(pdf_path: Path, doc: fitz.Document) -> str:
    meta = doc.metadata or {}
    title = (meta.get("title") or pdf_path.stem).strip()
    author = (meta.get("author") or "").strip()
    subject = (meta.get("subject") or "").strip()
    keywords = (meta.get("keywords") or "").strip()

    date = ""
    raw_date = (meta.get("creationDate") or "").strip()
    if raw_date.startswith("D:") and len(raw_date) >= 10:
        try:
            date = f"{raw_date[2:6]}-{raw_date[6:8]}-{raw_date[8:10]}"
        except Exception:
            date = ""

    lines = ["---", f'title: "{_yaml_escape(title)}"']
    if author:
        lines.append(f'author: "{_yaml_escape(author)}"')
    if date:
        lines.append(f'date: "{date}"')
    if subject:
        lines.append(f'subject: "{_yaml_escape(subject)}"')
    if keywords:
        lines.append(f'keywords: "{_yaml_escape(keywords)}"')
    lines.append(f'source: "{pdf_path.name}"')
    lines.append(f'pages: {doc.page_count}')
    lines.append("---")
    return "\n".join(lines)


def _norm_for_match(s: str) -> str:
    s = re.sub(r"\*+", "", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip().lower()


def drop_orphan_heading_fragments(md: str) -> str:
    """Drop heading lines that are short single-word fragments left after
    TOC normalization absorbed a multi-line heading. Such fragments are
    lowercase or 1-2 words and tend to appear directly after a longer heading.
    """
    heading_re = re.compile(r"^(#{1,6})\s+(.*)$")
    lines = md.split("\n")
    out: list[str] = []
    prev_was_heading = False
    for line in lines:
        m = heading_re.match(line)
        if m:
            text = m.group(2).strip()
            words = text.split()
            # Drop only lowercase-starting fragments: those are wrap continuations.
            # Capitalized single-word headings (e.g. "Syllabus", "Overview") are real.
            is_fragment = (
                prev_was_heading
                and len(words) <= 2
                and len(text) <= 25
                and bool(text)
                and text[0].islower()
            )
            if is_fragment:
                continue
            prev_was_heading = True
            out.append(line)
        else:
            if line.strip():
                prev_was_heading = False
            out.append(line)
    return "\n".join(out)


def normalize_headings_from_toc(md: str, toc: list) -> str:
    """Canonicalize heading text and force levels using the PDF outline.

    The outline (bookmarks / TOC) is the document's authoritative table of
    contents — it survives line wraps and font quirks. When a detected
    heading approximately matches a TOC entry, we replace it with the
    canonical title at the TOC's level.
    """
    if not toc:
        return md

    toc_entries: list[tuple[int, str, str]] = []
    for entry in toc:
        if not entry or len(entry) < 2:
            continue
        level, title = int(entry[0]), str(entry[1]).strip()
        if title:
            toc_entries.append((level, title, _norm_for_match(title)))
    if not toc_entries:
        return md

    heading_re = re.compile(r"^(#{1,6})\s+(.*)$")
    out_lines: list[str] = []
    for line in md.split("\n"):
        m = heading_re.match(line)
        if not m:
            out_lines.append(line)
            continue
        text = m.group(2).strip()
        text_norm = _norm_for_match(text)
        matched = None
        for tlvl, ttext, tnorm in toc_entries:
            if not tnorm:
                continue
            if text_norm == tnorm:
                matched = (tlvl, ttext)
                break
            # Substring match within a tolerance to handle "1 Motivation..." vs
            # "1 Motivation for Digital Design"
            if (tnorm in text_norm or text_norm in tnorm) and abs(len(tnorm) - len(text_norm)) <= max(15, int(len(tnorm) * 0.4)):
                matched = (tlvl, ttext)
                break
        if matched:
            new_level, new_text = matched
            out_lines.append(f"{'#' * new_level} {new_text}")
        else:
            out_lines.append(line)
    return "\n".join(out_lines)


PARAGRAPH_END = (".", "!", "?", ":", ";", "\"", "”", "’", ")", "]", "}", "…")


# Running page furniture: "Page 3 of 77", "v4.0 GA Page 3 of 77 2025/05/02".
# These lines are not prose. Before #141 the <small> wrapper kept them out of
# the wrapped-paragraph merge; now that small blocks render as plain text, this
# content test fills the same role so a footer is never fused into an adjacent
# paragraph. The opt-in #187 pass subtracts band furniture that recurs across
# pages; this regex still guards stragglers (short docs, below-threshold, or
# furniture outside the band) from being fused into prose.
_PAGE_FURNITURE_RE = re.compile(r"\bpage\s+\d+\s+of\s+\d+\b", re.IGNORECASE)


def looks_like_page_furniture(text: str) -> bool:
    return bool(_PAGE_FURNITURE_RE.search(text))


def is_block_paragraph(block: str) -> bool:
    # A leading indent now carries list-nesting meaning: the block is a
    # continuation paragraph bound to a list item (#167). Treat it as
    # structural so the wrapped-paragraph merge never folds a de-indented
    # top-level sibling into it (which would keep the indent and pull the
    # sibling inside the <li>).
    if block[:1] in (" ", "\t"):
        return False
    s = block.lstrip()
    if not s:
        return False
    first = s[0]
    if first == "#":
        return False
    if first == "|":
        return False
    if s.startswith("- ") or s.startswith("* ") or s.startswith("+ "):
        return False
    if s.startswith("---"):
        return False
    if s.startswith("```"):
        return False
    if s.startswith(">"):
        return False  # blockquote (#147): structural, never fused into prose
    if NUMBERED_RE.match(s):
        return False
    # A running header/footer is not prose; keep it out of the merge so it is
    # not fused into the surrounding paragraphs (#141).
    if looks_like_page_furniture(s):
        return False
    return True


def _should_merge_into_previous(prev: str, curr: str) -> bool:
    prev_tail = prev.rstrip()
    curr_head = curr.lstrip()
    if not prev_tail or not curr_head:
        return False
    if prev_tail.endswith(PARAGRAPH_END):
        return False
    # Hyphenated word break ("self-\nconfident")
    if prev_tail.endswith("-") and len(prev_tail) > 1 and prev_tail[-2].isalpha():
        return True
    # Trailing comma → clear continuation
    if prev_tail.endswith(","):
        return True
    # Next line starts with lowercase or with a common continuation word
    first_char = curr_head[0]
    if first_char.islower():
        return True
    first_word = curr_head.split(None, 1)[0].lower().rstrip(",.;:")
    if first_word in {"and", "or", "but", "nor", "however", "therefore", "thus", "e.g.,", "i.e.,"}:
        return True
    return False


def merge_continued_paragraphs(md: str) -> str:
    """Join adjacent paragraphs that look like one was wrapped into two blocks.

    Only merges when the second block clearly continues the first
    (lowercase start, leading "and/or/but", trailing comma/hyphen), so lists
    of proper nouns (e.g. Contributors) are preserved as separate blocks.
    """
    blocks = re.split(r"\n{2,}", md)
    result: list[str] = []
    for b in blocks:
        if (
            result
            and is_block_paragraph(result[-1])
            and is_block_paragraph(b)
            and _should_merge_into_previous(result[-1], b)
        ):
            tail = result[-1].rstrip()
            if tail.endswith("-") and len(tail) > 1 and tail[-2].isalpha():
                result[-1] = tail[:-1] + b.lstrip()
            else:
                result[-1] = tail + " " + b.lstrip()
        else:
            result.append(b)
    return "\n\n".join(result)


CONTINUATION_TAIL_WORDS = {
    "the", "a", "an", "of", "in", "on", "at", "for", "to", "by",
    "from", "with", "into", "and", "or", "but", "as", "via", "per",
    "this", "that", "these", "those", "their", "his", "her", "our",
    "digital",  # domain-specific carriers seen in IREB; harmless elsewhere
}


def merge_wrapped_headings(md: str) -> str:
    """Merge two consecutive same-level headings only when the first is
    clearly mid-phrase (ends with a preposition/article/conjunction)."""
    lines = md.split("\n")
    out: list[str] = []
    i = 0
    heading_re = re.compile(r"^(#{1,6})\s+(.*)$")
    while i < len(lines):
        m = heading_re.match(lines[i])
        if not m:
            out.append(lines[i])
            i += 1
            continue
        level, text = m.group(1), m.group(2).strip()
        j = i + 1
        while j < len(lines) and lines[j].strip() == "":
            j += 1
        if j < len(lines):
            m2 = heading_re.match(lines[j])
            if m2 and m2.group(1) == level:
                cont = m2.group(2).strip()
                last_word = text.rsplit(None, 1)[-1].lower().strip(",.:;\"'()[]") if text else ""
                first_char = cont[:1]
                if (
                    cont
                    and not first_char.isdigit()
                    and len(cont) <= 70
                    and last_word in CONTINUATION_TAIL_WORDS
                ):
                    out.append(f"{level} {text} {cont}")
                    i = j + 1
                    continue
        out.append(lines[i])
        i += 1
    return "\n".join(out)


def main() -> int:
    parser = argparse.ArgumentParser(description="Convert PDF to structured Markdown (no AI).")
    parser.add_argument("pdf_path", type=Path)
    parser.add_argument("-o", "--output", type=Path, required=True)
    parser.add_argument("--page-break", action="store_true", help="Insert --- between pages")
    parser.add_argument("--with-images", action="store_true", help="Extract images to ./images/<pdf>/ and reference them in the .md")
    parser.add_argument("--inline-images", action="store_true", help="Embed images inline as base64 data URIs so the .md is self-contained (no image files); overrides --with-images (#372)")
    parser.add_argument("--caption-alt-text", action="store_true", help="Use a small-font caption line below an image as its alt text (opt-in, #149)")
    parser.add_argument("--no-front-matter", action="store_true", help="Skip YAML front matter")
    parser.add_argument(
        "--detect-blockquotes",
        action="store_true",
        help="Classify sustained-indent body blocks as blockquotes (opt-in, #147)",
    )
    parser.add_argument(
        "--cluster-headings",
        action="store_true",
        help="Map font sizes to heading levels by gap-partitioned bands and merge multi-line headings (opt-in, #188)",
    )
    parser.add_argument(
        "--subtract-furniture",
        action="store_true",
        help="Subtract running headers/footers that recur across pages (opt-in, #187)",
    )
    parser.add_argument(
        "--preserve-line-breaks",
        action="store_true",
        help="Keep intentional layout line breaks (poetry, addresses) as hard breaks (opt-in, #156)",
    )
    parser.add_argument(
        "--max-heading-level",
        type=int,
        default=3,
        choices=range(1, 7),
        metavar="N",
        help="Cap clustered heading depth at N (1-6); only affects output with --cluster-headings (#146)",
    )
    parser.add_argument(
        "--footnote-pairing",
        action="store_true",
        help="Pair small-font footer footnotes with body superscript refs as GFM [^N] (opt-in, #148)",
    )
    parser.add_argument(
        "--autolink-urls",
        action="store_true",
        help="Wrap bare http(s) URLs in body text as CommonMark autolinks (opt-in, #157)",
    )
    parser.add_argument(
        "--autolink-emails",
        action="store_true",
        help="Wrap bare email addresses in body text as CommonMark autolinks (opt-in, #157)",
    )
    parser.add_argument(
        "--reference-link-threshold",
        type=int,
        default=0,
        metavar="N",
        help="Collapse a URL linked inline N+ times into reference style with a definitions block; 0 disables (opt-in, #158)",
    )
    parser.add_argument(
        "--emit-heading-anchors",
        action="store_true",
        help="Append a deterministic Pandoc/mkdocs {#slug} anchor to each heading (opt-in, #152)",
    )
    parser.add_argument(
        "--pair-quote-attribution",
        action="store_true",
        help="Fold a dash-introduced attribution line into the blockquote above it (opt-in, #173)",
    )
    parser.add_argument(
        "--extract-abbreviations",
        action="store_true",
        help="Emit *[ABBR]: expansion lines from a two-column abbreviation glossary section (opt-in, #163)",
    )
    parser.add_argument(
        "--smart-typography-quotes",
        choices=("preserve", "ascii"),
        default="preserve",
        help="Fold curly quotes to straight ASCII (opt-in, #171)",
    )
    parser.add_argument(
        "--smart-typography-ellipsis",
        choices=("preserve", "ascii"),
        default="preserve",
        help="Fold an ellipsis character to ... (opt-in, #171)",
    )
    parser.add_argument(
        "--smart-typography-dashes",
        choices=("preserve", "ascii"),
        default="preserve",
        help="Fold en/em dash to --/--- (opt-in, #171)",
    )
    parser.add_argument(
        "--detect-task-lists",
        action="store_true",
        help="Map source checkbox glyphs / bracket sequences to GFM task-list items (opt-in, #172)",
    )
    parser.add_argument(
        "--task-list-extended",
        action="store_true",
        help="Also recognize the todo-md [-] in-progress marker (requires --detect-task-lists, #172)",
    )
    parser.add_argument(
        "--extract-highlights",
        action="store_true",
        help="Emit ==text== from PDF text-highlight annotations (opt-in, #162)",
    )
    parser.add_argument(
        "--emit-figure-anchors",
        action="store_true",
        help="Emit {#fig-N .figure} on numbered figures for cross-references (opt-in, needs --with-images, #165)",
    )
    parser.add_argument(
        "--table-column-align",
        action="store_true",
        help="Detect table-cell alignment and emit GFM separator markers (opt-in, #175)",
    )
    parser.add_argument("--tight-loose-lists", action="store_true", help="Preserve PDF list spacing as CommonMark tight or loose lists (opt-in, #168)")
    parser.add_argument("--list-loose-threshold", type=float, default=1.5, metavar="N", help="Gap in body line-heights that marks a list loose (default: 1.5, #168)")
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()

    if not args.pdf_path.exists():
        print(f"File not found: {args.pdf_path}", file=sys.stderr)
        return 1
    args.output.parent.mkdir(parents=True, exist_ok=True)
    convert_document(
        args.pdf_path,
        args.output,
        page_break=args.page_break,
        debug=args.debug,
        extract_images=args.with_images and not args.inline_images,
        inline_images=args.inline_images,
        front_matter=not args.no_front_matter,
        detect_blockquotes=args.detect_blockquotes,
        cluster_headings=args.cluster_headings,
        subtract_running_furniture=args.subtract_furniture,
        preserve_line_breaks=args.preserve_line_breaks,
        max_heading_level=args.max_heading_level,
        footnote_pairing=args.footnote_pairing,
        autolink_urls=args.autolink_urls,
        autolink_emails=args.autolink_emails,
        reference_link_threshold=args.reference_link_threshold,
        emit_heading_anchors=args.emit_heading_anchors,
        pair_quote_attribution=args.pair_quote_attribution,
        extract_abbreviations=args.extract_abbreviations,
        smart_typography_quotes=args.smart_typography_quotes,
        smart_typography_ellipsis=args.smart_typography_ellipsis,
        smart_typography_dashes=args.smart_typography_dashes,
        caption_alt_text=args.caption_alt_text,
        detect_task_lists=args.detect_task_lists,
        task_list_extended=args.task_list_extended,
        extract_highlights=args.extract_highlights,
        emit_figure_anchors=args.emit_figure_anchors,
        table_column_align=args.table_column_align,
        tight_loose_lists=args.tight_loose_lists,
        list_loose_threshold=args.list_loose_threshold,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
