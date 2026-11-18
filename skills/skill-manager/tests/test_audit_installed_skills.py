from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "audit-installed-skills.py"
SPEC = importlib.util.spec_from_file_location("audit_installed_skills", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class AuditInstalledSkillsTests(unittest.TestCase):
    def fake_registry(self) -> dict:
        return {
            "generated_at": "2026-01-01T00:00:00Z",
            "domains": {
                "core-tools": {
                    "probe": {
                        "available": True,
                        "codex_present": True,
                        "gh_present": True,
                        "gh_authenticated": True,
                        "pandoc_present": True,
                        "scrot_present": True,
                        "playwright_present": True,
                        "playwright_browser_cache_present": True,
                        "libreoffice_present": True,
                        "linux_screenshot_tools": {"scrot": True, "gnome-screenshot": False, "import": False},
                        "notion_mcp_configured": True,
                        "notion_credentials_present": True,
                        "rmcp_enabled": True,
                    }
                },
                "docs-python": {
                    "probe": {
                        "available": True,
                        "modules": {
                            "docx": True,
                            "pdf2image": True,
                            "pdfplumber": True,
                            "pypdf": True,
                            "reportlab": True,
                            "pypdfium2": True,
                        },
                    }
                },
                "science-python": {"probe": {"available": True}},
                "ml-python": {"probe": {"available": True}},
            }
        }

    def test_skill_readiness_uses_shared_domains(self) -> None:
        registry = self.fake_registry()
        del registry["domains"]["docs-python"]
        verdict, _reason, probe, artifact = MODULE.skill_readiness("latex-to-word", registry)
        self.assertEqual(verdict, "ready")
        self.assertTrue(probe)
        self.assertIsNone(artifact)
        registry["domains"]["core-tools"]["probe"]["pandoc_present"] = False
        self.assertEqual(MODULE.skill_readiness("latex-to-word", registry)[0], "env_blocked")
        verdict, _reason, probe, artifact = MODULE.skill_readiness("playwright", registry)
        self.assertEqual(verdict, "ready")
        self.assertTrue(probe)
        self.assertIsNone(artifact)

    def test_audit_installed_skills_writes_summary(self) -> None:
        names = ["latex-to-word", "paper-visualizer", "openai-docs", "skill-manager"]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "skills"
            for name in names:
                folder = root / name
                folder.mkdir(parents=True)
                (folder / "SKILL.md").write_text(f"---\nname: {name}\n---\n", encoding="utf-8")
            with patch.object(MODULE, "build_registry", return_value=self.fake_registry()):
                payload = MODULE.audit_installed_skills(skills_root=root, workspace_root=Path(tmp) / "reports")
        self.assertEqual(payload["summary"]["total"], 4)
        self.assertEqual(payload["summary"]["ready"], 4)
        self.assertEqual(
            {item["runtime_domain"] for item in payload["skills"]},
            {"science-python", "core-tools"},
        )

    def test_live_audit_ignores_stale_cache_and_marks_unmapped_skills(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            runtime = root / "runtimes"
            runtime.mkdir()
            cached = runtime / "registry.json"
            snapshot = json.dumps(self.fake_registry())
            cached.write_text(snapshot, encoding="utf-8")
            for name in ["skill-manager", "new-skill", "typst"]:
                skill = root / "skills" / name
                skill.mkdir(parents=True)
                (skill / "SKILL.md").write_text(f"---\nname: {name}\n---\n", encoding="utf-8")
            with patch.dict(os.environ, {"HOME": tmp, "USERPROFILE": tmp, "PATH": str(root / "no-tools")}):
                payload = MODULE.audit_installed_skills(
                    skills_root=root / "skills", workspace_root=root / "audit", runtime_root=runtime
                )
            by_name = {item["skill_name"]: item for item in payload["skills"]}
            self.assertEqual(by_name["skill-manager"]["readiness_verdict"], "env_blocked")
            self.assertEqual(by_name["new-skill"]["readiness_verdict"], "unverified")
            self.assertIsNone(by_name["new-skill"]["runtime_probe_passed"])
            self.assertIsNone(by_name["new-skill"]["artifact_check"])
            self.assertEqual(by_name["typst"]["readiness_verdict"], "env_blocked")
            self.assertIn("Missing typst", by_name["typst"]["readiness_reason"])
            self.assertIsNone(by_name["typst"]["artifact_check"])
            self.assertEqual(payload["summary"]["unverified"], 1)
            self.assertEqual(cached.read_text(encoding="utf-8"), snapshot)

    def test_typst_rejects_compiler_success_without_pdf(self) -> None:
        def write_text_only(args, *, cwd, **kwargs):
            (cwd / args[-1]).write_bytes(b"no PDF")
            return subprocess.CompletedProcess(args, 0, b"", b"")

        with patch.object(shutil, "which", return_value="typst"), patch.object(subprocess, "run", write_text_only):
            verdict, _, passed, artifact = MODULE.skill_readiness("typst", {})
        self.assertEqual((verdict, passed, artifact), ("env_blocked", False, False))

    @unittest.skipUnless(shutil.which("typst"), "needs a local Typst compiler")
    def test_real_typst_compiler_produces_pdf(self) -> None:
        verdict, reason, passed, artifact = MODULE.skill_readiness("typst", {})
        self.assertEqual((verdict, passed, artifact), ("ready", True, True), reason)

    def test_missing_root_fails_before_writing_reports(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with self.assertRaises(NotADirectoryError):
                MODULE.audit_installed_skills(skills_root=root / "missing", workspace_root=root / "audit")
            self.assertFalse((root / "audit").exists())


if __name__ == "__main__":
    unittest.main()
