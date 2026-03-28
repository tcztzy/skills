#!/usr/bin/env python3
"""
Create a local, editable bundle of template files for a team-intel run.

This script does NOT fetch any web content. It's purely scaffolding.
"""

from __future__ import annotations

import argparse
import json
import os
import re
from datetime import date
from pathlib import Path


def _slug(s: str) -> str:
    s = s.strip().lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-") or "untitled"


def main() -> int:
    p = argparse.ArgumentParser(description="Scaffold a Career Team Intel output bundle.")
    p.add_argument("--out", default=".", help="Parent output directory (default: current dir).")
    p.add_argument("--company", required=True, help="Target company name.")
    p.add_argument("--focus", default="", help="Focus keyword(s), used for naming only.")
    p.add_argument(
        "--day",
        default=str(date.today()),
        help="Date stamp in YYYY-MM-DD (default: today).",
    )
    p.add_argument("--force", action="store_true", help="Overwrite existing files.")
    args = p.parse_args()

    day = args.day.strip()
    # Minimal validation; keep it lenient.
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", day):
        raise SystemExit(f"--day must be YYYY-MM-DD, got: {day!r}")

    bundle_name = f"{day}_{_slug(args.company)}"
    if args.focus.strip():
        bundle_name += f"__{_slug(args.focus)}"

    out_dir = Path(args.out).expanduser().resolve() / "career-team-intel" / bundle_name
    out_dir.mkdir(parents=True, exist_ok=True)

    def write(path: Path, content: str) -> None:
        if path.exists() and not args.force:
            raise SystemExit(f"Refusing to overwrite existing file: {path} (use --force)")
        path.write_text(content, encoding="utf-8")

    # Templates are intentionally short; the skill references richer templates in references/output-templates.md.
    write(
        out_dir / "team_brief.md",
        f"""# Team Brief — {args.company} / <Team>
Date: {day}
Scope keywords: <...>

## What this team builds (public)
- <...>

## Why now (hiring intent)
- <strong/medium/weak> — <1 line> (Date, Link)

## Priorities & success metrics
- <...> (Link)

## Tech stack & constraints (signals)
- <...> (Link)

## What they likely need in this hire
- <...>

## My fit (proof points)
- <...>

## Best outreach angle
- <...>

## Open questions to validate
- <req ID?> <level?> <location?> <interview focus?> ...
""",
    )

    write(
        out_dir / "hiring_signals.md",
        f"""# Hiring Signals — {args.company} / <Team>

| Date | Source | Signal | Strength | Notes | Link |
|---|---|---|---|---|---|
| {day} | <leader_post/official_req/etc> | <...> | <S/M/W/N> | <...> | <...> |
""",
    )

    write(
        out_dir / "people_map.md",
        f"""# People Map — {args.company} / <Team>

| Person | Role | Why them | Best channel | What to ask/send | Evidence |
|---|---|---|---|---|---|
| <Name> | <EM/TL/HM/recruiter/IC> | <...> | <...> | <...> | <links> |
""",
    )

    write(
        out_dir / "resume_alignment.md",
        f"""# Resume Alignment — {args.company} / <Team>

| Team priority/pain | Evidence | My proof | Resume bullet (draft) |
|---|---|---|---|
| <...> | <link> | <metric> | <action + metric + context> |
""",
    )

    write(
        out_dir / "outreach_messages.md",
        """# Outreach Messages (Templates)

Leader / hiring manager:
Hi <Name> — I saw your post about hiring for <role/team> (<date/link>). I’ve worked on <matching area>, e.g. <metric/result>.
Is there a req ID/link you prefer I apply through?
""",
    )

    write(
        out_dir / "interview_prep.md",
        f"""# Interview Prep — {args.company} / <Team>

## Likely topics (evidence-linked)
- <topic> (Link) -> prepare: <what to say/do>

## My stories (STAR)
- <story title>: Situation / Task / Action / Result (metric)

## Questions to ask them
- <...>
""",
    )

    extraction = {
        "bundle": {
            "id": bundle_name,
            "created_at": day,
            "source_notes": "",
        },
        "target": {
            "company": args.company,
            "role_type": "",
            "level": "",
            "focus_keywords": [k for k in re.split(r"[,\s]+", args.focus.strip()) if k] if args.focus else [],
            "constraints": {"location": "", "remote_ok": None, "visa": ""},
        },
        "artifacts": [],
        "candidates": [],
        "notes": {"uncertainties": [], "do_not_do": []},
    }
    write(out_dir / "extraction.json", json.dumps(extraction, indent=2, ensure_ascii=False) + "\n")

    print(str(out_dir))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
