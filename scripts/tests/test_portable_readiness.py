"""Check the public readiness CLI in a fresh profile with no tools on PATH.

Fixtures exercise skill discovery, missing prerequisites, untested skills, and
a missing skills root. All reports and user directories live under a temp tree.
"""

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


AUDIT = Path(__file__).resolve().parents[2] / "skills/skill-manager/scripts/audit-installed-skills.py"


class PortableReadinessTest(unittest.TestCase):
    def test_fresh_profile_with_no_tools(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            profile = root / "user profile"
            profile.mkdir()
            env = {key: os.environ[key] for key in ("SYSTEMROOT", "WINDIR") if key in os.environ}
            env.update(HOME=str(profile), USERPROFILE=str(profile), PATH="",
                       TMPDIR=directory, TEMP=directory, TMP=directory)
            skills = root / "skills"
            workspace = root / "audit"
            command = [str(Path(sys.executable).absolute()), "-B", str(AUDIT),
                       "--skills-root", str(skills), "--workspace", str(workspace),
                       "--runtime-root", str(root / "runtimes")]

            missing = subprocess.run(command, cwd=root, env=env, capture_output=True, text=True)
            self.assertNotEqual(missing.returncode, 0)
            self.assertFalse(workspace.exists())

            for name in ("typst", "new-skill"):
                skill = skills / name
                skill.mkdir(parents=True)
                (skill / "SKILL.md").write_text(
                    f"---\nname: {name}\ndescription: Exercise portable readiness.\n---\n",
                    encoding="utf-8",
                )
            audit = subprocess.run(command, cwd=root, env=env, capture_output=True, text=True)
            self.assertEqual(audit.returncode, 0, audit.stderr)
            report_path = Path(json.loads(audit.stdout)["report_json"])
            report = json.loads(report_path.read_text(encoding="utf-8"))
            rows = {item["skill_name"]: item for item in report["skills"]}
            self.assertEqual(set(rows), {"typst", "new-skill"})
            self.assertEqual(rows["typst"]["readiness_verdict"], "env_blocked")
            self.assertIs(rows["typst"]["runtime_probe_passed"], False)
            self.assertIsNone(rows["typst"]["artifact_check"])
            self.assertEqual(rows["new-skill"]["readiness_verdict"], "unverified")
            self.assertIsNone(rows["new-skill"]["runtime_probe_passed"])
