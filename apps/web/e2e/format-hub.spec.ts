import { test, expect } from '@playwright/test'
import AxeBuilder from '@axe-core/playwright'

/**
 * Format hub matrix on Home (#237).
 *
 * Drives the happy path the matrix promises: from Home, a shipped pair that has
 * a converter page navigates to that converter and produces output. MD-to-PDF is
 * used because it is the shipped pair with a UI page; the MD-to-DOCX download
 * lives with the future md-to-docx converter-page issue (that pair ships in the
 * API but has no page yet, so the matrix renders it non-navigable, not a dead
 * link). Also runs axe over Home with the new pills/links present.
 */

const SAMPLE_MD = `# Hub sample\n\nParagraph from the format hub flow.\n`

test.beforeEach(async ({ context }) => {
  await context.addInitScript(() => {
    window.localStorage.setItem('md-bridge:locale', 'en')
  })
})

test('a shipped pair with a page navigates from the matrix to a working converter', async ({
  page,
}) => {
  await page.goto('/')

  // The matrix renders from GET /api/formats.
  await expect(page.getByRole('heading', { name: /all conversions/i })).toBeVisible()

  // The shipped, page-backed pair is a real link; the shipped-without-page pair
  // (Markdown → DOCX) shows but is not a navigable link to a dead route.
  const docxCell = page.getByText('Markdown → DOCX')
  await expect(docxCell).toBeVisible()
  await expect(page.getByRole('link', { name: /Markdown → DOCX/i })).toHaveCount(0)

  await page.getByRole('link', { name: /open converter.*Markdown → PDF/i }).click()
  await expect(page).toHaveURL(/\/convert\/md-to-pdf$/)

  await page.getByLabel(/pasted markdown/i).fill(SAMPLE_MD)
  await page.getByRole('button', { name: /^convert$/i }).click()

  const iframe = page.locator('iframe.pdf-preview')
  await expect(iframe).toBeVisible({ timeout: 60_000 })
  await expect(iframe).toHaveAttribute('src', /^blob:/)
})

test('Home stays axe-clean with the format matrix present', async ({ page }) => {
  await page.goto('/', { waitUntil: 'networkidle' })
  await expect(page.getByRole('heading', { name: /all conversions/i })).toBeVisible()

  const results = await new AxeBuilder({ page })
    .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
    .analyze()
  expect(results.violations).toEqual([])
})
