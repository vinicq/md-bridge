import { expect, test } from '@playwright/test'

test.beforeEach(async ({ context }) => {
  await context.addInitScript(() => {
    window.localStorage.setItem('md-bridge:locale', 'en')
  })
})

test('Themes list loads from the real /api/themes endpoint', async ({ page }) => {
  await page.goto('/convert/md-to-pdf')
  await expect(page.getByText('Default A4')).toBeVisible({ timeout: 15_000 })

  const defaultRadio = page.getByLabel('Default A4')
  await expect(defaultRadio).toBeChecked()
})

test('Generated PDF preview uses the default theme', async ({ page }) => {
  await page.goto('/convert/md-to-pdf')
  await expect(page.getByText('Default A4')).toBeVisible({ timeout: 15_000 })

  await page
    .getByLabel(/pasted markdown/i)
    .fill('---\ntitle: "Themed"\n---\n\n# Title\n\nparagraph')
  await page.getByRole('button', { name: /generate pdf/i }).click()

  const iframe = page.locator('iframe.pdf-preview')
  await expect(iframe).toBeVisible({ timeout: 60_000 })
  await expect(iframe).toHaveAttribute('src', /^blob:/)
})
