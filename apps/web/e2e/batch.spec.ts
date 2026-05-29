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
  const dl = page.waitForEvent('download')
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

test('Batch: clearing the list cancels and empties the queue', async ({ page }) => {
  await page.goto('/convert/pdf-to-md')
  await page.locator('input[type="file"]').setInputFiles([ISTQB, ISTQB])
  await expect(page.locator('.batch__row')).toHaveCount(2)

  await page.getByRole('button', { name: /clear list/i }).click()
  await expect(page.locator('.batch__list')).toHaveCount(0)
})
