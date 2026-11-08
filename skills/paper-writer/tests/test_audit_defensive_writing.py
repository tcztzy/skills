"""离线验证分类流程、论文指标和文件处理；不测量模型的语义准确率。"""

from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import tomllib
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import httpx2
from openai import OpenAI

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
import audit_defensive_writing as audit


LABELS = ["not_shown", "unsupported_doubt", "grounded_limit", "generic_scope",
          "future_work", "claim", "other"]


def label(sentence_id, category="claim", **changes):
    return {"id": sentence_id, "label": category, "proposition": "", "source_quote": "", **changes}


def response_body(value, *, status="completed", refusal=False):
    content = ({"type": "refusal", "refusal": "Cannot complete this request"}
               if refusal else {"type": "output_text", "text": json.dumps(value), "annotations": []})
    return {
        "id": "resp_offline_test", "object": "response", "created_at": 0,
        "status": status, "model": "test-model", "error": None,
        "incomplete_details": {"reason": "max_output_tokens"} if status == "incomplete" else None,
        "output": [{"id": "msg_test", "type": "message", "role": "assistant",
                    "status": "completed", "content": [content]}],
    }


def offline_client(responses):
    requests = []
    replies = iter(responses)

    def handle(request):
        requests.append(json.loads(request.content))
        return httpx2.Response(200, json=next(replies))

    client = OpenAI(
        api_key="offline-test-key", base_url="https://example.test/v1", max_retries=0,
        http_client=httpx2.Client(transport=httpx2.MockTransport(handle)),
    )
    return client, requests


class RuntimeContractTests(unittest.TestCase):
    def test_uv_entrypoint_and_dependencies_without_upper_bounds(self):
        source = Path(audit.__file__).read_text(encoding="utf-8")
        self.assertEqual(source.splitlines()[0], "#!/usr/bin/env -S uv run --script")
        block = source.split("# /// script\n", 1)[1].split("# ///", 1)[0]
        metadata = tomllib.loads("\n".join(line.removeprefix("# ") for line in block.splitlines()))
        dependencies = metadata["dependencies"]
        self.assertTrue(any(d == "pysbd" or d.startswith("pysbd>=") for d in dependencies))
        self.assertTrue(all("<" not in d for d in dependencies), dependencies)


class DocumentTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)

    def write(self, name, text):
        path = self.root / name
        path.write_text(text, encoding="utf-8")
        return path

    def assert_prose(self, text):
        self.assertIn("test title", text.lower())
        self.assertIn("Abstract result is 3.14 units.", text)
        self.assertIn("A strong result.", text)
        self.assertIn("A second paragraph.", text)
        self.assertIn("A strong result.", audit.paragraphs(text))
        self.assertIn("A second paragraph.", audit.paragraphs(text))
        self.assertNotIn("**strong**", text)
        self.assertNotIn(r"\textbf", text)
        self.assertTrue(any("3.14 units." in row["text"] for row in audit.split_sentences(text, "en")))

    def test_text_input_preserves_utf8_and_line_endings(self):
        original = "结果是 3.14。\r\n\r\n第二段。\n"
        path = self.root / "draft.txt"
        path.write_bytes(original.encode("utf-8"))
        self.assertEqual(audit.read_document(path), original)

    def test_unknown_suffix_is_rejected(self):
        path = self.write("draft.unsupported", "Some text.")
        with self.assertRaises(ValueError):
            audit.read_document(path)

    @unittest.skipUnless(shutil.which("pandoc"), "pandoc is not installed")
    def test_markdown_title_and_abstract_are_preserved(self):
        source = ("---\ntitle: Test Title\nabstract: |\n  Abstract result is 3.14 units.\n---\n\n"
                  "A **strong** result.\n\nA second paragraph.\n")
        for suffix in ["md", "markdown"]:
            with self.subTest(suffix=suffix):
                self.assert_prose(audit.read_document(self.write(f"draft.{suffix}", source)))

    @unittest.skipUnless(shutil.which("pandoc"), "pandoc is not installed")
    def test_latex_abstract_and_relative_input_are_preserved(self):
        self.write("section.tex", "A second paragraph.\n")
        source = (r"\documentclass{article}" "\n" r"\title{Test Title}" "\n"
                  r"\begin{document}" "\n" r"\maketitle" "\n"
                  r"\begin{abstract}Abstract result is 3.14 units.\end{abstract}" "\n\n"
                  r"A \textbf{strong} result." "\n\n" r"\input{section.tex}" "\n"
                  r"\end{document}" "\n")
        text = audit.read_document(self.write("draft.tex", source))
        self.assert_prose(text)
        self.assertNotIn(r"\input", text)
        self.assertNotIn(r"\begin", text)

    @unittest.skipUnless(shutil.which("pandoc"), "pandoc is not installed")
    def test_typst_relative_include_and_markup_are_converted(self):
        self.write("section.typ", "A second paragraph.\n")
        source = ("= Test Title\n\nAbstract result is 3.14 units.\n\n"
                  "A *strong* result.\n\n#include \"section.typ\"\n")
        text = audit.read_document(self.write("draft.typ", source))
        self.assert_prose(text)
        self.assertNotIn("#include", text)
        self.assertNotIn("*strong*", text)

    @unittest.skipUnless(shutil.which("pandoc"), "pandoc is not installed")
    def test_docx_body_and_abstract_are_converted(self):
        source = self.write("docx-source.md", "# Test Title\n\nAbstract result is 3.14 units.\n\n"
                            "A **strong** result.\n\nA second paragraph.\n")
        document = self.root / "draft.docx"
        subprocess.run(["pandoc", str(source), "--to=docx", "--output", str(document)], check=True)
        self.assert_prose(audit.read_document(document))


