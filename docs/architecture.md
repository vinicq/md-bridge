# Architecture

This page describes how md-bridge is put together. It is meant for
contributors picking up an issue and reviewers looking at a PR that
crosses module boundaries.

## Shape of the project

```
md-bridge/
├── apps/
│   ├── api/                 FastAPI backend
│   │   ├── app/
│   │   │   ├── routes/      HTTP endpoints (convert, health, inspect)
│   │   │   ├── services/    business logic, calls into packages/
│   │   │   ├── schemas/     pydantic models for request/response
│   │   │   ├── errors.py    structured error codes for the UI
│   │   │   └── main.py      FastAPI app factory
│   │   └── tests/           unit + integration suites
│   └── web/                 React frontend
│       ├── src/
│       │   ├── components/  reusable UI (DropZone, BatchPanel, Toast)
│       │   ├── pages/       routed pages (Home, PdfToMd, MdToPdf, About)
│       │   ├── hooks/       useBatchConvert and friends
│       │   ├── i18n/        EN/PT-BR/ES dictionaries
│       │   ├── lib/         API client, helpers
│       │   └── styles/      tokens.css + globals.css
│       ├── e2e/             Playwright tests
│       └── tests/           Vitest unit + integration
├── packages/
│   ├── pdf-to-markdown/     vendored converter (Python, deterministic)
│   └── markdown-to-pdf/     vendored converter (Python, Playwright)
└── docs/                    MkDocs Material site
```

Three layers, each replaceable without rewriting the others:

- **Converter packages** at the bottom. Pure functions over file paths
  and byte buffers. They have no HTTP knowledge and no UI knowledge.
- **FastAPI backend** in the middle. Wraps the packages, adds validation,
  emits stable error codes, exposes the converters over HTTP.
- **React frontend** on top. Calls the API, renders the results, handles
  batch state and i18n.

## Component diagram

```
                    ┌──────────────────────┐
                    │   React (apps/web)   │
                    │  DropZone, batches,  │
                    │  i18n, preview       │
                    └──────────┬───────────┘
                               │  fetch + multipart/form-data
                               │  /api/pdf-to-md, /api/md-to-pdf
                               ▼
                    ┌──────────────────────┐
                    │  FastAPI (apps/api)  │
                    │  routes -> services  │
                    │  validation, errors  │
                    └──────────┬───────────┘
                               │  Python function call
                               ▼
              ┌────────────────┴─────────────────┐
              │                                  │
      ┌───────▼────────┐                ┌────────▼─────────┐
      │ pdf-to-markdown│                │ markdown-to-pdf  │
      │ (PyMuPDF +     │                │ (Python markdown │
      │  heuristics)   │                │  + Playwright)   │
      └────────────────┘                └──────────────────┘
```

The same shape ships in Docker: two images, `md-bridge-api` and
`md-bridge-web`. Nginx serves the static React bundle and reverse-proxies
`/api/*` to the FastAPI container.

## PDF to Markdown flow

A request to `POST /api/pdf-to-md`:

1. **Route** (`routes/convert.py`) reads the upload, validates size and
   content-type, hands the bytes to the service.
2. **Service** (`services/pdf_to_md.py`) writes the bytes to a temp file
   and calls `packages/pdf-to-markdown/scripts/pdf_to_markdown.py`. No
   network calls happen inside the converter.
3. **Converter** opens the PDF with PyMuPDF, reads font metadata and the
   outline tree, then runs heuristics over the layout:
   - Font-size histogram detects H1/H2/H3 candidates against the body
     baseline.
   - Outline (when present) gives canonical headings and overrides the
     histogram for matching positions.
   - `find_tables` from PyMuPDF reconstructs grid tables; freeform
     pseudo-tables are recovered through column-position clustering.
   - Bulleted and numbered lists are inferred from indentation steps and
     marker glyphs.
   - YAML front matter is built from PDF metadata.
4. **Response** carries the generated Markdown, a list of warnings keyed
   by stable codes (the frontend localises the messages), and the
   warning count.

The converter is deterministic. Same input, same output, every run. The
heuristics are documented in `packages/pdf-to-markdown/REFERENCE.md`.

