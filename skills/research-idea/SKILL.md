---
name: research-idea
description: Generate, validate, novelty-check, triage, and reposition research ideas. Use when turning a topic into testable proposals; checking idea JSON; searching for close prior work; deciding GO, KILL, PIVOT, or SCOPE-DOWN; identifying the smallest decisive experiments; or sharpening a project's central claim, timing, audience, and paper story.
---

# Research Idea

Move a research direction from a vague topic to an evidence-bound decision. Use
only the modes the request needs; run the full sequence when the user wants an
end-to-end idea assessment.

## Select the mode

- `generate`: produce concrete, falsifiable candidate ideas.
- `validate`: check a proposal against the idea schema.
- `novelty-check`: search for close prior work and record the search scope.
- `triage`: choose `GO`, `KILL`, `PIVOT`, or `SCOPE-DOWN`.
- `position`: sharpen the core claim, intended reader, timing, and paper story.

Route full manuscript drafting to `paper-writer`, formal peer review to
`paper-reviewer`, and library management to `zotero`.

## Workflow

1. Establish the decision context.
   - Identify stage: topic, idea, active experiments, draft, or pre-submission.
   - Record constraints: data, compute, time, expertise, venue, and risk.
   - Ask what decision the user needs now rather than evaluating everything.
2. State the strongest truthful thesis.
   - Write one falsifiable hypothesis or core claim.
   - Write one sentence answering why the result would matter.
   - If success would still yield a trivial conclusion, stop and triage before
     proposing more experiments.
3. Generate or normalize candidates.
   - Prefer one to three distinct ideas over cosmetic variants.
   - Tie every experiment to a hypothesis, baseline, metric, and failure signal.
   - For structured proposals, follow `references/idea-schema.md` and validate:

```bash
uv run -s scripts/idea_schema_validate.py --in ideas.json
```

4. Check novelty cautiously.
   - Decompose each idea into task, mechanism, setting, and closest baseline.
   - Run several broad, mechanism-specific, and baseline-centered queries.
   - Record exact queries, date, and closest results.
   - The helper is offline by default. Use `--online` only with user approval:

```bash
uv run -s scripts/s2_search.py --query "task mechanism"
uv run -s scripts/s2_search.py --online --query "task mechanism" --limit 10
```

   - Read `references/novelty-check.md` before writing novelty claims.
5. Run impact and feasibility triage.
   - Test importance, falsifiability, comparative advantage, feasibility, timing,
     and the hardest obvious prior-work objection.
   - Identify the smallest evidence that would change the decision.
   - Do not recommend experiments that merely make the project look busier.
6. Commit to one decision.
   - `GO`: the claim matters and remaining work is execution.
   - `KILL`: even the best-case truthful conclusion is weak or infeasible.
   - `PIVOT`: the evidence supports a different, more meaningful claim.
   - `SCOPE-DOWN`: one narrower claim can work, but the current project is
     overloaded.
7. Return the next action.
   - Name the decisive experiment, search, analysis, or story correction.
   - Separate observed evidence, inference, and unresolved uncertainty.

## Output contracts

For proposal generation, return idea JSON when machine-readable output is
useful; use `references/prompt-templates.md` and `references/idea.schema.json`.

For triage or positioning, use `assets/strategy-memo-template.md`. Always include
one explicit decision and the immediate next action.

## Load references only when needed

- Selecting whether an idea is worth investment:
  `references/idea-selection.md`
- Choosing GO/KILL/PIVOT/SCOPE-DOWN and required evidence:
  `references/project-triage.md`
- Repairing a paper's single-claim story:
  `references/paper-story.md`
- Evaluating timing, audience, or "why now":
  `references/timing-and-positioning.md`
- Network, privacy, novelty, and disclosure constraints:
  `references/safeguards.md`

## Guardrails

- A literature search is a sanity check, not proof of novelty.
- Never turn absent search results into "first work" language.
- Treat impact and timing as judgments under uncertainty.
- Prefer one decisive experiment to an unbounded experiment list.
- Do not preserve a weak direction because of sunk cost.
- Do not invent citations, results, available data, or team advantages.

## Example

Input: "We improve one baseline by 1.5% on one dataset. Is this a paper, and what
should we test next?"

Output: identify the strongest possible claim, check whether nearby work already
supports it, select one decision, and name the minimum robustness or
generalization test that would change that decision.
