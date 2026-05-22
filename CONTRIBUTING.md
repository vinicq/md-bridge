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

## Repository secrets

A few workflows need credentials that cannot live in the repo. Contributors
do not have to set these up themselves; the maintainer creates them
repo-side before the dependent feature lands on `main`. If you are reading
this because a workflow you wrote needs a new secret, name the secret in
your PR description so the maintainer can provision it before merge.

| Secret | Purpose | Created by |
|---|---|---|
| `GITHUB_TOKEN` | Automatic per-job token issued by GitHub Actions; covers most workflow needs. | GitHub (automatic) |
| `PROJECTS_TOKEN` | Fine-grained PAT scoped to user-level Projects v2 board (`Account: Projects: Read and write`). Required because the default `GITHUB_TOKEN` cannot mutate user-level projects. Workflows that touch the board (`issue-claim.yml`, `board-sync.yml`) fall back to a no-op with a warning when the secret is missing, so the rest of the workflow still completes. | Maintainer |
| `CODECOV_TOKEN` | Codecov upload token for backend coverage reports. Provisioned at <https://codecov.io> after the repo is added; the value is set as a repo secret in **Settings → Secrets and variables → Actions**. | Maintainer |

All secrets are stored in **Settings → Secrets and variables → Actions** at
the repo level (not at the environment level, since md-bridge does not use
deployment environments). Tokens that mutate state outside the repo (the
Projects v2 board, third-party services) are issued as fine-grained PATs
with a one-year expiry and a calendar reminder for rotation.

If you spot a workflow that references a secret which is not listed above,
that is a documentation bug. Open an issue.

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

### Features that need design

