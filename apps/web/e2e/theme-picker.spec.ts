import { expect, test } from '@playwright/test'

const SAMPLE_MD = `---
title: "Theme picker E2E"
---

# Hello themes

Paragraph text with **bold**.
`

test.beforeEach(async ({ context }) => {
  // Note: init scripts re-run on every navigation (including reload), so this
  // only seeds the locale. The theme is left to its natural 'default' so the
  // persistence assertion after reload reflects the real localStorage write.
  await context.addInitScript(() => {
    window.localStorage.setItem('md-bridge:locale', 'en')
  })
})

test('theme picker lists the API themes, persists the choice, and re-renders on switch', async ({
  page,
}) => {
  await page.goto('/convert/md-to-pdf')

  // The picker renders one tile per theme the backend registry returns.
  const radios = page.getByRole('radio')
  await expect(radios).toHaveCount(4)
  await expect(page.getByRole('radio', { name: /default/i })).toBeChecked()
  for (const name of ['Academic', 'Business', 'Minimal']) {
    await expect(page.locator('.theme-tile', { hasText: name })).toBeVisible()
  }

  // Convert once with the default theme and capture the preview source.
  await page.getByLabel(/pasted markdown/i).fill(SAMPLE_MD)
  await page.getByRole('button', { name: /^convert$/i }).click()

  const iframe = page.locator('iframe.pdf-preview')
  await expect(iframe).toBeVisible({ timeout: 60_000 })
  await expect(iframe).toHaveAttribute('src', /^blob:/)
  const firstSrc = await iframe.getAttribute('src')

  // Switching the theme re-runs the conversion; the preview points at a new blob.
  await page.locator('.theme-tile', { hasText: 'Academic' }).click()
  await expect(page.getByRole('radio', { name: /academic/i })).toBeChecked()
  await expect
    .poll(async () => iframe.getAttribute('src'), { timeout: 60_000 })
    .not.toBe(firstSrc)
  await expect(iframe).toHaveAttribute('src', /^blob:/)

  // The choice survives a reload.
  await page.reload()
  await expect(page.getByRole('radio', { name: /academic/i })).toBeChecked()
})
