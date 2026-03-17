#!/usr/bin/env python3
"""Project enabled Claude skills into ~/.codex/skills as symlinks."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


MANIFEST_NAME = ".claude-enabled-skills.json"


@dataclass(frozen=True)
class SkillLink:
    name: str
    source: Path
    plugin_id: str
    marketplace: str
    plugin_name: str


def load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def split_plugin_id(plugin_id: str) -> tuple[str, str]:
    if "@" not in plugin_id:
        raise ValueError(
            f"Enabled plugin id {plugin_id!r} is missing a marketplace suffix"
        )
    plugin_name, marketplace = plugin_id.rsplit("@", 1)
    if not plugin_name or not marketplace:
        raise ValueError(f"Enabled plugin id {plugin_id!r} is invalid")
    return plugin_name, marketplace


def find_plugin(marketplace_root: Path, plugin_name: str) -> dict[str, Any] | None:
    marketplace_path = marketplace_root / ".claude-plugin" / "marketplace.json"
    if not marketplace_path.exists():
        return None
    marketplace = load_json(marketplace_path)
    plugins = marketplace.get("plugins", [])
    if not isinstance(plugins, list):
        raise ValueError(f"{marketplace_path} has a non-list 'plugins' field")
    for plugin in plugins:
        if isinstance(plugin, dict) and plugin.get("name") == plugin_name:
            return plugin
    return None


def index_marketplaces(marketplaces_root: Path) -> dict[str, Path]:
    index: dict[str, Path] = {}
    for candidate in sorted(marketplaces_root.iterdir()):
        if not candidate.is_dir():
            continue
        marketplace_path = candidate / ".claude-plugin" / "marketplace.json"
        if not marketplace_path.exists():
            continue
        marketplace = load_json(marketplace_path)
        name = marketplace.get("name")
        if not isinstance(name, str) or not name:
            continue
        if name in index and index[name] != candidate:
            raise ValueError(
                f"Duplicate marketplace name {name!r}: {index[name]} vs {candidate}"
            )
        index[name] = candidate
    return index


def resolve_path_candidates(
    marketplace_root: Path, plugin: dict[str, Any], relative_path: str
) -> list[Path]:
    rel = Path(relative_path)
    candidates = [(marketplace_root / rel).resolve()]

    source = plugin.get("source")
    if isinstance(source, str) and source:
        source_dir = (marketplace_root / Path(source)).resolve()
        candidates.append((source_dir / rel).resolve())
        candidates.append((source_dir.parent / rel).resolve())

    seen: set[Path] = set()
    result: list[Path] = []
    for candidate in candidates:
        if candidate not in seen:
            seen.add(candidate)
            result.append(candidate)
    return result


def resolve_skill_dirs(marketplace_root: Path, plugin: dict[str, Any]) -> list[Path]:
    raw_skills = plugin.get("skills")
    if isinstance(raw_skills, list) and raw_skills:
        resolved: list[Path] = []
        for item in raw_skills:
            if not isinstance(item, str):
                raise ValueError(
                    f"Plugin {plugin.get('name')!r} has a non-string skill path"
                )
            for candidate in resolve_path_candidates(marketplace_root, plugin, item):
                if (candidate / "SKILL.md").exists():
                    resolved.append(candidate)
                    break
            else:
                raise FileNotFoundError(
                    f"Could not resolve skill path {item!r} for plugin "
                    f"{plugin.get('name')!r} under {marketplace_root}"
                )
        return resolved

    source = plugin.get("source")
    if isinstance(source, str) and source:
        source_dir = (marketplace_root / Path(source)).resolve()
        if (source_dir / "SKILL.md").exists():
            return [source_dir]

        plugin_json = source_dir / ".claude-plugin" / "plugin.json"
        if plugin_json.exists():
            plugin_data = load_json(plugin_json)
            nested_skills = plugin_data.get("skills")
            if isinstance(nested_skills, list) and nested_skills:
                nested_plugin = dict(plugin)
                nested_plugin["source"] = source
                nested_plugin["skills"] = nested_skills
                return resolve_skill_dirs(marketplace_root, nested_plugin)

    return []


def collect_enabled_skill_links(
    settings_path: Path, marketplaces_root: Path
) -> tuple[list[SkillLink], list[str]]:
    settings = load_json(settings_path)
    enabled_plugins = settings.get("enabledPlugins", {})
    if not isinstance(enabled_plugins, dict):
        raise ValueError(f"{settings_path} has a non-object 'enabledPlugins' field")

    marketplace_index = index_marketplaces(marketplaces_root)
    collected: dict[str, SkillLink] = {}
    notes: list[str] = []

    for plugin_id, enabled in enabled_plugins.items():
        if not enabled:
            continue
        if not isinstance(plugin_id, str):
            notes.append("Skipping non-string enabled plugin id")
            continue

        try:
            plugin_name, marketplace_name = split_plugin_id(plugin_id)
        except ValueError as exc:
            notes.append(f"Skipping {plugin_id!r}: {exc}")
            continue

        marketplace_root = marketplace_index.get(marketplace_name)
        if not marketplace_root:
            notes.append(
                f"Skipping {plugin_id}: marketplace {marketplace_name!r} is missing"
            )
            continue

        plugin = find_plugin(marketplace_root, plugin_name)
        if not plugin:
            notes.append(
                f"Skipping {plugin_id}: plugin is not declared in marketplace.json"
            )
            continue

        skill_dirs = resolve_skill_dirs(marketplace_root, plugin)
        if not skill_dirs:
            notes.append(f"Ignoring {plugin_id}: plugin does not expose skills")
            continue

        for skill_dir in skill_dirs:
            skill_name = skill_dir.name
            link = SkillLink(
                name=skill_name,
                source=skill_dir.resolve(),
                plugin_id=plugin_id,
                marketplace=marketplace_name,
                plugin_name=plugin_name,
            )
            existing = collected.get(skill_name)
            if existing and existing.source != link.source:
                raise ValueError(
                    f"Skill name collision for {skill_name!r}: "
                    f"{existing.source} vs {link.source}"
                )
            collected[skill_name] = link

    return sorted(collected.values(), key=lambda item: item.name), notes


def ensure_target_dir(target_dir: Path, replace_symlink: bool, dry_run: bool) -> None:
    if target_dir.is_symlink():
        if not replace_symlink:
            raise RuntimeError(
                f"{target_dir} is currently a symlink. "
                "Use --replace-symlink to replace it with a managed directory."
            )
        print(
            f"{'DRY-RUN ' if dry_run else ''}replace symlinked target root {target_dir}"
        )
        if not dry_run:
            target_dir.unlink()
            target_dir.mkdir(parents=True, exist_ok=True)
        return

    if target_dir.exists() and not target_dir.is_dir():
        raise RuntimeError(f"{target_dir} exists and is not a directory")

    if target_dir.exists():
        return

    print(f"{'DRY-RUN ' if dry_run else ''}mkdir {target_dir}")
    if not dry_run:
        target_dir.mkdir(parents=True, exist_ok=True)


def load_manifest(target_dir: Path) -> dict[str, str]:
    manifest_path = target_dir / MANIFEST_NAME
    if not manifest_path.exists():
        return {}
    data = load_json(manifest_path)
    entries = data.get("entries", {})
    if not isinstance(entries, dict):
        raise ValueError(f"{manifest_path} has a non-object 'entries' field")
    return {str(key): str(value) for key, value in entries.items()}


def write_manifest(target_dir: Path, links: list[SkillLink], dry_run: bool) -> None:
    manifest_path = target_dir / MANIFEST_NAME
    payload = {
        "entries": {link.name: str(link.source) for link in links},
        "source": "claude-enabled-plugins",
    }
    if dry_run:
        print(f"DRY-RUN write {manifest_path}")
        return
    manifest_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def remove_stale_links(
    target_dir: Path, desired_names: set[str], prior_manifest: dict[str, str], dry_run: bool
) -> int:
    removed = 0
    for stale_name in sorted(set(prior_manifest) - desired_names):
        stale_path = target_dir / stale_name
        if not stale_path.exists() and not stale_path.is_symlink():
            removed += 1
            continue
        if stale_path.is_symlink():
            print(f"{'DRY-RUN ' if dry_run else ''}unlink {stale_path}")
            if not dry_run:
                stale_path.unlink()
            removed += 1
            continue
        print(f"Skipping unmanaged stale entry at {stale_path}", file=sys.stderr)
    return removed


def sync_links(target_dir: Path, links: list[SkillLink], dry_run: bool) -> tuple[int, int]:
    created = 0
    updated = 0
    for link in links:
        dest = target_dir / link.name
        if dest.is_symlink():
            if dest.resolve() == link.source:
                continue
            print(f"{'DRY-RUN ' if dry_run else ''}relink {dest} -> {link.source}")
            if not dry_run:
                dest.unlink()
                dest.symlink_to(link.source)
            updated += 1
            continue

        if dest.exists():
            print(
                f"Skipping {dest}: destination already exists and is not a managed symlink",
                file=sys.stderr,
            )
            continue

        print(f"{'DRY-RUN ' if dry_run else ''}link {dest} -> {link.source}")
        if not dry_run:
            dest.symlink_to(link.source)
        created += 1

    return created, updated


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Read Claude enabledPlugins and project enabled skills into ~/.codex/skills."
        )
    )
    parser.add_argument(
        "--claude-settings",
        type=Path,
        default=Path("~/.claude/settings.json").expanduser(),
        help="Path to Claude settings.json",
    )
    parser.add_argument(
        "--claude-marketplaces",
        type=Path,
        default=Path("~/.claude/plugins/marketplaces").expanduser(),
        help="Root directory containing Claude plugin marketplaces",
    )
    parser.add_argument(
        "--codex-skills",
        type=Path,
        default=Path("~/.codex/skills").expanduser(),
        help="Directory to populate with skill symlinks",
    )
    parser.add_argument(
        "--replace-symlink",
        action="store_true",
        help="Replace ~/.codex/skills if it is currently a symlink",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print planned changes without touching the filesystem",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    try:
        links, notes = collect_enabled_skill_links(
            settings_path=args.claude_settings,
            marketplaces_root=args.claude_marketplaces,
        )
        ensure_target_dir(args.codex_skills, args.replace_symlink, args.dry_run)
        prior_manifest = load_manifest(args.codex_skills)
        removed = remove_stale_links(
            target_dir=args.codex_skills,
            desired_names={link.name for link in links},
            prior_manifest=prior_manifest,
            dry_run=args.dry_run,
        )
        created, updated = sync_links(
            target_dir=args.codex_skills,
            links=links,
            dry_run=args.dry_run,
        )
        write_manifest(args.codex_skills, links, args.dry_run)
    except (OSError, ValueError, RuntimeError, FileNotFoundError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    for note in notes:
        print(note, file=sys.stderr)

    print(
        f"Synced {len(links)} skill link(s): {created} created, "
        f"{updated} updated, {removed} removed."
    )
    if links:
        for link in links:
            print(f"- {link.name} <- {link.plugin_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
