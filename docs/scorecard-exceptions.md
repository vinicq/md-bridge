# OpenSSF Scorecard exceptions

This document records Scorecard checks where md-bridge accepts a low score
intentionally. Each entry names the check, the current score, why we accept
it, and what would change that.

The score and breakdown are visible at
<https://scorecard.dev/viewer/?uri=github.com/vinicq/md-bridge>.

## Code-Review

**Current state:** Low score.
**Reason:** md-bridge is a single-maintainer project. The maintainer
self-merges their own PRs after CI passes. Branch protection on `main`
requires every PR to be merged via the PR UI (no direct push), and every
required check has to be green, but no second reviewer is required because
there is no second reviewer to require.

**What would change this:** A regular co-maintainer joining the project and
becoming the required second approver on PRs that touch security-sensitive
code (auth surface, CSP, container build). At that point the requirement
goes into branch protection and the score climbs.

## Fuzzing

**Current state:** No fuzzing harness.
**Reason:** The PDF↔Markdown conversion surface is deterministic and the
existing test pyramid (unit + integration + E2E + Playwright with axe-core)
covers the failure modes a contributor sees in practice. A fuzzer would
generate exotic inputs, but the converter already rejects malformed PDFs
with a structured error response rather than crashing, and there is no
parser the project owns end-to-end (pdfium and weasyprint are pinned and
audited upstream).

**What would change this:** A reproducible crash from a real-world PDF
encountered in the wild. The first such report opens an issue, gets a
regression test in `apps/api/tests/`, and the conversation about adopting
a fuzzer reopens with evidence.

## Pinned-Dependencies (pip and npm install commands)

**Current state:** 10 alerts across `.github/workflows/ci.yml`,
`.github/workflows/pages.yml`, `.github/workflows/credit-contributor.yml`,
`apps/api/Dockerfile` (including the opt-in `runtime-ocr` stage at line 49 and
the `test` stage at line 60), and `apps/web/Dockerfile` flagging `pip install`
and `npm install` / `npm ci` lines as "not pinned by hash".

**Reason:** The dependency surface is already pinned by other means:

- `pip install -e ".[dev]"` and `pip install -r requirements.txt` resolve
  against version constraints in `pyproject.toml` and `requirements.txt`.
  Every package carries a minimum version chosen to clear known CVEs
  (`pypdf>=6.10.2`, `markdown>=3.8.1`, `python-multipart>=0.0.27`).
  Dependabot opens version-bump PRs as new patches drop.
- `npm ci` consults `apps/web/package-lock.json` for exact hashes of every
  transitive package. The lockfile is committed and is the source of truth.
- `mkdocs-material` in `pages.yml` is a leaf install with no runtime input;
  the cost of hash-pinning that one line is high relative to its blast radius
  (build-time only, no app code reads it).

Per-command hash pinning (`pip install --require-hashes` plus a generated
`requirements.lock`, or `npm install --integrity` workflows) is on the
roadmap once the project gains a regular co-maintainer who can carry the
churn of refreshing those lockfiles on every Dependabot bump. Until then,
the constraint-plus-lockfile model is the chosen trade-off.

**What would change this:** A pip- or npm-level supply chain attack that
the constraint resolver could not have caught (a malicious patch release
inside a satisfied range). At that point the constraint-only model breaks
and per-command hash pinning becomes worth the maintenance cost.

## Maintained

**Current state:** Low score. The repository was created less than 90 days ago,
so Scorecard cannot yet assess maintenance cadence.

**Reason:** This is a time-based check. Scorecard awards full credit when the
project has at least one commit per week over the previous 90 days, but it
needs the project to be older than 90 days to evaluate at all. md-bridge is
a new repository; the score is structural, not behavioural.

The commit cadence on `main` is comfortably above one commit per week, so the
score will rise on its own once the repository crosses the 90-day mark.

**What would change this:** Time. The check auto-resolves when the repo ages
past the 90-day floor, assuming the current commit cadence holds.

## CIIBestPractices

**Current state:** No OpenSSF Best Practices badge applied for.

**Reason:** The badge is optional and self-attested. Applying for it does
not improve the codebase by itself; it puts a maintainer's time into the
application form and the ongoing attestation refresh.

**What would change this:** A downstream user or sponsor citing the badge
as a requirement for adopting md-bridge. At that point the application
becomes worth it.

## How to revisit this list

The exceptions above are not permanent. Re-check on every milestone close
or when the Scorecard score changes by more than a point. If the reason
for an exception stops holding (co-maintainer joins, a fuzzing-class bug
lands), drop the entry and act on the check.
