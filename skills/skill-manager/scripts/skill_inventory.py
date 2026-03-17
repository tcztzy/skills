#!/usr/bin/env python3
"""Inventory helpers for installed top-level and vendored skills."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any


_KEY_RE = re.compile(r"^([A-Za-z0-9_-]+):(?:\s+(.*)|\s*)$")


def _unquote_yaml_scalar(value: str) -> str:
    raw = value.strip()
    if len(raw) >= 2 and raw[0] == raw[-1] and raw[0] in ("'", '"'):
        quote = raw[0]
        inner = raw[1:-1]
        if quote == "'":
            return inner.replace("''", "'")
        inner = inner.replace('\\"', '"').replace("\\\\", "\\")
        inner = inner.replace("\\n", "\n").replace("\\t", "\t").replace("\\r", "\r")
        return inner
    return raw


def _parse_frontmatter(skill_md: Path) -> dict[str, str]:
    content = skill_md.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n")
    if not content.startswith("---\n"):
        return {}
    match = re.match(r"^---\n(.*?)\n---\n?", content, re.DOTALL)
    if not match:
        return {}

    front = match.group(1)
    parsed: dict[str, str] = {}
    for line in front.split("\n"):
        if not line or line.startswith((" ", "\t")):
            continue
        key_match = _KEY_RE.match(line)
        if not key_match:
            continue
        parsed[key_match.group(1)] = _unquote_yaml_scalar((key_match.group(2) or "").rstrip())
    return parsed


def _skill_name_for(path: Path) -> str:
    parsed = _parse_frontmatter(path / "SKILL.md")
    return parsed.get("name") or path.name


def discover_skills(skills_root: str | Path, _workspace_root: str | Path | None = None) -> list[dict[str, Any]]:
    root = Path(skills_root).expanduser().resolve()
    discovered: list[dict[str, Any]] = []
    if not root.is_dir():
        return discovered

    for top_level in sorted(root.iterdir()):
        if not top_level.is_dir() or top_level.name.startswith(".") or top_level.name == "_backup":
            continue
        if not (top_level / "SKILL.md").exists():
            continue

        discovered.append(
            {
                "skill_name": _skill_name_for(top_level),
                "skill_path": str(top_level),
                "skill_kind": "top_level",
                "entry_type": "leaf_skill",
            }
        )

        vendor_root = top_level / "vendor"
        if not vendor_root.is_dir():
            continue

        for vendor_source in sorted(vendor_root.iterdir()):
            if not vendor_source.is_dir():
                continue
            for vendored in sorted(vendor_source.iterdir()):
                if not vendored.is_dir() or not (vendored / "SKILL.md").exists():
                    continue
                discovered.append(
                    {
                        "skill_name": _skill_name_for(vendored),
                        "skill_path": str(vendored),
                        "skill_kind": "vendored",
                        "entry_type": "leaf_skill",
                        "suite_name": top_level.name,
                        "vendor_source": vendor_source.name,
                    }
                )
    return discovered
