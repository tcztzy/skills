# Static Type-Checker Stack

Use Python like a statically typed language.

Do not stop at one checker if the repository can support more.
Different tools catch different classes of mistakes.

## Baseline

Always run:

1. `ruff check`
2. `mypy --strict`
3. `basedpyright` or `pyright`

Recommended preference:

- `basedpyright` first if the repo accepts its stricter posture
- otherwise `pyright`
- keep `mypy --strict` too; do not replace one with the other

## Additional checkers

Add these when the environment supports them and the maintenance cost is acceptable:

- `pyre --noninteractive check`
- `pytype`
- `ty check`

## CI order

A practical order is:

```bash
ruff check .
mypy --strict .
basedpyright
pyright
pyre --noninteractive check
pytype
ty check
```

Run only the tools that are actually installed for that repo, but if a tool is already part of the environment, use it.

## Policy

- Prefer strict modes
- Avoid `Any` unless there is a real boundary reason
- Type-check tests too when feasible
- Do not waive failures by default
- If two checkers disagree, tighten the code until both pass when practical
- Treat typed public APIs as contracts, not comments

## Notes on overlap

- `mypy` and `pyright` overlap, but not perfectly
- `basedpyright` is usually stricter than upstream `pyright`
- `pyre`, `pytype`, and `ty` may catch additional issues or model code differently
- Redundancy is acceptable when it catches different classes of bugs; pointless ceremony is not

## Wrapper-function stance

Static typing is not an excuse to add ceremony.

Do not create a tiny wrapper function only to move one obvious typed call behind another name unless it creates a real abstraction boundary or reuse point.
