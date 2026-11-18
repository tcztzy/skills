#!/usr/bin/env python3
"""Audit all installed Codex skills against the shared WSL2 runtime registry."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parent))

from runtime_registry import (  # type: ignore  # noqa: E402
    DOCS_SKILLS,
    ML_SKILLS,
    NOTION_SKILLS,
    SCIENCE_SKILLS,
    build_registry,
    registry_path,
    resolve_runtime_root,
    runtime_domain_for_skill,
)
from skill_inventory import discover_skills  # type: ignore  # noqa: E402
from utils import dump_json, dump_text, ensure_lab_workspace, utc_now_iso  # type: ignore  # noqa: E402

DEFAULT_SKILLS_ROOT = Path.home() / ".codex" / "skills"


def probe_typst() -> tuple[str, str, bool, bool | None]:
    compiler = shutil.which("typst")
    if compiler is None:
        return "env_blocked", "Missing typst compiler on PATH", False, None
    with tempfile.TemporaryDirectory(prefix="typst-probe-") as tmp:
        workdir = Path(tmp)
        (workdir / "sample.typ").write_text("#set document(date: none)\n= Runtime check\n", encoding="utf-8")
        try:
            result = subprocess.run(
                [str(Path(compiler).resolve()), "compile", "sample.typ", "sample.pdf"], cwd=workdir,
                capture_output=True, timeout=30,
            )
            if result.returncode:
                error = result.stderr.decode(errors="replace").strip()[:240]
                return "env_blocked", f"typst compile exited {result.returncode}: {error}", False, False
            pdf = (workdir / "sample.pdf").read_bytes()
        except (OSError, subprocess.TimeoutExpired) as exc:
            return "env_blocked", f"typst compile failed: {exc}", False, False
    if not (pdf.startswith(b"%PDF-") and b"startxref" in pdf and pdf.rstrip().endswith(b"%%EOF")):
        return "env_blocked", "typst compile did not produce a PDF with a header and trailer", False, False
    return "ready", f"typst compiled a sample PDF ({len(pdf)} bytes)", True, True


def skill_readiness(skill_name: str, registry: dict[str, Any]) -> tuple[str, str, bool | None, bool | None]:
    domain = runtime_domain_for_skill(skill_name)
    domains = registry.get("domains", {})
    core = domains.get("core-tools", {}).get("probe", {})
    domain_probe = domains.get(domain, {}).get("probe", {})
    runtime_probe_passed = bool(domain_probe.get("available"))
    if skill_name == "typst":
        return probe_typst()
    if skill_name == "latex-to-word":
        if core.get("pandoc_present"):
            return "ready", "Python and Pandoc are available for preprocessing and conversion", True, None
        return "env_blocked", "Missing pandoc on PATH for DOCX conversion", False, None
    if skill_name in DOCS_SKILLS:
        if skill_name == "doc":
            modules = domain_probe.get("modules", {})
            ok = runtime_probe_passed and all(modules.get(key, False) for key in ["docx", "pdf2image", "pypdfium2"]) and core.get("libreoffice_present", False)
            if ok:
                return "ready", "Shared docs runtime and LibreOffice are available", True, None
            return "conditional_ready", "Shared docs runtime or LibreOffice is incomplete", False, None
        if skill_name == "pdf":
            modules = domain_probe.get("modules", {})
            ok = runtime_probe_passed and all(modules.get(key, False) for key in ["reportlab", "pdfplumber", "pypdf", "pypdfium2"])
            if ok:
                return "ready", "Shared docs runtime is available for PDF generation, extraction, and rendering", True, None
            return "conditional_ready", "Shared docs runtime is incomplete for PDF workflows", False, None
    if skill_name in SCIENCE_SKILLS:
        if runtime_probe_passed:
            return "ready", "Shared science runtime is available", True, None
        return "conditional_ready", "Shared science runtime is incomplete", False, None
    if skill_name in ML_SKILLS:
        if runtime_probe_passed:
            return "ready", "Shared ML runtime is available", True, None
        return "conditional_ready", "Shared ML runtime is incomplete", False, None
    if skill_name == "gh-fix-ci":
        ok = core.get("gh_present", False) and core.get("gh_authenticated", False)
        return ("ready", "GitHub CLI is installed and authenticated", ok, None) if ok else ("conditional_ready", "GitHub CLI is missing or unauthenticated", False, None)
    if skill_name == "yeet":
        ok = core.get("gh_present", False) and core.get("gh_authenticated", False)
        return ("ready", "GitHub CLI is installed and authenticated; external writes still require explicit consent", ok, None) if ok else ("conditional_ready", "GitHub CLI is missing or unauthenticated", False, None)
    if skill_name in NOTION_SKILLS:
        ok = core.get("notion_mcp_configured", False) and core.get("notion_credentials_present", False) and core.get("rmcp_enabled", False)
        return ("ready", "Notion MCP and credentials are configured globally", ok, None) if ok else ("conditional_ready", "Notion MCP or credentials are incomplete", False, None)
    if skill_name == "screenshot":
        ok = any(core.get("linux_screenshot_tools", {}).values())
        return ("ready", "Linux screenshot backend is available globally", ok, None) if ok else ("env_blocked", "No Linux screenshot backend is installed", False, None)
    if skill_name == "playwright":
        ok = core.get("playwright_present", False) and core.get("playwright_browser_cache_present", False)
        return ("ready", "Playwright CLI and browser cache are available globally", ok, None) if ok else ("conditional_ready", "Playwright CLI or browser cache is incomplete", False, None)
    if skill_name in {"skill-creator", "skill-installer", "skill-manager", "openai-docs"}:
        ok = core.get("codex_present", False)
        return ("ready", "Core Codex tooling is available globally", ok, None) if ok else ("env_blocked", "Codex CLI is missing", False, None)
    return "unverified", "No runtime probe is defined for this skill", None, None


def write_markdown(payload: dict[str, Any], output_path: Path) -> None:
    lines = [
        "# All Installed Skills Global Runtime Audit",
        "",
        f"- Generated at: {payload['generated_at']}",
        f"- Skills root: `{payload['skills_root']}`",
        f"- Runtime root: `{payload['runtime_root']}`",
        f"- Live runtime probes started at: {payload['probe_started_at']}",
        "",
        "| Skill | Domain | Readiness | Runtime probe | Artifact check | Reason |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for item in payload["skills"]:
        passed = item["runtime_probe_passed"]
        probe = "untested" if passed is None else str(passed).lower()
        artifact = item["artifact_check"]
        check = "untested" if artifact is None else str(artifact).lower()
        reason = " ".join(item["readiness_reason"].splitlines()).replace("|", "\\|")
        lines.append(
            f"| `{item['skill_name']}` | {item['runtime_domain'] or '—'} | "
            f"{item['readiness_verdict']} | {probe} | {check} | {reason} |"
        )
    dump_text(output_path, "\n".join(lines) + "\n")


def audit_installed_skills(*, skills_root: Path, workspace_root: Path, runtime_root: str | Path | None = None) -> dict[str, Any]:
    if not skills_root.is_dir():
        raise NotADirectoryError(f"Skills root is not a directory: {skills_root}")
    layout = ensure_lab_workspace(workspace_root)
    registry = build_registry(runtime_root=runtime_root, install_missing=False, persist=False)
    skills = discover_skills(skills_root, layout["root"])
    entries = []
    for skill in skills:
        skill_name = skill["skill_name"]
        domain = runtime_domain_for_skill(skill_name)
        verdict, reason, probe_passed, artifact_check = skill_readiness(skill_name, registry)
        entries.append({
            "skill_name": skill_name,
            "skill_path": skill["skill_path"],
            "skill_kind": skill.get("skill_kind"),
            "entry_type": skill.get("entry_type"),
            "runtime_domain": domain if probe_passed is not None else None,
            "runtime_probe_passed": probe_passed,
            "artifact_check": artifact_check,
            "project_local_dependency_leak": None,
            "readiness_verdict": verdict,
            "readiness_reason": reason,
        })
    payload = {
        "generated_at": utc_now_iso(),
        "probe_started_at": registry["generated_at"],
        "skills_root": str(skills_root.resolve()),
        "runtime_root": str(resolve_runtime_root(runtime_root)),
        "registry_path": str(registry_path(runtime_root)),
        "summary": {
            "total": len(entries),
            "unverified": sum(1 for item in entries if item["readiness_verdict"] == "unverified"),
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
    try:
        payload = audit_installed_skills(
            skills_root=Path(args.skills_root).expanduser(),
            workspace_root=Path(args.workspace).expanduser().resolve(),
            runtime_root=args.runtime_root,
        )
    except NotADirectoryError as exc:
        parser.error(str(exc))
    print(json.dumps({
        "summary": payload["summary"],
        "report_json": str(Path(args.workspace).resolve() / "reports" / "all_installed_runtime_readiness.json"),
        "report_md": str(Path(args.workspace).resolve() / "reports" / "all_installed_runtime_readiness.md"),
    }, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
