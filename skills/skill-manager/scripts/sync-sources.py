#!/usr/bin/env python3
"""Sync skill source repositories into a local cache.

This script avoids the GitHub API (rate limits) by using git clone/pull.
It reads `references/sources.json` and syncs to:
  ~/.codex/tmp/skill-sources/<source-id>/

Restricted sources (restricted=true) are never synced.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


class SyncError(Exception):
    pass


@dataclass(frozen=True)
class Source:
    id: str
    repo: str
    ref: str
    restricted: bool
    sync: bool


def _codex_home() -> Path:
    return Path(os.environ.get("CODEX_HOME", os.path.expanduser("~/.codex"))).expanduser()


def _expand_codex_path(raw: str, codex_home: Path) -> Path:
    value = os.path.expandvars(raw.strip())
    norm = value.replace("\\", "/")
    if norm.startswith("~/.codex"):
        suffix = norm[len("~/.codex") :].lstrip("/")
        return (codex_home / suffix).resolve()
    return Path(os.path.expanduser(value)).expanduser().resolve()


def _load_sources_json(path: Path) -> tuple[Path, list[Source]]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        raise SyncError(f"Failed to read JSON: {path}") from exc
    if not isinstance(data, dict):
        raise SyncError(f"Invalid JSON root (expected object): {path}")

    codex_home = _codex_home()
    cache_root_raw = str(data.get("cache_root") or "~/.codex/tmp/skill-sources")
    cache_root = _expand_codex_path(cache_root_raw, codex_home)

    sources_raw = data.get("sources")
    if not isinstance(sources_raw, list) or not sources_raw:
        raise SyncError(f"Missing or invalid 'sources' list: {path}")

    sources: list[Source] = []
    for item in sources_raw:
        if not isinstance(item, dict):
            continue
        source_id = str(item.get("id") or "").strip()
        repo = str(item.get("repo") or "").strip()
        ref = str(item.get("ref") or "main").strip()
        restricted = bool(item.get("restricted", False))
        sync = bool(item.get("sync", True))
        if not source_id or not repo:
            continue
        sources.append(
            Source(
                id=source_id,
                repo=repo,
                ref=ref,
                restricted=restricted,
                sync=sync,
            )
        )
    if not sources:
        raise SyncError(f"No valid sources found in: {path}")
    return cache_root, sources


def _run_git(args: list[str], *, cwd: Path | None = None) -> None:
    result = subprocess.run(
        args,
        cwd=str(cwd) if cwd else None,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if result.returncode != 0:
        raise SyncError(result.stderr.strip() or "Git command failed.")


def _clone_or_update(source: Source, dest_dir: Path) -> None:
    dest_dir.parent.mkdir(parents=True, exist_ok=True)

    if not dest_dir.exists():
        # Prefer cloning the requested ref as a shallow clone.
        try:
            _run_git(
                [
                    "git",
                    "clone",
                    "--depth",
                    "1",
                    "--branch",
                    source.ref,
                    source.repo,
                    str(dest_dir),
                ]
            )
            return
        except SyncError:
            # Fallback: clone default branch shallow, then fetch+reset to ref.
            _run_git(["git", "clone", "--depth", "1", source.repo, str(dest_dir)])

    # Always reset to the requested ref (works even if detached).
    _run_git(["git", "-C", str(dest_dir), "remote", "set-url", "origin", source.repo])
    _run_git(["git", "-C", str(dest_dir), "fetch", "--depth", "1", "origin", source.ref])
    _run_git(["git", "-C", str(dest_dir), "reset", "--hard", "FETCH_HEAD"])


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sync skill source repos into ~/.codex/tmp/skill-sources.")
    parser.add_argument(
        "--all",
        action="store_true",
        help="Sync all non-restricted sources with sync=true",
    )
    parser.add_argument(
        "--source",
        action="append",
        default=[],
        help="Sync only the given source id(s). Can be repeated.",
    )
    parser.add_argument(
        "--cache-root",
        help="Override cache root (default from references/sources.json)",
    )
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    skill_manager_dir = Path(__file__).resolve().parent.parent
    sources_json = skill_manager_dir / "references" / "sources.json"
    try:
        cache_root, sources = _load_sources_json(sources_json)
        args = _parse_args(argv)
        if args.cache_root:
            cache_root = _expand_codex_path(args.cache_root, _codex_home())

        selected_ids = [s.strip() for s in (args.source or []) if s.strip()]
        if not args.all and not selected_ids:
            raise SyncError("Specify --all or --source <id>.")

        by_id = {s.id: s for s in sources}
        if args.all:
            selected = [s for s in sources if s.sync and not s.restricted]
        else:
            missing = [sid for sid in selected_ids if sid not in by_id]
            if missing:
                raise SyncError(f"Unknown source id(s): {', '.join(missing)}")
            selected = [by_id[sid] for sid in selected_ids]

        for src in selected:
            if src.restricted:
                raise SyncError(f"Refusing to sync restricted source: {src.id}")
            if not src.sync:
                continue
            dest_dir = cache_root / src.id
            print(f"[SYNC] {src.id} -> {dest_dir}")
            _clone_or_update(src, dest_dir)

        print("Done.")
        return 0
    except SyncError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

