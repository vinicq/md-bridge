# markdown-to-pdf

A small Python library that converts a structured Markdown file into a clean,
well-typeset PDF. It builds HTML from the Markdown with the `markdown`
library (extra, tables, fenced_code, footnotes, toc, smarty, md_in_html
extensions), then renders the HTML through headless Chromium via Playwright.

Reads YAML front matter for title, author, and date. Applies a CSS theme for
the visual style. Supports A4 page format with automatic page numbers,
footnotes, tables, code blocks, and internal links. No external binaries
needed (no Pandoc, no wkhtmltopdf, no LaTeX).

This package is vendored by `md-bridge` but works as a standalone CLI.

## When to use it

- You have a `.md` file (typically one produced by the `pdf-to-markdown`
  package) and want a printable PDF.
- You want a custom-styled PDF without installing Pandoc, LaTeX, or
  wkhtmltopdf.
- Output target: A4, screen-readable, with title page, headings, tables,
  code blocks, footnotes, links.

## When NOT to use it

- Pixel-perfect reproduction of a source PDF (that needs a LaTeX template
  per document family, out of scope).
- Math-heavy content with MathJax/KaTeX rendering (the renderer does not
  execute JavaScript in this configuration).
- Very long documents (1000+ pages) where memory becomes a concern.

## Stack

| Layer | Tool | Why |
|---|---|---|
| MD to HTML | Python `markdown` lib (extra, tables, fenced_code, footnotes, toc, smarty, md_in_html) | Standard CommonMark plus extensions |
| HTML and CSS to PDF | Playwright (headless Chromium) | Full CSS print support (@page, counters, page-break-*), modern CSS, no GTK or wkhtmltopdf binary on Windows |
| Theme | CSS file in `templates/` | Easily swappable per project |

Both libs already ship in this environment:

- `Markdown==3.10.2`
- `playwright==1.58.0` plus the Chromium binary

First-time setup (if Playwright's Chromium is not installed yet):

```bash
playwright install chromium
```

## Workflow

1. **Convert** with the default theme:

   ```bash
   python packages/markdown-to-pdf/scripts/convert.py "<input.md>" -o "<output.pdf>"
   ```

2. **Convert** with a custom CSS:

   ```bash
   python packages/markdown-to-pdf/scripts/convert.py "<input.md>" -o "<output.pdf>" --css path/to/theme.css
   ```

3. **Stack multiple CSS files** (for example base plus overrides):

   ```bash
   python packages/markdown-to-pdf/scripts/convert.py "<input.md>" -o "<output.pdf>" \
     --css packages/markdown-to-pdf/templates/default.css \
     --css my_brand_overrides.css
   ```

4. **Set the HTML lang** (defaults to `pt-BR`):

   ```bash
   python packages/markdown-to-pdf/scripts/convert.py "<input.md>" -o "<output.pdf>" --lang en
   ```

## What the default theme provides

- A4, 2.5cm by 2cm margins
- Page number "N / Total" at the bottom (hidden on first page)
- Segoe UI sans-serif for body and headings, Consolas for code
- 11pt body, justified text with hyphenation
- H1 always starts a new page (except the first one)
- Heading hierarchy with sensible spacing
- Tables: collapsed borders, header row shaded, `page-break-inside: avoid`
- Code: inline gray pill plus fenced block with border
- Blockquotes with left border plus tinted background
- `<small>` for captions

## Front matter

If the `.md` starts with YAML front matter, `title` is used for the HTML
`<title>`. The front matter block is stripped from the body before
rendering, so it does not appear in the PDF.

```yaml
---
title: "Foundation Level Syllabus"
author: "Stan Bühne"
date: "2024-06-26"
---
```

A future extension is a "cover page" template that renders title, author,
and date from the front matter as a styled first page.

## Planned extensions (not yet implemented)

- **Theme variants** in `templates/`: corporate, academic, brand-specific.
- **Cover page block** rendered from front matter (title, author, date, logo).
- **TOC generation** from headings (`[TOC]` placeholder plus CSS for the listing).
- **Watermark / draft stamp** via `@page` background.
- **Per-section page breaks** controlled by front matter directives.
- **Image resolution check** (warn when an embedded image is below print DPI).

## Files

- `README.md`: this file
- `scripts/convert.py`: main converter (MD to HTML to PDF)
- `templates/default.css`: neutral A4 print theme

## Round-trip with pdf-to-markdown

The two packages are designed to pair:

```bash
# PDF to MD (structure-preserving)
python packages/pdf-to-markdown/scripts/convert.py "input.pdf" -o "doc.md"

# MD to PDF (styled, not pixel-identical to the original)
python packages/markdown-to-pdf/scripts/convert.py "doc.md" -o "doc-rendered.pdf"
```

The round-trip does NOT reproduce the original PDF's exact look. Fonts,
colors, and layout decisions come from the CSS theme. What is preserved is
the **semantic structure** (headings, lists, tables, emphasis, links).
