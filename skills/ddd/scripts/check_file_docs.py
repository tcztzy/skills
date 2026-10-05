#!/usr/bin/env python3
"""Audit source trees for language-native file-level documentation.

Role:
    Provide a cheap structural baseline for Documentation-Driven Development.
Flow:
    Paths -> supported source files -> header parser -> text or JSON report.
Side effects:
    Reads source files and writes reports to stdout and input errors to stderr;
    never edits targets. Exit codes: 0 for no failures, 1 for failed headers,
    2 for invalid inputs or no supported source files.
Limits:
    Checks leading documentation markers and summary length, not language
    validity or semantic accuracy. Python is parsed in full with the host AST.
"""

from __future__ import annotations

import argparse
import ast
from dataclasses import asdict, dataclass
import json
from pathlib import Path
import re
import sys
from typing import Iterable, Sequence


LANGUAGES = {
    ".py": "python",
    ".pyi": "python",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".mts": "typescript",
    ".cts": "typescript",
    ".c": "c",
    ".h": "c-cpp",
    ".cc": "cpp",
    ".cp": "cpp",
    ".cpp": "cpp",
    ".cxx": "cpp",
    ".hh": "cpp",
    ".hpp": "cpp",
    ".hxx": "cpp",
    ".ixx": "cpp",
    ".rs": "rust",
}

EXCLUDED_DIRECTORIES = {
    ".git",
    ".hg",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".tox",
    ".venv",
    "build",
    "coverage",
    "dist",
    "node_modules",
    "target",
    "vendor",
    "vendors",
}

