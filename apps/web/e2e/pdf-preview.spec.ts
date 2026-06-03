import { expect, test } from '@playwright/test'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const here = path.dirname(fileURLToPath(import.meta.url))
const ISTQB = path.resolve(here, '..', '..', 'api', 'tests', 'fixtures', 'istqb-ctal-ta-syllabus-en.pdf')

test.beforeEach(async ({ context }) => {
  await context.addInitScript(() => {
    window.localStorage.setItem('md-bridge:locale', 'en')
  })
})

test('desktop: source PDF and converted Markdown show side by side', async ({ page }) => {
  await page.setViewportSize({ width: 1280, height: 1000 })
  await page.goto('/convert/pdf-to-md')
  await page.locator('input[type="file"]').setInputFiles(ISTQB)

  // The source PDF pane renders on drop, before converting: a same-origin blob
  // iframe whose document is reachable (the wait condition, not a fixed sleep).
  const frame = page.locator('iframe.compare__frame')
  await expect(frame).toBeVisible({ timeout: 30_000 })
  await expect(frame).toHaveAttribute('src', /^blob:/)
  await expect(frame).toHaveAttribute('title', /source pdf: istqb/i)

  // The diagnostic strip describes the previewed PDF.
  await expect(page.locator('.diag--strip')).toContainText(/pages/i)

  // No tablist at desktop width; both panes are laid out by the grid.
  await expect(page.getByRole('tablist')).toHaveCount(0)

  // Convert: the Markdown pane fills with a real extracted heading.
  await page.getByRole('button', { name: /convert all/i }).click()
  await expect(page.locator('.compare__pane--md h1, .compare__pane--md h2').first()).toBeVisible({
    timeout: 60_000,
  })
})

test('mobile: tabs swap between the PDF and Markdown panes', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 900 })
  await page.goto('/convert/pdf-to-md')
  await page.locator('input[type="file"]').setInputFiles(ISTQB)

  const tablist = page.getByRole('tablist')
  await expect(tablist).toBeVisible({ timeout: 30_000 })

  // Markdown is the default active tab; its panel is visible, the PDF panel is hidden.
  const pdfTab = page.getByRole('tab', { name: 'PDF' })
  const mdTab = page.getByRole('tab', { name: 'Markdown' })
  await expect(mdTab).toHaveAttribute('aria-selected', 'true')
  await expect(page.locator('#compare-panel-md')).toBeVisible()
  await expect(page.locator('#compare-panel-pdf')).toBeHidden()

  // Switch to the PDF tab: its panel (the source iframe) becomes visible.
  await pdfTab.click()
  await expect(pdfTab).toHaveAttribute('aria-selected', 'true')
  await expect(page.locator('#compare-panel-pdf')).toBeVisible()
  await expect(page.locator('#compare-panel-md')).toBeHidden()
  await expect(page.locator('iframe.compare__frame')).toHaveAttribute('src', /^blob:/)
})
