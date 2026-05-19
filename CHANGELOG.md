# Changelog

All notable changes to md-bridge are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
and this project adheres to [Semantic Versioning](https://semver.org/).
Each version section answers three questions for the reader:

- **Added** — new behaviour or files that did not exist before.
- **Changed** — behaviour or files that already existed and now work
  differently.
- **Removed** — behaviour or files that no longer exist.

If a section is empty in a release, the section is omitted entirely.

## [Unreleased]

### Added

- **Oracle Cloud Always Free deployment recipe** under
  `deployment/oracle-cloud/`: step-by-step `README.md`, `bootstrap.sh`
  that installs Docker + Caddy + the stack on a fresh ARM Ampere A1
  VM, and a reference `Caddyfile.example`. Cost: zero. The docs site
  picks up the page under a new "Deploy" nav section.
- **Release-drafter** workflow that keeps a draft GitHub Release in sync
  with merged PRs on `main`. Categories are driven by PR labels
  (`enhancement`, `bug`, `security`, `documentation`, `chore`, ...) and
  the next semver bump is resolved automatically (major / minor /
  patch). Config in `.github/release-drafter.yml`.
- `workflow_dispatch` trigger on `docker-publish.yml` so a manual
  re-publish from the Actions UI is now possible without an unrelated
  commit.
- **Documentation site** at <https://vinicq.github.io/md-bridge/>. MkDocs
  Material build deployed to GitHub Pages on every doc change. `mkdocs.yml`
  plus `docs/index.md` and `docs/getting-started.md` provide a curated
  landing experience separate from the GitHub README.
- **Docker images on GHCR**: a release-triggered workflow publishes
  `ghcr.io/vinicq/md-bridge-api` and `ghcr.io/vinicq/md-bridge-web` so
  users can `docker pull` instead of building locally. Tags follow the
  semver scheme.
- **OpenSSF Scorecard** workflow that runs weekly + on push, surfaces the
  result in the Security tab, and exposes a public score at
  scorecard.dev. README gains a Scorecard badge alongside CI and CodeQL.
- **Brand assets** under `docs/brand/` (logo, wordmark, social preview).
  Programmatic Pillow geometry, deterministic, no AI generation.
- **Demo GIF** at `docs/screenshots/demo.gif`, used as the README hero.
- **Star history chart** and a "If md-bridge helped you" CTA at the
  bottom of the README.

## [0.1.1] — 2026-05-19

Maintenance and governance release. No behaviour changes in the
converter; only infrastructure, security posture, and contributor
ergonomics.

### Added

- Optional `pre-commit` configuration that runs `ruff` and basic
  hygiene hooks (trailing whitespace, EOF newline, YAML/TOML syntax,
  merge conflict markers, large files) before every commit. Documented
  in `CONTRIBUTING.md`.
- `.github/workflows/dependabot-auto-merge.yml` enables `gh pr merge
  --auto` for Dependabot PRs that are patch bumps (`X.Y.Z → X.Y.Z+1`)
  or transitive (indirect) dependency updates. Branch protection still
  gates the actual merge on every required status check; minor and
  major bumps stay in the manual review queue.
- Branch protection on `main` documented in `CONTRIBUTING.md`:
  required status checks for Backend, Web, End-to-end, and the two
  CodeQL jobs; force-push and deletion blocked; linear history
  required.
- `SECURITY.md` now lists the GitHub-native defenses that are active
  on the repository so contributors know what they get for free
  (secret scanning, push protection, CodeQL, Dependabot, private
  vulnerability reporting).

### Changed

- GitHub Actions bumped to current majors: `actions/checkout` v4 → v6,
  `actions/setup-python` v5 → v6, `github/codeql-action` v3 → v4,
  `actions/setup-node` v4 → v6, `actions/upload-artifact` v4 → v7.
  Clears the Node.js 20 deprecation warnings on the runner.
- Docker base images bumped: web `node:22-alpine` → `node:26-alpine`,
  web runtime `nginx:1.27-alpine` → `nginx:1.31-alpine`.
- npm devDependencies bumped: `typescript-eslint` 8.59.3 → 8.59.4
  (patch), `@types/node` 24.12.4 → 25.9.0.

### Security

- Enabled GitHub-native repo features via API: secret scanning, push
  protection, private vulnerability reporting, vulnerability alerts,
  Dependabot security updates.
- Branch protection on `main` requires every CI and CodeQL status
  check to pass before a merge can land.

## [0.1.0] — 2026-05-19

First tagged release. md-bridge is a self-hosted PDF and Markdown
converter with a FastAPI backend and a React frontend.

### Added

- **PDF to Markdown** conversion with heading detection, list recovery,
  table extraction, and YAML front matter.
- **Markdown to PDF** rendering through headless Chromium with a bundled
  A4 stylesheet.
- **Batch mode** in the UI: drop one file or a whole folder; each file
  is converted sequentially and can be downloaded as it lands.
- **`/api/inspect-pdf`** endpoint returns diagnostics (fonts, sizes,
  tagged-PDF flag, OCR hint) so the UI can warn before conversion.
- **Bilingual UI** in English (default) and Portuguese, with the choice
  persisted to `localStorage`.
- **Interactive API docs** at `/docs` (Swagger UI) and `/redoc`, plus a
  walkthrough in [`docs/API.md`](docs/API.md).
- **Docker Compose stack** for one-command boot of API + Web with
  healthchecks.
- **Test pyramid** with 124 tests (92 unit, 26 integration, 6 end-to-end),
  every one of which runs on CI against the committed ISTQB CTAL-TA
  syllabus fixture. No silent CI skips.
- **CI workflow** for backend pytest, web build + lint + vitest, and
  Playwright end-to-end.
- **CodeQL** static security analysis on every push and pull request,
  with a weekly scheduled scan, covering both Python and TypeScript.
- **Backend linting** via `ruff` with the `E F W I UP B` rule set,
  enforced in CI.
- **Frontend linting** via ESLint, enforced in CI.
- **Open source governance** files: `LICENSE` (MIT), `CONTRIBUTING.md`,
  `CODE_OF_CONDUCT.md`, `SECURITY.md`, `.github/dependabot.yml`,
  issue and PR templates, `.editorconfig`.

[Unreleased]: https://github.com/vinicq/md-bridge/compare/v0.1.1...HEAD
[0.1.1]: https://github.com/vinicq/md-bridge/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/vinicq/md-bridge/releases/tag/v0.1.0
