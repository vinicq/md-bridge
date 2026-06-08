import { test, expect } from '@playwright/test'
import AxeBuilder from '@axe-core/playwright'
import { execFileSync } from 'node:child_process'
import { existsSync, mkdtempSync } from 'node:fs'
import { tmpdir } from 'node:os'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

/**
 * Honesty gate for the Markdown → DOCX converter page (#276).
 *
 * Drives the flow the format hub promises end to end: from the matrix on Home,
 * the Markdown → DOCX cell is now a real internal link (it gained a page), so we
 * click through, convert, download the .docx, and read the artifact BACK as a
 * zip with the stdlib. We assert the real package — PK zip magic, a
 * word/document.xml entry, and the converted body text — rather than trusting
 * the response MIME. Also runs axe over the new route (new a11y surface).
 */

const here = path.dirname(fileURLToPath(import.meta.url))
const repoRoot = path.resolve(here, '..', '..')

// Same resolution as playwright.config.ts: the API venv on a dev box, plain
// `python` on CI. read_docx.py uses only stdlib zipfile, so no extra dep.
function resolvePython(): string {
  const winVenv = path.join(repoRoot, 'apps', 'api', '.venv', 'Scripts', 'python.exe')
  const nixVenv = path.join(repoRoot, 'apps', 'api', '.venv', 'bin', 'python')
  if (existsSync(winVenv)) return winVenv
  if (existsSync(nixVenv)) return nixVenv
  return 'python'
}

const SAMPLE_MD = `# Docx honesty\n\nParagraph from the format hub DOCX flow.\n`

test.beforeEach(async ({ context }) => {
  await context.addInitScript(() => {
    window.localStorage.setItem('md-bridge:locale', 'en')
  })
})

test('Markdown → DOCX: matrix link, convert, and download a real .docx', async ({ page }) => {
  await page.goto('/')

  await expect(page.getByRole('heading', { name: /all conversions/i })).toBeVisible()

  // The pair now has a page, so its cell is a navigable converter link.
  await page.getByRole('link', { name: /open converter.*Markdown → DOCX/i }).click()
  await expect(page).toHaveURL(/\/convert\/md-to-docx$/)

  await page.getByLabel(/pasted markdown/i).fill(SAMPLE_MD)
  await page.getByRole('button', { name: /^convert$/i }).click()

  // Pull the produced DOCX down and read it back as a zip. Two "Download .docx"
  // buttons exist (top action bar + per-item row); the top one is the current
  // result.
  const downloadPromise = page.waitForEvent('download', {
    predicate: (d) => d.suggestedFilename().endsWith('.docx'),
  })
  await page.getByRole('button', { name: /download \.docx/i }).first().click()
  const download = await downloadPromise

  const dir = mkdtempSync(path.join(tmpdir(), 'md-bridge-docx-'))
  const docxPath = path.join(dir, 'out.docx')
  await download.saveAs(docxPath)

  const raw = execFileSync(resolvePython(), [path.join(here, 'read_docx.py'), docxPath], {
    encoding: 'utf-8',
  })
  const docx = JSON.parse(raw) as {
    zip_magic: string
    has_document_xml: boolean
    entry_count: number
    text: string
  }

  // Real Office Open XML package, not just a 200 with a docx MIME.
  expect(docx.zip_magic).toBe('504b0304') // PK\x03\x04
  expect(docx.has_document_xml).toBe(true)
  // The converted body text actually landed in the document.
  expect(docx.text).toContain('Docx honesty')
  expect(docx.text).toContain('Paragraph from the format hub DOCX flow.')
})

test('the md-to-docx route is axe-clean', async ({ page }) => {
  await page.goto('/convert/md-to-docx', { waitUntil: 'networkidle' })
  await expect(page.getByRole('heading', { name: /markdown to docx/i })).toBeVisible()

  const results = await new AxeBuilder({ page })
    .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
    .analyze()
  expect(results.violations).toEqual([])
})