class SentenceTests(unittest.TestCase):
    def test_decimal_and_abbreviations_do_not_split_sentences(self):
        text = ("Smith et al. measured 3.14 units, e.g. in vitro. The effect was stable.\n\n"
                "A separate trial failed.")
        self.assertEqual(audit.split_sentences(text, "en"), [
            {"id": 1, "paragraph": 1, "text": "Smith et al. measured 3.14 units, e.g. in vitro."},
            {"id": 2, "paragraph": 1, "text": "The effect was stable."},
            {"id": 3, "paragraph": 2, "text": "A separate trial failed."},
        ])

    def test_blank_lines_and_crlf_define_paragraphs(self):
        self.assertEqual(audit.split_sentences("First result.\r\n \r\nSecond result.\r\n", "en"), [
            {"id": 1, "paragraph": 1, "text": "First result."},
            {"id": 2, "paragraph": 2, "text": "Second result."},
        ])

    def test_all_seven_labels_are_retained_in_sentence_order(self):
        sentences = [{"id": i, "paragraph": 1, "text": f"Sentence {i}."} for i in range(1, 8)]
        labels = [label(i, category) for i, category in enumerate(LABELS, 1)]
        client, _ = offline_client([response_body({"sentences": list(reversed(labels))})])
        with client:
            rows = audit.classify_sentences(client, "test-model", sentences, {"original": "Source."})
        self.assertEqual([r["id"] for r in rows], list(range(1, 8)))
        self.assertEqual([r["label"] for r in rows], LABELS)
        self.assertEqual([r["text"] for r in rows], [s["text"] for s in sentences])

    def test_batches_cover_every_sentence(self):
        sentences = [{"id": i, "paragraph": i, "text": f"Sentence {i}."} for i in range(1, 36)]
        client, requests = offline_client([
            response_body({"sentences": [label(i) for i in range(1, 33)]}),
            response_body({"sentences": [label(i) for i in range(33, 36)]}),
        ])
        with client:
            rows = audit.classify_sentences(client, "test-model", sentences, {"original": "Source."})
        self.assertEqual([r["id"] for r in rows], list(range(1, 36)))
        sent_ids = [s["id"] for request in requests for s in json.loads(request["input"])["sentences"]]
        self.assertEqual(sent_ids, list(range(1, 36)))

    def test_missing_duplicate_and_invented_ids_are_rejected(self):
        for actual in [[1], [1, 1], [1, 2, 3], [1, 99]]:
            with self.subTest(actual=actual), self.assertRaises(ValueError):
                audit.check_ids([SimpleNamespace(id=i) for i in actual], [1, 2])
        audit.check_ids([SimpleNamespace(id=2), SimpleNamespace(id=1)], [1, 2])
        audit.check_ids([], [])

    def test_classification_checks_ids_before_accepting_batch(self):
        sentences = [{"id": 1, "paragraph": 1, "text": "First."},
                     {"id": 2, "paragraph": 1, "text": "Second."}]
        client, _ = offline_client([response_body({"sentences": [label(1)]})])
        with client, self.assertRaises(ValueError):
            audit.classify_sentences(client, "test-model", sentences, {"original": "Source."})

    def test_invented_source_quote_is_rejected(self):
        client, _ = offline_client([response_body({"sentences": [
            label(1, "not_shown", proposition="The effect is causal.", source_quote="Invented support.")
        ]})])
        with client, self.assertRaisesRegex(ValueError, "source_quote"):
            audit.classify_sentences(client, "test-model", [{"id": 1, "paragraph": 1, "text": "No proof."}],
                                     {"original": "A correlation was observed."})


