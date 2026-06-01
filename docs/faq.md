# FAQ

The questions that come up often enough that the answer belongs in
the docs rather than in a Discussions thread.

## Why is OCR opt-in and not default?

OCR adds three things md-bridge otherwise does not need: the
Tesseract binary on the host, the `pytesseract` Python package, and
non-trivial CPU time per page. Most operators converting PDFs already
have text-bearing PDFs (digital exports, LaTeX output, anything
produced by `print to PDF`). Pulling a 100 MB binary and a Python
dependency for a code path 90 percent of users never hit would push
the lean default install in the wrong direction.

The opt-in flow is one environment variable and one Docker target:

```bash
# pip install with the [ocr] extra (plus the Tesseract binary + language packs)
python -m pip install -e "apps/api[ocr]"

# OCR then runs automatically for scanned PDFs — no flag needed.
uvicorn app.main:app --app-dir apps/api

# Force it off even when installed:
MD_BRIDGE_OCR_ENABLED=0 uvicorn app.main:app --app-dir apps/api

# Or build the dedicated container target (OCR on by default):
docker build -f apps/api/Dockerfile --target runtime-ocr \
  -t md-bridge-api:ocr .
```

When the flag is on, the converter only triggers OCR for PDFs that
have no extractable text (`diagnostics.needs_ocr == true`). PDFs that
already carry a text layer skip OCR entirely. The response payload
gains an `ocr_applied: bool` field so the UI can label the converted
file accurately.

