# ADR-001: Canonical Markdown dialect

- Status: Accepted
- Date: 2026-06-02
- Deciders: maintainer + senior advisor panel
- Supersedes: none

## Context

md-bridge ships two converters. `pdf-to-markdown` produces Markdown; `markdown-to-pdf` consumes it. Neither had a written statement of which Markdown dialect is canonical. That gap forced a per-case decision on every feature that touches syntax: tables, task lists, strikethrough, footnotes, math. Reviews stalled on dialect questions that should be settled once, and the output risked drifting into an ad-hoc HTML-flavored dialect with no predictable surface for downstream sanitizers (GitHub, mkdocs-material, Pandoc).

The identity contract asks for open formats and a small, opinionated surface. A declared dialect serves both: it names what is in scope and gives reviewers a single anchor to cite when accepting or declining a syntax proposal.

## Decision

The canonical dialect is **CommonMark 0.31.2** plus a named set of extensions.

**Base**
- CommonMark 0.31.2, full spec. This is the target the output conforms to and the input the renderer is expected to accept.

**Adopted GFM extensions**
- Tables
- Strikethrough (`~~text~~`)
- Task lists (`- [ ]` / `- [x]`)
- Autolinks (bare URLs and `<https://...>`)

**Adopted Pandoc extensions**
- Footnotes (`[^n]` reference and definition)
- Heading attributes (`{#slug}`)
- Superscript and subscript (`^x^`, `~x~`)

**Adopted front matter**
- YAML front matter, flat scalar metadata only (`title`, `author`, `date`, `source`, `pages`). Nested mappings and sequences are not part of the contract; the parser tolerates them on input but the converters neither produce nor depend on them.

**Raw HTML**
- The output emits no raw HTML by default. Any HTML is opt-in and capped to an inline, non-scripting allow-list. See ADR companion issue #154 and `packages/pdf-to-markdown/REFERENCE.md`. The single emission gate is `emit_html`.

**Out of scope**
- Math (default). Math support lands as an optional extra, tracked in #151, not in the base install.
- Emoji shortcodes (`:smile:`)
- Definition lists
- Abbreviations
- MathJax or any JS-rendered syntax by default

**Renderer policy**
- `markdown-to-pdf` consumes this same dialect. Syntax outside the dialect passes through as literal characters rather than being reinterpreted. Determinism holds: the same Markdown renders to the same PDF.

## Implementation notes (current state, 2026-06-02)

This ADR declares the target. The current implementation is close but not identical, and the deltas are recorded here honestly so contributors do not mistake intent for reality.

- `pdf-to-markdown` already emits the base plus strikethrough (`~~`, #142), superscript (`^x^`, #141), tables, fenced code with language inference, and flat YAML front matter (#150). It emits zero raw HTML (#154).
- `markdown-to-pdf` renders with python-markdown and the extensions `extra`, `sane_lists`, `smarty`, `toc`, `md_in_html`. python-markdown is a pragmatic implementation, not a certified CommonMark parser, so a handful of edge cases differ from the 0.31.2 spec.
- Known deltas to close in later work, each its own change:
  - python-markdown core does not parse GFM strikethrough or task lists, and does not parse Pandoc caret superscript/subscript. A `~~` or `^x^` produced by `pdf-to-markdown` renders literally if round-tripped through `markdown-to-pdf` today. Aligning the renderer (for example via `pymdownx` equivalents) is follow-up work, not part of this ADR.
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
