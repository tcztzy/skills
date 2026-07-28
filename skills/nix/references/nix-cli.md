# Version-aware Nix CLI

Use the installed CLI as the authority:

```sh
nix --version
nix <command> --help
```

Official command reference:
https://nix.dev/manual/nix/latest/command-ref/new-cli/nix.html

## Read-only inspection

```sh
nix config show
nix config check
nix registry list
nix store info
nix flake metadata --no-write-lock-file .
nix flake show --all-systems --no-write-lock-file .
```

`nix config show` is the current spelling. `nix show-config` is the pre-2.20
spelling; use it only as a compatibility fallback.

Inspect outputs before selecting them:

```sh
nix flake show --all-systems --no-write-lock-file .
nix eval --json --no-write-lock-file '.#packages.aarch64-darwin' \
  --apply builtins.attrNames
```

Do not assume an input or project exports `packages.<system>.default`.

## Evaluation and build

```sh
nix eval --show-trace --no-write-lock-file INSTALLABLE
nix flake check --no-build --show-trace --no-write-lock-file
nix build -L --show-trace INSTALLABLE
nix log INSTALLABLE
```

`nix flake check --no-build` checks evaluation and output shape, not whether a
derivation builds. `nix build` normally creates a `result` symlink; use
`--no-link` when no local link is wanted.

## Lock-file changes

These commands write `flake.lock`:

```sh
nix flake update
nix flake update nixpkgs
```

`nix flake lock --update-input nixpkgs` is deprecated. Review and commit
intentional lock-file changes; do not update unrelated inputs while debugging.

## Configuration edits

Configuration location and precedence vary by installation and platform.
Inspect `nix config show` before editing; one `nix.conf` does not prove a setting
is active.

## Legacy compatibility

Use `nix-build`, `nix-shell`, or pre-2.20 `nix show-config` only when the project
or installed Nix requires them.

When a flag is rejected, check that subcommand's local `--help` rather than
guessing a replacement.
