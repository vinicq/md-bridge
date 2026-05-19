# Contributing to md-bridge

Thanks for taking the time to look at this project. md-bridge stays small and
opinionated on purpose, but pull requests, bug reports, and ideas are welcome.
This guide explains how to file something useful and how to land a change.

## 30-second cheat sheet

If you only read one section, read this one. The four hard rules:

1. **Every change ships with tests.** Bug fix? Add a test that fails on `main`
   and passes on your branch. New feature? Add unit and integration tests.
2. **Keep pull requests small.** One logical change per PR, at most three
   commits. If your branch grows, split it.
3. **No AI agents as co-authors.** Copilot, Claude, Cursor, and friends are
   editors, not authors. Do not add them as `Co-Authored-By` lines in commit
   messages. (`Co-Authored-By` is a trailing line Git uses to credit a second
   author. We use it for humans only.)
4. **No tests that silently skip on CI.** If a test needs a file, commit the
   file. If you cannot commit it, the test does not belong in the public
   suite.

Everything below is the longer version of those rules. If you have never
opened a pull request on GitHub before, jump to
[Your first pull request](#your-first-pull-request) for the step-by-step.

## Quick links

- New to the code? Read the [README](README.md) first, especially the
  [Quickstart](README.md#quickstart) section.
- Found something broken? File a [bug report](.github/ISSUE_TEMPLATE/bug_report.md).
- Have an idea? Open a [feature request](.github/ISSUE_TEMPLATE/feature_request.md)
  or start a thread in
  [Discussions](https://github.com/vinicq/md-bridge/discussions).
- Reporting a security issue? Follow [SECURITY.md](SECURITY.md) instead of
  opening a public issue.

## Filing an issue

Before you open a new issue, please search existing issues to avoid
duplicates. If you do open one, the templates ask for the basics:

- For bugs: what you did, what you expected, what actually happened, and how
  to reproduce it. Logs and screenshots help a lot.
- For features: describe the problem first, then your proposed solution and
  any alternatives you have already considered.

Keep the title short and concrete. "PDF inspect endpoint returns 500 on
tagged files" is better than "bug in API".

## Your first pull request

If you have never opened a pull request on GitHub before, this section is
for you. Experienced contributors can skip to
[Submitting a pull request](#submitting-a-pull-request).

A pull request (PR) is a request to merge your changes into someone else's
repository. The full GitHub flow has eight steps. The commands below assume
you have Git installed and a GitHub account.

### 1. Fork the repository

On the [project page](https://github.com/vinicq/md-bridge), click the
**Fork** button at the top right. GitHub creates a copy of the repo under
your own account. You will work on this copy and propose your changes back
to the original.

### 2. Clone your fork to your computer

Replace `your-username` with your GitHub username:

```bash
git clone https://github.com/your-username/md-bridge.git
cd md-bridge
```

### 3. Track the upstream repository

"Upstream" is the original `vinicq/md-bridge` repo. Tracking it lets you
pull in new changes from the maintainer later. Run this once:

```bash
git remote add upstream https://github.com/vinicq/md-bridge.git
```

You can confirm with `git remote -v`: you should see `origin` pointing at
your fork and `upstream` pointing at the original repo.

### 4. Create a topic branch

Never commit directly to your `main`. Make a new branch named after the
work you are doing. The convention is `prefix/short-description`:

- `feature/` for new functionality (`feature/ocr-fallback`)
- `fix/` for bug fixes (`fix/inspect-tagged-pdf`)
- `docs/` for documentation only (`docs/quickstart-windows`)
- `chore/` for tooling, dependencies, CI (`chore/bump-vitest`)

```bash
git checkout -b fix/inspect-tagged-pdf
```

### 5. Make your changes and commit

Edit the code, add tests, run `npm run test:all` locally to confirm the
suite is green. Then commit, using the message style in
[Commit messages](#commit-messages):

```bash
git add path/to/changed/files
git commit -m "Fix inspect endpoint crash on tagged PDFs"
```

### 6. Push the branch to your fork

```bash
git push -u origin fix/inspect-tagged-pdf
```

The `-u` flag tells Git to track the remote branch, so future
`git push` commands are shorter.

### 7. Open the pull request

GitHub shows a banner with a "Compare & pull request" button right after
the push. Click it, and you will see a form pre-filled with the
[PR template](.github/pull_request_template.md). Fill in:

- The **summary** in one or two sentences.
- The **changes** as a short bullet list.
- The **test plan** checkboxes for the commands you ran.
- The **checklist** confirming tests cover the change, no silent CI
  skips, no AI co-author trailers, and the commit count is reasonable.

Click **Create pull request**. Your PR is now visible to the maintainer.

### 8. Work through review

CI runs automatically on every push to a PR. The expected outcome is
green checks on backend, web, and end-to-end jobs.

The maintainer will read the PR and either:

- **Approve and merge.** GitHub squashes your commits into one and merges
  the result into `main`. You will get a notification.
- **Request changes.** The maintainer leaves comments inline. To respond:
  edit the files, commit on the same branch, push. The PR updates
  automatically and the conversation continues.

There is no fixed turnaround time. If a week passes without a response,
feel free to ping with a polite comment.

### 9. After the merge

Once your PR is merged, clean up your fork:

```bash
# Switch back to main and pull the merged change from upstream
git checkout main
git pull upstream main
git push origin main

# Delete the branch locally and on your fork
git branch -d fix/inspect-tagged-pdf
git push origin --delete fix/inspect-tagged-pdf
```

You can also delete the branch directly on the GitHub UI through the PR
page.

### What this project does not require

- **No Contributor License Agreement (CLA)** or **Developer Certificate
  of Origin (DCO) sign-off.** You do not need to add a `Signed-off-by`
  trailer.
- **No GPG-signed commits.** Signed commits are welcome but not enforced.
- **No issue before a small PR.** Open an issue first only when the
  change is large or risky enough to need design discussion.

## Submitting a pull request

A pull request is a proposal to merge your branch into `main`. The basic
flow, in summary:

1. Fork the repo and create a topic branch off `main`.
2. Make your change with tests at the lowest viable tier.
3. Run the full test pyramid locally (see [Tests](#tests)).
4. Open the PR using the provided template.
5. Address review feedback by adding follow-up commits to the same branch.

If any step is unfamiliar, the detailed walkthrough is in
[Your first pull request](#your-first-pull-request).

Small, focused PRs ship faster than large ones. If a change is going to be
big, open an issue first so we can agree on the approach before you write
the code.

### Tests are required

Every behaviour change ships with tests. There is no separate "I will add
tests later" path. Concretely:

- **Bug fix:** add a regression test that fails on `main` and passes on your
  branch. The test proves the bug is gone and stays gone.
- **New feature:** add unit tests for pure logic, and an integration or
  end-to-end test if the feature has a user-visible surface.
- **Refactor with no behaviour change:** the existing suite must still pass.
- **Pure docs change:** no new tests required, but `npm run test:all` should
  still pass on your branch.

PRs that change runtime behaviour without tests will be asked to add them
before review.

### PR size and commit history

We aim for PRs that one person can review in a single sitting. As a rule
of thumb:

- One logical change per PR. If your branch grows into two unrelated topics,
  split it into two PRs.
- Up to three commits per PR is the comfortable ceiling for review. If your
  branch has more, fold them together locally before pushing. The two common
  tools for that are `git rebase -i` (interactive rebase: lets you combine
  or reorder commits) and `git commit --amend` (replace the last commit with
  a new one).
- The default merge strategy is **squash on merge**, which means GitHub
  collapses all your commits into a single commit on `main`. If you want
  the individual commits preserved (for example, a refactor commit followed
  by a behaviour commit), say so in the PR description and keep each commit
  atomic and buildable on its own.

The point is reviewer cognitive load, not the number itself.

### Authorship and AI tooling

This project does not accept AI agents as contributors. Concretely:

- Do **not** add AI agents (Copilot, Claude, GPT-family bots, Cursor, and
  similar) as `Co-Authored-By` trailers, commit authors, or GitHub
  contributors. (A "trailer" is a line near the end of a commit message
  that Git treats specially, like `Co-Authored-By:` or `Signed-off-by:`.)
- AI tools may be used as editors or assistants while you write code, the
  same way an IDE is a tool. The human pushing the commit is the author
  and is responsible for the change.
- Commit messages and PR descriptions should describe what the change does
  and why, in your own words. Generic AI-style boilerplate ("This pull
  request introduces a comprehensive refactor that...") will be flagged in
  review.

PRs that include an AI co-author trailer will be asked to rewrite the
commit history before merge.

## Local setup

Follow the [Quickstart in the README](README.md#quickstart). In short, you
need:

- Python 3.12 or newer for the backend.
- Node 22 and npm 10 or newer for the frontend.
- A one-time `python -m playwright install chromium` so the Markdown to PDF
  renderer can boot.

Once that is wired up, the root-level `npm run dev` starts the API on
`localhost:8000` and the Vite dev server on `localhost:5173`.

### How the `main` branch is protected

The `main` branch is gated on the GitHub side. Pull requests cannot be
merged until every required status check is green:

- Backend (pytest)
- Web (vitest + build)
- End-to-end (Playwright)
- Analyze (python)              -- CodeQL
- Analyze (javascript-typescript) -- CodeQL

Direct force-pushes and branch deletions are blocked, and merges produce
a linear history (no merge commits). Reviewer requirements are not
enforced (this is a solo-maintainer project), but the checks themselves
are non-negotiable.

### Dependabot auto-merge

Dependabot opens weekly PRs across the ecosystems configured in
`.github/dependabot.yml`. The `.github/workflows/dependabot-auto-merge.yml`
workflow auto-enables merge on two safe categories:

- Patch bumps (`X.Y.Z → X.Y.Z+1`).
- Transitive (indirect) dependency updates that come from a lockfile.

In both cases the same required status checks still have to pass before
the merge actually lands. Minor and major version bumps stay in the
manual review queue; their changelogs are worth two minutes of attention
before pulling.

### Optional: pre-commit hooks

The repo ships a `.pre-commit-config.yaml` that wires `ruff` and a handful
of hygiene checks (trailing whitespace, end-of-file newline, YAML/TOML
syntax, merge conflict markers, large files). Installing the hooks is
optional but catches the boring mistakes before review:

```bash
pip install pre-commit
pre-commit install
```

From that point on, every `git commit` runs the hooks against the staged
files. CI runs the same checks, so skipping pre-commit only delays the
feedback; it does not let bad code reach `main`.

## Tests

md-bridge follows a strict test pyramid: many small tests, fewer slower
tests, even fewer end-to-end tests. Every pull request adds tests at the
lowest viable tier.

- **Unit tests** for pure functions, heuristics, and components.
  Backend: `pytest apps/api/tests/unit tests/unit`. Frontend:
  `npm run test:unit`.
- **Integration tests** for the FastAPI app and React routing wired
  together. Backend: `pytest apps/api/tests/integration tests/regression`.
  Frontend: `npm run test:integration`.
- **End-to-end tests** with Playwright that drive a real browser against a
  real backend. Frontend: `npm run test:e2e`.

Pick the lowest tier that actually exercises the behaviour. A heuristic
that parses a heading does not need a Playwright test; a button that
triggers a download does.

The suite runs against a committed real-world fixture
(`apps/api/tests/fixtures/istqb-ctal-ta-syllabus-en.pdf`) so every clone
can reproduce the green build with no extra data and no silent skips.

### What is allowed in tests

- Real implementations whenever possible. The PDF fixture in
  `apps/api/tests/fixtures/` is committed for exactly this reason.
- Platform-level test doubles from the standard React Testing Library and
  Vitest toolkits: callback spies via `vi.fn()`, fake timers via
  `useFakeTimers`, and similar helpers provided by the test framework.

### What is not allowed in tests

- Mocking business-layer modules. If a component calls a helper from
  `packages/`, the test should run that helper for real.
- Mocking `fetch`, the File API, or other browser APIs. Use a real request
  against the running app, a real `File` object, or a Playwright test if
  the boundary really is the browser.
- Hand-rolled stand-ins for modules that already have a real implementation
  in the repo.
- Tests that silently skip on CI because they depend on data not present
  in the repo. Either commit the fixture or drop the test.

If you find yourself reaching for a heavy mock, that is usually a signal
that the test belongs one tier higher.

## Code style

### TypeScript and React

- `strict` mode is on in `tsconfig.json` and stays on. No `any`, no
  `// @ts-ignore` without a comment that explains why.
- Prefer function components and hooks. Keep components small.
- ESLint is the source of truth: `npm run lint` from `apps/web/` must pass.
  CI enforces this.

### Python

- Target Python 3.12+ idioms: PEP 695 type parameters where they help,
  `match` statements when the alternative is a long `if/elif` chain,
  `pathlib.Path` over `os.path` strings.
- Type hints on public functions. `from __future__ import annotations` is
  fine but not required.
- [`ruff`](https://docs.astral.sh/ruff/) is the linter. Configuration lives
  in `apps/api/pyproject.toml` under `[tool.ruff]`. CI runs `ruff check`
  on every PR. Run it locally before pushing:

  ```bash
  python -m ruff check apps/api tests packages --config apps/api/pyproject.toml
  ```

  The rule selection is `E F W I UP B` (pycodestyle errors and warnings,
  pyflakes, import sorting, pyupgrade, bugbear). `ruff check --fix`
  resolves most issues automatically.

### Comments

Code should read top to bottom. Comments explain the non-obvious "why",
not the obvious "what". A comment that restates the next line is noise;
a comment that explains a workaround for a PyMuPDF quirk is useful.

## Commit messages

We follow the standard Git convention:

- Subject line in the imperative mood ("Add fallback for tagged PDFs",
  not "Added" or "Adds").
- 72 characters or fewer for the subject.
- Body wrapped at 80 columns, separated from the subject by a blank line.
- Explain the "why" in the body when the change is not self-evident.
- Reference issues with `Fixes #123` or `Refs #123` on a trailing line.

A good commit message looks like:

```
Drop pypdf fallback for outline parsing

PyMuPDF's get_toc() now handles every fixture we ship, and the pypdf
fallback added 200 ms to cold starts. Remove it and the dependency.

Fixes #142
```

## License and contributions

md-bridge is released under the [MIT License](LICENSE). By submitting a
pull request you agree that your contribution will be licensed under the
same terms. If you are contributing on behalf of a company, please make
sure you have permission to do so.

## Code of conduct

This project follows the [Contributor Covenant 2.1](CODE_OF_CONDUCT.md).
Be kind, assume good faith, and report any incident to the maintainer
email listed there. We want a healthy project, and that starts with how
people treat each other.

Welcome aboard, and thanks again for helping out.
