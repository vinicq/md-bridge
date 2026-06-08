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

test('Batch: two PDFs queue up, run sequentially, each downloadable', async ({ page }) => {
  // Two real /api/pdf-to-md round-trips run sequentially here, and the
  // done-count assertion below already waits up to 120s for them. The default
  // 30s per-test budget is shorter than that wait, so on the slower webkit
  // engine the whole test was killed at 30s before the conversions finished,
  // flaking on unrelated PRs (#233). Lift only this test's ceiling to match the
  // work it does; chromium/firefox finish well under it, and no assertion is
  // weakened (still two sequential conversions, each downloadable).
  test.setTimeout(150_000)

  await page.goto('/convert/pdf-to-md')

  // Drop the same ISTQB fixture twice through the file input (multiple is on).
  await page.locator('input[type="file"]').setInputFiles([ISTQB, ISTQB])

  // The batch list shows two queued rows.
  const list = page.locator('.batch__list')
  await expect(list).toBeVisible({ timeout: 30_000 })
  await expect(list.locator('.batch__row')).toHaveCount(2)
  await expect(page.getByText(/2 files queued/i)).toBeVisible()

  // Kick the run.
  await page.getByRole('button', { name: /convert all/i }).click()

  // Both rows finish (real /api/pdf-to-md round-trips for each).
  await expect(list.locator('.batch__row--done')).toHaveCount(2, { timeout: 120_000 })

  // Per-item download is available (label is the localized .md download text).
  const firstDownload = list.locator('.batch__row').first().getByRole('button', {
    name: /download \.md/i,
  })
  // Filter to the .md download: with the source-PDF preview (#15), headless
  // Chromium (which lacks the inline PDF viewer) emits a download for the
  // previewed PDF blob, so the page can produce more than one download event.
  const dl = page.waitForEvent('download', {
    predicate: (d) => d.suggestedFilename().endsWith('.md'),
  })
  await firstDownload.click()
  const file = await dl
  expect(file.suggestedFilename()).toMatch(/\.md$/)
})

test('Batch: skipping a stuck item lets the rest finish', async ({ page }) => {
  // Hold the first conversion request open forever (simulates the backgrounded
  // tab hang from issue #138); let every later request reach the real API.
  let seen = 0
  await page.route('**/api/pdf-to-md', (route) => {
    seen += 1
    if (seen === 1) return // never settle: this item is stuck in `converting`
    return route.continue()
  })

  await page.goto('/convert/pdf-to-md')
  await page.locator('input[type="file"]').setInputFiles([ISTQB, ISTQB])
  await page.getByRole('button', { name: /convert all/i }).click()

  // First row is stuck converting and exposes the Skip button.
  const firstRow = page.locator('.batch__row').first()
  const skip = firstRow.getByRole('button', { name: /skip/i })
  await expect(skip).toBeVisible({ timeout: 30_000 })
  await skip.click()

  // The skipped item errors out and the second item still completes: the loop
  // is not blocked behind the stuck request.
  await expect(firstRow).toHaveClass(/batch__row--error/, { timeout: 30_000 })
  await expect(page.locator('.batch__row--done')).toHaveCount(1, { timeout: 120_000 })
  await expect(page.locator('.batch__row--converting')).toHaveCount(0)
  // The batch finished, so Clear is enabled again (it is disabled while running).
  await expect(page.getByRole('button', { name: /clear list/i })).toBeEnabled()
})

test('Batch: Download all bundles the done items into a single .zip', async ({ page }) => {
  await page.route('**/api/pdf-to-md', (route) =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        md: '# hello\n\ncontent',
        front_matter: {},
        warnings: [],
        stats: { headings: 1, tables: 0, bullets: 0 },
      }),
    }),
  )
  await page.goto('/convert/pdf-to-md')
  await page.locator('input[type="file"]').setInputFiles([ISTQB, ISTQB])
  await page.getByRole('button', { name: /convert all/i }).click()
  await expect(page.locator('.batch__row--done')).toHaveCount(2, { timeout: 30_000 })

  // Filter to the .zip bundle: the source-PDF preview (#15) can emit a separate
  // PDF-blob download in headless Chromium (no inline viewer).
  const dl = page.waitForEvent('download', {
    predicate: (d) => d.suggestedFilename().endsWith('.zip'),
  })
  await page.getByRole('button', { name: /download all \(2\)/i }).click()
  const file = await dl
  expect(file.suggestedFilename()).toBe('markdown.zip')
})

test('Batch: clearing the list cancels and empties the queue', async ({ page }) => {
  await page.goto('/convert/pdf-to-md')
  await page.locator('input[type="file"]').setInputFiles([ISTQB, ISTQB])
  await expect(page.locator('.batch__row')).toHaveCount(2)

  await page.getByRole('button', { name: /clear list/i }).click()
  await expect(page.locator('.batch__list')).toHaveCount(0)
})
