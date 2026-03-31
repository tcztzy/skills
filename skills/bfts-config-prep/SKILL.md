---
name: bfts-config-prep
description: Prepare a BFTS run directory from idea JSON by generating idea.md and a configured bfts_config.yaml. Use when starting a BFTS experiment from structured idea inputs and you want a runnable timestamped run folder under `runs/`.
---

# BFTS Config Prep

## Overview
Create a run folder with a timestamped name, generate `idea.md` from `idea.json`, copy a BFTS config template, and fill in required paths (`desc_file`, `data_dir`, `log_dir`, `workspace_dir`).

This skill subsumes the former `idea-to-markdown` step so BFTS setup is a single entrypoint instead of two chained skills.

## Workflow
1. **Ensure idea JSON exists**
   - `idea.json` follows `references/idea.schema.json`.
2. **Generate `idea.md`**
   - `uv run -s scripts/idea_to_markdown.py --in idea.json --out idea.md`
   - Optional code context:
   - `uv run -s scripts/idea_to_markdown.py --in idea.json --out idea.md --code-path baseline.py`
3. **Prepare run folder**
   - `uv run --with pyyaml -s scripts/prep_bfts_config.py --idea-json idea.json --idea-md idea.md --out-root runs`

## Outputs
- `runs/<timestamp>_<idea_name>/`
  - `idea.json`, `idea.md`, `bfts_config.yaml`
  - `data/`, `logs/`, `workspaces/`

## Safeguards
- Does not modify source idea files.
- Writes only under `--out-root`.

## References
- Idea schema: `references/idea.schema.json`
- BFTS template: `references/bfts_config_template.yaml`
