#!/usr/bin/env python3
"""Codex Stop hook: record observed skill use and gold-set confusion."""

from __future__ import annotations

import sys

from common import (
    EVENT_LOG,
    append_jsonl,
    compact_text,
    confusion,
    expected_for_prompt,
    inventory_skills,
    latest_message_text,
    maybe_store_text,
    now_iso,
    observed_skills_from_text,
    payload_get,
    read_stdin_json,
    sha256_text,
    transcript_path_from_payload,
    iter_transcript_items,
)


def main() -> int:
    payload = read_stdin_json()
    skills = inventory_skills()
    skill_names = {skill["name"] for skill in skills}
    transcript_path = transcript_path_from_payload(payload)
    items = iter_transcript_items(transcript_path) if transcript_path else []

    user_text = latest_message_text(items, "user")
    assistant_text = payload_get(payload, "last_assistant_message", "lastAssistantMessage")
    if not isinstance(assistant_text, str) or not assistant_text.strip():
        assistant_text = latest_message_text(items, "assistant")
    observed = observed_skills_from_text(assistant_text or "", skill_names)
    expected = expected_for_prompt(user_text) if user_text else []

    event = {
        "event": "stop",
        "ts": now_iso(),
        "cwd": payload_get(payload, "cwd"),
        "session_id": payload_get(payload, "session_id", "sessionId"),
        "transcript_path": str(transcript_path) if transcript_path else None,
        "prompt_sha256": sha256_text(user_text) if user_text else None,
        "prompt": maybe_store_text(compact_text(user_text)) if user_text else None,
        "assistant_sha256": sha256_text(assistant_text or ""),
        "assistant": maybe_store_text(compact_text(assistant_text or "")),
        "observed_skills": observed,
        "gold_expected_skills": expected,
        "confusion": confusion(expected, observed) if expected else None,
        "available_skill_count": len(skills),
    }
    append_jsonl(EVENT_LOG, event)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # noqa: BLE001 - hooks must never break a Codex turn.
        print(f"skill-metrics stop error: {exc}", file=sys.stderr)
        raise SystemExit(0)
