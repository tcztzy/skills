"""Validate supplied annotations and arithmetic, not semantic classification accuracy."""

from contextlib import redirect_stdout
from copy import deepcopy
import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

from pydantic import ValidationError

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import audit_defensive_writing as audit


DOCUMENTS = {"input": "Separate checks miss joint failures. We therefore check the assembly.",
             "evidence_1": "Three assemblies passed the check."}


def annotations() -> dict:
    return {"schema_version": "argument-relations-v1", "annotator": "Test fixture",
            "annotation_context": "Authored labels; no semantic accuracy or independent review claim.",
            "document_sha256": {key: hashlib.sha256(text.encode()).hexdigest() for key, text in DOCUMENTS.items()},
            "contract": {"scope": "Two fixed relations in the supplied input.", "units": [
                {"id": "R1", "kind": "difficulty_requirement", "relationship": "Joint failures require joint checks."},
                {"id": "R2", "kind": "claim_evidence", "relationship": "Evidence supports assembly effectiveness."}]},
            "judgments": [
                {"id": "R1", "status": "explicit", "anchors": [
                    {"document": "input", "sentence_id": 1, "quote": "Separate checks miss joint failures."},
                    {"document": "input", "sentence_id": 2, "quote": "We therefore check the assembly."}],
                 "rationale": "Both endpoints and their connection are stated.", "uncertainty": ""},
                {"id": "R2", "status": "unclear", "anchors": [
                    {"document": "input", "sentence_id": 2, "quote": "We therefore check the assembly."}],
                 "rationale": "A procedure is described; its effectiveness is not established.",
                 "uncertainty": "No comparator or outcome is described in the input."}]}


class ArgumentRelationTests(unittest.TestCase):
    def measure(self, data: dict, documents: dict[str, str] = DOCUMENTS) -> dict:
        return audit.audit_argument_annotations(audit.ArgumentAnnotations.model_validate(data), documents, "en")

    def test_fixed_denominators_and_full_source_sentences(self) -> None:
        report = self.measure(annotations())
        metric = report["metrics_by_kind"]["claim_evidence"]
        self.assertEqual((metric["explicit"], metric["unclear"], metric["denominator"]), (0, 1, 1))
        self.assertEqual(metric["explicit_fraction"], 0)
        self.assertIsNone(report["metrics_by_kind"]["requirement_mechanism"]["explicit_fraction"])
        self.assertEqual(report["judgments"][0]["anchors"][0]["sentence"], DOCUMENTS["input"].split(" We")[0])
        self.assertIsNone(report["inter_annotator_agreement"])

    def test_missing_duplicate_extra_and_changed_contracts(self) -> None:
        data = annotations()
        for rows in [data["judgments"][:1], data["judgments"] * 2,
                     data["judgments"] + [data["judgments"][0] | {"id": "extra"}]]:
            with self.subTest(rows=len(rows)), self.assertRaises(ValueError):
                self.measure(data | {"judgments": rows})
        changed = deepcopy(data)
        changed["contract"]["units"][1]["relationship"] = "A different claim."
        self.assertNotEqual(self.measure(changed)["contract_sha256"], self.measure(data)["contract_sha256"])
        changed["contract"]["units"][1]["id"] = "R1"
        with self.assertRaisesRegex(ValueError, "重复"):
            self.measure(changed)

    def test_source_hash_sentence_and_quote_integrity(self) -> None:
        data = annotations()
        with self.assertRaisesRegex(ValueError, "SHA-256"):
            self.measure(data, DOCUMENTS | {"input": DOCUMENTS["input"] + " Modified."})
        for changes in [{"document": "unknown"}, {"sentence_id": 200}, {"quote": "Invented quote."},
                        {"sentence_id": 0}, {"quote": " "}]:
            changed = deepcopy(data)
            changed["judgments"][0]["anchors"][0].update(changes)
            with self.subTest(changes=changes), self.assertRaises((ValueError, ValidationError)):
                self.measure(changed)

    def test_positive_relations_require_input_and_evidence_anchors(self) -> None:
        changed = annotations()
        changed["judgments"][0]["anchors"] = []
        with self.assertRaisesRegex(ValueError, "正文"):
            self.measure(changed)
        changed = annotations()
        changed["judgments"][1]["status"] = "explicit"
        with self.assertRaisesRegex(ValueError, "来源证据"):
            self.measure(changed)
        changed["judgments"][1]["anchors"].append(
            {"document": "evidence_1", "sentence_id": 1, "quote": DOCUMENTS["evidence_1"]})
        self.assertEqual(self.measure(changed)["metrics_by_kind"]["claim_evidence"]["explicit"], 1)

    def test_uncertainty_and_absence_are_not_silently_excluded(self) -> None:
        changed = annotations()
        changed["judgments"][1]["uncertainty"] = ""
        with self.assertRaisesRegex(ValueError, "不确定性"):
            self.measure(changed)
        changed["judgments"][1].update(status="absent", anchors=[], uncertainty="")
        result = self.measure(changed)["metrics_by_kind"]["claim_evidence"]
        self.assertEqual((result["absent"], result["denominator"], result["explicit_fraction"]), (1, 1, 0))

    def test_cli_is_offline_and_protects_inputs_and_existing_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            text, evidence, packet, report = [root / name for name in ["input.txt", "evidence.txt", "labels.json", "report.json"]]
            text.write_text(DOCUMENTS["input"])
            evidence.write_text(DOCUMENTS["evidence_1"])
            packet.write_text(json.dumps(annotations()))
            arguments = ["audit", str(text), "--evidence", str(evidence), "--argument-annotations", str(packet), "--report", str(report)]
            with patch.object(sys, "argv", arguments), patch.object(audit, "OpenAI") as sdk, redirect_stdout(io.StringIO()):
                self.assertEqual(audit.main(), 0)
            sdk.assert_not_called()
            self.assertNotIn("before", json.loads(report.read_text()))
            for extra in [[], ["--prepare-review"], ["--responses-jsonl", "calls.jsonl"]]:
                with self.subTest(extra=extra), patch.object(sys, "argv", arguments + extra), \
                        patch("sys.stderr", new_callable=io.StringIO), self.assertRaises(SystemExit):
                    audit.main()
            original = packet.read_text()
            arguments[-1] = str(packet)
            with patch.object(sys, "argv", arguments), patch("sys.stderr", new_callable=io.StringIO), self.assertRaises(SystemExit):
                audit.main()
            self.assertEqual(packet.read_text(), original)


if __name__ == "__main__":
    unittest.main()
