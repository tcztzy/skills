---
name: nix
description: Write, review, and debug Nix expressions, flakes, NixOS/Home Manager/nix-darwin modules, overlays, and derivations. Use for *.nix files; Nix evaluation or build failures; package, app, devShell, and system outputs; or nix build/run/develop/flake/config commands.
---

# Nix

Focus on Nix-specific semantic failures. Do not reteach basic syntax unless the
user asks.

## Work from the local contract

Before editing:

1. Read repository instructions, the task, nearby Nix files, and `flake.lock`.
2. Identify the boundary: expression, flake output, NixOS/Home
   Manager/nix-darwin module, overlay, or derivation.
3. Inspect the supplied `lib`, packages, inputs, and outputs. Never assume a
   package exists, an input exports `.default`, or a fake `lib` is complete.
4. Check Nix version and target system when relevant. Use
   `scripts/nix-diagnose.sh` if environment details are unclear.
5. Run the narrowest existing evaluator or test before editing.

Read `references/nixbench-lessons.md` for modules, packaging, purity, debugging,
or escaping. Its guardrails come from GPT-5.6 Sol's NixBench failures.

## Non-negotiable checks

- Use the exact option/output namespace and keep NixOS, Home Manager,
  nix-darwin, overlays, and derivations in their proper layers.
- Extend module values with module merging; do not read an option while defining
  the same option just to append to it.
- Preserve unrelated definitions and gate new configuration at the narrowest
  correct boundary.
- Treat the project's dependency set as an API. Use only verified helpers and
  package attributes.
- Keep builds offline: fixed Nix inputs, store paths, and no sandbox bypass.
- Distinguish native build tools from target dependencies; preserve phase,
  `meta`, and `passthru` contracts.
- Review Nix interpolation, shell interpolation, command substitution, and path
  composition separately.

## Validate in layers

Prefer repository checks. Otherwise use the smallest applicable sequence:

1. Format or parse check.
2. Focused `nix eval --show-trace` of the changed value.
3. `nix flake show --all-systems` or `nix flake check --no-build`.
4. `nix build -L --show-trace <exact-installable>` when build behavior matters.
5. A safe, authorized runtime or activation check when needed.

Parsing is not module evaluation; evaluation is not a build. State which layers
remain unverified.

## Evidence and handoff

- Classify the failure: parse, evaluation, fetch, build, activation, or
  runtime.
- Preserve the exact reproducer and first relevant error. Separate observations
  from hypotheses and do not chase symptoms from a later layer.
- Report the changed contract, checks and results, system/version assumptions,
  and remaining unverified behavior.

## Version-sensitive commands

Read `references/nix-cli.md` before suggesting configuration, lock-file, profile,
or other commands that have changed across Nix releases. Prefer the installed
CLI's `--help` over remembered flags.
