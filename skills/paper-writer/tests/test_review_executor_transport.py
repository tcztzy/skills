"""Offline contract tests; the external executor and any model are never executed."""

from contextlib import redirect_stdout
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import test_audit_defensive_writing as fixtures

audit, label, response_body = fixtures.audit, fixtures.label, fixtures.response_body


class LedgerTransportTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.journal = self.root / "calls.jsonl"
        self.requests = self.root / "requests"
        self.executor = Path("/not-executed/review_executor.py")
        self.state = self.root / "state"
        self.model = "deepseek/deepseek-v4.1-flash"

    def transport(self, execute=False):
        return audit.LedgerCalls(self.journal, self.requests,
                                 self.executor if execute else None, self.state if execute else None)

    def pending(self):
        with self.transport() as client, self.assertRaises(audit.PendingReview):
            audit.ask(client, self.model, "Classify.", {"text": "Evidence."}, audit.Classification)
        return next(self.requests.glob("*.txt"))

    def prepare_state(self, prompt, status="READY", response=None, review_id="fixture-review"):
        self.state.mkdir(exist_ok=True)
        fingerprint = hashlib.sha256(prompt.read_bytes()).hexdigest()
        state = {"config": {"review_id": review_id, "target": "offline fixture",
                            "provider": "cmdcode", "model": self.model, "effort": "max",
                            "scope": {"audit_request_sha256": fingerprint}, "prompt": str(prompt),
                            "zero_tools_overlay_verified": True, "pinned_files": {str(prompt): fingerprint}},
                 "status": status, "unknown_requests": [], "requests": []}
        if response is not None:
            state["outcome_status"] = "COMPLETE"
            state["requests"] = [{"id": "receipt-1", "result": {"final": json.dumps(response)}}]
        (self.state / "state.json").write_text(json.dumps(state), encoding="utf-8")
        return state

    def answer(self, state, response):
        state.update(status="COMPLETE", outcome_status="COMPLETE")
        state["requests"] = [{"id": state["config"]["review_id"] + "-request",
                              "result": {"final": json.dumps(response)}}]
        (self.state / "state.json").write_text(json.dumps(state), encoding="utf-8")
        return subprocess.CompletedProcess([], 0, "{}", "")

    def test_prepare_exports_complete_request_without_executor_or_sdk(self):
        with patch.object(audit.subprocess, "run") as run, patch.object(audit, "OpenAI") as sdk:
            pending = self.pending()
        run.assert_not_called(); sdk.assert_not_called()
        packet = json.loads(pending.read_text())
        self.assertEqual(packet["request"], {"model": self.model, "instructions": "Classify.",
                                           "input": {"text": "Evidence."},
                                           "schema": audit.Classification.model_json_schema()})
        self.assertFalse(self.journal.exists())

    def test_prepare_cannot_launch_and_journal_cannot_overwrite_an_artifact(self):
        base = ["audit", "draft.txt", "--model", self.model, "--evidence", "evidence.txt", "--report", "report.json"]
        cases = [["--responses-jsonl", "calls.jsonl", "--prepare-review", "--review-executor", str(self.executor), "--review-state", str(self.state)],
                 ["--responses-jsonl", "draft.txt", "--prepare-review"],
                 ["--responses-jsonl", "report.json", "--prepare-review"]]
        for extra in cases:
            with self.subTest(extra=extra), patch.object(sys, "argv", base + extra), \
                    patch("sys.stderr", new_callable=io.StringIO), patch.object(audit.subprocess, "run") as run, \
                    patch.object(audit, "read_document") as reader, self.assertRaises(SystemExit) as error:
                audit.main()
            self.assertEqual(error.exception.code, 2)
            run.assert_not_called(); reader.assert_not_called()

    def test_only_run_is_invoked_and_receipt_is_durable_before_next_request(self):
        prompt = self.pending(); state = self.prepare_state(prompt)
        with patch.object(audit.subprocess, "run", side_effect=lambda *a, **k: self.answer(state, {"sentences": [label(1, "claim")]})) as run:
            with self.transport(True) as client:
                self.assertEqual(audit.ask(client, self.model, "Classify.", {"text": "Evidence."}, audit.Classification).sentences[0].label, "claim")
                self.assertEqual(len(self.journal.read_text().splitlines()), 1)
                with self.assertRaises(audit.PendingReview):
                    audit.ask(client, self.model, "Next.", {}, audit.Claims)
        self.assertEqual(run.call_count, 1)
        self.assertEqual(run.call_args.args[0], [sys.executable, str(self.executor), "run", "--state-dir", str(self.state)])
        record = json.loads(self.journal.read_text())
        self.assertEqual(record["ledger_request_ids"], ["fixture-review-request"])

    def test_wrong_model_scope_prompt_pin_or_overlay_never_launches(self):
        prompt = self.pending()
        for field in ("model", "scope", "prompt", "pinned_files", "zero_tools_overlay_verified"):
            with self.subTest(field=field):
                state = self.prepare_state(prompt)
                state["config"][field] = {"scope": {}, "pinned_files": {}, "prompt": str(self.root / "absent"),
                                           "zero_tools_overlay_verified": False}.get(field, "wrong-model")
                (self.state / "state.json").write_text(json.dumps(state))
                with patch.object(audit.subprocess, "run") as run, self.transport(True) as client, self.assertRaises((ValueError, OSError)):
                    audit.ask(client, self.model, "Classify.", {"text": "Evidence."}, audit.Classification)
                run.assert_not_called()

    def test_unknown_and_budget_pause_do_not_resubmit(self):
        prompt = self.pending()
        for status in ("UNKNOWN_REQUIRES_RECONCILIATION", "PAUSE_REQUIRES_USER_APPROVAL", "FAILED"):
            with self.subTest(status=status):
                self.prepare_state(prompt, status)
                with patch.object(audit.subprocess, "run") as run, self.transport(True) as client, self.assertRaises(RuntimeError):
                    audit.ask(client, self.model, "Classify.", {"text": "Evidence."}, audit.Classification)
                run.assert_not_called()

    def test_completed_paused_result_and_split_json_are_consumed_without_run(self):
        prompt = self.pending(); state = self.prepare_state(prompt, "PAUSE_REQUIRES_USER_APPROVAL", {"sentences": [label(1, "claim")]})
        final = state["requests"][0]["result"]["final"]
        state["requests"] = [{"id": "partial", "result": {"final": final[:20]}},
                             {"id": "completed", "result": {"final": final[20:]}}]
        (self.state / "state.json").write_text(json.dumps(state))
        with patch.object(audit.subprocess, "run") as run, self.transport(True) as client:
            result = audit.ask(client, self.model, "Classify.", {"text": "Evidence."}, audit.Classification)
        self.assertEqual(result.sentences[0].id, 1); run.assert_not_called()
        self.assertEqual(json.loads(self.journal.read_text())["ledger_request_ids"], ["partial", "completed"])

    def test_controller_failure_or_invalid_json_retains_ledger_without_resend(self):
        prompt = self.pending(); self.prepare_state(prompt)
        def uncertain(*args, **kwargs):
            self.prepare_state(prompt, "UNKNOWN_REQUIRES_RECONCILIATION")
            return subprocess.CompletedProcess([], 1, "", "not printed")
        with patch.object(audit.subprocess, "run", side_effect=uncertain) as run:
            for _ in range(2):
                with self.transport(True) as client, self.assertRaises(RuntimeError):
                    audit.ask(client, self.model, "Classify.", {"text": "Evidence."}, audit.Classification)
        self.assertEqual(run.call_count, 1); self.assertFalse(self.journal.exists())
        self.prepare_state(prompt, "COMPLETE", {"sentences": [label(1, "invalid")]})
        with patch.object(audit.subprocess, "run") as run, self.transport(True) as client, self.assertRaises(ValueError):
            audit.ask(client, self.model, "Classify.", {"text": "Evidence."}, audit.Classification)
        run.assert_not_called(); self.assertFalse(self.journal.exists())

    def test_full_six_stage_audit_resumes_only_matching_ledgers_and_preserves_outputs(self):
        fixture = fixtures.CommandTests("test_optional_rewrite_rescores_with_same_original_claims")
        fixture.setUp(); self.addCleanup(fixture.doCleanups)
        responses = fixture.before_responses() + [response_body({"text": "The method improves accuracy."}),
                     response_body({"sentences": [label(1, "claim")]}),
                     response_body({"claims": [{"id": 1, "status": "kept", "quote": "The method improves accuracy."}]})]
        fixture.run_main(responses, rewrite=True)
        events = [json.loads(line) for line in fixture.recording.read_text().splitlines()]
        for event in events: event["request"]["model"] = self.model
        report = self.root / "report.json"; rewrite = self.root / "revised.txt"
        base = ["audit", str(fixture.input), "--original", str(fixture.original), "--model", self.model,
                "--report", str(report), "--rewrite", str(rewrite), "--responses-jsonl", str(self.journal),
                "--request-dir", str(self.requests)]
        with patch.object(sys, "argv", base + ["--prepare-review"]), redirect_stdout(io.StringIO()), patch.object(audit.subprocess, "run") as run:
            self.assertEqual(audit.main(), 3)
        run.assert_not_called()
        calls = []
        for index, event in enumerate(events):
            prompt = sorted(self.requests.glob("*.txt"))[-1]
            self.assertEqual(json.loads(prompt.read_text())["request"], event["request"])
            self.state = self.root / f"state-{index}"
            state = self.prepare_state(prompt, review_id=f"authorized-fixture-{index}")
            arguments = base + ["--review-executor", str(self.executor), "--review-state", str(self.state)]
            with patch.object(sys, "argv", arguments), redirect_stdout(io.StringIO()), \
                    patch.object(audit.subprocess, "run", side_effect=lambda *a, **k: self.answer(state, event["response"])) as run, \
                    patch.object(audit, "OpenAI") as sdk:
                self.assertEqual(audit.main(), 0 if index == len(events) - 1 else 3)
            calls.extend(run.call_args_list); sdk.assert_not_called()
        actual = json.loads(report.read_text()); expected = json.loads(fixture.report.read_text())
        actual.pop("ledger_states"); actual.pop("execution"); expected.pop("execution")
        expected["model"] = self.model
        self.assertEqual(actual, expected)
        self.assertEqual(rewrite.read_bytes(), fixture.rewrite.read_bytes())
        self.assertEqual(len(calls), 6)
        records = [json.loads(line) for line in self.journal.read_text().splitlines()]
        self.assertEqual(len(records), 6)
        self.assertEqual(len({row["ledger_state"] for row in records}), 6)
        self.assertEqual(len(list(self.requests.glob("*.txt"))), 6)


if __name__ == "__main__":
    unittest.main()
