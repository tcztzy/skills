---
name: data-to-viz-correlation
description: Design correlation visuals such as scatter plots, hexbins, 2D density views, and dense-point compatibility paths. Use after `data-to-viz` routes a task to correlation or when prompts ask about relationships between numeric variables, scatter plots, dense point clouds, or regression-style comparison; output a correlation-chart shortlist or a backend recommendation plus the shared generator path.
metadata:
  short_name: viz-corr
  aliases: scatter,hexbin,2d density,correlation plot
---

# Correlation

Use this skill when the message is about the relationship between numeric variables rather than ranking, time order, or pure distribution.

## Default chart forms

- scatter for moderate sample sizes
- hexbin or 2D density for dense point clouds
- correlation matrix only when the task is genuinely many-to-many

## Avoid or downgrade

- alpha-only scatter when density is high enough that the distribution disappears
- regression line as the sole message when uncertainty or subgroup structure is the real point

## Publication-first backend matrix

### Generator-backed in v1

- `seaborn`: scatter and grouped numeric relationships from tidy tables
- `plotnine`: grammar-first scatter workflows
- `matplotlib`: custom scatter / hexbin / annotation control

### Compatibility path

- `hvPlot` / `HoloViews` / `Datashader`: use the shared `gen_holoviz_skeleton.py --mode explore` path when the dataset is too dense for direct scatter rendering

### Doc-first in v1

- `Vega-Lite`
- `Observable Plot`
- `PGFPlots`

## Shared execution path

1. Run `../data-to-viz/scripts/tabular_inventory.py`.
2. Use a static generator-backed backend first unless `large_dataset_hint` forces a dense-rendering path.
3. For dense data, stay in the correlation family but switch rendering to the shared HoloViz compatibility path with `datashader`.

## Example

**Input**

- "Show the relationship between two metrics. There are so many points that a regular scatter plot becomes a blur."

**Actions**

1. Pick the correlation family.
2. Reject plain alpha-only scatter.
3. Use a hexbin / density concept or the Datashader-compatible HoloViz path.

**Output**

- A correlation shortlist or a route to static or dense-rendering generator-backed execution.
