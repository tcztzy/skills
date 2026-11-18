# Optional maintenance commands

These existing utilities retain their CLI interfaces. Run only commands needed for
the requested maintenance task; they are not prerequisites for reviewing a skill.
Examples assume this repository's root. For an installed copy, resolve `scripts/`
relative to its `SKILL.md`. Check the selected command's `--help` for all options.

| Task | Command | Result and side effects |
| --- | --- | --- |
| Validate metadata | `python3 skills/skill-manager/scripts/validate-skill.py path/to/skill` | Checks basic frontmatter, name, and description; does not assess usefulness or semantic accuracy |
| Inventory and runtime readiness | `python3 skills/skill-manager/scripts/audit-installed-skills.py --skills-root path/to/skills --workspace path/to/audit` | Inventories the supplied directory and probes the current environment in memory. Writes JSON and Markdown reports. |
| Convert a Claude skill | `python3 skills/skill-manager/scripts/convert-claude-skill.py --src path/to/source --dest path/to/skills` | Copies and rewrites the skill; `--force` replaces an existing destination |
| Migrate Windows skills | `python3 skills/skill-manager/scripts/migrate-windows-codex-skills.py --source-root path/to/source --dest-root path/to/skills --workspace /tmp/skill-migration` | Copies missing skills and writes a migration manifest |
| Inspect migrated skills | `python3 skills/skill-manager/scripts/audit-migrated-skills.py --manifest path/to/migration_manifest.json --workspace /tmp/skill-audit --skills-root path/to/skills` | Writes readiness reports and evaluation packs; its retirement labels do not establish a skill's usefulness |
| Refresh runtime registry without installation | `python3 skills/skill-manager/scripts/bootstrap-global-skill-runtime.py --no-install --runtime-root path/to/runtimes` | Probes and writes the registry, shell initialization, and refresh helper; this is not a read-only command |

Runtime bootstrap without `--no-install` may create environments and install packages
or tools. The shared runtime uses the Unix/WSL virtual environment layout and a POSIX
shell. Its package lists use the versions available at install time. A domain refresh
preserves the other domains and their probe times. The default root is
`~/.codex/skill-runtimes/`. The helper at `~/.local/bin/codex-skill-runtime-refresh`
uses the current bootstrap script and selected root. Override the root with
`CODEX_SKILL_RUNTIME_ROOT` or `--runtime-root`.

Each successful Python domain installation writes
`<runtime-root>/<domain>/requirements.freeze.txt`. Its header identifies the
interpreter and platform. It contains the installed versions from `pip freeze --all`,
including transitive dependencies. A failed installation or dependency check retains
the last successful snapshot and returns a nonzero bootstrap status.

To replay a saved snapshot, use the matching Python interpreter on a compatible
platform and a new environment. For example, with `SNAPSHOT` set to the file path:

```sh
python3 -m venv replay-env
replay-env/bin/python -m pip install --no-deps -r "$SNAPSHOT"
replay-env/bin/python -m pip check
replay-env/bin/python -m pip freeze --local --all
```

The final package lines should match the snapshot. For offline replay, supply a
wheelhouse containing the recorded distributions via `--no-index --find-links`.
The snapshot records package versions. Preserve the wheels and their hashes when
exact build artifacts matter, and retain the sources of any direct references.

The installed-skills report tests runtime prerequisites covered by explicit probes.
`unverified` means the skill has no probe. The Typst probe compiles a fixed, local
sample in a temporary directory and checks the PDF header and trailer. The JSON
`artifact_check` is true for a passing sample, false for a failed attempt, and null
when no output check ran. The LaTeX-to-Word probe checks Python and Pandoc availability.
Run a representative task to evaluate workflow quality.
The separate migration audit can reuse a saved runtime snapshot.

Conversion reads [preferences.json](preferences.json) for placeholder rewrites and
Codex usage notes. It generates missing `agents/openai.yaml`; `--prefs`, `--no-notes`,
and `--no-rewrite` control those behaviors. Review the converted output for meaning.

`validate_skill.py`, `skill_inventory.py`, `runtime_registry.py`, and `utils.py` are
shared implementations used by these entry points. Keep their callers in scope when
changing an interface. Use the built-in `skill-creator` for general authoring guidance.

## Relevant checks

```bash
python3 skills/skill-manager/scripts/validate-skill.py skills/skill-manager
python3 -m unittest discover -s skills/skill-manager/tests -p 'test_*.py'
```
