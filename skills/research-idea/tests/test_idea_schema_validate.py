import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "idea_schema_validate.py"
IDEA = {
    "Name": "example",
    "Title": "Example proposal",
    "Short Hypothesis": "A testable hypothesis",
    "Related Work": "A baseline",
    "Abstract": "A summary",
    "Experiments": ["Compare against the baseline"],
    "Risk Factors and Limitations": ["Limited data"],
}


class IdeaSchemaValidationTest(unittest.TestCase):
    def validate(self, document):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "ideas.json"
            path.write_text(json.dumps(document), encoding="utf-8")
            return subprocess.run(
                [sys.executable, str(SCRIPT), "--in", str(path)],
                capture_output=True,
                text=True,
                check=False,
            )

    def test_accepts_document_shapes(self):
        for document in (IDEA, [IDEA], {"idea": IDEA}, {"ideas": [IDEA]}):
            with self.subTest(document=document):
                result = self.validate(document)
                self.assertEqual(result.returncode, 0, result.stderr)

    def test_rejects_null_required_fields(self):
        for field in IDEA:
            with self.subTest(field=field):
                result = self.validate({**IDEA, field: None})
                self.assertEqual(result.returncode, 1)
                self.assertIn(field, result.stderr)

    def test_accepts_string_experiments_and_risks(self):
        result = self.validate({
            **IDEA,
            "Experiments": "Compare against the baseline",
            "Risk Factors and Limitations": "Limited data",
        })
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
