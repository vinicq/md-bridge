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
  // This test drives two real md-to-pdf conversions: one on Convert, then a
  // second when the theme switch re-runs the queue, and the re-run is verified
  // with a poll budget up to 60s. The default 30s per-test ceiling is shorter
  // than that work, so the slower CI engines were killed at 30s mid-re-run
  // before the new blob landed. Lift the ceiling to match the work it does, the
  // same way batch.spec.ts does for its sequential conversions; no assertion is
  // weakened.
  test.setTimeout(120_000)

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
