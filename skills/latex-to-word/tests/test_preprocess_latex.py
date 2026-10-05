import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "preprocess_latex.py"
spec = importlib.util.spec_from_file_location("preprocess_latex", SCRIPT)
preprocessor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(preprocessor)


class PreprocessTests(unittest.TestCase):
    def test_resizebox_preserves_nested_content_and_removes_matching_brace(self):
        body = "\n" + r"\begin{tabular}{ll}a&\textbf{b}\\\end{tabular}" + "\n"
        for source in (
            r"\resizebox{\textwidth}{!}{" + body + "}",
            r"\resizebox{\dimexpr\textwidth-\fboxsep}{!}{" + body + "}",
        ):
            with self.subTest(source=source):
                result, counts = preprocessor.preprocess(source)
                self.assertEqual(result, body)
                self.assertEqual(counts["resizebox"], 1)

    def test_ordinary_table_group_is_preserved(self):
        source = r"{\begin{tabular}{ll}a&b\\\end{tabular}}" + "\n"
        self.assertEqual(preprocessor.preprocess(source)[0], source)

    def test_resizebox_handles_escaped_braces_and_comments(self):
        body = "\n" + r"\{value\} % unmatched { in a comment" + "\n"
        source = r"\resizebox{1cm}{!}{" + body + "} after"
        self.assertEqual(preprocessor.preprocess(source)[0], body + " after")

    def test_nested_formatting_configuration_is_removed_completely(self):
        source = r"\hypersetup{pdftitle={A title},colorlinks=true}" + "\nText"
        self.assertEqual(preprocessor.preprocess(source)[0], "\nText")

    def test_optional_table_position_and_alignment(self):
        source = r"\begin{tabularx}{\textwidth}[t]{C{2cm}R{3cm}X}a&b&c\\\end{tabularx}"
        result, _ = preprocessor.preprocess(source)
        self.assertEqual(result, r"\begin{tabular}[t]{crl}a&b&c\\\end{tabular}")

    def test_complex_table_and_multiline_definition_remain_reviewable(self):
        source = (r"\usepackage{tabularx}" + "\n" + r"\newcolumntype{Y}{" + "\n"
                  + r">{\raggedright\arraybackslash}X}" + "\n"
                  + r"\begin{tabularx}{\textwidth}{>{\bfseries}X}a\\\end{tabularx}")
        result, _ = preprocessor.preprocess(source)
        self.assertEqual(result, source)
        self.assertIn("tabularx", preprocessor.remaining_risks(result))
        self.assertIn("custom column definition", preprocessor.remaining_risks(result))

    def test_command_prefix_is_not_removed(self):
        source = r"\allowbreakfast \allowbreak word"
        self.assertEqual(preprocessor.preprocess(source)[0], r"\allowbreakfast  word")

    def test_source_cannot_be_overwritten_through_hard_link(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source.tex"
            output = Path(directory) / "output.tex"
            source.write_text(r"\documentclass{ctexart}")
            output.hardlink_to(source)
            completed = subprocess.run(
                [sys.executable, str(SCRIPT), str(source), "--output", str(output), "--force"],
                capture_output=True, text=True,
            )
            self.assertNotEqual(completed.returncode, 0)
            self.assertEqual(source.read_text(), r"\documentclass{ctexart}")


if __name__ == "__main__":
    unittest.main()