class MetricTests(unittest.TestCase):
    def test_rates_use_pooled_words_and_paragraph_presence(self):
        paragraphs = [1, 1, 2, 2, 3, 3, 3]
        rows = [{"id": i, "paragraph": p, "text": " ".join(["word"] * i), "label": category}
                for i, (p, category) in enumerate(zip(paragraphs, LABELS), 1)]
        result = audit.sentence_metrics(rows, "en")
        self.assertEqual(result["word_count"], 28)
        self.assertEqual(result["sentence_count"], 7)
        self.assertEqual(result["paragraph_count"], 3)
        self.assertEqual(result["label_counts"], {category: 1 for category in LABELS})
        self.assertEqual(result["U_count"], 3)
        self.assertEqual(result["U_paragraph_count"], 2)
        self.assertAlmostEqual(result["R_U"], 300 / 28)
        self.assertAlmostEqual(result["R_not_shown"], 100 / 28)
        self.assertAlmostEqual(result["P_U"], 2 / 3)
        self.assertEqual(result["P_U_unit"], "paragraph")
        self.assertNotAlmostEqual(result["R_U"], (200 / 3 + 100 / 7) / 3)

    def test_chinese_character_rate_is_not_named_word_rate(self):
        rows = [{"id": 1, "paragraph": 1, "text": "结果有效。", "label": "claim"},
                {"id": 2, "paragraph": 1, "text": "证据不足。", "label": "not_shown"}]
        result = audit.sentence_metrics(rows, "zh")
        self.assertEqual(result["character_count"], 8)
        self.assertEqual(result["R_U_per_100_chars"], 12.5)
        self.assertEqual(result["R_not_shown_per_100_chars"], 12.5)
        self.assertNotIn("R_U", result)
        self.assertNotIn("word_count", result)

    def test_empty_sentences_have_null_rates(self):
        for language, rate in [("en", "R_U"), ("zh", "R_U_per_100_chars")]:
            with self.subTest(language=language):
                result = audit.sentence_metrics([], language)
                self.assertIsNone(result[rate])
                self.assertIsNone(result["P_U"])
                self.assertEqual(result["U_count"], 0)

    def test_retraction_and_softening_have_distinct_numerators(self):
        rows = [{"status": status} for status in ["kept", "weakened", "scoped", "retracted", "dropped"]]
        result = audit.claim_metrics(rows)
        self.assertEqual(result["claim_count"], 5)
        self.assertEqual(result["Ret"], 0.2)
        self.assertEqual(result["Soft"], 0.4)
        self.assertEqual(result["status_counts"]["dropped"], 1)
        self.assertEqual(result["status_counts"]["strengthened"], 0)
        self.assertEqual(audit.claim_metrics([{"status": "retracted"}, {"status": "dropped"}])["Soft"], 0)

    def test_no_original_claims_returns_null_not_zero(self):
        result = audit.claim_metrics([])
        self.assertEqual(result["claim_count"], 0)
        self.assertIsNone(result["Ret"])
        self.assertIsNone(result["Soft"])


