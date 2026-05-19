# Security policy

Thanks for taking the time to report security issues responsibly. This
page tells you how to reach the maintainer privately and what to expect
once you do.

## Which versions get fixes

md-bridge is a small project on its first development cycle. Security
fixes are applied to the latest commit on `main`. There is no separate
long-term support branch yet.

| Version | Supported |
| ------- | --------- |
| `main`  | yes       |
| tagged releases below the latest | no |

When the first `1.x` release line ships, this table will be updated.

## How to report a vulnerability

Please do **not** open a public GitHub issue for security problems.
Public issues are visible to everyone, including people who might abuse
the bug. Use one of the private channels below so the fix can ship
before the bug is publicized.

- **GitHub Security Advisories (preferred):** open a private report at
  <https://github.com/vinicq/md-bridge/security/advisories/new>. This
  keeps the discussion inside the repo and lets the maintainer credit
  you in the eventual release notes if you want.
- **Email:** `vinicq@gmail.com` with the subject prefix
  `[md-bridge security]`.

Include in the report:

- A short description of the issue and the impact you observed or expect.
- Steps to reproduce, ideally with a minimal PDF or markdown payload.
- The commit SHA (the long hash that identifies a commit) or version you
  tested against.
- Whether the issue has already been disclosed elsewhere.

If you are not sure whether something counts as a security issue, send
the report anyway. Better safe than sorry.

## What to expect

- An acknowledgement within five business days.
- A reproduction or follow-up question within ten business days.
- A fix or a clear "won't fix" rationale before any public disclosure.
- Credit in the release notes if you want it. Anonymous reports are also
  fine.

## What the repository already does for you

The following GitHub-native defenses are enabled on this repository and
run continuously. You do not need to opt in to benefit from them:

- **Secret scanning** and **push protection** block accidental commits
  of credentials (API tokens, private keys, cloud secrets) at push time.
  If you try to push a commit that contains a recognized secret, the
  push is rejected with a clear message.
- **CodeQL** runs static security analysis on every push and pull
  request, plus a weekly scheduled scan. Findings appear under the
  Security tab.
- **Dependabot** opens weekly version-bump pull requests for pip, npm,
  GitHub Actions, and Docker base images. Security advisories trigger
  out-of-cycle PRs that jump the queue.
- **Private vulnerability reporting** is enabled (see the reporting
  channel above).

## What is not a security issue

The following are bugs, not vulnerabilities. Please file them as regular
issues:

- Denial of service by uploading PDFs above the documented 500 MB cap.
  The cap is the defense; tune it for your deployment.
- Conversion artifacts (extra whitespace, font fallback, table reflow).
- Dependency issues already tracked by their upstream advisory database
  with no actionable remediation in this repo.
