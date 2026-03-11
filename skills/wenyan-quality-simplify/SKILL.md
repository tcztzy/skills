---
name: wenyan-quality-simplify
description: Simplify Wenyan language source code (`.wy`, especially `wenyan.wy`) with strict quality gates while preserving semantics. Use when Codex is asked to compress/refactor/reduce duplication in Wenyan programs and must verify bootstrap compatibility across `wenyan.py` and `@wenyan/cli`, plus SPEC/grammar consistency.
---

# Wenyan Quality Simplify

Simplify Wenyan source with behavior preserved, bootstrap-safe changes, and measurable quality wins.

## Workflow

1. Establish baseline on target `.wy` file.
- Record lines (`wc -l`) and bytes (`wc -c`).
- Record sentence count (count `。`) and keyword counts for touched forms.
- Compile once and record generated Python AST metrics (nodes/branches/max depth).
- Run host execution baseline with `wenyan.py` (same input/output fixtures).
- For `wenyan.wy`, run bootstrap baseline (`uv run python -m unittest tests/test_bootstrap_prep.py tests/test_wywy_cli.py`).

2. Apply behavior-preserving simplifications in Wenyan syntax.
- Remove duplicated phrase patterns and repeated literal blocks.
- Collapse one-time aliasing/temporary names when readability improves.
- Prefer reusable Wenyan idioms only when total phrase complexity decreases.
- Keep error-surface behavior stable (especially grammar/lexer-facing paths).

3. Enforce Wenyan-specific hard constraints.
- Preserve observable semantics and output order.
- Preserve bootstrap startup compatibility: updated `wenyan.wy` must run under both implementations.
- Keep terminology and style consistent with existing Wenyan codebase conventions.
- Avoid grammar drift: if simplification requires syntax/keyword behavior changes, update `SPEC.md`, `wy.spec`, tests, and examples together.

4. Validate every pass.
- Recompute lines/bytes/sentence+keyword metrics and compiled Python AST metrics.
- Re-run affected tests and examples.
- Minimum regression checks:
  - `uv run python -m unittest discover -s tests -p "test_*.py"`
  - `uv run python scripts/compare_examples_impl.py` (when runtime parity is in scope)
- For `wenyan.wy` changes, explicitly run both:
  - `uv run python -m unittest tests/test_bootstrap_prep.py`
  - `uv run python -m unittest tests/test_wywy_cli.py`

5. Treat non-improvement as failure.
- If only lines drop but bytes/sentence complexity/AST complexity/readability do not improve, fail.
- If simplification harms maintainability or debugging clarity, fail.
- Explain failure cause and switch strategy (e.g., deduplicate declarations first, then reduce nested control flow).

## Suggested Metrics Snippet (for `.wy` text + compiled AST)

```python
import ast
from pathlib import Path

import wenyan

路徑 = Path("wenyan.wy")
原文 = 路徑.read_text(encoding="utf-8")

關鍵詞 = ["吾有", "今有", "名之曰", "施", "乃得", "若", "凡", "書之"]
文本統計 = {
    "lines": 原文.count("\n") + (1 if 原文 else 0),
    "bytes": len(原文.encode("utf-8")),
    "sentences": 原文.count("。"),
    "keywords": {詞: 原文.count(詞) for 詞 in 關鍵詞},
}

樹 = wenyan.編譯為PythonAST(原文, str(路徑))
節點數 = sum(1 for _ in ast.walk(樹))
分支型別 = (ast.If, ast.For, ast.AsyncFor, ast.While, ast.Try, ast.IfExp)
分支數 = sum(isinstance(n, 分支型別) for n in ast.walk(樹))


def 最大深度(node, depth=0):
    子節點 = list(ast.iter_child_nodes(node))
    if not 子節點:
        return depth
    return max(最大深度(ch, depth + 1) for ch in 子節點)

print(
    {
        **文本統計,
        "ast_nodes": 節點數,
        "ast_branches": 分支數,
        "ast_max_depth": 最大深度(樹),
    }
)
```

## Decision Rules

- Optimize for multi-metric simplification, not line-count-only wins.
- Keep semantics equivalent unless explicitly asked to change behavior.
- For `wenyan.wy`, require dual-engine bootstrap validation before claiming success.
- Keep edits minimal and reversible.
- Prefer clarity over dense compression.

## Output Checklist

- Report baseline and final metrics: lines, bytes, sentence count, touched-keyword counts, ast_nodes, ast_branches, ast_max_depth.
- Report net deltas and readability/maintainability judgment.
- Report validation results: bootstrap tests, impacted unittest suite, and parity checks if run.
- If no true simplification is achieved, provide failure analysis and next strategy.
