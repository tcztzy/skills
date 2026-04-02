# Repository AGENTS

## Scope
- Applies to the entire repository.
- If this file conflicts with a parent `AGENTS.md`, follow this repository-local file for work inside this repo.

## Default Stance: Occam's Razor
- Choose the simplest change that fully solves the current task.
- Do not add code, files, abstractions, options, or checks unless they are justified by a present requirement, a real failure, or a repeated pattern that already exists in the codebase.
- If the default behavior is already what we want, do not write an extra line to restate it.

## Concrete Rules
- Prefer modifying an existing file, module, function, or script over creating a new one when the current structure can absorb the change cleanly.
- Do not create, switch, or push to a new git branch unless the user explicitly asks for a branch. Default to working on the current branch.
- Do not add defensive programming for hypothetical failures unless there is an observed error, an explicit requirement, or a real trust boundary that needs the guard.
- Prefer deleting or simplifying code over layering new code on top of existing behavior.
- Do not introduce extension points, strategy objects, plugin systems, factories, or feature flags for imagined future use.
- Do not extract a helper or utility file for a single call site unless it clearly improves readability right now.
- Keep validation at real boundaries such as user input, network input, filesystem input, subprocess output, or untrusted data. Avoid redundant internal guards once data is already constrained.
- If a state should be impossible under current invariants, fail clearly instead of adding speculative recovery branches.
- Keep tests proportional to the change. Test the behavior that was added or changed, not hypothetical branches that do not exist yet.
- Avoid compatibility shims, migration wrappers, and alias layers unless there is an active caller that still needs the old path.
- Prefer direct data flow over indirection. If one implementation is enough, keep one implementation.

## Examples
- If a library or framework default already matches the requirement, do not set the same default explicitly.
- If one more branch in an existing function solves the task cleanly, do not create `foo_v2.py`, `helpers.py`, or a new adapter module.
- If one function is enough, do not introduce a class with one method.
- If there is only one implementation, do not add a factory, interface, base class, or registry.
- If there is no failing case, no bug report, and no unsafe boundary, do not add fallback code "just in case".
- If an existing script can take one localized change, do not duplicate the script.
- If removing a wrapper lets the caller use the upstream tool directly, prefer removing the wrapper.
- If a small amount of duplication appears only once, keep it local until the duplication becomes real.

## Decision Check
Before adding a new file, abstraction, option, guard, or layer, ask:

1. Is there a concrete requirement or failing case right now?
2. Can the current structure handle this change without becoming unclear?
3. Does the added complexity reduce current complexity immediately, not theoretically later?

If the answer to any of these is "no", do the simpler thing.
