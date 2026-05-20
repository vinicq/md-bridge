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
