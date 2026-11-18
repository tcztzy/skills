"""Exercise release checks against a real checkout and an unpublished working tree."""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from check_plugin_release import release_errors


class PluginReleaseTest(unittest.TestCase):
    def test_content_version_and_retired_caller(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            manifest = repo / ".codex-plugin/plugin.json"
            manifest.parent.mkdir()
            manifest.write_text('{"version":"1.0.0"}', encoding="utf-8")
            companions = repo / ".claude-plugin/external-plugins.json"
            companions.parent.mkdir()
            companions.write_text(json.dumps([{
                "name": "remote-skill",
                "source": {"source": "url", "url": "https://example.invalid/skills.git", "sha": "a" * 40},
                "skills": ["./remote-skill"],
            }]), encoding="utf-8")
            entry = repo / "skills/old-skill/SKILL.md"
            entry.parent.mkdir(parents=True)
            entry.write_text("---\nname: old-skill\ndescription: First.\n---\n", encoding="utf-8")
            (repo / "README.md").write_text("Use `old-skill` for this task.\n", encoding="utf-8")
            subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
            subprocess.run(["git", "add", "."], cwd=repo, check=True)
            subprocess.run(["git", "-c", "user.name=Tester", "-c", "user.email=test@example.invalid",
                            "commit", "-qm", "initial release"], cwd=repo, check=True)
            self.assertEqual(release_errors(repo, "HEAD"), [])
            entry.write_text(entry.read_text(encoding="utf-8") + "Changed.\n", encoding="utf-8")
            self.assertTrue(any("version" in msg for msg in release_errors(repo, "HEAD")))
            manifest.write_text(json.dumps({"version": "1.1.0"}), encoding="utf-8")
            self.assertEqual(release_errors(repo, "HEAD"), [])
            entry.unlink()
            self.assertTrue(any("old-skill" in msg for msg in release_errors(repo, "HEAD")))
            (repo / "README.md").write_text("Retirement complete.\n", encoding="utf-8")
            self.assertEqual(release_errors(repo, "HEAD"), [])
            companions.write_text("[]", encoding="utf-8")
            (repo / "README.md").write_text("Use `remote-skill` for this task.\n", encoding="utf-8")
            self.assertTrue(any("remote-skill" in msg for msg in release_errors(repo, "HEAD")))
