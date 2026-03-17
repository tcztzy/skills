#!/usr/bin/env python3
"""Run readiness checks and a retirement-style audit for newly migrated Windows skills."""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

SCRIPT_ROOT = Path(__file__).resolve().parent
SKILL_CREATOR_ROOT = Path.home() / ".codex" / "skills" / ".system" / "skill-creator"
for candidate in (SCRIPT_ROOT, SKILL_CREATOR_ROOT):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

from runtime_registry import load_or_probe_registry, registry_path, resolve_runtime_root  # type: ignore  # noqa: E402
from scripts.aggregate_benchmark import generate_benchmark, generate_markdown as generate_benchmark_markdown  # type: ignore  # noqa: E402
from scripts.quick_validate import validate_skill  # type: ignore  # noqa: E402
from scripts.retirement_lab import compare_benchmark_pairs, evaluate_retirement_gate  # type: ignore  # noqa: E402
from scripts.run_task_benchmark import run_benchmark  # type: ignore  # noqa: E402
from scripts.simple_eval_compiler import compile_simple_eval_pack, generate_executable_eval_pack  # type: ignore  # noqa: E402
from scripts.skill_inventory import discover_skills  # type: ignore  # noqa: E402
from scripts.utils import dump_json, dump_text, ensure_lab_workspace, load_json, utc_now_iso  # type: ignore  # noqa: E402
from scripts.workflow_fidelity import build_workflow_oracle  # type: ignore  # noqa: E402

DEFAULT_SKILLS_ROOT = Path.home() / ".codex" / "skills"
GITHUB_SKILLS = {"gh-fix-ci", "yeet"}
NOTION_SKILLS = {
    "notion-knowledge-capture",
    "notion-meeting-intelligence",
    "notion-research-documentation",
    "notion-spec-to-implementation",
}
SAFE_BENCHMARK_SKILLS = {"doc", "pdf", "jupyter-notebook", "latex-to-word", "openai-docs", "playwright", "screenshot", "gh-fix-ci"}
READY_EXTERNAL_WRITE_SKILLS = set(NOTION_SKILLS) | {"yeet"}
REQUIRED_RUN_FILES = ("artifact_isolation.json", "grading.json", "timing.json", "workflow_fidelity.json")
DEFAULT_RERUN_ATTEMPTS = 2


def has_python_module(module_name: str) -> bool:
    return importlib.util.find_spec(module_name) is not None


def command_exists(command: str) -> bool:
    return shutil.which(command) is not None


def run_command(command: list[str], *, timeout: int = 20) -> tuple[int, str, str]:
    completed = subprocess.run(command, capture_output=True, text=True, timeout=timeout, check=False)
    return completed.returncode, completed.stdout.strip(), completed.stderr.strip()


def probe_codex_mcp() -> dict[str, Any]:
    if not command_exists("codex"):
        return {"codex_present": False, "configured": False, "servers": [], "stdout": "", "stderr": "codex missing"}
    rc, stdout, stderr = run_command([
        "codex",
        "-c",
        'model_reasoning_effort="medium"',
        "mcp",
        "list",
    ])
    lines = [line.strip() for line in stdout.splitlines() if line.strip()]
    configured = rc == 0 and any(not line.lower().startswith("no mcp servers") for line in lines)
    return {
        "codex_present": True,
        "configured": configured,
        "servers": lines,
        "stdout": stdout,
        "stderr": stderr,
        "return_code": rc,
    }


def probe_environment(*, runtime_root: str | Path | None = None) -> dict[str, Any]:
    runtime_registry = load_or_probe_registry(runtime_root=runtime_root, install_missing=False)
    core_probe = runtime_registry.get("domains", {}).get("core-tools", {}).get("probe", {})
    docs_probe = runtime_registry.get("domains", {}).get("docs-python", {}).get("probe", {})

    config_path = Path.home() / ".codex" / "config.toml"
    config_text = config_path.read_text(encoding="utf-8") if config_path.exists() else ""
    mcp = probe_codex_mcp()
    notion_configured = any("notion" in line.lower() for line in mcp.get("servers", [])) or bool(core_probe.get("notion_mcp_configured")) or "notion" in config_text.lower()
    playwright_mcp_configured = any("playwright" in line.lower() for line in mcp.get("servers", [])) or bool(core_probe.get("playwright_mcp_configured")) or "playwright" in config_text.lower()
    rmcp_enabled = bool(core_probe.get("rmcp_enabled")) or "rmcp_client" in config_text.lower() or "experimental_use_rmcp_client" in config_text.lower()

    return {
        "python3_present": command_exists("python3"),
        "git_present": command_exists("git"),
        "pandoc_present": bool(core_probe.get("pandoc_present")) or command_exists("pandoc"),
        "playwright_present": bool(core_probe.get("playwright_present")) or command_exists("playwright"),
        "playwright_browser_cache_present": bool(core_probe.get("playwright_browser_cache_present")),
        "playwright_mcp_configured": playwright_mcp_configured,
        "gh_present": bool(core_probe.get("gh_present")) or command_exists("gh"),
        "gh_authenticated": bool(core_probe.get("gh_authenticated")),
        "gh_auth_message": core_probe.get("gh_auth_message", "gh missing"),
        "display": os.environ.get("DISPLAY"),
        "wayland_display": os.environ.get("WAYLAND_DISPLAY"),
        "linux_screenshot_tools": core_probe.get("linux_screenshot_tools", {
            "scrot": command_exists("scrot"),
            "gnome-screenshot": command_exists("gnome-screenshot"),
            "import": command_exists("import"),
        }),
        "python_modules": {
            "docx": bool(docs_probe.get("modules", {}).get("docx")),
            "pdf2image": bool(docs_probe.get("modules", {}).get("pdf2image")),
            "pdfplumber": bool(docs_probe.get("modules", {}).get("pdfplumber")),
            "pypdf": bool(docs_probe.get("modules", {}).get("pypdf")),
            "reportlab": bool(docs_probe.get("modules", {}).get("reportlab")),
            "pypdfium2": bool(docs_probe.get("modules", {}).get("pypdfium2")),
            "playwright": False,
        },
        "codex_mcp": mcp,
        "notion_mcp_configured": notion_configured,
        "notion_credentials_present": bool(core_probe.get("notion_credentials_present")),
        "rmcp_enabled": rmcp_enabled,
        "runtime_root": str(resolve_runtime_root(runtime_root)),
        "runtime_registry_path": str(registry_path(runtime_root)),
        "runtime_registry": runtime_registry,
    }


