# Good vs Bad Question-Design Examples (Web-Sourced)

This file gives concrete examples you can reuse when teaching or auditing item quality.
Each pair includes why the good version works and why the bad version fails.

## Pair 1: One-best-answer MCQ (construct purity)

### Good (from NBME style guidance)

Prompt pattern:
- Present a short clinical vignette.
- Ask a focused lead-in such as: "Which is the most likely diagnosis?"
- Keep all options in one semantic class (all diagnoses).

Why good:
- Measures one construct.
- Options are mutually competitive.
- Scoring is deterministic (one best answer).

### Bad (from NBME item-flaw examples)

Prompt pattern:
- Same vignette.
- Ask: "Which statement is true?"
- Mix option types (diagnosis, treatment, pathology, epidemiology).

Why bad:
- Tests multiple constructs at once.
- Lets test-wise elimination beat domain reasoning.
- Reduces reliability and interpretability of score.

Source:
- NBME Item-Writing Guide: https://www.nbme.org/item-writing-guide
- PDF direct: https://www.nbme.org/sites/default/files/2020-01/ConstructingWrittenTestQuestionsForTheBasicAndClinicalSciences.pdf

## Pair 2: MCQ options with/without homogeneous alternatives

### Good

Prompt pattern:
- Lead-in asks for one mechanism.
- All options are mechanisms, at similar abstraction level.

Why good:
- Forces discrimination within the same concept family.
- Wrong answers are informative for diagnosis of misconception.

### Bad

Prompt pattern:
- Lead-in asks for one mechanism.
- Options mix mechanisms, risk factors, and management actions.

Why bad:
- Option heterogeneity creates shortcut cues.
- Incorrect picks do not map cleanly to one misconception category.

Source:
- NBME item-flaw discussion and option-homogeneity rule (same links as Pair 1).

## Pair 3: Multi-step reasoning question (fully specified vs underspecified)

### Good (dataset-style example)

Prompt pattern:
- Ask several dependent arithmetic subquestions inside one scenario.
- End with strict final-answer format requirement.

Why good:
- Requires state tracking across steps.
- Supports objective checking.
- Low ambiguity, high reproducibility.

Example source:
- GSM8K README example and formatting (`#### final answer`):
  https://github.com/openai/grade-school-math

### Bad (anti-pattern adaptation)

Prompt pattern:
- "A carnival sold 500 tickets and made money from rides and food. How much profit?"

Why bad:
- Missing unit economics and constraints.
- Multiple valid interpretations.
- Fails determinacy (cannot produce one ground truth).

Design basis source:
- GSM8K task style (for what good determinacy looks like):
  https://github.com/openai/grade-school-math

## Pair 4: Agentic web task (explicit contract vs vague objective)

### Good (real WebArena task format)

Prompt pattern:
- Give concrete intent.
- Provide evaluator fields (e.g., exact match, required strings, URL checks).
- Keep environment and success criteria explicit.

Why good:
- Tests planning + tool execution under observable criteria.
- Enables deterministic or semi-deterministic automated scoring.

Source:
- WebArena task JSON format and evaluator fields:
  https://raw.githubusercontent.com/web-arena-x/webarena/main/config_files/test_raw.json
- WebArena repo:
  https://github.com/web-arena-x/webarena

### Bad

Prompt pattern:
- "Browse around and improve this website."

Why bad:
- No completion condition.
- No measurable artifact.
- Cannot separate failure of planning vs failure of judging.

Design basis source:
- WebArena structured task/eval design (same links as above).

## Pair 5: Agentic coding task (aligned issue-to-test scope vs misaligned scope)

### Good (SWE-bench Verified style)

Prompt pattern:
- Real issue statement.
- Test requirements align with issue scope.
- Evaluation checks changed behavior with targeted tests.

Why good:
- Measures repository-grounded bug fixing.
- Limits hidden gotchas unrelated to task statement.

Source:
- SWE-bench repo:
  https://github.com/SWE-bench/SWE-bench
- OpenAI "Introducing SWE-bench Verified" (task quality examples):
  https://openai.com/index/introducing-swe-bench-verified/

### Bad (publicly documented benchmark flaw)

Prompt pattern:
- Problem statement asks for one fix.
- Hidden/official tests require extra behavior not stated in the issue.

Why bad:
- Penalizes correct issue-focused fixes.
- Confounds capability measurement with benchmark artifact mismatch.

Source:
- OpenAI "Why we're no longer publishing SWE-bench Verified scores":
  https://openai.com/index/why-were-no-longer-publishing-swe-bench-verified-scores/

## Pair 6: Scoring standard (analytic rubric vs binary-only score)

### Good

Prompt pattern:
- Score multiple dimensions separately (e.g., specification clarity, test scope, difficulty).
- Use ordinal anchors (for example 0-3 with written descriptors).

Why good:
- Better diagnostic signal.
- Supports error analysis and rubric calibration.

Source:
- SWE-bench Verified annotation rubric/instructions:
  https://openai.com/index/introducing-swe-bench-verified/

### Bad

Prompt pattern:
- Single pass/fail score with no criteria breakdown.

Why bad:
- No actionable diagnosis.
- Poor inter-rater consistency.
- Hides whether failure came from reasoning, tool use, or formatting.

Design basis source:
- Multi-criterion annotation design in SWE-bench Verified (same source as above).
