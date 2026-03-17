---
name: "yeet"
description: "Use only when the user explicitly asks to stage, commit, push, and open a GitHub pull request in one flow using the GitHub CLI (`gh`)."
---

## Prerequisites

- Require GitHub CLI `gh`. Check `gh --version`. If missing, ask the user to install `gh` and stop.
- Require authenticated `gh` session. Run `gh auth status`. If not authenticated, ask the user to run `gh auth login` (and re-run `gh auth status`) before continuing.

## Naming conventions

- Branch: `codex/{description}` when starting from main/master/default.
- Commit: `{description}` (terse).
- PR title: `[codex] {description}` summarizing the full diff.

## Workflow

- If on main/master/default, create a branch: `git checkout -b "codex/{description}"`
- Otherwise stay on the current branch.
- Confirm status with `git status -sb`.
- If unrelated or unexpected changes are present, stop and ask the user which files belong in this submission.
- Stage only the task-related files explicitly (for example `git add path/to/file1 path/to/file2`). Do not default to `git add -A`.
- Commit tersely with the description: `git commit -m "{description}"`
- Run checks if not already. If checks fail due to missing deps/tools, install dependencies and rerun once.
- Push with tracking: `git push -u origin $(git branch --show-current)`
- If `git push` fails, report the category clearly:
  - authentication/permission problem -> fix `gh` or git credentials
  - non-fast-forward -> explain that the remote branch changed and ask before pulling or rebasing
  - other transport/server errors -> report stderr and stop
- Do not automatically pull, merge, or rewrite history to make the push succeed.
- Open a PR and edit title/body to reflect the description and the deltas: `GH_PROMPT_DISABLED=1 GIT_TERMINAL_PROMPT=0 gh pr create --draft --fill --head $(git branch --show-current)`
- Write the PR description to a temp file with real newlines (e.g. pr-body.md ... EOF) and run pr-body.md to avoid \\n-escaped markdown.
- PR description (markdown) must be detailed prose covering the issue, the cause and effect on users, the root cause, the fix, and any tests or checks used to validate.
