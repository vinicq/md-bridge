# AGENTS.md - md-bridge

Guidance for automated agents and code-review bots (Codex and others) working in this repository. Human contributors should read `CONTRIBUTING.md`; this file sets the house style for machine-generated review comments and changes.

## Project identity

md-bridge is a self-hosted, deterministic, offline-capable PDF <-> Markdown converter. The contract:

- Self-hosted, deterministic, no external API calls at runtime
- Heuristic, hand-written conversion (no ML in the default install; OCR is opt-in)
- Lean default install; expensive features sit behind optional extras
- Format-pair architecture (DOCX, EPUB, RTF are welcome on the roadmap)
- OSS multi-locale (en, pt, es from day one)
- Free and open formats only; no telemetry, no proprietary lock-in
- Small, opinionated surface

A change that contradicts this contract should be flagged, not waved through.

## Language

This is an open-source project. Every public artifact is written in English: PR review comments, review summaries, commit messages, issue comments, and docs. Internal reasoning can happen in any language, but anything posted to GitHub is English.

## Writing style (applies to all review comments and summaries)

- No emojis. Not in summaries, not in inline comments, not in headings, not as status markers. Use plain words ("blocker", "nit", "approved").
- No em-dash (`-` em-dash). Use a hyphen, comma, or colon.
- Prefer "but" over "however".
- No inflated language: drop "essential", "fundamental", "robust", "powerful", "elegant", "seamless" as filler praise.
- No superficial "-ing" openers ("Ensuring X, the code...""). Rewrite in active voice.
- No vague attribution ("it is widely known", "many would agree").
- No forced rule-of-three lists.
- Vary sentence length. Mix short and long.
- Be direct and specific. Cite `file:line`. Quote the code you mean.

## No AI attribution

Never add AI attribution anywhere that lands in the public record: no `Co-Authored-By: <AI>` trailers in commits, no "Generated with ..." footers in PR bodies or review comments, no mention of the assistant in issue comments or contributor lists. A human co-author from a different account is fine.

## Code-review output contract

When reviewing a PR, post a top-level summary plus inline comments anchored to `file:line`. Keep the voice OSS-cordial: direct about problems, not performative.

Top-level summary structure:

- **Verdict** on the first line: APPROVE, REQUEST CHANGES, or NEEDS DISCUSSION.
- **Reasoning**: 3 to 6 short bullets, each grounded in code with a `file:line` citation. No assertions from memory.
- **Action items**: a numbered list of exactly what the author must change to land the PR. Separate blockers from nits explicitly.
- **Reversibility**: name the rollback mechanism for a non-trivial change (down migration, feature flag, clean revert, or not applicable).

Inline comments: one per concrete issue, at the line it occurs, with the suggested change. Do not restate the summary inline.

## Testing bar (non-negotiable)

Mirror the standard the senior reviewers hold:

- Tests land in the same PR. "I'll add tests later" is a REQUEST CHANGES blocker.
- Match each touched behavior to a tier: unit, integration, or E2E. A behavior that crosses a process boundary and is user-visible needs the full pyramid.
- A bug fix needs a regression test that fails on `main` and passes on the branch. No regression test is a blocker.
- Integration tier hits the real binaries (PyMuPDF, Tesseract, Chromium). Mocking a subprocess or native binary at the integration tier hides divergence and is a blocker.
- An a11y attribute change needs an axe-core E2E check.
- A UI diff needs before/after evidence; a design-token change needs visual regression.
- A unit test that mounts a parent component and awaits an async chain to assert a one-line render is over-engineered. Render the leaf in isolation.
- A test that `pytest.skip`s because a gitignored fixture is missing is a blocker. Commit the fixture or drop the test.
- Read CI output before trusting it. A green check on a feature with zero tests is a false positive, not coverage.

## Native dependencies

A new runtime or OS dependency (Tesseract, Poppler, mutool, and the like) lands in `pyproject`, the Dockerfile, and CI in the same PR. Flag any one of the three being missing.

## Visual regression baselines

Visual snapshot baselines are generated under Linux on CI only, never committed from a local machine (font rendering differs). The sanctioned refresh path is a maintainer comment `/update-snapshots` on the PR. Do not suggest committing locally-generated baselines.

## Scope discipline

Flag scope creep: a PR that quietly expands the product surface, adds a runtime external call, introduces telemetry, or drifts from the identity contract above. Keep PRs small (around 3 commits or fewer).
