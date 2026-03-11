# Rust Playbook (Simplification + Measurement)

Use this reference when simplifying Rust code. Keep changes behavior-preserving by default, and validate with formatter-aligned metrics plus `cargo check` / `cargo clippy` / tests.

## Measurement

Start with the standard Rust quality gates:

```console
$ cargo fmt --all
$ cargo check
$ cargo clippy
$ cargo test
```

Track formatted size with:

```console
$ wc -l path/to/file.rs
$ wc -c path/to/file.rs
```

When token/AST metrics matter, create a tiny one-off probe with `proc-macro2` and `syn`.

`Cargo.toml`:

```toml
[package]
name = "rust_metrics"
version = "0.1.0"
edition = "2021"

[dependencies]
proc-macro2 = "1"
syn = { version = "2", features = ["full", "visit"] }
```

`src/main.rs`:

```rust
use proc_macro2::{TokenStream, TokenTree};
use std::{env, fs};
use syn::visit::{self, Visit};

fn count_tokens(stream: TokenStream) -> usize {
    fn walk(tt: TokenTree) -> usize {
        match tt {
            TokenTree::Group(group) => 1 + group.stream().into_iter().map(walk).sum::<usize>(),
            _ => 1,
        }
    }

    stream.into_iter().map(walk).sum()
}

#[derive(Default)]
struct AstMetrics {
    nodes: usize,
    branches: usize,
    depth: usize,
    max_depth: usize,
}

impl<'ast> Visit<'ast> for AstMetrics {
    fn visit_expr(&mut self, node: &'ast syn::Expr) {
        self.nodes += 1;
        self.depth += 1;
        self.max_depth = self.max_depth.max(self.depth);
        if matches!(
            node,
            syn::Expr::If(_)
                | syn::Expr::Match(_)
                | syn::Expr::ForLoop(_)
                | syn::Expr::While(_)
                | syn::Expr::Loop(_)
                | syn::Expr::Try(_)
        ) {
            self.branches += 1;
        }
        visit::visit_expr(self, node);
        self.depth -= 1;
    }

    fn visit_item(&mut self, node: &'ast syn::Item) {
        self.nodes += 1;
        self.depth += 1;
        self.max_depth = self.max_depth.max(self.depth);
        visit::visit_item(self, node);
        self.depth -= 1;
    }
}

fn main() {
    let path = env::args().nth(1).expect("usage: rust_metrics <file.rs>");
    let src = fs::read_to_string(&path).expect("read source");
    let toks = count_tokens(src.parse::<TokenStream>().expect("tokenize"));
    let file = syn::parse_file(&src).expect("parse");

    let mut metrics = AstMetrics::default();
    metrics.visit_file(&file);

    println!(
        "{{\"tokens\":{},\"ast_nodes\":{},\"ast_branches\":{},\"ast_max_depth\":{}}}",
        toks, metrics.nodes, metrics.branches, metrics.max_depth
    );
}
```

Notes:
- Always format first, or line-count wins will be noisy.
- Compare `lines` + `bytes` + `tokens` + `ast_*` together, not one metric in isolation.

## Simplification Patterns (Rust)

- Remove duplicate `match` arms and repeated literals.
- Collapse one-use temporaries and pass-through wrappers.
- Prefer iterator adapters/combinators only when they reduce total complexity after formatting.
- Prefer `if let`, `let ... else`, or `matches!` when they flatten control flow without hiding intent.
- Replace repetitive condition chains with data-driven lookups or small helpers when the result is clearer.

## Hard Guards

- Keep explicit types on public APIs and parsing/serialization boundaries.
- Preserve ownership/borrowing clarity; do not add clones just for shorter code.
- Keep `Result`-based propagation (`?`) for recoverable paths.
- Do not replace structured errors with opaque strings unless constraints force it.
- Keep doc examples and public API behavior aligned with the change.

## Positive vs Negative Examples

### Positive (branch reduction with `Option`)

Before:
```rust
fn finish_reason_text(reason: Option<&str>) -> &str {
    match reason {
        Some(reason) => reason,
        None => "stop",
    }
}
```

After:
```rust
fn finish_reason_text(reason: Option<&str>) -> &str {
    reason.unwrap_or("stop")
}
```

Why good:
- Same behavior.
- Fewer branches and tokens.
- Ownership/lifetime contract preserved.

### Negative (shorter but less clear)

```rust
let kind = if role == "user" { "human" } else if role == "assistant" { "ai" } else { "other" };
```

Why bad:
- Dense and harder to scan.
- Encourages nested conditional sprawl.
- Often loses to a readable `match` after formatting.

### Positive (readability-preserving simplification)

Before:
```rust
let tools = if payload.tools.is_empty() {
    Vec::new()
} else {
    payload.tools.clone()
};
```

After:
```rust
let tools = payload.tools.clone();
```

Why good:
- Behavior preserved (empty vec clone is still empty).
- Removes a redundant branch.
- Clearer intent.

## Common Failure Mode: Measurement Mistake

Do not claim success from a raw diff only:
- The file looks shorter before formatting.
- `cargo fmt` removes the apparent win.
- Tokens/bytes/AST were not measured.
- `clippy` or tests were skipped.

Correct action:
- Re-run formatter + metrics + `cargo check` / `cargo clippy` / tests, then report the true outcome.

## Output Checklist

- Report baseline and final metrics: lines, bytes, tokens, `ast_nodes`, `ast_branches`, `ast_max_depth`.
- Report net deltas and whether readability/maintainability stayed acceptable.
- Report validation results for `cargo check`, `cargo clippy`, and affected tests.
- If no true simplification is achieved, provide failure analysis and the next strategy.
