from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "audit-installed-skills.py"
SPEC = importlib.util.spec_from_file_location("audit_installed_skills", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

SKILLS_ROOT = Path.home() / ".codex" / "skills"


class AuditInstalledSkillsTests(unittest.TestCase):
    def fake_registry(self) -> dict:
        return {
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
        verdict, _reason, probe, leak = MODULE.skill_readiness("doc", registry)
        self.assertEqual(verdict, "ready")
        self.assertTrue(probe)
        self.assertFalse(leak)
        verdict, _reason, probe, leak = MODULE.skill_readiness("gradio", registry)
        self.assertEqual(verdict, "ready")
        self.assertTrue(probe)
        self.assertFalse(leak)

    def test_audit_installed_skills_writes_summary(self) -> None:
        fake_skills = [
            {"skill_name": "doc", "skill_path": str(SKILLS_ROOT / "doc"), "skill_kind": "top_level", "entry_type": "leaf_skill"},
            {"skill_name": "gradio", "skill_path": str(SKILLS_ROOT / "huggingface-suite/vendor/huggingface-skills/gradio"), "skill_kind": "vendored", "entry_type": "leaf_skill"},
            {"skill_name": "skill-manager", "skill_path": str(SKILLS_ROOT / "skill-manager"), "skill_kind": "top_level", "entry_type": "leaf_skill"},
            {"skill_name": "screenshot", "skill_path": str(SKILLS_ROOT / "screenshot"), "skill_kind": "top_level", "entry_type": "leaf_skill"},
        ]
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(MODULE, "load_or_probe_registry", return_value=self.fake_registry()), patch.object(MODULE, "discover_skills", return_value=fake_skills):
                payload = MODULE.audit_installed_skills(skills_root=SKILLS_ROOT, workspace_root=Path(tmp))
        self.assertEqual(payload["summary"]["total"], 4)
        self.assertEqual(payload["summary"]["ready"], 4)
        self.assertEqual({item["runtime_domain"] for item in payload["skills"]}, {"docs-python", "ml-python", "core-tools"})


if __name__ == "__main__":
    unittest.main()
