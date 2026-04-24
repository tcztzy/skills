#!/usr/bin/env python3
"""Shared helpers for local Codex skill metrics hooks."""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


HOME = Path.home()
BASE_DIR = HOME / ".codex" / "skill-metrics"
LOG_DIR = BASE_DIR / "logs"
EVENT_LOG = LOG_DIR / "events.jsonl"
SKILL_LOG = LOG_DIR / "skill-use.jsonl"
INVENTORY_CACHE = LOG_DIR / "skill-inventory.json"
GOLD_FILE = BASE_DIR / "gold" / "skills.jsonl"
SKILL_ROOTS = [
    HOME / ".codex" / "skills",
    HOME / ".agents" / "skills",
    HOME / ".codex" / "plugins" / "cache",
    HOME / "skills" / "skills",
    HOME / "skills",
]

FRONTMATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*", re.DOTALL)
SKILL_MENTION_RE = re.compile(r"(?<![\w/.-])\$([A-Za-z0-9][A-Za-z0-9_.:-]{1,80})\b")
SKILL_ANNOUNCE_RE = re.compile(
    r"(?:using|use|invoke|invoking|trigger(?:ed)?|skill(?:s)?[:\s]+)"
    r"[^.\n]{0,80}?([A-Za-z0-9][A-Za-z0-9_.:-]{1,80})",
    re.IGNORECASE,
)
STOPWORDS = {
    "about",
    "agent",
    "agents",
    "analysis",
    "answer",
    "build",
    "check",
    "codex",
    "create",
    "data",
    "debug",
    "edit",
    "file",
    "files",
    "guide",
    "help",
    "implement",
    "local",
    "make",
    "model",
    "output",
    "paper",
    "prompt",
    "prompts",
    "python",
    "repo",
    "request",
    "review",
    "run",
    "script",
    "that",
    "this",
    "skill",
    "skills",
    "task",
    "test",
    "text",
    "tool",
    "tools",
    "update",
    "user",
    "using",
    "when",
    "with",
    "without",
    "work",
    "workflow",
}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def read_stdin_json() -> dict[str, Any]:
    raw = sys.stdin.read()
    if not raw.strip():
        return {}
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return {"_raw_stdin": raw}
    return data if isinstance(data, dict) else {"_stdin": data}


