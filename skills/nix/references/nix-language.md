# Nix Language (Nix Expression Language)

Primary references (official / canonical):
- Nix Reference Manual (language index): https://nix.dev/manual/nix/2.33/language/index.html
- Nix Reference Manual (syntax): https://nix.dev/manual/nix/2.33/language/syntax.html
- nix.dev tutorial (language basics): https://nix.dev/tutorials/nix-language

## Mental model

- The Nix language is an expression language used to describe build actions and configurations.
- You mostly compose values (attribute sets, lists, strings, functions) into higher-level outputs:
  - derivations (build recipes / store paths)
  - module options (NixOS / home-manager)
  - flake outputs (packages, apps, devShells, etc.)

## Core syntax quick reference

### Values

```nix
123
true
null
"string"
./relative/path
[ 1 "two" true ]
{ a = 1; b = "x"; }
```

### Attribute sets (maps)

```nix
{ name = "hello"; version = "1.0"; }

# Merge (right wins)
{ a = 1; } // { a = 2; b = 3; }

# Recursive set (self-reference inside the set)
rec { a = 1; b = a + 1; }

# inherit (copy identifiers into a set)
let x = 1; y = 2; in { inherit x y; }
```

### Functions

Nix functions take a single argument. Multi-arg functions are usually written as curried lambdas.

```nix
x: x + 1

a: b: a + b

{ pkgs, lib }:
  pkgs.hello
```

### let/in

```nix
let
  x = 1;
  y = 2;
in
  x + y
```

### Strings + interpolation

```nix
"hello ${toString 123}"

''multi-line
string with ${"interpolation"}''
```

### Importing other .nix files

`import` evaluates another Nix file and returns its resulting value.

```nix
let
  pkgs = import <nixpkgs> {};
in
  pkgs.hello
```

In flake-based projects, prefer passing `pkgs` explicitly (avoid `<nixpkgs>` when possible).

```nix
# ./lib.nix
{ pkgs }:
{
  helloPkg = pkgs.hello;
}

# flake.nix
outputs = { self, nixpkgs }:
let
  pkgs = nixpkgs.legacyPackages.x86_64-linux;
  lib = import ./lib.nix { inherit pkgs; };
in
{
  packages.x86_64-linux.default = lib.helloPkg;
};
```

## Common idioms in nixpkgs-style code

- `with pkgs; [ ... ]` brings package names into scope (use sparingly; it can obscure where names come from).
- `callPackage` pattern: write a function that takes dependencies as args, then let nixpkgs fill them.
- `lib` helpers (string/list/attrset utilities) are usually under `pkgs.lib` or `lib`.

## Debugging / evaluation helpers (version-dependent)

- Add `--show-trace` when you see evaluation errors.
- Use `nix eval` / `nix repl` to inspect expressions in isolation.

Keep solutions version-aware (ask for `nix --version` and use `nix <cmd> --help` when a flag differs).

