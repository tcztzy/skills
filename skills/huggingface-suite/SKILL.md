---
name: huggingface-suite
description: "Unified entrypoint for Hugging Face Hub, datasets, training, evaluation, tracking, and Gradio workflows (vendored)."
---

# Hugging Face Suite

## Purpose
- This is a **suite entrypoint skill** that consolidates related capabilities behind one top-level trigger.
- Vendored skills live under `vendor/huggingface-skills/` and are not intended to trigger independently as top-level skills.

## Routing Rules (Recommended)
- Hub and CLI authentication, downloads, uploads, cache management, or repository administration -> `hugging-face-cli`
- Dataset creation, maintenance, templates, SQL querying, or publishing -> `hugging-face-datasets`
- Writing evaluation results into model cards or `model-index` metadata -> `hugging-face-evaluation`
- TRL plus Hugging Face Jobs training, alignment workflows, or GGUF conversion -> `hugging-face-model-trainer`
- Experiment metric logging, alerts, or Trackio dashboards -> `hugging-face-trackio`
- Gradio demos or Blocks-based UIs -> `gradio`

## Included Vendored Skills

| Directory | skill.name | Description |
|------|------------|------|
| `hugging-face-cli` | `hugging-face-cli` | Execute Hugging Face Hub operations using the `hf` CLI. Use when the user needs to download models/datasets/spaces, upload files to Hub repositories, create repos, manage local cache, or run compute jobs on HF infrastructure. Covers authentication, file transfers, repository creation, cache operations, and cloud compute. |
| `hugging-face-datasets` | `hugging-face-datasets` | Create and manage datasets on Hugging Face Hub. Supports initializing repos, defining configs/system prompts, streaming row updates, and SQL-based dataset querying/transformation. Designed to work alongside HF MCP server for comprehensive dataset workflows. |
| `hugging-face-evaluation` | `hugging-face-evaluation` | Add and manage evaluation results in Hugging Face model cards. Supports extracting eval tables from README content, importing scores from Artificial Analysis API, and running custom model evaluations with vLLM/lighteval. Works with the model-index metadata format. |
| `hugging-face-model-trainer` | `hugging-face-model-trainer` | This skill should be used when users want to train or fine-tune language models using TRL (Transformer Reinforcement Learning) on Hugging Face Jobs infrastructure. Covers SFT, DPO, GRPO and reward modeling training methods, plus GGUF conversion for local deployment. Includes guidance on the TRL Jobs package, UV scripts with PEP 723 format, dataset preparation and validation, hardware selection, cost estimation, Trackio monitoring, Hub authentication, and model persistence. Should be invoked for tasks involving cloud GPU training, GGUF conversion, or when users mention training on Hugging Face Jobs without local GPU setup. |
| `hugging-face-trackio` | `hugging-face-trackio` | Track and visualize ML training experiments with Trackio. Use when logging metrics during training (Python API), firing alerts for training diagnostics, or retrieving/analyzing logged metrics (CLI). Supports real-time dashboard visualization, alerts with webhooks, HF Space syncing, and JSON output for automation. |
| `gradio` | `gradio` | Build Gradio web UIs and demos in Python. Use when creating or editing Gradio apps, components, event listeners, layouts, or chatbots. |

## License and Source
- Upstream repository: `https://github.com/huggingface/skills.git@main`
- License and notice files: see the relevant files under `vendor/huggingface-skills/` when present.

## Update / Rebuild
- Sync cached sources: run `skill-manager/scripts/sync-sources.py --all`
- Rebuild the suite: run `skill-manager/scripts/build-suites.py --all`
- Restart Codex after rebuilding so newly added or updated skills are loaded.
