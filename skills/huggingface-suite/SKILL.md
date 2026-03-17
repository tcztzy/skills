---
name: huggingface-suite
description: "Hugging Face Hub / datasets / training / evaluation / tracking / Gradio 的统一入口（vendored）。"
---

# Hugging Face Suite

## 用途
- 这是一个 **套件入口 skill**：把同域技能合并到一个入口，避免触发分裂。
- vendored skills 存放在：`vendor/huggingface-skills/`（不会作为顶层 skill 被单独触发）。

## 路由规则（推荐）
- Hub/CLI 认证、下载/上传、缓存、repo 管理 → `hugging-face-cli`
- 数据集创建/维护/模板/SQL 查询/推送 → `hugging-face-datasets`
- 模型评测结果写入 model card / model-index → `hugging-face-evaluation`
- TRL + HF Jobs 训练/对齐、GGUF 转换 → `hugging-face-model-trainer`
- 实验指标记录/告警/仪表盘（Trackio）→ `hugging-face-trackio`
- Gradio demo / Blocks UI → `huggingface-gradio`（skill 名称通常是 `gradio`）

## 包含的 vendored skills

| 目录 | skill.name | 描述 |
|------|------------|------|
| `hugging-face-cli` | `hugging-face-cli` | Execute Hugging Face Hub operations using the `hf` CLI. Use when the user needs to download models/datasets/spaces, upload files to Hub repositories, create repos, manage local cache, or run compute jobs on HF infrastructure. Covers authentication, file transfers, repository creation, cache operations, and cloud compute. |
| `hugging-face-datasets` | `hugging-face-datasets` | Create and manage datasets on Hugging Face Hub. Supports initializing repos, defining configs/system prompts, streaming row updates, and SQL-based dataset querying/transformation. Designed to work alongside HF MCP server for comprehensive dataset workflows. |
| `hugging-face-evaluation` | `hugging-face-evaluation` | Add and manage evaluation results in Hugging Face model cards. Supports extracting eval tables from README content, importing scores from Artificial Analysis API, and running custom model evaluations with vLLM/lighteval. Works with the model-index metadata format. |
| `hugging-face-model-trainer` | `hugging-face-model-trainer` | This skill should be used when users want to train or fine-tune language models using TRL (Transformer Reinforcement Learning) on Hugging Face Jobs infrastructure. Covers SFT, DPO, GRPO and reward modeling training methods, plus GGUF conversion for local deployment. Includes guidance on the TRL Jobs package, UV scripts with PEP 723 format, dataset preparation and validation, hardware selection, cost estimation, Trackio monitoring, Hub authentication, and model persistence. Should be invoked for tasks involving cloud GPU training, GGUF conversion, or when users mention training on Hugging Face Jobs without local GPU setup. |
| `hugging-face-trackio` | `hugging-face-trackio` | Track and visualize ML training experiments with Trackio. Use when logging metrics during training (Python API), firing alerts for training diagnostics, or retrieving/analyzing logged metrics (CLI). Supports real-time dashboard visualization, alerts with webhooks, HF Space syncing, and JSON output for automation. |
| `huggingface-gradio` | `gradio` | Build Gradio web UIs and demos in Python. Use when creating or editing Gradio apps, components, event listeners, layouts, or chatbots. |

## 许可与来源
- 上游仓库：`https://github.com/huggingface/skills.git@main`
- License/NOTICE：见 `vendor/huggingface-skills/` 下的相关文件（若存在）。

## 更新/重建
- 同步来源缓存：运行 `skill-manager/scripts/sync-sources.py --all`
- 重建套件：运行 `skill-manager/scripts/build-suites.py --all`
- 构建后重启 Codex 以加载新/更新的 skills。
