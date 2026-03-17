#!/usr/bin/env python3
"""Copy Windows-only Codex skills into the WSL skills root and write a manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parent))

from validate_skill import validate_skill  # type: ignore  # noqa: E402

DEFAULT_SOURCE_ROOT = Path("/mnt/c/Users/huolo/.codex/skills")
DEFAULT_DEST_ROOT = Path.home() / ".codex" / "skills"
DEFAULT_TMP_ROOT = Path.home() / ".codex" / "tmp" / "windows-skill-migration-audit"
WINDOWS_ONLY_TARGETS = [
    "doc",
    "gh-fix-ci",
    "jupyter-notebook",
    "latex-to-word",
    "notion-knowledge-capture",
    "notion-meeting-intelligence",
    "notion-research-documentation",
    "notion-spec-to-implementation",
    "openai-docs",
    "pdf",
    "playwright",
    "screenshot",
    "yeet",
]


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def make_timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def list_source_skills(source_root: Path) -> dict[str, Path]:
    skills: dict[str, Path] = {}
    for path in sorted(source_root.iterdir()):
        if not path.is_dir() or path.name == "_backup":
            continue
        if (path / "SKILL.md").exists():
            skills[path.name] = path
    return skills


def hash_tree(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        rel = path.relative_to(root).as_posix().encode("utf-8")
        digest.update(rel)
        digest.update(b"\0")
        with path.open("rb") as handle:
            while True:
                chunk = handle.read(1024 * 1024)
                if not chunk:
                    break
                digest.update(chunk)
        digest.update(b"\0")
    return digest.hexdigest()


def dump_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def migrate_skills(*, source_root: Path, dest_root: Path, workspace_root: Path, skills: list[str] | None = None) -> dict[str, Any]:
    source_root = source_root.resolve()
    dest_root = dest_root.resolve()
    workspace_root = workspace_root.resolve()
    workspace_root.mkdir(parents=True, exist_ok=True)

    available = list_source_skills(source_root)
    requested = skills or WINDOWS_ONLY_TARGETS
    copied: list[dict[str, Any]] = []
    overlaps: list[dict[str, Any]] = []
    missing: list[dict[str, Any]] = []
    invalid: list[dict[str, Any]] = []

    for skill_name in requested:
        src = available.get(skill_name)
        dst = dest_root / skill_name
        if src is None:
            missing.append({
                "skill_name": skill_name,
                "source_path": str(source_root / skill_name),
                "dest_path": str(dst),
                "copied_at": None,
                "source_hash": None,
                "validation_passed": False,
                "notes": ["missing_from_windows_source"],
            })
            continue

        source_valid, source_message = validate_skill(src)
        source_hash = hash_tree(src)
        if not source_valid:
            invalid.append({
                "skill_name": skill_name,
                "source_path": str(src),
                "dest_path": str(dst),
                "copied_at": None,
                "source_hash": source_hash,
                "validation_passed": False,
                "notes": [f"source_validation_failed: {source_message}"],
            })
            continue

        if dst.exists():
            overlaps.append({
                "skill_name": skill_name,
                "source_path": str(src),
                "dest_path": str(dst),
                "copied_at": None,
                "source_hash": source_hash,
                "validation_passed": True,
                "notes": ["wsl_skill_already_exists; skipped to avoid overwrite"],
            })
            continue

        shutil.copytree(src, dst)
        dest_valid, dest_message = validate_skill(dst)
        copied.append({
            "skill_name": skill_name,
            "source_path": str(src),
            "dest_path": str(dst),
            "copied_at": utc_now_iso(),
            "source_hash": source_hash,
            "validation_passed": dest_valid,
            "notes": [
                f"source_validation: {source_message}",
                f"dest_validation: {dest_message}",
            ],
        })

    payload = {
        "generated_at": utc_now_iso(),
        "source_root": str(source_root),
        "dest_root": str(dest_root),
        "workspace": str(workspace_root),
        "requested_skills": requested,
        "copied_count": len(copied),
        "overlap_count": len(overlaps),
        "missing_count": len(missing),
        "invalid_count": len(invalid),
        "copied_skills": copied,
        "overlap_skills": overlaps,
        "missing_skills": missing,
        "invalid_skills": invalid,
    }
    dump_json(workspace_root / "migration_manifest.json", payload)
    return payload


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Copy Windows-only Codex skills into the WSL skills root")
    parser.add_argument("--source-root", default=str(DEFAULT_SOURCE_ROOT), help="Windows Codex skills directory")
    parser.add_argument("--dest-root", default=str(DEFAULT_DEST_ROOT), help="WSL Codex skills directory")
    parser.add_argument("--workspace", default=None, help="Audit workspace root (defaults to a new timestamped tmp dir)")
    parser.add_argument("--skill", dest="skills", action="append", help="Specific skill(s) to migrate; repeatable")
    args = parser.parse_args(argv)

    workspace = Path(args.workspace).expanduser() if args.workspace else (DEFAULT_TMP_ROOT / make_timestamp())
    payload = migrate_skills(
        source_root=Path(args.source_root).expanduser(),
        dest_root=Path(args.dest_root).expanduser(),
        workspace_root=workspace,
        skills=args.skills,
    )
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
