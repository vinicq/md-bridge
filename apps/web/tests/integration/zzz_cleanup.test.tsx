import { afterAll, describe, expect, it } from 'vitest'
import { rmSync, existsSync } from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const here = path.dirname(fileURLToPath(import.meta.url))
const webRoot = path.resolve(here, '..', '..')

const TARGETS = [
  path.join(webRoot, 'test-results'),
  path.join(webRoot, 'playwright-report'),
  path.join(webRoot, 'coverage'),
]

afterAll(() => {
  for (const t of TARGETS) {
    if (existsSync(t)) {
      rmSync(t, { recursive: true, force: true })
    }
  }
})

describe('zzz cleanup', () => {
  it('removes test-time artifacts from the web workspace', () => {
    for (const t of TARGETS) {
      if (existsSync(t)) {
        rmSync(t, { recursive: true, force: true })
      }
    }
    for (const t of TARGETS) {
      expect(existsSync(t)).toBe(false)
    }
  })
})
