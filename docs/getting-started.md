# Getting started

There are two supported ways to run md-bridge locally: with Docker (one
command) or from source (Python + Node). Both end up with the same API
on `http://localhost:8000` and the same UI on `http://localhost:5173`.

## With Docker (recommended for trying it out)

You only need Docker Engine + Docker Compose.

```bash
git clone https://github.com/vinicq/md-bridge.git
cd md-bridge
docker compose up
```

The compose stack waits for the API healthcheck before starting the web
container, so the first call from the browser already has a live backend
behind it.

To pull pre-built images instead of building locally (faster, no toolchain
required):

```bash
docker pull ghcr.io/vinicq/md-bridge-api:latest
docker pull ghcr.io/vinicq/md-bridge-web:latest
```

The compose file then runs them without a build step.

### Running the test suite inside Docker

The compose stack runs the application by default, not the tests. An opt-in
`test` profile spins up ephemeral containers that execute pytest and
vitest:

```bash
docker compose --profile test run --rm tests-api   # backend pytest
docker compose --profile test run --rm tests-web   # frontend vitest
```

Both containers exit when the suite finishes; nothing keeps running in the
background.

## From source

You will need:

- Python 3.12 or newer
- Node 22 and npm 10 or newer

The commands below work the same on macOS, Linux, and Windows once the
virtual environment is activated.

```bash
# 1. Backend: create the virtual environment
cd apps/api
python -m venv .venv

# Activate it (pick the line for your shell):
source .venv/bin/activate                   # macOS / Linux / Git Bash
# .venv\Scripts\Activate.ps1                # Windows PowerShell

# Install the backend and the converter dependencies:
python -m pip install -e ".[dev]"
python -m playwright install chromium

# 2. Frontend
cd ../web
npm install
npx playwright install chromium

# 3. Root-level helper (lets you start API and UI together)
cd ../..
npm install

# 4. Boot the dev servers: API on port 8000, Vite on port 5173
npm run dev
```

Open `http://localhost:5173` for the UI and `http://localhost:8000/docs`
for the interactive API documentation.

## First conversion

The UI's PDF → Markdown page accepts both individual files and whole
folders dropped onto the dropzone. Try it with one of the syllabus
fixtures committed under `apps/api/tests/fixtures/` if you want a known
input.

For an API-only smoke test:

```bash
curl -X POST http://localhost:8000/api/pdf-to-md \
  -F "file=@apps/api/tests/fixtures/istqb-ctal-ta-syllabus-en.pdf" \
  -F 'options={"front_matter": true}'
```

The response includes the extracted Markdown, a `stats` block (heading
count, bullet count, table count), any warnings the heuristic produced,
and the YAML front matter.

## Limits worth knowing about

- The API caps uploads at **500 MB** per request. nginx in front of it
  waits up to **10 minutes** per conversion, which fits very large PDFs
  end-to-end.
- Scanned PDFs need OCR before submission. md-bridge does not bundle
  Tesseract; the inspect endpoint will tell you when OCR is the missing
  step.
- Tables with merged cells can be flattened by the heuristic extractor.

## Where to go next

- [API reference](API.md) — every endpoint, every option, every error.
- [Contributing](contributing.md) — code style, test pyramid, PR rules.