def readiness_for_skill(skill_name: str, skill_path: Path, env: dict[str, Any]) -> dict[str, Any]:
    valid, message = validate_skill(skill_path)
    checks: dict[str, Any] = {"skill_valid": valid, "validation_message": message}
    docs_modules = env.get("python_modules", {})
    core_probe = env.get("runtime_registry", {}).get("domains", {}).get("core-tools", {}).get("probe", {})
    docs_probe = env.get("runtime_registry", {}).get("domains", {}).get("docs-python", {}).get("probe", {})

    if skill_name == "doc":
        checks.update({
            "runtime_domain": "docs-python",
            "runtime_root": env.get("runtime_root"),
            "runtime_python": docs_probe.get("python"),
            "runtime_available": docs_probe.get("available", False),
            "python_docx": docs_modules.get("docx", False),
            "pdf2image": docs_modules.get("pdf2image", False),
            "pypdfium2": docs_modules.get("pypdfium2", False),
            "soffice_present": core_probe.get("libreoffice_present", False),
        })
        if docs_probe.get("available") and docs_modules.get("docx") and docs_modules.get("pdf2image") and docs_modules.get("pypdfium2") and core_probe.get("libreoffice_present"):
            verdict = "ready"
            reason = "Shared docs runtime and LibreOffice are available for DOCX rendering"
        elif docs_probe.get("python"):
            verdict = "conditional_ready"
            reason = "Shared docs runtime exists, but DOCX visual-render dependencies are still incomplete"
        else:
            verdict = "env_blocked"
            reason = "Shared docs runtime is not bootstrapped yet"
    elif skill_name == "pdf":
        checks.update({
            "runtime_domain": "docs-python",
            "runtime_root": env.get("runtime_root"),
            "runtime_python": docs_probe.get("python"),
            "runtime_available": docs_probe.get("available", False),
            "pdfplumber": docs_modules.get("pdfplumber", False),
            "pypdf": docs_modules.get("pypdf", False),
            "reportlab": docs_modules.get("reportlab", False),
            "pypdfium2": docs_modules.get("pypdfium2", False),
        })
        if docs_probe.get("available") and docs_modules.get("pdfplumber") and docs_modules.get("pypdf") and docs_modules.get("reportlab") and docs_modules.get("pypdfium2"):
            verdict = "ready"
            reason = "Shared docs runtime is available for PDF generation, extraction, and rendering"
        elif docs_probe.get("python"):
            verdict = "conditional_ready"
            reason = "Shared docs runtime exists, but PDF helper libraries are not fully installed"
        else:
            verdict = "env_blocked"
            reason = "Shared docs runtime is not bootstrapped yet"
    elif skill_name == "gh-fix-ci":
        checks.update({
            "gh_present": env["gh_present"],
            "gh_authenticated": env["gh_authenticated"],
            "gh_auth_message": env["gh_auth_message"],
            "git_present": env["git_present"],
        })
        if env["gh_present"] and env["gh_authenticated"]:
            verdict = "ready"
            reason = "GitHub CLI is installed and authenticated for read-only CI inspection workflows"
        elif env["gh_present"]:
            verdict = "conditional_ready"
            reason = "GitHub CLI is installed, but authentication is still required"
        else:
            verdict = "env_blocked"
            reason = "GitHub CLI is not installed in this WSL environment"
    elif skill_name == "yeet":
        checks.update({
            "gh_present": env["gh_present"],
            "gh_authenticated": env["gh_authenticated"],
            "gh_auth_message": env["gh_auth_message"],
            "git_present": env["git_present"],
        })
        if env["gh_present"] and env["gh_authenticated"]:
            verdict = "ready"
            reason = "GitHub CLI is installed and authenticated; this audit will still skip real push/PR side effects"
        elif env["gh_present"]:
            verdict = "conditional_ready"
            reason = "GitHub CLI is installed, but this push/PR skill still requires explicit authenticated user intent"
        else:
            verdict = "env_blocked"
            reason = "GitHub CLI is not installed in this WSL environment"
    elif skill_name in NOTION_SKILLS:
        checks.update({
            "codex_mcp_configured": env["codex_mcp"]["configured"],
            "notion_mcp_configured": env["notion_mcp_configured"],
            "rmcp_enabled": env["rmcp_enabled"],
            "notion_credentials_present": env["notion_credentials_present"],
        })
        if env["notion_mcp_configured"] and env["rmcp_enabled"] and env["notion_credentials_present"]:
            verdict = "ready"
            reason = "Notion MCP is configured and OAuth credentials are present"
        elif env["notion_mcp_configured"]:
            verdict = "conditional_ready"
            reason = "Notion MCP is configured, but OAuth authentication is still required"
        else:
            verdict = "env_blocked"
            reason = "Notion MCP is not configured in this WSL Codex environment"
    elif skill_name == "playwright":
        checks.update({
            "playwright_cli_present": env["playwright_present"],
            "python_playwright": env["python_modules"]["playwright"],
            "playwright_mcp_configured": env["playwright_mcp_configured"],
            "playwright_browser_cache_present": env["playwright_browser_cache_present"],
        })
        if env["playwright_present"] and env["playwright_browser_cache_present"]:
            verdict = "ready"
            reason = "Playwright CLI and browser runtime are installed locally"
        elif env["playwright_mcp_configured"]:
            verdict = "conditional_ready"
            reason = "Playwright MCP is configured, but the local CLI/browser runtime is incomplete"
        else:
            verdict = "env_blocked"
            reason = "Playwright runtime is not installed in this WSL environment"
    elif skill_name == "screenshot":
        checks.update({
            "display": env["display"],
            "wayland_display": env["wayland_display"],
            **env["linux_screenshot_tools"],
        })
        if any(bool(value) for value in env["linux_screenshot_tools"].values()):
            verdict = "ready"
            reason = "Linux screenshot backend available"
        else:
            verdict = "env_blocked"
            reason = "No supported Linux screenshot utility is installed, so live capture is blocked"
    elif skill_name == "jupyter-notebook":
        checks.update({
            "python3_present": env["python3_present"],
            "script_present": (skill_path / "scripts" / "new_notebook.py").exists(),
            "template_count": len(list((skill_path / "assets").glob("*.ipynb"))),
        })
        verdict = "ready"
        reason = "Python, notebook scaffolding script, and templates are available locally"
    elif skill_name == "latex-to-word":
        checks.update({"pandoc_present": env["pandoc_present"], "runtime_domain": "docs-python"})
        verdict = "ready" if env["pandoc_present"] else "env_blocked"
        reason = "Pandoc is installed locally" if env["pandoc_present"] else "Pandoc is missing"
    elif skill_name == "openai-docs":
        checks.update({"skill_valid": valid})
        verdict = "ready"
        reason = "This skill is guidance-first and does not require extra local runtimes to benchmark safely"
    else:
        checks.update({"skill_valid": valid})
        verdict = "ready" if valid else "env_blocked"
        reason = "Default readiness applied"

    if not valid:
        verdict = "env_blocked"
        reason = f"skill validation failed: {message}"

    return {
        "readiness_verdict": verdict,
        "readiness_reason": reason,
        "checks": checks,
    }

def load_bundled_evaluations(skill_path: Path, skill_name: str) -> dict[str, Any] | None:
    eval_dir = skill_path / "evaluations"
    if not eval_dir.is_dir():
        return None
    evals = []
    for index, path in enumerate(sorted(eval_dir.glob("*.json")), start=1):
        payload = load_json(path)
        prompt = payload.get("query") or payload.get("prompt") or f"Use ${skill_name} on a representative task from {path.stem}."
        expected_bits = list(payload.get("success_criteria", [])) + list(payload.get("expected_behavior", []))
        evals.append({
            "id": index,
            "name": payload.get("name", path.stem),
            "mode": "task",
            "prompt": prompt,
            "expected_output": " ".join(expected_bits[:8]) or payload.get("name", path.stem),
            "workflow_expectations": {
                "required_steps": list(payload.get("expected_behavior", []))[:8],
                "required_artifacts": [],
                "critical_constraints": list(payload.get("success_criteria", []))[:8],
            },
        })
    return {
        "skill_name": skill_name,
        "status": "bundled_draft",
        "executable": False,
        "notes": ["Converted from bundled skill evaluations for audit context; not auto-benchmarked in this run."],
        "evals": evals,
    }


def write_fixture_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    dump_text(path, content)


