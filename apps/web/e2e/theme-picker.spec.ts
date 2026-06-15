import { expect, test } from '@playwright/test'

const SAMPLE_MD = `---
title: "Theme picker E2E"
---

# Hello themes

Paragraph text with **bold**.
`

test.beforeEach(async ({ context }) => {
  await context.addInitScript(() => {
    window.localStorage.setItem('md-bridge:locale', 'en')
  })
})

test('theme picker lists API themes, persists choice, and re-renders on switch', async ({
  page,
}) => {
  await page.goto('/convert/md-to-pdf')

  // The select renders with at least the core themes from the backend registry.
  const select = page.getByRole('combobox', { name: /theme/i })
  await expect(select).toBeVisible()
  await expect(select).toHaveValue('default')
  for (const name of ['Default', 'Academic', 'Business', 'Minimal']) {
    await expect(page.getByRole('option', { name })).toBeAttached()
  }

  // Convert once with the default theme and capture the preview source.
  await page.getByLabel(/pasted markdown/i).fill(SAMPLE_MD)
  await page.getByRole('button', { name: /^convert$/i }).click()

  const iframe = page.locator('iframe.pdf-preview')
  await expect(iframe).toBeVisible({ timeout: 60_000 })
  await expect(iframe).toHaveAttribute('src', /^blob:/)
  const firstSrc = await iframe.getAttribute('src')

  // Switching the theme re-runs the conversion; the preview points at a new blob.
  await page.getByRole('combobox', { name: /theme/i }).selectOption('academic')
  await expect(select).toHaveValue('academic')
  await expect
    .poll(async () => iframe.getAttribute('src'), { timeout: 60_000 })
    .not.toBe(firstSrc)
  await expect(iframe).toHaveAttribute('src', /^blob:/)

  // The choice survives a reload.
  await page.reload()
  await expect(page.getByRole('combobox', { name: /theme/i })).toHaveValue('academic')
})
