#!/usr/bin/env python3
"""Create a pandoc-friendly LaTeX copy without modifying the source file."""

from __future__ import annotations

import argparse
import re
from collections import Counter
from collections.abc import Callable
from pathlib import Path


STANDARD_CLASSES = {"article", "book", "report"}
REMOVED_PACKAGES = {"enumitem", "tabularx"}


def _read_braced_argument(text: str, start: int) -> tuple[str, int] | None:
    """Read one balanced braced argument after optional whitespace."""
    cursor = start
    while cursor < len(text) and text[cursor].isspace():
        cursor += 1
    if cursor >= len(text) or text[cursor] != "{":
        return None
    depth = 0
    index = cursor
    while index < len(text):
        if text[index] == "\\":
            index += 2  # Escaped braces and percent signs are not delimiters.
            continue
        if text[index] == "%":
            newline = text.find("\n", index)
            if newline == -1:
                return None
            index = newline
        elif text[index] == "{":
            depth += 1
        elif text[index] == "}":
            depth -= 1
            if depth == 0:
                return text[cursor + 1 : index], index + 1
        index += 1
    return None


def _replace_tabularx(content: str, counts: Counter[str]) -> str:
    def replace(match: re.Match[str]) -> str:
        table = match.group(0)
        width = _read_braced_argument(table, len(r"\begin{tabularx}"))
        if width is None:
            return table
        position = re.match(r"\s*(\[[tbc]\])?", table[width[1] :])
        colspec = _read_braced_argument(table, width[1] + position.end())
        if colspec is None:
            return table
        # Leave complex column specifications intact for manual review.
        columns = re.findall(r"[CLRPpmb]\{[^{}]+\}|[|lcrXY\s]", colspec[0])
        if "".join(columns) != colspec[0]:
            return table
        simplified = "".join(
            {"C": "c", "L": "l", "R": "r", "P": "l"}[column[0]]
            if column[0] in "CLRP" else {"X": "l", "Y": "l"}.get(column, column)
            for column in columns
        )
        counts["tabularx"] += 1
        return (
            r"\begin{tabular}" + (position.group(1) or "") + "{" + simplified + "}"
            + table[colspec[1] : -len(r"\end{tabularx}")] + r"\end{tabular}"
        )

    return re.sub(r"\\begin\{tabularx\}.*?\\end\{tabularx\}", replace, content, flags=re.DOTALL)


def _unwrap_resizeboxes(content: str, counts: Counter[str]) -> str:
    cursor = 0
    while match := re.search(r"\\resizebox(?![A-Za-z])", content[cursor:]):
        start = cursor + match.start()
        width = _read_braced_argument(content, cursor + match.end())
        height = _read_braced_argument(content, width[1]) if width else None
        body = _read_braced_argument(content, height[1]) if height else None
        if body is None:
            cursor += match.end()
            continue
        content = content[:start] + body[0] + content[body[1] :]
        counts["resizebox"] += 1
        cursor = start
    return content


def _sub(
    pattern: str,
    replacement: str | Callable[[re.Match[str]], str],
    text: str,
    counts: Counter[str],
    label: str,
    *,
    flags: int = 0,
) -> str:
    updated, count = re.subn(pattern, replacement, text, flags=flags)
    counts[label] += count
    return updated


