---
name: paper-visualizer
description: "Route publication-grade visualization tasks by chart family and execute manuscript-facing plot or diagram workflows with packaged agents, shared generators, style guides, and inspectable run artifacts. Use when prompts mention paper figures, chart choice or critique, plotting backends such as matplotlib, seaborn, ggplot2, plotnine, hvplot, geoviews, or datashader, or `paper-visualizer` workflows, and the deliverable is a paper-ready chart, plot, or diagram rather than casual image editing."
metadata:
  short_name: paper-visualizer
  aliases: data-to-viz,data-viz,data viz,chart chooser,chart critique,publication figure,matplotlib,seaborn,plotnine,ggplot2,hvplot,geoviews,datashader,bar chart,scatter,histogram,line chart,heatmap,choropleth,sankey,treemap
---

# Paper Visualizer

## Overview

Use this as the single top-level skill for publication-grade charts, plots, diagrams, and manuscript figure workflows.

This skill now absorbs the former `data-to-viz*` routing layer:
- first decide whether the request is chart-choice-only or a full implementation/workflow task,
- then route by chart family,
- then either return a shortlist with caveats or execute a manuscript-facing workflow / shared generator path.

Treat this skill's packaged `agents/`, `references/`, `scripts/`, and `assets/` as the source of truth for manuscript-facing workflow contracts. Treat the sibling `../data-to-viz/` directory as a shared asset pack for chart-selection references and deterministic generator helpers; it is no longer a separate user-facing skill entrypoint.

## When to Use

- Use this skill when the user wants chart selection, chart critique, publication figures, or paper-ready plots and diagrams.
- Use this skill when the prompt mentions plotting backends such as `matplotlib`, `seaborn`, `plotnine`, `ggplot2`, `hvplot`, `geoviews`, or `datashader` but the correct chart family still needs to be chosen first.
- Use this skill when the user gives a manuscript path such as `main.tex`, `paper.md`, `paper.typ`, or `draft.docx` and wants a prompt like `paper-visualizer main.tex 绘制 图 1`.
- Use this skill when the request mentions `full`, `planner`, `planner_stylist`, `planner_critic`, `vanilla`, `polish`, `evaluate`, or `chunked_extraction`.
- Do not use this skill for arbitrary photo editing, casual image refinement, or non-paper visual asset work.

## Routing Contract

- `paper-visualizer` is now the single entrypoint for both visualization routing and execution.
- Backend names are preference signals only. Do not choose a backend before choosing a chart family.
- Chart-choice-only tasks should return a shortlist with caveats instead of running a full workflow by default.
- Implementation tasks should choose the chart family first, then select either:
  - a shared generator-backed path,
  - a manuscript-facing `paper-visualizer` stage workflow,
  - or a doc-first backend recommendation when no generator-backed path exists.

## Chart Family Routing

Use the shared references in `../data-to-viz/references/` before choosing an implementation path.

- comparison or ranking:
  - questions like who is bigger, what is the order, grouped benchmark comparison
  - default forms: grouped bar, lollipop, Cleveland dot, grouped interval
- distribution:
  - spread, skew, tails, outliers, grouped distributions
  - default forms: histogram, density, box, violin, beeswarm, ridgeline
- correlation:
  - relationships between numeric variables, dense points, regression-style comparison
  - default forms: scatter, hexbin, 2D density
- evolution:
  - time, epoch, step, iteration, ordered trajectories
  - default forms: line, connected trajectory, ordered-step summary
- map:
  - locations, choropleths, spatial density, geospatial overlays
  - default forms: point map, choropleth, geographic density view
- multivariate:
  - heatmaps, small multiples, pair plots, many-variable layouts
  - default forms: heatmap, pair plot, correlogram, small multiples
- part-to-whole:
  - composition of a whole
  - default forms: stacked bar, normalized stacked bar, treemap, sunburst
- flow:
  - movement, transfer, transitions, connection volume
  - default forms: Sankey, alluvial, chord, network flow

## Global Caveat Filter

- Use `../data-to-viz/references/chart-selection-guide.md` and `../data-to-viz/references/chart-caveats.md`.
- Reject pie or doughnut when ordered comparison matters.
- Reject radar or spider when exact comparison or axis order matters.
- Reject dual-axis unless the task is critique.
- Treat Datashader as a rendering fallback inside correlation, evolution, or map, not as a new chart family.

