---
name: data-to-viz-comparison-ranking
description: Design comparison and ranking visuals such as bars, lollipops, Cleveland dots, grouped intervals, and leaderboard-style summaries. Use after `data-to-viz` routes a task to comparison/ranking or when prompts ask who is bigger, what is the order, grouped bar chart, lollipop chart, or benchmark comparison; output a comparison-chart shortlist or a backend recommendation plus the shared generator path.
metadata:
  short_name: viz-compare
  aliases: bar chart,lollipop,cleveland dot,ranking,leaderboard
---

# Comparison / Ranking

Use this skill after the router has decided that the main question is comparative: who wins, what is the order, how do groups compare, or how should a benchmark table become a chart.

## Default chart forms

- grouped bar when the audience expects a familiar category comparison
- Cleveland dot or lollipop when exact comparison matters
- grouped interval / error bar summary when uncertainty matters
- sorted horizontal bar when rank order is the message

## Avoid or downgrade

- pie/doughnut when precise ordering matters
- radar/spider for model or benchmark comparison
- stacked bars when the primary message is rank order rather than composition

## Publication-first backend matrix

### Generator-backed in v1

- `seaborn`: tidy grouped comparisons with low boilerplate
- `plotnine`: ggplot-like structure in Python
- `ggplot2`: R-first reporting or publication workflow
- `matplotlib`: custom annotation, manual layout, or mixed raster/vector control

### Doc-first in v1

- `Vega-Lite`: paper-first browser-native vector charts
- `Observable Plot`: concise statistical JS charts
- `PGFPlots`: LaTeX-native comparison figures

## Shared execution path

1. Run the shared inventory script at `../data-to-viz/scripts/tabular_inventory.py`.
2. Choose one of the generator-backed backends above.
3. Generate a skeleton with the shared script:
   - `../data-to-viz/scripts/gen_seaborn_skeleton.py`
   - `../data-to-viz/scripts/gen_plotnine_skeleton.py`
   - `../data-to-viz/scripts/gen_ggplot2_skeleton.py`
   - `../data-to-viz/scripts/gen_matplotlib_skeleton.py` when the source is array-like or heavily custom
4. Execute the generated script with `--manifest viz_manifest.json` when a full deliverable is required.

## Example

**Input**

- "比较 6 个模型在 3 个数据集上的准确率和方差，想要论文图。"

**Actions**

1. Pick comparison/ranking as the family.
2. Prefer grouped interval or Cleveland dot over radar/pie.
3. Use `seaborn`, `plotnine`, or `ggplot2` for the first runnable skeleton.

**Output**

- A shortlist of comparison chart forms or a shared generator-backed path for one of the publication-first backends.
