---
name: wsl-fs
description: Use when the task needs to work with projects stored in the WSL Linux filesystem, including path translation, entering a distro, finding repos under /home, and running build or git commands in WSL instead of on Windows.
---

# WSL FS

## Purpose

Use this skill when a user wants to work against a project that lives inside a WSL2 distro, especially under paths like `/home/<user>/...`, rather than a Windows drive such as `C:\...`.

This skill helps Codex operate through `wsl.exe` and Linux paths, translate paths between Windows and WSL, auto-discover likely project roots, auto-select the best distro, and keep commands running in the distro where the toolchain actually lives.

By default, discovery is top-level-first: it prefers ancestor repo roots and hides nested subprojects such as `xgboost/plugin` unless you explicitly opt into nested results.

Important: this skill does **not** add new native workspace-mount capabilities to Codex Desktop. It improves the workflow for operating on WSL-backed projects and files that are already reachable from the current machine.

## When To Use It

Use this skill when the user asks for any of the following:

- Work on a repo stored in WSL, such as `/home/tom/project`
- Run commands inside a specific WSL2 distro instead of PowerShell
- Convert paths between Windows and WSL formats
- Find where a repo lives under a distro
- Auto-discover likely WSL project roots by name
- Auto-select the best distro before entering a repo
- Resolve an ambiguous project name to the right repo path
- Diagnose "works in WSL but not in Windows" environment differences
- Keep Python, Node, Rust, or build tools running inside Linux for performance and compatibility

Do not use this skill when the task is fully Windows-native and the project already lives on a Windows filesystem.

## Workflow

1. Identify or infer the distro and target path.

- Prefer checking available distros with `wsl.exe -l -v`.
- If the user does not specify a distro, prefer the running distro and then the default distro.
- Confirm whether the project path is a Linux path like `/home/...` or a Windows path like `C:\...`.
- When only a project name is given, search likely roots such as `$HOME/workspace`, `$HOME/projects`, `$HOME/src`, `$HOME/dev`, `$HOME/code`, and `$HOME/repos`.
- For discovery output, prefer top-level repos by default so nested repo noise does not dominate the result list.

2. Normalize the working path.

- For Linux-path projects, run commands with:

```powershell
wsl.exe -d <distro> -- bash -lc "cd '<linux-path>' && <command>"
```

- For Windows paths that must be used from WSL, convert them with `wslpath` first.
- For Linux paths that need a Windows-visible form, use `wslpath -w` or the UNC form `\\wsl$\<distro>\...` when appropriate.
- Prefer the helper scripts for repeatable automation:
  - `scripts/wsl-path.ps1` for path conversion
  - `scripts/wsl-project.ps1` for top-level-first discovery, resolution, and execution

3. Keep the toolchain in Linux.

- Prefer running package managers, compilers, tests, git, and other dev tooling inside WSL when the repo lives in WSL.
- Avoid running Linux-project toolchains through `/mnt/c/...` unless the user explicitly wants that tradeoff.

4. Be explicit about limitations.

- If the request depends on Codex Desktop opening a WSL path as a native workspace root, state that this skill cannot change the desktop app's workspace picker behavior.
- When needed, offer the closest practical workaround: operate through `wsl.exe`, use UNC paths when accessible, or keep the repo in WSL and use Codex primarily through terminal-driven workflows.

## Common Commands

List distros:

```powershell
wsl.exe -l -v
```

Run a command inside a distro:

```powershell
wsl.exe -d Ubuntu-22.04 -- bash -lc "cd '/home/tom/project' && git status"
```

Convert a Windows path to a WSL path:

```powershell
wsl.exe -d Ubuntu-22.04 -- wslpath 'C:\Users\huolo\Documents\Playground'
```

Convert a Linux path to a Windows path:

```powershell
wsl.exe -d Ubuntu-22.04 -- wslpath -w '/home/tom/project'
```

Discover likely WSL projects across preferred distros:

```powershell
powershell -ExecutionPolicy Bypass -File "$env:USERPROFILE\.codex\skills\wsl-fs\scripts\wsl-project.ps1" -Mode discover
```

Discover all nested candidates instead of only top-level repos:

```powershell
powershell -ExecutionPolicy Bypass -File "$env:USERPROFILE\.codex\skills\wsl-fs\scripts\wsl-project.ps1" -Mode discover -IncludeNested
```

Resolve a project name to a distro and repo root:

```powershell
powershell -ExecutionPolicy Bypass -File "$env:USERPROFILE\.codex\skills\wsl-fs\scripts\wsl-project.ps1" -Mode resolve -Project RealComplexNet
```

Resolve a nested project explicitly by exact name or exact path:

```powershell
powershell -ExecutionPolicy Bypass -File "$env:USERPROFILE\.codex\skills\wsl-fs\scripts\wsl-project.ps1" -Mode resolve -Project /home/tom/workspace/AdaCVNN/wccn_demo_code
```

Execute a command inside an auto-discovered repo:

```powershell
powershell -ExecutionPolicy Bypass -File "$env:USERPROFILE\.codex\skills\wsl-fs\scripts\wsl-project.ps1" -Mode exec -Project RealComplexNet -Command "git status --short"
```

Return machine-readable JSON:

```powershell
powershell -ExecutionPolicy Bypass -File "$env:USERPROFILE\.codex\skills\wsl-fs\scripts\wsl-project.ps1" -Mode resolve -Project RealComplexNet -Json
```

## Local Helper

Use the helper scripts in `scripts/` when you need repeatable automation from PowerShell.

- `scripts/wsl-path.ps1`: quick one-shot path conversion
- `scripts/wsl-project.ps1`: top-level-first discovery by default, with `-IncludeNested` for full nested scans
- `references/usage.md`: default search roots, auto-selection rules, and ready-to-run command patterns

If `resolve` returns an ambiguous match, prefer rerunning it with `-Json` or `-AllMatches`, inspect the candidates, and then rerun with either a more specific project name, an explicit path, or an explicit `-Distro`.

## Output Expectations

When using this skill, prefer returning:

- The distro used
- The normalized Linux working path
- The discovery or match method if a project name was inferred
- The exact command run in WSL
- Any translated path needed on the Windows side
- A short note if a limitation comes from Codex Desktop rather than from WSL itself
