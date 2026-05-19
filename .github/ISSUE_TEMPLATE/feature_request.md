---
name: Feature request
about: Suggest an idea or improvement
title: ""
labels: enhancement
assignees: ""
---

## Problem

What real use case is this trying to solve? Who is affected and how often?

## Proposed solution

A clear description of what you would like to see happen. Sketch the API,
the UI, or the CLI command if it helps.

## Architect notes

Technical sketch: which modules change, what is the seam, what depends on
what. Cross-cutting impact: does this touch CI, Docker, deployment, or
existing public API contracts? If yes, name those touchpoints explicitly.

## QA notes (every implementation needs tests)

Be explicit about **which tests, at which tier, in which files**. Fill in
the rows that apply; leave blank the ones that do not.

| Tier | File | What it asserts |
|---|---|---|
| Unit | e.g. `apps/api/tests/unit/test_foo.py` | ... |
| Integration | e.g. `apps/api/tests/integration/test_bar.py` | ... |
| E2E | e.g. `apps/web/e2e/foo.spec.ts` | ... |
| Regression | (for bug fixes) test that fails on `main` and passes on the branch | ... |

A feature with no test plan does not merge. See `CONTRIBUTING.md` for the
test pyramid and the no-business-mocks rule.

## Design notes

Skip if the change has no UI surface. Otherwise, describe the visual /
UX impact and what a designer needs to produce **before** an engineer
opens the implementation PR:

- Spec doc / Figma frame for the new component or page state.
- Token mapping if new colours, spacing, or typography are introduced.
- Accessibility considerations (contrast pairs, focus order, screen reader announcements).

Frontend issues without design notes will be asked to add them before the
implementation PR is reviewed.

## Alternatives considered

Other approaches you thought about and why they fell short.

## Acceptance criteria

- [ ] ...
- [ ] ...

Use checkboxes. A maintainer ticks them off as the PR lands.

## Out of scope

Bullet list of things this issue explicitly does NOT cover. Helps a future
contributor avoid scope creep.

## Additional context

Links, related issues, design references, or anything else that helps.
