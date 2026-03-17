---
name: research-suite
description: "科研写作、EDA、统计分析、可视化统一入口（vendored）。"
---

# Research Suite

## 用途
- 这是一个 **套件入口 skill**：把同域技能合并到一个入口，避免触发分裂。
- vendored skills 存放在：`vendor/k-dense-claude-scientific-skills/`（不会作为顶层 skill 被单独触发）。

## 路由规则（推荐）
- 论文/报告写作（IMRAD、引用格式、审稿回复）→ `scientific-writing`
- 数据探索与质量检查（EDA 报告）→ `exploratory-data-analysis`
- 统计检验/效应量/假设检验与规范化汇报 → `statistical-analysis`
- 期刊级出图（多面板、显著性标注、色盲友好）→ `scientific-visualization`

## 重要说明
- vendored 文档里可能含有较强硬的流程建议（例如“必须画图形摘要”等）。本 suite 只把它们当作 **可选策略**，不作为硬性要求。

## 包含的 vendored skills

| 目录 | skill.name | 描述 |
|------|------------|------|
| `scientific-writing` | `scientific-writing` | Core skill for the deep research and writing tool. Write scientific manuscripts in full paragraphs (never bullet points). Use two-stage process with (1) section outlines with key points using research-lookup then (2) convert to flowing prose. IMRAD structure, citations (APA/AMA/Vancouver), figures/tables, reporting guidelines (CONSORT/STROBE/PRISMA), for research papers and journal submissions. |
| `exploratory-data-analysis` | `exploratory-data-analysis` | Perform comprehensive exploratory data analysis on scientific data files across 200+ file formats. This skill should be used when analyzing any scientific data file to understand its structure, content, quality, and characteristics. Automatically detects file type and generates detailed markdown reports with format-specific analysis, quality metrics, and downstream analysis recommendations. Covers chemistry, bioinformatics, microscopy, spectroscopy, proteomics, metabolomics, and general scientific data formats. |
| `statistical-analysis` | `statistical-analysis` | Guided statistical analysis with test selection and reporting. Use when you need help choosing appropriate tests for your data, assumption checking, power analysis, and APA-formatted results. Best for academic research reporting, test selection guidance. For implementing specific models programmatically use statsmodels. |
| `scientific-visualization` | `scientific-visualization` | Meta-skill for publication-ready figures. Use when creating journal submission figures requiring multi-panel layouts, significance annotations, error bars, colorblind-safe palettes, and specific journal formatting (Nature, Science, Cell). Orchestrates matplotlib/seaborn/plotly with publication styles. For quick exploration use seaborn or plotly directly. |

## 许可与来源
- 上游仓库：`https://github.com/K-Dense-AI/claude-scientific-skills.git@main`
- License/NOTICE：见 `vendor/k-dense-claude-scientific-skills/` 下的相关文件（若存在）。

## 更新/重建
- 同步来源缓存：运行 `skill-manager/scripts/sync-sources.py --all`
- 重建套件：运行 `skill-manager/scripts/build-suites.py --all`
- 构建后重启 Codex 以加载新/更新的 skills。
