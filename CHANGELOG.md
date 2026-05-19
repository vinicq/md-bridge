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

- `docs/screenshots/home-es.png` Spanish home-page screenshot at the
  same 2880x1800 retina resolution as the EN and PT companions.
  README's screenshot section now shows the trilingual UI in a
  3-column table (EN / PT / ES). `docs/screenshots/demo.gif` was
  regenerated with the three locales at the start so the README hero
  shows the trilingual capability before the conversion flow.
- Spanish locale coverage added to the page-level integration tests:
  `About.test.tsx` asserts the ES title, `Home.test.tsx` asserts the
  ES hero headline, and `Navigation.test.tsx` flips the whole UI to
  ES via the language toggle and asserts both the headline and the
  About link translate. The Portuguese tests stay in place.
- **all-contributors** specification adopted. `.all-contributorsrc`
  at the repo root tracks every contributor and their kind of
  contribution (code, doc, translation, design, review, test, infra,
  maintenance). README gains a `## Contributors` section between
  `## License` and `## If md-bridge helped you` that renders the
  current list (Vinicius Queiroz + @zhouzhou626 for the Spanish
  locale). `CONTRIBUTING.md` documents how to be credited: no bot to
  install, no extra PR; the maintainer regenerates the README block
  during release prep.

## [0.2.2] — 2026-05-19

Patch release. Headline change is the trilingual warning fix; the rest is
governance, infrastructure, and documentation polish accumulated since
`v0.2.1`.

### Fixed

