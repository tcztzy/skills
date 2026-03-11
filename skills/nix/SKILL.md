---
name: nix
description: Explain, write, and debug Nix expression language + common Nix workflows (flakes, nix CLI, nixpkgs). Use when working with *.nix files (flake.nix, flake.lock, shell.nix, default.nix), NixOS/home-manager configs, or commands like `nix build`, `nix run`, `nix develop`, `nix shell`, `nix profile`, and `nix flake`.
---

# Nix

## Overview

Help users understand and author Nix code (the Nix expression language) and apply it via reproducible workflows (especially flakes + the `nix` CLI).

## Workflow (do this first)

1. Identify the goal: language question vs. flake wiring vs. CLI invocation vs. packaging/debugging.
2. Ask for the minimum context:
   - OS (Linux/macOS/NixOS/WSL) + CPU arch
   - Nix version (`nix --version`)
   - flakes enabled? (`nix-command` + `flakes` experimental features)
   - target output: package, app, dev shell, NixOS config, home-manager, etc.
3. Prefer minimal, copy/pasteable deliverables:
   - name exact files to create/edit
   - provide a single command to run + what to expect
4. When debugging, request the full error + stack trace:
   - add `--show-trace` for evaluation errors
   - add `-L` / `--print-build-logs` for build failures

## References (load as needed)

- Nix language fundamentals + idioms: `references/nix-language.md`
- Flakes structure + lock file + inputs/outputs patterns: `references/flakes.md`
- Nix CLI cheat sheet (build/run/develop/shell/profile/flake) + debugging flags: `references/nix-cli.md`

## Common deliverables

- Minimal `flake.nix` that provides:
  - `packages.<system>.default` and/or `apps.<system>.default`
  - `devShells.<system>.default` for `nix develop`
- Non-flake entrypoints:
  - `default.nix` (for `nix-build` or `nix build --file/-f`)
  - `shell.nix` (for `nix-shell`)

## Notes

- The Nix 3 CLI and flakes are often documented as "experimental". Prefer version-aware guidance and fall back to `nix <cmd> --help` when behavior differs across versions.