class ClaimTests(unittest.TestCase):
    def test_claims_extracted_once_per_original_paragraph(self):
        client, requests = offline_client([
            response_body({"claims": ["The method improves accuracy.", "The effect is causal."]}),
            response_body({"claims": []}),
            response_body({"claims": ["The method is cheaper."]}),
        ])
        with client:
            claims = audit.extract_claims(client, "test-model", "First paragraph.\n\nSettings.\n\nThird paragraph.")
        self.assertEqual([(c["id"], c["paragraph"]) for c in claims], [(1, 1), (2, 1), (3, 3)])
        self.assertEqual(len(requests), 3)
        self.assertEqual(json.loads(requests[1]["input"]), {"original_paragraph": "Settings."})

    def test_tracking_retains_claim_order_and_checks_exact_quotes(self):
        claims = [{"id": 1, "paragraph": 1, "claim": "The method works."},
                  {"id": 2, "paragraph": 1, "claim": "It is cheaper."}]
        client, _ = offline_client([response_body({"claims": [
            {"id": 2, "status": "dropped", "quote": ""},
            {"id": 1, "status": "weakened", "quote": "The method may work."},
        ]})])
        with client:
            rows = audit.track_claims(client, "test-model", "Original.", "The method may work.", claims)
        self.assertEqual([r["id"] for r in rows], [1, 2])
        self.assertEqual([r["status"] for r in rows], ["weakened", "dropped"])
        client, _ = offline_client([response_body({"claims": [
            {"id": 1, "status": "kept", "quote": "Invented quotation."},
        ]})])
        with client, self.assertRaisesRegex(ValueError, "quote"):
            audit.track_claims(client, "test-model", "Original.", "The method may work.", claims[:1])

    def test_tracking_rejects_incomplete_claim_coverage(self):
        client, _ = offline_client([response_body({"claims": []})])
        with client, self.assertRaises(ValueError):
            audit.track_claims(client, "test-model", "Original.", "Rewrite.",
                               [{"id": 1, "paragraph": 1, "claim": "The method works."}])


class ResponseTests(unittest.TestCase):
    def test_real_sdk_parses_schema_and_disables_storage(self):
        client, requests = offline_client([response_body({"sentences": [label(1, "grounded_limit")]})])
        with client:
            result = audit.ask(client, "test-model", "Classify.", {}, audit.Classification)
        self.assertEqual(result.sentences[0].label, "grounded_limit")
        self.assertFalse(requests[0]["store"])
        self.assertEqual(requests[0]["text"]["format"]["type"], "json_schema")

    def test_refusal_and_incomplete_response_fail(self):
        for response in [response_body({}, refusal=True),
                         response_body({"sentences": []}, status="incomplete")]:
            with self.subTest(status=response["status"]):
                client, _ = offline_client([response])
                with client, self.assertRaises(RuntimeError):
                    audit.ask(client, "test-model", "Classify.", {}, audit.Classification)


class CommandTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.input = self.root / "draft.txt"
        self.original = self.root / "original.txt"
        self.report = self.root / "report.json"
        self.rewrite = self.root / "revision.txt"
        self.recording = self.root / "calls.jsonl"
        self.original.write_text("The method improves accuracy.", encoding="utf-8")
        self.input.write_text("The method may improve accuracy.", encoding="utf-8")

    def arguments(self):
        return ["audit_defensive_writing.py", str(self.input), "--model", "test-model",
                "--original", str(self.original), "--report", str(self.report),
                "--responses-jsonl", str(self.recording)]

    def run_main(self, responses, *, rewrite=False, extra=()):
        client, requests = offline_client(responses)
        arguments = self.arguments() + list(extra)
        if rewrite:
            arguments += ["--rewrite", str(self.rewrite)]
        self.recording.write_text("", encoding="utf-8")
        events = []
        sdk_ask = audit.ask

        def record(_unused, model, prompt, data, schema):
            result = sdk_ask(client, model, prompt, data, schema)
            events.append({"request": {"model": model, "instructions": prompt,
                                       "input": data, "schema": schema.model_json_schema()},
                           "response": result.model_dump()})
            return result

        with client, patch.object(audit, "ask", side_effect=record), \
                patch.object(sys, "argv", arguments), redirect_stdout(io.StringIO()):
            self.assertEqual(audit.main(), 0)
        expected = self.report.read_bytes()
        self.report.unlink()
        expected_rewrite = self.rewrite.read_bytes() if rewrite else None
        if rewrite:
            self.rewrite.unlink()
        self.recording.write_text("".join(json.dumps(row) + "\n" for row in events), encoding="utf-8")
        with patch.object(audit, "OpenAI") as constructor, patch.object(sys, "argv", arguments), \
                redirect_stdout(io.StringIO()):
            result = audit.main()
        constructor.assert_not_called()
        self.assertEqual(self.report.read_bytes(), expected)
        if rewrite:
            self.assertEqual(self.rewrite.read_bytes(), expected_rewrite)
        return result, requests

    def before_responses(self):
        return [
            response_body({"claims": ["The method improves accuracy."]}),
            response_body({"sentences": [label(1, "unsupported_doubt")]}),
            response_body({"claims": [{"id": 1, "status": "weakened", "quote": "The method may improve accuracy."}]}),
        ]

    def test_default_audit_reports_sentence_labels_and_claim_changes(self):
        result, requests = self.run_main(self.before_responses())
        self.assertEqual(result, 0)
        self.assertEqual(len(requests), 3)
        self.assertFalse(self.rewrite.exists())
        report = json.loads(self.report.read_text())
        self.assertNotIn("after", report)
        self.assertEqual(report["before"]["sentences"][0]["label"], "unsupported_doubt")
        self.assertEqual(report["before"]["claim_metrics"]["Soft"], 1)

    def test_all_input_slots_use_document_reader(self):
        evidence = self.root / "evidence.docx"
        contents = {self.input: "The method may improve accuracy.",
                    self.original: "The method improves accuracy.",
                    evidence: "Independent source material."}
        with patch.object(audit, "read_document", side_effect=contents.__getitem__) as reader:
            result, requests = self.run_main(self.before_responses(), extra=["--evidence", str(evidence)])
        self.assertEqual(result, 0)
        self.assertEqual({call.args[0] for call in reader.call_args_list}, set(contents))
        sources = json.loads(requests[1]["input"])["sources"]
        self.assertEqual(sources["original"], contents[self.original])
        self.assertEqual(sources["evidence_1"], contents[evidence])

    def test_non_text_revision_suffix_is_rejected_before_api_call(self):
        arguments = self.arguments() + ["--rewrite", str(self.root / "revision.docx")]
        with patch.object(audit, "OpenAI") as constructor, patch.object(sys, "argv", arguments), \
                patch("sys.stderr", new_callable=io.StringIO), self.assertRaises(SystemExit) as error:
            audit.main()
        self.assertEqual(error.exception.code, 2)
        constructor.assert_not_called()

    def test_optional_rewrite_rescores_with_same_original_claims(self):
        responses = self.before_responses() + [
            response_body({"text": "The method improves accuracy."}),
            response_body({"sentences": [label(1, "claim")]}),
            response_body({"claims": [{"id": 1, "status": "kept", "quote": "The method improves accuracy."}]}),
        ]
        result, requests = self.run_main(responses, rewrite=True)
        self.assertEqual(result, 0)
        self.assertEqual(self.input.read_text(), "The method may improve accuracy.")
        self.assertEqual(self.rewrite.read_text(), "The method improves accuracy.")
        report = json.loads(self.report.read_text())
        self.assertEqual(report["before"]["metrics"]["U_count"], 1)
        self.assertEqual(report["after"]["metrics"]["U_count"], 0)
        self.assertEqual(report["after"]["claim_metrics"]["Soft"], 0)
        payloads = [json.loads(request["input"]) for request in requests]
        self.assertEqual(sum("original_paragraph" in payload for payload in payloads), 1)
        self.assertEqual(payloads[2]["claims"], payloads[5]["claims"])
        # 各请求独立：检查实际发出的指令包含所需定义，而非仅引用论文或上一请求。
        for request in requests:
            self.assertNotRegex(request["instructions"], r"(?i)arxiv|2610\.11355|附录")
        for index in (1, 3, 4):
            self.assertIn(audit.LABEL_RULES, requests[index]["instructions"])
        for index in (2, 3, 5):
            self.assertIn(audit.STATUS_RULES, requests[index]["instructions"])

    def test_existing_output_is_not_overwritten_and_api_is_not_called(self):
        for existing in [self.report, self.rewrite]:
            existing.write_text("保留原文件", encoding="utf-8")
            arguments = self.arguments() + ["--rewrite", str(self.rewrite)]
            with self.subTest(existing=existing), patch.object(audit, "OpenAI") as constructor, \
                    patch.object(sys, "argv", arguments), patch("sys.stderr", new_callable=io.StringIO), \
                    self.assertRaises(SystemExit) as error:
                audit.main()
            self.assertEqual(error.exception.code, 2)
            constructor.assert_not_called()
            self.assertEqual(existing.read_text(encoding="utf-8"), "保留原文件")
            existing.unlink()


