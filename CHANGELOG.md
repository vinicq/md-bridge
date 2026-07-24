# Changelog

All notable changes to md-bridge are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
and this project adheres to [Semantic Versioning](https://semver.org/).
Each version section answers three questions for the reader:

- **Added** — new behaviour or files that did not exist before.
- **Changed** — behaviour or files that already existed and now work
  differently.
- **Removed** — behaviour or files that no longer exist.

If a section is empty in a release, the section is omitted entirely.

## [Unreleased]

## [0.12.0] — 2026-07-24

This release makes md-bridge safe to run as a self-hosted public service:
a same-origin deploy topology, optional access control and rate limiting,
work and queue limits with safe defaults, and a slimmer access log. The web
app also gains the Mermaid render toggle on the md-to-pdf screen.

### Added

- **Same-origin production topology.** The official deploy serves the web app
  and the API behind one origin with Caddy, and the request body cap is enforced
  at every proxy edge (nginx and Caddy), not only at the app. The deploy smoke
  check fetches the served `/` page as well as the API, so a broken web route
  fails the check. `bootstrap.sh` pins the smoke script to a ref instead of
  always running `main` as root, and creates secret files with no world-readable
  window. (#435)
- **Access control and abuse protection.** Set `MD_BRIDGE_API_TOKEN` to require a
  bearer token on the API, and `MD_BRIDGE_RATE_LIMIT` (with
  `MD_BRIDGE_RATE_WINDOW_SECONDS`, default 60) to cap requests per client IP per
  window. Both run in HTTP middleware before the upload body is parsed, so an
  unauthenticated or over-quota request is rejected (401 or 429) before it spends
  memory. Both default off, so an existing install behaves as before. The upload
  cap is now deployment-configurable via `MD_BRIDGE_MAX_UPLOAD_MB` (default 500).
  The token guards the API; a same-origin browser UI is gated by the edge proxy
  (Caddy basic-auth or SSO), not the token. (#436)
- **Work and queue limits.** Heavy conversions run behind a concurrency gate with
  a bounded wait queue and a per-request timeout, tunable via
  `MD_BRIDGE_MAX_CONCURRENCY` (default 2), `MD_BRIDGE_QUEUE_MAX` (default 8),
  `MD_BRIDGE_QUEUE_WAIT_SECONDS` (default 10), and
  `MD_BRIDGE_CONVERT_TIMEOUT_SECONDS` (default 300). A request that waits too long
  for a slot returns 503; one that exceeds the timeout returns 504.
  `MD_BRIDGE_MAX_PDF_PAGES` (default 0, unlimited) rejects an oversized PDF with
  422. (#437)
- **Render Mermaid toggle on the md-to-pdf screen.** The md-to-pdf page exposes
  the existing `render_mermaid` option as a switch, sends it to the API, and
  keeps it off by default. A fenced ```mermaid block already in the Markdown
  renders to a diagram; a block that fails to parse stays as its source code, and
  one invalid block no longer stops the valid ones from rendering. (#439)

### Changed

- **Conversion concurrency and timeout now have safe defaults.** Unlike the
  opt-in auth and rate-limit knobs, the work limits are on out of the box: at most
  two heavy conversions run at once and a conversion is capped at 300 seconds. A
  single-user local install is unaffected in practice; a busy deployment no longer
  lets unbounded parallel renders compete for memory. Tune with the env vars
  above, or set the timeout to `0` to disable it. (#437)
- **Successful health probes are dropped from the access log.** The web app polls
  `GET /api/health` about once a second, which buried real requests in the log.
  Those `200` probe lines are now filtered from the `uvicorn.access` log by
  default, while any failing probe stays visible. Set `MD_BRIDGE_LOG_HEALTH=true`
  to log every request. Ships with log-rotation guidance and an operations
  guide. (#438)

## [0.11.0] — 2026-07-22

The web app grows a settings home, a local history, and reusable presets, and
the converter learns to read text trapped inside images. Conversion defaults are
unchanged: the new converter option is opt-in and off by default, and the web
features are additive and browser-local.

### Added

- **Per-image OCR.** With `ocr_images` set to `all`, eligible embedded images are
  run through OCR and the recognized text is inlined next to each image. Only the
  50 largest candidates per document that clear a size and page-area floor and are
  not CMYK are processed, and the mode is skipped when the full-page `needs_ocr`
  pre-pass already fires (page OCR takes precedence). OCR is opt-in and not in the
  default install: `all` needs the optional OCR extra plus the
  `MD_BRIDGE_OCR_ENABLED` environment variable, and it forces inline base64 images.
  See `docs/API.md`. (#140)
- **Preferences page.** A single `/preferences` page groups four settings: default
  language, default PDF theme, dark mode, and reduce-motion. The theme and
  reduce-motion defaults persist under `md-bridge:prefs`; language and dark mode
  keep their existing `md-bridge:locale` and `md-bridge:theme` keys. Reset clears
  the whole `md-bridge:*` namespace. No server, no accounts. (#64)
- **Local conversion history.** The pdf-to-md page keeps a browser-local list of
  recent conversions (name, size, options, outcome, timestamp), capped at 20
  newest-first. Re-download a result while its blob is alive in the tab, or re-run
  from the source file. The list is metadata only: the source file and result blob
  are never written to `localStorage` or any server-side store, and the file a
  conversion uploads is processed in a temporary directory and then discarded. (#63)
- **Conversion presets.** The md-to-pdf page can save the current theme and
  custom CSS as a named preset under `md-bridge:presets:md-to-pdf` and re-apply
  it in one click, with JSON import and export to share a set. Capped at 12 per
  format pair. (#62)

## [0.10.0] — 2026-07-21

Seven converter heuristics, each opt-in and off by default, so a document
converted with the defaults is byte-identical to 0.9.0.

### Added

- **Table column alignment.** With `table_column_align` on, the converter reads
  each column's text extent and emits the GFM alignment markers (`:---`, `---:`,
  `:---:`) in the separator row. It classifies by comparing the left and right
  gaps, so left-aligned multi-word text is not misread as centered. (#175)
- **Tight and loose list spacing.** With `tight_loose_lists` on, the converter
  reads the vertical gaps between PDF list items and preserves them as
  CommonMark tight or loose lists. `list_loose_threshold` (default 1.5x the
  dominant body font size) sets where a gap counts as loose. (#168)
- **Image width hints.** With `image_width_hints` on, an extracted image carries
  its source width as an attr-list hint (`{width=N}`). The width is converted
  from PDF points to CSS pixels (x96/72), so a round-trip through the renderer
  keeps the image at its original size instead of shrinking it. (#169)
- **Image click links.** With `image_link_anchors` on, an image that the PDF
  wraps in a click action is emitted as `[![alt](src)](target)`, preserving the
  link through the conversion. The three document post-passes (smart typography,
  reference-link collapsing, and the needs_ocr text-density check) recognize the
  construct and operate on the external target, never the image source. (#170)
- **Nested ordered lists.** With `nested_ordered_lists` on, a nested ordered
  sublist keeps its own first-item start and indents four spaces per level so
  the renderer nests it (`<ol start="N">`). Depth is measured from the list's
  outermost margin, so a sublist with more items than its parent still nests.
  (#194)
- **Grid tables.** With `multiline_table_format` set to `grid`, a table that has
  any cell spanning more than one line is emitted as a Pandoc grid table so the
  line breaks survive; an all-single-line table stays a pipe table. Rendering a
  grid table back to a PDF needs the optional `grid-tables` extra
  (`markdown-grids`, MIT). Adopted in ADR-001. (#166)
- **Definition lists.** With `detect_definition_lists` on, a run of at least two
  term/definition pairs (a short body-font term at the margin, then an indented
  body definition) is emitted as `Term` / `: definition`, rendered to
  `<dl><dt><dd>`. The detector is deliberately strict to keep false positives
  low: a heading or a styled label classifies as a heading and is excluded, and
  the run, length, font, and indent guards make ordinary prose unlikely to read
  as a term. `definition_list_max_term_length` and `definition_list_min_indent_pt`
  tune the bounds. Adopted in ADR-001. (#161)

### Changed

- **Dependencies.** Bumped the nginx base image digest (#425), the web
  `typescript-eslint` group (#426), `@testing-library/jest-dom` to 7 (#427), the
  CI actions group (#428), and `actions/setup-python` to 7 (#429).

## [0.9.0] — 2026-07-17

### Added

- **Highlighted text round-trips.** `pdf-to-markdown` reads PDF text-highlight
  annotations and emits the covered text as `==text==`; `markdown-to-pdf` renders
  `==text==` to `<mark>`. Opt-in via `extract_highlights` (off by default, so a
  document without highlights is byte-identical). A span whose text already holds
  `==` is left unmarked so the delimiter cannot break. (#162)
- **Figure anchors.** With `emit_figure_anchors` on (off by default), a numbered
  figure caption (`Figure 3`, `Fig. 2.1`, `Figura 5`) gives its image a stable
  `{#fig-N .figure}` id, so a cross-reference can link to it. Ids dedupe across
  the document and against heading anchors. Only figures: the renderer cannot
  attach an id to a table, tracked in #414. (#165)
- **GFM alert callouts.** `> [!NOTE]`, `> [!TIP]`, `> [!IMPORTANT]`,
  `> [!WARNING]`, and `> [!CAUTION]` render as a bordered box with an icon and a
  localized label (EN/PT/ES) instead of a plain blockquote. A blockquote without
  a marker is untouched. (#159)
- **Custom containers.** `::: warning` ... `:::` blocks (the MkDocs/VuePress
  admonition syntax) render as the same callout box; the common names map onto
  the five types. (#164)
- **Strikethrough and task lists in the PDF.** `~~text~~` renders as `<del>` and
  `- [ ]` / `- [x]` render as a disabled GitHub-style checkbox, closing two of
  the renderer deltas the dialect ADR named. (#143)

## [0.8.0] — 2026-07-16

### Added

- **Theme library page.** `/themes` is now a full catalogue: a grid of every
  theme from the API, a family filter (serif / sans / mono), a live preview that
  stacks the theme (and optional custom CSS) over the base in an isolated frame,
  a read-only view of the theme CSS, and buttons to use a theme or download its
  `.css`. The preview renders realistic samples (article, resume, email,
  contract, blog) so a theme can be judged against real content. (#392, #398)
- **Ten new PDF themes.** letter, manuscript, newsprint, notebook, novel,
  resume, slate, slides, techbook, and whitepaper, bringing the catalogue to 21.
  Each is a CSS overlay on the base stylesheet. (#393)
- **Mermaid diagrams in md-to-pdf.** A `mermaid` code fence renders to a diagram
  at print time through a vendored bundle, so it works offline and
  deterministically with no CDN. Opt-in via `render_mermaid` (off by default; a
  document without the option renders exactly as before). (#394)
- **Live theme preview in md-to-pdf.** Before converting, the pasted Markdown is
  shown styled by the selected theme, so the theme's effect is visible without a
  round-trip. (#397)
- **Custom CSS in md-to-pdf.** An optional CSS block layers after the theme,
  shown live in the preview and applied to the PDF. Empty by default, so output
  is unchanged when unused. (#395)
- **Format-matrix status filter.** The conversion matrix on Home filters by
  status (All / Shipped / Roadmap / Wanted), each with a count. (#396)

## [0.7.0] — 2026-07-16

### Added

- **Generated OpenAPI TypeScript client.** The web app's request and
  response types come from the FastAPI schema now instead of being
  hand-typed. `python -m app.export_openapi` snapshots the schema to
  `apps/web/src/lib/openapi.json`, and `npm run gen:api` turns it into
  `apps/web/src/lib/api-types.ts`. A CI step regenerates both and fails on
  any diff, so a backend schema change that skips the regen cannot land.
  (#32)
- **Styled blockquotes in the Markdown preview.** Quotes emitted by
  `detect_blockquotes` render with an accent left side-rule, a soft accent
  tint, and muted italic text instead of the browser default. Quoted text
  and quoted links both meet WCAG AA in light and dark. (#218)

## [0.6.0] — 2026-07-15

### Added

- **Self-contained Markdown with inline images.** `pdf-to-md` can embed
  extracted images as base64 `data:` URIs instead of dropping them or
  writing sidecar files, so a single `.md` travels intact. The API
  `with_images` flag turns it on and the CLI exposes `--inline-images`.
  (#372, #373)
- **GFM task lists.** Source checkbox glyphs map to `- [ ]` / `- [x]`
  items behind `detect_task_lists`, off by default so output stays
  byte-identical. (#172)
- **OCR page cap.** `MD_BRIDGE_OCR_MAX_PAGES` bounds how many pages the OCR
  pre-pass rasterizes on a shared or hosted deployment; `0` (the default)
  keeps it unbounded. (#208)
- **OCR per-page timeout.** `MD_BRIDGE_OCR_PAGE_TIMEOUT` (default 60s)
  bounds how long a single page's Tesseract run may take. A timed-out page
  returns `ocr_failed` naming the page instead of pinning the worker
  thread. (#364)
- **Keyboard-dismissable toasts.** Success and warning toasts carry a
  focusable, localized close button that also pauses the auto-dismiss
  while it has focus. (#355)

### Changed

- **The Markdown to PDF renderer is offline-only.** It no longer fetches
  external resources and blocks network egress, WebSocket, popup, and
  `file:` escapes, so a hostile Markdown document cannot reach the network
  or the filesystem through Chromium. (#363, #369, #371)
- **Batch keyboard reorder is discoverable and standards-based.** Rows
  describe the Space-to-grab, arrow-to-move interaction through
  `aria-describedby` and announce each move in a live region, replacing
  the deprecated `aria-grabbed`. (#358)
- **Batch and chrome strings are fully localized.** The remove and reorder
  controls, the theme toggle, the spinner label, and unknown-error text
  come from the typed en/pt/es catalog instead of leaking English or
  Portuguese. (#354)
- **Uploads are read once instead of buffered twice.** The upload reader
  reads the parsed upload a single time, bounded at the size cap, instead
  of growing a bytearray and copying it into bytes, roughly halving peak
  memory. (#365)

### Fixed

- **`Content-Disposition` is well-formed for any filename.** The download
  header strips quotes, CR/LF, and path separators from the name and adds
  an RFC 5987 `filename*`, closing a header-injection path. (#362)
- **Invalid options return `422`, not `500`.** A rejected `allow_html`
  value no longer crashes the error handler while it serializes the
  validation error. (#361)
- **A corrupt or non-PDF upload returns the `422` error envelope** instead
  of a plain-text `500`. (#360, #370)
- **The success toast no longer fires over a failed batch,** and it
  survives parent re-renders instead of resetting its timer on every
  keystroke. (#353, #355)
- **Removing a batch item mid-run** aborts its in-flight request and
  unschedules it instead of finishing discarded work invisibly. (#357)
- **A persisted theme slug missing from the server catalog** falls back to
  `default` instead of leaving the picker unselected and posting a stale
  slug. (#356)
- **The drop-zone highlight no longer flickers** while the pointer drags
  over child elements. (#359)

## [0.5.0] — 2026-07-08

### Added

- Converter refinements: caption-derived image alt text (#149),
  smart-typography ASCII folding for quotes, ellipses, and dashes (#171),
  an abbreviation glossary emitted as `*[abbr]:` definitions (#163), quote
  attribution paired with the blockquote above it (#173), deterministic
  heading-anchor slugs (#152), reference-style links for repeated URLs
  (#158), and autolinks for bare URLs and emails (#157).

### Changed

- The `/pdf-to-md` page replaces the compare and options panes with a
  batch queue and drag-to-reorder. (#294, #304)

See the [v0.5.0 release](https://github.com/vinicq/md-bridge/releases/tag/v0.5.0)
for the full list.

## [0.4.0] — 2026-06-08

### Added

- **Theme system for Markdown → PDF.** A request can now pick a visual
  theme through `options.theme`; `GET /api/themes` lists the registered
  themes and `GET /api/themes/{slug}/css` serves a theme's stylesheet.
  Three themes ship alongside the neutral `default`: **academic** (serif,
  justified body, decimal section numbering), **business** (sans-serif,
  red accent masthead and table headers), and **minimal** (low-chrome
  draft layout, rule-only tables). Each theme is a CSS overlay stacked on
  `default.css`, so it carries only its own identity and inherits a
  complete base layout. An unknown slug returns `400 unknown_theme`.
  (#23 registry + endpoints, #22 CSS templates)
- **Markdown to DOCX.** A `/convert/md-to-docx` page and `POST
  /api/md-to-docx` render Markdown to a deterministic Word document, with
  a format-pair registry behind `GET /api/formats`. (#60, #271, #279)
- **Per-request page setup** for Markdown to PDF: page size, margins, and
  a running header/footer. (#243, #272, #275)
- Heading detection reaches H4-H6 (#234), hard line breaks are preserved
  (#232), recurrent page headers and footers are subtracted (#221), font
  sizes cluster into heading bands (#220), and the docs site ships in
  three languages (PT, ES) with a selector. (#29)

See the [v0.4.0 release](https://github.com/vinicq/md-bridge/releases/tag/v0.4.0)
for the full list.

## [0.3.0] — 2026-06-01

Minor release. Two converter behaviour changes lead the headline: the OCR
pre-pass now runs **automatically when the OCR stack is installed** (no flag),
and pdf-to-markdown now emits **pure Markdown** instead of raw `<small>` and
`<sup>` HTML tags. The release also ships automatic trilingual OCR (English,
Portuguese, Spanish), GFM strikethrough detection, four list and front-matter
conversion fixes, and the docs build-out (heuristics, FAQ, API recipes,
deployment recipes). The lean default install is unchanged: no OCR binary, no
behaviour shift, a scan still returns `422 ocr_required`.

### Added

- **Automatic multi-language OCR (English, Portuguese, Spanish).** The
  opt-in OCR pre-pass now defaults to `eng+por+spa`, so a scanned
  document in any of the three is read without configuring a language
  per document; Tesseract scores each region across the three models,
  which is deterministic. Spanish (`tesseract-ocr-spa`) is added to the
  OCR Docker image, the CI Tesseract install, and the docs. PT-PT and
  PT-BR share the single `por` model. `MD_BRIDGE_OCR_LANG` still pins a
  language. A narrower per-document auto-detect is a follow-up. (#199)
- **GFM strikethrough in pdf-to-markdown.** Text struck through in the
  source PDF (a line drawn across the glyphs) now converts to
  `~~text~~` instead of dropping the semantic. PyMuPDF surfaces the
  stroke on the span's `char_flags` when the page is read with
  `TEXT_COLLECT_STYLES`; the detection is version-gated, so an older
  PyMuPDF degrades to "no strikethrough" rather than misbehaving.
  Strikethrough nests outside emphasis (`~~**text**~~`). (#142)
- **Optional Tesseract OCR pre-pass for scanned PDFs** by @0exec
  (first external contribution from this account). New
  `apps/api/app/services/ocr.py` runs when `MD_BRIDGE_OCR_ENABLED=1`
  and the inspect diagnostics report `needs_ocr: true`. PDFs that
  already carry a text layer skip OCR entirely. Response payload
  gained `ocr_applied: bool`. New Docker stage `runtime-ocr` (lean
  default `runtime` stage unchanged), `[ocr]` extras in
  `pyproject.toml`, and CI installs `tesseract-ocr` for the
  integration tests. (#86, closes #5)
- **Descriptive iframe title on the PDF preview** by @zhouzhou626
  (third PR landed by this contributor). New
  `mdToPdf.previewIframeTitle` dictionary key across EN, PT-BR, ES,
  bound at `apps/web/src/pages/MdToPdf.tsx:119`. Screen readers
  now announce "Generated PDF preview, frame" instead of inheriting
  the page heading. WCAG 4.1.2 (Name, Role, Value). (#87, closes #72)
- **Heuristics documentation page** at `docs/heuristics.md`:
  document profile, heading detection, TOC normalization, list
  recovery, table cleanup, inline formatting, paragraph stitching,
  header/footer suppression, front matter, and the deliberately
  out-of-scope items. Each section names the function in
  `packages/pdf-to-markdown/scripts/convert.py`. (#92)
- **FAQ page** at `docs/faq.md`: why OCR is opt-in, why the
  converter persists nothing, how to add a new locale, heuristics
  vs language model, Playwright + headless Chromium trade-off,
  server-side vs client-side conversion, offline operation. (#93)
- **API recipes page** at `docs/api-recipes.md`: copy-paste recipes
  for the four HTTP endpoints from curl, Python requests, and
  JavaScript fetch (browser + Node), plus error-envelope reading,
  CORS configuration, and rate-limit guidance. (#97, closes #26)
- **Deployment recipes page** at `docs/deployment-other.md`:
  Render, Fly.io, and Railway walkthroughs with blueprints, free-tier
  caveats, and a consolidated common-gotchas section
  (`VITE_API_URL` build-time, CORS, cold-start timeouts, 500 MB
  upload cap). (#98, partial fix for #7)

### Changed

- **OCR runs by default when the stack is installed.** Previously the
  OCR pre-pass only ran with `MD_BRIDGE_OCR_ENABLED=1`. Now installing
  the OCR stack (the `[ocr]` extra plus the Tesseract binary, or the
  `runtime-ocr` image) is itself the opt-in: a scanned PDF is OCR'd
  automatically, with no flag. A lean install without the stack carries
  neither the binary nor the binding, so OCR stays off and a scan still
  returns `422 ocr_required` — the lean default is unchanged.
  `MD_BRIDGE_OCR_ENABLED` now overrides the auto decision both ways:
  `1`/`true` forces on, `0`/`false` forces off. (#207)
- **pdf-to-markdown emits pure Markdown instead of raw HTML tags.**
  Small-font blocks (captions, footnotes, copyright lines) now render
  as plain paragraphs instead of `<small>...</small>`, and superscript
  spans render as Pandoc `^x^` instead of `<sup>...</sup>`. This keeps
  the output clean for RAG pipelines, plain Markdown viewers, search
  indexers, and Pandoc. The size hint on small text is dropped (Markdown
  has no clean equivalent); literal carets in prose are left bare. The
  `needs_ocr` payload warning no longer strips a `<small>` wrapper that
  is no longer emitted, so small-font text now counts as content (the
  hard `ocr_required` gate is unaffected — it reads raw PDF chars).
  Opt-in raw-HTML preservation is deferred to the allow-list policy.
  (#141, follow-ups #154 and #148)
- **Contribution-guide section in every open issue body.** All 27
  open issues now carry a standardized "How to contribute" block
  covering claim workflow, branch naming, Conventional Commits,
  test pyramid, no AI co-authors, squash merge, and reversibility
  declaration. The section is idempotent: re-running the batch
  skips issues that already carry it.
- **Scorecard exceptions doc** (`docs/scorecard-exceptions.md`)
  updated to cover the three new Pinned-Dependencies paths
  introduced by the OCR pipeline (`apps/api/Dockerfile:49,60` and
  `.github/workflows/ci.yml:28`) plus a new Maintained section
  documenting the time-based auto-resolution. (#90)
- **Contributors recognition**: @zhouzhou626 gains the `a11y`
  type (#88); @0exec joins the contributors block with `code`,
  `doc`, `test`, `infra` types (#89). Avatar URLs use numeric ID
  form so username changes do not break the links.

### Removed

- **Orphan `useConvert.ts` hook** at `apps/web/src/hooks/`.
  Declared `usePdfToMd()` and `useMdToPdf()` but had zero
  callsites. Pages call the API functions directly from
  `src/lib/api.ts`; the batch flow uses `useBatchConvert`. The
  hook was superseded during early development. (#91)
- **Unused `docs/brand/social-preview.png` asset**. Not referenced
  from `mkdocs.yml`, README, any markdown, or any HTML meta tag.
  No `og:image` is wired in the docs site or the React app. (#91)
- **Dead `mkdocs.yml` nav entry** that pointed at
  `docs/deployment/oracle-cloud.md`, which never existed in repo
  history. Replaced with the new `Deploy: deployment-other.md`
  entry so MkDocs builds without the orphan-page warning. (#98)

### Fixed

- **Multi-paragraph list items no longer collapse.** A list item that
  spanned more than one paragraph in the PDF used to emit the second
  paragraph at top level, splitting the list. The page assembly now
  tracks the open item and nests a paragraph indented past the marker
  inside the `<li>`. (#167)
- **Code blocks under a list item stay in the item.** A fenced code
  block indented past the marker used to escape to top level and split
  the list; it now nests inside the item as an indented code block
  (the shipped renderer does not nest a fence at the content column, so
  the language hint is dropped for the nested case). (#197)
- **YAML front matter keeps list, nested, and multi-line values.** The
  markdown-to-pdf reader parsed front matter with a hand-written
  split-on-colon loop that flattened or dropped anything that was not a
  flat `key: value`; it now uses PyYAML, with the block hardened against
  a billion-laughs / deep-nesting denial of service. (#150)
- **A full-width rule is no longer misread as strikethrough.** PyMuPDF's
  strikeout flag fires for any horizontal line or thin rule crossing text
  at mid-height, including a page rule or section divider. The converter
  now cross-checks the drawn geometry: a stroke that overruns the span
  toward the margins is a rule, not a strike, so the spurious `~~` is
  dropped. A genuine strike (a line spanning the struck text) still
  converts. (#202)

## [0.2.3] — 2026-05-20

Minor release. Headline change is the **first external contribution**:
@ko4lax landed the WCAG 2.1 AA audit and remediation in PR #54. The
release also ships the new design system catalogue (PRs #58 + #65)
that future UI work tracks back to, plus the trilingual screenshots
refresh, the Spanish locale page tests, the all-contributors adoption,
and a handful of CI hygiene fixes accumulated since `v0.2.2`.

### Added

- **WCAG 2.1 AA accessibility audit and remediation** by @ko4lax (first
  external contributor on the project). `DropZone.tsx` refactored so
  the file input is a sibling of the `role="button"` wrapper instead of
  nested inside it (closes the axe nested-interactive-controls
  violation); skip-to-content link added in `App.tsx`; nav landmark
  labelled `Main navigation`; batch progress carries an
  `aria-live="polite"` announcement. New `docs/accessibility-audit.md`
  documents findings with WCAG identifiers (`wcag2a`, `wcag2aa`,
  `wcag21a`, `wcag21aa`) and reproduction steps. New
  `apps/web/e2e/audit.spec.ts` wires `@axe-core/playwright` into the
  existing E2E job so CI fails on critical or serious violations
  going forward. (#54, closes #36)
- **`docs/design/` design system catalogue.** Self-contained HTML
  (`design-thinking.html`) with hi-fi mockups and paste-ready issue
  specs for eight features: F1 CSS theme picker, F2 theme library,
  F3 per-conversion options panel, F4 format hub (DOCX/EPUB/HTML/RTF),
  F5 language workshop, F6 conversion presets, F7 local history, and
  F8 preferences page. The HTML reuses
  `apps/web/src/styles/tokens.css` verbatim so visual changes to the
  React app propagate to the catalogue. Published with the docs site
  at [/design/](https://vinicq.github.io/md-bridge/design/); MkDocs nav
  now includes a Design system entry; CONTRIBUTING.md routes
  contributors who pick up `design-required` issues at the catalogue
  first; README gains a dedicated Design system section above Limits.
  Seeds six new feature issues (#59 F3, #60 F4, #61 F5, #62 F6, #63 F7,
  #64 F8). (#58)
- **`docs/design/screenshots/` retina captures** (1440x900 at 2x device
  scale) of every catalogue section: hero, principles, foundations,
  roadmap, plus F1..F8 mockup spreads. The design landing page and the
  GitHub-view README render the gallery so contributors preview the
  catalogue before opening the HTML. (#65)
- `docs/screenshots/home-es.png` Spanish home-page screenshot at the
  same 2880x1800 retina resolution as the EN and PT companions.
  README's screenshot section now shows the trilingual UI in a
  3-column table (EN / PT / ES). `docs/screenshots/demo.gif` was
  regenerated with the three locales at the start so the README hero
  shows the trilingual capability before the conversion flow. (#49)
- Spanish locale coverage added to the page-level integration tests:
  `About.test.tsx` asserts the ES title, `Home.test.tsx` asserts the
  ES hero headline, and `Navigation.test.tsx` flips the whole UI to
  ES via the language toggle and asserts both the headline and the
  About link translate. The Portuguese tests stay in place. (#49)
- **all-contributors** specification adopted. `.all-contributorsrc` at
  the repo root tracks every contributor and their kind of
  contribution (code, doc, translation, design, review, test, infra,
  maintenance). README gains a `## Contributors` section between
  `## License` and `## If md-bridge helped you` that renders the
  current list. `CONTRIBUTING.md` documents how to be credited: no bot
  to install, no extra PR; the maintainer regenerates the README block
  during release prep. (#48)
- `@ko4lax` credited as a contributor with categories `code`, `doc`,
  `test`, `infra`, `translation` per the diff classification in PR
  #54. Avatar URL uses the numeric-ID form per the maintainer credit
  rule. (#67)
- `.github/workflows/pr-linked-issue.yml` posts a single one-line
  comment on every issue closed via "Closes #N" naming the PR author,
  so attribution survives in the casual reader's view. (#56, refined
  in #57)

### Changed

- All `docs/screenshots/*.png` refreshed at the current 2880x1800
  retina resolution from the post-v0.2.2 UI state (after the About
  rewrite, the extensibility positioning, and the warning i18n fix).
  The `pdf-to-md`, `pdf-to-md-batch`, `md-to-pdf`, `about`, and
  `swagger` captures now match the UI a contributor sees today.
  `demo.gif` was regenerated with eight frames covering the
  trilingual home pages and the full conversion flow. (#51)
- `Validate PR title` is now a **required** status check on `main`.
  Previously the Conventional Commits validation ran on every PR but
  did not block the merge if it failed (caught when PR #49 merged
  with the malformed scope `feat(web,docs):` despite a red title
  check). Branch protection now requires every PR title to parse
  cleanly as `<type>(<scope>)<!>: <description>` before the merge
  button enables. CONTRIBUTING.md's branch-protection list is updated
  to include the sixth required check. (#50)
- CONTRIBUTING.md regression test guidance promoted from a single
  paragraph to a step-by-step checklist under "Writing a good
  regression test". Documents the failing-diff format, tier choice,
  fixture vs synthetic input, and the no-silent-skips rule with a
  worked example from PR #20. (#52)
- `@zhouzhou626`'s entry in `.all-contributorsrc` switched to the
  numeric-ID avatar URL (was producing identicon fallback) and gained
  the `doc` contribution credit for PR #52. CONTRIBUTING.md codifies
  the post-merge maintainer credit rule as a five-step mechanical
  checklist any future maintainer (or AI assistant) can apply without
  judgement. (#53)

### Fixed

- `MdToPdf.tsx` was passing `t.pdfToMd.ready` ("Ready" / "Pronto" /
  "Listo") to the `ConvertButton`'s `success` label slot instead of
  the page-owned `t.mdToPdf.success` ("PDF ready." / equivalents).
  The branch was unreachable under the current
  `status={batch.running ? 'loading' : 'idle'}` state machine, so no
  user saw the wrong copy, but the dead path would have surfaced the
  next time anyone wired the success state. Aligned to the correct
  key. (#66)

## [0.2.2] — 2026-05-19

Patch release. Headline change is the trilingual warning fix; the rest is
governance, infrastructure, and documentation polish accumulated since
`v0.2.1`.

### Fixed

- **`/api/pdf-to-md` warnings now follow the active UI locale.** The
  backend used to emit hardcoded English strings ("Very little text was
  extracted…"); PT and ES users saw English while the rest of the UI
  was in their locale. Backend emits stable codes (`needs_ocr`,
  `images_not_persisted`); the frontend dictionary translates per
  locale. The lookup falls back to the raw string for unknown codes so
  future warnings stay forward-compatible. (#40, PR #42)
- `apps/api/app/main.py` Swagger metadata pointed `contact.url` and
  the `API_DESCRIPTION` markdown link at the placeholder
  `https://github.com/your-org/md-bridge`. The Swagger UI at `/docs`
  surfaced both. Replaced with the real repository URL. (PR #46)
- `docker-publish.yml` smoke test for the Web image was running
  `nginx -t` against the bundled config, which contains
  `proxy_pass http://api:8000`. In an isolated container the `api`
  hostname does not resolve, so the parse failed and the workflow
  reported a red CI even though the publish itself succeeded. The
  smoke now asserts that the Vite build stage produced `index.html`
  and copied it to the nginx web root. (PR #20)

### Added

- **Conventional Commits 1.0.0** is now the project's commit and
  PR-title convention. New CI workflow `semantic-pr.yml` rejects PR
  titles that do not match `<type>(<scope>)<!>: <description>`.
  `CONTRIBUTING.md` gains a full reference section with the recognised
  types, bump rules, and worked examples. The `release-drafter.yml`
  config gains an `autolabeler` block. (PR #19)
- `CONTRIBUTING.md` now documents the **issue-claiming process**:
  contributors comment to claim, maintainer assigns via the native
  GitHub `assignee` field, seven-day window before the issue returns
  to the pool. (PR #41)
- Issue templates (`bug_report.md`, `feature_request.md`) now require
  a **test plan with explicit file paths and tiers**. Feature template
  also gains Architect and Design notes sections so the
  tri-disciplinary review pattern shows up before the issue is filed.
  (PR #43)
- `docs/screenshots/warning-i18n.png` visual proof for #40 (deterministic
  Pillow render, no AI image generation). (PR #45)

### Changed

- Pre-commit hooks moved from a separate "Optional" section near
  Tests to **Local setup** in `CONTRIBUTING.md` so new contributors see
  them at the same moment they install Python and Node. The "Strongly
  recommended" framing replaces "Optional". A new paragraph explains
  that the hooks deliberately do not check branch staleness; branch
  protection on `main` ("require branches to be up to date before
  merging") handles that server-side. PR template checklist gains the
  two matching items. (PR #44)
- Project descriptions across `package.json`,
  `apps/api/pyproject.toml`, `README.md`, and `docs/index.md` now state
  the extensibility intent explicitly: md-bridge is a document
  converter that ships PDF ↔ Markdown today and welcomes new format
  pairs as contributions land. The GitHub repo description and topics
  were updated to match. (PR #39)
- About page copy rewritten across `en`, `pt`, and `es` in an
  OSS-professional register. New copy leads with positioning
  ("open source, self-hosted, deterministic, no model inference, no
  telemetry") and names the heuristic stack (PyMuPDF + headless
  Chromium) directly. "Built with" becomes "Open source" with explicit
  MIT-licence and `CONTRIBUTING.md` pointers. (PR #21)
- Theme picker for Markdown → PDF (#14) reorganised as an **umbrella
  issue** with three sister sub-issues: design (#22, CSS templates),
  backend (#23, registry + `/api/themes`), frontend (#24, picker
  dropdown). The pattern is now the project's reference for
  multi-discipline features.

## [0.2.1] — 2026-05-19

### Fixed

- `docker-publish.yml` now builds **multi-platform** images
  (`linux/amd64` + `linux/arm64`). The Oracle Cloud Always Free
  deployment recipe targets ARM Ampere A1 VMs but the previous
  amd64-only publishes failed `docker pull` on ARM hosts with a
  manifest-mismatch error. Apple Silicon developers were affected by
  the same issue. A post-publish smoke job verifies both arches by
  pulling the image and running a minimal probe. (#12)

## [0.2.0] — 2026-05-19

First minor release. Ships the new trilingual UI plus a wider set of
visibility, distribution, and contributor-onboarding work.

### Added

- **Spanish (`es`) locale** in the web UI. The header toggle now lists
  EN / PT / ES. Locale detection and the `<html lang>` attribute were
  generalised so future locales drop in without further code changes.
  Translations are native-quality; tests and the Playwright spec
  exercise all three locales. (#9 by @zhouzhou626 — first external
  contributor.)
- **Oracle Cloud Always Free deployment recipe** under
  `deployment/oracle-cloud/`: step-by-step `README.md`, `bootstrap.sh`
  that installs Docker + Caddy + the stack on a fresh ARM Ampere A1
  VM, and a reference `Caddyfile.example`. Cost: zero. The docs site
  picks up the page under a new "Deploy" nav section.
- **Release-drafter** workflow that keeps a draft GitHub Release in
  sync with merged PRs on `main`. Categories are driven by PR labels
  (`enhancement`, `bug`, `security`, `documentation`, `chore`, ...)
  and the next semver bump is resolved automatically (major / minor /
  patch). Config in `.github/release-drafter.yml`.
- `workflow_dispatch` trigger on `docker-publish.yml` so a manual
  re-publish from the Actions UI is now possible without an unrelated
  commit.
- **Documentation site** at <https://vinicq.github.io/md-bridge/>.
  MkDocs Material build deployed to GitHub Pages on every doc change.
  `mkdocs.yml` plus `docs/index.md` and `docs/getting-started.md`
  provide a curated landing experience separate from the GitHub README.
- **Docker images on GHCR**: a release-triggered workflow publishes
  `ghcr.io/vinicq/md-bridge-api` and `ghcr.io/vinicq/md-bridge-web` so
  users can `docker pull` instead of building locally. Tags follow the
  semver scheme; both images are public.
- **OpenSSF Scorecard** workflow that runs weekly + on push, surfaces
  the result in the Security tab, and exposes a public score at
  scorecard.dev. README gains a Scorecard badge alongside CI and
  CodeQL.
- **Brand assets** under `docs/brand/` (logo, wordmark, social
  preview). Programmatic Pillow geometry, deterministic, no AI
  generation.
- **Demo GIF** at `docs/screenshots/demo.gif`, used as the README
  hero.
- **Star history chart** and a "If md-bridge helped you" CTA at the
  bottom of the README.

## [0.1.1] — 2026-05-19

Maintenance and governance release. No behaviour changes in the
converter; only infrastructure, security posture, and contributor
ergonomics.

### Added

- Optional `pre-commit` configuration that runs `ruff` and basic
  hygiene hooks (trailing whitespace, EOF newline, YAML/TOML syntax,
  merge conflict markers, large files) before every commit. Documented
  in `CONTRIBUTING.md`.
- `.github/workflows/dependabot-auto-merge.yml` enables `gh pr merge
  --auto` for Dependabot PRs that are patch bumps (`X.Y.Z → X.Y.Z+1`)
  or transitive (indirect) dependency updates. Branch protection still
  gates the actual merge on every required status check; minor and
  major bumps stay in the manual review queue.
- Branch protection on `main` documented in `CONTRIBUTING.md`:
  required status checks for Backend, Web, End-to-end, and the two
  CodeQL jobs; force-push and deletion blocked; linear history
  required.
- `SECURITY.md` now lists the GitHub-native defenses that are active
  on the repository so contributors know what they get for free
  (secret scanning, push protection, CodeQL, Dependabot, private
  vulnerability reporting).

### Changed

- GitHub Actions bumped to current majors: `actions/checkout` v4 → v6,
  `actions/setup-python` v5 → v6, `github/codeql-action` v3 → v4,
  `actions/setup-node` v4 → v6, `actions/upload-artifact` v4 → v7.
  Clears the Node.js 20 deprecation warnings on the runner.
- Docker base images bumped: web `node:22-alpine` → `node:26-alpine`,
  web runtime `nginx:1.27-alpine` → `nginx:1.31-alpine`.
- npm devDependencies bumped: `typescript-eslint` 8.59.3 → 8.59.4
  (patch), `@types/node` 24.12.4 → 25.9.0.

### Security

- Enabled GitHub-native repo features via API: secret scanning, push
  protection, private vulnerability reporting, vulnerability alerts,
  Dependabot security updates.
- Branch protection on `main` requires every CI and CodeQL status
  check to pass before a merge can land.

## [0.1.0] — 2026-05-19

First tagged release. md-bridge is a self-hosted PDF and Markdown
converter with a FastAPI backend and a React frontend.

### Added

- **PDF to Markdown** conversion with heading detection, list recovery,
  table extraction, and YAML front matter.
- **Markdown to PDF** rendering through headless Chromium with a bundled
  A4 stylesheet.
- **Batch mode** in the UI: drop one file or a whole folder; each file
  is converted sequentially and can be downloaded as it lands.
- **`/api/inspect-pdf`** endpoint returns diagnostics (fonts, sizes,
  tagged-PDF flag, OCR hint) so the UI can warn before conversion.
- **Bilingual UI** in English (default) and Portuguese, with the choice
  persisted to `localStorage`.
- **Interactive API docs** at `/docs` (Swagger UI) and `/redoc`, plus a
  walkthrough in [`docs/API.md`](docs/API.md).
- **Docker Compose stack** for one-command boot of API + Web with
  healthchecks.
- **Test pyramid** with 124 tests (92 unit, 26 integration, 6 end-to-end),
  every one of which runs on CI against the committed ISTQB CTAL-TA
  syllabus fixture. No silent CI skips.
- **CI workflow** for backend pytest, web build + lint + vitest, and
  Playwright end-to-end.
- **CodeQL** static security analysis on every push and pull request,
  with a weekly scheduled scan, covering both Python and TypeScript.
- **Backend linting** via `ruff` with the `E F W I UP B` rule set,
  enforced in CI.
- **Frontend linting** via ESLint, enforced in CI.
- **Open source governance** files: `LICENSE` (MIT), `CONTRIBUTING.md`,
  `CODE_OF_CONDUCT.md`, `SECURITY.md`, `.github/dependabot.yml`,
  issue and PR templates, `.editorconfig`.

[Unreleased]: https://github.com/vinicq/md-bridge/compare/v0.12.0...HEAD
[0.12.0]: https://github.com/vinicq/md-bridge/compare/v0.11.0...v0.12.0
[0.11.0]: https://github.com/vinicq/md-bridge/compare/v0.10.0...v0.11.0
[0.10.0]: https://github.com/vinicq/md-bridge/compare/v0.9.0...v0.10.0
[0.9.0]: https://github.com/vinicq/md-bridge/compare/v0.8.0...v0.9.0
[0.8.0]: https://github.com/vinicq/md-bridge/compare/v0.7.0...v0.8.0
[0.7.0]: https://github.com/vinicq/md-bridge/compare/v0.6.0...v0.7.0
[0.6.0]: https://github.com/vinicq/md-bridge/compare/v0.5.0...v0.6.0
[0.5.0]: https://github.com/vinicq/md-bridge/compare/v0.4.0...v0.5.0
[0.4.0]: https://github.com/vinicq/md-bridge/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/vinicq/md-bridge/compare/v0.2.3...v0.3.0
[0.2.3]: https://github.com/vinicq/md-bridge/compare/v0.2.2...v0.2.3
[0.2.2]: https://github.com/vinicq/md-bridge/compare/v0.2.1...v0.2.2
[0.2.1]: https://github.com/vinicq/md-bridge/compare/v0.2.0...v0.2.1
[0.2.0]: https://github.com/vinicq/md-bridge/compare/v0.1.1...v0.2.0
[0.1.1]: https://github.com/vinicq/md-bridge/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/vinicq/md-bridge/releases/tag/v0.1.0
