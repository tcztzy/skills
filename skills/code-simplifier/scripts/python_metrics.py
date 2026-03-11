#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///

from __future__ import annotations

import argparse
import ast
import io
import json
import tokenize
from pathlib import Path
from typing import Any

_BRANCH_TYPES = (
    ast.If,
    ast.For,
    ast.AsyncFor,
    ast.While,
    ast.Try,
    ast.Match,
    ast.IfExp,
)


def _max_depth(node: ast.AST, depth: int = 0) -> int:
    children = list(ast.iter_child_nodes(node))
    if not children:
        return depth
    return max(_max_depth(child, depth + 1) for child in children)


def _python_file_metrics(path: Path) -> dict[str, Any]:
    raw = path.read_bytes()
    line_count = raw.count(b"\n")  # matches `wc -l`

    with tokenize.open(path) as handle:
        src = handle.read()

    tokens = sum(
        1
        for tok in tokenize.generate_tokens(io.StringIO(src).readline)
        if tok.type
        not in {
            tokenize.ENCODING,
            tokenize.NL,
            tokenize.NEWLINE,
            tokenize.ENDMARKER,
        }
    )

    tree = ast.parse(src, filename=str(path))
    nodes = sum(1 for _ in ast.walk(tree))
    branches = sum(isinstance(n, _BRANCH_TYPES) for n in ast.walk(tree))

    return {
        "path": str(path),
        "bytes": len(raw),
        "lines": line_count,
        "tokens": tokens,
        "ast_nodes": nodes,
        "ast_branches": branches,
        "ast_max_depth": _max_depth(tree),
    }


def _iter_py_files(path: Path) -> list[Path]:
    if path.is_file():
        return [path]
    return sorted(p for p in path.rglob("*.py") if p.is_file())


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Compute formatter-aligned size and AST complexity metrics for Python source files.",
    )
    parser.add_argument("paths", nargs="+", help="File and/or directory paths")
    args = parser.parse_args()

    files: list[Path] = []
    for raw_path in args.paths:
        files.extend(_iter_py_files(Path(raw_path)))

    metrics = [_python_file_metrics(path) for path in files]
    total = {
        "files": len(metrics),
        "bytes": sum(m["bytes"] for m in metrics),
        "lines": sum(m["lines"] for m in metrics),
        "tokens": sum(m["tokens"] for m in metrics),
        "ast_nodes": sum(m["ast_nodes"] for m in metrics),
        "ast_branches": sum(m["ast_branches"] for m in metrics),
        "ast_max_depth": max((m["ast_max_depth"] for m in metrics), default=0),
    }

    print(json.dumps({"files": metrics, "total": total}, indent=2, sort_keys=True))
    return 0


raise SystemExit(main())