def build_screenshot_eval_pack(*, skill_name: str, pack_dir: Path) -> dict[str, Any]:
    fixtures_dir = pack_dir / "fixtures"
    write_fixture_file(
        fixtures_dir / "start_test_window.sh",
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        "title=\"${1:-Codex Screenshot Audit}\"\n"
        "body=\"${2:-Codex Screenshot Audit Window}\"\n"
        "timeout 45 xmessage -center -title \"$title\" \"$body\" >/dev/null 2>&1 &\n"
        "echo $! > xmessage.pid\n"
        "sleep 2\n",
    )
    (fixtures_dir / "start_test_window.sh").chmod(0o755)
    payload = {
        "skill_name": skill_name,
        "status": "auto_generated",
        "executable": True,
        "generated_by": "skill_manager_specialized_pack",
        "notes": [
            "Uses a controlled xmessage window so the audit does not capture the user's real desktop.",
        ],
        "evals": [
            {
                "id": 1,
                "name": "capture-controlled-active-window",
                "mode": "task",
                "files": ["fixtures/start_test_window.sh"],
                "prompt": (
                    f"Use ${skill_name} to capture a controlled test window instead of the real desktop. "
                    "Run `bash fixtures/start_test_window.sh 'Codex Screenshot Audit' 'Codex Screenshot Audit Window'`, "
                    "then use the bundled helper at `.agents/skills/screenshot/scripts/take_screenshot.py` with `--active-window --path captured-active.png`. "
                    "Create `capture-note.md` that records the saved path and the window title `Codex Screenshot Audit`, then mention `captured-active.png` in the final message. "
                    "After capture, stop the test window with `kill $(cat xmessage.pid)` if it is still running."
                ),
                "expected_output": "Creates a screenshot file for the controlled test window and reports the saved path.",
                "must_create": ["captured-active.png", "capture-note.md"],
                "must_include": ["captured-active.png"],
                "file_must_include": [
                    {"path": "capture-note.md", "substring": "captured-active.png"},
                    {"path": "capture-note.md", "substring": "Codex Screenshot Audit"},
                ],
                "workflow_expectations": {
                    "required_steps": [
                        "Create the controlled test window instead of capturing the user's real desktop.",
                        "Use the bundled screenshot helper to capture the active window.",
                        "Report the saved screenshot path.",
                    ],
                    "required_artifacts": ["captured-active.png", "capture-note.md"],
                    "critical_constraints": [
                        "Do not capture unrelated desktop content.",
                    ],
                },
            },
            {
                "id": 2,
                "name": "capture-controlled-window-with-boundary",
                "mode": "task",
                "files": ["fixtures/start_test_window.sh"],
                "prompt": (
                    f"Use ${skill_name} to capture another controlled test window. "
                    "Run `bash fixtures/start_test_window.sh 'Codex Screenshot Audit Boundary' 'Boundary Window'`, "
                    "capture the active window with the bundled helper to `captures/boundary-window.png`, and create `captures/summary.md`. "
                    "In `captures/summary.md`, include the saved path, the title `Codex Screenshot Audit Boundary`, and explicitly say OCR/annotation is out of scope for this screenshot skill. "
                    "Mention `captures/boundary-window.png` in the final message, then stop the test window."
                ),
                "expected_output": "Captures the controlled window to the requested path and states the skill boundary clearly.",
                "must_create": ["captures/boundary-window.png", "captures/summary.md"],
                "must_include": ["captures/boundary-window.png"],
                "file_must_include": [
                    {"path": "captures/summary.md", "substring": "captures/boundary-window.png"},
                    {"path": "captures/summary.md", "substring": "Codex Screenshot Audit Boundary"},
                    {"path": "captures/summary.md", "substring": "out of scope"},
                ],
                "workflow_expectations": {
                    "required_steps": [
                        "Create the controlled test window.",
                        "Use the bundled screenshot helper to capture the active window to the explicit path.",
                        "State the screenshot skill boundary without pretending to do OCR or annotation.",
                    ],
                    "required_artifacts": ["captures/boundary-window.png", "captures/summary.md"],
                    "critical_constraints": [
                        "Do not capture unrelated desktop content.",
                        "Do not pretend the screenshot skill performs OCR or annotation.",
                    ],
                },
            },
        ],
    }
    dump_json(pack_dir / "simple_eval_spec.json", payload)
    compiled = compile_simple_eval_pack(payload, model=None, use_model=False)
    dump_json(pack_dir / "compiled_evals.json", compiled)
    return compiled


def build_gh_fix_ci_eval_pack(*, skill_name: str, pack_dir: Path) -> dict[str, Any]:
    fixtures_dir = pack_dir / "fixtures"
    gha_dir = fixtures_dir / "github-actions"
    external_dir = fixtures_dir / "external"
    dump_json(
        gha_dir / "checks.json",
        [
            {
                "name": "tests / unit (ubuntu-latest)",
                "state": "completed",
                "conclusion": "failure",
                "detailsUrl": "https://github.com/acme/widgets/actions/runs/123456789/job/987654321",
                "startedAt": "2026-03-08T15:00:00Z",
                "completedAt": "2026-03-08T15:05:00Z",
            }
        ],
    )
    dump_json(
        gha_dir / "run_123456789.json",
        {
            "conclusion": "failure",
            "status": "completed",
            "workflowName": "CI",
            "name": "tests / unit",
            "event": "pull_request",
            "headBranch": "codex/fix-ci",
            "headSha": "abcdef1234567890",
            "url": "https://github.com/acme/widgets/actions/runs/123456789",
        },
    )
    write_fixture_file(
        gha_dir / "job_987654321.log",
        "Run python -m pytest\n"
        "============================= test session starts =============================\n"
        "E   ModuleNotFoundError: No module named 'yaml'\n"
        "FAILED tests/test_config.py::test_load_defaults - ModuleNotFoundError: No module named 'yaml'\n",
    )
    dump_json(
        external_dir / "checks.json",
        [
            {
                "name": "buildkite / integration",
                "state": "failure",
                "detailsUrl": "https://buildkite.com/acme/widgets/builds/99",
                "startedAt": "2026-03-08T15:10:00Z",
                "completedAt": "2026-03-08T15:11:00Z",
            }
        ],
    )
    payload = {
        "skill_name": skill_name,
        "status": "auto_generated",
        "executable": True,
        "generated_by": "skill_manager_specialized_pack",
        "notes": [
            "Uses local fixtures so the benchmark stays read-only and deterministic.",
        ],
        "evals": [
            {
                "id": 1,
                "name": "triage-github-actions-fixture",
                "mode": "task",
                "files": [
                    "fixtures/github-actions/checks.json",
                    "fixtures/github-actions/run_123456789.json",
                    "fixtures/github-actions/job_987654321.log",
                ],
                "prompt": (
                    f"Use ${skill_name} to inspect a failing GitHub Actions PR check from local fixtures only. "
                    "Run the bundled script `.agents/skills/gh-fix-ci/scripts/inspect_pr_checks.py` with `--fixture-dir fixtures/github-actions --pr 123 --json > pr-checks.json`, "
                    "then create `fix-plan.md` summarizing the failing check name, an actionable log snippet, and a concise fix plan. "
                    "Explicitly say no implementation should happen before approval, and mention `fix-plan.md` in the final message."
                ),
                "expected_output": "Creates a triage file with the failing check summary and a fix plan, without implementing changes.",
                "must_create": ["pr-checks.json", "fix-plan.md"],
                "must_include": ["fix-plan.md"],
                "file_must_include": [
                    {"path": "pr-checks.json", "substring": "tests / unit (ubuntu-latest)"},
                    {"path": "fix-plan.md", "substring": "tests / unit (ubuntu-latest)"},
                    {"path": "fix-plan.md", "substring": "ModuleNotFoundError: No module named 'yaml'"},
                    {"path": "fix-plan.md", "substring": "approval"},
                ],
                "workflow_expectations": {
                    "required_steps": [
                        "Use the bundled inspect_pr_checks.py helper against the provided fixture data.",
                        "Summarize the failing GitHub Actions check and actionable log snippet.",
                        "Draft a fix plan without implementing changes.",
                    ],
                    "required_artifacts": ["pr-checks.json", "fix-plan.md"],
                    "critical_constraints": [
                        "Do not implement code changes before explicit approval.",
                    ],
                },
            },
            {
                "id": 2,
                "name": "report-external-check-fixture",
                "mode": "task",
                "files": ["fixtures/external/checks.json"],
                "prompt": (
                    f"Use ${skill_name} to inspect an external CI failure from local fixtures only. "
                    "Run the bundled script `.agents/skills/gh-fix-ci/scripts/inspect_pr_checks.py` with `--fixture-dir fixtures/external --pr 124 --json > external-checks.json`, "
                    "then create `external-summary.md` that marks the failing check as external/out of scope and reports only the details URL. "
                    "Do not claim GitHub Actions logs were fetched, and mention `external-summary.md` in the final message."
                ),
                "expected_output": "Creates a summary that labels the failing check external and reports only the details URL.",
                "must_create": ["external-checks.json", "external-summary.md"],
                "must_include": ["external-summary.md"],
                "file_must_include": [
                    {"path": "external-checks.json", "substring": "buildkite / integration"},
                    {"path": "external-summary.md", "substring": "external"},
                    {"path": "external-summary.md", "substring": "https://buildkite.com/acme/widgets/builds/99"},
                ],
                "workflow_expectations": {
                    "required_steps": [
                        "Use the bundled inspect_pr_checks.py helper against the provided fixture data.",
                        "Identify that the failing check is external to GitHub Actions.",
                        "Report only the details URL instead of pretending external logs were fetched.",
                    ],
                    "required_artifacts": ["external-checks.json", "external-summary.md"],
                    "critical_constraints": [
                        "Do not pretend Buildkite or other external providers were inspected directly.",
                    ],
                },
            },
        ],
    }
    dump_json(pack_dir / "simple_eval_spec.json", payload)
    compiled = compile_simple_eval_pack(payload, model=None, use_model=False)
    dump_json(pack_dir / "compiled_evals.json", compiled)
    return compiled


