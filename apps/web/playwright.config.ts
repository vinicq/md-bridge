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
  use: {
    baseURL: 'http://127.0.0.1:5173',
    trace: 'retain-on-failure',
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
    { name: 'firefox', use: { ...devices['Desktop Firefox'] } },
    { name: 'webkit', use: { ...devices['Desktop Safari'] } },
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
