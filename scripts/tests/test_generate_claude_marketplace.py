"""Publish distributable skills and pinned remote sources, not private local mounts."""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from generate_claude_marketplace import build_marketplace, collect_plugins


class MarketplaceInventoryTests(unittest.TestCase):
    def test_remote_entry_survives_without_a_local_installation(self):
        external = json.loads((Path(__file__).resolve().parents[2] /
                               ".claude-plugin/external-plugins.json").read_text())
        self.assertEqual(external[0]["source"], {
            "source": "url", "url": "https://github.com/Kiterlin/anti-defensive-writing.git",
            "sha": "6345f09c9141be94df055fd048c94a4f26a8ed66",
        })
        self.assertEqual(external[0]["skills"], ["./skill/anti-defensive-writing"])
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            skills = root / "skills"
            skills.mkdir()
            manifest = root / ".claude-plugin/external-plugins.json"
            manifest.parent.mkdir()
            manifest.write_text(json.dumps(external))
            self.assertEqual(build_marketplace(skills)["plugins"], external)
            # A local installation is not the source for the remote entry.
            (skills / "anti-defensive-writing").symlink_to(root / "absent-local-install")
            self.assertEqual(build_marketplace(skills)["plugins"], external)
            # Never silently replace a bundled skill with an external namesake.
            local = skills / "local-copy"
            local.mkdir()
            (local / "SKILL.md").write_text(
                "---\nname: anti-defensive-writing\ndescription: Local skill.\n---\n")
            with self.assertRaisesRegex(ValueError, "unique"):
                build_marketplace(skills)

    def test_inventory_matches_distributable_skill_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            skills = root / "skills"
            for name in ("tracked", "new", "private", "removed"):
                skill = skills / name
                skill.mkdir(parents=True)
                (skill / "SKILL.md").write_text(
                    f"---\nname: {name}\ndescription: Example skill.\n---\n",
                    encoding="utf-8",
                )
            subprocess.run(
                ["git", "add", "skills/tracked", "skills/removed"],
                cwd=root,
                check=True,
            )
            (skills / "removed" / "SKILL.md").unlink()
            # An ignored local skill must not create an entry absent in a clone.
            (skills / "private" / ".gitignore").write_text("*\n", encoding="utf-8")
            # Tracked files remain distributable even if an ignore rule matches.
            (root / ".gitignore").write_text("skills/tracked/\n", encoding="utf-8")

            self.assertEqual(
                [plugin["name"] for plugin in collect_plugins(skills)],
                ["new", "tracked"],
            )


if __name__ == "__main__":
    unittest.main()
