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

## How to revisit this list

The exceptions above are not permanent. Re-check on every milestone close
or when the Scorecard score changes by more than a point. If the reason
for an exception stops holding (co-maintainer joins, a fuzzing-class bug
lands), drop the entry and act on the check.
