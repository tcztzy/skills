---
name: data-to-viz-multivariate
description: Design multivariate visuals such as heatmaps, small multiples, pair plots, correlograms, and other many-variable layouts. Use after `data-to-viz` routes a task to multivariate or when prompts ask to show several variables together and no simpler chart family is enough; output a multivariate-chart shortlist or a backend recommendation plus the shared minimal generator path.
metadata:
  short_name: viz-multi
  aliases: heatmap,pair plot,correlogram,small multiples,parallel coordinates
---

# Multivariate

Use this skill when several variables must be shown together and no simpler single-family chart can carry the message.

## Default chart forms

- heatmap for matrix-like structure
- small multiples for repeated univariate or bivariate views
- pair plot or correlogram for many numeric variables
- parallel coordinates only when the audience can tolerate a more technical chart

## Avoid or downgrade

- pair plots when the variable count is so large that the display stops being readable
- parallel coordinates as a default chart for non-technical audiences

## Publication-first backend matrix

### Minimal generator-backed path in v1

- `matplotlib`: matrix-like heatmap and image-style multivariate views via the shared array workflow

### Doc-first in v1

- `seaborn`: pair plot / clustermap / correlogram style workflows
- `Observable Plot`
- `PGFPlots`

## Shared execution path

1. If the source is matrix-like or already array-based, run `../data-to-viz/scripts/npy_inventory.py`.
2. Use `../data-to-viz/scripts/gen_matplotlib_skeleton.py` for the first heatmap-style runnable path.
3. If the task is truly about pair plots or correlograms on tabular numeric data, stay doc-first in v1 and recommend the backend rather than claiming a dedicated generator path.

## Example

**Input**

- "I have a correlation matrix and want to turn it into a paper-style heatmap."

**Actions**

1. Pick the multivariate family.
2. Prefer a heatmap over a generic many-panel layout.
3. Use the shared `matplotlib` generator-backed path.

**Output**

- A multivariate shortlist or the minimal generator-backed heatmap path.
