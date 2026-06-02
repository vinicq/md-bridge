import { expect, test } from '@playwright/test'

// The /contribute/i18n route is also in the axe ROUTES sweep (audit.spec.ts),
// so accessibility is covered there. These cover the interactive flow.
test.describe('Language Workshop (#214)', () => {
  test('a draft edit persists across a reload', async ({ page }) => {
    await page.goto('/contribute/i18n')
    const first = page.getByRole('textbox').first()
    await first.fill('valor de teste unico para persistir')
    await page.reload()
    await expect(page.getByRole('textbox').first()).toHaveValue(
      'valor de teste unico para persistir',
    )
  })

  test('offers TypeScript and JSON export actions', async ({ page }) => {
    await page.goto('/contribute/i18n')
    await expect(page.getByRole('button', { name: /copy as typescript/i })).toBeEnabled()
    await expect(page.getByRole('button', { name: /copy as json/i })).toBeEnabled()
  })
})
