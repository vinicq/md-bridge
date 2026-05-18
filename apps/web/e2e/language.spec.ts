import { expect, test } from '@playwright/test'

test('Language toggle switches the whole UI between EN and PT', async ({ page }) => {
  // Start with no stored locale so the provider falls back to its default.
  await page.goto('/')
  // Force EN to make assertions deterministic regardless of navigator language.
  await page.evaluate(() => window.localStorage.setItem('md-bridge:locale', 'en'))
  await page.reload()

  await expect(page.getByRole('heading', { level: 1 })).toContainText(/honest conversions/i)

  // Flip to PT via the header button.
  await page.getByRole('button', { name: /portugu/i }).click()
  await expect(page.getByRole('heading', { level: 1 })).toContainText(/conversões honestas/i)

  // The choice survives a reload (localStorage is the source of truth).
  await page.reload()
  await expect(page.getByRole('heading', { level: 1 })).toContainText(/conversões honestas/i)
})