def preprocess(content: str) -> tuple[str, Counter[str]]:
    """Return transformed LaTeX and a count of applied rewrites."""
    counts: Counter[str] = Counter()

    def normalize_class(match: re.Match[str]) -> str:
        options = match.group(1) or ""
        document_class = match.group(2)
        if document_class in STANDARD_CLASSES:
            return match.group(0)
        counts["document_class"] += 1
        return rf"\documentclass{options}{{article}}"

    content = re.sub(
        r"\\documentclass(\[[^\]]*\])?\{([^}]+)\}",
        normalize_class,
        content,
    )
    # Keep custom definitions: line-based deletion corrupts multiline macros.
    content = _replace_tabularx(content, counts)
    content = _unwrap_resizeboxes(content, counts)
    content = _sub(
        r"\\path\{([^}]*)\}",
        r"\\texttt{\1}",
        content,
        counts,
        "path",
    )
    cursor = 0
    pattern = r"\\(?:setlist|captionsetup|hypersetup)(?![A-Za-z])(?:\[[^\]]*\])?"
    while match := re.search(pattern, content[cursor:]):
        start = cursor + match.start()
        argument = _read_braced_argument(content, cursor + match.end())
        if argument is None:
            cursor += match.end()
            continue
        content = content[:start] + content[argument[1] :]
        counts["formatting_config"] += 1
        cursor = start

    def remove_package(match: re.Match[str]) -> str:
        options = match.group(1) or ""
        packages = [item.strip() for item in match.group(2).split(",")]
        kept = [
            item for item in packages
            if item not in REMOVED_PACKAGES or (item == "tabularx" and r"\begin{tabularx}" in content)
        ]
        removed = len(packages) - len(kept)
        counts["package"] += removed
        return rf"\usepackage{options}{{{','.join(kept)}}}" if kept else ""

    content = re.sub(
        r"\\usepackage(\[[^\]]*\])?\{([^}]+)\}",
        remove_package,
        content,
    )
    content = _sub(
        r"\\begin\{enumerate\}\[[^\]]+\]",
        r"\\begin{enumerate}",
        content,
        counts,
        "enumerate_options",
    )
    content = _sub(
        r"\\cmidrule\([^)]*\)",
        r"\\cmidrule",
        content,
        counts,
        "cmidrule",
    )
    for command in (r"\allowbreak", r"\ignorespaces"):
        content = _sub(re.escape(command) + r"(?![A-Za-z])", "", content, counts, command[1:])
    content = _sub(
        r"^[ \t]*\\small[ \t]*(?:\n|$)",
        "",
        content,
        counts,
        "small",
        flags=re.MULTILINE,
    )
    content = _sub(
        r"\n{3,}",
        "\n\n",
        content,
        counts,
        "blank_lines",
    )
    return content, counts


def remaining_risks(content: str) -> list[str]:
    """Report constructs that may still require manual conversion review."""
    patterns = {
        "tabularx": r"\\(?:begin|end)\{tabularx\}",
        "resizebox": r"\\resizebox",
        "custom column definition": r"\\newcolumntype",
        "multirow": r"\\multirow",
        "makecell": r"\\makecell",
        "tabulary/supertabular": r"\\(?:begin|end)\{(?:tabulary|supertabular)\}",
    }
    return [label for label, pattern in patterns.items() if re.search(pattern, content)]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create a pandoc-friendly copy of a LaTeX source file."
    )
    parser.add_argument("source", type=Path, help="Source .tex file")
    parser.add_argument(
        "--output",
        type=Path,
        help="Output .tex path (default: SOURCE.pandoc.tex)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite an existing output file",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    source = args.source.expanduser().resolve()
    output = (
        args.output.expanduser().resolve()
        if args.output
        else source.with_name(f"{source.stem}.pandoc.tex")
    )

    if source.suffix.lower() != ".tex":
        raise SystemExit(f"source must be a .tex file: {source}")
    if not source.is_file():
        raise SystemExit(f"source does not exist: {source}")
    if output == source or (output.exists() and output.samefile(source)):
        raise SystemExit("output must differ from source")
    if output.exists() and not args.force:
        raise SystemExit(f"output exists; pass --force to replace it: {output}")

    content = source.read_text(encoding="utf-8")
    transformed, counts = preprocess(content)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(transformed, encoding="utf-8")

    print(f"output: {output}")
    print(f"rewrites: {sum(counts.values())}")
    for label, count in sorted(counts.items()):
        if count:
            print(f"  {label}: {count}")
    risks = remaining_risks(transformed)
    if risks:
        print("manual review: " + ", ".join(risks))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
