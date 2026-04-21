#!/usr/bin/env python3
"""Optional explicit skill-use marker.

Usage from a skill or local command:
  python3 ~/.codex/skill-metrics/log_use.py caveman --version local
"""

from __future__ import annotations

import argparse
import os
import sys

from common import SKILL_LOG, append_jsonl, now_iso


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("skill")
    parser.add_argument("--version", default=None)
    parser.add_argument("--source", default="manual")
    args = parser.parse_args()
    append_jsonl(
        SKILL_LOG,
        {
            "event": "skill_use",
            "ts": now_iso(),
            "skill": args.skill,
            "version": args.version,
            "source": args.source,
            "cwd": os.getcwd(),
            "session_id": os.environ.get("CODEX_SESSION_ID"),
        },
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # noqa: BLE001 - metrics must not break main work.
        print(f"skill-metrics log_use error: {exc}", file=sys.stderr)
        raise SystemExit(0)
