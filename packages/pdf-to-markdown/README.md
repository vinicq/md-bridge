# pdf-to-markdown

A small, self-contained Python library that converts a digitally-generated
PDF (not scanned) into structured Markdown. The conversion is deterministic:
it runs hand-written heuristics over PyMuPDF's font metadata and the PDF's
outline (when present). Same input, same output, every run.

Headings (H1/H2/H3), bold and italic, super and subscript, hyperlinks,
bulleted and numbered lists with multi-level indentation, tables, and
paragraph flow are all preserved. YAML front matter is generated from PDF
metadata.

This package is vendored by `md-bridge` but works as a standalone CLI.

## When to use it

- You have a digitally-generated PDF (text plus font metadata intact) and
  want Markdown that preserves structure.
- Works for any language (EN, PT-BR, ES, DE, and so on): it reads font
  metadata, not natural language.

## When NOT to use it

- Scanned or image-only PDFs: run OCR first. Use `scripts/inspect_pdf.py` to
  check. Zero fonts or zero characters means the PDF is scanned.
- PDFs with heavy multi-column layout, math formulas, or floating figures.
  The output will need manual cleanup. See `REFERENCE.md` for the post-conversion
  checklist.

## Workflow

1. **Inspect** the PDF first:

   ```bash
   python packages/pdf-to-markdown/scripts/inspect_pdf.py "<input.pdf>"
   ```

   Reports: font size histogram, inferred body size, heading candidates, and
   whether the PDF is tagged (`/MarkInfo`, `/StructTreeRoot`, top structure
   tags).

2. **Convert**:

   ```bash
   python packages/pdf-to-markdown/scripts/convert.py "<input.pdf>" -o "output/<name>.md"
   ```

   Flags:

   - `--page-break`: insert `---` between pages
   - `--with-images`: extract images to `output/images/<pdf-stem>/` and
     reference them in the `.md` (default: off, no images pulled into the
     markdown)
   - `--inline-images`: embed images inline as base64 `data:` URIs so the `.md`
     is self-contained with no image files (overrides `--with-images`). Handy to
     move or email the file with its images intact. Trade-offs: base64 grows the
     file by ~1/3, and github.com does not render `data:` images (VS Code,
     pandoc, and browsers do).
   - `--no-front-matter`: skip YAML front matter
   - `--debug`: print inferred profile plus TOC entry count

3. **Review** using `REFERENCE.md` (the post-conversion checklist).

## What it produces

```markdown
---
title: "DDP Syllabus"
author: "Stan Bühne"
date: "2024-06-26"
source: "ddp_foundationlevel_syllabus_en_v2.0.2.pdf"
pages: 37
---

# Foundation Level

### Terms of Use

All contents of this document, especially texts, photographs, graphics...

| Education Unit | Title | Level | Duration |
| --- | --- | --- | --- |
| EU 1 | Motivation for Digital Design | L2 | 30 min. |
```

## What it detects

| Element | Source signal |
|---|---|
| H1 / H2 / H3 | Font size relative to body (top 3 larger sizes), plus PDF outline (`doc.get_toc()`) for canonical titles. |
| Section labels | Body-size text in a non-body font OR bold-only short standalone line goes to H3. |
| Bold / italic | Font flags (bit 4 / bit 1) plus font name contains "Bold"/"Italic"/"Oblique". |
| Superscript | Font flag bit 0 wraps text in `<sup>...</sup>`. |
| Hyperlinks | `page.get_links()` bboxes intersected with span bboxes produce `[text](url)`. |
| Bulleted lists | Lines starting with `▪ • ● ◦ ‣ ⁃ ∙` become `- `. |
| Numbered lists | `^\d+[.)]\s` or `^[a-z][.)]\s`. |
| List nesting | `(block.x0 - list_base_x0) / 18pt` produces 2-space-per-level indent. |
| Tables | `page.find_tables()` with empty-column drop and wrapped-row merge. |
| Paragraphs | Block-level plus merge when the predecessor ends mid-phrase AND the next starts lowercase or with `and`/`or`/`but`, a comma, or a hyphen. |
| Front matter | `doc.metadata` (title, author, creationDate, subject, keywords) becomes YAML. |
| TOC dot leaders | `Title ........ 12` is stripped. |
| Headers/footers | Top 4% / bottom 4% of page are dropped. |

## How the PDF outline helps

If the PDF has a TOC outline (`doc.get_toc()`), it is used as the source of
truth for chapter titles. Detected headings are matched against TOC entries;
on match, the canonical title and level replace what the heuristic found.
This fixes wrapped titles like "5 Structuring the building process from a
Digital Design" plus "perspective" automatically.

Tagged-PDF structure tags (`/H1`, `/P`, `/Table`) are detected by
`inspect_pdf.py` but not yet used for conversion. The outline already covers
most of the practical benefit.

## Cleanup behavior

- Re-running the converter on the same PDF wipes the prior images subdir
  before re-extracting (no stale files accumulate).
- Empty image dirs are removed at the end.
- The `.md` is overwritten in place.

## Files

- `README.md`: this file
- `REFERENCE.md`: capability table plus post-conversion checklist
- `scripts/inspect_pdf.py`: font usage histogram plus tagged-PDF detection
- `scripts/convert.py`: main converter
