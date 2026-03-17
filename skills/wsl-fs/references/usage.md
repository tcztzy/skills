# WSL FS Usage Notes

## Auto-selection rules

- If `-Distro` is provided, use that distro only.
- Otherwise prefer a running distro first.
- If multiple distros are available, prefer the default distro next.
- Ignore `docker-desktop` style utility distros for normal project discovery.

## Default search roots

When no `-SearchRoots` are provided, the helper searches these Linux paths in order:

- `$HOME/workspace`
- `$HOME/projects`
- `$HOME/src`
- `$HOME/dev`
- `$HOME/code`
- `$HOME/repos`
- `$HOME/git`

If `-IncludeHomeFallback` is set, it also scans `$HOME` itself and prunes hidden directories under the home root.

## Default discovery behavior

- `discover` returns top-level repos by default.
- Nested subprojects under a higher-level repo are hidden unless `-IncludeNested` is provided.
- `resolve` and `exec` still allow exact nested matches by exact name or exact path.
- Fuzzy nested matching only happens when `-IncludeNested` is provided.

## Recommended command patterns

Discover projects:

```powershell
powershell -ExecutionPolicy Bypass -File "$env:USERPROFILE\.codex\skills\wsl-fs\scripts\wsl-project.ps1" -Mode discover
```

Discover projects including nested subprojects:

```powershell
powershell -ExecutionPolicy Bypass -File "$env:USERPROFILE\.codex\skills\wsl-fs\scripts\wsl-project.ps1" -Mode discover -IncludeNested
```

Resolve one project:

```powershell
powershell -ExecutionPolicy Bypass -File "$env:USERPROFILE\.codex\skills\wsl-fs\scripts\wsl-project.ps1" -Mode resolve -Project RealComplexNet -Json
```

Execute inside the resolved repo:

```powershell
powershell -ExecutionPolicy Bypass -File "$env:USERPROFILE\.codex\skills\wsl-fs\scripts\wsl-project.ps1" -Mode exec -Project RealComplexNet -Command "git status --short" -Json
```

List all matches when a name is ambiguous:

```powershell
powershell -ExecutionPolicy Bypass -File "$env:USERPROFILE\.codex\skills\wsl-fs\scripts\wsl-project.ps1" -Mode resolve -Project wccn_demo_code -AllMatches -Json
```

Resolve an explicit Linux path:

```powershell
powershell -ExecutionPolicy Bypass -File "$env:USERPROFILE\.codex\skills\wsl-fs\scripts\wsl-project.ps1" -Mode resolve -Project /home/tom/workspace/RealComplexNet -Json
```

Resolve a nested project exactly without turning on fuzzy nested matching:

```powershell
powershell -ExecutionPolicy Bypass -File "$env:USERPROFILE\.codex\skills\wsl-fs\scripts\wsl-project.ps1" -Mode resolve -Project /home/tom/workspace/AdaCVNN/wccn_demo_code -Json
```
