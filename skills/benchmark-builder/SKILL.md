---
name: benchmark-builder
description: Build high-quality benchmark items, embedded scoring contracts, review examples, rubrics, evaluators, and release protocols for model and agent evaluation. Use when prompts mention benchmark construction, item writing, rubric design, score-boundary design, checker design, review examples, benchmark health, contamination control, pilot calibration, or auditing an existing benchmark set.
metadata:
  aliases: "agentic-evaluation-question-design,evaluation-question-design,benchmark-design"
---

# Benchmark Builder

Use this skill to construct benchmark-ready task sets with clear measurement targets, analytic rubrics, evaluator protocols, explicit benchmark-lifecycle decisions, and type-specific authoring patterns for short-answer, multistep reasoning, and coding tasks.
Write outputs in English unless the user explicitly requests another language.
When updating an existing benchmark, treat the current item specs, checkers, and score reports as artifacts to audit rather than assumptions to preserve.

## Archetypes

Use one of these item archetypes before drafting details:
- `short_answer`: one local decision or light reasoning judgment, usually rubric-scored.
- `multistep_reasoning`: 3-5 dependent steps, possibly `multi_skill_synthesis`, with step-level evaluation.
- `coding`: code-generation task with tests-as-source-of-truth, typically pass/fail.

Choose the archetype first, then tailor the scoring contract and review examples to that archetype.

## Workflow

1. Write a benchmark charter before writing items.
2. Define the evidence model and scoring model.
3. Choose task formats that truly require the target capability.
4. Write items with controlled difficulty and minimal shortcut paths.
5. Lock scoring boundaries and embed `scoring_contract` plus `review_examples` inside the item before finalizing it.
6. Add multi-step reasoning and agentic state where needed.
7. Add safety, trustworthiness, and recovery constraints.
8. Pilot with reruns, rater calibration, and checker audits.
9. Package metadata, holdouts, and lifecycle policy.

## 1) Write A Benchmark Charter First

Use an ECD-lite charter before drafting any item.
If you cannot explain what evidence would count as success or failure, the construct is still underspecified.

Minimum charter checklist:
- `deployment_scenario`: Where the benchmark result will be used.
- `primary_construct`: The one capability the item should primarily measure.
- `secondary_constructs`: Allowed secondary skills that may appear but should not dominate scoring.
- `evidence_model`: Allowed evidence channels such as provided text, web retrieval, local tools, code execution, or environment state.
- `task_model`: The family of tasks that can legitimately elicit the construct.
- `scoring_model`: How success will be checked and who or what will judge it.
- `threat_model`: Shortcut paths, contamination risk, prompt leakage, judge gaming, or task-specific exploits.
- `risk_policy`: Hallucination tolerance, refusal expectations, safety constraints, and privacy boundaries.
- `success_granularity`:
  - `final_only`: score only the final answer or artifact.
  - `process_plus_final`: score observable checkpoints plus the final answer.

Reject items that mainly measure an unintended shortcut such as keyword recall, template matching, or benchmark contamination.
Do not require private chain-of-thought as the gold artifact. Score observable intermediate products instead.

## 2) Choose Task Formats That Force The Target Capability

Pick a format only if the capability is genuinely needed to solve it.

Common task families:
- `Reasoning`: math, logic, scientific inference, structured synthesis.
- `Tool-routed QA`: the model must choose and sequence tools correctly.
- `Interactive web task`: the model must navigate, extract, verify, and act in a browser.
- `Repository task`: the model must modify code, run checks, and satisfy repository-grounded constraints.
- `Desktop workflow task`: the model must operate across apps and files with stateful side effects.
- `Research synthesis task`: the model must retrieve, triage, compare, and cite evidence.

For every task family, specify:
- The observable artifact or end state that represents success.
- Whether multiple solution paths are valid.
- Which state changes are allowed or forbidden.
- What partial progress signals should be recorded.
- Which failure modes should count as capability failure versus evaluator noise.

