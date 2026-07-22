import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { expect, test } from '@playwright/test'

const here = path.dirname(fileURLToPath(import.meta.url))
const FIXTURES = path.resolve(here, '..', '..', 'api', 'tests', 'fixtures')
const ISTQB = path.resolve(FIXTURES, 'istqb-ctal-ta-syllabus-en.pdf')
const CODE_SAMPLE = path.resolve(FIXTURES, 'code-sample.pdf')

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

// #218: the blockquote style only appears after a conversion, so the static
// route screenshots above never exercise it. Mock a conversion whose Markdown
// covers the quote variants (simple, nested, with a list and a code fence, and
// an attribution) and snapshot the rendered preview in both themes, so a pixel
// change in the quote treatment is caught here.
const BLOCKQUOTE_MD = [
  '# Blockquote styles',
  '',
  '> A simple single-line quote.',
  '',
  '> A quote that carries a [link](https://example.com) on the tint.',
  '',
  '> Outer quote.',
  '>',
  '> > A nested quote inside it.',
  '',
  '> A quote that carries a list:',
  '>',
  '> - first item',
  '> - second item',
  '>',
  '> ```js',
  '> const x = 1',
  '> ```',
  '',
  '> The quote ends with an attribution.',
  '>',
  '> Attribution: a cited source.',
].join('\n')

for (const theme of THEMES) {
  test(`blockquote preview — ${theme}`, async ({ page }) => {
    await page.emulateMedia({ reducedMotion: 'reduce' })
    await page.addInitScript(
      (t) => {
        window.localStorage.setItem('md-bridge:theme', t)
        window.localStorage.setItem('md-bridge:locale', 'en')
      },
      theme,
    )
    await page.route('**/api/pdf-to-md', (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          md: BLOCKQUOTE_MD,
          front_matter: {},
          warnings: [],
          stats: { headings: 1, tables: 0, bullets: 2 },
        }),
      }),
    )
    await page.goto('/convert/pdf-to-md')
    await expect(page.locator('html')).toHaveAttribute('data-theme', theme)
    await page.addStyleTag({ content: FREEZE_CSS })

    await page.locator('input[type="file"]').setInputFiles(ISTQB)
    await page.getByRole('button', { name: /convert all/i }).click()

    const preview = page.locator('.md-preview')
    await expect(preview.locator('blockquote').first()).toBeVisible({ timeout: 30_000 })
    await page.waitForLoadState('networkidle')

    await expect(preview).toHaveScreenshot(`blockquote-preview-${theme}.png`, {
      animations: 'disabled',
    })
  })
}

// #392: the theme library page. Its live-preview iframe renders theme CSS whose
// pixels are not stable to diff, so mask it; the baseline covers the page chrome
// (grid, filter, tabs, tiles) in both themes.
for (const theme of THEMES) {
  test(`theme library — ${theme}`, async ({ page }) => {
    await page.emulateMedia({ reducedMotion: 'reduce' })
    await page.addInitScript(
      (t) => {
        window.localStorage.setItem('md-bridge:theme', t)
        window.localStorage.setItem('md-bridge:locale', 'en')
      },
      theme,
    )
    await page.goto('/themes')
    await expect(page.locator('html')).toHaveAttribute('data-theme', theme)
    await page.addStyleTag({ content: FREEZE_CSS })
    await expect(page.getByRole('button', { name: /academic/i })).toBeVisible({ timeout: 30_000 })
    await page.waitForLoadState('networkidle')

    await expect(page).toHaveScreenshot(`theme-library-${theme}.png`, {
      fullPage: true,
      animations: 'disabled',
      mask: [page.locator('.theme-lib__frame')],
    })
  })
}

// #63: the recent-history panel only renders rows after a conversion, so the
// static pdf-to-md baseline above never exercises the status badges or the new
// warn-soft/strong tokens. Convert two files (mocked) so the panel carries a
// `done` row and a `needs_ocr` `warn` row, then snapshot just the panel in both
// themes. The age label ("m ago") is masked so the clock never flakes the diff.
for (const theme of THEMES) {
  test(`recent history panel — ${theme}`, async ({ page }) => {
    await page.emulateMedia({ reducedMotion: 'reduce' })
    await page.addInitScript(
      (t) => {
        window.localStorage.setItem('md-bridge:theme', t)
        window.localStorage.setItem('md-bridge:locale', 'en')
      },
      theme,
    )
    let calls = 0
    await page.route('**/api/pdf-to-md', (route) => {
      calls += 1
      const warnings = calls === 2 ? ['needs_ocr'] : []
      return route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          md: '# hello\n\ncontent',
          front_matter: {},
          warnings,
          stats: { headings: 1, tables: 0, bullets: 0 },
        }),
      })
    })
    await page.goto('/convert/pdf-to-md')
    await expect(page.locator('html')).toHaveAttribute('data-theme', theme)
    await page.addStyleTag({ content: FREEZE_CSS })

    await page.locator('input[type="file"]').setInputFiles([ISTQB, CODE_SAMPLE])
    await page.getByRole('button', { name: /convert all/i }).click()

    const recent = page.locator('.recent')
    await expect(recent.locator('.recent-row')).toHaveCount(2, { timeout: 30_000 })
    await page.waitForLoadState('networkidle')

    await expect(recent).toHaveScreenshot(`recent-history-${theme}.png`, {
      animations: 'disabled',
      mask: [recent.locator('.recent-row__name small')],
    })
  })
}

// #62: the preset chips only render with saved presets, so seed two and activate
// one, then snapshot just the chip row in both themes. The active chip uses an
// inverted fill, so its pixels are only exercised here.
const PRESET_SEED = JSON.stringify([
  { id: 'a', name: 'Briefs', pair: 'md-to-pdf', options: { theme: 'academic' }, createdAt: 1 },
  { id: 'b', name: 'Reports', pair: 'md-to-pdf', options: { theme: 'default' }, createdAt: 2 },
])
for (const theme of THEMES) {
  test(`preset chips — ${theme}`, async ({ page }) => {
    await page.emulateMedia({ reducedMotion: 'reduce' })
    await page.addInitScript(
      ([t, seed]) => {
        window.localStorage.setItem('md-bridge:theme', t)
        window.localStorage.setItem('md-bridge:locale', 'en')
        window.localStorage.setItem('md-bridge:presets:md-to-pdf', seed)
      },
      [theme, PRESET_SEED] as const,
    )
    await page.goto('/convert/md-to-pdf')
    await expect(page.locator('html')).toHaveAttribute('data-theme', theme)
    await page.addStyleTag({ content: FREEZE_CSS })
    await page.getByRole('button', { name: /Apply preset Briefs/i }).click()

    const presets = page.locator('.presets')
    await expect(presets.locator('.preset-chip.is-active')).toHaveCount(1)

    await expect(presets).toHaveScreenshot(`preset-chips-${theme}.png`, {
      animations: 'disabled',
    })
  })
}