## Shared Generator Paths

Use these helpers when the user wants a runnable first draft and the full staged workflow would be overkill.

- common inventory:
  - `../data-to-viz/scripts/tabular_inventory.py`
  - `../data-to-viz/scripts/npy_inventory.py`
- comparison or ranking:
  - `../data-to-viz/scripts/gen_seaborn_skeleton.py`
  - `../data-to-viz/scripts/gen_plotnine_skeleton.py`
  - `../data-to-viz/scripts/gen_ggplot2_skeleton.py`
  - `../data-to-viz/scripts/gen_matplotlib_skeleton.py`
- distribution:
  - `../data-to-viz/scripts/gen_seaborn_skeleton.py`
  - `../data-to-viz/scripts/gen_plotnine_skeleton.py`
  - `../data-to-viz/scripts/gen_ggplot2_skeleton.py`
- correlation:
  - `../data-to-viz/scripts/gen_seaborn_skeleton.py`
  - `../data-to-viz/scripts/gen_plotnine_skeleton.py`
  - `../data-to-viz/scripts/gen_matplotlib_skeleton.py`
- evolution:
  - `../data-to-viz/scripts/gen_seaborn_skeleton.py`
  - `../data-to-viz/scripts/gen_plotnine_skeleton.py`
  - `../data-to-viz/scripts/gen_ggplot2_skeleton.py`
  - `../data-to-viz/scripts/gen_matplotlib_skeleton.py`
- map:
  - `../data-to-viz/scripts/gen_holoviz_skeleton.py --mode geo`
- multivariate:
  - `../data-to-viz/scripts/gen_matplotlib_skeleton.py`
- `part-to-whole` and `flow` remain doc-first in v1; recommend the backend rather than claiming a generator-backed path.

## Workflow Modes

- `chart-choice-only`: classify the analytical claim, pick a chart family, run the caveat filter, and return a shortlist plus backend recommendation.
- `shared generator-backed chart`: use the shared helper scripts under `../data-to-viz/scripts/` to inventory data and generate a first runnable plotting skeleton.
- `full` or `planner_*`: generate a new diagram or plot from source content, optionally with retrieval, styling, and critic iterations.
- `manuscript figure`: read a manuscript, extract the relevant Figure context, pick a style guide from the manuscript domain, generate a diagram with Gemini, save it locally, and insert it back into the manuscript when the format supports it.
- `vanilla`: shortest direct render path when retrieval, styling, or critic loops are not needed.
- `polish`: analyze an existing benchmark image, suggest changes, and optionally regenerate.
- `evaluate`: compare a generated artifact and compute deterministic overall scoring.
- `chunked_extraction`: experimental long-source preprocessing.

## Input -> Actions -> Output

- Input:
  - for chart routing: the analytical claim, data shape, and any backend or publication constraints
  - for generator-backed chart runs: dataset path or inventory-ready input plus desired backend
  - for end-to-end manuscript runs: manuscript path, target figure number, and optional model/style overrides
  - `mode` and `task` (`diagram` or `plot`)
  - a writable working directory
  - source content, benchmark asset, or pre-split chunks depending on mode
  - optional `workflow_spec.json`; otherwise create a minimal one in the run directory
- Actions:
  - classify the request as route-only, shared-generator, or packaged workflow
  - choose the chart family before choosing a backend
  - use the shared chart-selection references and caveat filter when the request is not already pinned to a manuscript-stage workflow
  - when a generator-backed chart path is enough, run the relevant helpers under `../data-to-viz/scripts/`
  - for manuscript runs: read the manuscript, resolve `\input` / `\include` for LaTeX, extract caption + figref + method context, auto-select the most relevant packaged style guide, call Gemini text refinement and image generation through `scripts/manuscript_figure.py`, save the generated image under the manuscript repo, and rewrite the manuscript at the target figure location when supported
  - for staged workflows: run the packaged stage workers, validate with `scripts/validate_run.py`, and summarize with `scripts/summarize_run.py`
- Output:
  - chart-choice-only: a shortlist with caveats, family, and backend recommendation
  - implementation task: a JSON object with `mode`, `task`, `status`, `run_dir`, `artifacts`, and `notes`
  - persistent artifacts rooted under `runs/paper-visualizer/<run_id>/` when a workflow or generator-backed path is executed

