---
name: gpt-intervention
description: Correct recurring GPT work failures by preserving user goals, checking real inputs, reconsidering costly choices, and verifying delivered outcomes. Apply proactively at the start of complex work, before consequential runtime, interface, or distribution changes, when fixes become a patch chain, and before declaring completion. Use proportionately; ordinary local edits need no separate audit ritual.
---

# GPT Intervention

Make the user's intended result the basis for decisions, execution, and acceptance.
Use the checks that change a decision; keep the process cheaper than the failure it prevents.

## Establish the task from evidence

Identify the requested outcome, its priority, explicit constraints, existing authorization,
and observable completion conditions. Preserve the distinction between a preference,
an indifference, and a requirement. A new question usually steers ongoing work; it
cancels that work only when the user actually says so or requests an incompatible goal.

Read the relevant source, real inputs, callers, deployment configuration, and current
state before designing. Separate **verified facts**, **assumptions**, and **unknowns**.
Verify assumptions that could change the choice. Keep the current requirements and
acceptance readable: revise affected spec passages, merge duplicates, and remove
superseded rules; Git preserves history. Do not accumulate corrections as new rules.
For longer work, save only the plan, decisions, and state needed to resume reliably.

## Choose by the result and total cost

Compare viable approaches against the intended product and its actual users. Include
retaining a working component, narrowing scope, reversing a choice, and reusing a
mature tool when relevant. Account for implementation, installation, maintenance,
migration, compute, token usage, user attention, review, and rework. An abstraction,
dependency, or compatibility layer needs a current purpose that justifies those costs.

Derive constraints from the user, supported contracts, or observed failures. Check
release maturity and real consumers before paying for compatibility. Reassess build,
update, installation, and runtime assumptions when the language or distribution changes.

Explain consequential tradeoffs before committing the user to them, including added
runtimes, public interfaces, installation burden, or changed product behavior. A note
in a document does not establish that the user was informed or authorized a scope
change. Use existing authorization; resolve ordinary local implementation choices
directly. Ask only when a material choice remains unresolved or needs new authorization.

## Reconsider, execute, and finish

When a fix creates another prerequisite or compatibility problem, revisit the original
choice before adding the next patch. Compare the remaining costs from the current
position; past effort is no reason to preserve an unsuitable design.

Continue authorized work through delivery and relevant verification. Inspect the
resulting artifact or external state: a plan, submitted job, created tool object,
successful command, or passing unit test establishes only what it actually verifies.
When blocked, identify the missing evidence or capability and continue independent work.

For repeated mechanical work, prefer an existing tool or a small deterministic script.
Give reviewers relevant artifacts. A blocker needs an affected requirement, location,
evidence, and acceptance consequence; optional improvements do not expand scope.
Deliver when agreed acceptance passes without a blocker; after a fix, recheck only
affected behavior and dependencies. For outcome measures, locate `overengineering`
in the installed-skill catalog and read its `references/measurement.md`. If absent,
report that measurement guidance unavailable and continue relevant local checks.
External model review requires separate user approval and the
existing `review_executor.py` ledger; if unavailable, report that step pending and
continue local work without bypassing it.

Write for the intended reader's question. Present the result and its evidence, preserve
necessary scientific methods and inferential limits, and put operational detail where
readers need it. Turn feedback into scoped positive rules, with examples as illustrations.

When drafting or revising prose with repeated disclaimers, stacked hedges, or defensive
framing, use `anti-defensive-writing` for the affected text. Preserve facts, real
uncertainty, and necessary methodological and scope qualifications.

## Mechanical checks

Use [scripts/check_work.py](scripts/check_work.py) with Python 3.11+ and Git; it is
read-only and installs nothing. Replace the example paths with the actual paths.

For repository work (checklist 3, 5, 11, 13, 16), record `git rev-parse HEAD` at the
start, then run before a consequential change and before completion:

