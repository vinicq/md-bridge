import { defineConfig, devices } from '@playwright/test'
import { existsSync } from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const here = path.dirname(fileURLToPath(import.meta.url))
const repoRoot = path.resolve(here, '..', '..')

/**
 * Resolve the Python binary used to boot the API for E2E.
 *
 * - On a Windows dev machine we expect `apps/api/.venv/Scripts/python.exe`.
 * - On Linux / macOS dev machines we expect `apps/api/.venv/bin/python`.
 * - On CI (GitHub Actions) we install the package globally with `pip install -e`,
 *   so we fall back to the `python` binary on PATH.
 */
function resolvePython(): string {
  const winVenv = path.join(repoRoot, 'apps', 'api', '.venv', 'Scripts', 'python.exe')
  const nixVenv = path.join(repoRoot, 'apps', 'api', '.venv', 'bin', 'python')
  if (existsSync(winVenv)) return winVenv
  if (existsSync(nixVenv)) return nixVenv
  return 'python'
}

const apiPython = resolvePython()

export default defineConfig({
  testDir: './e2e',
  fullyParallel: false,
  workers: 1,
  retries: 0,
  reporter: [['list']],
  // Visual baselines live beside the spec under e2e/__screenshots__/ with the
  // project + platform suffix Playwright appends, so a Linux baseline never
  // collides with a local dev one.
  snapshotPathTemplate: '{testDir}/__screenshots__/{testFileName}/{arg}-{projectName}-{platform}{ext}',
  expect: {
    // 0.5%: strict enough to catch a real layout/colour regression, loose
    // enough to forgive sub-pixel font-rendering noise between CI runs (#16).
    toHaveScreenshot: { maxDiffPixelRatio: 0.005 },
  },
  use: {
    baseURL: 'http://127.0.0.1:5173',
    trace: 'retain-on-failure',
  },
  projects: [
    // The functional suite runs on all three browsers but never on the visual
    // spec; the visual baselines are Chromium-only and run in their own project.
    { name: 'chromium', use: { ...devices['Desktop Chrome'] }, testIgnore: '**/visual.spec.ts' },
    { name: 'firefox', use: { ...devices['Desktop Firefox'] }, testIgnore: '**/visual.spec.ts' },
    { name: 'webkit', use: { ...devices['Desktop Safari'] }, testIgnore: '**/visual.spec.ts' },
    { name: 'visual', use: { ...devices['Desktop Chrome'] }, testMatch: '**/visual.spec.ts' },
  ],
  webServer: [
    {
      command: `"${apiPython}" -m uvicorn app.main:app --host 127.0.0.1 --port 8000`,
      cwd: path.join(repoRoot, 'apps', 'api'),
      port: 8000,
      reuseExistingServer: !process.env.CI,
      timeout: 60_000,
    },
    {
      command: 'npm run dev -- --host 127.0.0.1 --port 5173 --strictPort',
      cwd: here,
      port: 5173,
      reuseExistingServer: !process.env.CI,
      timeout: 60_000,
    },
  ],
})
