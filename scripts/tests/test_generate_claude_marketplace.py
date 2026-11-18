"""Publish distributable skills and pinned remote sources, not private local mounts."""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from generate_claude_marketplace import build_marketplace, collect_plugins, distribution_files
from validate_plugin_metadata import validate_doc_links, validate_plugin_manifest, validate_retired_skills
from validate_skill import validate_skill


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
            local = skills / external[0]["name"]
            # Some Windows installations restrict symlinks to privileged users.
            try:
                local.symlink_to(root / "absent-local-install", target_is_directory=True)
            except OSError:
                pass
            else:
                self.assertEqual(build_marketplace(skills)["plugins"], external)
                local.unlink()
            # Never silently replace a bundled skill with an external namesake.
            local.mkdir()
            (local / "SKILL.md").write_text(
                f"---\nname: {local.name}\ndescription: Local skill.\n---\n")
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

    def test_catalog_and_validator_share_metadata_rules_in_archive(self):
        with tempfile.TemporaryDirectory(prefix="source archive ") as directory:
            root = Path(directory)
            skill = root / "skills" / "example"
            skill.mkdir(parents=True)
            entry = skill / "SKILL.md"
            entry.write_text("---\nname: example\ndescription: >-\n  First line\n  second line.\n---\n")
            self.assertTrue(validate_skill(skill)[0])
            self.assertEqual(collect_plugins(skill.parent)[0]["description"], "First line second line.")
            for raw in (
                "name: example\n---", "name: example\ndescription: ''\n---",
                "name: wrong\ndescription: Example.\n---", "name: example\ndescription: Example.",
            ):
                with self.subTest(raw=raw):
                    entry.write_text(f"---\n{raw}\n")
                    self.assertFalse(validate_skill(skill)[0])
                    with self.assertRaises(ValueError):
                        collect_plugins(skill.parent)

    def test_retirement_and_rename_check_catalog_and_callers(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            older = root / "skills" / "older"
            older.mkdir(parents=True)
            (older / "SKILL.md").write_text("---\nname: older\ndescription: Original.\n---\n")
            self.assertEqual([p["name"] for p in collect_plugins(older.parent)], ["older"])
            (root / "README.md").write_text("[guide](skills/older/SKILL.md)\nUse `older` for review.\n")
            newer = older.rename(older.with_name("newer"))
            (newer / "SKILL.md").write_text("---\nname: newer\ndescription: Replacement.\n---\n")
            self.assertEqual([p["name"] for p in collect_plugins(newer.parent)], ["newer"])
            self.assertEqual(len(validate_doc_links(root, distribution_files(root))), 1)
            self.assertTrue(any("Use `older`" in issue for issue in validate_retired_skills(root, {"older"})))
            (root / "README.md").write_text("[guide](skills/newer/SKILL.md)\nUse `newer` for review.\n")
            self.assertEqual(validate_doc_links(root, distribution_files(root)), [])
            self.assertEqual(validate_retired_skills(root, {"older"}), [])
            (newer / "SKILL.md").unlink()
            self.assertEqual(collect_plugins(newer.parent), [])
            self.assertTrue(validate_doc_links(root, distribution_files(root)))

    def test_unpinned_remote_and_wrong_codex_root(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "skills").mkdir()
            manifest = root / ".claude-plugin/external-plugins.json"
            manifest.parent.mkdir()
            manifest.write_text(json.dumps([{"name": "external", "source": {
                "source": "url", "url": "https://example.com/skill.git"}, "skills": ["./skill"]}]))
            with self.assertRaisesRegex(ValueError, "commit SHA"):
                build_marketplace(root / "skills")
            codex = root / ".codex-plugin/plugin.json"
            codex.parent.mkdir()
            codex.write_text(json.dumps({"name": "skills", "skills": "./.claude-plugin"}))
            self.assertTrue(validate_plugin_manifest(codex)[1])
            codex.write_text(json.dumps({"name": "skills", "skills": "./skills/"}))
            self.assertEqual(validate_plugin_manifest(codex)[1], [])

    def test_ignored_local_assets_cannot_satisfy_published_links(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            (root / ".gitignore").write_text("private/\n")
            refs = root / "skills" / "reader"
            private = refs / "private"
            private.mkdir(parents=True)
            (private / "fixture.md").write_text("Only exists in this checkout.\n")
            (refs / "SKILL.md").write_text(
                "---\nname: reader\ndescription: Example.\n---\n"
                "[missing in the release](private/fixture.md)\n"
                "```md\n[example syntax](missing/example)\n```\n"
            )
            issues = validate_doc_links(root, distribution_files(root))
            self.assertEqual(len(issues), 1)
            self.assertIn("private/fixture.md", issues[0])


if __name__ == "__main__":
    unittest.main()
