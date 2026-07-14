# API recipes

This page collects copy-paste recipes for talking to the md-bridge
HTTP API from the three places contributors and operators ask about:
the shell (`curl`), Python (`requests`), and the browser or Node
(`fetch`).

The API is documented endpoint-by-endpoint at
[`/docs`](https://vinicq.github.io/md-bridge/API/) (Swagger UI on the
running service). This page focuses on the practical "give me a
working snippet" angle.

## Endpoints at a glance

| Method | Path | Purpose | Request body | Response |
|---|---|---|---|---|
| `GET` | `/api/health` | Liveness probe | empty | `{ "status": "ok" }` |
| `POST` | `/api/inspect-pdf` | Read PDF metadata without converting | `multipart/form-data` (file) | JSON |
| `POST` | `/api/pdf-to-md` | Convert PDF to Markdown | `multipart/form-data` (file + options) | JSON |
| `POST` | `/api/md-to-pdf` | Render Markdown to PDF | `multipart/form-data` (file + options) | `application/pdf` |

Default host in every recipe is `http://localhost:8000`. Switch to
your deployed host as needed.

Upload limit on all `POST` endpoints is **500 MB** (`MAX_UPLOAD_BYTES`
in `apps/api/app/config.py`).

## Health check

The cheapest sanity check.

### curl

```bash
curl -sf http://localhost:8000/api/health
# => {"status":"ok"}
```

### Python

```python
import requests

r = requests.get("http://localhost:8000/api/health", timeout=5)
r.raise_for_status()
print(r.json())  # {'status': 'ok'}
```

### JavaScript

```js
const r = await fetch("http://localhost:8000/api/health");
const data = await r.json();
console.log(data); // { status: "ok" }
```

## Inspect a PDF (no conversion)

Returns the document profile that the converter would build, without
running the conversion. Useful for deciding whether OCR is needed
before paying the conversion cost.

### Response shape

```json
{
  "pages": 4,
  "body_size_pt": 11.0,
  "heading_sizes_pt": [18.0, 14.0, 12.5],
  "fonts": [
    { "name": "Helvetica-Bold", "size": 18.0, "count": 6, "sample": "Introduction" }
  ],
  "tagged": false,
  "needs_ocr": false
}
```

`needs_ocr: true` means the PDF has no extractable text on at least
one page; the converter would emit a `needs_ocr` warning unless OCR
is enabled.

### curl

```bash
curl -X POST http://localhost:8000/api/inspect-pdf \
  -F "file=@whitepaper.pdf"
```

### Python

```python
import requests

with open("whitepaper.pdf", "rb") as fh:
    r = requests.post(
        "http://localhost:8000/api/inspect-pdf",
        files={"file": ("whitepaper.pdf", fh, "application/pdf")},
        timeout=60,
    )
r.raise_for_status()
report = r.json()
if report["needs_ocr"]:
    print("This PDF is scanned. Install the OCR extra on the server "
          "(it then runs automatically), or retry with force=true.")
```

### JavaScript

```js
const form = new FormData();
form.append("file", fileInput.files[0]);  // browser <input type="file">

const r = await fetch("http://localhost:8000/api/inspect-pdf", {
  method: "POST",
  body: form,
});
if (!r.ok) {
  throw new Error(`Inspect failed: ${r.status}`);
}
const report = await r.json();
```

## PDF to Markdown

The most common conversion.

### Options

The `options` field is a JSON string. All fields are optional.

| Field | Type | Default | What it does |
|---|---|---|---|
| `page_break` | bool | `false` | Inserts `---` between pages |
| `with_images` | bool | `false` | Embeds images inline as base64 `data:` URIs (self-contained `.md`) |
| `front_matter` | bool | `true` | Emits YAML front matter at the top |
| `lang` | string | `"pt-BR"` | Affects warning translations only |

### Response shape

```json
{
  "md": "---\ntitle: \"Whitepaper\"\npages: 4\n---\n\n# Introduction\n\n...",
  "front_matter": {
    "title": "Whitepaper",
    "author": "Author Name",
    "date": "2026-04-12",
    "source": "whitepaper.pdf",
    "pages": 4
  },
  "warnings": [],
  "stats": { "headings": 6, "tables": 1, "bullets": 14 },
  "ocr_applied": false
}
```

### curl

Bare conversion:

```bash
curl -X POST http://localhost:8000/api/pdf-to-md \
  -F "file=@whitepaper.pdf"
```

With options and saving the Markdown to disk:

```bash
curl -X POST http://localhost:8000/api/pdf-to-md \
  -F "file=@whitepaper.pdf" \
  -F 'options={"page_break": true, "front_matter": true, "lang": "en"}' \
  | jq -r '.md' > whitepaper.md
```

### Python

```python
import json
import requests

with open("whitepaper.pdf", "rb") as fh:
    r = requests.post(
        "http://localhost:8000/api/pdf-to-md",
        files={"file": ("whitepaper.pdf", fh, "application/pdf")},
        data={"options": json.dumps({"front_matter": True, "lang": "en"})},
        timeout=300,
    )
r.raise_for_status()
result = r.json()

if result["warnings"]:
    print("Warnings:", result["warnings"])
print(f"Extracted {result['stats']['headings']} headings, "
      f"{result['stats']['tables']} tables, "
      f"{result['stats']['bullets']} bullets")

with open("whitepaper.md", "w", encoding="utf-8") as fh:
    fh.write(result["md"])
```

### JavaScript

Browser flow that posts a `<input type="file">` and downloads the
Markdown as a file:

