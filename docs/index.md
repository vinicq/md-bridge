---
hide:
  - navigation
---

<p align="center">
  <img src="brand/wordmark.png" alt="md-bridge" width="600">
</p>

<p align="center">
  <strong>Self-hosted PDF ↔ Markdown converter.</strong><br>
  Deterministic, heuristic, no external calls.
</p>

---

## What it does

md-bridge is a small HTTP service plus a React UI that converts PDFs into
Markdown and Markdown into PDFs. The conversion is **deterministic**: the
same input file produces the same output file every run. No model, no
fine-tuning, no API key, no network call to a third party.

- **PDF → Markdown** with heading detection, list recovery, table
  extraction, and YAML front matter.
- **Markdown → PDF** rendered through headless Chromium with a bundled
  A4 stylesheet.
- **Batch mode** in the UI: drop a folder, convert the whole thing
  sequentially, download per file.
- **Diagnostics endpoint** so the UI can warn about tagged PDFs, OCR
  needs, or missing fonts before kicking off a conversion.
- **Multilingual UI** (English + Portuguese + Spanish), choice persisted in
  `localStorage`.

## Quick demo

![Demo flow through the conversion UI](screenshots/demo.gif)

## Run it in two commands

```bash
git clone https://github.com/vinicq/md-bridge.git
cd md-bridge && docker compose up
```

UI at `http://localhost:5173`, API at `http://localhost:8000/docs`.
Detailed setup steps live on the [Getting started](getting-started.md)
page.

## Why md-bridge

| What you might want | What md-bridge gives you |
| --- | --- |
| Convert PDFs without uploading them to a third-party | Self-hosted; nothing leaves the box |
| Reproducible results | Same input, same output, every run |
| Batch a whole archive | Drop a folder, get a queue |
| Plug into your own tools | `/api/pdf-to-md`, `/api/md-to-pdf`, `/api/inspect-pdf` |
| Read the conversion code | [`packages/pdf-to-markdown/scripts/convert.py`](https://github.com/vinicq/md-bridge/blob/main/packages/pdf-to-markdown/scripts/convert.py) |

## Where to go next

- [Getting started](getting-started.md) — install, run, batch a folder.
- [API reference](API.md) — endpoints, options, error envelope.
- [Contributing](contributing.md) — how to file an issue or open a PR.
- [Security](security.md) — how to report a vulnerability privately.
- [Changelog](changelog.md) — what landed in each release.

## License

[MIT](https://github.com/vinicq/md-bridge/blob/main/LICENSE).