## 3) Write Strong Benchmark Items

Apply these design rules:
- Keep objective, scope, and answerability unambiguous.
- Provide all required information or explicitly require retrieval.
- Remove accidental cues that reveal the answer without reasoning.
- Specify one intended reasoning path and at least one acceptable alternative path.
- Cap irrelevant context; include distractors only if they test robustness, not reading fatigue.
- Specify output format exactly: schema, units, precision, ordering, and citation style if needed.
- For agentic tasks, define the success artifact or state explicitly, not just the intent.
- Add at least one edge-case condition for medium or hard items.
- Do not hide required behavior in unofficial tests, unstated assumptions, or evaluator code.

Use this item quality gate:
- `Clarity`: another evaluator can restate the task with no ambiguity.
- `Determinacy`: expected answer or end state can be verified objectively.
- `Construct purity`: success depends on the target capability, not test-taking artifacts.
- `Difficulty control`: easy, medium, and hard labels align with pilot outcomes.
- `Shortcut audit`: the answer is not trivially recoverable from leakage, memorization, or surface heuristics.
- `State observability`: for interactive tasks, success and damage can be observed from logs or final state.
- `Checkerability`: a reliable evaluator exists before the task is released.

## 4) Design Evaluators Before Finalizing Items

Prefer the cheapest reliable evaluator that preserves construct validity.
Use this order of preference:
1. `Exact match` for strict answers or schemas.
2. `Programmatic checker` for structured outputs.
3. `Executable checker` for code or artifact behavior.
4. `State-based checker` for interactive tasks with mutable environments.
5. `Calibrated human rating` when automated checking is impossible.
6. `Grounded LLM judge` only when the item is open-ended and properly anchored.

Rules for evaluators:
- Prefer end-state and artifact checks over action-trace exact match.
- Allow multiple valid solution paths whenever the environment permits them.
- Add `collateral_damage_checks` for tasks that can succeed while causing unsafe or incorrect side effects.
- Separate evaluator errors from model errors by reviewing false positives and false negatives during piloting.
- If a checker depends on hidden assumptions, revise the task or expose those assumptions explicitly.

Rules for LLM judges:
- Use them only when a deterministic or executable checker is not feasible.
- Provide a rubric, reference answer or reference artifacts, and the evidence packet the judge may use.
- Blind the judge to model identity and answer order when possible.
- Sample disagreements for human adjudication.
- Report judge-human agreement rather than only judge-produced scores.
- Do not use an ungrounded judge as the sole source of factual correctness when a checker could exist.

## 5) Build Scoring Points And Scoring Standards

Prefer analytic rubrics over single holistic scores.
Keep outcome, process, and safety dimensions distinct when the task can affect external state.

Lock scoring boundaries before declaring an item done.
At item-writing time, embed a `scoring_contract` and `review_examples` inside the item or task spec rather than storing the scoring logic only in prose.

Pre-commit how the evaluator should score at least these answer variants:
- `fully_correct`
- `correct_answer_wrong_reason`
- `partial`
- `wrong_but_plausible`
- `off_scope_or_fabricated`

For each criterion, define the observable scoring boundary:
- `pass_if`: the exact claim, artifact, or state change that earns credit.
- `partial_if`: what counts as incomplete but nonzero credit when your scale allows partial credit.
- `fail_if`: the missing element, contradiction, or error that should fail the criterion.
- `common_false_positive`: a tempting near-miss that should not accidentally pass.
- `why_it_matters`: why this criterion exists and what near-miss it is meant to separate.

If the benchmark is supposed to test reasoning rather than answer recall, add a zero-credit gate:
- A correct final answer with incorrect reasoning, mechanism, evidence, or causal explanation must receive `0` or `fail`, even if the conclusion matches the gold answer.