Issues tagged `design-required` need a visual proposal before a PR
lands. The project's design system at
[`docs/design/`](docs/design/) (also published at
<https://vinicq.github.io/md-bridge/design/>) catalogues every accepted
mockup as features F1 through F8. When you pick up a `design-required`
issue, scan the catalogue first; most open ones already have a matching
mockup with a paste-ready acceptance spec you can implement against.

For brand-new ideas, open the issue with a sketch (Excalidraw, plain
PNG, even ASCII) and the maintainer will decide whether it slots into
an existing F-section or warrants a fresh design pass.

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

## Claiming an issue before you code

If the change you want to make matches an existing open issue, please
**claim the issue before you start coding**. This stops two
contributors from racing on the same work without realising.

### The fast path: `/claim`

Comment **`/claim`** (or the alias **`/take`**) on the issue. The
`Issue claim` Action adds the `status: claimed` label, assigns you if
you are a collaborator, posts a confirmation comment with the deadline,
and moves the card to the Claimed column on the project board. No
maintainer wait.

External contributors cannot be set as GitHub assignees on this
repository (the API rejects non-collaborators). The Action posts an
attribution comment in that case so the claim is still anchored in the
issue history. The label and the project board move work the same way.

From the moment of confirmation, the issue is yours for **seven days**.

### What to do once claimed

1. Open a draft PR within the window, even if it is empty. The draft
   signals progress and lets the maintainer pre-review your direction.
2. If the scope changed since you read it, leave a comment naming the
   change so the maintainer can confirm or narrow.
3. If you cannot finish in time, comment to release the issue and the
   maintainer will reassign it.

The assignee always has first refusal. If you open a PR against an
issue someone else is assigned to, the maintainer will close yours as
a duplicate and direct you to the original assignee's PR.

### When you do not need to claim

For tiny fixes — typos, broken links, one-line bug fixes, dependency
bumps the maintainer has not yet seen — you do not need to claim a
matching issue first. Just open the PR with `Fixes #N` (if the issue
exists) and you are done.

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

- **Bug fix:** add a regression test in the appropriate tier (unit,
  integration, or E2E) that **demonstrably fails on `main` without your
  fix**. Include the failing diff in the PR description so reviewers can
  verify the test catches the bug.
- **New feature:** add unit tests for pure logic, and an integration or
  end-to-end test if the feature has a user-visible surface.
- **Refactor with no behaviour change:** the existing suite must still pass.
- **Pure docs change:** no new tests required, but `npm run test:all` should
  still pass on your branch.

PRs that change runtime behaviour without tests will be asked to add them
before review.

### Writing a good regression test

A good regression test proves two things: the old bug is observable, and the
new fix is what makes the test pass. It should live at the lowest tier that
exercises the bug and should fail against `main` without unrelated setup.

For example, #20 fixed a false-red Docker publish smoke probe introduced in
#17. The original web-image smoke command ran `nginx -t`, but
`apps/web/nginx.conf` contains `proxy_pass http://api:8000`. In an isolated
`docker run`, the `api` hostname is not present, so `nginx -t` fails even
when the built web image is fine.

A useful regression test for that bug would:

1. Run the same web-image smoke probe the workflow uses.
2. Fail on `main` with the `host not found in upstream "api"` error while
   the probe still relies on `nginx -t`.
3. Pass on the fix branch after the probe checks the build artifact that
   matters, such as `/usr/share/nginx/html/index.html`.

Include the failing diff or failure output in the PR description. Reviewers
should be able to see that the test catches the specific bug, not just that
the final suite is green.

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

### Install the pre-commit hooks (strongly recommended)

Before your first commit, install the local hooks. They run `ruff` and a
handful of hygiene checks (trailing whitespace, end-of-file newline,
YAML/TOML syntax, merge conflict markers, large files) against every
staged file, catching the boring mistakes in milliseconds instead of in
the CI run minutes later:

```bash
pip install pre-commit
pre-commit install
```

From that point on, every `git commit` runs the hooks. The hook list
lives in `.pre-commit-config.yaml`. CI runs the same checks, so skipping
the hooks does not let bad code reach `main`, but it does mean you pay
the round-trip every time.

**What the hooks do not check (and do not need to):** whether your
branch is behind `main`. That is a server-side concern. Branch protection
on `main` enforces *"require branches to be up to date before merging"*,
so the GitHub UI shows an **Update branch** button on every PR opened
against a stale base. You only need to click it (or run
`gh api -X PUT repos/<owner>/<repo>/pulls/<n>/update-branch`) before the
merge; the pre-commit hooks deliberately stay out of network operations.

### How the `main` branch is protected

The `main` branch is gated on the GitHub side. Pull requests cannot be
merged until every required status check is green:

- Backend (pytest)
- Web (vitest + build)
- End-to-end (Playwright)
- Analyze (python)              -- CodeQL
- Analyze (javascript-typescript) -- CodeQL
- Validate PR title             -- Conventional Commits regex

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

### Pre-commit hooks

See [Install the pre-commit hooks](#install-the-pre-commit-hooks-strongly-recommended)
under Local setup. The hooks run on every `git commit`; if you skipped
the install during setup, you can add them at any time without changing
your existing branch.

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

## Commit messages — Conventional Commits

This project follows the
[Conventional Commits 1.0.0](https://www.conventionalcommits.org/en/v1.0.0/)
specification. Because the default merge strategy is **squash on merge**,
the PR title becomes the commit message on `main`. Both the PR title and
the commits in your branch must match the format.

The CI workflow `.github/workflows/semantic-pr.yml` validates every PR
title against the spec; a non-compliant title fails the check and blocks
the merge.

### Format

```
<type>(<scope>)<!>: <description>

[body]

[footer(s)]
```

- `<type>` is required and lowercase.
- `(<scope>)` is optional and lowercase. Use it to point at the affected
  area: `(api)`, `(web)`, `(docs)`, `(deps)`, `(ci)`.
- `!` after the type or `(<scope>)` flags a breaking change (also
  declarable in the footer as `BREAKING CHANGE: ...`).
- `<description>` starts lowercase, present tense, imperative mood. No
  trailing period. 72 characters max.
- Blank line between subject and body. Body wrapped at 80 columns,
  explains the *why*. Reference issues in a footer: `Fixes #142` or
  `Refs #99`.

### Recognised types

| Type      | Use it for                                       | Bumps    |
| --------- | ------------------------------------------------ | -------- |
| `feat`    | New user-facing feature                          | minor    |
| `fix`     | Bug fix                                          | patch    |
| `docs`    | Documentation only (README, CONTRIBUTING, docs/) | none     |
| `style`   | Whitespace, formatting, no logic change          | none     |
| `refactor`| Refactor without behaviour change                | none     |
| `perf`    | Performance improvement                          | patch    |
| `test`    | Adds or fixes tests only                         | none     |
| `build`   | Build system, Docker, package configs            | none     |
| `ci`      | CI configuration, workflows                      | none     |
| `chore`   | Maintenance that does not fit the above          | none     |
| `revert`  | Reverts a previous commit                        | depends  |

A trailing `!` (`feat(api)!: change /pdf-to-md response shape`) or a
`BREAKING CHANGE:` footer **always** bumps major, regardless of type.

### Examples

```
fix(api): tolerate string page destinations in PDF link annotation

PyMuPDF returns link["page"] as a string when a named destination cannot
be resolved to a numeric page index. The old `page_dest >= 0` check then
raised TypeError mid-conversion. Coerce the value safely and skip the
link when it is not an integer page index.

Fixes #142
```

```
feat(web): add Spanish locale

Adds 'es' to the Locale union, the LOCALES array, and the DICTIONARIES
map. Generalises locale detection so the html lang attribute and the
storage fallback handle every declared locale instead of just 'en' and
'pt'. Tests and the Playwright spec exercise the three locales.

Fixes #6
```

```
docs: expand the Oracle Cloud deployment recipe
```

```
chore(deps): bump nginx from 1.27-alpine to 1.31-alpine
```

```
feat(api)!: change /api/md-to-pdf response shape

The response is now a JSON envelope { pdf, stats } instead of a raw
binary stream. Clients that downloaded the previous shape will break.

BREAKING CHANGE: /api/md-to-pdf no longer returns application/pdf
directly. Set Accept: application/pdf to opt back into the legacy
binary response, or read the base64 pdf field from the new envelope.
```

### Why this matters

- **`semantic-pr.yml`** rejects PR titles that do not match the spec, so
  the requirement is enforced, not aspirational.
- **`release-drafter`** keeps the draft GitHub Release in sync with the
  PR types it sees, and it auto-resolves the next semver bump from those
  types.
- **`git log --oneline`** becomes documentation: `feat:` and `fix:`
  prefixes let a reader scan the changelog in seconds.
- **Tools that generate CHANGELOGs from commit history** (git-cliff,
  conventional-changelog-cli, release-please) work out of the box.

## License and contributions

md-bridge is released under the [MIT License](LICENSE). By submitting a
pull request you agree that your contribution will be licensed under the
same terms. If you are contributing on behalf of a company, please make
sure you have permission to do so.

### Getting credit in the Contributors list

The project follows the
[all-contributors specification](https://github.com/all-contributors/all-contributors).
Every kind of contribution counts: code, documentation, translation,
design, ideas, review, tests, infrastructure, even bug reports. The
list lives in the [`Contributors` section of the README](README.md#contributors)
and is rendered from `.all-contributorsrc`.

After your PR merges, the maintainer will add you to the list with the
emoji that fits your contribution type (see the
[emoji key](https://allcontributors.org/docs/en/emoji-key)). If you
want to claim a specific type up front, mention it in the PR
description. There is no need to install a bot or open a second PR for
this; the maintainer regenerates the README block as part of release
maintenance.

### Maintainer responsibility: keep the credit list current

After every external-contributor PR merges, the
[`Credit contributor on merge`](.github/workflows/credit-contributor.yml)
workflow runs:

1. Infers contribution categories from the merged diff. The mapping is
   mechanical: code under `apps/`, `packages/` → `code`; `*.md` and
   `docs/` → `doc`; tests → `test`; `i18n` or `dictionaries.ts` →
   `translation`; workflows, Dockerfiles, `deployment/` → `infra`;
   `docs/design/`, `tokens.css`, `theme.css` → `design`.
2. Runs `npx all-contributors-cli add` (idempotent, merges new
   categories with any existing entry) and `generate` to rewrite the
   README block.
3. Opens a `chore(docs): credit @<author>` PR with the changes,
   assigned to vinicq. The maintainer reviews the inferred categories
   and merges.

The workflow skips maintainer PRs (vinicq) and bot PRs (Dependabot,
release-drafter, etc.) at the job `if`. Merged PRs that close without
merging never trigger it.

**Manual fallback when the Action does not fit.** If a contribution
deserves a category the diff-based inference cannot see (`review` 👀
on a PR that caught a bug, `bug` 🐛 for a report that led to a fix,
`ideas` 🤔 for the umbrella discussion that shaped a feature), edit
`.all-contributorsrc` by hand and run `npx all-contributors-cli
generate` locally. The Conventional Commits subject is
`chore(docs): credit <login> for <type1>+<type2>`. Avatar URLs must
use the numeric-ID form
(`https://avatars.githubusercontent.com/u/<id>?v=4` from
`curl -s https://api.github.com/users/<login> | jq -r .id`) or they
fall back to an identicon.

Types accumulate over a contributor's lifetime in the project; they
never narrow. The credit list is part of how the project respects the
people who show up.

## Code of conduct

This project follows the [Contributor Covenant 2.1](CODE_OF_CONDUCT.md).
Be kind, assume good faith, and report any incident to the maintainer
email listed there. We want a healthy project, and that starts with how
people treat each other.

Welcome aboard, and thanks again for helping out.
