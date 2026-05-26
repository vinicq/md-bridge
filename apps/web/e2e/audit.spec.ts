import { test, expect } from '@playwright/test'
import AxeBuilder from '@axe-core/playwright'
import fs from 'fs'
import path from 'path'

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