```js
const form = new FormData();
form.append("file", fileInput.files[0]);
form.append("options", JSON.stringify({ front_matter: true, lang: "en" }));

const r = await fetch("http://localhost:8000/api/pdf-to-md", {
  method: "POST",
  body: form,
});
if (!r.ok) {
  const err = await r.json().catch(() => ({}));
  throw new Error(err.error?.message ?? `HTTP ${r.status}`);
}
const data = await r.json();

const blob = new Blob([data.md], { type: "text/markdown" });
const url = URL.createObjectURL(blob);
const link = document.createElement("a");
link.href = url;
link.download = "converted.md";
link.click();
URL.revokeObjectURL(url);
```

Node.js with `undici`'s `FormData` (Node 20+):

```js
import { readFile } from "node:fs/promises";
import { writeFile } from "node:fs/promises";

const buf = await readFile("whitepaper.pdf");
const form = new FormData();
form.append("file", new Blob([buf], { type: "application/pdf" }), "whitepaper.pdf");
form.append("options", JSON.stringify({ lang: "en" }));

const r = await fetch("http://localhost:8000/api/pdf-to-md", { method: "POST", body: form });
const result = await r.json();
await writeFile("whitepaper.md", result.md);
```

## Markdown to PDF

The renderer returns the PDF as the raw response body
(`application/pdf`), with a `Content-Disposition: attachment;
filename="<name>.pdf"` header.

### Options

| Field | Type | Default | What it does |
|---|---|---|---|
| `lang` | string | `"pt-BR"` | Sets `<html lang>` and affects hyphenation hints |

### curl

```bash
curl -X POST http://localhost:8000/api/md-to-pdf \
  -F "file=@notes.md" \
  --output notes.pdf
```

With language option:

```bash
curl -X POST http://localhost:8000/api/md-to-pdf \
  -F "file=@notes.md" \
  -F 'options={"lang": "en"}' \
  --output notes.pdf
```

### Python

```python
import json
import requests

with open("notes.md", "rb") as fh:
    r = requests.post(
        "http://localhost:8000/api/md-to-pdf",
        files={"file": ("notes.md", fh, "text/markdown")},
        data={"options": json.dumps({"lang": "en"})},
        timeout=300,
    )
r.raise_for_status()

with open("notes.pdf", "wb") as fh:
    fh.write(r.content)
```

### JavaScript

Browser flow that posts a Markdown file and triggers a download of
the PDF:

```js
const form = new FormData();
form.append("file", fileInput.files[0]);
form.append("options", JSON.stringify({ lang: "en" }));

const r = await fetch("http://localhost:8000/api/md-to-pdf", {
  method: "POST",
  body: form,
});
if (!r.ok) throw new Error(`HTTP ${r.status}`);

const blob = await r.blob();
const url = URL.createObjectURL(blob);
const link = document.createElement("a");
link.href = url;
link.download = "rendered.pdf";
link.click();
URL.revokeObjectURL(url);
```

## Error handling

Every failure returns the same envelope:

```json
{
  "error": {
    "code": "<machine_readable>",
    "message": "<human_readable>",
    "detail": "<optional, varies by code>"
  }
}
```

The HTTP status reflects the class of error:

| Status | Code examples | When |
|---|---|---|
| `400` | `wrong_file_type` | The upload's filename does not match the expected extension |
| `413` | `payload_too_large` | The upload exceeded 500 MB |
| `422` | `invalid_options` | The `options` JSON failed to parse or failed Pydantic validation |
| `500` | depends | Renderer crashed, OS dep missing, etc. |

### Reading the envelope

#### curl

```bash
curl -sf -X POST http://localhost:8000/api/md-to-pdf \
  -F "file=@notes.txt" \
  --output notes.pdf

echo $?   # non-zero on failure; --fail-with-body prints the JSON
```

Pretty-printing the error body:

```bash
curl -X POST http://localhost:8000/api/md-to-pdf \
  -F "file=@notes.txt" \
  --fail-with-body \
  --output - | jq .error
```

#### Python

```python
import requests

r = requests.post(
    "http://localhost:8000/api/md-to-pdf",
    files={"file": ("notes.txt", b"# wrong extension", "text/plain")},
)
if not r.ok:
    err = r.json().get("error", {})
    raise RuntimeError(f"[{err.get('code')}] {err.get('message')}")
```

#### JavaScript

```js
const r = await fetch("http://localhost:8000/api/md-to-pdf", {
  method: "POST",
  body: form,
});
if (!r.ok) {
  const body = await r.json().catch(() => ({}));
  const err = body.error ?? {};
  throw new Error(`[${err.code ?? r.status}] ${err.message ?? "request failed"}`);
}
```

## CORS and cross-origin requests

The dev server in `apps/api/app/main.py` allows requests from
`http://localhost:5173` (the Vite dev server). For other origins,
set the `MD_BRIDGE_CORS_ORIGINS` environment variable to a
comma-separated list when starting the API:

```bash
MD_BRIDGE_CORS_ORIGINS="https://app.example.com,https://docs.example.com" \
  uvicorn app.main:app --app-dir apps/api
```

If the browser console shows `CORS policy: No 'Access-Control-Allow-Origin'`,
the origin making the call is not in that list.

## Rate limits and concurrency

There is no built-in rate limiter. The conversion endpoints run the
work in a thread pool via `asyncio.to_thread`, so concurrent
requests do not block each other at the FastAPI layer, but they do
share the host's CPU. Two practical knobs:

- **Process-level concurrency**: `uvicorn --workers N` runs N
  separate Python processes. Each process serves requests in
  parallel.
- **Per-process thread cap**: the default thread-pool size is
  `min(32, os.cpu_count() + 4)`. PDF conversions are CPU-bound, so
  raising this past the core count rarely helps.

If you need a real rate limit (per-IP, per-API-key), put a reverse
proxy in front (nginx with `limit_req`, Traefik with the rate-limit
middleware, or Caddy with `rate_limit`).
