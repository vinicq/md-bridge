/**
 * Standalone axe-core audit using @axe-core/playwright directly.
 * Usage: node audit.mjs
 */
import { chromium } from 'playwright'
import AxeBuilder from '@axe-core/playwright'
import fs from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))

const BASE_URL = 'http://127.0.0.1:5173'
const ROUTES = [
  { path: '/', name: 'Home' },
  { path: '/convert/pdf-to-md', name: 'PdfToMd' },
  { path: '/convert/md-to-pdf', name: 'MdToPdf' },
  { path: '/about', name: 'About' },
]

const resultsDir = path.resolve(__dirname, '../../docs/audit-results')
fs.mkdirSync(resultsDir, { recursive: true })

const browser = await chromium.launch({ 
  headless: true,
  args: ['--no-sandbox']
})

const allViolations = []

try {
  for (const route of ROUTES) {
    const context = await browser.newContext({ viewport: { width: 1280, height: 800 } })
    const page = await context.newPage()
    
    console.log(`\n=== Auditing ${route.name} (${route.path}) ===`)
    await page.goto(`${BASE_URL}${route.path}`, { waitUntil: 'networkidle', timeout: 15000 })
    
    const builder = new AxeBuilder(page)
    const results = await builder
      .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
      .analyze()
    
    const violations = results.violations.map(v => ({
      id: v.id,
      impact: v.impact,
      description: v.description,
      help: v.help,
      helpUrl: v.helpUrl,
      wcagCriteria: v.tags.filter(t => t.startsWith('wcag')),
      nodes: v.nodes.map(n => ({
        html: n.html.slice(0, 300),
        target: n.target,
        failureSummary: n.failureSummary?.slice(0, 400),
      })),
    }))
    
    const summary = {
      total: results.violations.length,
      critical: results.violations.filter(v => v.impact === 'critical').length,
      serious: results.violations.filter(v => v.impact === 'serious').length,
      moderate: results.violations.filter(v => v.impact === 'moderate').length,
      minor: results.violations.filter(v => v.impact === 'minor').length,
      passes: results.passes.length,
      incomplete: results.incomplete.length,
    }
    
    allViolations.push({ route: route.path, name: route.name, violations, summary })
    
    // Print summary
    console.log(`  Violations: ${summary.total} (critical: ${summary.critical}, serious: ${summary.serious}, moderate: ${summary.moderate}, minor: ${summary.minor})`)
    console.log(`  Passes: ${summary.passes}, Incomplete: ${summary.incomplete}`)
    
    for (const v of violations) {
      console.log(`  [${v.impact.toUpperCase()}] ${v.id}`)
      console.log(`    ${v.help} (${v.nodes.length} elements)`)
      console.log(`    ${v.wcagCriteria.slice(0, 3).join(', ')}`)
      for (const n of v.nodes.slice(0, 2)) {
        console.log(`    HTML: ${n.html.slice(0, 120)}`)
      }
    }
    
    // Write per-route JSON
    const fileName = route.path.replace(/\//g, '_') || 'home'
    fs.writeFileSync(
      path.join(resultsDir, `${fileName}.json`),
      JSON.stringify(allViolations[allViolations.length - 1], null, 2)
    )
    
    await context.close()
  }
  
  // Write combined results
  fs.writeFileSync(
    path.join(resultsDir, 'combined.json'),
    JSON.stringify(allViolations, null, 2)
  )
  
  console.log(`\n=== COMBINED SUMMARY ===`)
  let totalCritical = 0, totalSerious = 0, totalModerate = 0, totalMinor = 0
  for (const r of allViolations) {
    totalCritical += r.summary.critical
    totalSerious += r.summary.serious
    totalModerate += r.summary.moderate
    totalMinor += r.summary.minor
  }
  console.log(`  Critical: ${totalCritical}`)
  console.log(`  Serious: ${totalSerious}`)
  console.log(`  Moderate: ${totalModerate}`)
  console.log(`  Minor: ${totalMinor}`)
  
  if (totalCritical + totalSerious > 0) {
    console.log(`\n⚠️  ${totalCritical + totalSerious} critical/serious violations need remediation.`)
  } else {
    console.log(`\n✅ No critical or serious violations found — only moderate/minor issues.`)
  }
  
  // Write unified audit findings
  console.log(`\nRaw data written to ${resultsDir}/`)
  
} finally {
  await browser.close()
}
