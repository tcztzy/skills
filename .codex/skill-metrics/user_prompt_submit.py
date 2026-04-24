#!/usr/bin/env python3
"""Codex UserPromptSubmit hook: record skill opportunities."""

from __future__ import annotations

import sys

from common import (
    EVENT_LOG,
    append_jsonl,
    compact_text,
    expected_for_prompt,
    explicit_skill_mentions,
    inventory_skills,
    maybe_store_text,
    now_iso,
    payload_get,
    rough_candidate_skill_matches,
    read_stdin_json,
    sha256_text,
)


def main() -> int:
    payload = read_stdin_json()
    prompt = payload_get(payload, "prompt", "message", "last_user_message") or ""
    if not isinstance(prompt, str):
        prompt = str(prompt)
    skills = inventory_skills()
    candidate_matches = rough_candidate_skill_matches(prompt, skills)
    candidate_hints = [row["skill"] for row in candidate_matches]
    event = {
        "event": "user_prompt_submit",
        "ts": now_iso(),
        "cwd": payload_get(payload, "cwd"),
        "session_id": payload_get(payload, "session_id", "sessionId"),
        "transcript_path": payload_get(payload, "transcript_path", "transcriptPath"),
        "prompt_sha256": sha256_text(prompt),
        "prompt": maybe_store_text(compact_text(prompt)),
        "explicit_skill_mentions": explicit_skill_mentions(prompt),
        "candidate_skill_hints": candidate_hints,
        "candidate_skill_matches": candidate_matches,
        "candidate_expected_skills": candidate_hints,
        "gold_expected_skills": expected_for_prompt(prompt),
        "available_skill_count": len(skills),
    }
    append_jsonl(EVENT_LOG, event)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # noqa: BLE001 - hooks must never break a Codex turn.
        print(f"skill-metrics user_prompt_submit error: {exc}", file=sys.stderr)
        raise SystemExit(0)
