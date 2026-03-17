---
name: dash-connected-lower-case-skill-name
description: Task-first, action-oriented description. Include trigger keywords, explicit "Use when ...", and avoid leading with a library or vendor name unless the tool itself is the task.
license: MIT (optional)
compatibility: Describe environment requirements if any (optional).
metadata:
  author: <author name>
  version: "0.1"
  optional: true
allowed-tools: Bash Base Read Edit Write Optional-space-separated-list
---

# Skill Title

Brief summary of what the skill does.

## When to Use This Skill

- Trigger scenario 1
- Trigger scenario 2

## Decision Ladder / Routing Axis

- Primary user task or judgment:
- Important input structure:
- Semantic family or decision layer:
- Cross-cutting constraints or standards:
- Implementation options or tools:

## Workflow

1. Classify the task and decide the correct semantic family
2. Apply the main caveats, standards, or quality gates
3. Choose the implementation path or tool only after the decision layer is clear

## Constraints / Standards

- Publication, compliance, export, safety, or accessibility rules that apply across tools

## Implementation Layer

- Backend / script / runtime option 1
- Backend / script / runtime option 2

## Input -> Actions -> Output (Minimal Template)

Input:
- User request + essential context.

Actions:
1. Identify the user task and the decision layer that matters most.
2. Apply the relevant standards or caveats before tool choice.
3. Route to the implementation path and return one prioritized next check when uncertainty exists.

Output:
- Required fields in the final response.
- One concise rationale tied to input evidence and the chosen decision path.

## Example

**Input**
User request example.

**Actions**
1. Choose the task family
2. Apply a key constraint
3. Pick the implementation path

**Output**
What the result should look like.

## Edge Cases / Validation

- Important caveat or validation criteria.
- If several tools can implement the same job, explain why this skill is not organized tool-first.
