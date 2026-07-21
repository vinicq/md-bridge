import { test, expect } from '@playwright/test'

/**
 * Preferences page (#64).
 *
 * Dark mode (owned by the theme provider) toggled here survives a round-trip
 * through another route, and the manual reduce-motion toggle sets the
 * `data-reduce-motion` flag on <html> that the static spinner fallbacks read.
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

test('reduce-motion toggle sets the data-reduce-motion flag on <html>', async ({ page }) => {
  await page.goto('/preferences')

  const motionSwitch = page.getByRole('switch', { name: /reduce motion/i })
  await motionSwitch.click()
  await expect(motionSwitch).toHaveAttribute('aria-checked', 'true')
  await expect(page.locator('html')).toHaveAttribute('data-reduce-motion', 'true')
})
