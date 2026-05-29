import { test, expect } from '@playwright/test'
import AxeBuilder from '@axe-core/playwright'
import fs from 'fs'
import path from 'path'
import { fileURLToPath } from 'node:url'

const here = path.dirname(fileURLToPath(import.meta.url))
const ISTQB = path.resolve(
  here,
  '..',
  '..',
  'api',
  'tests',
  'fixtures',
  'istqb-ctal-ta-syllabus-en.pdf',
)

const ROUTES = [
  { path: '/', name: 'Home' },
  { path: '/convert/pdf-to-md', name: 'PdfToMd' },
  { path: '/convert/md-to-pdf', name: 'MdToPdf' },
  { path: '/about', name: 'About' },
]

test.describe('WCAG 2.1 AA Accessibility Audit', () => {
  for (const route of ROUTES) {
    test(`audit ${route.name} (${route.path})`, async ({ page }, testInfo) => {
      await page.goto(route.path, { waitUntil: 'networkidle' })

      const results = await new AxeBuilder({ page })
        .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
        .analyze()

      const data = {
        route: route.path,
        name: route.name,
        violations: results.violations.map(v => ({
          id: v.id,
          impact: v.impact,
          description: v.description,
          help: v.help,
          helpUrl: v.helpUrl,
          wcagTags: v.tags.filter(t => t.startsWith('wcag')),
          nodes: v.nodes.map(n => ({
            html: n.html.slice(0, 300),
            target: n.target,
            failureSummary: n.failureSummary?.slice(0, 400),
          })),
        })),
        summary: {
          total: results.violations.length,
          critical: results.violations.filter(v => v.impact === 'critical').length,
          serious: results.violations.filter(v => v.impact === 'serious').length,
          moderate: results.violations.filter(v => v.impact === 'moderate').length,
          minor: results.violations.filter(v => v.impact === 'minor').length,
          passes: results.passes.length,
          incomplete: results.incomplete.length,
        }
      }

      // Write results to Playwright's output directory (no untracked files)
      const outputFile = testInfo.outputPath(
        `axe-${route.path.replace(/\//g, '_') || 'home'}.json`,
      )
      fs.mkdirSync(path.dirname(outputFile), { recursive: true })
      fs.writeFileSync(outputFile, JSON.stringify(data, null, 2))

      console.log(`\n=== ${route.name} (${route.path}) ===`)
      console.log(`  Critical: ${data.summary.critical}`)
      console.log(`  Serious: ${data.summary.serious}`)
      console.log(`  Moderate: ${data.summary.moderate}`)
      console.log(`  Minor: ${data.summary.minor}`)
      console.log(`  Passes: ${data.summary.passes}`)

      for (const v of data.violations) {
        console.log(`\n  [${v.impact.toUpperCase()}] ${v.id}: ${v.help}`)
        console.log(`    WCAG: ${v.wcagTags.join(', ')}`)
        for (const n of v.nodes.slice(0, 3)) {
          console.log(`    Element: ${n.html.slice(0, 100)}`)
        }
      }

      // CRITICAL ASSERTION: No critical or serious violations
      const criticalSerious = results.violations.filter(
        v => v.impact === 'critical' || v.impact === 'serious',
      )
      expect(
        criticalSerious,
        `Found ${criticalSerious.length} critical/serious violations on ${route.path}: ${criticalSerious.map(v => v.id).join(', ')}`,
      ).toHaveLength(0)
    })
  }
})

type Locale = 'en' | 'pt' | 'es'
type Theme = 'light' | 'dark'

interface ContrastScenario {
  route: string
  name: string
  locale: Locale
  theme: Theme
}

// Matrix is intentionally reduced (10 instead of 24): routes do not change
// color tokens and locales only swap text, so `{light,dark} x 4 routes` in EN
// is the meaningful surface, plus a smoke run per non-EN locale on home.
const CONTRAST_SCENARIOS: ContrastScenario[] = [
  ...ROUTES.flatMap((r): ContrastScenario[] => [
    { route: r.path, name: r.name, locale: 'en', theme: 'light' },
    { route: r.path, name: r.name, locale: 'en', theme: 'dark' },
  ]),
  { route: '/', name: 'Home', locale: 'pt', theme: 'light' },
  { route: '/', name: 'Home', locale: 'es', theme: 'light' },
]

