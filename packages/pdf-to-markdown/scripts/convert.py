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
import io
import re
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

import fitz  # PyMuPDF

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

FLAG_SUPERSCRIPT = 1 << 0
FLAG_ITALIC = 1 << 1
FLAG_SERIF = 1 << 2
FLAG_MONO = 1 << 3
FLAG_BOLD = 1 << 4

BULLET_CHARS = {"▪", "•", "●", "◦", "‣", "⁃", "∙"}
NUMBERED_RE = re.compile(r"^\s*(\d{1,3}|[a-zA-Z])[.)]\s+")

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
MONO_FONT_HINTS = ("Mono", "Courier", "Consolas", "Menlo", "Inconsolata", "Hack")
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

    def heading_level(self, size: float) -> int | None:
        for level in (1, 2, 3):
            if size >= self.heading_thresholds[level]:
                return level
        return None

    def nesting_level(self, x0: float) -> int:
        if self.indent_unit <= 0:
            return 0
        n = int(round(max(0.0, x0 - self.list_base_x0) / self.indent_unit))
        return min(max(n, 0), 5)


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
    )


def parse_block(raw_block: dict) -> Block | None:
    lines: list[Line] = []
    for raw_line in raw_block.get("lines", []):
        spans = []
        for raw_span in raw_line.get("spans", []):
            text = raw_span["text"]
            if not text:
                continue
            spans.append(
                Span(
                    text=text,
                    size=raw_span["size"],
                    font=raw_span["font"],
                    flags=raw_span["flags"],
                    bbox=tuple(raw_span.get("bbox", (0.0, 0.0, 0.0, 0.0))),
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


def render_span(span: Span) -> str:
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
    if core:
        if mono and "`" not in core:
            # Code spans render their content literally, so do not escape inside
            # the backticks. Every other case is literal prose that must be
            # escaped before we add our own emphasis/link markers.
            core = f"`{core}`"
        else:
            core = escape_markdown_inline(core)
        if sup:
            core = f"<sup>{core}</sup>"
        if bold and italic:
            core = f"***{core}***"
        elif bold:
            core = f"**{core}**"
        elif italic:
            core = f"*{core}*"
        if span.link:
            core = f"[{core}]({span.link})"
    return out[:leading] + core + (out[len(out) - trailing:] if trailing else "")


def render_line(line: Line) -> str:
    # Merge adjacent spans with same style to avoid `**a****b**` artifacts
    merged: list[Span] = []
    for s in line.spans:
        if (
            merged
            and merged[-1].is_bold == s.is_bold
            and merged[-1].is_italic == s.is_italic
            and is_mono_span(merged[-1]) == is_mono_span(s)
        ):
            merged[-1] = Span(
                text=merged[-1].text + s.text,
                size=merged[-1].size,
                font=merged[-1].font,
                flags=merged[-1].flags,
            )
        else:
            merged.append(s)
    return "".join(render_span(s) for s in merged)


def dominant_font(block: Block) -> str:
    fonts: Counter[str] = Counter()
    for line in block.lines:
        for s in line.spans:
            fonts[s.font] += len(s.text)
    return fonts.most_common(1)[0][0] if fonts else ""


def is_mono_span(span: Span) -> bool:
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
    if re.search(r"^\s*(function\s|const\s|let\s|var\s|=>\s)", text, re.MULTILINE):
        return "javascript"
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


def classify_block(block: Block, profile: DocProfile) -> str:
    """Return one of: heading1, heading2, heading3, bullet, numbered, code, paragraph, small."""
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


def render_table(table) -> str:
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

    rows = [[(c or "").strip().replace("\n", " ") for c in row] for row in rows]
    width = max(len(r) for r in rows)
    rows = [r + [""] * (width - len(r)) for r in rows]

    # Drop columns that are entirely empty
    keep_cols = [i for i in range(width) if any(r[i] for r in rows)]
    if not keep_cols:
        return ""
    rows = [[r[i] for i in keep_cols] for r in rows]
    width = len(keep_cols)

    # Merge duplicate adjacent columns: when two adjacent columns hold the same
    # value in every row (or one is always blank when the other isn't), collapse them.
    merged_cols: list[list[str]] = [[r[0] for r in rows]]
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
        else:
            merged_cols.append(col)
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
    out.append("| " + " | ".join("---" for _ in header) + " |")
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


def convert_page(
    page: fitz.Page,
    profile: DocProfile,
    *,
    images_dir: Path | None = None,
    pdf_stem: str = "",
    skip_header_footer: bool = True,
) -> str:
    table_finder = page.find_tables()
    tables = list(table_finder)
    table_bboxes = [tuple(t.bbox) for t in tables]
    rendered_tables = {tuple(t.bbox): render_table(t) for t in tables}

    page_height = page.rect.height
    page_width = page.rect.width

    page_links: list[dict] = []
    try:
        page_links = page.get_links() or []
    except Exception:
        page_links = []

    image_items: list[tuple[float, str]] = []
    if images_dir is not None:
        image_items = extract_page_images(page, images_dir, pdf_stem)

    items: list[tuple[float, str, object]] = []
    for t in tables:
        items.append((t.bbox[1], "table", t))
    for y, md in image_items:
        items.append((y, "image", md))

    parsed_blocks: list[Block] = []
    for raw_block in page.get_text("dict").get("blocks", []):
        if raw_block.get("type") != 0:
            continue
        block = parse_block(raw_block)
        if block is None:
            continue
        if skip_header_footer and is_header_footer(block.bbox, page_height, page_width):
            continue
        if block_in_any_bbox(block.bbox, table_bboxes):
            continue
        parsed_blocks.append(block)

    annotate_spans_with_links(parsed_blocks, page_links)
    for block in parsed_blocks:
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
        nonlocal numbered_loose_pending
        if numbered_run:
            out_parts.append("\n".join(numbered_run))
            numbered_run.clear()
        numbered_loose_pending = False

    for kind, payload in items:
        if kind == "table":
            flush_numbered()
            list_marker_x0 = None
            if payload:
                out_parts.append(payload)
            continue
        if kind == "image":
            flush_numbered()
            list_marker_x0 = None
            out_parts.append(payload)
            continue

        block: Block = payload
        cls = classify_block(block, profile)

        if cls == "code":
            flush_numbered()
            list_marker_x0 = None
            code_lines = [line.text.rstrip() for line in block.lines if line.text.strip()]
            if not code_lines:
                continue
            code_body = "\n".join(code_lines)
            lang = detect_language(code_body)
            out_parts.append(f"```{lang}\n{code_body}\n```")
            continue

        text_rendered = " ".join(render_line(line).strip() for line in block.lines if line.text.strip()).strip()
        if not text_rendered:
            continue

        text_clean = HEADING_DOTS_RE.sub("", text_rendered)

        # A paragraph indented past the open item's marker continues that item.
        # Emit it aligned to the item content; a blank line (the run's internal
        # blank, or the outer "\n\n" join for bullets) makes the item loose so
        # the renderer nests the paragraph inside the <li> (#167).
        if (
            cls == "paragraph"
            and list_marker_x0 is not None
            and block.bbox[0] >= list_marker_x0 + LIST_CONTINUATION_MIN_INDENT
        ):
            cont_line = list_cont_indent + text_clean
            if numbered_run:
                numbered_run.append("")
                numbered_run.append(cont_line)
                numbered_loose_pending = True
            else:
                out_parts.append(cont_line)
            continue

        # Any non-numbered block ends the current ordered-list run.
        if cls != "numbered":
            flush_numbered()

        if cls.startswith("heading"):
            list_marker_x0 = None
            level = int(cls[-1])
            heading_text = re.sub(r"\*+", "", text_clean).strip()
            out_parts.append(f"{'#' * level} {heading_text}")
        elif cls == "bullet":
            stripped = text_clean.lstrip()
            for ch in BULLET_CHARS:
                if stripped.startswith(ch):
                    stripped = stripped[len(ch):].lstrip()
                    break
            nesting = profile.nesting_level(block.bbox[0])
            out_parts.append(f"{'  ' * nesting}- {stripped}")
            list_marker_x0 = block.bbox[0]
            list_cont_indent = "  " * nesting + "    "
        elif cls == "numbered":
            nesting = profile.nesting_level(block.bbox[0])
            marker, content = normalize_ordered_marker(text_clean, first=not numbered_run)
            if numbered_loose_pending:
                numbered_run.append("")
                numbered_loose_pending = False
            if marker:
                numbered_run.append(f"{'  ' * nesting}{marker} {content}")
            else:
                # Classified numbered but no recognizable marker: keep as-is.
                numbered_run.append(f"{'  ' * nesting}{text_clean}")
            list_cont_indent = "  " * nesting + "    "
            list_marker_x0 = block.bbox[0]
        elif cls == "small":
            list_marker_x0 = None
            out_parts.append(f"<small>{text_clean}</small>")
        else:
            list_marker_x0 = None
            out_parts.append(text_clean)

    flush_numbered()
    return "\n\n".join(out_parts)


def extract_page_images(page: fitz.Page, images_dir: Path, pdf_stem: str) -> list[tuple[float, str]]:
    """Save each image on the page to <images_dir>/<pdf_stem>/p{N}_img{I}.<ext>
    and return [(top_y, markdown_ref), ...] for placement in reading order."""
    out: list[tuple[float, str]] = []
    doc = page.parent
    page_no = page.number + 1
    target_dir = images_dir / pdf_stem
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
        except (TypeError, IndexError, ValueError):
            top_y = 0.0
        filename = f"p{page_no}_img{idx + 1}.{ext}"
        target_dir.mkdir(parents=True, exist_ok=True)
        (target_dir / filename).write_bytes(img["image"])
        rel = f"images/{pdf_stem}/{filename}".replace("\\", "/")
        out.append((top_y, f"![]({rel})"))
    return out


def convert_document(
    pdf_path: Path,
    output_path: Path,
    *,
    page_break: bool = False,
    debug: bool = False,
    extract_images: bool = False,
    front_matter: bool = True,
) -> None:
    doc = fitz.open(pdf_path)
    profile = build_profile(doc)
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
            page, profile, images_dir=images_dir, pdf_stem=pdf_stem
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
    if s.startswith("<small>") or s.startswith("---"):
        return False
    if s.startswith("```"):
        return False
    if NUMBERED_RE.match(s):
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
    parser.add_argument("--no-front-matter", action="store_true", help="Skip YAML front matter")
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
        extract_images=args.with_images,
        front_matter=not args.no_front_matter,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
