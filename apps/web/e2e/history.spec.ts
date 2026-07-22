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

// A mocked, deterministic /api/pdf-to-md response so these journeys assert the
// history UI, not the converter (the real round-trip is covered in batch.spec).
async function mockConvert(page: import('@playwright/test').Page) {
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
}

test.beforeEach(async ({ context }) => {
  await context.addInitScript(() => {
    window.localStorage.setItem('md-bridge:locale', 'en')
  })
})

test('History: a finished conversion appears and re-downloads from the session blob', async ({
  page,
}) => {
  await mockConvert(page)
  await page.goto('/convert/pdf-to-md')

  await page.locator('input[type="file"]').setInputFiles(ISTQB)
  await page.getByRole('button', { name: /convert all/i }).click()

  // The recent row shows up, marked done, with the source filename.
  const row = page.locator('.recent-row')
  await expect(row).toHaveCount(1, { timeout: 30_000 })
  await expect(row).toContainText('istqb-ctal-ta-syllabus-en.pdf')
  await expect(page.locator('.recent-row--done')).toHaveCount(1)

  // Re-download pulls the in-session blob back out as an .md file.
  const dl = page.waitForEvent('download', {
    predicate: (d) => d.suggestedFilename().endsWith('.md'),
  })
  await page.getByRole('button', { name: /re-download the result of/i }).click()
  const file = await dl
  expect(file.suggestedFilename()).toBe('istqb-ctal-ta-syllabus-en.md')
})

test('History: after a reload the result is expired and Re-run asks for the file instead of faking a run', async ({
  page,
}) => {
  await mockConvert(page)
  await page.goto('/convert/pdf-to-md')
  await page.locator('input[type="file"]').setInputFiles(ISTQB)
  await page.getByRole('button', { name: /convert all/i }).click()
  await expect(page.locator('.recent-row--done')).toHaveCount(1, { timeout: 30_000 })

  // Reload: metadata survives in localStorage but the session blob and the
  // source File do not, so the row rehydrates as expired.
  await page.reload()
  await expect(page.locator('.recent-row')).toHaveCount(1)
  await expect(page.locator('.recent-row--expired')).toHaveCount(1)
  await expect(
    page.getByRole('button', { name: /re-download the result of/i }),
  ).toHaveCount(0)
  // The batch queue is empty after the reload.
  await expect(page.locator('.batch__row')).toHaveCount(0)

  // Re-run with no source File must not fabricate a conversion: it surfaces an
  // honest prompt to re-add the file and adds nothing to the queue.
  await page.getByRole('button', { name: /re-run the conversion of/i }).click()
  await expect(page.getByText(/add istqb-ctal-ta-syllabus-en\.pdf again to re-run/i)).toBeVisible()
  await expect(page.locator('.batch__row')).toHaveCount(0)
})
