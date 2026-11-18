"""Exercise the skill metrics hook and summary CLIs under a fresh user profile.

Fixtures include explicit positive, negative and absent labels, and two
conversations. Only files beneath a temporary directory receive logs.
"""

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPTS = Path(__file__).resolve().parents[1]


class HookScoringTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.profile = Path(temporary.name)
        self.metrics = self.profile / ".codex" / "skill-metrics"
        self.env = dict(os.environ, HOME=temporary.name, USERPROFILE=temporary.name,
                        SKILL_METRICS_STORE_TEXT="0", PYTHONDONTWRITEBYTECODE="1")
        gold_dir = self.metrics / "gold"
        gold_dir.mkdir(parents=True)
        with (gold_dir / "skills.jsonl").open("w", encoding="utf-8") as gold:
            for prompt, expected in [("negative", []), ("positive", ["example-skill"])]:
                row = {"id": prompt, "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
                       "expected_skills": expected}
                gold.write(json.dumps(row) + "\n")

    def invoke(self, script, arguments=(), payload=None):
        result = subprocess.run(
            [sys.executable, "-B", str(SCRIPTS / script), *arguments],
            input=json.dumps(payload), capture_output=True, text=True, env=self.env,
            check=True,
        )
        self.assertEqual(result.stderr, "")
        return result.stdout

    def stop(self, **payload):
        self.invoke("stop.py", payload=payload)
        lines = (self.metrics / "logs" / "events.jsonl").read_text(encoding="utf-8").splitlines()
        return json.loads(lines[-1])

    def test_explicit_negative_and_unlabeled_events_score_differently(self):
        fields = {"last_assistant_message": "Using $example-skill"}
        negative = self.stop(last_user_message="negative", **fields)
        self.assertEqual(negative["gold_expected_skills"], [])
        self.assertEqual(negative["confusion"], {"tp": [], "fn": [], "fp": ["example-skill"]})
        unknown = self.stop(last_user_message="unlabeled", **fields)
        self.assertIsNone(unknown["gold_expected_skills"])
        self.assertIsNone(unknown["confusion"])
        row, = json.loads(self.invoke("summarize.py", ["--json"]))["skills"]
        self.assertEqual((row["observed_count"], row["fp"], row["f1"]), (2, 1, 0.0))

    def test_stop_uses_the_transcript_named_by_its_event(self):
        sessions = self.profile / ".codex" / "sessions"
        sessions.mkdir()
        transcript = sessions / "a.jsonl"
        rows = [
            {"type": "session_meta", "payload": {"id": "a"}},
            {"role": "user", "content": "positive"},
            {"role": "assistant", "content": "Using $example-skill"},
        ]
        transcript.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
        matching = self.stop(sessionId="a", transcriptPath=str(transcript))
        self.assertEqual(matching["confusion"]["tp"], ["example-skill"])
        for payload in ({}, {"transcript_path": str(sessions / "missing")}, {"transcript_path": str(transcript)}):
            with self.subTest(payload=payload):
                event = self.stop(session_id="b", **payload)
                self.assertIsNone(event["transcript_path"])
                self.assertIsNone(event["prompt_sha256"])
                self.assertIsNone(event["confusion"])


if __name__ == "__main__":
    unittest.main()