Mandatory scoring-contract fields:
- `score_unit`
- `requires_reasoning_correct_for_any_credit`
- `global_zero_if`
- `criterion_specs`
- `score_bands`

Mandatory review-example policy:
- Every achievable score must have at least one `review_example`.
- For low-cardinality scores, cover every score exactly.
- For larger numeric scales, redesign into named score bands before release so examples can cover every reported outcome.
- Score `0` must include an off-topic / fabricated example.
- When `requires_reasoning_correct_for_any_credit` is true, score `0` must also include a correct-answer / wrong-reason example.

For boolean or low-entropy judges:
- Make every rubric point atomic and independently observable from the final answer or artifact.
- Avoid composite bullets that merge decision, condition, and rationale unless you truly want them to rise and fall together.
- Provide at least one representative pass anchor and one representative fail anchor for each bullet.
- Require an answer-variant table that shows the exact expected score or pass/fail pattern before release.

Recommended rubric skeleton (100-point total):
- `Task completion` (0-30): Did the output or end state solve the requested objective?
- `Reasoning / decision quality` (0-20): Were key steps valid and logically connected?
- `Evidence use` (0-15): Were claims grounded in correct retrieved or provided evidence?
- `Constraint adherence` (0-15): Did the answer respect required format, budget, tools, and stated policies?
- `Verification and recovery` (0-10): Did the system check its own work and recover from mistakes when needed?
- `Safety and trustworthiness` (0-10): Did the system avoid privacy leaks, unsafe actions, and prohibited shortcuts?

Add hard-fail conditions when required:
- Fabricated evidence or citations.
- Violation of explicit safety or privacy constraints.
- Unsupported final claim delivered with high confidence.
- Non-compliance with mandatory output format.
- Success achieved only through forbidden tools or disallowed state changes.

Use explicit level definitions per criterion:
- `0 = missing or incorrect`
- `1 = partial`
- `2 = acceptable`
- `3 = strong`
- `4 = excellent`

Then map level scores to points with fixed weights.
Before pilot release, create a compact scoring contract with:
- `criterion_specs`: criterion-level pass/fail/partial semantics.
- `score_bands`: explicit definitions for every reportable score or score band.
- `review_examples`: examples covering every reportable score.
- `hard_fail_conditions`: global failure states that override point totals.

For human rating quality control:
- Double-rate a pilot subset.
- Resolve rubric ambiguity before full annotation.
- Track inter-rater agreement and disagreement hotspots.
- Keep an adjudication log for recurrent ambiguity patterns.

## 6) Build Multi-Step Reasoning Tasks

Encode compositional reasoning explicitly:
- Decompose target reasoning into 3-7 dependent steps.
- Make at least one step require an intermediate state transformation.
- Make the final answer depend on multiple prior steps, not one local lookup.
- Add one plausible distractor branch to test correction behavior.
- Use contrastive variants with similar wording but different correct conclusions.

Use this design pattern:
1. `State`: give initial facts and resources.
2. `Transition`: require operations that transform state.
3. `Check`: require a verification or consistency check.
4. `Commit`: require the final answer in a strict schema.

Guard against shallow pattern matching:
- Vary entity names and surface wording.
- Keep the reasoning graph stable while paraphrasing text.
- Audit whether the answer can be guessed from one local cue.

## 7) Build Tasks For Agentic Capability

Define which agentic abilities are tested:
- Planning and decomposition.
- Tool selection and invocation.
- Long-horizon execution.
- Error detection and recovery.
- Memory and state tracking across turns.
- Cost and time efficiency under budget constraints.
- Safe completion under policy.

Define the environment contract in every task:
- Available tools and forbidden tools.
- Time, token, and call budget.
- Initial state and mutable state.
- `state_invariants`: conditions that must remain true.
- `allowed_mutations`: state changes that are permitted.
- `recovery_events`: what counts as a recoverable error and how it is observed.
- `termination_rule`: how success, failure, and timeout are determined.
- Observable logs, artifacts, or screenshots for judging.
- `rerun_policy`: whether the task should be evaluated once or across multiple reruns.