- **`/api/pdf-to-md` warnings now follow the active UI locale.** The
  backend used to emit hardcoded English strings ("Very little text was
  extracted…"); PT and ES users saw English while the rest of the UI
  was in their locale. Backend emits stable codes (`needs_ocr`,
  `images_not_persisted`); the frontend dictionary translates per
  locale. The lookup falls back to the raw string for unknown codes so
  future warnings stay forward-compatible. (#40, PR #42)
- `apps/api/app/main.py` Swagger metadata pointed `contact.url` and
  the `API_DESCRIPTION` markdown link at the placeholder
  `https://github.com/your-org/md-bridge`. The Swagger UI at `/docs`
  surfaced both. Replaced with the real repository URL. (PR #46)
- `docker-publish.yml` smoke test for the Web image was running
  `nginx -t` against the bundled config, which contains
  `proxy_pass http://api:8000`. In an isolated container the `api`
  hostname does not resolve, so the parse failed and the workflow
  reported a red CI even though the publish itself succeeded. The
  smoke now asserts that the Vite build stage produced `index.html`
  and copied it to the nginx web root. (PR #20)

### Added

- **Conventional Commits 1.0.0** is now the project's commit and
  PR-title convention. New CI workflow `semantic-pr.yml` rejects PR
  titles that do not match `<type>(<scope>)<!>: <description>`.
  `CONTRIBUTING.md` gains a full reference section with the recognised
  types, bump rules, and worked examples. The `release-drafter.yml`
  config gains an `autolabeler` block. (PR #19)
- `CONTRIBUTING.md` now documents the **issue-claiming process**:
  contributors comment to claim, maintainer assigns via the native
  GitHub `assignee` field, seven-day window before the issue returns
  to the pool. (PR #41)
- Issue templates (`bug_report.md`, `feature_request.md`) now require
  a **test plan with explicit file paths and tiers**. Feature template
  also gains Architect and Design notes sections so the
  tri-disciplinary review pattern shows up before the issue is filed.
  (PR #43)
- `docs/screenshots/warning-i18n.png` visual proof for #40 (deterministic
  Pillow render, no AI image generation). (PR #45)

### Changed

- Pre-commit hooks moved from a separate "Optional" section near
  Tests to **Local setup** in `CONTRIBUTING.md` so new contributors see
  them at the same moment they install Python and Node. The "Strongly
  recommended" framing replaces "Optional". A new paragraph explains
  that the hooks deliberately do not check branch staleness; branch
  protection on `main` ("require branches to be up to date before
  merging") handles that server-side. PR template checklist gains the
  two matching items. (PR #44)
- Project descriptions across `package.json`,
  `apps/api/pyproject.toml`, `README.md`, and `docs/index.md` now state
  the extensibility intent explicitly: md-bridge is a document
  converter that ships PDF ↔ Markdown today and welcomes new format
  pairs as contributions land. The GitHub repo description and topics
  were updated to match. (PR #39)
- About page copy rewritten across `en`, `pt`, and `es` in an
  OSS-professional register. New copy leads with positioning
  ("open source, self-hosted, deterministic, no model inference, no
  telemetry") and names the heuristic stack (PyMuPDF + headless
  Chromium) directly. "Built with" becomes "Open source" with explicit
  MIT-licence and `CONTRIBUTING.md` pointers. (PR #21)
- Theme picker for Markdown → PDF (#14) reorganised as an **umbrella
  issue** with three sister sub-issues: design (#22, CSS templates),
  backend (#23, registry + `/api/themes`), frontend (#24, picker
  dropdown). The pattern is now the project's reference for
  multi-discipline features.

## [0.2.1] — 2026-05-19

### Fixed

- `docker-publish.yml` now builds **multi-platform** images
  (`linux/amd64` + `linux/arm64`). The Oracle Cloud Always Free
  deployment recipe targets ARM Ampere A1 VMs but the previous
  amd64-only publishes failed `docker pull` on ARM hosts with a
  manifest-mismatch error. Apple Silicon developers were affected by
  the same issue. A post-publish smoke job verifies both arches by
  pulling the image and running a minimal probe. (#12)

## [0.2.0] — 2026-05-19

First minor release. Ships the new trilingual UI plus a wider set of
visibility, distribution, and contributor-onboarding work.

### Added

- **Spanish (`es`) locale** in the web UI. The header toggle now lists
  EN / PT / ES. Locale detection and the `<html lang>` attribute were
  generalised so future locales drop in without further code changes.
  Translations are native-quality; tests and the Playwright spec
  exercise all three locales. (#9 by @zhouzhou626 — first external
  contributor.)
- **Oracle Cloud Always Free deployment recipe** under
  `deployment/oracle-cloud/`: step-by-step `README.md`, `bootstrap.sh`
  that installs Docker + Caddy + the stack on a fresh ARM Ampere A1
  VM, and a reference `Caddyfile.example`. Cost: zero. The docs site
  picks up the page under a new "Deploy" nav section.
- **Release-drafter** workflow that keeps a draft GitHub Release in
  sync with merged PRs on `main`. Categories are driven by PR labels
  (`enhancement`, `bug`, `security`, `documentation`, `chore`, ...)
  and the next semver bump is resolved automatically (major / minor /
  patch). Config in `.github/release-drafter.yml`.
- `workflow_dispatch` trigger on `docker-publish.yml` so a manual
  re-publish from the Actions UI is now possible without an unrelated
  commit.
- **Documentation site** at <https://vinicq.github.io/md-bridge/>.
  MkDocs Material build deployed to GitHub Pages on every doc change.
  `mkdocs.yml` plus `docs/index.md` and `docs/getting-started.md`
  provide a curated landing experience separate from the GitHub README.
- **Docker images on GHCR**: a release-triggered workflow publishes
  `ghcr.io/vinicq/md-bridge-api` and `ghcr.io/vinicq/md-bridge-web` so
  users can `docker pull` instead of building locally. Tags follow the
  semver scheme; both images are public.
- **OpenSSF Scorecard** workflow that runs weekly + on push, surfaces
  the result in the Security tab, and exposes a public score at
  scorecard.dev. README gains a Scorecard badge alongside CI and
  CodeQL.
- **Brand assets** under `docs/brand/` (logo, wordmark, social
  preview). Programmatic Pillow geometry, deterministic, no AI
  generation.
- **Demo GIF** at `docs/screenshots/demo.gif`, used as the README
  hero.
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

[Unreleased]: https://github.com/vinicq/md-bridge/compare/v0.2.2...HEAD
[0.2.2]: https://github.com/vinicq/md-bridge/compare/v0.2.1...v0.2.2
[0.2.1]: https://github.com/vinicq/md-bridge/compare/v0.2.0...v0.2.1
[0.2.0]: https://github.com/vinicq/md-bridge/compare/v0.1.1...v0.2.0
[0.1.1]: https://github.com/vinicq/md-bridge/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/vinicq/md-bridge/releases/tag/v0.1.0