def append_jsonl(path: Path, event: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()


def maybe_store_text(text: str) -> str | None:
    if os.environ.get("SKILL_METRICS_STORE_TEXT", "1") in {"0", "false", "False"}:
        return None
    return text


def compact_text(text: str, limit: int = 5000) -> str:
    text = text.replace("\r\n", "\n").strip()
    if len(text) <= limit:
        return text
    return text[:limit] + f"\n...[truncated {len(text) - limit} chars]"


def payload_get(payload: dict[str, Any], *names: str) -> Any:
    for name in names:
        value = payload.get(name)
        if value not in (None, ""):
            return value
    return None


def extract_prompt(payload: dict[str, Any]) -> str:
    for key in ("prompt", "message", "last_user_message"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value
    content = payload.get("content")
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict) and isinstance(item.get("text"), str):
                parts.append(item["text"])
        return "\n".join(parts).strip()
    return ""


def parse_frontmatter(text: str) -> dict[str, str]:
    match = FRONTMATTER_RE.match(text)
    if not match:
        return {}
    data: dict[str, str] = {}
    for raw_line in match.group(1).splitlines():
        line = raw_line.strip()
        if not line or ":" not in line:
            continue
        key, value = line.split(":", 1)
        data[key.strip()] = value.strip().strip("\"'")
    return data


def iter_skill_files() -> list[Path]:
    seen: set[Path] = set()
    files: list[Path] = []
    for root in SKILL_ROOTS:
        if not root.exists():
            continue
        for path in root.rglob("SKILL.md"):
            try:
                real = path.resolve()
            except OSError:
                continue
            if real not in seen:
                seen.add(real)
                files.append(real)
    return sorted(files)


def inventory_skills() -> list[dict[str, str]]:
    ttl = int(os.environ.get("SKILL_METRICS_INVENTORY_TTL", "600"))
    try:
        if INVENTORY_CACHE.exists() and time.time() - INVENTORY_CACHE.stat().st_mtime < ttl:
            data = json.loads(INVENTORY_CACHE.read_text(encoding="utf-8"))
            if isinstance(data, list):
                return [row for row in data if isinstance(row, dict)]
    except (OSError, json.JSONDecodeError):
        pass

    skills: list[dict[str, str]] = []
    for path in iter_skill_files():
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        meta = parse_frontmatter(text)
        name = meta.get("name") or path.parent.name
        description = meta.get("description", "")
        skills.append(
            {
                "name": name,
                "description": description,
                "path": str(path),
                "sha256": sha256_text(text),
            }
        )
    try:
        append_jsonl(LOG_DIR / "inventory-refresh.jsonl", {"event": "inventory_refresh", "ts": now_iso(), "count": len(skills)})
        INVENTORY_CACHE.write_text(json.dumps(skills, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    except OSError:
        pass
    return skills


def explicit_skill_mentions(text: str) -> list[str]:
    return sorted(set(SKILL_MENTION_RE.findall(text)))


def skill_match_terms(text: str) -> list[str]:
    return [
        token.lower()
        for token in re.findall(r"[A-Za-z0-9_+-]{4,}", text)
        if token.lower() not in STOPWORDS
    ]


def rough_candidate_skill_matches(
    prompt: str,
    skills: list[dict[str, str]],
    limit: int = 12,
    min_score: int = 3,
) -> list[dict[str, Any]]:
    prompt_l = prompt.lower()
    matches: list[dict[str, Any]] = []
    explicit = set(explicit_skill_mentions(prompt))
    for skill in skills:
        name = skill["name"]
        desc = skill.get("description", "")
        score = 0
        reasons: list[str] = []
        if name in explicit:
            score += 100
            reasons.append("explicit_mention")
        if name.lower() in prompt_l:
            score += 20
            reasons.append("skill_name")

        name_hits = sorted({token for token in skill_match_terms(name) if token in prompt_l})
        if name_hits:
            score += min(12, len(name_hits) * 4)
            reasons.extend(f"name:{token}" for token in name_hits[:4])

        desc_hits = sorted({token for token in skill_match_terms(desc) if token in prompt_l})
        if desc_hits:
            score += min(6, len(desc_hits))
            reasons.extend(f"description:{token}" for token in desc_hits[:6])

        if name in explicit or score >= min_score:
            matches.append({"skill": name, "score": score, "reasons": reasons})
    return sorted(matches, key=lambda row: (-int(row["score"]), str(row["skill"])))[:limit]


def rough_candidate_skills(prompt: str, skills: list[dict[str, str]], limit: int = 12) -> list[str]:
    return [row["skill"] for row in rough_candidate_skill_matches(prompt, skills, limit=limit)]


def latest_transcript() -> Path | None:
    session_root = HOME / ".codex" / "sessions"
    if not session_root.exists():
        return None
    latest: Path | None = None
    latest_mtime = -1.0
    for path in session_root.rglob("*.jsonl"):
        try:
            mtime = path.stat().st_mtime
        except OSError:
            continue
        if mtime > latest_mtime:
            latest = path
            latest_mtime = mtime
    return latest


def transcript_path_from_payload(payload: dict[str, Any]) -> Path | None:
    value = payload_get(payload, "transcript_path", "transcriptPath", "session_path", "sessionPath")
    if isinstance(value, str) and value:
        path = Path(value).expanduser()
        if path.exists():
            return path
    return latest_transcript()


def iter_transcript_items(path: Path) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return items
    for line in lines:
        if not line.strip():
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(item, dict):
            items.append(item)
    return items


def message_text(item: dict[str, Any], role: str | None = None) -> str:
    payload = item.get("payload") if isinstance(item.get("payload"), dict) else item
    if role and payload.get("role") != role and item.get("role") != role:
        return ""
    content = payload.get("content")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for chunk in content:
            if isinstance(chunk, dict):
                text = chunk.get("text")
                if isinstance(text, str):
                    parts.append(text)
        return "\n".join(parts)
    message = payload.get("message")
    if isinstance(message, str):
        return message
    return ""


def latest_message_text(items: list[dict[str, Any]], role: str) -> str:
    for item in reversed(items):
        text = message_text(item, role)
        if text.strip():
            return text
    return ""


def observed_skills_from_text(text: str, skill_names: set[str]) -> list[str]:
    found = set(explicit_skill_mentions(text))
    for name in skill_names:
        escaped = re.escape(name)
        if re.search(
            rf"(?i)(?:\busing\b|\buse\b|\binvoke\b|\binvoking\b|\btrigger(?:ed)?\b|使用|用|触发|觸發)"
            rf"[^.\n]{{0,120}}(?<![\w/.-])\$?{escaped}(?![\w/.-])",
            text,
        ):
            found.add(name)
        elif re.search(rf"(?i)(?<![\w/.-])\$?{escaped}(?![\w/.-])[^.\n]{{0,60}}\bskill\b", text):
            found.add(name)
    for match in SKILL_ANNOUNCE_RE.finditer(text):
        name = match.group(1)
        if name in skill_names:
            found.add(name)
    return sorted(name for name in found if not skill_names or name in skill_names)


def load_gold() -> list[dict[str, Any]]:
    if not GOLD_FILE.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in GOLD_FILE.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(row, dict):
            rows.append(row)
    return rows


def expected_for_prompt(prompt: str) -> list[str]:
    prompt_hash = sha256_text(prompt)
    for row in load_gold():
        if row.get("prompt_sha256") == prompt_hash:
            skills = row.get("expected_skills", [])
            return sorted(skills) if isinstance(skills, list) else []
    return []


def confusion(expected: list[str], observed: list[str]) -> dict[str, list[str]]:
    exp = set(expected)
    obs = set(observed)
    return {
        "tp": sorted(exp & obs),
        "fn": sorted(exp - obs),
        "fp": sorted(obs - exp),
    }
