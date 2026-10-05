"""Keep private local skills out of the distributable marketplace."""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from generate_claude_marketplace import collect_plugins


class MarketplaceInventoryTests(unittest.TestCase):
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
