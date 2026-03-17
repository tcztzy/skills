#!/usr/bin/env python3
"""Audit all installed Codex skills against the shared WSL2 runtime registry."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

SKILL_CREATOR_ROOT = Path.home() / ".codex" / "skills" / ".system" / "skill-creator"
SCRIPT_ROOT = Path(__file__).resolve().parent
for candidate in (SCRIPT_ROOT, SKILL_CREATOR_ROOT):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

from runtime_registry import (  # type: ignore  # noqa: E402
    DOCS_SKILLS,
    DOMAIN_SPECS,
    ML_SKILLS,
    NOTION_SKILLS,
    SCIENCE_SKILLS,
    load_or_probe_registry,
    registry_path,
    resolve_runtime_root,
    runtime_domain_for_skill,
)
from scripts.skill_inventory import discover_skills  # type: ignore  # noqa: E402
from scripts.utils import dump_json, dump_text, ensure_lab_workspace, utc_now_iso  # type: ignore  # noqa: E402

DEFAULT_SKILLS_ROOT = Path.home() / ".codex" / "skills"


def skill_readiness(skill_name: str, registry: dict[str, Any]) -> tuple[str, str, bool, bool]:
    domain = runtime_domain_for_skill(skill_name)
    domains = registry.get("domains", {})
    core = domains.get("core-tools", {}).get("probe", {})
    domain_probe = domains.get(domain, {}).get("probe", {})
    runtime_probe_passed = bool(domain_probe.get("available")) if domain != "core-tools" else True
    if skill_name in DOCS_SKILLS:
        if skill_name == "doc":
            modules = domain_probe.get("modules", {})
            ok = runtime_probe_passed and all(modules.get(key, False) for key in ["docx", "pdf2image", "pypdfium2"]) and core.get("libreoffice_present", False)
            if ok:
                return "ready", "Shared docs runtime and LibreOffice are available", True, False
            return "conditional_ready", "Shared docs runtime or LibreOffice is incomplete", False, False
        if skill_name == "pdf":
            modules = domain_probe.get("modules", {})
            ok = runtime_probe_passed and all(modules.get(key, False) for key in ["reportlab", "pdfplumber", "pypdf", "pypdfium2"])
            if ok:
                return "ready", "Shared docs runtime is available for PDF generation, extraction, and rendering", True, False
            return "conditional_ready", "Shared docs runtime is incomplete for PDF workflows", False, False
        if skill_name == "latex-to-word":
            ok = runtime_probe_passed and core.get("pandoc_present", False)
            if ok:
                return "ready", "Shared docs runtime and Pandoc are available", True, False
            return "conditional_ready", "Pandoc or docs runtime is incomplete", False, False
    if skill_name in SCIENCE_SKILLS:
        if runtime_probe_passed:
            return "ready", "Shared science runtime is available", True, False
        return "conditional_ready", "Shared science runtime is incomplete", False, False
    if skill_name in ML_SKILLS:
        if runtime_probe_passed:
            return "ready", "Shared ML runtime is available", True, False
        return "conditional_ready", "Shared ML runtime is incomplete", False, False
    if skill_name == "gh-fix-ci":
        ok = core.get("gh_present", False) and core.get("gh_authenticated", False)
        return ("ready", "GitHub CLI is installed and authenticated", ok, False) if ok else ("conditional_ready", "GitHub CLI is missing or unauthenticated", False, False)
    if skill_name == "yeet":
        ok = core.get("gh_present", False) and core.get("gh_authenticated", False)
        return ("ready", "GitHub CLI is installed and authenticated; external writes still require explicit consent", ok, False) if ok else ("conditional_ready", "GitHub CLI is missing or unauthenticated", False, False)
    if skill_name in NOTION_SKILLS:
        ok = core.get("notion_mcp_configured", False) and core.get("notion_credentials_present", False) and core.get("rmcp_enabled", False)
        return ("ready", "Notion MCP and credentials are configured globally", ok, False) if ok else ("conditional_ready", "Notion MCP or credentials are incomplete", False, False)
    if skill_name == "screenshot":
        ok = any(core.get("linux_screenshot_tools", {}).values())
        return ("ready", "Linux screenshot backend is available globally", ok, False) if ok else ("env_blocked", "No Linux screenshot backend is installed", False, False)
    if skill_name == "playwright":
        ok = core.get("playwright_present", False) and core.get("playwright_browser_cache_present", False)
        return ("ready", "Playwright CLI and browser cache are available globally", ok, False) if ok else ("conditional_ready", "Playwright CLI or browser cache is incomplete", False, False)
    if skill_name in {"skill-creator", "skill-installer", "skill-manager", "openai-docs"}:
        ok = core.get("codex_present", False)
        return ("ready", "Core Codex tooling is available globally", ok, False) if ok else ("env_blocked", "Codex CLI is missing", False, False)
    return "ready", "No extra runtime beyond core tooling is required", True, False


def write_markdown(payload: dict[str, Any], output_path: Path) -> None:
    lines = [
        "# All Installed Skills Global Runtime Audit",
        "",
        f"- Generated at: {payload['generated_at']}",
        f"- Skills root: `{payload['skills_root']}`",
        f"- Runtime root: `{payload['runtime_root']}`",
        f"- Registry: `{payload['registry_path']}`",
        "",
        "| Skill | Domain | Readiness | Probe | Project-local leak | Reason |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for item in payload["skills"]:
        lines.append(
            f"| `{item['skill_name']}` | `{item['runtime_domain']}` | `{item['readiness_verdict']}` | `{str(item['runtime_probe_passed']).lower()}` | `{str(item['project_local_dependency_leak']).lower()}` | {item['readiness_reason']} |"
        )
    dump_text(output_path, "\n".join(lines) + "\n")


def audit_installed_skills(*, skills_root: Path, workspace_root: Path, runtime_root: str | Path | None = None) -> dict[str, Any]:
    layout = ensure_lab_workspace(workspace_root)
    registry = load_or_probe_registry(runtime_root=runtime_root, install_missing=False)
    skills = discover_skills(skills_root, layout["root"])
    entries = []
    for skill in skills:
        skill_name = skill["skill_name"]
        domain = runtime_domain_for_skill(skill_name)
        verdict, reason, probe_passed, project_leak = skill_readiness(skill_name, registry)
        entries.append({
            "skill_name": skill_name,
            "skill_path": skill["skill_path"],
            "skill_kind": skill.get("skill_kind"),
            "entry_type": skill.get("entry_type"),
            "runtime_domain": domain,
            "runtime_probe_passed": probe_passed,
            "project_local_dependency_leak": project_leak,
            "readiness_verdict": verdict,
            "readiness_reason": reason,
        })
    payload = {
        "generated_at": utc_now_iso(),
        "skills_root": str(skills_root.resolve()),
        "runtime_root": str(resolve_runtime_root(runtime_root)),
        "registry_path": str(registry_path(runtime_root)),
        "summary": {
            "total": len(entries),
            "ready": sum(1 for item in entries if item["readiness_verdict"] == "ready"),
            "conditional_ready": sum(1 for item in entries if item["readiness_verdict"] == "conditional_ready"),
            "env_blocked": sum(1 for item in entries if item["readiness_verdict"] == "env_blocked"),
        },
        "skills": entries,
    }
    report_dir = layout["reports"]
    dump_json(report_dir / "all_installed_runtime_readiness.json", payload)
    write_markdown(payload, report_dir / "all_installed_runtime_readiness.md")
    return payload


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Audit all installed skills against the shared WSL2 runtime registry")
    parser.add_argument("--skills-root", default=str(DEFAULT_SKILLS_ROOT))
    parser.add_argument("--workspace", required=True)
    parser.add_argument("--runtime-root", default=None)
    args = parser.parse_args(argv)
    payload = audit_installed_skills(
        skills_root=Path(args.skills_root).expanduser(),
        workspace_root=Path(args.workspace).expanduser().resolve(),
        runtime_root=args.runtime_root,
    )
    print(json.dumps({
        "summary": payload["summary"],
        "report_json": str(Path(args.workspace).resolve() / "reports" / "all_installed_runtime_readiness.json"),
        "report_md": str(Path(args.workspace).resolve() / "reports" / "all_installed_runtime_readiness.md"),
    }, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
