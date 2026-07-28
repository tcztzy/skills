# NixBench-derived failure checks

Source: [NixBench](https://github.com/maximilianpw/nixbench), its 29-task corpus,
and the detailed GPT-5.6 Sol xhigh run for corpus revision
`6c4205b2e2cf931545fbd2eebda50bc7a8363dbb`. These are guardrails, not answer
templates.

NixBench uses hidden shell checks and deliberately small fake libraries,
builders, and package sets. Plausible-looking Nix is not enough.

## Choose the right abstraction

- Map requirements to the exact option namespace.
- Native NixOS containers use `containers.<name>`; OCI backends use
  `virtualisation.oci-containers`.
- Inspect flake packages, apps, checks, and dev shells instead of inventing
  `.default`.
- Keep overlay output (`final: prev: { ... }`) out of module `options`/`config`.

Check: can the chosen value be evaluated with only the arguments and namespace
present in the task?

## Respect constrained APIs

- Do not introduce an unverified `lib` helper for convenience.
- Do not invent packages. Inspect attr names, flake outputs, or pinned nixpkgs.
- Prefer builtins when the available helpers are restricted.
- Test non-default values; configuration must flow through `cfg`.

## Compose modules; do not overwrite contributors

- Use `mkAfter`/`mkBefore` for list order and `mkDefault` for overridable values.
- Avoid definitions such as
  `option = config.option ++ [ value ];`: they self-reference the option being
  defined and can recurse.
- Preserve other consumers: Nushell must not remove Bash; Hyprland must not
  remove other portals or fallbacks.
- Apply `mkIf` at the correct boundary, adding a second gate when needed.

## Package with the phase and dependency contract

- Pin source and hash.
- Put host-executed helpers in `nativeBuildInputs`; put target libraries in
  `buildInputs`.
- Preserve required flags, checks, hooks, install destination, `meta`, and
  `mainProgram`.

With `overrideAttrs`, extend old metadata, hooks, `passthru`, and dependency
lists when they must survive.

## Keep builds offline

For an upstream-downloaded binary, model, or archive:

1. Fetch it through Nix with a pinned identity and hash.
2. Pass the store path by supported flag or environment variable.
3. Prefer a system library in `buildInputs` over a download feature.
4. Patch narrowly only when no offline switch exists.
5. Expose contracted assets through `passthru`.

Reject fixes that add `curl`/`wget` in a build phase, leave a network URL for
`build.rs`, or disable sandboxing.

## Separate Nix, shell, and path syntax

- Nix interpolation: `${nixExpression}`
- A literal shell interpolation inside an indented Nix string: `''${SHELL_VAR}`
- Shell command substitution: `$(command)`; inside a Nix string, verify it is
  meant for the shell.
- Path composition: `basePath + "/child"` stays a path;
  `"${basePath}/child"` is a string.

Review the evaluated string, not only the source text.

## Diagnose and report with evidence

- Use the earliest failing layer. An unknown option is evaluation, not runtime.
- Prefer discriminating observations: failed gateway ARP after link, address,
  and route outranks downstream DNS symptoms.
- Put false leads in `discarded`, not in evidence or next steps.
- Include exact command, platform, release, revision, expected/actual result,
  logs, observed facts, likely fix, and unverified items.
- Do not turn a likely fix into a confirmed root cause without verification.

## Validation pattern

For parameterized configuration, test enabled non-default values plus a disabled
or alternate case. Include existing list contributions and a restricted fake
dependency set where practical.

This catches hard-coded defaults, accidental replacement, self-reference, and
unverified helper assumptions.
