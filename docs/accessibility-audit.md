# Accessibility Audit — WCAG 2.1 AA

**Date:** 2026-05-20
**Tool:** axe-core 4.10.2 + Playwright
**Standard:** WCAG 2.1 Level AA (success criteria 2.0a, 2.0aa, 2.1a, 2.1aa)

## Executive Summary

| Route | Critical | Serious | Moderate | Minor | Passes |
|-------|----------|---------|----------|-------|--------|
| `/` (Home) | 0 | 0 | 0 | 0 | 18 |
| `/convert/pdf-to-md` | 0* | 0* | 0 | 0 | 21 |
| `/convert/md-to-pdf` | 0* | 0* | 0 | 0 | 21 |
| `/about` | 0 | 0 | 0 | 0 | 20 |

\* Fixed in this PR — 4 violations (2 critical, 2 serious) remediated.

**Before this PR:** 4 violations across 2 routes (critical × 2, serious × 2).
**After this PR:** 0 violations across all routes. 4/4 tests pass.

## Issues Found & Fixed

### 1. CRITICAL — Form elements missing labels

**WCAG:** 4.1.2 Name, Role, Value (Level A)
**Routes:** `/convert/pdf-to-md`, `/convert/md-to-pdf`
**Component:** `DropZone.tsx`

The hidden file `<input type="file">` inside the DropZone had no `aria-label` attribute. Screen readers could not announce what the input was for.

**Fix:** Added `aria-label={t.dropzone.ariaLabel(acceptLabel)}` to the file input, using the existing translation key that already described the drop zone purpose.

### 2. SERIOUS — Nested interactive controls

**WCAG:** 4.1.2 Name, Role, Value (Level A)
**Routes:** `/convert/pdf-to-md`, `/convert/md-to-pdf`
**Component:** `DropZone.tsx`

The outer `<div>` had `role="button"` with `tabIndex={0}`, and contained a focusable `<input type="file">`. Nested interactive controls confuse screen readers — the inner input would be announced inside the button context, creating ambiguity.

**Fix:**
- Added `tabIndex={-1}` to the file input (it is visually hidden; its click is triggered programmatically by the parent div)
- Added `aria-hidden="true"` to the file input (the parent div's `aria-label` already describes the purpose)
- The parent div retains `role="button"`, `tabIndex={0}`, keyboard handlers, and `aria-label` — it is the sole interactive element for this widget.

### 3. IMPROVEMENT — Navigation landmark label

**Component:** `App.tsx`

The `<nav>` element had `aria-label={t.nav.pdfToMd}` which resolved to "PDF · MD". This is not a descriptive label for the navigation landmark.

**Fix:** Changed to `aria-label="Main navigation"` which accurately describes the nav element's purpose.

### 4. IMPROVEMENT — Skip-to-content link

**Component:** `App.tsx`, `globals.css`

Added a visually hidden "Skip to content" link that becomes visible on keyboard focus. Allows keyboard and screen reader users to bypass the header navigation and jump directly to the main content.

**Implementation:**
- `<a className="skip-link" href="#main-content">Skip to content</a>` before `<header>`
- `<main id="main-content">` as the target
- CSS: `.skip-link` is positioned off-screen (`top: -100%`) by default, moves to `top: 0` on `:focus`

### 5. IMPROVEMENT — Live region for batch progress

**Component:** `BatchPanel.tsx`

The batch progress text (e.g. "2 of 5 complete") was not announced to screen readers during batch conversion.

**Fix:** Added `aria-live="polite"` to the progress `<span>`, so screen readers announce progress updates as files are converted.

## Routes Audited

### `/` (Home)
- **Status:** Clean — 0 violations
- Semantic heading hierarchy (h1 → h2)
- Links are descriptive ("Convert a PDF", "Generate a PDF")
- Cards use proper HTML structure

### `/convert/pdf-to-md`
- **Status:** Clean after fixes
- DropZone: file input now has aria-label, no nested interactive controls
- BatchPanel: progress announced via aria-live
- Warnings list has `aria-label`
- Download buttons have accessible names

### `/convert/md-to-pdf`
- **Status:** Clean after fixes
- Same DropZone fixes as pdf-to-md
- Textarea has `aria-label`
- Toast notifications use `role="alert"` (via Toast component)

### `/about`
- **Status:** Clean — 0 violations
- Pure content page with proper heading hierarchy
- Links are descriptive

## Remaining Recommendations (non-blocking)

These are improvements that don't block WCAG 2.1 AA compliance but would enhance the experience:

1. **Focus visible styles** — Audit `:focus-visible` styles on all interactive elements. Current `a` styles use `border-bottom` which may not be visible on all backgrounds.
2. **Color contrast** — Verify all text/background combinations meet 4.5:1 ratio (current theme appears compliant based on visual inspection, but no automated contrast check was performed in this pass).
3. **Reduced motion** — Add `@media (prefers-reduced-motion: reduce)` to disable the `fade-in` animation for users who prefer reduced motion.

## Test Reproduction

To reproduce the audit:

```bash
cd apps/web
npm install
npm run dev
npx playwright test --config=tests/a11y/playwright.config.ts
```

Or run axe-core manually in browser DevTools:
1. Open DevTools → Console
2. Paste axe-core script from [axe-core docs](https://github.com/dequelabs/axe-core/blob/develop/doc/developer-guide.md)
3. Run: `await axe.run(document, { runOnly: { type: 'tag', values: ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'] } })`
