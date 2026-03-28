---
name: code-simplifier
description: Safely simplify code with multi-metric quality gates. Use when prompts mention
  to refactor/compress/reduce size or complexity without functional change; validate with
  formatter-aligned metrics (lines/bytes + tokens/complexity when available) plus lint/tests/build.
---

# Code Simplifier

Simplify code without sacrificing correctness, readability, maintainability, or project standards.

Preserve exact functionality, follow project conventions, choose clarity over clever compactness, avoid over-simplification, and keep scope focused on recently touched code unless asked otherwise.

When a language pack exists, load only the relevant pack. For Rust work, use the shared workflow here plus the Rust playbook in `references/rust.md`.

## Core Principles

1. Preserve functionality.
- Never change behavior, outputs, side effects, error semantics, performance characteristics that tests/usage rely on, or public API shape unless explicitly requested.

2. Apply project standards.
- Read and follow the repo's conventions/instructions (for example: `AGENTS.md`, `CLAUDE.md`, `CONTRIBUTING.md`, style guides, lint configs).
- Use the project's formatter/linter/type checker and match its idioms (imports, naming, module boundaries).

3. Enhance clarity.
- Reduce unnecessary nesting and cognitive load.
- Remove redundancy (duplicate branches, repeated literals, repeated parsing/validation).
- Prefer explicit, readable code over dense one-liners.
- IMPORTANT: Avoid nested ternary operators (and similar "clever" constructs). Prefer `if/else` chains, `switch/match`, or small helpers when multiple conditions exist.
- Prefer the simplest implementation that satisfies the requirement.
- Do not add defensive branches, fallback layers, or configuration plumbing unless there is a concrete repository-specific need. Assume sane inputs and normal library defaults unless the codebase clearly requires stronger handling.

4. Maintain balance.
- Do not prioritize "fewer lines" over readability/debuggability.
- Do not introduce indirection (helpers/abstractions) unless total complexity and maintenance cost decreases.
- Do not collapse code in a way that makes logging, error handling, or invariants harder to reason about.

5. Focus scope.
- Default scope: recently modified code (current diff/session) or user-specified files/functions.
- Avoid broad refactors and mass renames unless requested.

## Workflow

1. Establish a baseline.
- Identify the scope (git diff, changed files, or user-provided list).
- Run the project formatter first (formatter-first avoids fake wins that disappear after formatting).
- Record size/complexity metrics on formatted code:
  - Formatted line count (`wc -l`).
  - Source bytes (`wc -c`).
  - Token count and structural complexity when feasible (AST nodes/branches/max depth, cyclomatic complexity).
- Run relevant checks for the language/repo (lint + type check + build + targeted tests).
- Rust default baseline: `cargo fmt --all`, then `cargo check`, `cargo clippy`, and targeted `cargo test`.

2. Apply behavior-preserving simplifications.
- Remove duplicated branches and repeated literals.
- Collapse obvious temporary variables and one-time wrappers.
- Reuse shared helper logic only when total post-format complexity decreases.
- Prefer data-driven mappings over repetitive condition chains.
- Use guard clauses to flatten nested control flow (when it stays readable).
- Consolidate related logic and delete dead/unused code paths (only if truly unused and validated).
- Rust-specific moves: deduplicate `match` arms, prefer `if let` / `let ... else` / `matches!` when they reduce nesting, and use iterator adapters/combinators only when post-format complexity truly drops.

3. Preserve safety and contracts where they protect risk.
- Keep types (or type annotations) on API boundaries, parsing/validation, and response shaping.
- Prefer concrete SDK/library types over broad fallbacks.
- Avoid weakening contracts for brevity (for example: introducing `Any`, removing invariants/assertions, broadening exceptions).
- Keep error-handling semantics intact (don't swallow errors; keep messages actionable).
- Rust guardrails: preserve ownership/borrowing clarity, avoid adding clones just to shorten code, keep `Result`-based propagation for recoverable paths, and do not replace structured errors with opaque strings.

4. Validate every pass.
- Re-run formatter.
- Re-check metrics against baseline.
- Re-run lint/typecheck/build/tests. If the project has a fast subset, run that on each pass and run the full suite before finalizing.

5. Treat non-improvement as failure.
- If only one metric improves (for example lines) while others regress or stay flat, treat it as a failed simplification unless it clearly improves clarity.
- If readability/maintainability drops, treat as failed even if size metrics improve.
- Explain why (formatter expansion, indirection overhead, compressed-but-harder control flow, hidden side effects, harder debugging).
- Switch strategy (different refactor shape) and try again.

## Language Packs (References + Scripts)

- Python: `references/python.md` and `scripts/python_metrics.py`. For Pydantic models, prefer class keyword config such as `class Model(BaseModel, extra="forbid"):` over `model_config = ConfigDict(extra="forbid")` when the keyword form expresses the same constraint.
- Rust: `references/rust.md` (use `cargo fmt`/`check`/`clippy`/`test`; if AST metrics matter, create the tiny `proc-macro2` + `syn` probe from the reference)
- Add other languages by adding markdown files under `references/` (and `scripts/` helpers when useful).

## Rust Defaults

- Keep `rustfmt` as the style baseline before comparing metrics.
- Keep `cargo clippy` and targeted `cargo test` green before claiming a simplification win.
- Preserve explicit types, trait/API conventions, and doc-example behavior on public surfaces.
- Prefer readability over compressed control flow; a shorter `match` replacement only counts if it stays clearer after formatting.

## Decision Rules

- Optimize for **multi-metric simplicity**: formatted lines + bytes + (tokens/complexity when available) + build/test confidence.
- Keep behavior equivalent by default; do not change API shape or edge-case semantics unless requested.
- Do not trade away readability just to game metrics.
- Do not trade away borrow-safety, explicit invariants, or error quality just to game metrics.
- Prefer small, reversible commits over large rewrites.
- Keep logs/errors informative when collapsing control flow (avoid removing helpful context).

## Example (Language-Agnostic)

**Input**
Simplify one or more files without functional change.

**Actions**
1. Identify scope (diff, file list, or user-specified functions).
2. Run the project's formatter, then record baseline metrics (lines/bytes; tokens/complexity when available).
3. Apply behavior-preserving simplifications while keeping readability and contracts intact.
4. Re-run formatter, re-measure, and run the relevant checks (lint/typecheck/build/tests).

**Output**
A short report with baseline vs final metrics, what checks were run, and confirmation that behavior is preserved.

## Output Checklist

- State baseline and final metrics (as available): line count, byte size, token count, complexity measures.
- State net deltas and whether readability/maintainability stayed acceptable.
- Confirm formatter + lint/typecheck/build/tests run and outcomes.
- If no true simplification, provide failure analysis and next strategy.
