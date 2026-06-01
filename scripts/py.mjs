#!/usr/bin/env node
// Resolve the project's Python interpreter across OSes, then exec it with the
// forwarded args. Mirrors the probe order in apps/web/playwright.config.ts:
// Windows venv -> POSIX venv -> `python` on PATH (CI installs the package
// globally, so the bare binary is the correct fallback there).
import { spawnSync } from 'node:child_process'
import { existsSync } from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const here = path.dirname(fileURLToPath(import.meta.url))
const repoRoot = path.resolve(here, '..')
const venv = path.join(repoRoot, 'apps', 'api', '.venv')

const winPy = path.join(venv, 'Scripts', 'python.exe')
const nixPy = path.join(venv, 'bin', 'python')
const python = existsSync(winPy) ? winPy : existsSync(nixPy) ? nixPy : 'python'

const result = spawnSync(python, process.argv.slice(2), { stdio: 'inherit' })
if (result.error) {
  console.error(`md-bridge: could not run "${python}". Is your venv created? See the Quickstart.`)
  console.error(result.error.message)
  process.exit(1)
}
process.exit(result.status ?? 1)
