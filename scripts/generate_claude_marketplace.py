#!/usr/bin/env python3
"""Generate Claude metadata from distributable local skills and pinned remote entries."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path, PurePosixPath
from typing import Any


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills/skill-manager/scripts"))
from validate_skill import ValidateError, read_skill_metadata


MARKETPLACE_NAME = "blackscience-tech-skills"
MARKETPLACE_DESCRIPTION = (
    "Research, evaluation, developer tooling, and document workflow skills."
)
OWNER = {
    "name": "Tang Ziya",
    "email": "tcztzy@gmail.com",
}


def summarize_description(description: str) -> str:
    for marker in (". Use when", "。Use when", ". use when"):
        if marker in description:
            head, _ = description.split(marker, 1)
            return head.strip() + "."
    return description


def distribution_files(root: Path) -> set[Path]:
    """List files shipped from a checkout or present in a clean unpacked source archive."""
    if (root / ".git").exists():
        try:
            listing = subprocess.check_output(
                ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"], cwd=root
            )
        except (OSError, subprocess.CalledProcessError) as exc:
            raise ValueError(f"Cannot read the Git inventory in {root}: {exc}") from exc
        candidates = (Path(os.fsdecode(name)) for name in listing.split(b"\0") if name)
    else:
        # Packaged source already contains the publisher's chosen files. Do not
        # follow private skill mounts or directories outside the archive.
        candidates = (
            (Path(directory) / name).relative_to(root)
            for directory, _, names in os.walk(root, followlinks=False)
            for name in names
        )
    return {path for path in candidates if (root / path).is_file() and not (root / path).is_symlink()}


def collect_plugins(skills_root: Path) -> list[dict[str, Any]]:
    skills_root = skills_root.resolve()
    if not skills_root.is_dir():
        raise ValueError(f"Missing skills directory: {skills_root}")
    root = skills_root.parent
    plugins: list[dict[str, Any]] = []
    for path in sorted(distribution_files(root)):
        if len(path.parts) != 3 or path.parts[0] != skills_root.name or path.name != "SKILL.md":
            continue
        if path.parts[1].startswith("."):
            continue
        skill_file = root / path
        try:
            meta = read_skill_metadata(skill_file)
        except ValidateError as exc:
            raise ValueError(f"{path.as_posix()}: {exc}") from exc
        skill_dir = skill_file.parent
        plugins.append(
            {
                "name": meta["name"],
                "description": summarize_description(" ".join(meta["description"].split())),
                "source": "./",
                "strict": False,
                "skills": [f"./skills/{skill_dir.name}"],
            }
        )
    return plugins


def read_external_plugins(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    entries = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(entries, list):
        raise ValueError(f"{path}: expected a list of external plugins")
    for index, entry in enumerate(entries):
        label = f"{path} entry {index + 1}"
        if not isinstance(entry, dict) or not isinstance(entry.get("name"), str) or not entry["name"]:
            raise ValueError(f"{label}: missing plugin name")
        source = entry.get("source")
        if not isinstance(source, dict) or not re.fullmatch(r"[0-9a-fA-F]{40}", str(source.get("sha", ""))):
            raise ValueError(f"{label}: pin the external Git source with a full 40-digit commit SHA")
        remote_key = {"github": "repo", "url": "url"}.get(str(source.get("source", "")))
        if not remote_key or not isinstance(source.get(remote_key), str) or not source[remote_key].strip():
            raise ValueError(f"{label}: expected a GitHub repository or Git URL source")
        paths = entry.get("skills")
        if not isinstance(paths, list) or not paths or any(
            not isinstance(item, str) or not item.startswith("./") or ".." in PurePosixPath(item).parts
            or "\\" in item for item in paths
        ):
            raise ValueError(f"{label}: skills must contain relative paths inside the pinned repository")
    return entries


def build_marketplace(skills_root: Path) -> dict[str, Any]:
    plugins = collect_plugins(skills_root)
    external_path = skills_root.parent / ".claude-plugin" / "external-plugins.json"
    plugins.extend(read_external_plugins(external_path))
    names = [plugin["name"] for plugin in plugins]
    if len(names) != len(set(names)):
        raise ValueError("Local and external marketplace plugin names must be unique")
    return {
        "$schema": "https://anthropic.com/claude-code/marketplace.schema.json",
        "name": MARKETPLACE_NAME,
        "description": MARKETPLACE_DESCRIPTION,
        "owner": OWNER,
        "metadata": {
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

    try:
        marketplace = build_marketplace(args.skills_root)
    except (OSError, ValueError) as exc:
        parser.exit(1, f"Marketplace generation failed: {exc}\n")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes((json.dumps(marketplace, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    print(
        f"Wrote {args.output} with {len(marketplace['plugins'])} plugin entries.",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
