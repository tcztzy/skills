from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "inspect_pr_checks.py"


class InspectPrChecksFixtureTests(unittest.TestCase):
    def test_fixture_mode_reports_github_actions_failure(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fixture_dir = Path(tmp)
            (fixture_dir / "checks.json").write_text(
                json.dumps([
                    {
                        "name": "tests / unit (ubuntu-latest)",
                        "state": "completed",
                        "conclusion": "failure",
                        "detailsUrl": "https://github.com/acme/widgets/actions/runs/123456789/job/987654321",
                    }
                ]),
                encoding="utf-8",
            )
            (fixture_dir / "run_123456789.json").write_text(
                json.dumps({
                    "workflowName": "CI",
                    "conclusion": "failure",
                    "status": "completed",
                    "headBranch": "codex/fix-ci",
                    "headSha": "abcdef1234567890",
                    "url": "https://github.com/acme/widgets/actions/runs/123456789",
                }),
                encoding="utf-8",
            )
            (fixture_dir / "job_987654321.log").write_text(
                "Run python -m pytest\n"
                "E   ModuleNotFoundError: No module named 'yaml'\n"
                "FAILED tests/test_config.py::test_load_defaults - ModuleNotFoundError: No module named 'yaml'\n",
                encoding="utf-8",
            )
            result = subprocess.run(
                [sys.executable, str(SCRIPT), "--fixture-dir", str(fixture_dir), "--pr", "123", "--json"],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 1, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["pr"], "123")
            self.assertEqual(payload["results"][0]["status"], "ok")
            self.assertIn("ModuleNotFoundError", payload["results"][0]["logSnippet"])
            self.assertEqual(payload["results"][0]["run"]["workflowName"], "CI")

    def test_fixture_mode_marks_external_checks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fixture_dir = Path(tmp)
            (fixture_dir / "checks.json").write_text(
                json.dumps([
                    {
                        "name": "buildkite / integration",
                        "state": "failure",
                        "detailsUrl": "https://buildkite.com/acme/widgets/builds/99",
                    }
                ]),
                encoding="utf-8",
            )
            result = subprocess.run(
                [sys.executable, str(SCRIPT), "--fixture-dir", str(fixture_dir), "--pr", "124", "--json"],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 1, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["results"][0]["status"], "external")
            self.assertIn("No GitHub Actions run id", payload["results"][0]["note"])


if __name__ == "__main__":
    unittest.main()
