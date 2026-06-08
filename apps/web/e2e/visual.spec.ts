import { expect, test } from '@playwright/test'

/**
 * Visual regression baselines for the public surface (#16).
 *
 * One full-page screenshot per route × locale × theme. The functional E2E
 * suite proves behaviour; this proves the rendered pixels, so a CSS change that
 * breaks the layout without breaking the event handlers fails here instead of
 * shipping.
 *
 * Determinism: theme and locale are pinned through localStorage before the app
 * boots (the same keys the app reads — `md-bridge:theme`, `md-bridge:locale`),
 * animations are frozen via reduced-motion plus a zero-duration stylesheet, and
 * the caret is hidden. Baselines are generated under Linux on CI only (see
 * `.github/workflows/visual-regression.yml`); local runs on Windows/macOS
 * differ in font rendering and must not be committed.
 *
 * Chromium only — Firefox/WebKit visual coverage is 3× the storage for marginal
 * value on a project that targets evergreen browsers (tracked in #37).
 */

const ROUTES = [
  { name: 'home', path: '/' },
  { name: 'pdf-to-md', path: '/convert/pdf-to-md' },
  { name: 'md-to-pdf', path: '/convert/md-to-pdf' },
  { name: 'md-to-docx', path: '/convert/md-to-docx' },
  { name: 'about', path: '/about' },
] as const

const LOCALES = ['en', 'pt', 'es'] as const
const THEMES = ['light', 'dark'] as const

// Kill transitions/animations and freeze the caret so a screenshot taken
// mid-transition can never flake the diff.
const FREEZE_CSS = `
  *, *::before, *::after {
    animation-duration: 0s !important;
    animation-delay: 0s !important;
    transition-duration: 0s !important;
    transition-delay: 0s !important;
    caret-color: transparent !important;
    scroll-behavior: auto !important;
  }
`

for (const route of ROUTES) {
  for (const locale of LOCALES) {
    for (const theme of THEMES) {
      test(`${route.name} — ${locale} — ${theme}`, async ({ page }) => {
        await page.emulateMedia({ reducedMotion: 'reduce' })
        await page.addInitScript(
          ([t, l]) => {
            window.localStorage.setItem('md-bridge:theme', t)
            window.localStorage.setItem('md-bridge:locale', l)
          },
          [theme, locale] as const,
        )
        await page.goto(route.path)
        // The app sets data-theme / lang on <html> from the pinned storage;
        // wait for that so the screenshot is never taken pre-hydration.
        await expect(page.locator('html')).toHaveAttribute('data-theme', theme)
        await page.addStyleTag({ content: FREEZE_CSS })
        await page.waitForLoadState('networkidle')

        await expect(page).toHaveScreenshot(`${route.name}-${locale}-${theme}.png`, {
          fullPage: true,
          animations: 'disabled',
        })
      })
    }
  }
}
