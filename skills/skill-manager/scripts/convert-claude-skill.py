#!/usr/bin/env python3
"""Convert a Claude Code skill folder into a Codex skill folder.

This script is dependency-free (no PyYAML). It focuses on:
- Keeping only `name` + `description` in SKILL.md YAML frontmatter
- Optionally rewriting common Claude placeholders (e.g. $ARGUMENTS)
- Inserting a small "Codex Notes" block near the top (optional)
- Generating agents/openai.yaml if missing
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
from dataclasses import dataclass, field
from pathlib import Path


DEFAULT_ALLOWED_FRONTMATTER_KEYS = {
    "name",
    "description",
    "license",
    "allowed-tools",
    "metadata",
}


ACRONYMS = {
    "GH",
    "MCP",
    "API",
    "CI",
    "CLI",
    "LLM",
    "PDF",
    "PR",
    "UI",
    "URL",
    "SQL",
}

BRANDS = {
    "openai": "OpenAI",
    "openapi": "OpenAPI",
    "github": "GitHub",
    "pagerduty": "PagerDuty",
    "datadog": "DataDog",
    "sqlite": "SQLite",
    "fastapi": "FastAPI",
}

SMALL_WORDS = {"and", "or", "to", "up", "with"}


class ConvertError(Exception):
    pass


@dataclass(frozen=True)
class Preferences:
    language: str = "en-US"
    shell: str = "powershell"
    insert_codex_notes: bool = True
    skip_rewrites_in_fenced_code_blocks: bool = True
    variable_rewrites: dict[str, str] = field(default_factory=lambda: {"$ARGUMENTS": "user-provided arguments"})


class Args(argparse.Namespace):
    src: str
    dest: str | None
    name: str | None
    prefs: str | None
    force: bool
    skip_existing: bool
    no_notes: bool
    no_rewrite: bool


def _codex_home() -> Path:
    return Path(os.environ.get("CODEX_HOME", os.path.expanduser("~/.codex"))).expanduser()


def _default_prefs_path() -> Path:
    # .../skill-manager/scripts/convert-claude-skill.py -> .../skill-manager/references/preferences.json
    return Path(__file__).resolve().parent.parent / "references" / "preferences.json"


def _load_preferences(path: Path | None) -> Preferences:
    prefs_path = path or _default_prefs_path()
    if not prefs_path.exists():
        return Preferences()
    try:
        data = json.loads(prefs_path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001 - surface config issues
        raise ConvertError(f"Failed to read preferences JSON: {prefs_path}") from exc
    if not isinstance(data, dict):
        raise ConvertError(f"Preferences must be a JSON object: {prefs_path}")

    defaults = Preferences()
    language = str(data.get("language", defaults.language))
    shell = str(data.get("shell", defaults.shell))
    insert_codex_notes = bool(data.get("insert_codex_notes", defaults.insert_codex_notes))
    skip_rewrites_in_fenced_code_blocks = bool(
        data.get("skip_rewrites_in_fenced_code_blocks", defaults.skip_rewrites_in_fenced_code_blocks)
    )
    variable_rewrites_raw = data.get("variable_rewrites", defaults.variable_rewrites)
    variable_rewrites: dict[str, str] = {}
    if isinstance(variable_rewrites_raw, dict):
        for key, value in variable_rewrites_raw.items():
            if isinstance(key, str) and isinstance(value, str) and key:
                variable_rewrites[key] = value
    if not variable_rewrites:
        variable_rewrites = defaults.variable_rewrites

    return Preferences(
        language=language,
        shell=shell,
        insert_codex_notes=insert_codex_notes,
        skip_rewrites_in_fenced_code_blocks=skip_rewrites_in_fenced_code_blocks,
        variable_rewrites=variable_rewrites,
    )


def _normalize_newlines(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n")


def _split_frontmatter(skill_md: str) -> tuple[str, str]:
    content = _normalize_newlines(skill_md)
    if not content.startswith("---\n"):
        raise ConvertError("SKILL.md has no YAML frontmatter starting with '---'.")
    match = re.match(r"^---\n(.*?)\n---\n?", content, re.DOTALL)
    if not match:
        raise ConvertError("Invalid YAML frontmatter block in SKILL.md.")
    frontmatter_text = match.group(1)
    body = content[match.end() :]
    return frontmatter_text, body


_KEY_RE = re.compile(r"^([A-Za-z0-9_-]+):(?:\s+(.*)|\s*)$")


def _unquote_yaml_scalar(value: str) -> str:
    raw = value.strip()
    if len(raw) >= 2 and raw[0] == raw[-1] and raw[0] in ("'", '"'):
        quote = raw[0]
        inner = raw[1:-1]
        if quote == "'":
            return inner.replace("''", "'")
        # Minimal escape handling for common sequences in double quotes.
        inner = inner.replace('\\"', '"').replace("\\\\", "\\")
        inner = inner.replace("\\n", "\n").replace("\\t", "\t").replace("\\r", "\r")
        return inner
    return raw


def _parse_top_level_frontmatter(frontmatter_text: str) -> dict[str, str]:
    lines = _normalize_newlines(frontmatter_text).split("\n")
    i = 0
    out: dict[str, str] = {}
    while i < len(lines):
        line = lines[i]
        if not line.strip() or line.lstrip().startswith("#"):
            i += 1
            continue
        if line.startswith((" ", "\t")):
            i += 1
            continue
        match = _KEY_RE.match(line)
        if not match:
            i += 1
            continue
        key = match.group(1)
        rest = (match.group(2) or "").rstrip()
        if rest.startswith("|") or rest.startswith(">"):
            block_lines: list[str] = []
            i += 1
            while i < len(lines):
                nxt = lines[i]
                if nxt.startswith((" ", "\t")):
                    block_lines.append(nxt.lstrip())
                    i += 1
                    continue
                break
            value = "\n".join(block_lines).rstrip()
            if rest.startswith(">"):
                # Fold single newlines into spaces, keep paragraph breaks.
                value = re.sub(r"(?<!\n)\n(?!\n)", " ", value)
            out[key] = value
            continue
        out[key] = _unquote_yaml_scalar(rest)
        i += 1
    return out


def _yaml_quote(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
    return f'"{escaped}"'


def _normalize_skill_name(raw_name: str) -> str:
    name = raw_name.strip().lower()
    name = name.replace("_", "-").replace(" ", "-")
    name = re.sub(r"[^a-z0-9-]+", "-", name)
    name = re.sub(r"-{2,}", "-", name).strip("-")
    if not name:
        raise ConvertError("Unable to derive a valid skill name.")
    return name[:64]


def _rewrite_outside_fences(text: str, replacements: dict[str, str]) -> str:
    content = _normalize_newlines(text)
    lines = content.split("\n")
    in_fence = False
    fence_delim: str | None = None
    out_lines: list[str] = []
    for line in lines:
        stripped = line.lstrip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            delim = stripped[:3]
            if not in_fence:
                in_fence = True
                fence_delim = delim
            elif fence_delim == delim:
                in_fence = False
                fence_delim = None
            out_lines.append(line)
            continue
        if not in_fence:
            for src, dst in replacements.items():
                line = line.replace(src, dst)
        out_lines.append(line)
    return "\n".join(out_lines)


def _insert_notes_after_title(body: str, notes: str) -> str:
    body_norm = _normalize_newlines(body)
    notes_norm = notes.strip("\n")
    if not notes_norm:
        return body_norm

    if "## Codex Notes" in body_norm:
        return body_norm

    match = re.search(r"^# .*(?:\n|$)", body_norm, flags=re.MULTILINE)
    if not match:
        stripped = body_norm.lstrip("\n")
        return f"{notes_norm}\n\n{stripped}"

    title_end = match.end()
    after = body_norm[title_end:]
    blank_match = re.match(r"\n*", after)
    blank_end = blank_match.end() if blank_match else 0
    content_start = title_end + blank_end
    before = body_norm[:title_end].rstrip("\n")
    rest = body_norm[content_start:].lstrip("\n")
    return f"{before}\n\n{notes_norm}\n\n{rest}"


def _format_display_name(skill_name: str) -> str:
    words = [word for word in skill_name.split("-") if word]
    formatted: list[str] = []
    for index, word in enumerate(words):
        lower = word.lower()
        upper = word.upper()
        if upper in ACRONYMS:
            formatted.append(upper)
            continue
        if lower in BRANDS:
            formatted.append(BRANDS[lower])
            continue
        if index > 0 and lower in SMALL_WORDS:
            formatted.append(lower)
            continue
        formatted.append(word.capitalize())
    return " ".join(formatted)


def _generate_short_description(display_name: str) -> str:
    description = f"Help with {display_name} tasks"

    if len(description) < 25:
        description = f"Help with {display_name} tasks and workflows"
    if len(description) < 25:
        description = f"Help with {display_name} tasks with guidance"

    if len(description) > 64:
        description = f"Help with {display_name}"
    if len(description) > 64:
        description = f"{display_name} helper"
    if len(description) > 64:
        description = f"{display_name} tools"
    if len(description) > 64:
        suffix = " helper"
        max_name_length = 64 - len(suffix)
        trimmed = display_name[:max_name_length].rstrip()
        description = f"{trimmed}{suffix}"
    if len(description) > 64:
        description = description[:64].rstrip()

    if len(description) < 25:
        description = f"{description} workflows"
        if len(description) > 64:
            description = description[:64].rstrip()

    return description


def _codex_notes(frontmatter: dict[str, str], prefs: Preferences) -> str:
    arg_hint = frontmatter.get("argument-hint", "").strip()
    removed: list[str] = []
    for key in ("argument-hint", "disable-model-invocation"):
        if key in frontmatter:
            removed.append(key)
    removed_text = ", ".join(removed) if removed else ""

    bullets_en: list[str] = []
    if arg_hint:
        bullets_en.append(f"Expected args: {arg_hint}")
    bullets_en.append("Codex does not inject `$ARGUMENTS`; ask the user for paths/args explicitly.")
    if removed_text:
        bullets_en.append(f"Removed Claude-only frontmatter: {removed_text}")
    if prefs.shell.lower() == "powershell":
        bullets_en.append("On PowerShell, prefer `Get-Command` over `which`.")
    return "## Codex Notes\n" + "\n".join(f"- {b}" for b in bullets_en)


def _write_openai_yaml(skill_dir: Path, skill_name: str, prefs: Preferences) -> None:
    agents_dir = skill_dir / "agents"
    agents_dir.mkdir(parents=True, exist_ok=True)
    output = agents_dir / "openai.yaml"
    if output.exists():
        return

    display_name = _format_display_name(skill_name)
    short_description = _generate_short_description(display_name)
    default_prompt = (
        "Manage or convert this skill. Provide the skill name, source (curated/GitHub/local), and desired action."
    )

    content = "\n".join(
        [
            "interface:",
            f"  display_name: {_yaml_quote(display_name)}",
            f"  short_description: {_yaml_quote(short_description)}",
            f"  default_prompt: {_yaml_quote(default_prompt)}",
            "",
        ]
    )
    output.write_text(content, encoding="utf-8")


def _convert_one_skill(
    src_dir: Path,
    dest_root: Path,
    prefs: Preferences,
    *,
    name_override: str | None,
    force: bool,
    skip_existing: bool,
    no_notes: bool,
    no_rewrite: bool,
) -> tuple[str, Path]:
    skill_md_path = src_dir / "SKILL.md"
    if not skill_md_path.exists():
        raise ConvertError(f"SKILL.md not found: {src_dir}")

    original = skill_md_path.read_text(encoding="utf-8")
    front_text, body = _split_frontmatter(original)
    frontmatter = _parse_top_level_frontmatter(front_text)

    raw_name = name_override or frontmatter.get("name") or src_dir.name
    skill_name = _normalize_skill_name(raw_name)

    raw_desc = frontmatter.get("description", "").strip()
    description = raw_desc or f"Converted from Claude skill: {src_dir.name}"

    if not no_rewrite and prefs.variable_rewrites:
        if prefs.skip_rewrites_in_fenced_code_blocks:
            body = _rewrite_outside_fences(body, prefs.variable_rewrites)
        else:
            for src, dst in prefs.variable_rewrites.items():
                body = body.replace(src, dst)

    if prefs.insert_codex_notes and not no_notes:
        body = _insert_notes_after_title(body, _codex_notes(frontmatter, prefs))

    new_frontmatter = "\n".join(
        [
            "---",
            f"name: {skill_name}",
            f"description: {_yaml_quote(description)}",
            "---",
            "",
        ]
    )
    new_skill_md = new_frontmatter + body.lstrip("\n")
    if not new_skill_md.endswith("\n"):
        new_skill_md += "\n"

    dest_dir = dest_root / skill_name
    if dest_dir.exists():
        if force:
            shutil.rmtree(dest_dir)
        elif skip_existing:
            return skill_name, dest_dir
        else:
            raise ConvertError(f"Destination already exists: {dest_dir}")

    dest_root.mkdir(parents=True, exist_ok=True)

    shutil.copytree(
        src_dir,
        dest_dir,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".DS_Store"),
    )
    (dest_dir / "SKILL.md").write_text(new_skill_md, encoding="utf-8")
    _write_openai_yaml(dest_dir, skill_name, prefs)
    return skill_name, dest_dir


def _discover_skills(src: Path) -> list[Path]:
    if (src / "SKILL.md").is_file():
        return [src]

    skills: list[Path] = []
    for child in src.iterdir():
        if child.is_dir() and (child / "SKILL.md").is_file():
            skills.append(child)
    return sorted(skills)


def _parse_args(argv: list[str]) -> Args:
    parser = argparse.ArgumentParser(description="Convert Claude Code skills to Codex skills.")
    parser.add_argument("--src", required=True, help="Claude skill directory, or a directory containing skills")
    parser.add_argument(
        "--dest",
        help="Destination skills root (default: $CODEX_HOME/skills or ~/.codex/skills)",
    )
    parser.add_argument("--name", help="Override output skill name (single-skill only)")
    parser.add_argument("--prefs", help="Path to preferences JSON (default: references/preferences.json)")
    parser.add_argument("--force", action="store_true", help="Overwrite destination skill directory if it exists")
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="Skip converting skills that already exist in destination",
    )
    parser.add_argument("--no-notes", action="store_true", help="Do not insert Codex notes block")
    parser.add_argument("--no-rewrite", action="store_true", help="Do not rewrite placeholders in body text")
    return parser.parse_args(argv, namespace=Args())


def main(argv: list[str]) -> int:
    args = _parse_args(argv)
    try:
        prefs = _load_preferences(Path(args.prefs).expanduser() if args.prefs else None)
        src = Path(args.src).expanduser().resolve()
        if not src.exists():
            raise ConvertError(f"Source not found: {src}")
        if not src.is_dir():
            raise ConvertError(f"Source is not a directory: {src}")

        dest_root = (
            Path(args.dest).expanduser().resolve()
            if args.dest
            else _codex_home() / "skills"
        )

        skills = _discover_skills(src)
        if not skills:
            raise ConvertError(
                "No skills found. Provide a directory containing SKILL.md, "
                "or a directory whose subfolders each contain SKILL.md."
            )

        if len(skills) > 1 and args.name:
            raise ConvertError("--name can only be used when converting a single skill.")

        converted: list[tuple[str, Path]] = []
        for skill_dir in skills:
            name, out_dir = _convert_one_skill(
                skill_dir,
                dest_root,
                prefs,
                name_override=args.name if len(skills) == 1 else None,
                force=args.force,
                skip_existing=args.skip_existing,
                no_notes=args.no_notes,
                no_rewrite=args.no_rewrite,
            )
            converted.append((name, out_dir))

        for name, out_dir in converted:
            print(f"[OK] {name} -> {out_dir}")
        print("Done. Restart Codex to pick up new skills.")
        return 0
    except ConvertError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