def build_doc_eval_pack(*, skill_name: str, pack_dir: Path) -> dict[str, Any]:
    fixtures_dir = pack_dir / "fixtures"
    write_fixture_file(
        fixtures_dir / "create_sample_docx.py",
        """from pathlib import Path
import sys
from docx import Document

target = Path(sys.argv[1])
target.parent.mkdir(parents=True, exist_ok=True)
doc = Document()
doc.add_heading('Codex DOCX Audit', level=1)
doc.add_paragraph('This document exists only for the controlled skill audit.')
table = doc.add_table(rows=2, cols=2)
table.cell(0, 0).text = 'Column A'
table.cell(0, 1).text = 'Column B'
table.cell(1, 0).text = 'Alpha'
table.cell(1, 1).text = 'Beta'
doc.save(target)
""",
    )
    write_fixture_file(
        fixtures_dir / "update_sample_docx.py",
        """from pathlib import Path
import sys
from docx import Document

target = Path(sys.argv[1])
doc = Document(target)
doc.add_paragraph('Boundary update for the controlled audit document.')
doc.save(target)
""",
    )
    for script_name in ["create_sample_docx.py", "update_sample_docx.py"]:
        (fixtures_dir / script_name).chmod(0o755)
    payload = {
        "skill_name": skill_name,
        "status": "auto_generated",
        "executable": True,
        "generated_by": "skill_manager_specialized_pack",
        "notes": [
            "Uses a controlled DOCX fixture and the bundled render helper through the shared docs runtime.",
        ],
        "evals": [
            {
                "id": 1,
                "name": "render-controlled-docx",
                "mode": "task",
                "files": ["fixtures/create_sample_docx.py"],
                "prompt": (
                    f"Use ${skill_name} to complete a controlled DOCX render handoff without improvising new tooling. "
                    "Run `.agents/skills/doc/scripts/use_docs_runtime.sh fixtures/create_sample_docx.py sample.docx`, "
                    "then render it with `.agents/skills/doc/scripts/use_docs_runtime.sh .agents/skills/doc/scripts/render_docx.py sample.docx --output_dir rendered-docx`. "
                    "Read `rendered-docx/render-manifest.json` and create `doc-review.md` with these exact fields: "
                    "`render_path: rendered-docx/page-1.png`, `render_backend: <value from manifest>`, "
                    "`checkpoint_title: Codex DOCX Audit`, `checkpoint_table_header: Column A | Column B`. "
                    "If the manifest says `structured-fallback`, add `fidelity_note: structured fallback confirms controlled DOCX content only, not full LibreOffice layout fidelity`. "
                    "Do not modify any file under `.agents/skills/doc/` and do not replace the bundled renderer with an HTML-only shortcut. Mention `rendered-docx/page-1.png` in the final message."
                ),
                "expected_output": "Creates a controlled DOCX fixture, renders it with the bundled helper, records the render backend, and writes a deterministic review handoff note.",
                "must_create": ["sample.docx", "rendered-docx/page-1.png", "rendered-docx/render-manifest.json", "doc-review.md"],
                "must_include": ["rendered-docx/page-1.png"],
                "file_must_include": [
                    {"path": "rendered-docx/render-manifest.json", "substring": "render_backend"},
                    {"path": "doc-review.md", "substring": "render_path: rendered-docx/page-1.png"},
                    {"path": "doc-review.md", "substring": "render_backend:"},
                    {"path": "doc-review.md", "substring": "checkpoint_title: Codex DOCX Audit"},
                    {"path": "doc-review.md", "substring": "checkpoint_table_header: Column A | Column B"},
                ],
                "workflow_expectations": {
                    "required_steps": [
                        "Use the shared docs runtime launcher.",
                        "Create a controlled DOCX fixture.",
                        "Render the DOCX with the bundled helper.",
                        "Record the render backend and deterministic review checkpoints.",
                    ],
                    "required_artifacts": ["sample.docx", "rendered-docx/page-1.png", "rendered-docx/render-manifest.json", "doc-review.md"],
                    "critical_constraints": [
                        "Do not modify files under `.agents/skills/doc/`.",
                        "Do not replace the bundled render helper with an HTML-only shortcut.",
                        "If render_backend is structured-fallback, do not claim full LibreOffice layout fidelity.",
                    ],
                },
            },
            {
                "id": 2,
                "name": "doc-boundary-and-rerender",
                "mode": "task",
                "files": ["fixtures/create_sample_docx.py", "fixtures/update_sample_docx.py"],
                "prompt": (
                    f"Use ${skill_name} on a controlled DOCX task that also requests one unsupported extra. "
                    "Run `.agents/skills/doc/scripts/use_docs_runtime.sh fixtures/create_sample_docx.py sample.docx`, "
                    "then `.agents/skills/doc/scripts/use_docs_runtime.sh fixtures/update_sample_docx.py sample.docx`, "
                    "then rerender with `.agents/skills/doc/scripts/use_docs_runtime.sh .agents/skills/doc/scripts/render_docx.py sample.docx --output_dir rerendered-docx`. "
                    "Read `rerendered-docx/render-manifest.json` and create `doc-boundary.md` with these exact fields: "
                    "`render_path: rerendered-docx/page-1.png`, `render_backend: <value from manifest>`, "
                    "`scope_boundary: Google Slides conversion is out of scope for this skill`, "
                    "`update_note: Boundary update for the controlled audit document.`. "
                    "If the manifest says `structured-fallback`, add `fidelity_note: structured fallback confirms controlled DOCX content only, not full LibreOffice layout fidelity`. "
                    "Do not modify any file under `.agents/skills/doc/` and do not replace the bundled renderer with an HTML-only shortcut. Mention `rerendered-docx/page-1.png` in the final message."
                ),
                "expected_output": "Rerenders the updated DOCX, records the render backend, and clearly refuses the unsupported extra instead of pretending to cover it.",
                "must_create": ["sample.docx", "rerendered-docx/page-1.png", "rerendered-docx/render-manifest.json", "doc-boundary.md"],
                "must_include": ["rerendered-docx/page-1.png"],
                "file_must_include": [
                    {"path": "rerendered-docx/render-manifest.json", "substring": "render_backend"},
                    {"path": "doc-boundary.md", "substring": "render_path: rerendered-docx/page-1.png"},
                    {"path": "doc-boundary.md", "substring": "render_backend:"},
                    {"path": "doc-boundary.md", "substring": "scope_boundary: Google Slides conversion is out of scope for this skill"},
                    {"path": "doc-boundary.md", "substring": "update_note: Boundary update for the controlled audit document."},
                ],
                "workflow_expectations": {
                    "required_steps": [
                        "Create and update the controlled DOCX fixture through the shared docs runtime.",
                        "Rerender the DOCX after the edit with the bundled helper.",
                        "State the unsupported extra explicitly instead of pretending the skill covers it.",
                        "Record the rerender backend in the boundary note.",
                    ],
                    "required_artifacts": ["sample.docx", "rerendered-docx/page-1.png", "rerendered-docx/render-manifest.json", "doc-boundary.md"],
                    "critical_constraints": [
                        "Do not fabricate support for the unsupported extra.",
                        "Do not modify files under `.agents/skills/doc/`.",
                        "Do not replace the bundled render helper with an HTML-only shortcut.",
                        "If render_backend is structured-fallback, do not claim full LibreOffice layout fidelity.",
                    ],
                },
            },
        ],
    }
    dump_json(pack_dir / "simple_eval_spec.json", payload)
    compiled = compile_simple_eval_pack(payload, model=None, use_model=False)
    dump_json(pack_dir / "compiled_evals.json", compiled)
    return compiled


