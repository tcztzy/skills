#!/usr/bin/env python3
"""Small shared helpers for skill-manager scripts."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def dump_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def dump_json(path: Path, payload: Any) -> None:
    dump_text(path, json.dumps(payload, indent=2, ensure_ascii=False) + "\n")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def ensure_lab_workspace(root: str | Path) -> dict[str, Path]:
    workspace_root = Path(root).expanduser().resolve()
    reports = workspace_root / "reports"
    eval_packs = workspace_root / "eval_packs"
    artifacts = workspace_root / "artifacts"
    for path in (workspace_root, reports, eval_packs, artifacts):
        path.mkdir(parents=True, exist_ok=True)
    return {
        "root": workspace_root,
        "reports": reports,
        "eval_packs": eval_packs,
        "artifacts": artifacts,
    }
