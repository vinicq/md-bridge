import { expect, test } from '@playwright/test'

test.beforeEach(async ({ context }) => {
  await context.addInitScript(() => window.localStorage.setItem('md-bridge:locale', 'en'))
})

test('Presets: save, persist across reload, apply, export and re-import', async ({ page }) => {
  await page.goto('/convert/md-to-pdf')

  // Save the current options as a named preset.
  await page.getByRole('button', { name: 'Save current' }).click()
  await page.getByRole('textbox', { name: /Preset name/i }).fill('Briefs')
  await page.getByRole('button', { name: 'Save' }).click()

  const chip = page.getByRole('button', { name: /Apply preset Briefs/i })
  await expect(chip).toBeVisible()
  await expect(page.getByText(/1 saved/i)).toBeVisible()

  // Persist across a reload (metadata lives in localStorage).
  await page.reload()
  await expect(page.getByRole('button', { name: /Apply preset Briefs/i })).toBeVisible()

  // Applying marks it active.
  await page.getByRole('button', { name: /Apply preset Briefs/i }).click()
  await expect(page.getByRole('button', { name: /Apply preset Briefs/i })).toHaveAttribute(
    'aria-current',
    'true',
  )

  // Export downloads a JSON file.
  const dl = page.waitForEvent('download', {
    predicate: (d) => d.suggestedFilename().endsWith('.json'),
  })
  await page.getByRole('button', { name: 'Export JSON' }).click()
  const file = await dl
  const savedPath = await file.path()

  // Delete the preset: the row empties.
  await page.getByRole('button', { name: /Delete preset Briefs/i }).click()
  await expect(page.getByRole('button', { name: /Apply preset Briefs/i })).toHaveCount(0)

  // Re-import the exported file: the preset comes back.
  await page.locator('.presets input[type="file"]').setInputFiles(savedPath!)
  await expect(page.getByRole('button', { name: /Apply preset Briefs/i })).toBeVisible()
})

test('Presets: a malformed import is rejected with a toast, no preset added', async ({ page }) => {
  await page.goto('/convert/md-to-pdf')

  await page.locator('.presets input[type="file"]').setInputFiles({
    name: 'bad.json',
    mimeType: 'application/json',
    buffer: Buffer.from('{ not valid json'),
  })

  await expect(page.getByText(/No valid md-bridge presets/i)).toBeVisible()
  // Nothing was saved.
  await expect(page.locator('.preset-chip').filter({ hasNotText: 'Save current' })).toHaveCount(0)
})
