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
- Definition lists
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
  - The `extra` bundle incidentally enables definition lists and abbreviations. They are not part of the declared dialect; they are tolerated as renderer input, not guaranteed, and `pdf-to-markdown` never produces them.

## Consequences

- Every syntax proposal is measured against this ADR: in scope if it aligns with the declared dialect, out of scope otherwise. Reviewers cite the ADR rather than re-deriving the boundary.
- New extensions land as an amendment to this ADR or a successor ADR (ADR-002, ...). The decision record, not a PR thread, is the source of truth.
- Closing the renderer deltas above is now visible work with a named target, instead of an implicit assumption.

## Reversibility

Documentation only. This is a single new file plus cross-link insertions. Removing it changes no runtime behavior.

## References

- CommonMark 0.31.2 specification: https://spec.commonmark.org/0.31.2/
- GitHub Flavored Markdown specification: https://github.github.com/gfm/
- Pandoc User's Guide (extensions): https://pandoc.org/MANUAL.html#pandocs-markdown
- `packages/pdf-to-markdown/REFERENCE.md`
- Related issues: #142, #144, #150, #151, #154
