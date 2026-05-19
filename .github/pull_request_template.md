<!--
Thanks for sending a pull request. A few notes before you submit:

- Keep this PR small and focused. One logical change per PR.
- Three commits is the comfortable ceiling for review. Squash on merge is
  the default, so you do not need to keep many commits.
- Tests at the lowest viable tier are expected for every behaviour change.
- See CONTRIBUTING.md for the full rules (no-business-mocks, no-AI-coauthor,
  test requirements, code style).

PR title must follow Conventional Commits 1.0.0:

  <type>(<scope>)<!>: <description>

Valid types: feat / fix / docs / style / refactor / perf / test / build /
ci / chore / revert. Examples:

  feat(web): add Spanish locale
  fix(api): tolerate string page destinations
  chore(deps): bump nginx to 1.31-alpine
  feat(api)!: change /api/md-to-pdf response shape (breaking)

The CI check `Semantic PR title` rejects non-compliant titles.
-->

## Summary

<!-- One or two sentences describing the change. -->

## Changes

- ...
- ...

## Test plan

- [ ] `npm run test:unit`
- [ ] `npm run test:integration`
- [ ] `npm run test:e2e` (if the change touches the UI or end-to-end flow)
- [ ] `npm run build` (if the frontend changed)

## Checklist

- [ ] Pre-commit hooks ran locally (`pre-commit run --all-files`).
- [ ] Branch is up to date with `main` (or the **Update branch** button
      on this PR has been clicked once required checks are queued).
- [ ] Tests cover the new behaviour (or the PR description explains why
      no test was needed).
- [ ] No new tests silently skip on CI.
- [ ] No `Co-Authored-By:` AI agent trailers in the commit history.
- [ ] Commit count is reasonable for review (rule of thumb: at most 3).

## Screenshots

<!-- Drop screenshots here if the UI changed. Before/after side by side helps. -->

## Related issues

<!-- Fixes #123, Refs #456 -->
