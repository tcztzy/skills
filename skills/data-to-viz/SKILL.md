---
name: data-to-viz
description: Route visualization tasks by Data-to-Viz chart family instead of choosing a library first. Use when prompts mention chart selection, chart critique, publication figures, dashboards, maps, large-data plotting, or specific backends such as matplotlib, seaborn, ggplot2, plotnine, hvplot, geoviews, or datashader and you still need to choose the correct chart family; output either a chart shortlist with caveats or a route to the matching `data-to-viz-*` family skill plus the shared execution path.
compatibility: Shared generator-backed paths use uv and Python 3.12+. Static Python families use pandas/numpy/matplotlib/seaborn/plotnine as needed. R-backed family paths use Rscript with ggplot2 + readr + jsonlite. Map and large-data compatibility paths use hvplot + holoviews + panel + bokeh, with geoviews + cartopy for geo mode and datashader for dense rendering.
metadata:
  short_name: data-to-viz
  aliases: data-viz,data viz,data to viz,chart chooser,chart critique,matplotlib,seaborn,plotnine,ggplot2,hvplot,holoviews,geoviews,datashader
---

# Data-to-Viz Router

Use this skill as the single entrypoint for visualization work. Do not choose a plotting library first. First decide whether the task is chart-choice-only, then map it to a Data-to-Viz chart family, run the caveat filter, and only then route to the matching family skill.

## Routing Contract

- `data-to-viz` is the router, not the implementation endpoint.
- Backend names such as `matplotlib`, `seaborn`, `ggplot2`, `plotnine`, `hvplot`, `geoviews`, or `datashader` still hit this router first.
- The router's job is to hand off to one of these family skills:
  - `data-to-viz-comparison-ranking`
  - `data-to-viz-distribution`
  - `data-to-viz-correlation`
  - `data-to-viz-evolution`
  - `data-to-viz-part-to-whole`
  - `data-to-viz-map`
  - `data-to-viz-flow`
  - `data-to-viz-multivariate`

## Workflow

1. Classify the request
   - If the user says "帮我选图", "which chart", "is this chart good", or "critique this viz", do chart-choice-first routing. Do not generate code unless explicitly asked.
   - If the user names a backend, treat that as a preference signal only. Still map the task to a chart family first.
   - If the user wants a full deliverable, choose a family first and then let the family skill decide whether there is a generator-backed path or a doc-only backend recommendation.

2. Map to a Data-to-Viz family
   - Use `references/chart-selection-guide.md`.
   - Route by analytical claim, not by software:
     - who is bigger / what is the order -> `data-to-viz-comparison-ranking`
     - spread / skew / tails / grouped distributions -> `data-to-viz-distribution`
     - relationship between numeric variables -> `data-to-viz-correlation`
     - ordered time / step / trajectory -> `data-to-viz-evolution`
     - composition of a whole -> `data-to-viz-part-to-whole`
     - location is part of the message -> `data-to-viz-map`
     - movement / connection / transition -> `data-to-viz-flow`
     - several variables shown together with no simpler family -> `data-to-viz-multivariate`

3. Run the global caveat filter
   - Use `references/chart-caveats.md` before committing to a family-specific chart form.
   - Reject pie/doughnut when ordered comparison matters.
   - Reject radar/spider when exact comparison or axis order matters.
   - Reject dual-axis unless the task is critique.
   - For dense scatter or line clouds, treat Datashader as a rendering fallback inside the relevant family, not as a new family.

4. Hand off to the family skill
   - Use the family skill for:
     - family-specific chart forms
     - publication-first backend matrix
     - generator-backed execution path when available
     - doc-only backend recommendations when v1 does not provide codegen

5. Reuse shared assets
   - Shared scripts stay here:
     - `scripts/tabular_inventory.py`
     - `scripts/npy_inventory.py`
     - `scripts/gen_matplotlib_skeleton.py`
     - `scripts/gen_seaborn_skeleton.py`
     - `scripts/gen_plotnine_skeleton.py`
     - `scripts/gen_ggplot2_skeleton.py`
     - `scripts/gen_holoviz_skeleton.py`
   - Shared references stay here:
     - `references/static-figure-guidelines.md`
     - `references/safeguards.md`
     - `references/viz-manifest.md`
     - `references/backend-organization.md`
     - `references/official-sources.md`

6. Keep the output contract narrow
   - Chart-choice-only task: return a shortlist with caveats and the target family skill.
   - Implementation task with generator-backed family path: return or run the shared generator path chosen by the family skill.
   - Implementation task without v1 generator-backed path: return the target family, recommended backend, and the reason that the path is doc-only in v1.

## Shared Execution Rules

- `viz_manifest.json` is still written only when the generated plotting/app script is executed with `--manifest`.
- Shared generator-backed coverage in v1:
  - comparison/ranking -> `seaborn`, `plotnine`, `ggplot2`, `matplotlib`
  - distribution -> `seaborn`, `plotnine`, `ggplot2`
  - correlation -> `seaborn`, `plotnine`, `matplotlib`
  - evolution -> `seaborn`, `plotnine`, `ggplot2`, `matplotlib`
  - map -> `GeoViews/Datashader` compatibility path
  - multivariate -> minimal `matplotlib` heatmap path
- `part-to-whole` and `flow` are doc-first in v1.

## Example

**Input**

- "比较 6 个模型在 3 个数据集上的准确率和方差，最好是论文图。"

**Actions**

1. Recognize this as a comparison/ranking task, not a backend selection task.
2. Use `references/chart-selection-guide.md` and `references/chart-caveats.md`.
3. Route to `data-to-viz-comparison-ranking`.
4. Let that family skill choose among grouped bars, Cleveland dots, or grouped interval plots and then decide whether to use `seaborn`, `plotnine`, `ggplot2`, or `matplotlib`.

**Output**

- A comparison/ranking shortlist or a route to the generator-backed family workflow.