def build_pdf_eval_pack(*, skill_name: str, pack_dir: Path) -> dict[str, Any]:
    fixtures_dir = pack_dir / "fixtures"
    write_fixture_file(
        fixtures_dir / "create_sample_pdf.py",
        """from pathlib import Path
import sys
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

target = Path(sys.argv[1])
target.parent.mkdir(parents=True, exist_ok=True)
pdf = canvas.Canvas(str(target), pagesize=letter)
pdf.setTitle('Codex PDF Audit')
pdf.drawString(72, 720, 'Codex PDF Audit Document')
pdf.drawString(72, 690, 'This PDF exists only for the controlled skill audit.')
pdf.drawString(72, 660, 'Layout fidelity must be checked from a rendered page, not text extraction alone.')
pdf.save()
""",
    )
    write_fixture_file(
        fixtures_dir / "extract_pdf_text.py",
        """from pathlib import Path
import sys
import pdfplumber

source = Path(sys.argv[1])
target = Path(sys.argv[2])
target.parent.mkdir(parents=True, exist_ok=True)
with pdfplumber.open(source) as pdf:
    text = '
'.join((page.extract_text() or '') for page in pdf.pages)
target.write_text(text, encoding='utf-8')
""",
    )
    for script_name in ["create_sample_pdf.py", "extract_pdf_text.py"]:
        (fixtures_dir / script_name).chmod(0o755)
    payload = {
        "skill_name": skill_name,
        "status": "auto_generated",
        "executable": True,
        "generated_by": "skill_manager_specialized_pack",
        "notes": [
            "Uses a controlled PDF fixture and the bundled render helper through the shared docs runtime.",
        ],
        "evals": [
            {
                "id": 1,
                "name": "render-controlled-pdf",
                "mode": "task",
                "files": ["fixtures/create_sample_pdf.py"],
                "prompt": (
                    f"Use ${skill_name} to create and visually verify a controlled PDF fixture. "
                    "Run `.agents/skills/pdf/scripts/use_docs_runtime.sh fixtures/create_sample_pdf.py sample.pdf`, "
                    "then render it with `.agents/skills/pdf/scripts/use_docs_runtime.sh .agents/skills/pdf/scripts/render_pdf.py sample.pdf --output_dir rendered-pdf`. "
                    "Create `pdf-review.md` that records `rendered-pdf/page-1.png` and one concrete visual check you performed, then mention `rendered-pdf/page-1.png` in the final message."
                ),
                "expected_output": "Creates a controlled PDF fixture, renders it to PNG pages, and records a visual review note.",
                "must_create": ["sample.pdf", "rendered-pdf/page-1.png", "pdf-review.md"],
                "must_include": ["rendered-pdf/page-1.png"],
                "file_must_include": [
                    {"path": "pdf-review.md", "substring": "rendered-pdf/page-1.png"},
                    {"path": "pdf-review.md", "substring": "visual"},
                ],
                "workflow_expectations": {
                    "required_steps": [
                        "Use the shared docs runtime launcher.",
                        "Create a controlled PDF fixture.",
                        "Render the PDF visually with the bundled helper.",
                        "Record at least one visual review conclusion.",
                    ],
                    "required_artifacts": ["sample.pdf", "rendered-pdf/page-1.png", "pdf-review.md"],
                    "critical_constraints": [
                        "Do not claim visual review without rendering the PDF.",
                    ],
                },
            },
            {
                "id": 2,
                "name": "extract-text-with-layout-boundary",
                "mode": "task",
                "files": ["fixtures/create_sample_pdf.py", "fixtures/extract_pdf_text.py"],
                "prompt": (
                    f"Use ${skill_name} for a controlled PDF task that also requires a boundary note. "
                    "Run `.agents/skills/pdf/scripts/use_docs_runtime.sh fixtures/create_sample_pdf.py sample.pdf`, "
                    "render it with `.agents/skills/pdf/scripts/use_docs_runtime.sh .agents/skills/pdf/scripts/render_pdf.py sample.pdf --output_dir rerendered-pdf`, "
                    "then extract text with `.agents/skills/pdf/scripts/use_docs_runtime.sh fixtures/extract_pdf_text.py sample.pdf extracted.txt`. "
                    "Create `pdf-boundary.md` that references `rerendered-pdf/page-1.png`, `extracted.txt`, and explicitly says text extraction does not prove layout fidelity. Mention `rerendered-pdf/page-1.png` in the final message."
                ),
                "expected_output": "Renders the PDF, extracts text, and clearly states that text extraction is not a substitute for layout fidelity.",
                "must_create": ["sample.pdf", "rerendered-pdf/page-1.png", "extracted.txt", "pdf-boundary.md"],
                "must_include": ["rerendered-pdf/page-1.png"],
                "file_must_include": [
                    {"path": "pdf-boundary.md", "substring": "rerendered-pdf/page-1.png"},
                    {"path": "pdf-boundary.md", "substring": "extracted.txt"},
                    {"path": "pdf-boundary.md", "substring": "does not prove layout fidelity"},
                ],
                "workflow_expectations": {
                    "required_steps": [
                        "Create the controlled PDF fixture through the shared docs runtime.",
                        "Render the PDF visually.",
                        "Extract text separately and explain the layout-fidelity boundary.",
                    ],
                    "required_artifacts": ["sample.pdf", "rerendered-pdf/page-1.png", "extracted.txt", "pdf-boundary.md"],
                    "critical_constraints": [
                        "Do not claim text extraction alone proves visual fidelity.",
                    ],
                },
            },
        ],
    }
    dump_json(pack_dir / "simple_eval_spec.json", payload)
    compiled = compile_simple_eval_pack(payload, model=None, use_model=False)
    dump_json(pack_dir / "compiled_evals.json", compiled)
    return compiled


