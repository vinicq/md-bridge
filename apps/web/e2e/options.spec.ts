import { expect, test } from '@playwright/test'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const here = path.dirname(fileURLToPath(import.meta.url))
const ISTQB = path.resolve(here, '..', '..', 'api', 'tests', 'fixtures', 'istqb-ctal-ta-syllabus-en.pdf')

test.beforeEach(async ({ context }) => {
  await context.addInitScript(() => {
    window.localStorage.setItem('md-bridge:locale', 'en')
  })
})

async function downloadHead(page: import('@playwright/test').Page): Promise<string> {
  const downloadPromise = page.waitForEvent('download')
  await page.getByRole('button', { name: /download \.md/i }).click()
  const download = await downloadPromise
  const stream = await download.createReadStream()
  const chunks: Buffer[] = []
  await new Promise<void>((resolve, reject) => {
    stream!.on('data', (c) => chunks.push(Buffer.from(c)))
    stream!.on('end', () => resolve())
    stream!.on('error', reject)
  })
  return Buffer.concat(chunks).toString('utf-8').slice(0, 200)
}

test('options panel forwards a real flag to the converter', async ({ page }) => {
  await page.goto('/convert/pdf-to-md')
  await page.locator('input[type="file"]').setInputFiles(ISTQB)
  await expect(page.getByText('Pages')).toBeVisible({ timeout: 60_000 })

  // Default front matter is on: the produced Markdown carries a YAML header
  // (also covered by istqb.spec). Turn it OFF before converting: the option
  // must reach the API and the output must NOT carry the front-matter block.
  await page.getByRole('checkbox', { name: /add front matter/i }).uncheck()
  await page.getByRole('button', { name: /convert all/i }).click()
  await expect(page.locator('.md-preview h1, .md-preview h2').first()).toBeVisible({ timeout: 60_000 })

  const head = await downloadHead(page)
  expect(head.startsWith('---\ntitle:')).toBeFalsy()
  // The heading still converts; only the front-matter block is gone.
  expect(head).toMatch(/#/)
})
