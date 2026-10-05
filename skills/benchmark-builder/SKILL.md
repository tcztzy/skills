---
name: benchmark-builder
description: Build or audit benchmark tasks, scoring contracts, rubrics, evaluators, review examples, pilot plans, and release policies. Use when designing model or agent evaluations, checking construct validity, defining score boundaries, calibrating judges, or controlling contamination and benchmark lifecycle.
---

# Benchmark Builder

Design the measurement contract before writing many items. Optimize for construct
validity and evaluator reliability, not item count.

## Choose an archetype

- `short_answer`: one bounded decision or factual judgment.
- `multistep_reasoning`: dependent steps whose intermediate artifacts are
  observable.
- `coding`: executable behavior is the source of truth.
- `agentic`: tools, mutable state, recovery, safety, and collateral effects matter.

## Workflow

### 1. Write the charter

Define:

- deployment decision the score will inform
- primary construct and allowed secondary constructs
- evidence and tools available to the solver
- task family and success artifact or end state
- scoring method and reportable score granularity
- shortcut, leakage, contamination, privacy, and safety threats

Reject a proposed task if success can come mainly from a surface cue,
memorization, or an unintended capability. Do not require private chain-of-thought;
score observable reasoning products or state transitions.

### 2. Specify the task contract

Every item must state:

- objective, inputs, constraints, and output schema
- allowed and forbidden tools or mutations
- what constitutes success, partial progress, and hard failure
- whether multiple solution paths are valid
- edge cases and invariants the evaluator will inspect

Draft the evaluator alongside the item. If the expected result cannot be checked
reliably, revise the task before expanding the set.

### 3. Choose the evaluator

Prefer the least subjective evaluator that preserves the intended construct:

1. exact or schema match
2. programmatic checker
3. executable behavior or artifact test
4. state-based checker
5. calibrated human rating
6. grounded LLM judge

Prefer final-state and artifact checks over exact action traces. For mutable
environments, check both requested success and collateral damage.

Use an LLM judge only when deterministic checking would discard essential
quality. Give it the rubric, reference evidence, and permitted evidence packet;
blind model identity where possible and measure judge-human agreement on a
sample.

### 4. Lock the scoring contract

Use analytic criteria with observable boundaries. For each criterion define:

- `pass_if`
- `partial_if`, if partial credit is meaningful
- `fail_if`
- `common_false_positive`
- `why_it_matters`

Also define:

- `score_unit`
- `requires_reasoning_correct_for_any_credit`
- `global_zero_if`
- `criterion_specs`
- `score_bands`
- `hard_fail_conditions`

Pre-score these variants before release:

- fully correct
- correct answer for the wrong reason
- partial
- wrong but plausible
- off-scope or fabricated

If reasoning is the construct, a correct conclusion supported by an incorrect
mechanism or invalid evidence receives zero credit.

Provide a review example for every reportable score or named score band. Include
an off-topic or fabricated zero, and a correct-answer/wrong-reason zero whenever
the reasoning gate applies. See `references/examples-good-vs-bad.md` for
source-backed boundary patterns.

### 5. Add archetype-specific checks

For multistep reasoning:

- require three to seven dependent steps
- expose at least one intermediate transformation
- make the final result depend on multiple prior steps
- include a verification step and a plausible near-miss

For coding:

- treat executable tests as the scoring source of truth
- test behavior, interfaces, failure cases, and unintended changes
- keep hidden tests consistent with the public contract

For agentic tasks:

- specify initial state, mutable state, budgets, and permissions
- define `state_invariants`, `allowed_mutations`, and `recovery_events`
- define success, failure, and timeout termination rules and a rerun policy
- record end state, relevant logs, cost, and unsafe side effects
- distinguish capability failure from infrastructure or evaluator failure

### 6. Pilot before release

Pilot a representative subset and:

- rerun stochastic systems
- inspect false positives and false negatives
- double-rate a human-scored subset
- review judge disagreements and checker brittleness
- estimate item difficulty from outcomes, not author intuition
- remove leaked, ambiguous, or shortcut-prone items

Separate train, development, and test items by source, time, or author where
appropriate; check for near-duplicates and keep a private holdout. Record seeds
and environment versions, and set a freshness cutoff for changing external facts.

Version tasks, data, checkers, rubrics, and judge prompts together. Record
provenance, collection date, split, exposure risk, and retirement policy.
Consult `references/primary-sources.md` when the benchmark design needs formal
support or source attribution.

## Required output

Return:

1. benchmark charter
2. item specifications grouped by archetype and difficulty
3. embedded scoring contracts and review examples
4. evaluator/checker design
5. pilot and adjudication plan
6. contamination, versioning, and retirement policy
7. unresolved validity risks

When auditing an existing benchmark, lead with the highest-risk validity or
evaluator defects and propose the smallest repair that makes the score
interpretable.
