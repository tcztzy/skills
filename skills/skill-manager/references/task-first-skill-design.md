# Task-First Skill Design

This reference answers a question that comes even before "How should I write SKILL.md?": along which axis should a skill be organized?

## Core judgment

Default priority order:

1. What task or judgment problem the user is trying to solve
2. What the input looks like
3. What semantic or analytical choice has to be made
4. What cross-cutting quality, compliance, publication, or export constraints apply
5. Only then, which tool should implement it

If a skill tree starts by expanding tool names, it has usually chosen the wrong primary axis.

## Recommended decision chain

Design a skill around the following chain instead of a list of tool names:

1. `Research question / user intent`
   - What is the user trying to judge, compare, or produce?
2. `Input structure`
   - tabular / array / document / codebase / browser state / API response
3. `Semantic family`
   - for example comparison, distribution, correlation; or create, audit, convert, install
4. `Cross-cutting constraints`
   - publication standards, audit requirements, accessibility, export format, permissions, safety, determinism
5. `Implementation backend`
   - matplotlib, ggplot2, TikZ, Playwright, pandoc, specific SDKs, and so on

## Why tool-first should not be the default

- Tool names do not explain why the work should be done that way.
- The same task often has multiple interchangeable tools.
- What users actually care about is usually whether the result is correct, the reasoning holds, and the deliverable is compliant, not which library name was used.
- Tool-first skills often confuse "can be done this way" with "should be done this way."

## When tool-first is justified

Consider a separate top-level skill only when the tool changes at least one of the following:

- the primary artifact type
- the runtime or installation dependency profile
- the permission boundary
- the validation strategy
- the user's own task name

Examples:

- `pdf` and `doc` can be separate because the artifact, toolchain, and validation strategy differ.
- `playwright` can stand alone because it depends on a real browser and interactive page state.
- Plain `matplotlib`, `seaborn`, and `ggplot2` usually should not become top-level skills first if they are all solving "make a paper figure."

## Make constraints explicit

Many repositories do not fail because they lack tool instructions. They fail because they lack a constraints layer.

The following should be modeled explicitly as cross-cutting layers instead of being buried in a backend subsection:

- publication standards
- compliance or audit requirements
- accessibility, color, and typography constraints
- export size, resolution, and vector-format requirements
- safety and permission boundaries

## Applying this to paper figures

Recommended order:

1. research question
2. data structure
3. figure task or visual grammar
4. submission rules and figure-panel constraints
5. tool implementation

In a skill tree, the better pattern is:

- router: route by research question and figure family
- family skills: explain when to use which figure type, what can mislead, and which caveats are needed
- backend: implementation options inside the family skill

A worse pattern is to split the top level directly into:

- `matplotlib`
- `seaborn`
- `ggplot2`
- `plotly`

That answers "how to draw it," not "why this is the right figure."

## Order inside SKILL.md

If you adopt a task-first organization, the body should usually follow a similar order:

1. when the skill should trigger
2. what judgment or classification should happen first
3. which semantic choices are the default route
4. which cross-cutting constraints must be checked first
5. which tools or scripts should be chosen last

## Authoring self-check

- Does the top-level skill name describe a task or just a library?
- If you swapped out the tool, would the core of the skill still hold?
- Is the constraints layer written explicitly?
- Do the examples show "problem -> choice -> implementation" rather than just "input -> call a script"?