test.describe('color-contrast sweep (WCAG 1.4.3)', () => {
  for (const sc of CONTRAST_SCENARIOS) {
    const label = `${sc.name} ${sc.route} [${sc.locale}/${sc.theme}]`
    test(`no color-contrast violations on ${label}`, async ({ page }) => {
      // Seed locale + theme via localStorage on the origin BEFORE the SPA boots
      // so the providers pick up the desired state on first render. Using the
      // visible controls would still work, but a few routes (e.g. /about) hide
      // the language switcher, and toggling after hydration adds flake. The
      // storage keys mirror what the live providers write.
      await page.goto('/', { waitUntil: 'domcontentloaded' })
      await page.evaluate(
        ({ locale, theme }) => {
          window.localStorage.setItem('md-bridge:locale', locale)
          window.localStorage.setItem('md-bridge:theme', theme)
        },
        { locale: sc.locale, theme: sc.theme },
      )

      await page.goto(sc.route, { waitUntil: 'networkidle' })

      // Sanity check that the theme attribute landed on <html>.
      const appliedTheme = await page.evaluate(() =>
        document.documentElement.getAttribute('data-theme'),
      )
      expect(appliedTheme, `expected data-theme=${sc.theme} on ${label}`).toBe(sc.theme)

      const results = await new AxeBuilder({ page })
        .withRules(['color-contrast'])
        .analyze()

      if (results.violations.length > 0) {
        // Surface the full violation payload to make CI failures actionable.
        console.log(
          `\ncolor-contrast violations on ${label}:\n` +
            JSON.stringify(results.violations, null, 2),
        )
      }

      expect(
        results.violations,
        `color-contrast violations on ${label}: ${results.violations
          .map((v) => v.id)
          .join(', ')}`,
      ).toHaveLength(0)
    })
  }
})

test.describe('batch Skip button a11y', () => {
  // The Skip button only renders while an item is `converting` (issue #138),
  // so the static route audit above never sees it. Hold one conversion in
  // flight and run axe with the button on screen.
  test('Skip button has no critical/serious axe violations while converting', async ({
    page,
  }) => {
    await page.addInitScript(() => {
      window.localStorage.setItem('md-bridge:locale', 'en')
    })
    // Never settle the conversion request: the item stays in `converting`.
    await page.route('**/api/pdf-to-md', () => {})

    await page.goto('/convert/pdf-to-md')
    await page.locator('input[type="file"]').setInputFiles(ISTQB)
    await page.getByRole('button', { name: /convert all/i }).click()

    const skip = page.getByRole('button', { name: /skip/i })
    await expect(skip).toBeVisible({ timeout: 30_000 })

    // The `Converting` status label has a pre-existing color-contrast miss
    // (accent text on the accent-soft row tint) that this PR did not introduce
    // and that the static route audit never exercised. It is tracked in #178
    // and fixed separately under the design-token lens; excluding the node here
    // keeps this test focused on the Skip control #138 adds.
    const results = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
      .exclude('.batch__status--converting')
      .analyze()

    const criticalSerious = results.violations.filter(
      (v) => v.impact === 'critical' || v.impact === 'serious',
    )
    expect(
      criticalSerious,
      `Found ${criticalSerious.length} critical/serious violations with Skip visible: ${criticalSerious
        .map((v) => v.id)
        .join(', ')}`,
    ).toHaveLength(0)
  })
})