Score both outcomes and process:
- Outcome score: success of the final artifact or state.
- Process score: plan quality, tool efficiency, verification, and recovery from mistakes.
- Penalty score: unnecessary tool spam, policy violations, brittle behavior, or collateral damage.
- For high-risk tasks, separate `raw_success` from `success_under_policy`.

## 8) Reliability, Contamination, And Benchmark Health

Apply benchmark hygiene before release:
- Split by source, time, or author to reduce contamination.
- Hide test answers and keep a private holdout.
- Avoid near-duplicate items across train, dev, and test.
- Write deterministic auto-checkers where possible.
- Use fixed seeds and environment snapshots for reproducibility.
- Set a `freshness_cutoff` for tasks that depend on changing external information.
- Add contamination probes for public benchmarks or public leaderboards.

Run pilot and calibration:
- Pilot with multiple models or agents and at least one human baseline.
- Inspect false positives and false negatives from checkers.
- Rebalance difficulty if all systems cluster too high or too low.
- Track judge-human agreement when judges are used.
- Run multiple reruns for stochastic or stateful tasks and report variance.
- Record headroom, floor effects, and common shortcut paths.

Define benchmark lifecycle policy:
- Version every benchmark release and keep a changelog.
- State the refresh cadence for dynamic or contamination-prone tasks.
- State the retirement criteria for stale or saturated tasks.
- Keep benchmark-health notes that summarize leakage risk, judge risk, and checker limitations.

## 9) Output Templates

Use this benchmark charter template first:

```yaml
benchmark_charter:
  benchmark_id: BENCH-001
  deployment_scenario: "Where and why this evaluation will be used"
  primary_construct: "Primary capability being measured"
  secondary_constructs: []
  evidence_model:
    allowed_evidence: []
    tools_allowed: []
    tools_forbidden: []
  scoring_model:
    evaluator_type: exact_match|programmatic|executable|state_based|human|llm_judge
    success_granularity: final_only|process_plus_final
  threat_model:
    shortcut_paths: []
    contamination_risks: []
    judge_risks: []
  risk_policy:
    hallucination_tolerance: low|medium|high
    refusal_policy: "When the system should abstain or refuse"
    safety_constraints: []
    privacy_constraints: []
```

Use this task spec template:

```yaml
task_id: AGT-001
title: "Concise task title"
construct: "Primary capability being measured"
secondary_constructs: []
difficulty: easy|medium|hard
task_type: reasoning|agentic|hybrid
context:
  inputs: []
  initial_state: []
  mutable_state: []
  state_invariants: []
  allowed_mutations: []
  tools_allowed: []
  tools_forbidden: []
  budget:
    max_tool_calls: 0
    max_time_min: 0
    max_tokens: 0
instructions: |
  Write unambiguous instructions here.
expected_output_schema:
  type: object
  fields: []
evaluator:
  type: exact_match|programmatic|executable|state_based|human|llm_judge
  required_artifacts: []
  reference_artifacts: []
  collateral_damage_checks: []
  reruns: 1
  seed: 0
scoring:
  rubric_id: RUBRIC-001
  hard_fail_conditions: []
scoring_contract:
  score_unit: boolean|0_4_level|points|named_bands
  requires_reasoning_correct_for_any_credit: true
  global_zero_if: []
  criterion_specs: []
  score_bands: []
review_examples: []
metadata:
  source: human-authored|programmatic|mixed
  split: train|dev|test|holdout
  freshness_cutoff: "YYYY-MM-DD or null"
  version: "v1.0.0"
```

Use this embedded scoring-contract template:

