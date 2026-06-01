# Heuristics

md-bridge converts PDF to Markdown with hand-written rules instead of a
language model. This page documents the heuristics that decide what
becomes a heading, what becomes a list item, and how tables get
recovered from PyMuPDF's geometry.

The full implementation lives in
`packages/pdf-to-markdown/scripts/convert.py`. If you are tracking a
specific decision down to a function, the section headings below name
the relevant function in that file.

## Why heuristics

A PDF has no semantic structure. It has glyphs at coordinates, font
metadata, and a binary outline tree if the author included one. There is
no "this is a heading" tag and no list semantics. md-bridge reconstructs
those decisions from what is observable: font size, font weight,
geometry, and indentation patterns.

The trade-off is honest. Heuristics give deterministic output for the
common case and fail visibly on the unusual one. A language model would
recover more documents, but the same input would not produce the same
output twice, and a bad call would be invisible. For a tool that runs
self-hosted with no telemetry, determinism wins.

## The document profile

The first pass over the PDF builds a `DocProfile`
(`convert.py:build_profile`) that captures, per document:

- **`body_size`**: the font size with the most characters across the
  whole document. This is the baseline; everything else is judged
  against it.
- **`body_font`**: the dominant font face at `body_size`. Used to
  detect "same size, different font" labels that are stylistically a
  subheading even when the geometry says paragraph.
- **`heading_thresholds`**: the three largest sizes above `body_size`,
  mapped to `H1`, `H2`, `H3`. If the document has fewer than three
  larger sizes, the missing levels collapse onto increments above the
  body size.
- **`small_size`**: anything below this is treated as a caption or
  footnote and wrapped in `<small>` instead of becoming a paragraph.
- **`body_x0` / `list_base_x0` / `indent_unit`**: the typical left
  margins for paragraphs and for first-level list items, plus the
  step used to detect nested lists.

The profile is built once per document and reused on every page. No
threshold is hard-coded against pixels; everything is relative to what
the PDF itself uses as its body.

## Heading detection

`classify_block` runs three checks in order:

1. **Font size**. If the block's dominant size clears
   `heading_thresholds[1]`, the block is `H1`. Otherwise `H2`, then
   `H3`.
2. **Section-label heuristic**. A block at exactly `body_size`, in a
   font different from the body font, two lines or fewer, eighty
   characters or fewer, and not ending in `.`, `:`, `?`, or `!` becomes
   `H3`. This catches academic templates that style section headers in
   a different face without changing the size.
3. **Bold-only short line**. A single-line block of fewer than sixty
   characters where every span is bold, not ending in `.`, `?`, or `!`,
   also becomes `H3`. This catches inline subheadings that match the
   body face but stand alone visually.

### TOC normalization

The detected heading text is then run through
`normalize_headings_from_toc`. If the PDF carries an outline (most
academic PDFs and most exported reports do), the outline is the
authoritative table of contents. When a detected heading matches a TOC
entry (by normalized text, exact or substring with a length
tolerance), the heading is replaced with the canonical title at the
TOC's level.

This fixes two common artifacts in one pass:

- Headings that wrap across two lines in the PDF get rejoined to the
  full title the author wrote.
- Heading levels that the font-size heuristic guessed wrong get
  corrected to what the outline declares.

`drop_orphan_heading_fragments` then removes lowercase one- or
two-word headings that survived the wrap, which are nearly always the
tail of a heading the TOC just absorbed.

## List recovery

Bullets and numbered items are detected at the block level by their
first character.

A block is a `bullet` if its first non-space character is one of
`▪ • ● ◦ ‣ ⁃ ∙`. The bullet glyph is stripped, the rest of the line is
re-rendered with inline styles preserved, and the block emits
`- {text}` with the right amount of indentation.

A block is `numbered` if its first non-space matches
`^\s*(\d{1,3}|[a-zA-Z])[.)]\s+`. The original numbering is kept verbatim
so cross-references in the body text still resolve.

### Nesting

`DocProfile.nesting_level` translates the block's left margin into a
nesting depth:

```
n = round((block.bbox.x0 - list_base_x0) / indent_unit)
```

The indent unit defaults to eighteen PDF points, which corresponds to
the common quarter-inch indent step. The result is clamped to the
range `[0, 5]`, so deeply nested lists do not produce arbitrary
indentation in the Markdown output.

