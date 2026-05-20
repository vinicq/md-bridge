/**
 * Accessibility audit — uses Playwright test framework directly.
 * Run: cd apps/web && npx playwright test tests/a11y/audit.spec.ts --reporter=list --workers=1 --config=tests/a11y/playwright.config.ts
 * 
 * But since we have no config file for a11y, let's use a standalone script approach.
 */
import { test, expect } from '@playwright/test'
import AxeBuilder from '@axe-core/playwright'
import fs from 'fs'
import path from 'path'

const BASE_URL = 'http://127.0.0.1:5173'

const ROUTES = [
  { path: '/', name: 'Home' },
  { path: '/convert/pdf-to-md', name: 'PdfToMd' },
  { path: '/convert/md-to-pdf', name: 'MdToPdf' },
  { path: '/about', name: 'About' },
]

test.describe('WCAG 2.1 AA Accessibility Audit', () => {
  for (const route of ROUTES) {
    test(`audit ${route.name} (${route.path})`, async ({ page }) => {
      await page.goto(`${BASE_URL}${route.path}`, { waitUntil: 'networkidle' })
      
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
      
      const outDir = path.resolve('audit-results')
      fs.mkdirSync(outDir, { recursive: true })
      const outFile = path.join(outDir, (route.path.replace(/\//g, '_') || 'home') + '.json')
      fs.writeFileSync(outFile, JSON.stringify(data, null, 2))
      
      console.log(`\n=== ${route.name} (${route.path}) ===`)
      console.log(`  Critical: ${data.summary.critical}`)
      console.log(`  Serious: ${data.summary.serious}`)  
      console.log(`  Moderate: ${data.summary.moderate}`)
      console.log(`  Minor: ${data.summary.minor}`)
      console.log(`  Passes: ${data.summary.passes}`)
      
      for (const v of data.violations) {
        console.log(`\n  [${v.impact.toUpperCase()}] ${v.id}: ${v.help}`)
        console.log(`    WCAG: ${v.wcagTags.join(', ')}`)
        console.log(`    ${v.description}`)
        for (const n of v.nodes.slice(0, 3)) {
          console.log(`    Element: ${n.html.slice(0, 100)}`)
          console.log(`    Fix: ${n.failureSummary}`)
        }
      }
    })
  }
})
