---
name: research-suite
description: "Unified entrypoint for scientific writing, exploratory data analysis, statistical analysis, and visualization workflows (vendored)."
---

# Research Suite

## Purpose
- This is a **suite entrypoint skill** that consolidates related capabilities behind one top-level trigger.
- Vendored skills live under `vendor/k-dense-claude-scientific-skills/` and are not intended to trigger independently as top-level skills.

## Routing Rules (Recommended)
- Research-idea triage, `go/kill/pivot/scope-down` decisions, or paper positioning/story tightening -> top-level `research-impact-strategy` instead of this suite
- Manuscript or report writing, including IMRAD structure, citation formats, and reviewer responses -> `scientific-writing`
- Data exploration and quality checks, including EDA reports -> `exploratory-data-analysis`
- Statistical testing, effect sizes, hypothesis testing, and standardized reporting -> `statistical-analysis`
- Journal-ready figures, including multi-panel layouts, significance annotations, and colorblind-safe palettes -> `scientific-visualization`

## Important Note
- Some vendored documentation uses stronger process language, for example by treating graphical abstracts as mandatory. In this suite, those items should be treated as **optional strategies**, not hard requirements.

## Included Vendored Skills

| Directory | skill.name | Description |
|------|------------|------|
| `scientific-writing` | `scientific-writing` | Core skill for the deep research and writing tool. Write scientific manuscripts in full paragraphs (never bullet points). Use two-stage process with (1) section outlines with key points using research-lookup then (2) convert to flowing prose. IMRAD structure, citations (APA/AMA/Vancouver), figures/tables, reporting guidelines (CONSORT/STROBE/PRISMA), for research papers and journal submissions. |
| `exploratory-data-analysis` | `exploratory-data-analysis` | Perform comprehensive exploratory data analysis on scientific data files across 200+ file formats. This skill should be used when analyzing any scientific data file to understand its structure, content, quality, and characteristics. Automatically detects file type and generates detailed markdown reports with format-specific analysis, quality metrics, and downstream analysis recommendations. Covers chemistry, bioinformatics, microscopy, spectroscopy, proteomics, metabolomics, and general scientific data formats. |
| `statistical-analysis` | `statistical-analysis` | Guided statistical analysis with test selection and reporting. Use when you need help choosing appropriate tests for your data, assumption checking, power analysis, and APA-formatted results. Best for academic research reporting, test selection guidance. For implementing specific models programmatically use statsmodels. |
| `scientific-visualization` | `scientific-visualization` | Meta-skill for publication-ready figures. Use when creating journal submission figures requiring multi-panel layouts, significance annotations, error bars, colorblind-safe palettes, and specific journal formatting (Nature, Science, Cell). Orchestrates matplotlib/seaborn/plotly with publication styles. For quick exploration use seaborn or plotly directly. |

## License and Source
- Upstream repository: `https://github.com/K-Dense-AI/claude-scientific-skills.git@main`
- License and notice files: see the relevant files under `vendor/k-dense-claude-scientific-skills/` when present.

## Update / Rebuild
- Sync cached sources: run `skill-manager/scripts/sync-sources.py --all`
- Rebuild the suite: run `skill-manager/scripts/build-suites.py --all`
- Restart Codex after rebuilding so newly added or updated skills are loaded.