test.describe('needs_ocr alerts a11y (#139)', () => {
  test('Path B: needs_ocr warning renders a clean role=alert region', async ({ page }) => {
    await page.addInitScript(() => window.localStorage.setItem('md-bridge:locale', 'en'))
    await page.route('**/api/pdf-to-md', (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          md: '# almost empty',
          front_matter: {},
          warnings: ['needs_ocr'],
          stats: { headings: 0, tables: 0, bullets: 0 },
        }),
      }),
    )
    await page.goto('/convert/pdf-to-md')
    await page.locator('input[type="file"]').setInputFiles(ISTQB)
    await page.getByRole('button', { name: /convert all/i }).click()

    await expect(page.getByRole('alert')).toBeVisible({ timeout: 30_000 })
    const results = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
      .analyze()
    const criticalSerious = results.violations.filter(
      (v) => v.impact === 'critical' || v.impact === 'serious',
    )
    expect(
      criticalSerious,
      `critical/serious with needs_ocr alert: ${criticalSerious.map((v) => v.id).join(', ')}`,
    ).toHaveLength(0)
  })

  test('Path A: 422 ocr_required renders a focusable error with a reachable CTA', async ({
    page,
  }) => {
    await page.addInitScript(() => window.localStorage.setItem('md-bridge:locale', 'en'))
    await page.route('**/api/pdf-to-md', (route) =>
      route.fulfill({
        status: 422,
        contentType: 'application/json',
        body: JSON.stringify({
          error: {
            code: 'ocr_required',
            message: 'This PDF has no extractable text layer.',
            detail: { docs: 'https://vinicq.github.io/md-bridge/getting-started/' },
          },
        }),
      }),
    )
    await page.goto('/convert/pdf-to-md')
    await page.locator('input[type="file"]').setInputFiles(ISTQB)
    await page.getByRole('button', { name: /convert all/i }).click()

    const heading = page.getByRole('heading', { name: /OCR required/i })
    await expect(heading).toBeVisible({ timeout: 30_000 })
    // Focus moves to the error heading so a keyboard user is not stranded.
    await expect(heading).toBeFocused()
    const cta = page.getByRole('link', { name: /How to enable OCR/i })
    await expect(cta).toHaveAttribute('href', /getting-started/)

    const results = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
      .analyze()
    const criticalSerious = results.violations.filter(
      (v) => v.impact === 'critical' || v.impact === 'serious',
    )
    expect(
      criticalSerious,
      `critical/serious with ocr_required banner: ${criticalSerious.map((v) => v.id).join(', ')}`,
    ).toHaveLength(0)
  })
})

test.describe('focus-visible coverage', () => {
  for (const route of ROUTES) {
    test(`every keyboard-reachable element on ${route.name} shows a focus ring`, async ({ page }) => {
      await page.goto(route.path, { waitUntil: 'networkidle' })

      // Start focus from the document body so the first Tab lands on the first
      // tabbable element (skip link, header brand, etc).
      await page.evaluate(() => {
        if (document.activeElement instanceof HTMLElement) {
          document.activeElement.blur()
        }
      })

      const MAX_TABS = 12
      const seenSelectors = new Set<string>()

      for (let i = 0; i < MAX_TABS; i++) {
        await page.keyboard.press('Tab')

        const focused = await page.evaluate(() => {
          const el = document.activeElement as HTMLElement | null
          if (!el || el === document.body) return null
          const styles = getComputedStyle(el)
          return {
            tag: el.tagName.toLowerCase(),
            id: el.id || null,
            classes: el.className && typeof el.className === 'string' ? el.className : null,
            text: (el.textContent || '').trim().slice(0, 60),
            outlineWidth: styles.outlineWidth,
            outlineStyle: styles.outlineStyle,
            boxShadow: styles.boxShadow,
          }
        })

        if (!focused) {
          // Focus left the document (or wrapped past the last tabbable). Stop.
          break
        }

        const signature = `${focused.tag}#${focused.id ?? ''}.${focused.classes ?? ''}|${focused.text}`
        if (seenSelectors.has(signature)) {
          // Tab cycled back to a previously-seen element. Stop.
          break
        }
        seenSelectors.add(signature)

        const hasOutline =
          focused.outlineStyle !== 'none' && focused.outlineWidth !== '0px'
        const hasBoxShadow = focused.boxShadow !== 'none'

        expect(
          hasOutline || hasBoxShadow,
          `Focused element on ${route.path} has no visible focus indicator: ${signature} (outline=${focused.outlineWidth} ${focused.outlineStyle}, box-shadow=${focused.boxShadow})`,
        ).toBe(true)
      }

      // Sanity check: at least one element must have been tabbed to per route.
      expect(seenSelectors.size, `No tabbable elements found on ${route.path}`).toBeGreaterThan(0)
    })
  }
})