GENERATED_PATTERN = re.compile(
    r"\b(?:auto[- ]?generated|generated (?:file|code)|do not edit)\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class Result:
    """Represent one source file's structural documentation status."""

    path: str
    language: str
    status: str
    summary: str = ""
    reason: str = ""


def _first_nonempty_line(text: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped
    return ""


def _clean_comment_line(line: str) -> str:
    cleaned = re.sub(r"^\s*(?:/\*+!?|\*+/?|//!|///|//)\s?", "", line)
    return cleaned.strip()


def _comment_summary(block: str) -> str:
    block = re.sub(r"\*/\s*$", "", block)
    brief = re.search(r"(?:@|\\)brief\s+(.+)", block)
    if brief:
        return brief.group(1).strip()

    for line in block.splitlines():
        cleaned = _clean_comment_line(line)
        if not cleaned or cleaned.startswith(("@", "\\", "#")):
            continue
        return cleaned
    return ""


def _leading_comments(prefix: str, language: str) -> list[str]:
    """Collect comments before code, allowing shebangs and common directives."""

    if prefix.startswith("#!") and not prefix.startswith("#!["):
        prefix = prefix.partition("\n")[2]
    parts = [r"\s+", r"//[^\n]*", r"/\*[\s\S]*?\*/"]
    if language in {"c", "c-cpp", "cpp"}:
        parts.append(r"#(?:\\\n|[^\n])*(?:\n|$)")
    elif language == "rust":
        parts.append(r"#!\[[^\]\n]*\]")
    token = re.compile("|".join(parts))
    comments = []
    position = 0
    while match := token.match(prefix, position):
        if match.group().startswith(("//", "/*")):
            comments.append(match.group())
        position = match.end()
    return comments


def _read_text(path: Path) -> tuple[str | None, str | None]:
    try:
        return path.read_text(encoding="utf-8-sig"), None
    except UnicodeDecodeError:
        return None, "not UTF-8 text"
    except OSError as error:
        return None, f"cannot read: {error}"


def _check_python(path: Path, text: str, min_summary: int, max_lines: int) -> Result:
    try:
        tree = ast.parse(text, filename=str(path))
    except SyntaxError as error:
        return Result(str(path), "python", "fail", reason=f"syntax error: {error.msg}")

    docstring = ast.get_docstring(tree, clean=False)
    if not docstring:
        return Result(str(path), "python", "fail", reason="missing module docstring")
    if tree.body and tree.body[0].lineno > max_lines:
        return Result(
            str(path),
            "python",
            "fail",
            reason=f"module docstring begins after line {max_lines}",
        )
    summary = _first_nonempty_line(docstring)
    if len(summary) < min_summary:
        return Result(
            str(path),
            "python",
            "fail",
            summary,
            f"summary shorter than {min_summary} characters",
        )
    return Result(str(path), "python", "pass", summary)


def _check_typescript(path: Path, comments: list[str], min_summary: int) -> Result:
    blocks = [comment for comment in comments if comment.startswith("/**")]
    marked = [
        block
        for block in blocks
        if re.search(r"@(module|packageDocumentation)\b", block)
    ]
    if not marked:
        return Result(
            str(path),
            "typescript",
            "fail",
            reason="missing leading @module or @packageDocumentation block",
        )
    if marked[0] != blocks[0]:
        return Result(
            str(path),
            "typescript",
            "fail",
            reason="file documentation is not the first /** documentation block",
        )
    summary = _comment_summary(marked[0])
    if len(summary) < min_summary:
        return Result(
            str(path),
            "typescript",
            "fail",
            summary,
            f"summary shorter than {min_summary} characters",
        )
    return Result(str(path), "typescript", "pass", summary)


def _check_c_family(
    path: Path,
    language: str,
    comments: list[str],
    min_summary: int,
    c_style: str,
) -> Result:
    blocks = [comment for comment in comments if comment.startswith("/*")]
    if c_style == "kernel-doc":
        file_blocks = [block for block in blocks if re.search(r"\bFile role:", block)]
        missing_reason = "missing leading kernel-style block with File role:"
    else:
        file_blocks = [
            block
            for block in blocks
            if block.startswith(("/**", "/*!"))
            and re.search(r"(?:@|\\)file\b", block)
        ]
        missing_reason = "missing leading Doxygen @file block"
    if not file_blocks:
        return Result(
            str(path),
            language,
            "fail",
            reason=missing_reason,
        )
    summary = _comment_summary(file_blocks[0])
    if len(summary) < min_summary:
        return Result(
            str(path),
            language,
            "fail",
            summary,
            f"summary shorter than {min_summary} characters",
        )
    return Result(str(path), language, "pass", summary)


def _check_rust(path: Path, comments: list[str], min_summary: int) -> Result:
    docs = [comment for comment in comments if comment.startswith(("//!", "/*!"))]
    if not docs:
        return Result(
            str(path),
            "rust",
            "fail",
            reason="missing leading inner module documentation (//! or /*! */)",
        )
    summary = _comment_summary("\n".join(doc.removesuffix("*/") for doc in docs))
    if len(summary) < min_summary:
        return Result(
            str(path),
            "rust",
            "fail",
            summary,
            f"summary shorter than {min_summary} characters",
        )
    return Result(str(path), "rust", "pass", summary)


def check_file(
    path: Path,
    *,
    max_lines: int,
    min_summary: int,
    include_generated: bool,
    c_style: str,
) -> Result:
    """Check one supported source file for a language-native file contract."""

    language = LANGUAGES[path.suffix.lower()]
    text, error = _read_text(path)
    if error or text is None:
        return Result(str(path), language, "fail", reason=error or "cannot read")

    first_lines = "\n".join(text.splitlines()[:max_lines])
    if not include_generated and GENERATED_PATTERN.search("\n".join(text.splitlines()[:8])):
        return Result(str(path), language, "skip", reason="generated file")

    if language == "python":
        return _check_python(path, text, min_summary, max_lines)
    comments = _leading_comments(first_lines, language)
    if language == "typescript":
        return _check_typescript(path, comments, min_summary)
    if language in {"c", "c-cpp", "cpp"}:
        return _check_c_family(path, language, comments, min_summary, c_style)
    return _check_rust(path, comments, min_summary)


def _is_excluded(path: Path) -> bool:
    return any(part in EXCLUDED_DIRECTORIES for part in path.parts)


def _iter_source_files(paths: Iterable[Path]) -> Iterable[Path]:
    seen: set[Path] = set()
    for supplied in paths:
        if supplied.is_file():
            candidates = [supplied]
        elif supplied.is_dir():
            candidates = supplied.rglob("*")
        else:
            continue

        for candidate in candidates:
            if (
                not candidate.is_file()
                or candidate.is_symlink()
                or candidate.suffix.lower() not in LANGUAGES
                or _is_excluded(candidate)
            ):
                continue
            resolved = candidate.resolve()
            if resolved not in seen:
                seen.add(resolved)
                yield candidate


def _parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit language-native file documentation near source-file starts."
    )
    parser.add_argument("paths", nargs="+", type=Path, help="Files or directories to scan")
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Report format (default: text)",
    )
    parser.add_argument(
        "--max-lines",
        type=int,
        default=80,
        help="Header prefix limit; Python docstrings must start within it (default: 80)",
    )
    parser.add_argument(
        "--min-summary-chars",
        type=int,
        default=20,
        help="Minimum trimmed summary length in characters (default: 20)",
    )
    parser.add_argument(
        "--include-generated",
        action="store_true",
        help="Check files marked generated instead of skipping them",
    )
    parser.add_argument(
        "--c-style",
        choices=("doxygen", "kernel-doc"),
        default="doxygen",
        help="File-header convention for C/C++ inputs (default: doxygen)",
    )
    args = parser.parse_args(argv)
    if args.max_lines < 1:
        parser.error("--max-lines must be positive")
    if args.min_summary_chars < 1:
        parser.error("--min-summary-chars must be positive")
    for path in args.paths:
        if not path.is_file() and not path.is_dir():
            parser.error(f"input is not a file or directory: {path}")
    return args


def main(argv: Sequence[str] | None = None) -> int:
    """Run the audit and return nonzero when a checked file fails."""

    args = _parse_args(sys.argv[1:] if argv is None else argv)
    files = sorted(_iter_source_files(args.paths), key=lambda item: str(item))
    if not files:
        message = "No supported source files found."
        if args.format == "json":
            print(json.dumps({"error": message, "results": [], "summary": {"checked": 0}}))
        else:
            print(message, file=sys.stderr)
        return 2
    results = [
        check_file(
            path,
            max_lines=args.max_lines,
            min_summary=args.min_summary_chars,
            include_generated=args.include_generated,
            c_style=args.c_style,
        )
        for path in files
    ]

    counts = {
        status: sum(result.status == status for result in results)
        for status in ("pass", "fail", "skip")
    }
    if args.format == "json":
        payload = {
            "summary": {"checked": len(results), **counts},
            "results": [asdict(result) for result in results],
        }
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        for result in results:
            detail = result.summary if result.status == "pass" else result.reason
            print(f"{result.status.upper():4} {result.path}: {detail}")
        print(
            f"Checked {len(results)} files: {counts['pass']} passed, "
            f"{counts['fail']} failed, {counts['skip']} skipped."
        )

    return 1 if counts["fail"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