def build_specialized_eval_pack(skill_entry: dict[str, Any], pack_dir: Path) -> dict[str, Any] | None:
    skill_name = skill_entry["skill_name"]
    if skill_name == "doc":
        return build_doc_eval_pack(skill_name=skill_name, pack_dir=pack_dir)
    if skill_name == "pdf":
        return build_pdf_eval_pack(skill_name=skill_name, pack_dir=pack_dir)
    if skill_name == "screenshot":
        return build_screenshot_eval_pack(skill_name=skill_name, pack_dir=pack_dir)
    if skill_name == "gh-fix-ci":
        return build_gh_fix_ci_eval_pack(skill_name=skill_name, pack_dir=pack_dir)
    return None


def ensure_eval_pack_for_skill(skill_entry: dict[str, Any], workspace_root: Path, *, use_bundled_if_available: bool = True) -> dict[str, Any]:
    skill_id = skill_entry["skill_id"]
    pack_dir = workspace_root / "eval-packs" / skill_id
    pack_dir.mkdir(parents=True, exist_ok=True)
    compiled_path = pack_dir / "compiled_evals.json"

    skill_path = Path(skill_entry["skill_path"]).resolve()
    simple_path = pack_dir / "simple_eval_spec.json"
    bundled = load_bundled_evaluations(skill_path, skill_entry["skill_name"]) if use_bundled_if_available else None
    if bundled is not None:
        dump_json(pack_dir / "bundled_evaluations_simple_eval_spec.json", bundled)

    specialized = build_specialized_eval_pack(skill_entry, pack_dir)
    if specialized is not None:
        return specialized

    if compiled_path.exists():
        return load_json(compiled_path)

    if skill_entry["skill_name"] in SAFE_BENCHMARK_SKILLS:
        simple_payload = generate_executable_eval_pack(skill_path, entry_type=skill_entry["entry_type"])
        dump_json(simple_path, simple_payload)
        compiled = compile_simple_eval_pack(simple_payload, model=None, use_model=False)
        dump_json(compiled_path, compiled)
        return compiled

    if bundled is not None:
        return bundled

    draft_payload = generate_executable_eval_pack(skill_path, entry_type=skill_entry["entry_type"])
    draft_payload["status"] = "draft"
    draft_payload["executable"] = False
    dump_json(pack_dir / "draft_simple_eval_spec.json", draft_payload)
    return draft_payload


def summarize_run_summary(run_summary: dict[str, Any], config_name: str) -> dict[str, Any] | None:
    stats = run_summary.get(config_name)
    if not stats:
        return None
    return {
        "pass_rate_mean": stats.get("pass_rate", {}).get("mean"),
        "fidelity_pass_rate_mean": stats.get("fidelity_pass_rate", {}).get("mean"),
        "artifact_isolation_passed": stats.get("artifact_isolation_passed"),
        "time_seconds_median": stats.get("time_seconds", {}).get("median"),
        "tokens_median": stats.get("tokens", {}).get("median"),
        "freeform_shortcut_rate_mean": stats.get("freeform_shortcut_rate", {}).get("mean"),
    }


def write_markdown_report(payload: dict[str, Any], output_path: Path) -> None:
    lines = [
        "# Windows → WSL Skill Migration Audit",
        "",
        f"- Generated at: {payload['generated_at']}",
        f"- Workspace: `{payload['workspace']}`",
        f"- Migrated skills audited: {len(payload['skills'])}",
        "",
        "| Skill | Readiness | Retirement | Notes |",
        "| --- | --- | --- | --- |",
    ]
    for item in payload["skills"]:
        retirement = item.get("retirement_verdict") or item.get("skipped_reason") or "n/a"
        note = item.get("retirement_reason") or item.get("readiness_reason") or ""
        lines.append(f"| `{item['skill_name']}` | `{item['readiness_verdict']}` | `{retirement}` | {note} |")
    dump_text(output_path, "\n".join(lines) + "\n")


def build_base_report(skill_name: str, source_path: str | None, dest_path: str | None, readiness: dict[str, Any], oracle: dict[str, Any]) -> dict[str, Any]:
    return {
        "skill_name": skill_name,
        "source_path": source_path,
        "dest_path": dest_path,
        "readiness_verdict": readiness["readiness_verdict"],
        "readiness_reason": readiness["readiness_reason"],
        "artifact_isolation_passed": None,
        "benchmark_summary": None,
        "comparator_summary": None,
        "workflow_fidelity_summary": {
            "truth_source_used": oracle.get("truth_source_used"),
            "workflow_truth_sufficient": oracle.get("workflow_truth_sufficient"),
            "fidelity_scope": "eval",
        },
    }


def iteration_number(iteration_dir: Path) -> int:
    try:
        return int(iteration_dir.name.split("-")[-1])
    except (ValueError, IndexError):
        return -1


def list_iteration_dirs(skill_name: str, workspace_root: Path) -> list[Path]:
    root = workspace_root / "runs" / skill_name / "benchmark" / f"{skill_name}-workspace"
    return sorted([path for path in root.glob("iteration-*") if path.is_dir()], key=iteration_number)


def collect_iteration_health(iteration_dir: Path, *, runs_per_config: int) -> dict[str, Any]:
    eval_dirs = sorted([path for path in iteration_dir.glob("eval-*") if path.is_dir()], key=lambda path: path.name)
    missing_artifacts: list[str] = []
    leak_paths: list[str] = []
    error_runs: list[dict[str, str]] = []
    timeout_runs: list[dict[str, str]] = []

    for eval_dir in eval_dirs:
        for config_name in ("with_skill", "without_skill"):
            for run_number in range(1, runs_per_config + 1):
                run_dir = eval_dir / config_name / f"run-{run_number}"
                if not run_dir.is_dir():
                    missing_artifacts.append(str(run_dir.relative_to(iteration_dir)))
                    continue
                for filename in REQUIRED_RUN_FILES:
                    path = run_dir / filename
                    if not path.exists():
                        missing_artifacts.append(str(path.relative_to(iteration_dir)))
                artifact_file = run_dir / "artifact_isolation.json"
                if artifact_file.exists():
                    payload = load_json(artifact_file)
                    if payload.get("artifact_leakage_detected"):
                        leak_paths.append(str(artifact_file.relative_to(iteration_dir)))
                stderr_file = run_dir / "stderr.txt"
                if stderr_file.exists():
                    text = stderr_file.read_text(encoding="utf-8", errors="replace").strip()
                    if "codex exec failed" in text:
                        summary = text.splitlines()[0][:400]
                        error_runs.append({"run_dir": str(run_dir.relative_to(iteration_dir)), "message": summary})
                        if "exit code 124" in text or "timed out" in text.lower() or "Timeout" in text:
                            timeout_runs.append({"run_dir": str(run_dir.relative_to(iteration_dir)), "message": summary})

    benchmark_exists = (iteration_dir / "benchmark.json").exists()
    complete = benchmark_exists and not missing_artifacts and not leak_paths
    return {
        "iteration_dir": str(iteration_dir),
        "iteration_name": iteration_dir.name,
        "benchmark_exists": benchmark_exists,
        "eval_count": len(eval_dirs),
        "missing_artifacts": missing_artifacts,
        "artifact_leakage_paths": leak_paths,
        "error_runs": error_runs,
        "timeout_runs": timeout_runs,
        "complete": complete,
    }


