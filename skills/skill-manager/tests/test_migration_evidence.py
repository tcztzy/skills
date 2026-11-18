"""Exercise migration reports against local evaluation cases and simulated tool availability."""

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "audit-migrated-skills.py"
SPEC = importlib.util.spec_from_file_location("audit_migrated_skills", SCRIPT)
assert SPEC and SPEC.loader
audit = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit)


class MigrationEvidenceTests(unittest.TestCase):
    def test_preserves_bundled_cases_and_legacy_files_on_rerun(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            skill = root / "migrated"
            (skill / "evals").mkdir(parents=True)
            (skill / "evaluations").mkdir()
            case = {
                "id": 7, "prompt": "Translate the passage.", "expected_output": "A faithful translation.",
                "files": ["passage.txt"], "expectations": ["Retain the comparison."],
            }
            (skill / "evals/evals.json").write_text(json.dumps({"evals": [case]}), encoding="utf-8")
            (skill / "evaluations/old.json").write_text(json.dumps({
                "query": "Explain the result.", "success_criteria": ["Quote the data."],
            }), encoding="utf-8")
            audit.ensure_eval_pack_for_skill(
                {"skill_name": skill.name, "skill_path": str(skill)}, root / "packs",
                use_bundled_if_available=False,
            )
            pack = json.loads((root / "packs/migrated/compiled_evals.json").read_text(encoding="utf-8"))
            native, legacy = pack["evals"]
            self.assertEqual(native, case)
            self.assertNotEqual(native["id"], legacy["id"])
            self.assertEqual(legacy["prompt"], "Explain the result.")
            self.assertEqual(legacy["expected_output"], "Quote the data.")

    def test_ready_blocked_and_external_skills_require_outcome_evidence(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            skills = root / "skills"
            names = ["gh-fix-ci", "latex-to-word", "yeet"]
            for name in names:
                path = skills / name
                path.mkdir(parents=True)
                (path / "SKILL.md").write_text(
                    f"---\nname: {name}\ndescription: Exercise the migration audit.\n---\n", encoding="utf-8",
                )
            suite = skills / "latex-to-word" / "evals"
            suite.mkdir()
            (suite / "evals.json").write_text(json.dumps({
                "evals": [{"id": 1, "prompt": "Convert the manuscript.", "expected_output": "Edited DOCX."}],
            }), encoding="utf-8")
            manifest = root / "manifest.json"
            manifest.write_text(json.dumps({"copied_skills": [{"skill_name": n} for n in names]}), encoding="utf-8")
            env = {
                "gh_present": True, "gh_authenticated": True, "gh_auth_message": "test",
                "git_present": True, "pandoc_present": False,
                "runtime_root": str(root), "runtime_registry_path": str(root / "registry.json"),
            }
            with patch.object(audit, "probe_environment", return_value=env):
                audit.audit_skills(manifest_path=manifest, workspace_root=root / "work", skills_root=skills)
            report = json.loads((root / "work/reports/retirement_scan.json").read_text(encoding="utf-8"))
            generated, blocked, external = report["skills"]
            self.assertTrue(generated["eval_pack_executable"])
            self.assertGreater(generated["eval_case_count"], 0)
            self.assertEqual(blocked["readiness_verdict"], "env_blocked")
            self.assertEqual(blocked["eval_case_count"], 1)
            self.assertEqual(external["eval_case_count"], 0)
            for skill in report["skills"]:
                self.assertEqual(skill["eval_execution_status"], "not_run")
                self.assertEqual(skill["retirement_verdict"], "needs_manual_review")


if __name__ == "__main__":
    unittest.main()
