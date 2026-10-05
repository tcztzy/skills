---
name: experiment-bfts-runner
description: Run the standalone BFTS experiment pipeline to execute multi-agent tree-search experiments from a prepared bfts_config.yaml. Use with an existing run configuration to produce logs, workspaces, and experiment artifacts.
---

# Experiment BFTS Runner

## Overview
Execute the full BFTS tree-search experiment workflow from a prepared bfts_config.yaml, producing logs, workspaces, and per-node experiment results.

## Workflow
1. Prepare a run directory
   - Provide a run directory with `idea.json`, `idea.md`, and `bfts_config.yaml`; configure its input, log, and workspace paths.
2. Run the experiment
   - Offline default:
     ~~~bash
     uv run --with pyyaml,omegaconf,openai,anthropic,backoff,rich,humanize -s scripts/run_bfts.py --config runs/<run>/bfts_config.yaml
     ~~~
   - Online (required for LLM calls):
     ~~~bash
     uv run -s scripts/run_bfts.py --config runs/<run>/bfts_config.yaml --online
     ~~~
3. Inspect outputs
   - Inspect the logs, workspaces, and per-node results under the run directory.

## Inputs
- --config: path to bfts_config.yaml.
- --online: enable network calls to LLM providers (default: offline).

## Outputs
- logs/ and workspaces/ under the run directory.
- Per-node experiment results (e.g., experiment_results/ containing experiment_data.npy).

## Safeguards
- Offline by default; --online required for network calls.
- Reads only from the run directory; writes only within the run directory and its logs/ and workspaces/ subfolders.
- No file deletion unless you manually clean outputs.

## References
- Run manifest schema: references/run.manifest.json
- Idea schema: references/idea.schema.json
- Summary schema: references/summary.schema.json
