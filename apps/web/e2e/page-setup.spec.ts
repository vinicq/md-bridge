import { test, expect } from '@playwright/test'
import AxeBuilder from '@axe-core/playwright'
import { execFileSync } from 'node:child_process'
import { existsSync, mkdtempSync } from 'node:fs'
import { tmpdir } from 'node:os'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

/**
 * Honesty gate for the page-setup panel (#249).
 *
 * The panel wires page size / margins / header & footer slots to
 * options.page_setup. This spec fills it with a non-default geometry plus token
 * header/footer text, converts, then reads the produced PDF back with PyMuPDF
 * and asserts the REAL page — its dimensions and the substituted running text —
 * rather than trusting the request payload. It also runs axe over the page with
 * the panel filled, since the panel introduces a11y attributes (nested
 * fieldset/legend + a shared aria-describedby).
 */

const here = path.dirname(fileURLToPath(import.meta.url))
const repoRoot = path.resolve(here, '..', '..')

// Same resolution as playwright.config.ts: the API venv on a dev box, plain
// `python` on CI where the package is pip-installed. PyMuPDF ships with the API.
function resolvePython(): string {
  const winVenv = path.join(repoRoot, 'apps', 'api', '.venv', 'Scripts', 'python.exe')
  const nixVenv = path.join(repoRoot, 'apps', 'api', '.venv', 'bin', 'python')
  if (existsSync(winVenv)) return winVenv
  if (existsSync(nixVenv)) return nixVenv
  return 'python'
}

// Front matter feeds {{title}}/{{author}}; the renderer substitutes them
// server-side from the YAML block, never from the print clock (#243).
const SAMPLE_MD = `---
title: "Honesty Gate"
author: "QA"
---

# Page setup honesty

Body paragraph so the page has real content.
`

test.beforeEach(async ({ context }) => {
  await context.addInitScript(() => {
    window.localStorage.setItem('md-bridge:locale', 'en')
  })
})

test('page-setup choices reach the renderer and change the real PDF', async ({ page }) => {
  await page.goto('/convert/md-to-pdf')
  await page.getByLabel(/pasted markdown/i).fill(SAMPLE_MD)

  // Non-default geometry: Letter (612×792pt) instead of the historic A4
  // (595×842pt), loose margins.
  await page.getByRole('combobox', { name: /page size/i }).selectOption('Letter')
  await page.getByRole('combobox', { name: /margins/i }).selectOption('loose')

  // Token header/footer in two different bands, scoped by their legends.
  await page.getByRole('group', { name: 'Header' }).getByLabel('Left').fill('{{title}}')
  await page.getByRole('group', { name: 'Footer' }).getByLabel('Center').fill('{{page}} / {{pages}}')

  // a11y sweep with the panel filled: the nested fieldsets and the shared
  // aria-describedby must not introduce a WCAG violation.
  const axe = await new AxeBuilder({ page })
    .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
    .analyze()
  expect(axe.violations).toEqual([])

  await page.getByRole('button', { name: /^convert$/i }).click()

  const iframe = page.locator('iframe.pdf-preview')
  await expect(iframe).toBeVisible({ timeout: 60_000 })

  // Pull the produced PDF down and read it back with PyMuPDF.
  const downloadPromise = page.waitForEvent('download', {
    predicate: (d) => d.suggestedFilename().endsWith('.pdf'),
  })
  // Two "Download .pdf" buttons exist (the top action bar + the per-item row);
  // the top one downloads the currently-previewed result.
  await page.getByRole('button', { name: /download \.pdf/i }).first().click()
  const download = await downloadPromise

  const dir = mkdtempSync(path.join(tmpdir(), 'md-bridge-pagesetup-'))
  const pdfPath = path.join(dir, 'out.pdf')
  await download.saveAs(pdfPath)

  const raw = execFileSync(resolvePython(), [path.join(here, 'read_pdf.py'), pdfPath], {
    encoding: 'utf-8',
  })
  const pdf = JSON.parse(raw) as { pages: number; width: number; height: number; text: string }

  // Real page geometry is Letter portrait, not the A4 default — proves page_size
  // reached the renderer and changed the box.
  expect(pdf.width).toBeGreaterThan(610)
  expect(pdf.width).toBeLessThan(614)
  expect(pdf.height).toBeGreaterThan(790)
  expect(pdf.height).toBeLessThan(794)

  // Header token substituted from front matter; footer page numbering present.
  expect(pdf.text).toContain('Honesty Gate')
  expect(pdf.text).toMatch(/1\s*\/\s*1/)
})
