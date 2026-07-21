# ADR-001: Canonical Markdown dialect

- Status: Accepted
- Date: 2026-06-02
- Deciders: maintainer + senior advisor panel
- Supersedes: none

## Context

md-bridge ships two converters. `pdf-to-markdown` produces Markdown; `markdown-to-pdf` consumes it. Neither had a written statement of which Markdown dialect is canonical. That gap forced a per-case decision on every feature that touches syntax: tables, task lists, strikethrough, footnotes, math. Reviews stalled on dialect questions that should be settled once, and the output risked drifting into an ad-hoc HTML-flavored dialect with no predictable surface for downstream sanitizers (GitHub, mkdocs-material, Pandoc).

The identity contract asks for open formats and a small, opinionated surface. A declared dialect serves both: it names what is in scope and gives reviewers a single anchor to cite when accepting or declining a syntax proposal.

## Decision

The canonical dialect is **CommonMark 0.31.2** plus a named set of extensions. The adopted set is split by status so a reader never mistakes a declared target for shipped behavior.

**Base**
- CommonMark 0.31.2, full spec. This is the target the output conforms to and the input the renderer is expected to accept.

**Adopted and emitted today** (produced by `pdf-to-markdown` now)
- Tables (GFM)
- Strikethrough (`~~text~~`, GFM)
- Superscript (`^x^`, Pandoc)
- Inline links (`[text](url)`)
- Fenced code with language inference
- YAML front matter, flat scalar metadata only (`title`, `author`, `date`, `source`, `pages`). Nested mappings and sequences are not part of the contract; the parser tolerates them on input but the converters neither produce nor depend on them.

**Adopted as forward targets** (in the dialect, not yet emitted by either converter)
- Task lists (`- [ ]` / `- [x]`, GFM)
- Autolinks (bare URLs and `<https://...>`, GFM). Distinct from the inline links above, which are what the converter emits today.
- Footnotes (`[^n]` reference and definition, Pandoc)
- Heading attributes (`{#slug}`, Pandoc)

A proposal that implements one of these is in scope by default and does not need a new ADR. Until implemented, citing the ADR is not proof a feature ships; check the converter.

**Raw HTML**
- The output emits no raw HTML by default. Any HTML is opt-in and capped to an inline, non-scripting allow-list. See ADR companion issue #154 and `packages/pdf-to-markdown/REFERENCE.md`. The single emission gate is `emit_html`.

**Out of scope**
- Math (default). Math support lands as an optional extra, tracked in #151, not in the base install.
- Subscript (`~x~`). No use case is tracked; only superscript is emitted today. Reconsider via an ADR amendment if a real need appears.
- Emoji shortcodes (`:smile:`)
- Abbreviations
- MathJax or any JS-rendered syntax by default

