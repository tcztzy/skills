---
name: overengineering
description: "Reduce avoidable implementation, test, specification, and collaboration costs under the same real requirements. Use when addressing overengineering, unnecessary abstraction or defense, implementation-coupled tests, accumulating specs, or costly review rituals; measure size and dependencies where useful."
---

# Overengineering

## Define the problem before changing code

Establish the real requirements R from the user's request and supported contracts:
observable inputs, outputs, failure semantics, and relevant compatibility, security,
concurrency, integrity, and performance constraints. Map requirements to evidence and
acceptance scenarios in the existing task notes; surface omissions or unauthorized
substitutions. Existing code, tests, and specs are evidence, not automatically R.

Let x = (implementation I, tests T, specification S, collaboration/process P), and let F(R) contain
the alternatives satisfying R and its actual risk constraints. Seek a Pareto
improvement in the cost vector C(x | R): maintenance effort, execution/resources,
test upkeep, spec reading/reconciliation, and coordination effort. An avoidable-cost witness is an alternative
x' in F(R) with C(x') <= C(x) componentwise and at least one strict improvement.
For a cost measured in a single agreed unit, excess is C(x) - inf_{y in F(R)} C(y).
The optimum is usually unknown; report demonstrated savings and tradeoffs, not a
made-up distance to optimality. Unmeasured costs remain unknown.

The script supplies structural proxies, not C or a verdict. Large projects and
justified defenses can be necessary. Fewer tokens alone do not prove success;
use no composite score, universal threshold, or cross-language ranking.

## Measure a reproducible baseline

Use [measurement.md](references/measurement.md) for observable outcome events,
annotation/experiment boundaries, scope, formulas, and dependencies. Choose only
measurements that inform this task. The script never runs target project code.
It measures exact `cl100k_base` tokens per UTF-8 file, role-separated scale, PC,
SCC cycles, fan-in/out hotspots, and optional entry closure tokens.

```bash
uv run /path/to/overengineering/scripts/measure.py /path/to/project \
  --python-root src --entry package.cli --json /tmp/before.json
# After one scoped simplification, with the same selection and graph extraction:
uv run /path/to/overengineering/scripts/measure.py /path/to/project \
  --python-root src --entry package.cli --baseline /tmp/before.json \
  --json /tmp/after.json
```

For Rust/TypeScript, supply `--graph /tmp/graph.json` using the documented schema.
Inspect paths, roles, graph gaps, and limitations. Compare the same R and measurement
policy; follow measurement.md for extraction, comparability, and PC interpretation.

## Make one justified change

Distinguish a behavior-preserving refactor from an authorized behavior change.
For additions, name the missing responsibility; for deletions, show that the duty
is retired or preserved at a reachable replacement; for rewrites, state what meaning
or behavior must remain. Size is a cost, not the acceptance oracle. Record the
reason and evidence in existing task notes, without another approval ritual.

For prose and instructions, revise the whole argument for its intended reader.
Preserve claims, qualifications, examples that resolve ambiguity, and loading paths.
A moved rule is preserved only when the actual consumer receives it; a filename or
link alone is insufficient. Keep useful repetition when it enforces an independent
entry point. Label intended scope or policy changes explicitly instead of calling
them equivalent compression.

Trace one real behavior through its dependencies. Prioritize candidates supported
by code and usage: forwarding layers with no independent contract, duplicate state
and synchronization, speculative extension points without callers, and cyclic
ownership/dependencies. Remove or inline one candidate; consolidate state or move
a dependency to its actual owner when that reduces the real change surface.

For each guard, fallback, retry, compatibility branch, or validation layer, name
the violated invariant, plausible fault, and responsible boundary. Keep validation
at trust boundaries, bounded recovery, and required safety/concurrency guarantees.
Remove redundant internal checks only when the invariant is established. Do not
turn unexpected errors into success or remove protections merely to lower counts.

Treat tests as part of the design. Rewrite implementation-bound tests around public
behavior and meaningful faults; delete obsolete change detectors and scaffolding
created only to keep them green. Never preserve a bad structure for historical test
success. Internal interactions can be requirements when they enforce actual resource,
ordering, security, or concurrency constraints; preserve those acceptance outcomes.

Edit the current spec in place when R changes. Merge duplicate clauses, replace
superseded decisions, and remove obsolete or contradictory rules and their callers.
Keep one readable statement of current behavior; Git retains history. Preserve a
changelog or decision record only when it is itself required. Review the affected
whole passage rather than appending another exception or correction at the end.

Tie reviews, approvals, handoffs, and repeated checks to a concrete decision. A
blocking finding must name the affected R, location, evidence, and consequence for
acceptance. Separate optional improvements; they do not expand the task by default.
Remove stages whose output cannot change an action. Use existing tools, with no
new governance framework or fixed review-round count.

## Judge the result against the same acceptance

Check the affected public behavior, errors, and real loading/delivery path against
independent expected outcomes; include performance or concurrency where R requires
it. Static checks establish only their inspected properties. For instruction or
prose compression, compare fixed tasks with the same model, inputs, and acceptance;
report untested behavior as unknown. Passing script tests or retaining a sentence
does not establish unchanged model behavior. See measurement.md for the research
basis and limits; do not launch a paid experiment without separate authorization.

Use the measurement contract to distinguish observed costs, annotated outcomes,
and reviewer experiments; unmeasured behavior remains unknown.

Deliver R and evidence, removal rationale, baseline/after values, acceptance results
or explained test replacements, costs, tradeoffs, and gaps. Deliver when R passes;
recheck affected behavior after fixes. External model review requires separate user
approval and the existing `review_executor.py` ledger; if unavailable, report that
step pending and continue local work without bypassing it.

See [sources.md](references/sources.md) for the short research and tool references
behind these measurement and testing choices.
