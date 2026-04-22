---
name: modern-python-style
description: Enforce modern Python 3.10+ syntax, static typing discipline, and anti-ceremony code style with deterministic checks. Use when prompts mention banning typing.List or Optional, banning from __future__ import annotations, treating Python like a statically typed language, enabling multiple type checkers, rejecting pointless tiny wrapper functions, or wiring pre-commit and CI to fail on obsolete compatibility syntax.
---

# Modern Python Style

Use this skill to turn strict modern Python preferences into hard repo checks.

This skill is for Python 3.10+ codebases that want Python written like a statically typed language, with modern syntax mandatory rather than optional.

## Core stance

If the project has already upgraded to a version that supports better syntax or stronger tooling, use it everywhere.

Do not keep writing old compatibility syntax in a modern-only codebase.
Do not keep Python dynamically sloppy when static analysis can catch mistakes earlier.
Do not add one-use tiny wrapper functions that add no abstraction, no reuse, and no semantic compression.

## What this skill enforces

- Ban `from typing import List`, `Dict`, `Set`, `Tuple`, `Optional`, `Union`
- Ban `typing.List`, `typing.Dict`, `typing.Set`, `typing.Tuple`, `typing.Optional`, `typing.Union`
- Ban `from __future__ import annotations`
- Prefer built-in generics such as `list[str]` and unions such as `T | None`
- Treat Python as a statically typed language in practice: annotate public surfaces, keep types specific, and run multiple type checkers in CI
- Reject trivial single-use wrapper functions with no abstraction value; inline them or replace them with a real abstraction boundary

## Ruff coverage

Use Ruff as the syntax enforcement layer. Current Ruff can express the exact bans this skill needs:

- `UP006`: `List[T]` / `typing.List[T]` -> `list[T]`, and equivalent built-in generics
- `UP007`: `Union[A, B]` -> `A | B`
- `UP035`: deprecated `typing.List`, `typing.Dict`, `typing.Set`, `typing.Tuple` imports
- `UP045`: `Optional[T]` -> `T | None`
- `TID251`: configured project bans for `typing.*` names and `__future__.annotations`

Keep `FA100` and `FA102` ignored if the repo enables broader rule groups, because those rules suggest adding `from __future__ import annotations`, which this skill explicitly bans.

Ruff does not replace static type checkers or code-review judgment. Use Ruff for syntax and import policy; use type checkers for type correctness; use review judgment for pointless wrappers.

## Files in this skill

- `assets/pyproject.ruff.toml`: Ruff snippet for the policy baseline
- `assets/pre-commit.yaml`: Ruff pre-commit hook snippet
- `references/static-typecheck-stack.md`: recommended type-checker stack and CI order

## Default workflow

1. Confirm the project minimum Python version is `3.10+`.
2. Add the Ruff snippet from `assets/pyproject.ruff.toml` into the repo's `pyproject.toml`.
3. Add the pre-commit hook from `assets/pre-commit.yaml`.
4. Run Ruff in CI:

```bash
ruff check .
```

5. Add as many type checkers as the repo can support without redundancy theater. Default priority order is in `references/static-typecheck-stack.md`.
6. If the repo already has legacy annotations, fix them before enabling a required CI gate.
7. If the repo contains trivial one-use wrapper functions, remove them during cleanup instead of blessing them as style.

## Type-checking policy

For modern Python code, default to maximum practical static analysis.

Minimum expected stack:

- `basedpyright` or `pyright`
- `mypy`
- `ruff check`

Add any of these when available and useful in the repo environment:

- `pyre`
- `pytype`
- `ty`

Rules:

- Run every available checker in CI, not just one favorite
- Prefer strict modes over permissive defaults
- Keep annotations precise; avoid `Any` unless there is a concrete boundary reason
- Type-check tests too when feasible
- Treat new type-checker failures as real failures, not documentation

## Tiny wrapper rule

Strongly prefer direct code over throwaway wrappers.

Bad:

- function is called once
- body is only one obvious forwarding call
- adds no naming benefit, no reused policy, no boundary isolation, no test seam, no branch compression

Reasonable exceptions:

- real abstraction boundary
- reused behavior
- permission or side-effect boundary
- dependency inversion for testing
- materially better naming for a complex operation

If none of those apply, inline it.

## Commands

Check a repository tree:

```bash
ruff check .
```

Check only specific paths:

```bash
ruff check src tests
```

## Decision rules

- If the repository supports Python `<3.10`, do not use this skill as-is.
- If the repository is modern-only, prefer hard failure over soft guidance.
- Do not tell the model to "try" newer syntax while leaving the repo mechanically unenforced.
- Put the policy in code and CI, not only in prose.
- When choosing between ceremony and directness, prefer directness unless the abstraction clearly pays for itself.

## Expected output

A repo change set that includes:

- Ruff config for `UP`, `TID251`, and the banned APIs in `assets/pyproject.ruff.toml`
- pre-commit hook
- CI command that fails on banned syntax
- multiple static type checkers enabled where available
- fewer pointless wrapper functions, not more
