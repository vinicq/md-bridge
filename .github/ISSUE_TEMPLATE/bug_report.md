---
name: Bug report
about: Report a defect or unexpected behavior
title: ""
labels: bug
assignees: ""
---

## Summary

A short description of what went wrong.

## Steps to reproduce

1. ...
2. ...
3. ...

## Expected behavior

What you thought would happen.

## Actual behavior

What actually happened. Paste the error message or response body if relevant.

## Environment

- OS:
- Python version (`python --version`):
- Node version (`node --version`):
- Browser and version (if frontend):
- Run mode: local `npm run dev` / `docker compose up` / production build / GHCR pull

## Logs

Backend stack trace, browser console output, or `curl` output. Wrap in code
fences. Redact anything sensitive.

## Screenshots

For UI bugs, drop one or two screenshots that show the problem.

## Regression test plan (every bug fix needs one)

Every PR that fixes a bug ships with a regression test that fails on `main`
and passes on the branch. Sketch where the test will live so the
maintainer can pre-validate the approach:

| Tier | File | What it asserts |
|---|---|---|
| (pick one) | e.g. `apps/api/tests/unit/test_foo.py` | The bug is reproduced when the fix is reverted. |

If you are not sure which tier fits, that is fine — leave the row open and
the maintainer will pair on it during review. The discipline is that no
fix lands without a test demonstrating the bug.
