// Reusable preview samples (#398). Shared by the theme library (#392) and the
// md-to-pdf live preview (#397) so a theme can be judged against realistic
// content. The body is fixed Markdown (English); only the tab LABEL is
// localized, through `t.previewSamples[id]`. Kept as Markdown, not HTML, so the
// preview renders through the same pipeline the converter uses, offline.

export type PreviewSampleId =
  | 'document'
  | 'article'
  | 'resume'
  | 'email'
  | 'contract'
  | 'blog'

export interface PreviewSample {
  id: PreviewSampleId
  markdown: string
}

const DOCUMENT = `# Heading One

A paragraph with **bold** and *italic* text, plus \`inline code\`.

## Subheading

- First item
- Second item
- Third item

| Column A | Column B |
| --- | --- |
| 1 | 2 |
| 3 | 4 |

> A short blockquote to show the quote treatment.
`

const ARTICLE = `# Deterministic Document Conversion at Scale

Ana Ribeiro, John Carter

> **Abstract.** A heuristic, model-free pipeline that converts between PDF and
> Markdown with identical output on every run. It favours reproducibility over
> fidelity and needs no cloud service.

## 1. Introduction

Document conversion pipelines are often stochastic: the same input yields
slightly different output across runs. We argue that determinism is a
first-class requirement for archival and legal workflows.

## 2. Method

PDFs are parsed with PyMuPDF; headings are recovered from font size and the
document outline, and tables via \`find_tables\`.

### 2.1 Heuristics

- Heading detection by font-size clustering
- List recovery from bullet glyphs and numbered patterns
- Table extraction with row and column inference

## 3. Results

| Corpus | Byte-identical |
| --- | --- |
| ISTQB syllabus | 100% |
| Mixed reports | 100% |

## References

1. A. Ribeiro. *Reproducible Documents.* J. Doc. Eng., 2025.
2. J. Carter. *Local-first Tooling.* 2026.
`

const RESUME = `# Marina Alves

Senior Software Engineer · marina@example.com · github.com/marina

## Summary

Backend engineer with 8 years building deterministic document pipelines and
self-hosted tools.

## Experience

### Staff Engineer, md-bridge Labs (2022 - present)

- Led the PDF and Markdown conversion engine with fully deterministic output.
- Cut render time 40% with a headless-Chromium pipeline.

### Backend Engineer, Acme Docs (2018 - 2022)

- Built the theming system used by 12k documents per day.

## Education

**BSc Computer Science** - Universidade Federal, 2017

## Skills

- **Languages:** Python, TypeScript, Go
- **Tools:** Playwright, FastAPI, React
`

const EMAIL = `# Your monthly md-bridge digest

Hi Marina,

Here is what shipped this month across the converter and the theme library.

## What is new

- Ten new PDF themes, including Slate and Techbook
- Live theme preview with syntax highlighting
- Mermaid diagrams rendered at print time

> Same input, same output, every run.

[Read the release notes](https://vinicq.github.io/md-bridge)

---

You are receiving this because you starred md-bridge on GitHub.
`

const CONTRACT = `# Service Agreement

Contract No. MB-2026-0142

This Service Agreement (the "Agreement") is entered into by and between
**md-bridge Labs Ltda.** ("Provider") and **Client Name S.A.** ("Client").

## 1. Definitions

- **Services:** the document conversion software and support described in Exhibit A.
- **Confidential Information:** any non-public information disclosed by either party.

## 2. Scope of Services

1. Provider shall deliver the Services per the specifications in Exhibit A.
2. Any change to the scope must be agreed in writing and signed by both parties.
3. Provider warrants the Services will conform to the documentation.

## 3. Term and Termination

This Agreement commences on the Effective Date and continues for **twelve (12)
months**, renewing automatically unless either party gives thirty (30) days
written notice.

## 4. Fees

| Item | Amount (USD) |
| --- | --- |
| License (annual) | 12,000.00 |
| Support and maintenance | 3,600.00 |

## 5. Governing Law

This Agreement is governed by the laws of the applicable jurisdiction, without
regard to its conflict-of-laws provisions.
`

const BLOG = `# Why we made md-bridge deterministic

By Marina Alves · 12 min read · 14 July 2026

Most document converters are a little bit random. Run the same file twice and
you get two subtly different outputs. For a note-taking app that is fine. For
archives, audits, and legal work, it is a quiet disaster.

## The problem with "good enough"

When a pipeline leans on a model or a heuristic that depends on timing, the
output drifts. We wanted the opposite: **same input, same output, every run**.

> Determinism is not a feature you add at the end. It is a constraint you
> design around from day one.

## How it works

We parse PDFs with hand-written rules over \`PyMuPDF\` and render Markdown through
headless Chromium. No inference, no network, no surprises.

- Headings recovered by font size and outline
- Tables extracted with \`find_tables\`
- Everything runs on your machine

---

*Thanks for reading. Share it with a teammate who fights with document pipelines.*
`

export const PREVIEW_SAMPLES: PreviewSample[] = [
  { id: 'document', markdown: DOCUMENT },
  { id: 'article', markdown: ARTICLE },
  { id: 'resume', markdown: RESUME },
  { id: 'email', markdown: EMAIL },
  { id: 'contract', markdown: CONTRACT },
  { id: 'blog', markdown: BLOG },
]
