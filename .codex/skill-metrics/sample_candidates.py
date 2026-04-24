#!/usr/bin/env python3
"""Sample candidate skill prompts for gold-label review."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from common import EVENT_LOG


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(row, dict):
            rows.append(row)
    return rows


def candidate_match(event: dict[str, Any], skill: str) -> dict[str, Any]:
    for match in event.get("candidate_skill_matches") or []:
        if isinstance(match, dict) and match.get("skill") == skill:
            return match
    if skill in (event.get("candidate_skill_hints") or event.get("candidate_expected_skills") or []):
        return {"skill": skill, "score": None, "reasons": []}
    return {}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("skill")
    parser.add_argument("--events", type=Path, default=EVENT_LOG)
    parser.add_argument("--limit", type=int, default=25)
    parser.add_argument("--include-text", action="store_true")
    parser.add_argument("--gold-template", action="store_true")
    args = parser.parse_args()

    seen: set[str] = set()
    count = 0
    for event in read_jsonl(args.events):
        if event.get("event") != "user_prompt_submit":
            continue
        match = candidate_match(event, args.skill)
        if not match:
            continue
        prompt_hash = event.get("prompt_sha256")
        if not isinstance(prompt_hash, str) or prompt_hash in seen:
            continue
        seen.add(prompt_hash)
        count += 1
        if args.gold_template:
            row = {
                "id": f"{args.skill}-{count:03d}",
                "prompt_sha256": prompt_hash,
                "expected_skills": [args.skill],
                "notes": "review candidate; clear expected_skills if this is a false positive",
            }
        else:
            row = {
                "prompt_sha256": prompt_hash,
                "skill": args.skill,
                "candidate_score": match.get("score"),
                "candidate_reasons": match.get("reasons") or [],
            }
            if args.include_text:
                row["prompt"] = event.get("prompt")
        print(json.dumps(row, ensure_ascii=False, sort_keys=True))
        if count >= args.limit:
            break
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
