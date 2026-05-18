# API reference

Walkthrough of every endpoint exposed by **md-bridge**. If you prefer an
interactive playground, the running API serves Swagger UI at
`http://localhost:8000/docs` and ReDoc at `http://localhost:8000/redoc`.

> All examples assume the API is running on `http://localhost:8000`. Change
> the host if you deployed it elsewhere.

## Conventions

- All POST endpoints accept `multipart/form-data` uploads.
- Optional `options` is a **JSON string** posted as a form field, not a JSON
  body. This keeps file upload + structured options in a single request.
- All errors share the same envelope:

  ```json
  {
    "error": {
      "code": "machine_readable",
      "message": "human readable",
      "detail": "optional, can be string or object"
    }
  }
  ```

- Hard limits: **50 MB per upload**, **60 s per conversion**, no persistence.

---

## `GET /api/health`

Quick liveness probe. Use it from Docker/Kubernetes, your status page, or to
verify the API is reachable.

### Request

```bash
curl http://localhost:8000/api/health
```

### Response

```json
{ "status": "ok", "version": "0.1.0" }
```

---

## `POST /api/pdf-to-md`

Convert a PDF into structured Markdown using deterministic heuristics.

### Request fields

| field      | required | type   | description                                                  |
| ---------- | -------- | ------ | ------------------------------------------------------------ |
| `file`     | yes      | file   | A `.pdf` file (up to 50 MB).                                 |
| `options`  | no       | string | JSON string. See below.                                      |

### `options` shape

```json
{
  "page_break": false,
  "with_images": false,
  "front_matter": true,
  "lang": "en"
}
```

- `page_break` (default `false`): when `true`, inserts a `---` between pages.
- `with_images` (default `false`): when `true`, the converter extracts images
  to a temporary folder. The HTTP API does not serve images back, so use the
  CLI from `packages/pdf-to-markdown` if you want them.
- `front_matter` (default `true`): adds a YAML preamble with `title`,
  `author`, `date`, `source`, `pages`.
- `lang` (default `"pt-BR"`): informational tag stored in the front matter.

### Example: minimal

```bash
curl -X POST http://localhost:8000/api/pdf-to-md \
  -F "file=@whitepaper.pdf"
```

### Example: with options

```bash
curl -X POST http://localhost:8000/api/pdf-to-md \
  -F "file=@whitepaper.pdf" \
  -F 'options={"front_matter": true, "page_break": false, "lang": "en"}'
```

### Successful response (`200 OK`)

```json
{
  "md": "---\ntitle: \"Whitepaper\"\npages: 4\n---\n\n# Introduction\n\nFirst paragraph...",
  "front_matter": {
    "title": "Whitepaper",
    "author": "Author Name",
    "date": "2026-04-12",
    "source": "whitepaper.pdf",
    "pages": 4
  },
  "warnings": [],
  "stats": { "headings": 6, "tables": 1, "bullets": 14 }
}
```

`warnings` is non-empty when the PDF looks problematic, typically when the
converter extracted little text (signal of a scanned PDF) or when image
extraction was requested but cannot round-trip through the HTTP layer.

### Common errors

| status | code              | when                                              |
| ------ | ----------------- | ------------------------------------------------- |
| 400    | `wrong_file_type` | uploaded file does not end in `.pdf`              |
| 413    | `payload_too_large` | upload > 50 MB                                   |
| 422    | `invalid_options` | the `options` JSON is malformed or fails schema   |

---

## `POST /api/md-to-pdf`

Render Markdown into a PDF through headless Chromium.

### Request fields

| field      | required | type   | description                                                  |
| ---------- | -------- | ------ | ------------------------------------------------------------ |
| `file`     | yes      | file   | A UTF-8 `.md` file (up to 50 MB).                            |
| `options`  | no       | string | JSON string. See below.                                      |

### `options` shape

```json
{
  "theme": "default",
  "lang": "en"
}
```

- `theme` (default `"default"`): name of a `.css` file under
  `packages/markdown-to-pdf/templates/`. Use `GET /api/themes` to discover
  what is installed.
- `lang` (default `"pt-BR"`): written into `<html lang>`.

### Example: render and save

```bash
curl -X POST http://localhost:8000/api/md-to-pdf \
  -F "file=@notes.md" \
  -F 'options={"theme":"default"}' \
  --output notes.pdf
```

### Successful response (`200 OK`)

Binary `application/pdf`. The first bytes are the magic `%PDF-` header. The
`Content-Disposition` header carries a suggested filename:

```
HTTP/1.1 200 OK
content-type: application/pdf
content-disposition: attachment; filename="notes.pdf"
```

### Common errors

| status | code            | when                                                |
| ------ | --------------- | --------------------------------------------------- |
| 400    | `wrong_file_type` | uploaded file does not end in `.md`               |
| 400    | `unknown_theme` | the requested theme is not under `templates/`       |
| 400    | `invalid_markdown` | upload is not valid UTF-8                        |
| 500    | `render_failed` | Chromium crashed or a CSS template is missing       |

---

## `POST /api/inspect-pdf`

Read-only diagnostics about a PDF, useful as a pre-flight before converting.

### Request fields

| field   | required | type | description                  |
| ------- | -------- | ---- | ---------------------------- |
| `file`  | yes      | file | A `.pdf` file (up to 50 MB). |

### Example

```bash
curl -X POST http://localhost:8000/api/inspect-pdf \
  -F "file=@whitepaper.pdf"
```

### Successful response (`200 OK`)

```json
{
  "pages": 4,
  "body_size_pt": 11.0,
  "heading_sizes_pt": [18.0, 14.0, 12.5],
  "fonts": [
    { "name": "InterRegular", "size": 11.0, "count": 12048, "sample": "Lorem ipsum..." },
    { "name": "InterBold",    "size": 18.0, "count":   320, "sample": "Introduction" }
  ],
  "tagged": true,
  "needs_ocr": false
}
```

- `tagged`: true when the PDF advertises PDF/UA structure tags (good for
  accessibility, helpful for heading detection).
- `needs_ocr`: true when very little extractable text was found per page.
  Scanned PDFs need Tesseract (or another OCR tool) before they can be
  converted.

---

## `GET /api/themes`

List CSS themes available for Markdown to PDF rendering.

### Request

```bash
curl http://localhost:8000/api/themes
```

### Response

```json
[
  { "id": "default", "name": "Default A4", "preview_url": null }
]
```

To add a new theme, drop a `<name>.css` into
`packages/markdown-to-pdf/templates/`. It will show up on the next call,
no restart needed. The default theme is always layered first; custom themes
only need to override the parts they care about.

---

## End-to-end example: round-trip

```bash
# 1. Check the API is up
curl http://localhost:8000/api/health

# 2. Inspect the PDF first
curl -X POST http://localhost:8000/api/inspect-pdf -F "file=@paper.pdf"

# 3. Convert it to Markdown
curl -X POST http://localhost:8000/api/pdf-to-md \
  -F "file=@paper.pdf" \
  -F 'options={"front_matter": true}' \
  -o paper.md.json

# 4. Pull the `md` field into a real .md file
python -c "import json,sys; print(json.load(open('paper.md.json'))['md'])" > paper.md

# 5. Render it back to PDF with the default theme
curl -X POST http://localhost:8000/api/md-to-pdf \
  -F "file=@paper.md" \
  -F 'options={"theme":"default"}' \
  --output paper.rendered.pdf
```
