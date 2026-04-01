#!/usr/bin/env python3
"""Validate repository-local Codex and Claude plugin metadata."""

from __future__ import annotations

import difflib
import json
import sys
from pathlib import Path
from typing import Any

from generate_claude_marketplace import build_marketplace


REPO_ROOT = Path(__file__).resolve().parent.parent


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise SystemExit(f"Missing required file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid JSON in {path}: {exc}") from exc


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
    if not isinstance(skills_rel, str) or not skills_rel:
        errors.append(f"{repo_label(path)} is missing a string 'skills' path.")
    else:
        skills_path = (plugin_root / skills_rel).resolve()
        if not skills_path.exists():
            errors.append(
                f"{repo_label(path)} points to a missing skills path: {skills_rel}"
            )

    return manifest, errors


def validate_codex_metadata(repo_root: Path) -> list[str]:
    plugin_manifest_path = repo_root / ".codex-plugin" / "plugin.json"
    runtime_plugin_manifest_path = (
        repo_root / "plugins" / "skills" / ".codex-plugin" / "plugin.json"
    )
    marketplace_path = repo_root / ".agents" / "plugins" / "marketplace.json"
    plugin_manifest, errors = validate_plugin_manifest(plugin_manifest_path)
    runtime_plugin_manifest, runtime_errors = validate_plugin_manifest(
        runtime_plugin_manifest_path
    )
    marketplace = load_json(marketplace_path)

    errors.extend(runtime_errors)

    if plugin_manifest != runtime_plugin_manifest:
        diff = "\n".join(
            difflib.unified_diff(
                canonical_json(plugin_manifest).splitlines(),
                canonical_json(runtime_plugin_manifest).splitlines(),
                fromfile=repo_label(plugin_manifest_path),
                tofile=repo_label(runtime_plugin_manifest_path),
                lineterm="",
            )
        )
        errors.append(
            f"{repo_label(runtime_plugin_manifest_path)} is out of sync with "
            f"{repo_label(plugin_manifest_path)}.\n{diff}"
        )

    plugin_name = plugin_manifest.get("name")
    runtime_plugin_name = runtime_plugin_manifest.get("name")
    if (
        not isinstance(plugin_name, str)
        or not plugin_name
        or not isinstance(runtime_plugin_name, str)
        or not runtime_plugin_name
    ):
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

        if plugin_root_candidate == repo_root.resolve():
            errors.append(
                f"{repo_label(marketplace_path)} plugin entry {index} resolves to the "
                "repository root. Codex rejects empty local source paths such as './'."
            )
            continue

        candidate_manifest = plugin_root_candidate / ".codex-plugin" / "plugin.json"
        if candidate_manifest.resolve() == runtime_plugin_manifest_path.resolve():
            matching_entries.append((index, entry, plugin_root_candidate))
        elif isinstance(rel_path, str) and rel_path.strip() in {".", "./"}:
            errors.append(
                f"{repo_label(marketplace_path)} plugin entry {index} uses an empty "
                f"local source path: {rel_path!r}."
            )

    if not matching_entries:
        errors.append(
            f"{repo_label(marketplace_path)} does not contain a plugin entry that resolves "
            f"to {repo_label(runtime_plugin_manifest_path)}."
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
    if entry_name != runtime_plugin_name:
        errors.append(
            f"{repo_label(marketplace_path)} plugin entry {index} is named "
            f"{entry_name!r}, expected {runtime_plugin_name!r}."
        )

    source = entry.get("source")
    if not isinstance(source, dict) or source.get("source") != "local":
        errors.append(
            f"{repo_label(marketplace_path)} plugin entry {index} must use "
            f"'source.source': 'local'."
        )
    elif resolve_plugin_root(repo_root, entry) == repo_root.resolve():
        errors.append(
            f"{repo_label(marketplace_path)} plugin entry {index} must use a non-root "
            "local source path."
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


def validate_claude_metadata(repo_root: Path) -> list[str]:
    marketplace_path = repo_root / ".claude-plugin" / "marketplace.json"
    actual_marketplace = load_json(marketplace_path)
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


def main() -> int:
    errors = [
        *validate_codex_metadata(REPO_ROOT),
        *validate_claude_metadata(REPO_ROOT),
    ]
    if errors:
        print("Plugin metadata validation failed.\n", file=sys.stderr)
        for error in errors:
            print(error, file=sys.stderr)
            print(file=sys.stderr)
        return 1

    claude_marketplace = build_marketplace(REPO_ROOT / "skills")
    print(
        "Plugin metadata validation passed: "
        f"1 Codex plugin entry and {len(claude_marketplace['plugins'])} Claude entries."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
