# Nix CLI (quick cheat sheet)

Primary references (official / canonical):
- `nix build`: https://nix.dev/manual/nix/latest/command-ref/new-cli/nix3-build.html
- `nix run`: https://nix.dev/manual/nix/latest/command-ref/new-cli/nix3-run.html
- `nix profile`: https://nix.dev/manual/nix/latest/command-ref/new-cli/nix3-profile.html
- `nix flake`: https://nix.dev/manual/nix/latest/command-ref/new-cli/nix3-flake.html
- Install Nix (nix.dev): https://nix.dev/install-nix

## Package discovery

- Search (nixpkgs): `nix search nixpkgs <name>`
- Show a flake: `nix flake show github:NixOS/nixpkgs`

## Build / run

- Build a package (flake ref): `nix build nixpkgs#hello`
- Build current flake default: `nix build .`
- Build a specific attribute: `nix build .#myPkg`
- Run an app/package: `nix run nixpkgs#hello`
- Run current flake default app: `nix run .`

Notes:
- `nix build` typically creates a `./result` symlink unless you disable linking.
- Add `-L` / `--print-build-logs` to surface build logs.

## Development shells

- Enter a dev shell from a flake: `nix develop`
- Enter a named dev shell: `nix develop .#myShell`
- Run a command inside the dev shell: `nix develop -c <cmd> ...`

Contrast (roughly):
- `nix develop`: dev environment defined by `devShells` (flake output).
- `nix shell`: ad-hoc environment with selected packages (more like `nix-shell -p`).

If a user's Nix version lacks a subcommand or flag, fall back to `nix <cmd> --help`.

## User profiles (install packages into your user environment)

- Add a package: `nix profile add nixpkgs#jq`
- List installed packages: `nix profile list`
- Remove by index: `nix profile remove <index>`
- Upgrade: `nix profile upgrade --all`

## Flake management

- Initialize a new flake: `nix flake init`
- Show outputs: `nix flake show .`
- Update inputs (lock file): `nix flake update`
- Update one input: `nix flake lock --update-input nixpkgs`

## Debugging checklist

- Evaluation errors:
  - Re-run with `--show-trace`.
  - Reduce to a minimal expression (`nix eval` / `nix repl`) when possible.
- Build errors:
  - Add `-L` / `--print-build-logs`.
  - Ask for the failing derivation name and full log output.
- Repro issues:
  - Confirm `flake.lock` exists and is committed/pinned.
  - Confirm the user's system (`x86_64-linux`, `aarch64-darwin`, etc.).

