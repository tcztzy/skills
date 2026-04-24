#!/usr/bin/env python3
"""Summarize local Codex skill metrics JSONL files."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from common import EVENT_LOG, SKILL_LOG


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


def ratio(num: int, den: int) -> float | None:
    return None if den == 0 else num / den


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--events", type=Path, default=EVENT_LOG)
    parser.add_argument("--skill-use", type=Path, default=SKILL_LOG)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    events = read_jsonl(args.events)
    explicit_uses = read_jsonl(args.skill_use)
    candidate_counts: Counter[str] = Counter()
    candidate_score_totals: Counter[str] = Counter()
    candidate_score_counts: Counter[str] = Counter()
    observed_counts: Counter[str] = Counter()
    explicit_counts: Counter[str] = Counter()
    stats: dict[str, Counter[str]] = defaultdict(Counter)

    for event in events:
        for skill in event.get("candidate_skill_hints") or event.get("candidate_expected_skills") or []:
            candidate_counts[skill] += 1
        for match in event.get("candidate_skill_matches") or []:
            if not isinstance(match, dict):
                continue
            skill = match.get("skill")
            score = match.get("score")
            if isinstance(skill, str) and isinstance(score, (int, float)):
                candidate_score_totals[skill] += score
                candidate_score_counts[skill] += 1
        for skill in event.get("observed_skills") or []:
            observed_counts[skill] += 1
        conf = event.get("confusion")
        if isinstance(conf, dict):
            for field in ("tp", "fn", "fp"):
                for skill in conf.get(field) or []:
                    stats[skill][field] += 1

    for row in explicit_uses:
        skill = row.get("skill")
        if isinstance(skill, str):
            explicit_counts[skill] += 1

    all_skills = sorted(set(candidate_counts) | set(observed_counts) | set(explicit_counts) | set(stats))
    summary = {
        "event_count": len(events),
        "skill_use_marker_count": len(explicit_uses),
        "skills": [],
    }
    for skill in all_skills:
        tp = stats[skill]["tp"]
        fn = stats[skill]["fn"]
        fp = stats[skill]["fp"]
        precision = ratio(tp, tp + fp)
        recall = ratio(tp, tp + fn)
        f1 = None if precision is None or recall is None or precision + recall == 0 else 2 * precision * recall / (precision + recall)
        summary["skills"].append(
            {
                "skill": skill,
                "candidate_count": candidate_counts[skill],
                "avg_candidate_score": ratio(candidate_score_totals[skill], candidate_score_counts[skill]),
                "observed_count": observed_counts[skill],
                "explicit_marker_count": explicit_counts[skill],
                "tp": tp,
                "fn": fn,
                "fp": fp,
                "precision": precision,
                "recall": recall,
                "f1": f1,
            }
        )

    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
        return 0

    print(f"events: {summary['event_count']}  explicit markers: {summary['skill_use_marker_count']}")
    print("skill\tcandidate\tavg_score\tobserved\tmarker\ttp\tfn\tfp\tprecision\trecall\tf1")
    for row in summary["skills"]:
        def fmt(value: object) -> str:
            return "" if value is None else (f"{value:.3f}" if isinstance(value, float) else str(value))

        print(
            "\t".join(
                [
                    fmt(row["skill"]),
                    fmt(row["candidate_count"]),
                    fmt(row["avg_candidate_score"]),
                    fmt(row["observed_count"]),
                    fmt(row["explicit_marker_count"]),
                    fmt(row["tp"]),
                    fmt(row["fn"]),
                    fmt(row["fp"]),
                    fmt(row["precision"]),
                    fmt(row["recall"]),
                    fmt(row["f1"]),
                ]
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
