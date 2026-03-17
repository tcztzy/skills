from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "audit-migrated-skills.py"
SPEC = importlib.util.spec_from_file_location("audit_migrated_skills", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

SKILLS_ROOT = Path.home() / ".codex" / "skills"


class AuditMigratedSkillsTests(unittest.TestCase):
    def fake_env(self, *, gh_authenticated: bool = False, scrot: bool = False, docs_runtime: bool = False, libreoffice: bool = False) -> dict:
        docs_modules = {
            "docx": docs_runtime,
            "pdf2image": docs_runtime,
            "pdfplumber": docs_runtime,
            "pypdf": docs_runtime,
            "reportlab": docs_runtime,
            "pypdfium2": docs_runtime,
            "playwright": False,
        }
        return {
            "python3_present": True,
            "git_present": True,
            "pandoc_present": True,
            "playwright_present": True,
            "playwright_browser_cache_present": True,
            "playwright_mcp_configured": True,
            "gh_present": True,
            "gh_authenticated": gh_authenticated,
            "gh_auth_message": "ok" if gh_authenticated else "not logged in",
            "display": ":0",
            "wayland_display": "wayland-0",
            "linux_screenshot_tools": {
                "scrot": scrot,
                "gnome-screenshot": False,
                "import": False,
            },
            "python_modules": docs_modules,
            "codex_mcp": {"codex_present": True, "configured": True, "servers": [], "stdout": "", "stderr": "", "return_code": 0},
            "notion_mcp_configured": True,
            "notion_credentials_present": True,
            "rmcp_enabled": True,
            "runtime_root": "/tmp/shared-runtimes",
            "runtime_registry_path": "/tmp/shared-runtimes/registry.json",
            "runtime_registry": {
                "domains": {
                    "core-tools": {
                        "probe": {
                            "libreoffice_present": libreoffice,
                        }
                    },
                    "docs-python": {
                        "probe": {
                            "available": docs_runtime,
                            "python": "/tmp/shared-runtimes/docs-python/.venv/bin/python",
                            "modules": docs_modules,
                        }
                    },
                }
            },
        }

    def test_readiness_marks_screenshot_ready_with_scrot(self) -> None:
        readiness = MODULE.readiness_for_skill("screenshot", SKILLS_ROOT / "screenshot", self.fake_env(scrot=True))
        self.assertEqual(readiness["readiness_verdict"], "ready")

    def test_readiness_marks_gh_fix_ci_ready_when_authenticated(self) -> None:
        readiness = MODULE.readiness_for_skill("gh-fix-ci", SKILLS_ROOT / "gh-fix-ci", self.fake_env(gh_authenticated=True))
        self.assertEqual(readiness["readiness_verdict"], "ready")

    def test_readiness_marks_yeet_ready_when_authenticated(self) -> None:
        readiness = MODULE.readiness_for_skill("yeet", SKILLS_ROOT / "yeet", self.fake_env(gh_authenticated=True))
        self.assertEqual(readiness["readiness_verdict"], "ready")

    def test_readiness_marks_doc_ready_with_shared_runtime_and_libreoffice(self) -> None:
        readiness = MODULE.readiness_for_skill("doc", SKILLS_ROOT / "doc", self.fake_env(docs_runtime=True, libreoffice=True))
        self.assertEqual(readiness["readiness_verdict"], "ready")

    def test_readiness_marks_pdf_ready_with_shared_runtime(self) -> None:
        readiness = MODULE.readiness_for_skill("pdf", SKILLS_ROOT / "pdf", self.fake_env(docs_runtime=True, libreoffice=True))
        self.assertEqual(readiness["readiness_verdict"], "ready")

    def test_screenshot_eval_pack_is_executable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            entry = {
                "skill_id": "screenshot",
                "skill_name": "screenshot",
                "skill_path": str(SKILLS_ROOT / "screenshot"),
                "entry_type": "leaf_skill",
            }
            pack = MODULE.ensure_eval_pack_for_skill(entry, Path(tmp), use_bundled_if_available=False)
            self.assertTrue(pack["executable"])
            self.assertTrue(any(eval_item["files"] for eval_item in pack["evals"]))

    def test_doc_eval_pack_is_executable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            entry = {
                "skill_id": "doc",
                "skill_name": "doc",
                "skill_path": str(SKILLS_ROOT / "doc"),
                "entry_type": "leaf_skill",
            }
            pack = MODULE.ensure_eval_pack_for_skill(entry, Path(tmp), use_bundled_if_available=False)
            self.assertTrue(pack["executable"])
            self.assertTrue(any(eval_item["files"] for eval_item in pack["evals"]))
            source_spec = pack["source_spec"]
            first_eval = source_spec["evals"][0]
            second_eval = source_spec["evals"][1]
            self.assertIn("rendered-docx/render-manifest.json", first_eval["must_create"])
            self.assertIn("rerendered-docx/render-manifest.json", second_eval["must_create"])
            self.assertIn("Do not modify files under `.agents/skills/doc/`.", first_eval["workflow_expectations"]["critical_constraints"])
            self.assertIn("Do not replace the bundled render helper with an HTML-only shortcut.", second_eval["workflow_expectations"]["critical_constraints"])

    def test_pdf_eval_pack_is_executable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            entry = {
                "skill_id": "pdf",
                "skill_name": "pdf",
                "skill_path": str(SKILLS_ROOT / "pdf"),
                "entry_type": "leaf_skill",
            }
            pack = MODULE.ensure_eval_pack_for_skill(entry, Path(tmp), use_bundled_if_available=False)
            self.assertTrue(pack["executable"])
            self.assertTrue(any(eval_item["files"] for eval_item in pack["evals"]))

    def test_audit_safe_skips_yeet_when_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp) / "workspace"
            manifest_path = Path(tmp) / "migration_manifest.json"
            manifest_path.write_text(
                json.dumps({
                    "copied_skills": [
                        {
                            "skill_name": "yeet",
                            "source_path": "/mnt/c/Users/huolo/.codex/skills/yeet",
                            "dest_path": str(SKILLS_ROOT / "yeet"),
                        }
                    ]
                }),
                encoding="utf-8",
            )
            with patch.object(MODULE, "probe_environment", return_value=self.fake_env(gh_authenticated=True, scrot=True, docs_runtime=True, libreoffice=True)):
                result = MODULE.audit_skills(
                    manifest_path=manifest_path,
                    workspace_root=workspace,
                    skills_root=SKILLS_ROOT,
                    rerun_skills={"yeet"},
                )
            entry = result["retirement_scan"]["skills"][0]
            self.assertEqual(entry["readiness_verdict"], "ready")
            self.assertEqual(entry["retirement_verdict"], "keep_active")
            self.assertEqual(entry["retirement_reason"], "safe_skip_external_side_effects")


if __name__ == "__main__":
    unittest.main()
