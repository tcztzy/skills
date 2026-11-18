# Codex Skill Metrics

Local-only hooks for measuring skill triggering quality.

## Files

- `user_prompt_submit.py`: records each user prompt, explicit `$skill` mentions, scored candidate skill hints, and any gold-set expected skills.
- `stop.py`: records observed skills inferred from the last assistant message and transcript, then computes TP/FN/FP when gold labels exist.
- `log_use.py`: optional explicit marker a skill can call when it starts.
- `summarize.py`: aggregates hint counts, observed counts, marker counts, and precision/recall/F1 when gold labels exist.
- `sample_candidates.py`: samples prompt hashes for one candidate skill so you can add gold labels.
- `logs/events.jsonl`: hook events.
- `logs/skill-use.jsonl`: explicit skill-use markers.
- `gold/skills.jsonl`: manually labeled expected skills.

## Gold Labels

Put one JSON object per line in `~/.codex/skill-metrics/gold/skills.jsonl`.

```json
{"id":"001","prompt_sha256":"<sha256 from events.jsonl>","expected_skills":["caveman"],"notes":"Prompt explicitly requested caveman mode."}
```

Copy the hook's `prompt_sha256` and add the expected skill names. Set
`"expected_skills":[]` when no skill applies. On future matching prompts,
any observed skill then counts as a false positive. Unlabeled prompts have
`gold_expected_skills: null` and `confusion: null`. In older logs an empty
list with null confusion carries no usable label.

## Commands

Run from this repository root with Python 3.10 or newer. Logs and labels live under
`~/.codex/skill-metrics/`.

```sh
python3 .codex/skill-metrics/summarize.py
python3 .codex/skill-metrics/summarize.py --json
python3 .codex/skill-metrics/sample_candidates.py imagegen --limit 25 --gold-template
python3 .codex/skill-metrics/log_use.py caveman --source skill
```

Set `SKILL_METRICS_STORE_TEXT=0` before launching Codex to store only hashes instead of prompt/assistant text.

## Limits

Candidate skills are hints, not expected labels. Each new event stores `candidate_skill_matches` with a score and reasons, while the legacy `candidate_expected_skills` field is kept for old readers. A high candidate count means "worth sampling", not "should have triggered".

The Stop hook uses the transcript path supplied by its event. A missing path or
a transcript that declares a different session ID leaves only the event's own
messages available for scoring.

Observed skills are inferred from explicit `$skill` mentions and assistant text
patterns. The summary counts explicit `log_use.py` markers separately. Compare
scored outcomes with the underlying task before using them in a retirement
decision.
