#!/usr/bin/env python3
"""Build suite skills (single entrypoints) by vendoring multiple skills under one folder.

Inputs:
  - references/sources.json
  - references/suites.json

Outputs (default):
  - ~/.codex/skills/huggingface-suite
  - ~/.codex/skills/research-suite
  - ~/.codex/skills/pytorch-lightning

If a destination already exists, it is moved to:
  ~/.codex/skills/_backup/<name>-<timestamp>/
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


class BuildError(Exception):
    pass


@dataclass(frozen=True)
class Source:
    id: str
    repo: str
    ref: str
    restricted: bool
    sync: bool
    license_files: tuple[str, ...]


def _codex_home() -> Path:
    return Path(os.environ.get("CODEX_HOME", os.path.expanduser("~/.codex"))).expanduser()


def _expand_codex_path(raw: str, codex_home: Path) -> Path:
    value = os.path.expandvars(raw.strip())
    norm = value.replace("\\", "/")
    if norm.startswith("~/.codex"):
        suffix = norm[len("~/.codex") :].lstrip("/")
        return (codex_home / suffix).resolve()
    return Path(os.path.expanduser(value)).expanduser().resolve()


def _load_json(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        raise BuildError(f"Failed to read JSON: {path}") from exc
    if not isinstance(data, dict):
        raise BuildError(f"Invalid JSON root (expected object): {path}")
    return data


def _load_sources(skill_manager_dir: Path) -> tuple[Path, dict[str, Source]]:
    sources_json = skill_manager_dir / "references" / "sources.json"
    data = _load_json(sources_json)
    codex_home = _codex_home()
    cache_root_raw = str(data.get("cache_root") or "~/.codex/tmp/skill-sources")
    cache_root = _expand_codex_path(cache_root_raw, codex_home)

    sources_raw = data.get("sources")
    if not isinstance(sources_raw, list):
        raise BuildError(f"Missing or invalid 'sources' list: {sources_json}")

    out: dict[str, Source] = {}
    for item in sources_raw:
        if not isinstance(item, dict):
            continue
        sid = str(item.get("id") or "").strip()
        repo = str(item.get("repo") or "").strip()
        ref = str(item.get("ref") or "main").strip()
        restricted = bool(item.get("restricted", False))
        sync = bool(item.get("sync", True))
        license_files_raw = item.get("license_files") or []
        license_files: list[str] = []
        if isinstance(license_files_raw, list):
            for lf in license_files_raw:
                if isinstance(lf, str) and lf.strip():
                    license_files.append(lf.strip())
        if not sid or not repo:
            continue
        out[sid] = Source(
            id=sid,
            repo=repo,
            ref=ref,
            restricted=restricted,
            sync=sync,
            license_files=tuple(license_files),
        )

    if not out:
        raise BuildError(f"No valid sources found in: {sources_json}")
    return cache_root, out


def _backup_dir(skills_root: Path, name: str) -> Path:
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    return skills_root / "_backup" / f"{name}-{ts}"


def _move_to_backup_if_exists(dest_dir: Path, skills_root: Path) -> None:
    if not dest_dir.exists():
        return
    backup = _backup_dir(skills_root, dest_dir.name)
    backup.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(dest_dir), str(backup))
    print(f"[BACKUP] {dest_dir} -> {backup}")


def _copytree(src: Path, dest: Path) -> None:
    if not src.is_dir():
        raise BuildError(f"Skill path not found: {src}")
    if (src / "SKILL.md").is_file() is False:
        raise BuildError(f"SKILL.md not found: {src}")
    shutil.copytree(
        src,
        dest,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".DS_Store", ".git"),
    )


def _yaml_quote(text: str) -> str:
    escaped = text.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
    return f"\"{escaped}\""


def _write_openai_yaml(skill_dir: Path, *, display_name: str, short_description: str, default_prompt: str) -> None:
    agents_dir = skill_dir / "agents"
    agents_dir.mkdir(parents=True, exist_ok=True)
    out = agents_dir / "openai.yaml"
    content = "\n".join(
        [
            "interface:",
            f"  display_name: {_yaml_quote(display_name)}",
            f"  short_description: {_yaml_quote(short_description)}",
            f"  default_prompt: {_yaml_quote(default_prompt)}",
            "",
        ]
    )
    out.write_text(content, encoding="utf-8")


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


def _parse_frontmatter(skill_md: Path) -> dict[str, str]:
    text = skill_md.read_text(encoding="utf-8", errors="replace").replace("\r\n", "\n").replace("\r", "\n")
    if not text.startswith("---\n"):
        return {}
    match = re.match(r"^---\n(.*?)\n---\n?", text, re.DOTALL)
    if not match:
        return {}
    front = match.group(1)
    out: dict[str, str] = {}
    for line in front.split("\n"):
        m = _KEY_RE.match(line)
        if not m:
            continue
        key = m.group(1)
        rest = (m.group(2) or "").rstrip()
        out[key] = _unquote_yaml_scalar(rest)
    return out


def _suite_skill_md(
    *,
    suite_id: str,
    display_name: str,
    description: str,
    vendor_subdir: str,
    members: list[dict[str, str]],
    source_repo: str,
) -> str:
    lines: list[str] = []
    lines.extend(
        [
            "---",
            f"name: {suite_id}",
            f"description: {_yaml_quote(description)}",
            "---",
            "",
            f"# {display_name}",
            "",
            "## Purpose",
            "- This is a **suite entry skill**: it consolidates related skills behind one entry point and avoids fragmented triggering.",
            f"- Vendored skills live in `vendor/{vendor_subdir}/` and are not triggered independently as top-level skills.",
            "",
        ]
    )

    if suite_id == "huggingface-suite":
        lines.extend(
            [
                "## Recommended routing",
                "- Hub or CLI auth, download/upload, cache, and repo management -> `hugging-face-cli`",
                "- Dataset creation, maintenance, templates, SQL queries, and publishing -> `hugging-face-datasets`",
                "- Writing model evaluation results into model cards or model-index -> `hugging-face-evaluation`",
                "- TRL plus HF Jobs training or alignment, and GGUF conversion -> `hugging-face-model-trainer`",
                "- Experiment metric logging, alerts, and dashboards with Trackio -> `hugging-face-trackio`",
                "- Gradio demos or Blocks UI -> `gradio`",
                "",
            ]
        )
    elif suite_id == "research-suite":
        lines.extend(
            [
                "## Recommended routing",
                "- Paper or report writing, including IMRAD structure, citation style, and reviewer responses -> `scientific-writing`",
                "- Data exploration and quality checks, including EDA reports -> `exploratory-data-analysis`",
                "- Statistical tests, effect sizes, hypothesis testing, and standardized reporting -> `statistical-analysis`",
                "- Journal-grade figures, including multi-panel layouts, significance annotations, and colorblind-safe design -> `scientific-visualization`",
                "",
                "## Important note",
                "- Vendored documentation may contain more prescriptive workflow advice, such as requiring graphical abstracts. This suite treats those suggestions as **optional strategies**, not hard requirements.",
                "",
            ]
        )

    lines.extend(
        [
            "## Included vendored skills",
            "",
            "| Directory | skill.name | Description |",
            "|-----------|------------|-------------|",
        ]
    )
    for m in members:
        dir_name = m.get("dir_name", "")
        skill_name = m.get("skill_name", "") or "-"
        desc = (m.get("description", "") or "").replace("\n", " ").strip()
        desc = desc if desc else "-"
        lines.append(f"| `{dir_name}` | `{skill_name}` | {desc} |")

    lines.extend(
        [
            "",
            "## License and source",
            f"- Upstream repository: `{source_repo}`",
            f"- License or NOTICE files: see the relevant files under `vendor/{vendor_subdir}/` when present.",
            "",
            "## Update or rebuild",
            "- Sync source cache: run `skill-manager/scripts/sync-sources.py --all`",
            "- Rebuild suites: run `skill-manager/scripts/build-suites.py --all`",
            "- Restart Codex after a build to load new or updated skills.",
            "",
        ]
    )
    return "\n".join(lines)


def _copy_license_files(source_root: Path, vendor_source_root: Path, license_files: tuple[str, ...]) -> None:
    for lf in license_files:
        src = source_root / lf
        if src.is_file():
            shutil.copy2(src, vendor_source_root / src.name)


def _build_suite(
    *,
    suite: dict,
    sources: dict[str, Source],
    cache_root: Path,
    skills_root: Path,
) -> None:
    suite_id = str(suite.get("id") or "").strip()
    if not suite_id:
        raise BuildError("Suite is missing 'id'.")
    source_id = str(suite.get("source_id") or "").strip()
    if not source_id:
        raise BuildError(f"Suite '{suite_id}' is missing 'source_id'.")
    if source_id not in sources:
        raise BuildError(f"Unknown source_id for suite '{suite_id}': {source_id}")
    source = sources[source_id]
    if source.restricted:
        raise BuildError(f"Refusing to build from restricted source: {source_id}")

    source_subdir = str(suite.get("source_subdir") or "").strip()
    if not source_subdir:
        raise BuildError(f"Suite '{suite_id}' is missing 'source_subdir'.")
    vendor_subdir = str(suite.get("vendor_subdir") or source_id).strip() or source_id
    members_raw = suite.get("members")
    if not isinstance(members_raw, list) or not members_raw:
        raise BuildError(f"Suite '{suite_id}' has no members.")
    members_list: list[dict[str, str]] = []
    for raw_member in members_raw:
        if isinstance(raw_member, str) and raw_member.strip():
            members_list.append({"source_path": raw_member.strip(), "dest_name": raw_member.strip()})
            continue
        if isinstance(raw_member, dict):
            source_path = str(raw_member.get("source_path") or raw_member.get("id") or "").strip()
            dest_name = str(raw_member.get("dest_name") or source_path).strip()
            if source_path and dest_name:
                members_list.append({"source_path": source_path, "dest_name": dest_name})
    if not members_list:
        raise BuildError(f"Suite '{suite_id}' has no valid members.")

    display_name = str(suite.get("display_name") or suite_id).strip()
    suite_desc = str(suite.get("description") or "").strip() or f"Suite: {suite_id}"

    source_root = cache_root / source_id
    if not source_root.is_dir():
        raise BuildError(f"Missing source cache: {source_root} (run sync-sources.py first)")

    dest_dir = skills_root / suite_id
    _move_to_backup_if_exists(dest_dir, skills_root)
    dest_dir.mkdir(parents=True, exist_ok=True)

    vendor_source_root = dest_dir / "vendor" / vendor_subdir
    vendor_source_root.mkdir(parents=True, exist_ok=True)

    _copy_license_files(source_root, vendor_source_root, source.license_files)

    member_meta: list[dict[str, str]] = []
    for member in members_list:
        source_path = member["source_path"]
        dest_name = member["dest_name"]
        src = source_root / source_subdir / source_path
        dest = vendor_source_root / dest_name
        if not src.is_dir():
            raise BuildError(f"Missing suite member source for '{suite_id}': {src}")
        print(f"[VENDOR] {suite_id}: {source_path} -> {dest_name}")
        _copytree(src, dest)
        fm = _parse_frontmatter(dest / "SKILL.md")
        member_meta.append(
            {
                "dir_name": dest_name,
                "skill_name": fm.get("name", ""),
                "description": fm.get("description", ""),
            }
        )

    (dest_dir / "SKILL.md").write_text(
        _suite_skill_md(
            suite_id=suite_id,
            display_name=display_name,
            description=suite_desc,
            vendor_subdir=vendor_subdir,
            members=member_meta,
            source_repo=f"{source.repo}@{source.ref}",
        ),
        encoding="utf-8",
    )
    _write_openai_yaml(
        dest_dir,
        display_name=display_name,
        short_description=suite_desc,
        default_prompt=(
            "Use this suite entry skill to complete the task. First confirm the goal "
            "(for example Hub, datasets, training, evaluation, visualization, or writing), "
            "then choose the corresponding vendored skill using the suite routing rules."
        ),
    )


def _build_standalone(
    *,
    item: dict,
    sources: dict[str, Source],
    cache_root: Path,
    skills_root: Path,
) -> None:
    skill_id = str(item.get("id") or "").strip()
    if not skill_id:
        raise BuildError("Standalone item is missing 'id'.")
    source_id = str(item.get("source_id") or "").strip()
    if not source_id:
        raise BuildError(f"Standalone '{skill_id}' is missing 'source_id'.")
    if source_id not in sources:
        raise BuildError(f"Unknown source_id for standalone '{skill_id}': {source_id}")
    source = sources[source_id]
    if source.restricted:
        raise BuildError(f"Refusing to build from restricted source: {source_id}")

    source_subdir = str(item.get("source_subdir") or "").strip()
    source_path = str(item.get("source_path") or "").strip()
    if not source_subdir or not source_path:
        raise BuildError(f"Standalone '{skill_id}' is missing 'source_subdir' or 'source_path'.")

    display_name = str(item.get("display_name") or skill_id).strip()
    short_desc = str(item.get("description") or "").strip() or f"Skill: {skill_id}"

    source_root = cache_root / source_id
    if not source_root.is_dir():
        raise BuildError(f"Missing source cache: {source_root} (run sync-sources.py first)")

    src = source_root / source_subdir / source_path
    dest_dir = skills_root / skill_id
    _move_to_backup_if_exists(dest_dir, skills_root)
    print(f"[INSTALL] {skill_id}")
    _copytree(src, dest_dir)

    openai_yaml = dest_dir / "agents" / "openai.yaml"
    if not openai_yaml.exists():
        _write_openai_yaml(
            dest_dir,
            display_name=display_name,
            short_description=short_desc,
            default_prompt="Use this skill for the relevant task. Start by describing your code structure, training goal, and runtime environment.",
        )


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build suite skills from cached source repos.")
    parser.add_argument("--all", action="store_true", help="Build all suites and standalone items.")
    parser.add_argument("--suite", action="append", default=[], help="Build only the given suite id(s).")
    parser.add_argument("--standalone", action="append", default=[], help="Install only the given standalone id(s).")
    parser.add_argument("--skills-root", help="Override skills root (default: $CODEX_HOME/skills)")
    parser.add_argument("--cache-root", help="Override cache root (default from references/sources.json)")
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    skill_manager_dir = Path(__file__).resolve().parent.parent
    suites_json = skill_manager_dir / "references" / "suites.json"
    try:
        cache_root, sources = _load_sources(skill_manager_dir)
        data = _load_json(suites_json)
        args = _parse_args(argv)

        codex_home = _codex_home()
        if args.cache_root:
            cache_root = _expand_codex_path(args.cache_root, codex_home)

        skills_root = codex_home / "skills"
        if args.skills_root:
            skills_root = _expand_codex_path(args.skills_root, codex_home)

        suites = data.get("suites") or []
        standalone = data.get("standalone") or []
        if not isinstance(suites, list) or not isinstance(standalone, list):
            raise BuildError(f"Invalid suites.json structure: {suites_json}")

        selected_suite_ids = [s.strip() for s in (args.suite or []) if s.strip()]
        selected_standalone_ids = [s.strip() for s in (args.standalone or []) if s.strip()]
        if not args.all and not selected_suite_ids and not selected_standalone_ids:
            raise BuildError("Specify --all or --suite/--standalone.")

        if args.all:
            suite_items = suites
            standalone_items = standalone
        else:
            suite_items = [s for s in suites if str(s.get("id") or "").strip() in selected_suite_ids]
            standalone_items = [
                s for s in standalone if str(s.get("id") or "").strip() in selected_standalone_ids
            ]
            missing_suites = sorted(set(selected_suite_ids) - {str(s.get("id") or "").strip() for s in suite_items})
            missing_standalone = sorted(
                set(selected_standalone_ids) - {str(s.get("id") or "").strip() for s in standalone_items}
            )
            if missing_suites:
                raise BuildError(f"Unknown suite id(s): {', '.join(missing_suites)}")
            if missing_standalone:
                raise BuildError(f"Unknown standalone id(s): {', '.join(missing_standalone)}")

        for suite in suite_items:
            _build_suite(suite=suite, sources=sources, cache_root=cache_root, skills_root=skills_root)
        for item in standalone_items:
            _build_standalone(item=item, sources=sources, cache_root=cache_root, skills_root=skills_root)

        print("Done. Restart Codex to pick up new/updated skills.")
        return 0
    except BuildError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
