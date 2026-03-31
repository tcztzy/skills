# Wenyan Playbook (Simplification + Measurement)

Use this reference when simplifying Wenyan source (`.wy`), especially `wenyan.wy`. Keep changes behavior-preserving by default, and validate both source-level and compiled-Python complexity alongside Wenyan-specific bootstrap checks.

## Measurement

Track formatted size with:

```console
$ wc -l path/to/file.wy
$ wc -c path/to/file.wy
```

Also record:
- Sentence count by counting `。`.
- Touched keyword counts for forms such as `吾有`, `今有`, `名之曰`, `施`, `乃得`, `若`, `凡`, and `書之`.
- Compiled Python AST metrics (`ast_nodes`, `ast_branches`, `ast_max_depth`) from the Wenyan source.

Example probe:

```python
import ast
from pathlib import Path

import wenyan

path = Path("wenyan.wy")
source = path.read_text(encoding="utf-8")

keywords = ["吾有", "今有", "名之曰", "施", "乃得", "若", "凡", "書之"]
text_metrics = {
    "lines": source.count("\n") + (1 if source else 0),
    "bytes": len(source.encode("utf-8")),
    "sentences": source.count("。"),
    "keywords": {token: source.count(token) for token in keywords},
}

tree = wenyan.編譯為PythonAST(source, str(path))
node_count = sum(1 for _ in ast.walk(tree))
branch_types = (ast.If, ast.For, ast.AsyncFor, ast.While, ast.Try, ast.IfExp)
branch_count = sum(isinstance(node, branch_types) for node in ast.walk(tree))


def max_depth(node, depth=0):
    children = list(ast.iter_child_nodes(node))
    if not children:
        return depth
    return max(max_depth(child, depth + 1) for child in children)


print(
    {
        **text_metrics,
        "ast_nodes": node_count,
        "ast_branches": branch_count,
        "ast_max_depth": max_depth(tree),
    }
)
```

Notes:
- Compare `lines` + `bytes` + `sentences` + keyword counts + `ast_*` together, not one metric in isolation.
- For Wenyan, a shorter file is not a win if phrase complexity, bootstrap safety, or grammar clarity regresses.

## Simplification Patterns (Wenyan)

- Remove duplicated phrase patterns and repeated literal blocks.
- Collapse one-time aliases and temporary names when readability improves.
- Prefer reusable Wenyan idioms only when total phrase complexity decreases.
- Keep lexer/parser-facing paths easy to reason about; do not simplify in ways that obscure grammar behavior.

## Hard Guards

- Preserve observable semantics, output order, and error-surface behavior.
- Preserve bootstrap startup compatibility: updated `wenyan.wy` must run under both `wenyan.py` and `@wenyan/cli` when that file is in scope.
- Keep terminology and style consistent with the existing Wenyan codebase.
- Avoid grammar drift. If simplification requires syntax or keyword behavior changes, update `SPEC.md`, `wy.spec`, tests, and examples together.

## Validation

Minimum regression checks:

```console
$ uv run python -m unittest discover -s tests -p "test_*.py"
$ uv run python scripts/compare_examples_impl.py
```

For `wenyan.wy` changes, also run:

```console
$ uv run python -m unittest tests/test_bootstrap_prep.py
$ uv run python -m unittest tests/test_wywy_cli.py
```

Notes:
- Run the shared repo checks first, then add the Wenyan-specific bootstrap checks when `wenyan.wy` or bootstrap behavior is affected.
- If runtime parity is part of the touched surface, keep `scripts/compare_examples_impl.py` in scope.

## Common Failure Modes

- Claiming a win from line count alone while bytes, sentence complexity, or compiled AST complexity stay flat or regress.
- Introducing clever Wenyan idioms that are denser but harder to debug or reason about.
- Simplifying `wenyan.wy` without checking both implementations.
- Tweaking syntax-adjacent code without updating spec/tests/examples together.

Correct action:
- Re-measure all Wenyan-specific metrics, re-run the affected tests, and reject the change if the simplification is only cosmetic.

## Output Checklist

- Report baseline and final metrics: lines, bytes, sentence count, touched keyword counts, `ast_nodes`, `ast_branches`, `ast_max_depth`.
- Report net deltas and whether readability/maintainability stayed acceptable.
- Report validation results for impacted tests, runtime parity checks, and bootstrap checks when applicable.
- If no true simplification is achieved, provide failure analysis and the next strategy.
