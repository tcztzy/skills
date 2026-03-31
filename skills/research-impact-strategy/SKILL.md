---
name: research-impact-strategy
description: Decide whether a research idea, experiment thread, or paper draft is worth pursuing and how to sharpen it into one high-impact claim. Use when judging if a project should go, kill, pivot, or scope down; focusing experiments around a single thesis; or repositioning a paper's title, introduction, figures, and conclusion before submission.
metadata:
  short_name: impact-strategy
  aliases: best paper,research strategy,impact triage,paper positioning
---

# Research Impact Strategy

## Overview
This is an advisory, report-first skill for research judgment rather than manuscript drafting. Use it to decide whether a project is important enough, sharp enough, and timely enough to deserve more work, and to turn diffuse results into a tighter research story.

By default, the output is a short strategy memo using `assets/strategy-memo-template.md`. This skill does not generate a full paper, novelty-search bundle, or formal peer review unless the task clearly belongs in another skill.

## When to Use This Skill

- Early stage: "Is this idea worth pursuing?" "Does this feel top-venue worthy?"
- Mid-project: "The experiments kind of work; should we keep going, pivot, or cut scope?"
- Writing stage: "What is the one claim?" "Why does this draft not land?"
- Pre-submission: "What obvious reviewer question have we not answered yet?"
- Positioning stage: "Who is the reader?" "Does the paper explain why this matters now?"

## Decision Ladder / Routing Axis

- Primary user task or judgment:
  Decide whether to invest, redirect, narrow, or stop a research project, and how to position its main claim.
- Important input structure:
  Topic brief, experiment snapshot, draft outline, abstract, or full paper draft.
- Semantic family or decision layer:
  Impact triage, thesis extraction, scope control, must-answer evidence planning, and story audit.
- Cross-cutting constraints or standards:
  Do not overclaim novelty or importance. Separate evidence from inference. Optimize for one central idea, not maximal surface area.
- Implementation options or tools:
  Mostly prose analysis. Route to `research-ideation-novelty-check`, `paper-writer`, or `paper-reviewer` when the user actually needs ideation, manuscript drafting, or formal review.

## Workflow

1. Classify the stage
   - Put the task in one primary bucket: `idea`, `execution`, `writing`, or `submission timing`.
2. Extract the core thesis
   - Write the paper's one-sentence claim and the stronger "so what?" claim.
   - If either sentence is blurry, overloaded, or sounds like multiple papers, treat that as the first problem to fix.
3. Run impact triage
   - Check whether the problem matters beyond "this could be a paper".
   - Check whether there is an "only we can do this now" angle, a comparative advantage, or a timing window.
   - Check for novelty and positioning risk without claiming certainty.
4. Make the scope decision
   - Choose exactly one of `GO`, `KILL`, `PIVOT`, or `SCOPE-DOWN`.
   - List the must-answer experiments, arguments, or reader-positioning fixes required before more work is justified.
5. Audit the draft story when a draft exists
   - Check the title for accuracy and single-idea alignment.
   - Check the introduction for reader framing and story logic.
   - Check figures for self-contained takeaways.
   - Check the conclusion for an explicit answer to "so what?"

## Constraints / Standards

- Treat importance, novelty, and timing as judgments under uncertainty, not facts.
- Prefer one strong paper over a bag of loosely related claims.
- Kill or redirect projects that are technically functioning but strategically weak.
- Do not recommend more experiments by default; recommend only the evidence needed to answer the next skeptical question.
- Keep the output decision-complete enough that a researcher knows what to do next.

## Input -> Actions -> Output

Input:
- A topic brief, experiment snapshot, paper outline, abstract, or draft.

Actions:
1. Identify the current stage and the single claim the work is trying to support.
2. Evaluate impact, timing, comparative advantage, and obvious positioning risk.
3. Decide whether to go forward, kill the project, pivot the angle, or reduce the scope.
4. Return the smallest set of required evidence and story fixes needed for the next step.

Output:
- A concise strategy memo following `assets/strategy-memo-template.md`.
- One explicit decision from `GO`, `KILL`, `PIVOT`, or `SCOPE-DOWN`.
- A short rationale tied to the provided evidence.

## Example

**Input**

"We have a new training-time defense method that beats the baseline by 1.5%, but it is stable on only one dataset. Is this still worth aiming at a top venue?"

**Actions**

1. Classify the task as `execution`.
2. Extract the real claim: is this a new defense, a robustness lesson, or a narrower empirical observation?
3. Check whether the paper matters if the best-case conclusion is only "metric +1.5%".
4. Decide whether to `PIVOT` the framing, `SCOPE-DOWN` into a narrower paper, or `KILL` the project.
5. List the minimum evidence needed before further drafting.

**Output**

A short memo with:
- the core claim and impact thesis,
- why the current framing is weak or strong,
- the top risks,
- the required evidence,
- and a final `PIVOT` / `SCOPE-DOWN` / `GO` / `KILL` decision.

## Edge Cases / Validation

- If the user mainly wants new ideas or novelty queries, route to `research-ideation-novelty-check`.
- If the user already committed to writing and needs a full manuscript, route to `paper-writer` after the strategy memo.
- If the user wants a venue-style evaluation of a finished paper, route to `paper-reviewer`.
- If the best conclusion still sounds trivial when everything succeeds, prefer `KILL` or `PIVOT`.
- If the draft feels like multiple papers glued together, prefer `SCOPE-DOWN` before recommending more experiments.

## References

- Idea selection: `references/idea-selection.md`
- Project triage: `references/project-triage.md`
- Paper story: `references/paper-story.md`
- Timing and positioning: `references/timing-and-positioning.md`
- Output template: `assets/strategy-memo-template.md`
