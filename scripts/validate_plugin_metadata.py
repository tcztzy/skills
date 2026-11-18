#!/usr/bin/env python3
"""Validate repository-local Codex and Claude plugin metadata."""

from __future__ import annotations

import argparse
import difflib
import json
import re
import sys
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlsplit

from generate_claude_marketplace import build_marketplace, distribution_files


REPO_ROOT = Path(__file__).resolve().parent.parent


def load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise SystemExit(f"Missing required file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid JSON in {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"{repo_label(path)} must contain a JSON object.")
    return data


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2) + "\n"


def repo_label(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def resolve_plugin_root(repo_root: Path, marketplace_entry: dict[str, Any]) -> Path | None:
    source = marketplace_entry.get("source")
    if not isinstance(source, dict):
        return None

    rel_path = source.get("path")
    if not isinstance(rel_path, str) or not rel_path:
        return None

    return (repo_root / rel_path).resolve()


def validate_plugin_manifest(path: Path) -> tuple[dict[str, Any], list[str]]:
    manifest = load_json(path)
    errors: list[str] = []

    plugin_name = manifest.get("name")
    if not isinstance(plugin_name, str) or not plugin_name:
        errors.append(f"{repo_label(path)} is missing a string 'name'.")
        return manifest, errors

    plugin_root = path.parent.parent
    skills_rel = manifest.get("skills")
    if not isinstance(skills_rel, str) or Path(skills_rel) != Path("skills"):
        errors.append(f"{repo_label(path)} must point 'skills' at ./skills/.")
    elif not (plugin_root / "skills").is_dir() or (plugin_root / "skills").is_symlink():
        errors.append(f"{repo_label(path)} must point at the bundled skills directory.")

    return manifest, errors


def validate_codex_metadata(repo_root: Path) -> list[str]:
    plugin_manifest_path = repo_root / ".codex-plugin" / "plugin.json"
    marketplace_path = repo_root / ".agents" / "plugins" / "marketplace.json"
    plugin_manifest, errors = validate_plugin_manifest(plugin_manifest_path)
    marketplace = load_json(marketplace_path)
    plugin_name = plugin_manifest.get("name")
    if not isinstance(plugin_name, str) or not plugin_name:
        return errors

    plugins = marketplace.get("plugins")
    if not isinstance(plugins, list) or not plugins:
        errors.append(f"{repo_label(marketplace_path)} has no plugin entries.")
        return errors

    matching_entries: list[tuple[int, dict[str, Any], Path]] = []
    for index, entry in enumerate(plugins):
        if not isinstance(entry, dict):
            continue

        source = entry.get("source")
        rel_path = source.get("path") if isinstance(source, dict) else None
        plugin_root_candidate = resolve_plugin_root(repo_root, entry)
        if plugin_root_candidate is None:
            continue

        candidate_manifest = plugin_root_candidate / ".codex-plugin" / "plugin.json"
        if candidate_manifest.resolve() == plugin_manifest_path.resolve():
            matching_entries.append((index, entry, plugin_root_candidate))
        elif isinstance(rel_path, str) and rel_path.strip() in {".", "./"}:
            errors.append(
                f"{repo_label(marketplace_path)} plugin entry {index} resolves to "
                f"{repo_label(plugin_root_candidate)}, but its manifest does not match "
                f"{repo_label(plugin_manifest_path)}."
            )

    if not matching_entries:
        errors.append(
            f"{repo_label(marketplace_path)} does not contain a plugin entry that resolves "
            f"to {repo_label(plugin_manifest_path)}."
        )
        return errors

    if len(matching_entries) > 1:
        indexes = ", ".join(str(index) for index, _, _ in matching_entries)
        errors.append(
            f"{repo_label(marketplace_path)} contains multiple entries for the repo plugin "
            f"at indexes: {indexes}."
        )

    index, entry, _ = matching_entries[0]
    entry_name = entry.get("name")
    if entry_name != plugin_name:
        errors.append(
            f"{repo_label(marketplace_path)} plugin entry {index} is named "
            f"{entry_name!r}, expected {plugin_name!r}."
        )

    source = entry.get("source")
    if not isinstance(source, dict) or source.get("source") != "local":
        errors.append(
            f"{repo_label(marketplace_path)} plugin entry {index} must use "
            f"'source.source': 'local'."
        )
    elif resolve_plugin_root(repo_root, entry) != repo_root.resolve():
        errors.append(
            f"{repo_label(marketplace_path)} plugin entry {index} must resolve to the "
            f"repository root so Codex loads {repo_label(plugin_manifest_path)}."
        )

    rel_path = source.get("path")
    if not isinstance(rel_path, str) or rel_path.strip() not in {".", "./"}:
        errors.append(
            f"{repo_label(marketplace_path)} plugin entry {index} must use "
            "'source.path' as '.' or './'."
        )

    policy = entry.get("policy")
    if not isinstance(policy, dict):
        errors.append(
            f"{repo_label(marketplace_path)} plugin entry {index} is missing 'policy'."
        )
    else:
        for field in ("installation", "authentication"):
            if field not in policy:
                errors.append(
                    f"{repo_label(marketplace_path)} plugin entry {index} is missing "
                    f"'policy.{field}'."
                )

    if "category" not in entry:
        errors.append(
            f"{repo_label(marketplace_path)} plugin entry {index} is missing 'category'."
        )

    return errors


def validate_claude_metadata(repo_root: Path, expected_marketplace: dict[str, Any] | None = None) -> list[str]:
    marketplace_path = repo_root / ".claude-plugin" / "marketplace.json"
    actual_marketplace = load_json(marketplace_path)
    if expected_marketplace is None:
        expected_marketplace = build_marketplace(repo_root / "skills")

    if actual_marketplace == expected_marketplace:
        return []

    diff = "\n".join(
        difflib.unified_diff(
            canonical_json(actual_marketplace).splitlines(),
            canonical_json(expected_marketplace).splitlines(),
            fromfile=repo_label(marketplace_path),
            tofile=f"generated/{repo_label(marketplace_path)}",
            lineterm="",
        )
    )
    return [
        f"{repo_label(marketplace_path)} is out of date with current skills metadata.\n"
        f"{diff}"
    ]


def published_docs(files: set[Path]) -> list[Path]:
    """Only public skill documentation and the repository's user-facing index."""
    skills = {p.parent for p in files if p.match("skills/*/SKILL.md") and len(p.parts) == 3}
    return sorted(p for p in files if p == Path("README.md") or
                  (p.suffix.lower() == ".md" and any(parent in skills for parent in p.parents)))


INLINE_LINK = re.compile(r"""\]\(\s*(?:<([^>\n]+)>|([^()\s]+))(?:\s+["'][^)]*["'])?\s*\)""")


def validate_doc_links(repo_root: Path, files: set[Path]) -> list[str]:
    """Check ordinary local Markdown links against files in the distribution."""
    directories = {parent for path in files for parent in path.parents}
    root = repo_root.resolve()
    errors = []
    for doc in published_docs(files):
        fence = ""
        for number, line in enumerate((root / doc).read_text(encoding="utf-8").splitlines(), 1):
            marker = re.match(r"^ {0,3}(`{3,}|~{3,})", line)
            if marker:
                if not fence:
                    fence = marker[1]
                elif marker[1].startswith(fence) and not line[marker.end():].strip():
                    fence = ""
                continue
            if fence:
                continue
            for link in INLINE_LINK.finditer(line):
                target = link[1] or link[2]
                url = urlsplit(target)
                if url.netloc or url.scheme or not url.path:
                    continue
                path = (root / doc.parent / unquote(url.path)).resolve()
                relative = path.relative_to(root) if path.is_relative_to(root) else None
                if relative not in files and relative not in directories:
                    errors.append(f"{doc.as_posix()}:{number}: unpublished or missing link: {target}")
    return errors


def validate_retired_skills(repo_root: Path, retired: set[str]) -> list[str]:
    """Check removed names in explicit skill invocations and routing instructions."""
    if not retired:
        return []
    files = distribution_files(repo_root)
    names = "|".join(re.escape(name) for name in sorted(retired))
    # Ordinary commands can share a retired name. Treat a bare code span as a
    # skill only in routing prose; explicit $skill and skills/name paths stand alone.
    mentions = re.compile(
        rf"(?<![\w$])\$(?:{names})(?![\w-])|"
        rf"(?<![\w-])skills/(?:{names})(?=[/`\s)\]]|$)|"
        rf"(?:\b(?:route|delegate|hand off)\b[^.\n]{{0,90}}|\b(?:use|invoke|load)\s+|"
        rf"\b(?:skill|handoff)\s+|\bto\s+)`(?:{names})`",
        re.IGNORECASE,
    )
    errors = []
    for doc in published_docs(files):
        content = (repo_root / doc).read_text(encoding="utf-8")
        for match in mentions.finditer(content):
            line = content.count("\n", 0, match.start()) + 1
            mention = " ".join(match[0].split())
            errors.append(f"{doc.as_posix()}:{line}: retired skill reference: {mention}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--retired", action="append", default=[], metavar="NAME",
                        help="Check for callers of a renamed or retired skill (repeatable)")
    args = parser.parse_args()
    retired = set(args.retired)
    try:
        marketplace = build_marketplace(REPO_ROOT / "skills")
        active_names = {plugin["name"] for plugin in marketplace["plugins"]}
        errors = [
            *validate_codex_metadata(REPO_ROOT),
            *validate_claude_metadata(REPO_ROOT, marketplace),
            *validate_doc_links(REPO_ROOT, distribution_files(REPO_ROOT)),
            *validate_retired_skills(REPO_ROOT, retired),
        ]
        if retired & active_names:
            errors.append(f"Retired names are still published: {', '.join(sorted(retired & active_names))}")
    except (OSError, ValueError) as exc:
        errors = [str(exc)]
    if errors:
        print("Plugin metadata validation failed.\n", file=sys.stderr)
        for error in errors:
            print(error, file=sys.stderr)
            print(file=sys.stderr)
        return 1

    print(
        "Plugin metadata validation passed: "
        f"1 Codex plugin entry and {len(marketplace['plugins'])} Claude entries."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
