from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
import writeup_scaffold as scaffold


class JournalScaffoldTests(unittest.TestCase):
    def test_every_requested_section_has_a_template_destination(self):
        for profile, spec in scaffold.PROFILE_SPECS.items():
            with self.subTest(profile=profile):
                self.assertEqual(set(spec["sections"]), set(spec["placeholders"].values()))

    @unittest.skipUnless(shutil.which("pdflatex"), "pdflatex is not installed")
    def test_journal_scaffolds_compile(self):
        for profile in ("molecular-plant", "plant-communications", "bioinformatics", "softwarex"):
            with self.subTest(profile=profile), tempfile.TemporaryDirectory() as directory:
                generated = subprocess.run(
                    [sys.executable, str(SCRIPTS / "writeup_scaffold.py"),
                     "--profile", profile, "--title", "Example tool", "--out-dir", directory],
                    capture_output=True, text=True,
                )
                self.assertEqual(generated.returncode, 0, generated.stderr)
                compiled = subprocess.run(
                    ["pdflatex", "-interaction=nonstopmode", "-halt-on-error", "paper.tex"],
                    cwd=directory, capture_output=True, text=True,
                )
                self.assertEqual(compiled.returncode, 0, compiled.stdout[-4000:])
                self.assertTrue((Path(directory) / "paper.pdf").stat().st_size)


if __name__ == "__main__":
    unittest.main()
