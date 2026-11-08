"""Offline CLI checks for complete, portable review requests; no model evaluation."""

import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


SOURCE = Path(__file__).resolve().parents[1]


class ReviewPacketTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.skill = self.root / "independent-install"
        shutil.copytree(SOURCE, self.skill, ignore=shutil.ignore_patterns("__pycache__"))
        self.request = self.root / "request.json"
        self.output = self.root / "packet.json"
        self.data = {"scope": "targeted", "target": "Same-venue comparison",
                     "controls": [], "evidence": {"text": "A local claim.", "ledger": []}}
        self.request.write_text(json.dumps(self.data), encoding="utf-8")

    def run_packet(self):
        return subprocess.run(
            [sys.executable, "-B", str(self.skill / "scripts/close_reading_audit.py"),
             "packet", "--request", str(self.request), "--out", str(self.output)],
            cwd=self.root, capture_output=True, text=True)

    def test_relocated_cli_delivers_complete_rules_and_data_without_source_access(self):
        self.data["issn"] = "2352-7110"
        self.request.write_text(json.dumps(self.data), encoding="utf-8")
        expected = "\n\n".join(
            f"## {rel}\n{(self.skill / rel).read_text(encoding='utf-8')}"
            for rel in ("SKILL.md", "references/review.schema.json"))
        profile = (self.skill / "references/2352-7110.md").read_text(encoding="utf-8")
        result = self.run_packet()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        packet = json.loads(self.output.read_text())
        shutil.rmtree(self.skill)  # The receiving context has only the emitted packet.
        self.assertEqual(packet["instructions"], expected)
        self.assertEqual(json.loads(packet["input"]),
                         {"request": self.data, "journal_profile": profile})

    def test_changed_installed_rule_is_loaded_instead_of_a_cached_copy(self):
        path = self.skill / "SKILL.md"
        replacement = path.read_text() + "\nTask-specific decision: retain the verified exception.\n"
        path.write_text(replacement, encoding="utf-8")
        self.assertEqual(self.run_packet().returncode, 0)
        delivered = json.loads(self.output.read_text())["instructions"]
        self.assertEqual(delivered.split("\n\n## references/review.schema.json")[0],
                         "## SKILL.md\n" + replacement)

    def test_argument_cases_deliver_evidence_without_expected_judgments(self):
        """Transport check only; this does not evaluate reviewer reasoning."""
        fixtures = json.loads((SOURCE / "tests/argument_audit_cases.json").read_text())
        for case in fixtures["cases"]:
            with self.subTest(case=case["id"]):
                self.output.unlink(missing_ok=True)
                request = {"scope": case["scope"].split(":", 1)[0],
                           "target": case["scope"], "controls": [],
                           "evidence": case["input"]}
                self.request.write_text(json.dumps(request), encoding="utf-8")
                result = self.run_packet()
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                packet = json.loads(self.output.read_text())
                self.assertEqual(json.loads(packet["input"]), {"request": request})
                self.assertIn("## Argument audit within the agreed scope", packet["instructions"])

    def test_missing_required_rule_or_profile_cannot_emit_a_partial_packet(self):
        for rel in ("SKILL.md", "references/review.schema.json", "references/2352-7110.md"):
            with self.subTest(rel=rel):
                self.data["issn"] = "2352-7110"
                self.request.write_text(json.dumps(self.data), encoding="utf-8")
                path = self.skill / rel
                content = path.read_bytes()
                path.unlink()
                self.assertEqual(self.run_packet().returncode, 2)
                self.assertFalse(self.output.exists())
                path.write_bytes(content)

    def test_invalid_scope_or_path_like_issn_is_rejected_and_existing_output_preserved(self):
        for update in ({"scope": "skip-everything"}, {"scope": []}, {"evidence": ""},
                       {"controls": {}}, {"issn": "../../private"}):
            with self.subTest(update=update):
                self.request.write_text(json.dumps(self.data | update), encoding="utf-8")
                self.assertEqual(self.run_packet().returncode, 2)
                self.assertFalse(self.output.exists())
        self.request.write_text(json.dumps(self.data), encoding="utf-8")
        self.output.write_text("Keep existing packet", encoding="utf-8")
        self.assertEqual(self.run_packet().returncode, 2)
        self.assertEqual(self.output.read_text(), "Keep existing packet")

    def test_existing_prepare_validate_workflow_still_reports_incomplete_units(self):
        source = self.root / "paper.txt"
        source.write_text("Introduction\n\nA substantive claim with enough context to inspect its support.\n", encoding="utf-8")
        audit = self.root / "audit.jsonl"
        coverage = self.root / "coverage.json"
        script = str(self.skill / "scripts/close_reading_audit.py")
        prepared = subprocess.run([sys.executable, "-B", script, "prepare", "--text", str(source),
                                   "--out", str(audit), "--coverage", str(coverage)],
                                  capture_output=True, text=True)
        self.assertEqual(prepared.returncode, 0, prepared.stdout + prepared.stderr)
        command = [sys.executable, "-B", script, "validate", "--audit", str(audit)]
        self.assertEqual(subprocess.run(command, capture_output=True).returncode, 1)
        rows = [json.loads(line) for line in audit.read_text().splitlines()]
        self.assertTrue(rows)
        for row in rows:
            row.update(review_status="ok", review_note="Inspected in this offline fixture.")
        audit.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
        self.assertEqual(subprocess.run(command, capture_output=True).returncode, 0)


if __name__ == "__main__":
    unittest.main()
