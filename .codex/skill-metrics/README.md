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

Use one JSON object per line:

```json
{"id":"001","prompt_sha256":"<sha256 from events.jsonl>","expected_skills":["caveman"],"notes":"Prompt explicitly requested caveman mode."}
```

The hook records `prompt_sha256`; copy that hash into `gold/skills.jsonl` and add the expected skill names. Future matching prompts then get confusion metrics.

## Commands

```bash
python3 /Users/tcztzy/.codex/skill-metrics/summarize.py
python3 /Users/tcztzy/.codex/skill-metrics/summarize.py --json
python3 /Users/tcztzy/.codex/skill-metrics/sample_candidates.py imagegen --limit 25 --gold-template
python3 /Users/tcztzy/.codex/skill-metrics/log_use.py caveman --source skill
```

Set `SKILL_METRICS_STORE_TEXT=0` before launching Codex to store only hashes instead of prompt/assistant text.

## Limits

Candidate skills are hints, not expected labels. Each new event stores `candidate_skill_matches` with a score and reasons, while the legacy `candidate_expected_skills` field is kept for old readers. A high candidate count means "worth sampling", not "should have triggered".

Codex hooks do not expose a native `skill_activated` field. Observed skills are inferred from explicit `$skill` mentions, assistant text patterns, and optional `log_use.py` markers. Precision/recall become meaningful only after `gold/skills.jsonl` has labels.
