---
name: rust-quality-simplify
description: Rust-focused alias of `code-simplifier`. Use when users ask to refactor/compress/reduce Rust code without functional change; follow the shared multi-metric workflow plus Rust-specific `cargo fmt`/`clippy`/tests guidance.
---

# Rust Quality Simplify

This skill has been merged into `../code-simplifier/SKILL.md`.

For Rust simplification work:

1. Load `../code-simplifier/SKILL.md` for the shared workflow and output checklist.
2. Load `../code-simplifier/references/rust.md` for Rust-specific measurement, guardrails, and examples.
3. Keep the Rust quality gates: `cargo fmt --all`, `cargo check`, `cargo clippy`, and targeted `cargo test`.

Keep this skill thin so the generic and Rust-specific guidance does not drift.
