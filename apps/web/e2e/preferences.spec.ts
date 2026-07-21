import { test, expect } from '@playwright/test'

/**
 * Preferences page (#64).
 *
 * Two persistence paths across the store boundaries the page touches: dark mode
 * (owned by the theme provider) survives a round-trip through another route, and
 * the accent colour (owned by the unified prefs store) survives a full reload as
 * the `--c-accent` variable on :root.
 */

test.beforeEach(async ({ context }) => {
  await context.addInitScript(() => {
    window.localStorage.setItem('md-bridge:locale', 'en')
  })
})

test('dark mode toggled here persists across navigation', async ({ page }) => {
  await page.goto('/preferences')

  const darkSwitch = page.getByRole('switch', { name: /dark mode/i })
  await expect(darkSwitch).toHaveAttribute('aria-checked', 'false')
  await darkSwitch.click()
  await expect(darkSwitch).toHaveAttribute('aria-checked', 'true')
  await expect(page.locator('html')).toHaveAttribute('data-theme', 'dark')

  // Leave and come back: the choice holds.
  await page.getByRole('link', { name: /^about$/i }).click()
  await expect(page).toHaveURL(/\/about$/)
  await page.goBack()
  await expect(page.locator('html')).toHaveAttribute('data-theme', 'dark')
  await expect(page.getByRole('switch', { name: /dark mode/i })).toHaveAttribute(
    'aria-checked',
    'true',
  )
})

test('accent colour applies to :root and survives a reload', async ({ page }) => {
  await page.goto('/preferences')

  await page.getByRole('radio', { name: /green/i }).click()
  const accentAfterPick = await page.evaluate(() =>
    document.documentElement.style.getPropertyValue('--c-accent').trim(),
  )
  expect(accentAfterPick).toBe('#2e7d4a')

  await page.reload()
  const accentAfterReload = await page.evaluate(() =>
    document.documentElement.style.getPropertyValue('--c-accent').trim(),
  )
  expect(accentAfterReload).toBe('#2e7d4a')
})
