# Optional maintenance commands

These existing utilities retain their CLI interfaces. Run only commands needed for
the requested maintenance task; they are not prerequisites for reviewing a skill.
Examples assume this repository's root. For an installed copy, resolve `scripts/`
relative to its `SKILL.md`. Check the selected command's `--help` for all options.

| Task | Command | Result and side effects |
| --- | --- | --- |
| Validate metadata | `python3 skills/skill-manager/scripts/validate-skill.py path/to/skill` | Checks basic frontmatter, name, and description; does not assess usefulness or semantic accuracy |
| Inventory and runtime readiness | `python3 skills/skill-manager/scripts/audit-installed-skills.py --skills-root path/to/skills --workspace /tmp/skill-audit` | Writes reports; uses an existing runtime registry or probes in memory without installing dependencies |
| Convert a Claude skill | `python3 skills/skill-manager/scripts/convert-claude-skill.py --src path/to/source --dest path/to/skills` | Copies and rewrites the skill; `--force` replaces an existing destination |
| Migrate Windows skills | `python3 skills/skill-manager/scripts/migrate-windows-codex-skills.py --source-root path/to/source --dest-root path/to/skills --workspace /tmp/skill-migration` | Copies missing skills and writes a migration manifest |
| Inspect migrated skills | `python3 skills/skill-manager/scripts/audit-migrated-skills.py --manifest path/to/migration_manifest.json --workspace /tmp/skill-audit --skills-root path/to/skills` | Writes readiness reports and evaluation packs; its retirement labels do not establish a skill's usefulness |
| Refresh runtime registry without installation | `python3 skills/skill-manager/scripts/bootstrap-global-skill-runtime.py --no-install --runtime-root path/to/runtimes` | Probes and writes the registry, shell initialization, and refresh helper; this is not a read-only command |

Runtime bootstrap without `--no-install` may create environments and install packages
or tools. Use it only for a requested runtime preparation task. `--domain` limits the
selected domain; the default runtime root is `~/.codex/skill-runtimes/`. The refresh
helper is written to `~/.local/bin/codex-skill-runtime-refresh` even with a custom root.
Readiness results concern the recorded dependencies, not whether a skill improves
agent behavior; an existing registry can be reused without a fresh probe.

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
