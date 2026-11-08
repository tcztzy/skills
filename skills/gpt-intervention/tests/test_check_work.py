"""Exercise observable reports against isolated files and real local Git indexes."""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "check_work.py"


class CheckWorkTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.repo = self.root / "repo"
        self.repo.mkdir()
        self.git("init", "--quiet", "--template=")
        self.write("readme.txt", "Initial user work\n")
        self.git("add", "readme.txt")
        self.git("commit", "--quiet", "-m", "fixture baseline")
        self.base = self.git("rev-parse", "HEAD").strip()

    def git(self, *args: str) -> str:
        result = subprocess.run(
            ["git", "-c", "core.hooksPath=/dev/null", "-c", "commit.gpgSign=false",
             "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
             "-C", str(self.repo), *args],
            check=True, capture_output=True, text=True,
        )
        return result.stdout

    def write(self, relative: str, text: str) -> None:
        path = self.repo / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def check(self, *args: str) -> tuple[int, dict, str]:
        result = subprocess.run([sys.executable, "-B", str(SCRIPT), *args],
                                capture_output=True, text=True, check=False)
        self.assertEqual(result.stderr, "", result.stderr)
        return result.returncode, json.loads(result.stdout), result.stdout

    def inspect_repo(self, base: str | None = None) -> tuple[int, dict, str]:
        return self.check("repo", "--repo", str(self.repo), "--base",
                          self.base if base is None else base)

    def skill(self, name: str = "gpt-intervention", extra: str = "") -> Path:
        folder = self.root / "gpt-intervention"
        folder.mkdir(exist_ok=True)
        (folder / "SKILL.md").write_text(
            f"---\nname: {name}\ndescription: Inspect concrete work evidence.\n---\n{extra}",
            encoding="utf-8",
        )
        return folder

    def test_clean_repository_has_no_changes(self) -> None:
        code, report, _ = self.inspect_repo()
        self.assertEqual(code, 0)
        self.assertEqual(report["facts"]["baseline"], self.base)
        self.assertEqual(report["facts"]["changes"], [])
        self.assertEqual(report["warnings"], [])

    def test_committed_staged_unstaged_and_untracked_are_distinct_and_read_only(self) -> None:
        self.write("package.json", '{"dependencies":{"a":"SECRET-COMMITTED"}}')
        self.git("add", "package.json")
        self.git("commit", "--quiet", "-m", "fixture change")
        self.write("package.json", '{"dependencies":{"a":"SECRET-STAGED"}}')
        self.git("add", "package.json")
        self.write("package.json", '{"dependencies":{"a":"SECRET-UNSTAGED"}}')
        self.write("draft notes.txt", "SECRET-UNTRACKED")
        self.write("dist/bundle.tmp", "SECRET-BUILD")
        self.git("add", "dist/bundle.tmp")
        self.write(".env.production", "SECRET-ENV")
        status_before = self.git("status", "--porcelain=v1", "-z")
        index_before = (self.repo / ".git" / "index").read_bytes()
        files_before = {p: p.read_bytes() for p in self.repo.rglob("*")
                        if p.is_file() and ".git" not in p.relative_to(self.repo).parts}
        code, report, output = self.inspect_repo()
        self.assertEqual(code, 0)
        observed = {(e["layer"], e["path"]) for e in report["facts"]["changes"]}
        self.assertTrue({("committed", "package.json"), ("staged", "package.json"),
                         ("unstaged", "package.json"), ("untracked", "draft notes.txt")}
                        .issubset(observed))
        self.assertEqual(len(report["facts"]["manifest_comparisons"]), 3)
        for item in report["facts"]["manifest_comparisons"]:
            self.assertIn("dependencies", item["changed_supported_fields"])
        categories = {e["category"] for e in report["warnings"]}
        self.assertIn("possible_temporary_or_build_artifact", categories)
        self.assertIn("possibly_sensitive_filename", categories)
        self.assertNotIn("SECRET-", output)
        self.assertEqual(index_before, (self.repo / ".git" / "index").read_bytes())
        self.assertEqual(status_before, self.git("status", "--porcelain=v1", "-z"))
        self.assertEqual(files_before, {p: p.read_bytes() for p in files_before})

    def test_supported_toml_and_untracked_manifest(self) -> None:
        self.write("pyproject.toml", '[project]\ndependencies = ["secret-package>=1"]\n'
                   '[build-system]\nrequires = ["secret-builder"]\n')
        self.write("Cargo.toml", '[dependencies]\nsecret_crate = "1"\n')
        self.git("add", "Cargo.toml")
        code, report, output = self.inspect_repo()
        self.assertEqual(code, 0)
        fields = {e["path"]: e["changed_supported_fields"]
                  for e in report["facts"]["manifest_comparisons"]}
        self.assertIn("project.dependencies", fields["pyproject.toml"])
        self.assertIn("build-system", fields["pyproject.toml"])
        self.assertIn("dependencies", fields["Cargo.toml"])
        self.assertNotIn("secret-package", output)
        self.assertNotIn("secret_crate", output)

    def test_unparsed_manifest_is_unknown_not_validated(self) -> None:
        self.write("requirements-dev.txt", "SECRET-REQUIREMENT\n")
        self.write("uv.lock", "SECRET-LOCK\n")
        code, report, output = self.inspect_repo()
        self.assertEqual(code, 0)
        self.assertEqual({e["path"] for e in report["unknowns"]},
                         {"requirements-dev.txt", "uv.lock"})
        self.assertEqual(report["facts"]["manifest_comparisons"], [])
        self.assertNotIn("SECRET-", output)

    def test_invalid_manifest_reports_error_without_content(self) -> None:
        for name, content in [("package.json", '{"SECRET-INVALID":'),
                              ("pyproject.toml", '[SECRET-INVALID')]:
            with self.subTest(name=name):
                self.write(name, content)
                code, report, output = self.inspect_repo()
                self.assertEqual(code, 1)
                self.assertIn("invalid_manifest_syntax", {e["category"] for e in report["errors"]})
                self.assertNotIn("SECRET-INVALID", output)
                (self.repo / name).unlink()

    def test_deleted_manifest_compares_previous_declarations(self) -> None:
        self.write("package.json", '{"dependencies":{"a":"1"}}')
        self.git("add", "package.json")
        self.git("commit", "--quiet", "-m", "fixture package")
        self.base = self.git("rev-parse", "HEAD").strip()
        self.git("rm", "--quiet", "package.json")
        code, report, _ = self.inspect_repo()
        self.assertEqual(code, 0)
        item = report["facts"]["manifest_comparisons"][0]
        self.assertEqual(item["change"], "D")
        self.assertEqual(item["changed_supported_fields"], ["dependencies"])

    def test_empty_or_invalid_baseline_never_passes(self) -> None:
        for base in ("", "no-such-ref"):
            with self.subTest(base=base):
                code, report, _ = self.inspect_repo(base)
                self.assertEqual(code, 2)
                self.assertEqual(report["status"], "incomplete")

    def test_missing_baseline_argument_never_passes(self) -> None:
        result = subprocess.run([sys.executable, "-B", str(SCRIPT), "repo", "--repo", str(self.repo)],
                                capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 2)

    def test_unborn_or_nonrepository_never_passes(self) -> None:
        empty = self.root / "empty"
        empty.mkdir()
        for initialize in (False, True):
            with self.subTest(initialize=initialize):
                if initialize:
                    subprocess.run(["git", "init", "--quiet", "--template=", str(empty)], check=True)
                code, report, _ = self.check("repo", "--repo", str(empty), "--base", "HEAD")
                self.assertEqual(code, 2)
                self.assertEqual(report["status"], "incomplete")

    def test_nonancestor_baseline_never_passes(self) -> None:
        self.write("other.txt", "branch-only work")
        self.git("add", "other.txt")
        self.git("commit", "--quiet", "-m", "other branch")
        later = self.git("rev-parse", "HEAD").strip()
        self.git("checkout", "--quiet", "--detach", self.base)
        code, report, _ = self.inspect_repo(later)
        self.assertEqual(code, 2)
        self.assertEqual(report["status"], "incomplete")

    def test_symlink_manifest_does_not_follow_external_contents(self) -> None:
        external = self.root / "outside.json"
        external.write_text('{"SECRET-OUTSIDE": invalid}', encoding="utf-8")
        (self.repo / "package.json").symlink_to(external)
        for staged in (False, True):
            with self.subTest(staged=staged):
                if staged:
                    self.git("add", "package.json")
                code, report, output = self.inspect_repo()
                self.assertEqual(code, 0)
                self.assertIn("symlink_manifest_not_interpreted", {e["category"] for e in report["unknowns"]})
                self.assertNotIn("SECRET-OUTSIDE", output)

    def test_valid_skill_and_local_reference(self) -> None:
        folder = self.skill(extra="[Cases](references/cases.md)\n")
        (folder / "references").mkdir()
        (folder / "references" / "cases.md").write_text("# Cases\n", encoding="utf-8")
        code, report, _ = self.check("skill", str(folder))
        self.assertEqual(code, 0)
        self.assertEqual(len(report["facts"]["checked_local_file_links"]), 1)

    def test_missing_skill_or_empty_frontmatter_never_passes(self) -> None:
        folder = self.skill()
        for content in ("", "---\nname: gpt-intervention\n"):
            with self.subTest(content=content):
                (folder / "SKILL.md").write_text(content, encoding="utf-8")
                code, report, _ = self.check("skill", str(folder))
                self.assertEqual(code, 1)
                self.assertTrue(report["errors"])
        (folder / "SKILL.md").unlink()
        code, report, _ = self.check("skill", str(folder))
        self.assertEqual(code, 2)

    def test_mismatched_directory_and_missing_link_are_findings(self) -> None:
        folder = self.skill(name="different-skill", extra="[Missing](references/missing.md)\n")
        code, report, _ = self.check("skill", str(folder))
        self.assertEqual(code, 1)
        self.assertEqual({e["category"] for e in report["errors"]},
                         {"invalid_name_or_directory_mismatch", "missing_local_reference"})

    def test_unsupported_yaml_is_unknown(self) -> None:
        folder = self.skill()
        (folder / "SKILL.md").write_text(
            "---\nname: gpt-intervention\ndescription: >\n  Multiline example\n---\n", encoding="utf-8")
        code, report, _ = self.check("skill", str(folder))
        self.assertEqual(code, 2)
        self.assertEqual(report["status"], "incomplete")
        self.assertTrue(report["unknowns"])


if __name__ == "__main__":
    unittest.main()