def find_latest_complete_iteration(skill_name: str, workspace_root: Path, *, runs_per_config: int) -> tuple[Path | None, dict[str, Any] | None]:
    for iteration_dir in reversed(list_iteration_dirs(skill_name, workspace_root)):
        health = collect_iteration_health(iteration_dir, runs_per_config=runs_per_config)
        if health["complete"]:
            return iteration_dir, health
    return None, None


def latest_iteration(skill_name: str, workspace_root: Path) -> Path | None:
    iterations = list_iteration_dirs(skill_name, workspace_root)
    return iterations[-1] if iterations else None


def ensure_iteration_aggregate(skill_name: str, skill_path: Path, iteration_dir: Path, *, judge_model: str | None = None) -> tuple[dict[str, Any], dict[str, Any]]:
    benchmark = generate_benchmark(iteration_dir, skill_name, str(skill_path))
    dump_json(iteration_dir / "benchmark.json", benchmark)
    dump_text(iteration_dir / "benchmark.md", generate_benchmark_markdown(benchmark))
    comparator = compare_benchmark_pairs(iteration_dir, model=judge_model)
    return benchmark, comparator


def build_ready_report_from_iteration(
    *,
    skill_entry: dict[str, Any],
    base_report: dict[str, Any],
    iteration_dir: Path,
    iteration_health: dict[str, Any],
    oracle: dict[str, Any],
    judge_model: str | None,
) -> dict[str, Any]:
    skill_name = skill_entry["skill_name"]
    skill_path = Path(skill_entry["skill_path"]).resolve()
    benchmark, comparator = ensure_iteration_aggregate(skill_name, skill_path, iteration_dir, judge_model=judge_model)
    gate = evaluate_retirement_gate(skill_entry, benchmark, comparator["summary"], oracle)
    report = dict(base_report)
    report.update({
        "artifact_isolation_passed": benchmark.get("metadata", {}).get("artifact_isolation_passed"),
        "benchmark_summary": {
            "metadata": {
                **benchmark.get("metadata", {}),
                "selected_iteration_dir": str(iteration_dir),
                "selected_iteration_name": iteration_dir.name,
                "selected_iteration_complete": iteration_health.get("complete", False),
            },
            "with_skill": summarize_run_summary(benchmark.get("run_summary", {}), "with_skill"),
            "without_skill": summarize_run_summary(benchmark.get("run_summary", {}), "without_skill"),
        },
        "comparator_summary": comparator.get("summary"),
        "workflow_fidelity_summary": {
            "truth_source_used": oracle.get("truth_source_used"),
            "workflow_truth_sufficient": oracle.get("workflow_truth_sufficient"),
            "fidelity_scope": benchmark.get("metadata", {}).get("fidelity_scope", "eval"),
        },
        "retirement_verdict": gate["retirement_verdict"],
        "retirement_reason": gate["retirement_reason"],
        "gate_checks": gate.get("gate_checks", {}),
    })
    return report


def build_incomplete_ready_report(
    *,
    base_report: dict[str, Any],
    attempts: list[dict[str, Any]],
    oracle: dict[str, Any],
    latest_complete_iteration_dir: Path | None,
) -> dict[str, Any]:
    report = dict(base_report)
    report.update({
        "artifact_isolation_passed": False,
        "benchmark_summary": {
            "status": "benchmark_incomplete_or_flaky",
            "attempt_count": len(attempts),
            "attempted_iterations": attempts,
            "latest_complete_iteration_available": str(latest_complete_iteration_dir) if latest_complete_iteration_dir else None,
        },
        "comparator_summary": {
            "status": "not_available",
            "reason": "benchmark_incomplete_or_flaky",
        },
        "workflow_fidelity_summary": {
            "truth_source_used": oracle.get("truth_source_used"),
            "workflow_truth_sufficient": oracle.get("workflow_truth_sufficient"),
            "fidelity_scope": "eval",
        },
        "retirement_verdict": "keep_active",
        "retirement_reason": "benchmark_incomplete_or_flaky",
    })
    return report


def rerun_ready_skill(
    *,
    skill_entry: dict[str, Any],
    eval_pack: dict[str, Any],
    layout: dict[str, Path],
    oracle: dict[str, Any],
    base_report: dict[str, Any],
    model: str | None,
    judge_model: str | None,
    num_workers: int,
    runs_per_config: int,
    timeout: int,
    max_attempts: int,
) -> dict[str, Any]:
    skill_name = skill_entry["skill_name"]
    skill_path = Path(skill_entry["skill_path"]).resolve()
    benchmark_root = layout["runs"] / skill_entry["skill_id"] / "benchmark"
    latest_complete_before, _ = find_latest_complete_iteration(skill_name, layout["root"], runs_per_config=runs_per_config)
    attempts: list[dict[str, Any]] = []

    for _ in range(max_attempts):
        benchmark_run = run_benchmark(
            eval_set=eval_pack["evals"],
            skill_path=skill_path,
            workspace_root=benchmark_root,
            runs_per_config=runs_per_config,
            model=model,
            judge_model=judge_model,
            timeout=timeout,
            num_workers=num_workers,
            eval_source_root=layout["root"] / "eval-packs" / skill_entry["skill_id"],
            workflow_oracle=oracle,
            truth_source_used=oracle.get("truth_source_used", "skill_files"),
        )
        iteration_dir = Path(benchmark_run["iteration_dir"])
        try:
            ensure_iteration_aggregate(skill_name, skill_path, iteration_dir, judge_model=judge_model)
            aggregate_error = None
        except Exception as exc:  # pragma: no cover - defensive guard for partial iterations
            aggregate_error = str(exc)
        health = collect_iteration_health(iteration_dir, runs_per_config=runs_per_config)
        if aggregate_error:
            health["aggregate_error"] = aggregate_error
            health["complete"] = False
        attempts.append(health)
        if health["complete"]:
            return build_ready_report_from_iteration(
                skill_entry=skill_entry,
                base_report=base_report,
                iteration_dir=iteration_dir,
                iteration_health=health,
                oracle=oracle,
                judge_model=judge_model,
            )

    return build_incomplete_ready_report(
        base_report=base_report,
        attempts=attempts,
        oracle=oracle,
        latest_complete_iteration_dir=latest_complete_before,
    )


def rebuild_existing_ready_report(
    *,
    skill_entry: dict[str, Any],
    base_report: dict[str, Any],
    layout: dict[str, Path],
    oracle: dict[str, Any],
    judge_model: str | None,
    runs_per_config: int,
) -> dict[str, Any]:
    iteration_dir, health = find_latest_complete_iteration(skill_entry["skill_name"], layout["root"], runs_per_config=runs_per_config)
    if iteration_dir is None or health is None:
        return build_incomplete_ready_report(
            base_report=base_report,
            attempts=[],
            oracle=oracle,
            latest_complete_iteration_dir=None,
        )
    return build_ready_report_from_iteration(
        skill_entry=skill_entry,
        base_report=base_report,
        iteration_dir=iteration_dir,
        iteration_health=health,
        oracle=oracle,
        judge_model=judge_model,
    )