class ReplayBoundaryTests(unittest.TestCase):
    def test_exact_record_preserves_output_and_rejects_model_rule_material_or_schema_drift(self):
        request = {"model": "recorded", "instructions": "Classify this input.",
                   "input": {"text": "Evidence."}, "schema": audit.Classification.model_json_schema()}
        event = {"request": request, "response": {"sentences": [label(1, "claim")]}}
        result = audit.ask(iter([event]), "recorded", request["instructions"], request["input"], audit.Classification)
        self.assertEqual(result.sentences[0].label, "claim")
        for field in request:
            with self.subTest(field=field), self.assertRaises(ValueError):
                changed = event | {"request": request | {field: "wrong"}}
                audit.ask(iter([changed]), "recorded", request["instructions"], request["input"], audit.Classification)
        with self.assertRaises(ValueError):
            audit.ask(iter([]), "recorded", request["instructions"], request["input"], audit.Classification)
        with self.assertRaises(ValueError):
            audit.ask(iter([event | {"response": {"sentences": [label(1, "invalid")]}}]),
                      "recorded", request["instructions"], request["input"], audit.Classification)

    def test_live_cli_is_rejected_before_reading_manuscripts_or_constructing_sdk(self):
        arguments = ["audit", "draft.txt", "--model", "anything", "--evidence", "evidence.txt",
                     "--report", "out.json"]
        with patch.object(sys, "argv", arguments), patch.object(audit, "OpenAI") as constructor, \
                patch.object(audit, "read_document") as reader, patch("sys.stderr", new_callable=io.StringIO), \
                self.assertRaises(SystemExit) as error:
            audit.main()
        self.assertEqual(error.exception.code, 2)
        constructor.assert_not_called()
        reader.assert_not_called()

    def test_extra_record_fails_without_publishing_report_or_rewrite(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manuscript = root / "draft.txt"
            manuscript.write_text("A result.", encoding="utf-8")
            recording = root / "calls.jsonl"
            report = root / "out.json"
            arguments = ["audit", str(manuscript), "--model", "recorded", "--evidence", str(manuscript),
                         "--responses-jsonl", str(recording), "--report", str(report)]
            for extra in ('{"unconsumed": true}\n', 'null\n'):
                recording.write_text(extra, encoding="utf-8")
                with self.subTest(extra=extra), patch.object(sys, "argv", arguments), \
                        patch.object(audit, "analyze", return_value={"metrics": {}}), \
                        patch.object(audit, "OpenAI") as constructor, self.assertRaises(ValueError):
                    audit.main()
                constructor.assert_not_called()
                self.assertFalse(report.exists())



if __name__ == "__main__":
    unittest.main()
