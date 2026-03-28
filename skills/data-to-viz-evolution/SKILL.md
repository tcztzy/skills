---
name: data-to-viz-evolution
description: Design evolution visuals such as line charts, connected trajectories, and ordered-step summaries. Use after `data-to-viz` routes a task to evolution or when prompts ask how something changes over time, epoch, step, iteration, or sequence order; output an evolution-chart shortlist or a backend recommendation plus the shared generator path.
metadata:
  short_name: viz-evo
  aliases: line chart,time series,training curve,trajectory,evolution
---

# Evolution

Use this skill when the x-axis is ordered in time, epoch, step, iteration, or another meaningful sequence.

## Default chart forms

- line chart for time / epoch / step series
- connected scatter when the path between states matters
- area or stacked area only when cumulative composition is the point

## Avoid or downgrade

- isolated dots when ordered continuity is the message
- stacked area when the real question is rank order rather than cumulative share

## Publication-first backend matrix

### Generator-backed in v1

- `seaborn`
- `plotnine`
- `ggplot2`
- `matplotlib`

### Doc-first in v1

- `Vega-Lite`
- `Observable Plot`
- `PGFPlots`

## Shared execution path

1. Run `../data-to-viz/scripts/tabular_inventory.py`.
2. Prefer the static generator-backed backends above.
3. If line density becomes the problem, stay in this family and use the dense-rendering compatibility path from `../data-to-viz/scripts/gen_holoviz_skeleton.py`.

## Example

**Input**

- "Show how loss changes over epochs. I want a publication-style training curve."

**Actions**

1. Pick the evolution family.
2. Prefer a line-based chart.
3. Route to `seaborn`, `plotnine`, `ggplot2`, or `matplotlib`.

**Output**

- An evolution-chart shortlist or a generator-backed static implementation path.
