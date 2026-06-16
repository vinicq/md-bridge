import { expect, test } from '@playwright/test'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const here = path.dirname(fileURLToPath(import.meta.url))
const ISTQB = path.resolve(
  here,
  '..',
  '..',
  'api',
  'tests',
  'fixtures',
  'istqb-ctal-ta-syllabus-en.pdf',
)

test.beforeEach(async ({ context }) => {
  await context.addInitScript(() => {
    window.localStorage.setItem('md-bridge:locale', 'en')
  })
})

test('ISTQB syllabus converts to Markdown end-to-end', async ({ page }) => {
  await page.goto('/convert/pdf-to-md')

  await page.locator('input[type="file"]').setInputFiles(ISTQB)

  // The diagnostic panel comes from a real /api/inspect-pdf round-trip.
  await expect(page.getByText('Pages')).toBeVisible({ timeout: 60_000 })
  // ISTQB CTAL-TA is a multi-page document; the page count must reflect that.
  await expect(page.locator('.diag__grid')).toContainText(/[1-9][0-9]+/)

  await page.getByRole('button', { name: /convert all/i }).click()

  // The markdown preview shows a real heading extracted from the syllabus.
  await expect(
    page.locator('.md-preview h1, .md-preview h2').first(),
  ).toBeVisible({ timeout: 60_000 })

  // Download flow: the .md file produced by the heuristic converter starts with
  // a YAML front-matter header.
  // Filter to the .md download: headless Chromium can emit blob downloads for
  // other page resources, so predicate to the .md filename.
  const downloadPromise = page.waitForEvent('download', {
    predicate: (d) => d.suggestedFilename().endsWith('.md'),
  })
  await page.getByRole('button', { name: /download \.md/i }).click()
  const download = await downloadPromise
  const stream = await download.createReadStream()
  expect(stream).not.toBeNull()
  const chunks: Buffer[] = []
  await new Promise<void>((resolve, reject) => {
    stream!.on('data', (chunk) => chunks.push(Buffer.from(chunk)))
    stream!.on('end', () => resolve())
    stream!.on('error', reject)
  })
  const head = Buffer.concat(chunks).toString('utf-8').slice(0, 400)
  expect(head.startsWith('---\ntitle:')).toBeTruthy()
  expect(head).toMatch(/source:.*istqb/i)
})

test('ISTQB syllabus inspect diagnostics show expected fields', async ({ page }) => {
  await page.goto('/convert/pdf-to-md')
  await page.locator('input[type="file"]').setInputFiles(ISTQB)
  await expect(page.getByText('Pages')).toBeVisible({ timeout: 60_000 })
  await expect(page.getByText('Body')).toBeVisible()
  await expect(page.getByText('Detected headings')).toBeVisible()
  // ISTQB syllabi are born digital, not scanned.
  await expect(page.getByText(/run ocr/i)).toHaveCount(0)
})