Mixed-character bullets in the same list do not break nesting because
the level is read from geometry, not from glyph.

## Tables

Tables come from `page.find_tables()`, PyMuPDF's geometry-based table
finder. md-bridge does not run its own table detection. What it does
is clean the output, because raw `find_tables` results often have
artifacts.

`render_table` applies four passes:

1. **Strip whitespace and inline newlines** in every cell.
2. **Drop columns that are empty in every row**. This is the most
   common artifact: PyMuPDF will surface a half-pixel gutter as a
   ghost column.
3. **Merge adjacent columns that hold the same value across all rows**
   (or one is always blank when the other isn't). This collapses split
   header cells back into one.
4. **Merge wrapped continuation rows**. A row whose first cell is
   empty but other cells carry content is treated as a continuation of
   the row above, and the cells are concatenated.

The header is the first row, the alignment row is dashes, and the body
is the remainder. Cells get `|` characters escaped so the table parses
under any Markdown flavor.

### Block-in-table exclusion

A page's text blocks are not emitted directly if they sit inside a
table's bounding box (`block_in_any_bbox`). The text inside the table
has already been pulled into the rendered Markdown table; emitting it
again as paragraphs would duplicate every cell.

## Inline formatting

Per-span style detection lives on the `Span` dataclass:

- **Bold** when the PyMuPDF flag bit is set, or when the font name
  contains "Bold".
- **Italic** when the flag bit is set, or when the font name contains
  "Italic" or "Oblique".
- **Superscript** when the corresponding flag bit is set.

`render_line` merges adjacent spans that share the same style before
wrapping them, so the output is `**foo bar**` instead of
`**foo****bar**`. The latter is technically valid Markdown but renders
inconsistently across parsers.

Hyperlinks are recovered from `page.get_links()` and attached to
spans whose bounding box centre falls inside the link rectangle. The
URI is then wrapped as `[text](uri)` at render time.

## Paragraph stitching

After all pages are converted, two passes clean up paragraph and
heading wraps.

`merge_continued_paragraphs` joins adjacent blocks that look like one
paragraph wrapped into two. Triggers:

- The previous block ends in a hyphen with a letter before it
  (`self-\nconfident` becomes `self-confident`, no extra space).
- The previous block ends in a comma.
- The next block starts with a lowercase character.
- The next block starts with a common continuation word: `and`, `or`,
  `but`, `nor`, `however`, `therefore`, `thus`, `e.g.,`, `i.e.,`.

`merge_wrapped_headings` does the same for two consecutive
same-level headings, but only when the first ends in a preposition,
article, or conjunction (`the`, `of`, `for`, `and`, and so on). This
avoids merging two unrelated headings that happen to sit back-to-back
with a section break between them.

## Header and footer suppression

`is_header_footer` drops any block whose bounding box sits in the top
five percent or bottom four percent of the page. This catches page
numbers, running headers, and footers without needing to detect them
by content.

If you have a document where this rule eats real content, the
threshold lives in one place and is the right place to relax it.

## Front matter

`build_front_matter` extracts `title`, `author`, `subject`,
`keywords`, and `creationDate` from the PDF metadata and emits YAML
front matter at the top of the Markdown file. Empty fields are
omitted so the output stays clean.

Two fields are always set: `source` (the PDF filename) and `pages`
(the page count). They give the next pipeline stage something to read
without re-opening the PDF.

## What this does not do

A few things are deliberately out of scope:

- **OCR**. Scanned PDFs come back with `needs_ocr: true` from the
  inspect endpoint. The optional Tesseract pre-pass runs automatically
  when the OCR stack is installed (set `MD_BRIDGE_OCR_ENABLED=0` to force
  it off), before this converter sees the bytes; once OCR'd, the PDF goes
  through the same heuristics above.
- **Reading order across columns**. Multi-column layouts come out in
  the order PyMuPDF reports blocks, which is usually correct for
  single-column documents and best-effort for two-column academic
  papers.
- **Math**. Equations rendered as glyphs come out as text; LaTeX
  source is not reconstructed.
- **Footnotes**. They survive as `<small>` paragraphs but are not
  re-linked to their callsites in the body.

Each of these has a corresponding backlog issue. If one bites a
document you care about, that is the right place to add a regression
test fixture.