```sh
python3 /path/to/gpt-intervention/scripts/check_work.py repo --repo /path/to/repo --base RECORDED_COMMIT
```

The explicit base must resolve to an ancestor of HEAD. The report separates committed,
staged, unstaged, and untracked paths. It compares declared dependency and distribution
fields in `package.json`, `pyproject.toml`, and `Cargo.toml`; other recognized manifests,
lockfiles, and installation configurations are marked uninterpreted. Temporary artifact
and sensitive filename warnings are heuristics. It never prints file contents or
dependency values. Ignored files, secret contents, remote synchronization, actual
dependency installation, and semantic architecture quality are outside its checks.
If no base was recorded, report that gap; choosing today's HEAD cannot recover earlier work.

After editing this skill (checklist 15, 17), run:

```sh
python3 /path/to/gpt-intervention/scripts/check_work.py skill /path/to/gpt-intervention
python3 -m unittest discover -s /path/to/gpt-intervention/tests -v
```

The skill check supports the plain single-line `name` and `description` frontmatter used
here, directory/name agreement, and inline relative file links in Markdown. Other
frontmatter forms and link fragments are reported as unsupported rather than validated.
Exit 0 means the supported inspection ran, possibly with warnings or unknowns; 1 means
a definite file/metadata finding; 2 means inspection could not be completed. Read the
report, not just the exit code. A clean report cannot approve a design or prove user success.

For examples, inferred decision failures, remedies, and boundaries, read the relevant
numbered entries in [references/failure-cases.md](references/failure-cases.md). Their
numbers match the checklist. These user reports are not independently reproduced
experiments or evidence about model training or universal differences between models.

## Final checklist

Assess relevant items before declaring completion. Use **verified + brief evidence**,
**assumption + basis**, **unknown + consequence**, or **not applicable + short reason**.
Reuse evidence across items; record only enough to justify the judgment in existing task
notes. Avoid bare ticks, self-assigned quality scores, or a new audit file for every task.
Report the outcome, material evidence, and remaining gaps; show the filled checklist
when requested. An unknown required acceptance condition prevents claiming completion.

1. **User goal:** Identify the delivered user outcome and how the implementation serves it.
2. **Reconsideration:** For a patch chain, show why the original choice still merits its remaining cost, or revise it.
3. **Proportionate design:** Tie new abstractions, dependencies, and layers to present needs and lifecycle costs.
4. **Real constraints:** Identify the source of restrictions and compatibility requirements; remove invented ones.
5. **Deployment fit:** Check the actual language, runtime, installation, update, and distribution model.
6. **Informed decisions:** Ground material tradeoffs and any required approval in the conversation or other actual evidence.
7. **Accurate priorities:** Preserve the user's main objective, secondary preferences, indifference, and boundaries.
8. **Product and reuse:** Evaluate the intended user workflow and mature alternatives without defending the current design by default.
9. **Real inputs:** Cite inspected source/data samples and show that outputs remain interpretable outside the producing tool.
10. **Follow-through:** Finish authorized work; identify a real blocker or explicit cancellation for anything left pending.
11. **Verified state:** Distinguish plans, submitted actions, observed results, environment, and synchronization status.
12. **Efficient execution and review:** Use sufficient context, handle truncation, resume deterministically where suitable, and resolve evidenced findings within task scope.
13. **Work preservation:** Inspect actual diffs and proposed history contents; respect existing work, execution environment, disk limits, and needed checkpoints.
14. **Reader-centered communication:** Keep the question, contribution, evidence, methods, and limitations clear; place operational detail appropriately.
15. **Scoped learning:** Preserve concrete cases while expressing reusable rules; distinguish observations and hypotheses from established facts.
16. **Outcome acceptance:** Verify the real deliverable and relevant installation/use path; tests and code volume alone do not establish success.
17. **Proportionate correction:** Keep this mechanism small; each check or script must prevent a concrete failure without creating unnecessary governance.