**Escaping policy**
- Literal prose that would otherwise be reparsed is backslash-escaped at emission. Inline-dangerous punctuation (`` \ ` * _ [ ] ``) is escaped at the span level (#155); line-start-only block markers (`#`, `-`/`+`/`*`, `>`, and an ordered-list `N.`/`N)`) are escaped at line-level assembly when a paragraph genuinely begins with one (#192). Detected headings, lists, and quotes carry their real marker and are never escaped.

**Renderer policy**
- `markdown-to-pdf` consumes this same dialect. Syntax outside the dialect passes through as literal characters rather than being reinterpreted. Determinism holds: the same Markdown renders to the same PDF.
- Heading input accepts both ATX (`# Title`) and setext (a text line underlined with `===` for H1 or `---` for H2). ATX is canonical and is what `pdf-to-markdown` emits; setext is accepted on input for hand-authored documents (#177).
- HTML comments (`<!-- ... -->`) pass through to the HTML output and are ignored by the PDF renderer, so they stay out of the visible page. Use them for in-source notes or build pragmas (#160). This is independent of the raw-HTML emission gate above, which governs converter *output*.

## Implementation notes (current state, 2026-06-02)

This ADR declares the target. The current implementation is close but not identical, and the deltas are recorded here honestly so contributors do not mistake intent for reality.

- `pdf-to-markdown` already emits the base plus strikethrough (`~~`, #142), superscript (`^x^`, #141), tables, fenced code with language inference, and flat YAML front matter (#150). It emits zero raw HTML (#154).
- `markdown-to-pdf` renders with python-markdown and the extensions `extra`, `sane_lists`, `smarty`, `toc`, `md_in_html`. python-markdown is a pragmatic implementation, not a certified CommonMark parser, so a handful of edge cases differ from the 0.31.2 spec.
- Known deltas to close in later work, each its own change:
  - python-markdown core does not parse GFM strikethrough or Pandoc caret superscript. A `~~` or `^x^` produced by `pdf-to-markdown` renders literally if round-tripped through `markdown-to-pdf` today. Aligning the renderer (for example via `pymdownx` equivalents) is follow-up work, not part of this ADR.
  - The `extra` bundle enables definition lists (now part of the dialect, see the #161 amendment) and abbreviations. Abbreviations stay renderer-tolerated input only; `pdf-to-markdown` does not produce them.

## Consequences

- Every syntax proposal is measured against this ADR: in scope if it aligns with the declared dialect, out of scope otherwise. Reviewers cite the ADR rather than re-deriving the boundary.
- New extensions land as an amendment to this ADR or a successor ADR (ADR-002, ...). The decision record, not a PR thread, is the source of truth.
- Closing the renderer deltas above is now visible work with a named target, instead of an implicit assumption.

## Reversibility

Documentation only. This is a single new file plus cross-link insertions. Removing it changes no runtime behavior.

## Amendments

Extensions adopted after the original decision. Each entry names the syntax, the
converter side that changed, and the issue.

### 2026-07-17 - Highlight (mark), issue #162

Added to the adopted-and-emitted set: **highlight** (`==text==`, the pymdownx-mark
syntax), rendered to `<mark>`. `pdf-to-markdown` emits it from PDF text-highlight
annotations under the opt-in `extract_highlights` option (default off, so the
default output stays byte-identical). `markdown-to-pdf` renders `==text==` to
`<mark>` through a single-rule inline extension, not the `pymdown-extensions`
package, so the lean-install contract holds. Highlight is an inline span marker
like strikethrough: the `<mark>` tag is produced by the renderer's own parser,
never passed through the `emit_html` allow-list, so the raw-HTML emission gate and
the render egress policy (#363) are untouched.

### 2026-07-17 - GFM alert callouts, issue #159

Added to the adopted set: **GFM alerts** (`> [!NOTE]`, `> [!TIP]`, `> [!IMPORTANT]`,
`> [!WARNING]`, `> [!CAUTION]`). `markdown-to-pdf` renders them as a semantic
`.callout` box (icon, localized label, body) instead of a plain blockquote, via a
single treeprocessor that rewrites a marked blockquote after parsing. The marker
must sit alone on the blockquote's first line, matching GitHub; a plain blockquote
is untouched, so existing output is unchanged. Built from real elements, not the
`emit_html` gate, so the raw-HTML policy and the render egress policy (#363) are
untouched. `pdf-to-markdown` does not yet emit this syntax; this is a renderer
(input) adoption. No `pymdown-extensions` dependency.

### 2026-07-17 - Custom containers (`::: name`), issue #164

Added to the adopted set: **pymdownx-style custom containers** (`::: warning` ...
`:::`), the admonition syntax docs sites use (MkDocs, VuePress, Hugo).
`markdown-to-pdf` maps the common names (`note`, `info`/`important`, `tip`/`hint`/
`success`, `warning`/`warn`/`attention`, `caution`/`danger`/`error`) onto the five
base callout types and renders them with the same `.callout` box as the GFM
alerts (#159), so containers and alerts share one visual vocabulary. Done with a
preprocessor that rewrites a closed container into GFM alert syntax; a stray `:::`
with no closer, or one inside a code fence, is left untouched. No
`pymdown-extensions` dependency, no new CSS. Renderer (input) adoption only.

### 2026-07-17 - Strikethrough + task-list rendering, issue #143

Closes two of the renderer deltas noted above. `markdown-to-pdf` now renders GFM
**strikethrough** (`~~text~~` -> `<del>`) and **task lists** (`- [ ]` / `- [x]` ->
a disabled GitHub-style checkbox). Both were already in the dialect - strikethrough
is adopted-and-emitted (#142), task lists a forward target now emitted by
`pdf-to-markdown` (#172) - only the renderer lagged. Strikethrough uses the same
one-line inline rule as `==mark==`; task lists use a treeprocessor that rewrites a
`[ ]`/`[x]` list item into a disabled `<input type="checkbox">`. No
`pymdown-extensions` dependency. A document without the syntax renders unchanged.

### 2026-07-21 - Grid tables, issue #166

Added to the adopted set: **Pandoc grid tables** (the `+---+` / `+===+` border
syntax). A GFM pipe table cannot hold a cell that spans several lines, so a
source table with a multi-line cell either collapses the cell to one line or
breaks the row. A grid table draws explicit borders, so the line breaks survive,
and GitHub renders it the same as a pipe table.

`pdf-to-markdown` emits a grid table under the opt-in `multiline_table_format`
option: with `"grid"`, a table that has any multi-line cell is promoted to grid
syntax, while an all-single-line table stays a pipe table. The default,
`"pipe"`, flattens as before, so the default output is byte-identical. The
emitter is pure string formatting and needs no dependency.

`markdown-to-pdf` parses grid tables through the `grids` extension
(`markdown-grids`, MIT-licensed, compatible with md-bridge's MIT license). It is
an **optional extra** (`grid-tables`), consistent with the lean-default-install
contract: the base install stays dependency-free and a grid table degrades to
literal text; installing the extra makes the renderer reparse it into a
`<table>`. This was ratified by the maintainer over the initial reviewer caution
once a round-trip (emit grid, reparse, `<table>`) was proven with a
license-compatible dependency. The GPLv3 `markdown-grid-tables` package was
rejected as incompatible with the MIT license.

### 2026-07-21 - Definition lists, issue #161

Removed from "Out of scope" and added to the adopted-and-emitted set:
**definition lists** (`Term` then `: definition`, rendered to `<dl><dt><dd>`).
The renderer already parses them through the `extra` bundle's `def_list`; this
amendment covers the converter now producing them.

`pdf-to-markdown` emits a definition list under the opt-in
`detect_definition_lists` option. Definition lists carry the highest
false-positive risk of the Phase 7 heuristics (a term looks like a short
paragraph), so the detector is deliberately strict: it fires only on a run of
at least two consecutive term/definition pairs, where each term is a single
short line (bounded by `definition_list_max_term_length`) at the body font and
size, at the body margin, with no trailing punctuation, and each definition is
a body paragraph indented into a tight band past the term (floor
`definition_list_min_indent_pt`). A heading, a styled label (which classifies
as a heading), a list item, or a sentence never reads as a term. Detection is
per page (the guards read block geometry), so a run straddling a page boundary
with fewer than two pairs on a side stays plain paragraphs there, deliberate
under-detection. Off by default, so the default output stays byte-identical.
Ratified by the maintainer.

### 2026-07-21 - OCR provenance container (`::: ocr`), issue #140

Added to the adopted set: an **OCR provenance container** (`::: ocr` ... `:::`).
`pdf-to-markdown`, under the opt-in `ocr_images` option (`auto`/`all`, default
`off`), emits the text recognized inside an embedded image as a Markdown-native
custom container right after the image, never as raw HTML: the emit gate stays
closed. `markdown-to-pdf` renders `::: ocr` as a semantic `<figure class="ocr">`
with a localized `<figcaption>` label ("Texto reconhecido (OCR)") and a body that
preserves the OCR line breaks verbatim. The renderer builds the figure (permitted:
the raw-HTML veto binds the converter, not the renderer's own output) and stashes
it as literal final HTML, so the OCR text is never reparsed as Markdown: a line
starting with `#` or `-` stays literal, not a heading or list. OCR is provenance,
not an admonition, so it carries its own neutral `.ocr` vocabulary, off the five
callout colors. The renderer loads no external resource, so the render egress
policy (#363) is untouched. Default output stays byte-identical when `ocr_images`
is off. Ratified by the maintainer.

## References

- CommonMark 0.31.2 specification: https://spec.commonmark.org/0.31.2/
- GitHub Flavored Markdown specification: https://github.github.com/gfm/
- Pandoc User's Guide (extensions): https://pandoc.org/MANUAL.html#pandocs-markdown
- `packages/pdf-to-markdown/REFERENCE.md`
- Related issues: #142, #144, #150, #151, #154
