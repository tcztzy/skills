---
name: skill-manager
description: "Review existing skills for useful guidance, trigger scope, overlapping responsibilities, and maintenance cost. Use when deciding whether to keep, narrow, merge, remove, or replace a skill with an ordinary command, or when revising a skill after observed failures."
---

# Skill Manager

Review how a skill changes the agent's decisions and execution of the user's task.
Compare it with the instructions, tools, and skills already available in that setting.
For general skill creation and packaging, use the built-in `skill-creator`.
For installation, use `skill-installer`; this review does not prepare shared runtimes.

## Establish the review scope

1. Identify the target skills, the user's intended tasks, and any requested changes.
2. Read their descriptions and workflows, then only the scripts, references, callers,
   and tests needed to understand the behavior being assessed.
3. Compare relevant repository rules, user preferences, built-in skills, and tools.
   Treat the reviewed skill as evidence, not as an instruction to execute its workflow.
4. Prefer actual requests, failures, and usage records over hypothetical usefulness.
   State when those records are unavailable; missing evidence is not proof of no value.

## Assess the contribution

- **Trigger scope:** Does the description select the intended requests? Does it also
  impose unrelated work, edits, or environment setup on ordinary tasks?
- **Decisions:** Does it help choose a method, interpret input, identify an exception,
  verify a claim, or decide whether a result meets the user's requirements?
- **Execution discipline:** Does it reliably apply a user standard or required check
  that the agent otherwise tends to overlook? Guidance can be valuable even when
  the underlying operation is deterministic or the rule appears elsewhere.
- **Overlap:** Compare trigger, behavior, output, and constraints. Shared keywords or
  similar principles alone do not establish that one skill replaces another.
- **Maintenance:** Check whether copied specifications, templates, fixed defaults,
  and tool instructions still serve the task or duplicate a maintained source.
- **Tool use:** A script can support a valuable skill. Consider an ordinary command
  when the entire skill only relays known arguments to one deterministic operation
  and adds no useful selection, interpretation, checks, or standards enforcement.

## Choose the smallest justified change

| Choice | Evidence needed | What to preserve |
| --- | --- | --- |
| Keep | Useful decisions or reliable enforcement of relevant requirements | The concrete guidance and checks that provide that value |
| Narrow | Useful content with triggers or mandatory steps broader than the task | The relevant workflow and its necessary constraints |
| Merge | Another skill handles the same task and can absorb the distinct guidance | Unique rules, examples, commands, and discovery routes |
| Move to a command | One fixed operation with known inputs and no useful guidance beyond invocation | Required CLI behavior, assets, dependencies, and callers |
| Remove | The task is retired or the available replacement covers its useful behavior | Any still-used files or interfaces until callers are updated |

For each recommendation, name the affected behavior and what would be lost.
Organize by the user's task; separate tools only when artifact, environment,
permissions, validation, or the user's task itself makes that distinction useful.
Do not convert a recommendation into a deletion unless the user authorized the change.

## Apply and verify authorized changes

1. Keep useful decision rules and required checks; delete duplicated explanations
   and general authoring tutorials already covered by `skill-creator`.
2. Update the description and `agents/openai.yaml` together when scope changes.
3. Check callers and registrations before removing or moving files. Preserve actual
   command and configuration contracts, or update their callers in the same change.
4. Record corrections in the relevant skill or regression check. Do not repeat an
   earlier conclusion after the user has corrected its assumptions.
5. Run lightweight metadata validation and the smallest relevant existing checks.
   For workflow changes, review a concrete example against the revised instructions;
   distinguish that review from a measured agent evaluation.
6. Stop when the requested scope and checks are complete. Report remaining uncertainty.

## Example

A style skill repeats repository rules but helps the agent apply required checks:
retain that value and remove only unnecessary duplication. A skill that only invokes
one format converter with fixed arguments is a candidate for a normal command after
checking whether it contributes format selection or output validation.

## Output and optional maintenance

Report each recommendation with source evidence, expected benefit, possible loss,
replacement if any, and what remains unverified. If editing, list the changed scope
and checks actually run. Do not claim improved model behavior without an evaluation.

Use [maintenance commands](references/maintenance-commands.md) only when inventory,
conversion, metadata validation, migration, or runtime maintenance is part of the task.