def audit_skills(
    *,
    manifest_path: Path,
    workspace_root: Path,
    skills_root: Path,
    model: str | None = None,
    judge_model: str | None = None,
    num_workers: int = 2,
    runs_per_config: int = 1,
    timeout: int = 120,
    rerun_skills: set[str] | None = None,
    max_rerun_attempts: int = DEFAULT_RERUN_ATTEMPTS,
    runtime_root: str | Path | None = None,
) -> dict[str, Any]:
    layout = ensure_lab_workspace(workspace_root)
    manifest = load_json(manifest_path)
    migrated_names = [item["skill_name"] for item in manifest.get("copied_skills", [])]
    migrated_paths = {item["skill_name"]: item["dest_path"] for item in manifest.get("copied_skills", [])}
    source_paths = {item["skill_name"]: item["source_path"] for item in manifest.get("copied_skills", [])}

    full_catalog = discover_skills(skills_root, layout["root"])
    selected = [entry for entry in full_catalog if entry["skill_name"] in migrated_names]
    selected.sort(key=lambda item: migrated_names.index(item["skill_name"]))
    rerun_targets = set(rerun_skills) if rerun_skills is not None else {item["skill_name"] for item in selected if item["skill_name"] in SAFE_BENCHMARK_SKILLS}

    post_catalog = {
        "generated_at": utc_now_iso(),
        "workspace": str(layout["root"]),
        "skills_root": str(skills_root.resolve()),
        "migration_manifest": str(manifest_path.resolve()),
        "rerun_targets": sorted(rerun_targets),
        "skills": selected,
    }
    dump_json(layout["root"] / "post_migration_catalog.json", post_catalog)

    env = probe_environment(runtime_root=runtime_root)
    readiness_entries = []
    retirement_entries = []

    for skill_entry in selected:
        skill_name = skill_entry["skill_name"]
        skill_path = Path(skill_entry["skill_path"]).resolve()
        readiness = readiness_for_skill(skill_name, skill_path, env)
        eval_pack = ensure_eval_pack_for_skill(skill_entry, layout["root"])
        oracle = build_workflow_oracle(skill_path, None, model=judge_model, use_model=False)
        oracle_path = layout["runs"] / skill_entry["skill_id"] / "oracle.json"
        dump_json(oracle_path, oracle)

        readiness_item = {
            "skill_name": skill_name,
            "source_path": source_paths.get(skill_name),
            "dest_path": migrated_paths.get(skill_name),
            **readiness,
            "eval_pack_status": eval_pack.get("status", skill_entry.get("eval_pack_status", "missing")),
            "eval_pack_executable": bool(eval_pack.get("executable", False)),
            "oracle_path": str(oracle_path),
        }
        readiness_entries.append(readiness_item)

        base_report = build_base_report(skill_name, source_paths.get(skill_name), migrated_paths.get(skill_name), readiness, oracle)

        if readiness["readiness_verdict"] != "ready":
            base_report["skipped_reason"] = f"readiness_{readiness['readiness_verdict']}"
            retirement_entries.append(base_report)
            continue

        if skill_name in READY_EXTERNAL_WRITE_SKILLS:
            base_report.update({
                "benchmark_summary": {
                    "status": "safe_skip_external_side_effects",
                    "reason": "Environment is ready, but this audit does not perform real external writes to third-party systems.",
                },
                "comparator_summary": {
                    "status": "not_available",
                    "reason": "safe_skip_external_side_effects",
                },
                "retirement_verdict": "keep_active",
                "retirement_reason": "safe_skip_external_side_effects",
                "skipped_reason": "safe_skip_external_side_effects",
            })
            retirement_entries.append(base_report)
            continue

        if not eval_pack.get("executable", False):
            base_report["retirement_verdict"] = "needs_eval_authoring"
            base_report["retirement_reason"] = "missing_or_non_executable_eval_pack"
            base_report["skipped_reason"] = "non_executable_eval_pack"
            retirement_entries.append(base_report)
            continue

        if skill_name in rerun_targets:
            ready_report = rerun_ready_skill(
                skill_entry=skill_entry,
                eval_pack=eval_pack,
                layout=layout,
                oracle=oracle,
                base_report=base_report,
                model=model,
                judge_model=judge_model,
                num_workers=num_workers,
                runs_per_config=runs_per_config,
                timeout=timeout,
                max_attempts=max_rerun_attempts,
            )
        else:
            ready_report = rebuild_existing_ready_report(
                skill_entry=skill_entry,
                base_report=base_report,
                layout=layout,
                oracle=oracle,
                judge_model=judge_model,
                runs_per_config=runs_per_config,
            )
        retirement_entries.append(ready_report)

    readiness_payload = {
        "generated_at": utc_now_iso(),
        "workspace": str(layout["root"]),
        "environment": env,
        "skills": readiness_entries,
    }
    dump_json(layout["root"] / "readiness_report.json", readiness_payload)

    retirement_payload = {
        "generated_at": utc_now_iso(),
        "workspace": str(layout["root"]),
        "migration_manifest": str(manifest_path.resolve()),
        "rerun_targets": sorted(rerun_targets),
        "summary": {
            "total": len(retirement_entries),
            "ready": sum(1 for item in retirement_entries if item["readiness_verdict"] == "ready"),
            "conditional_ready": sum(1 for item in retirement_entries if item["readiness_verdict"] == "conditional_ready"),
            "env_blocked": sum(1 for item in retirement_entries if item["readiness_verdict"] == "env_blocked"),
            "retire_recommended": sum(1 for item in retirement_entries if item.get("retirement_verdict") == "retire_recommended"),
            "keep_active": sum(1 for item in retirement_entries if item.get("retirement_verdict") == "keep_active"),
            "needs_eval_authoring": sum(1 for item in retirement_entries if item.get("retirement_verdict") == "needs_eval_authoring"),
            "skipped": sum(1 for item in retirement_entries if item.get("skipped_reason")),
        },
        "skills": retirement_entries,
    }
    dump_json(layout["reports"] / "retirement_scan.json", retirement_payload)
    write_markdown_report(retirement_payload, layout["reports"] / "retirement_scan.md")
    return {
        "post_catalog": post_catalog,
        "readiness_report": readiness_payload,
        "retirement_scan": retirement_payload,
    }


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Audit newly migrated Windows Codex skills inside WSL")
    parser.add_argument("--manifest", required=True, help="Path to migration_manifest.json")
    parser.add_argument("--workspace", default=None, help="Workspace root (defaults to manifest directory)")
    parser.add_argument("--skills-root", default=str(DEFAULT_SKILLS_ROOT), help="WSL skills root")
    parser.add_argument("--skill", action="append", default=None, help="Ready skill(s) to rerun; repeatable. Report still covers all migrated skills.")
    parser.add_argument("--model", default=None)
    parser.add_argument("--judge-model", default=None)
    parser.add_argument("--num-workers", type=int, default=2)
    parser.add_argument("--runs-per-config", type=int, default=1)
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("--max-rerun-attempts", type=int, default=DEFAULT_RERUN_ATTEMPTS)
    parser.add_argument("--runtime-root", default=None)
    args = parser.parse_args(argv)

    manifest = Path(args.manifest).expanduser().resolve()
    workspace = Path(args.workspace).expanduser().resolve() if args.workspace else manifest.parent.resolve()
    payload = audit_skills(
        manifest_path=manifest,
        workspace_root=workspace,
        skills_root=Path(args.skills_root).expanduser(),
        model=args.model,
        judge_model=args.judge_model,
        num_workers=args.num_workers,
        runs_per_config=args.runs_per_config,
        timeout=args.timeout,
        rerun_skills=set(args.skill) if args.skill else None,
        max_rerun_attempts=args.max_rerun_attempts,
        runtime_root=args.runtime_root,
    )
    print(json.dumps({
        "workspace": str(workspace),
        "post_migration_catalog": str(workspace / "post_migration_catalog.json"),
        "readiness_report": str(workspace / "readiness_report.json"),
        "retirement_scan": str(workspace / "reports" / "retirement_scan.json"),
        "retirement_markdown": str(workspace / "reports" / "retirement_scan.md"),
        "summary": payload["retirement_scan"]["summary"],
    }, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
