# Skills Repository

This repository keeps installable Agent Skills under a single [`skills/`](./skills) entrypoint, following the layout used by [openai/skills](https://github.com/openai/skills) and [anthropics/skills](https://github.com/anthropics/skills).

## Layout

- [`skills/`](./skills): all discoverable skills
- [`skills/.system/`](./skills/.system): system-level helper skills
- [`skills/<skill-name>/`](./skills): user-installable skills

## Local Usage

Point your local skill roots at this directory:

- `~/.codex/skills -> /Users/tcztzy/skills/skills`
- `~/.claude/skills -> /Users/tcztzy/skills/skills`

That keeps runtime lookup paths stable, for example:

- `$CODEX_HOME/skills/playwright/scripts/playwright_cli.sh`
- `$CODEX_HOME/skills/jupyter-notebook/scripts/new_notebook.py`
