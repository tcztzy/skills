#!/usr/bin/env python3
"""Validate a Codex skill folder (dependency-free, no PyYAML required)."""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path


MAX_SKILL_NAME_LENGTH = 64
MAX_DESCRIPTION_LENGTH = 1024

ALLOWED_KEYS_DEFAULT = {
    "name",
    "description",
    "license",
    "allowed-tools",
    "metadata",
}


class ValidateError(Exception):
    pass


class Args(argparse.Namespace):
    skill_dir: str
    strict: bool


def _normalize_newlines(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n")


def _split_frontmatter(skill_md: str) -> tuple[str, str]:
    content = _normalize_newlines(skill_md)
    if not content.startswith("---\n"):
        raise ValidateError("No YAML frontmatter found (expected leading '---').")
    match = re.match(r"^---\n(.*?)\n---\n?", content, re.DOTALL)
    if not match:
        raise ValidateError("Invalid YAML frontmatter format.")
    return match.group(1), content[match.end() :]


_KEY_RE = re.compile(r"^([A-Za-z0-9_-]+):(?:\s+(.*)|\s*)$")


def _unquote_yaml_scalar(value: str) -> str:
    raw = value.strip()
    if len(raw) >= 2 and raw[0] == raw[-1] and raw[0] in ("'", '"'):
        quote = raw[0]
        inner = raw[1:-1]
        if quote == "'":
            return inner.replace("''", "'")
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
                value = re.sub(r"(?<!\n)\n(?!\n)", " ", value)
            out[key] = value
            continue
        out[key] = _unquote_yaml_scalar(rest)
        i += 1
    return out


def _validate_name(name: str) -> None:
    if not name:
        raise ValidateError("Missing or empty 'name' in frontmatter.")
    if len(name) > MAX_SKILL_NAME_LENGTH:
        raise ValidateError(
            f"Name is too long ({len(name)}). Maximum is {MAX_SKILL_NAME_LENGTH}."
        )
    if not re.match(r"^[a-z0-9-]+$", name):
        raise ValidateError("Name must be hyphen-case: lowercase letters, digits, hyphens.")
    if name.startswith("-") or name.endswith("-") or "--" in name:
        raise ValidateError("Name cannot start/end with '-' or contain consecutive hyphens.")


def _validate_description(description: str) -> None:
    if description is None:
        raise ValidateError("Missing 'description' in frontmatter.")
    desc = description.strip()
    if "<" in desc or ">" in desc:
        raise ValidateError("Description cannot contain angle brackets (< or >).")
    if len(desc) > MAX_DESCRIPTION_LENGTH:
        raise ValidateError(
            f"Description is too long ({len(desc)}). Maximum is {MAX_DESCRIPTION_LENGTH}."
        )


def validate_skill(skill_dir: str | Path, *, strict: bool = False) -> tuple[bool, str]:
    try:
        skill_dir = Path(os.path.expanduser(str(skill_dir))).resolve()
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.exists():
            raise ValidateError(f"SKILL.md not found: {skill_dir}")
        front_text, _body = _split_frontmatter(skill_md.read_text(encoding="utf-8"))
        frontmatter = _parse_top_level_frontmatter(front_text)

        allowed_keys = {"name", "description"} if strict else ALLOWED_KEYS_DEFAULT
        unexpected = set(frontmatter.keys()) - allowed_keys
        if unexpected:
            unexpected_list = ", ".join(sorted(unexpected))
            allowed_list = ", ".join(sorted(allowed_keys))
            raise ValidateError(
                f"Unexpected key(s) in frontmatter: {unexpected_list}. "
                f"Allowed keys: {allowed_list}."
            )

        _validate_name(frontmatter.get("name", ""))
        _validate_description(frontmatter.get("description", ""))
        return True, "Skill is valid!"
    except ValidateError as exc:
        return False, str(exc)


def _parse_args(argv: list[str]) -> Args:
    parser = argparse.ArgumentParser(description="Validate a Codex skill folder.")
    parser.add_argument("skill_dir", help="Path to the skill directory")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Only allow 'name' and 'description' in SKILL.md frontmatter",
    )
    return parser.parse_args(argv, namespace=Args())


def main(argv: list[str]) -> int:
    args = _parse_args(argv)
    valid, message = validate_skill(args.skill_dir, strict=args.strict)
    print(message)
    return 0 if valid else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
