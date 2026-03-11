# Flakes (flake.nix / flake.lock)

Primary references (official / canonical):
- nix.dev concept guide: https://nix.dev/concepts/flakes.html
- Nix Reference Manual (`nix flake`): https://nix.dev/manual/nix/latest/command-ref/new-cli/nix3-flake.html
- Nix Reference Manual (`nix run` / `nix build`): https://nix.dev/manual/nix/latest/command-ref/new-cli/nix3-run.html

## What a flake is

- A flake is a source tree with a `flake.nix` at its root.
- It declares:
  - `inputs` (dependencies, typically including `nixpkgs`)
  - `outputs` (packages, apps, dev shells, NixOS configs, etc.)
- When you evaluate a flake, Nix writes a `flake.lock` to pin input revisions for reproducibility.

## Enabling flakes (common setups)

Many installations still require enabling experimental features:

```
# ~/.config/nix/nix.conf (or /etc/nix/nix.conf)
experimental-features = nix-command flakes
```

If unsure, prefer asking the user to run:
- `nix --version`
- `nix show-config | grep experimental-features`

## Minimal flake example (dev shell + package)

```nix
{
  description = "Example flake";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";

  outputs = { self, nixpkgs }:
    let
      system = "x86_64-linux";
      pkgs = nixpkgs.legacyPackages.${system};
    in
    {
      packages.${system}.default = pkgs.hello;

      devShells.${system}.default = pkgs.mkShell {
        packages = [ pkgs.git pkgs.curl ];
      };
    };
}
```

Run:
- `nix develop` (enters the dev shell)
- `nix build` (builds `packages.<system>.default`)

## Common workflows

- Inspect outputs: `nix flake show .`
- Update inputs (writes `flake.lock`): `nix flake update`
- Update one input: `nix flake lock --update-input nixpkgs`
- Build a specific output: `nix build .#packages.<system>.myPkg`
- Run an app: `nix run .#myApp`
- Enter a dev shell: `nix develop .#myShell`

## Output conventions (useful defaults)

When users run `nix build .`, `nix run .`, or `nix develop .` without specifying an attribute,
Nix looks for conventional defaults (e.g., `packages.<system>.default`, `apps.<system>.default`,
`devShells.<system>.default`). When in doubt, check `nix flake show .`.

