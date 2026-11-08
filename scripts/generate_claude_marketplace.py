#!/usr/bin/env python3
"""Generate Claude metadata from distributable local skills and pinned remote entries."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any


MARKETPLACE_NAME = "blackscience-tech-skills"
MARKETPLACE_DESCRIPTION = (
    "Research, evaluation, developer tooling, and document workflow skills."
)
OWNER = {
    "name": "Tang Ziya",
    "email": "tcztzy@gmail.com",
}


def extract_frontmatter(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise ValueError(f"{path} is missing YAML frontmatter")

    try:
        raw_frontmatter = text.split("\n---\n", 1)[0].splitlines()[1:]
    except IndexError as exc:
        raise ValueError(f"{path} has an unterminated YAML frontmatter block") from exc

    fields: dict[str, str] = {}
    current_key: str | None = None
    for line in raw_frontmatter:
        if line and not line.startswith(" ") and ":" in line:
            key, value = line.split(":", 1)
            current_key = key.strip()
            fields[current_key] = value.strip()
            continue
        if current_key is not None:
            fields[current_key] = f"{fields[current_key]} {line.strip()}".strip()

    if "name" not in fields or "description" not in fields:
        raise ValueError(f"{path} frontmatter must include name and description")

    return {
        "name": unquote(fields["name"]),
        "description": one_line(unquote(fields["description"])),
    }


def unquote(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def one_line(value: str) -> str:
    return " ".join(value.split())


def summarize_description(description: str) -> str:
    for marker in (". Use when", "。Use when", ". use when"):
        if marker in description:
            head, _ = description.split(marker, 1)
            return head.strip() + "."
    return description


def collect_plugins(skills_root: Path) -> list[dict[str, Any]]:
    skill_paths = subprocess.check_output(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z", "--", "*/SKILL.md"],
        cwd=skills_root,
        text=True,
    )
    plugins: list[dict[str, Any]] = []
    for name in sorted(set(skill_paths.split("\0")) - {""}):
        relative_path = Path(name)
        if len(relative_path.parts) != 2 or relative_path.parts[0].startswith("."):
            continue
        skill_file = skills_root / relative_path
        if not skill_file.is_file():
            continue
        skill_dir = skill_file.parent

        meta = extract_frontmatter(skill_file)
        plugins.append(
            {
                "name": meta["name"],
                "description": summarize_description(meta["description"]),
                "source": "./",
                "strict": False,
                "skills": [f"./skills/{skill_dir.name}"],
            }
        )
    return plugins


def build_marketplace(skills_root: Path) -> dict[str, Any]:
    plugins = collect_plugins(skills_root)
    external_path = skills_root.parent / ".claude-plugin" / "external-plugins.json"
    if external_path.exists():
        plugins.extend(json.loads(external_path.read_text(encoding="utf-8")))
    names = [plugin["name"] for plugin in plugins]
    if len(names) != len(set(names)):
        raise ValueError("Local and external marketplace plugin names must be unique")
    return {
        "$schema": "https://anthropic.com/claude-code/marketplace.schema.json",
        "name": MARKETPLACE_NAME,
        "description": MARKETPLACE_DESCRIPTION,
        "owner": OWNER,
        "metadata": {
            "version": "1.0.0",
            "description": MARKETPLACE_DESCRIPTION,
        },
        "plugins": sorted(plugins, key=lambda plugin: plugin["name"]),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate Claude metadata from local skills and external-plugins.json"
    )
    parser.add_argument(
        "--skills-root",
        type=Path,
        default=Path("skills"),
        help="Root directory containing skill subdirectories",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(".claude-plugin/marketplace.json"),
        help="Output marketplace JSON path",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    marketplace = build_marketplace(args.skills_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(marketplace, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        f"Wrote {args.output} with {len(marketplace['plugins'])} plugin entries.",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