## Preconditions

- Verify the current working directory is writable before doing workflow work.
- Verify these packaged assets exist before proceeding:
  - `scripts/manuscript_figure.py`
  - `agents/`
  - `references/`
  - `scripts/resolve_paperbanana.py`
  - `scripts/render_plot.py`
  - `scripts/compute_overall.py`
  - `scripts/validate_run.py`
  - `scripts/summarize_run.py`
- Verify these shared charting assets exist before route-only or generator-backed work:
  - `../data-to-viz/references/chart-selection-guide.md`
  - `../data-to-viz/references/chart-caveats.md`
  - `../data-to-viz/scripts/tabular_inventory.py`
  - `../data-to-viz/scripts/npy_inventory.py`
- Treat `scripts/render_plot.py` as a trusted-code boundary because it executes Python plot code. Only run it on code generated inside the current workflow or on user-confirmed trusted input.
- Keep all persistent artifacts inside `runs/paper-visualizer/<run_id>/` under the current working directory.

## Core Rules

- Use chart family before backend.
- Use the packaged stage workers in `agents/` rather than inventing new stage names.
- Pass explicit task labels (`diagram` or `plot`) to every stage worker.
- Prefer file-based handoff over conversational summaries. If a stage result matters downstream, write it into the run directory before invoking the next stage.
- For a simple manuscript request, prefer:
  `uv run --script skills/paper-visualizer/scripts/manuscript_figure.py <manuscript> --figure <N>`
- Before returning success for a staged workflow, run `scripts/validate_run.py` and then `scripts/summarize_run.py`.
- Do not advertise `refine`; this skill does not implement a general refine/image-edit backend.

## Mode-Specific Notes

- `full`:
  - resolve the benchmark dataset with `scripts/resolve_paperbanana.py`
  - run retrieval when available, then planner, optional stylist, render, optional critic loop, validate, summarize
- `planner_critic`:
  - run planner, render it, then run the critic loop with `source=planner`
- `planner_stylist`:
  - run planner, stylist, and render both outputs
- `planner`:
  - run planner and render it
- `vanilla`:
  - shortest generation path; write artifacts under `candidates/candidate_00/`
- `polish`:
  - write `polish/suggestions.txt` first; skip regeneration if suggestions are `No changes needed`
- `evaluate`:
  - score only `faithfulness`, `conciseness`, `readability`, and `aesthetics`
  - compute `overall` with `scripts/compute_overall.py`
- `chunked_extraction`:
  - write canonical output to `chunked_extraction/final_inputs.json`

## Resources

- `../data-to-viz/references/chart-selection-guide.md`
  Use for chart-family routing before backend selection.
- `../data-to-viz/references/chart-caveats.md`
  Use for global caveat filtering and chart rejection rules.
- `../data-to-viz/references/static-figure-guidelines.md`
  Use for publication-first figure constraints on shared-generator paths.
- `../data-to-viz/scripts/*.py`
  Shared chart generator helpers retained as implementation assets after skill merge.
- `references/workflows.md`
  Use for mode-by-mode sequencing, support levels, artifact layout, and stop conditions.
- `references/agent-map.md`
  Use for stage selection, actual data keys, and file naming conventions.
- `references/evaluation.md`
  Use for evaluation dimensions and deterministic overall scoring.
- `assets/style_guides/*.md`
  Packaged style guides for stylist, polish, and manuscript runs.
- `scripts/manuscript_figure.py`
  End-to-end manuscript figure generation.
- `scripts/render_plot.py`
  Plot rendering semantics.
- `scripts/resolve_paperbanana.py`
  Dataset resolution and fallback behavior.
- `scripts/compute_overall.py`
  Deterministic overall aggregation.
- `scripts/validate_run.py`
  Run before returning success.
- `scripts/summarize_run.py`
  Canonical JSON summary for staged workflows.

## Example

User request:

```text
paper-visualizer main.tex 绘制 图 1
```

Expected behavior:

- write a run directory such as `runs/paper-visualizer/<run_id>/`
- create `workflow_spec.json`
- run `uv run --script skills/paper-visualizer/scripts/manuscript_figure.py main.tex --figure 1`
- save the generated image locally and update the manuscript when the format supports insertion
