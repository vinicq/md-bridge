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

- Hard limits: **500 MB per upload**, no persistence. The nginx reverse
  proxy waits up to 10 minutes per request, which covers very large PDFs.

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
| `file`     | yes      | file   | A `.pdf` file (up to 500 MB).                                 |
| `options`  | no       | string | JSON string. See below.                                      |

### `options` shape

```json
{
  "page_break": false,
  "with_images": false,
  "front_matter": true,
  "extract_highlights": false,
  "emit_figure_anchors": false,
  "lang": "en"
}
```

- `page_break` (default `false`): when `true`, inserts a `---` between pages.
- `with_images` (default `false`): when `true`, the converter embeds each image
  inline in the Markdown as a base64 `data:` URI (`![alt](data:image/png;base64,...)`),
  so the response is self-contained and carries no separate files. Two caveats:
  base64 grows the payload by about a third, and github.com strips `data:` image
  URIs when it renders Markdown, so inline images do not show there (VS Code,
  Obsidian, pandoc, and browsers render them fine).
- `front_matter` (default `true`): adds a YAML preamble with `title`,
  `author`, `date`, `source`, `pages`.
- `extract_highlights` (default `false`): when `true`, PDF text-highlight
  annotations become `==highlighted text==` (rendered as `<mark>` by
  `md-to-pdf`). Off keeps the output byte-identical.
- `emit_figure_anchors` (default `false`): when `true` and used with
  `with_images`, a numbered figure caption gives its image a `{#fig-N .figure}`
  anchor id so cross-references can link to it.
- `lang` (default `"pt-BR"`): informational tag stored in the front matter.

The converter accepts more options than shown here (blockquote detection,
autolinks, footnote pairing, smart typography, task-list detection, and others).
The 0.10.0 heuristics join the same opt-in family, each off by default so output
stays byte-identical:

- `table_column_align`: emit GFM alignment markers in the table separator (#175).
- `tight_loose_lists` (with `list_loose_threshold`): keep a PDF list's tight or
  loose spacing (#168).
- `image_width_hints`: emit each image's source width as a `{width=N}` hint;
  needs `with_images` (it acts on the extracted images) (#169).
- `image_link_anchors`: wrap an image in its click-action link as
  `[![alt](src)](target)`; needs `with_images` (#170).
- `nested_ordered_lists`: keep a nested ordered sublist's own start and indent it
  to nest in the renderer (#194).
- `multiline_table_format` (`pipe` or `grid`): emit a Pandoc grid table for a
  table with a multi-line cell; rendering it back needs the `grid-tables` extra
  (#166).
- `detect_definition_lists` (with `definition_list_max_term_length` and
  `definition_list_min_indent_pt`): emit `Term` / `: definition` for a glossary
  layout (#161).

The 0.11.0 line adds one more:

- `ocr_images` (`off` or `all`, default `off`): with `all`, eligible embedded
  images are run through OCR and the recognized text is inlined next to each
  image. Candidates are bounded: an image must be at least 200x100 px and cover at
  least 0.5% of the page, must not be CMYK, and only the 50 largest per document
  are processed. It is skipped when the full-page `needs_ocr` pre-pass fires, so a
  scanned page takes the page-OCR path instead (the two do not both run). Enabling
  `all` needs the optional OCR extra AND the `MD_BRIDGE_OCR_ENABLED` environment
  variable set to a truthy value; without both, the request returns
  `422 ocr_not_available`. `all` also forces inline base64 images (as if
  `with_images` were on), which grows the response (#140).

See `packages/pdf-to-markdown/scripts/convert.py --help` for the full CLI surface.

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
| 413    | `payload_too_large` | upload > 500 MB                                   |
| 422    | `invalid_options` | the `options` JSON is malformed or fails schema   |

---

## `POST /api/md-to-pdf`

Render Markdown into a PDF through headless Chromium.

### Request fields

| field      | required | type   | description                                                  |
| ---------- | -------- | ------ | ------------------------------------------------------------ |
| `file`     | yes      | file   | A UTF-8 `.md` file (up to 500 MB).                            |
| `options`  | no       | string | JSON string. See below.                                      |

### `options` shape

```json
{
  "theme": "academic",
  "lang": "en"
}
```

- `theme` (default `"default"`): slug of a registered theme (see `GET /api/themes`). The renderer stacks the selected theme's stylesheet on top of the base `default.css`; `"default"` renders the base alone. An unknown slug returns `400 unknown_theme`.
- `lang` (default `"pt-BR"`): written into `<html lang>`.

### Example: render and save

```bash
curl -X POST http://localhost:8000/api/md-to-pdf \
  -F "file=@notes.md" \
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
| 400    | `invalid_markdown` | upload is not valid UTF-8                        |
| 400    | `unknown_theme` | `options.theme` is not a registered slug            |
| 500    | `render_failed` | Chromium crashed or a CSS template is missing       |

---

## `GET /api/themes`

List the registered Markdown → PDF themes.

### Response (`200 OK`)

```json
[
  { "slug": "default", "name": "Default", "description": "Neutral, legible A4 base used when no theme is selected.", "family": "general" },
  { "slug": "academic", "name": "Academic", "description": "Serif, paper-like layout...", "family": "academic" }
]
```

`default` is always first. Pass any `slug` as `options.theme` on `POST /api/md-to-pdf`.

---

## `GET /api/themes/{slug}/css`

Return a theme's own stylesheet as `text/css`, for inline display in a theme catalogue.

### Response (`200 OK`)

`text/css; charset=utf-8`. For `default` this is the base stylesheet; for any other theme it is the overlay that stacks on top of the base.

### Common errors

| status | code            | when                                |
| ------ | --------------- | ----------------------------------- |
| 400    | `unknown_theme` | `slug` is not a registered theme    |

---

## `POST /api/inspect-pdf`

Read-only diagnostics about a PDF, useful as a pre-flight before converting.

### Request fields

| field   | required | type | description                  |
| ------- | -------- | ---- | ---------------------------- |
| `file`  | yes      | file | A `.pdf` file (up to 500 MB). |

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

# 5. Render it back to PDF
curl -X POST http://localhost:8000/api/md-to-pdf \
  -F "file=@paper.md" \
  --output paper.rendered.pdf
```