The full rationale and the original design discussion live in
issue [#5](https://github.com/vinicq/md-bridge/issues/5).

## Why no database? Why does the converter not persist anything?

md-bridge is a stateless converter. The contract on every request
is: bytes in, bytes out, no trace.

Concretely:

- Every request gets a fresh `tempfile.TemporaryDirectory` with a
  named prefix (`md-bridge-pdf2md-` or `md-bridge-md2pdf-`). The
  directory holds the input, the intermediate artifacts, and the
  output bytes until the response is written.
- The `with` block deletes the directory on the way out. Even
  uncaught exceptions trip the cleanup because tempfile uses the
  context manager's `__exit__` to recurse-delete.
- A regression test (`tests/integration/test_zzz_cleanup.py`)
  confirms no `md-bridge-*` directory survives a normal request,
  a request that triggers a converter error, or a request that
  the client aborts mid-stream.
- The server keeps no log of what was converted. The only
  observability surface is the structured FastAPI access log
  (request line, status code, latency), which carries no document
  content.

What that means in practice:

- **Conversion history**: not stored server-side. If you want a
  history of what you converted, that lives on the client. Issue
  [#63](https://github.com/vinicq/md-bridge/issues/63) tracks
  adding browser-local history via `localStorage`.
- **Multi-user separation**: there is none, because there are no
  users. The deployment model is "one operator, one instance, one
  trust boundary". Multi-user with auth is a separate proposal
  ([#33](https://github.com/vinicq/md-bridge/issues/33)).
- **Resumable uploads**: not supported. If the request fails
  mid-stream, you re-upload. This keeps the server with no
  durable state to recover.
- **No telemetry**: zero. The Docker image makes no outbound
  network calls except to fetch the headless Chromium binary
  during build, which is baked into the image and not invoked at
  runtime.

The shape is intentional. A self-hosted converter that holds onto
your documents would have a different threat model and a different
privacy story. md-bridge picks the no-state path because it removes
both questions at once.

## How do I add a new locale?

The web UI ships three locales today: English (`en`), Brazilian
Portuguese (`pt`), and Spanish (`es`). Adding a fourth is a small,
well-bounded PR.

### What to change

The contract is the `Dictionary` interface in
`apps/web/src/i18n/dictionaries.ts`. It is a strict TypeScript type
covering every user-facing string in the app, including
ARIA-relevant attributes (`previewIframeTitle`, `mainLabel`,
`skipToContent`).

Steps:

1. **Add the locale code** to the `Locale` union at the top of
   `dictionaries.ts`:

   ```ts
   export type Locale = 'en' | 'pt' | 'es' | 'fr'
   ```

2. **Add it to the `LOCALES` array** with its label in its own
   language (this is the string shown in the locale switcher):

   ```ts
   { code: 'fr', label: 'Français' },
   ```

3. **Translate the dictionary block**. Copy the `en` block, rename
   to `fr`, and translate every value. The TypeScript interface
   makes the compiler reject any missing key, so you cannot ship a
   half-translated locale by accident.

4. **Update the `<html lang>` switcher**. The `LocaleProvider` reads
   the active locale and sets `document.documentElement.lang`. No
   extra wiring is needed unless your locale needs `dir="rtl"`, in
   which case the provider also sets the document direction. See
   how PT-BR set up its accent handling for a reference.

5. **Add a unit test**. The `MdToPdf.test.tsx` and
   `PdfToMd.test.tsx` suites parameterize over locales via
   `it.each`. Adding a row to that array gives you locale coverage
   automatically.

6. **Update the docs site**. If you want the MkDocs site to show in
   the new locale too, see [#29](https://github.com/vinicq/md-bridge/issues/29).
   The web app and the docs site share no translation pipeline, so
   the docs translation is a separate effort.

### Voice rules for translators

Translations follow the same humanizer rules as the rest of the
project's prose:

- Direct register, no marketing tone.
- Match the source's rhythm; do not over-compress or pad.
- Honor the formal/informal register the existing locales use.
  PT-BR is "você" register, not "tu". ES uses the "tú" register,
  matching the Spanish-speaking developer community on the web.

### Things to flag in your PR

- Strings that genuinely have no good translation in your locale
  (technical terms that are commonly left in English). Leaving
  them in English is usually the right call; flag it so the
  reviewer agrees explicitly.
- Locales where word length explodes (German, Finnish): mention
  the longest term so the reviewer can look at whether any layout
  breaks. The toast and the button labels are the two surfaces
  most sensitive to length.

The [#9](https://github.com/vinicq/md-bridge/issues/9) PR (Spanish
locale by @zhouzhou626) is the reference shape. It also did the
small refactor that made the `<html lang>` switch deterministic, so
read the diff alongside.

## Why heuristics instead of a language model?

See the [Heuristics](heuristics.md) page. Short version: the tool
runs self-hosted with no telemetry, the threat model demands that
the same input produce the same output every time, and the
deterministic failure mode (a misread heading) is easier to fix in
the field than a probabilistic one.

## Why Playwright and headless Chromium for Markdown → PDF?

The Markdown → PDF flow renders the document through a real browser
engine. The trade-off:

- The output matches what a user would see if they printed the
  Markdown from their browser, including CSS theme support, the
  Inter and JetBrains Mono fonts, and the same paragraph spacing
  rules the browser uses.
- The cost is the headless Chromium image, which is heavy. The
  base image is pinned by digest
  (`mcr.microsoft.com/playwright/python`), so the size is known
  and reproducible.

Alternatives that were considered:

- **WeasyPrint** — pure-Python, no browser, but CSS support is a
  subset of what real browsers ship. Themes that lean on flexbox
  or grid would not render the way users expect.
- **wkhtmltopdf** — uses an old WebKit fork, the project is in
  maintenance-only mode upstream, and the rendering quirks
  accumulate.
- **Pandoc + LaTeX** — high-quality output, but the LaTeX
  toolchain on Linux is even heavier than headless Chromium and
  the failure modes are obscure for users who do not already
  speak LaTeX.

The "real browser" path was the one with the best
predictability-per-megabyte trade-off.

## Where does conversion happen — client or server?

Server. The backend reads the bytes, runs the converter, and writes
the bytes back. The frontend never holds a converted document in
memory longer than the response stream.

Two reasons:

1. PyMuPDF and Playwright/Chromium are heavyweight; pushing them
   to the client via WebAssembly would balloon the bundle size and
   still not match the deterministic Python implementation.
2. Keeping the conversion server-side means a single deployment
   path (one Python service) instead of two (Python service plus
   a WASM target that has to be kept in sync).

The browser does one thing: format check, send, render the result.

## Can I run md-bridge offline?

Yes, with two caveats.

- **At install time**, you need network access to pull the Docker
  image (`ghcr.io/vinicq/md-bridge-api:latest` and `-web:latest`).
  The image bundles headless Chromium, fonts, and every Python
  dependency, so once the pull completes there is nothing else to
  download.
- **At runtime**, the converter makes zero outbound network calls.
  Backend, frontend, and the Chromium it drives all run within
  the container. You can run the stack on an air-gapped machine
  by transferring the saved image with `docker save` and `docker
  load`, the way you would any container.

The opt-in OCR target (`runtime-ocr`) adds the Tesseract binary,
which is also self-contained. The English, Portuguese, and Spanish
language packs (`tesseract-ocr-por`, `tesseract-ocr-spa`) are
included and applied together by default, so a scanned document in
any of the three is read without configuring a language. Set
`MD_BRIDGE_OCR_LANG` to pin a single pack, and other languages are an
`apt install` away inside the image.

## How do I contribute?

`CONTRIBUTING.md` at the repo root covers the workflow end to end:
branch naming, Conventional Commits PR titles, the test pyramid,
the all-contributors credit pipeline, and the OSS-cordial review
voice. Read it before opening your first PR.

The 30-second version:

1. Pick an issue labeled `good first issue` or `help wanted`.
2. Drop a `/claim` comment so the issue-claim workflow assigns it.
3. Open a feature branch, write the change with tests, push, open
   a PR with a Conventional Commits title.
4. Wait for the six required checks (Backend pytest, Web vitest
   + build, End-to-end Playwright, CodeQL Python, CodeQL JS/TS,
   Validate PR title). Squash merge once green.

Specific lanes that always have something open: backend, frontend,
i18n, a11y, infrastructure, docs. The issue labels are the
authoritative filter.
