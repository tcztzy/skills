"""Exercise file-header audit failures that could incorrectly pass a CI gate.

Temporary source fixtures distinguish real leading documentation from strings,
item-level comments, and ordinary C comments. CLI checks capture exit status and
reports without changing the inspected files.
"""

from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import check_file_docs


class HeaderAuditTests(unittest.TestCase):
    def check_source(self, source: str, suffix: str):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / f"source{suffix}"
            path.write_text(source, encoding="utf-8")
            return check_file_docs.check_file(
                path,
                max_lines=80,
                min_summary=20,
                include_generated=False,
                c_style="doxygen",
            )

    def test_doc_markers_after_code_are_not_file_headers(self):
        sources = {
            ".ts": "export const value = 1;\n/** Coordinates all application requests.\n * @module\n */",
            ".c": "int value;\n/** @file\n * @brief Coordinates all application requests.\n */",
            ".rs": "mod child {\n//! Coordinates all application requests.\n}",
        }
        for suffix, source in sources.items():
            with self.subTest(suffix=suffix):
                self.assertEqual(self.check_source(source, suffix).status, "fail")

    def test_markers_in_strings_are_not_file_headers(self):
        sources = {
            ".ts": "const example = `/** Coordinates all application requests.\n * @module\n */`;",
            ".c": 'const char *example = "/* @file @brief Coordinates all application requests. */";',
            ".rs": 'const EXAMPLE: &str = r#"\n//! Coordinates all application requests.\n"#;',
        }
        for suffix, source in sources.items():
            with self.subTest(suffix=suffix):
                self.assertEqual(self.check_source(source, suffix).status, "fail")

    def test_ordinary_c_comments_are_not_doxygen(self):
        self.assertEqual(
            self.check_source("/* @file\n * @brief Coordinates all application requests.\n */", ".c").status,
            "fail",
        )

    def test_inline_comment_delimiters_are_not_summary_text(self):
        for suffix, source in {
            ".rs": "/*! Coordinates all application requests. */\n//! More details about the flow.",
            ".c": "/** @file @brief Coordinates all application requests. */",
        }.items():
            with self.subTest(suffix=suffix):
                result = self.check_source(source, suffix)
                self.assertEqual(result.status, "pass")
                self.assertEqual(result.summary, "Coordinates all application requests.")

    def test_valid_leading_headers(self):
        sources = {
            ".py": '#!/usr/bin/env python3\n"""Coordinates all application requests."""\n',
            ".ts": "#!/usr/bin/env node\n// SPDX-License-Identifier: MIT\n/** Coordinates all application requests.\n * @module\n */\nexport const value = 1;",
            ".h": "#pragma once\n/** @file\n * @brief Coordinates all application requests.\n */\nint value;",
            ".rs": "#![allow(dead_code)]\n//! Coordinates all application requests.\nmod child {}",
        }
        for suffix, source in sources.items():
            with self.subTest(suffix=suffix):
                result = self.check_source(source, suffix)
                self.assertEqual(result.status, "pass", result.reason)

    def test_missing_input_does_not_pass_with_valid_input(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "valid.py"
            path.write_text('"""Coordinates all application requests."""\n', encoding="utf-8")
            with redirect_stdout(StringIO()), redirect_stderr(StringIO()):
                with self.assertRaises(SystemExit) as raised:
                    check_file_docs.main([str(path), str(path.with_name("missing.py"))])
            self.assertEqual(raised.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