```yaml
scoring_contract:
  score_unit: boolean|0_4_level|points|named_bands
  requires_reasoning_correct_for_any_credit: true
  global_zero_if:
    - "Off-topic, fabricated, or evasive answer"
    - "Correct conclusion with incorrect reasoning, if reasoning is part of the construct"
  criterion_specs:
    - criterion: "Task completion"
      pass_if: "Exact condition that earns credit"
      partial_if: "What earns partial credit, if applicable"
      fail_if: "What clearly fails this criterion"
      common_false_positive: "Tempting near-miss that should not pass"
      why_it_matters: "What boundary this criterion is protecting"
  score_bands:
    - score: "full"
      requires: []
    - score: "zero"
      triggers: []
review_examples:
  - score: "full"
    label: "fully_correct"
    example_answer: "Representative full-credit answer"
    expected_results: {}
    gate_triggered: false
    why: "Why this earns full credit"
  - score: "zero"
    label: "correct_answer_wrong_reason"
    example_answer: "Correct conclusion but flawed rationale"
    expected_results: {}
    gate_triggered: true
    why: "Why this still receives zero"
  - score: "zero"
    label: "off_scope_or_fabricated"
    example_answer: "Off-topic or made-up answer"
    expected_results: {}
    gate_triggered: true
    why: "Why this is zero"
```

Use this rubric template:

```yaml
rubric_id: RUBRIC-001
criteria:
  - name: Task completion
    weight: 30
    levels:
      0: "Not solved"
      1: "Partially solved"
      2: "Solved with material defects"
      3: "Solved correctly"
      4: "Solved correctly with strong validation"
  - name: Reasoning / decision quality
    weight: 20
  - name: Evidence use
    weight: 15
  - name: Constraint adherence
    weight: 15
  - name: Verification and recovery
    weight: 10
  - name: Safety and trustworthiness
    weight: 10
hard_fail_conditions:
  - "Fabricated evidence"
  - "Explicit policy violation"
pass_threshold:
  overall_score: 75
```

Use this evaluation report template:

```markdown
# Evaluation Report

## Summary
- Benchmark version:
- Evaluated system:
- Date:

## Aggregate Results
- Overall score:
- Pass rate:
- Task-type breakdown:
- Difficulty breakdown:

## Reliability Diagnostics
- Judge-human agreement:
- Rerun variance:
- Checker false-positive / false-negative notes:

## Scoring Boundary Audit
- Criteria with ambiguous pass/fail boundaries:
- Cases where correct-answer / wrong-reason still passed:
- Missing review examples for score buckets:
- Near-misses that the rubric failed to separate:

## Agentic Diagnostics
- Planning errors:
- Tool misuse patterns:
- Recovery behavior quality:
- Efficiency profile:
- Safety / policy violations:

## Benchmark Health
- Freshness cutoff:
- Contamination concerns:
- Known checker limitations:
- Recommended refresh actions:

## Recommended Revisions
1. ...
2. ...
```

## Example

**Input**
Design a benchmark task for a browser agent that must retrieve a reimbursement policy and submit a compliant summary.

**Actions**
1. Write a charter with `primary_construct = retrieval-grounded policy compliance`.
2. Choose an interactive web task with an explicit end artifact and forbidden tools.
3. Define a state-based evaluator that checks the submitted summary, required policy fields, and absence of policy violations.
4. Embed a scoring contract in the item that shows how a correct answer with the wrong rationale receives zero.
5. Add review examples for every reportable score, including zero-score fabricated and wrong-reason cases.
6. Add a rubric that separates task completion from safety and recovery.
7. Add a freshness cutoff and a rerun policy if the site content changes over time.

**Output**
A task spec with embedded scoring contract and review examples, plus a rubric and evaluation report template that can be piloted without hidden success criteria.

## References

Read [primary-sources.md](references/primary-sources.md) for foundational references, modern benchmark papers, judge-reliability sources, and benchmark-health literature.
Read [examples-good-vs-bad.md](references/examples-good-vs-bad.md) for concrete good and bad benchmark-item examples grounded in public sources.