## Markdown to PDF flow

A request to `POST /api/md-to-pdf`:

1. **Route** (`routes/convert.py`) reads the payload (either an uploaded
   `.md` or pasted text) plus optional theme and page-size options.
2. **Service** (`services/md_to_pdf.py`) writes Markdown to a temp file
   and calls `packages/markdown-to-pdf/scripts/markdown_to_pdf.py`.
3. **Converter** builds HTML with the Python `markdown` library
   (extra, tables, fenced_code, footnotes, toc, smarty, md_in_html
   extensions), wraps it in a template with a CSS theme from
   `packages/markdown-to-pdf/templates/`, and prints to PDF through
   headless Chromium via Playwright. Print CSS (`@page`, counters,
   `page-break-*`) drives the page layout.
4. **Response** carries the PDF bytes back through FastAPI's
   `StreamingResponse`.

YAML front matter sets title, author, and date. The chosen theme drives
the visual style. No Pandoc, no LaTeX, no wkhtmltopdf.

## Why these choices

Some decisions are load-bearing for the project's identity and worth
calling out:

**Heuristics over LLMs.** The converters use hand-written rules. No
external API calls, no model inference, no cloud key required. The
trade-off is that exotic layouts need manual cleanup; the win is that
the same PDF always produces the same Markdown, and self-hosting is
trivial.

**Vendored converter packages.** The `packages/` directory holds the
two converters as standalone Python libraries. They ship inside the
md-bridge container and they also work as CLIs outside it. This makes
the project less of a monolith: the backend is a thin HTTP wrapper
around libraries that have their own tests and READMEs.

**Stable error codes.** The API emits structured warning codes
(`PDFTOMD_FONT_INFO_MISSING` and friends). The frontend has the
translations in `apps/web/src/i18n/dictionaries.ts`. New locales add an
entry; the backend never has to know which language the user picked.

**Multi-arch Docker by default.** `apps/api/Dockerfile` is built on the
Playwright/Chromium base image so the runtime has every system library
Chromium needs. The publish workflow ships `linux/amd64` and
`linux/arm64` manifests. The Oracle Cloud Always Free deploy recipe
and Apple Silicon devs both rely on the arm64 image.

**Determinism gates in CI.** Backend tests assert byte-exact Markdown
output against fixture PDFs. Frontend tests assert axe-core finds zero
critical or serious accessibility violations on every route. Both gates
sit on `main` as branch-protection-required checks.

## Where to add a new format pair

The architecture is designed to welcome new converters. The plan in the
roadmap is DOCX, EPUB, RTF, and HTML, each behind the same heuristic
pipeline pattern. To add one:

1. **Library first.** Drop a new directory under `packages/`, with a
   `README.md`, a `scripts/<name>.py` entry, and tests. The library
   should work as a CLI before any backend code is written.
2. **Service in the backend.** Add `apps/api/app/services/<name>.py`
   that shells out to the library. Keep it thin: no business logic
   beyond the file IO.
3. **Route.** Add the HTTP endpoint in `apps/api/app/routes/convert.py`.
   Match the request shape of existing routes (multipart upload, JSON
   options, structured warning list in the response).
4. **Frontend.** Add the page under `apps/web/src/pages/`. Reuse the
   existing `DropZone` and `BatchPanel` components. Add dictionary
   entries to all three locales.
5. **Tests.** Determinism gate in `apps/api/tests/`. E2E gate in
   `apps/web/e2e/`. Both required-status-check eligible.

The design system catalogue at `docs/design/` has hi-fi mockups for the
new format hub (F4) plus six other features that future contributors
will pick up. Each mockup links to a paste-ready issue spec.

## Related docs

- API surface: [API reference](API.md)
- Accessibility gate: [Accessibility audit](accessibility-audit.md)
- Deployment recipes: [Oracle Cloud Always Free](deployment/oracle-cloud.md)
- Visual language: [Design system catalogue](https://vinicq.github.io/md-bridge/design/)
- How the converters work in detail: `packages/pdf-to-markdown/REFERENCE.md`
