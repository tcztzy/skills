---
name: data-to-viz-distribution
description: Design distribution visuals such as histograms, density curves, box plots, violin plots, beeswarms, and ridgelines. Use after `data-to-viz` routes a task to distribution or when prompts ask about spread, skew, tails, outliers, or grouped distributions; output a distribution-chart shortlist or a backend recommendation plus the shared generator path.
metadata:
  short_name: viz-dist
  aliases: histogram,density,box plot,violin,ridgeline,distribution
---

# Distribution

Use this skill when the main question is about spread, skew, tails, outliers, or how distributions differ across groups.

## Default chart forms

- histogram or density for a single variable
- box + points or violin + points for grouped distributions
- beeswarm when sample size is small enough that individual points matter
- ridgeline only when many grouped densities must share one frame

## Avoid or downgrade

- violin alone when sample size is tiny
- smoothed density when the data is too sparse to support it
- ridgeline when exact cross-group comparison matters more than compactness

## Publication-first backend matrix

### Generator-backed in v1

- `seaborn`: histograms, KDEs, box/violin, grouped distribution quickstarts
- `plotnine`: grammar-first distribution plots in Python
- `ggplot2`: R-first publication workflow

### Doc-first in v1

- `Observable Plot`: compact statistical JS visuals
- `Vega-Lite`: clean vector distribution charts
- `PGFPlots`: LaTeX-native histogram / density / box-plot workflows

## Shared execution path

1. Run `../data-to-viz/scripts/tabular_inventory.py`.
2. Prefer `seaborn`, `plotnine`, or `ggplot2` for the first runnable implementation.
3. Use the matching shared generator script and then execute the generated script with `--manifest` when you need artifacts.

## Example

**Input**

- "看一下不同模型 loss 的分布，最好能看尾部和离群点。"

**Actions**

1. Pick the distribution family.
2. Prefer histogram + box/points or violin + points.
3. Route to `seaborn`, `plotnine`, or `ggplot2`.

**Output**

- A distribution-chart shortlist or a generator-backed path for a publication-first backend.
