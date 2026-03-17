---
name: data-to-viz-part-to-whole
description: Design part-to-whole visuals such as stacked bars, normalized bars, treemaps, and sunburst-like composition views. Use after `data-to-viz` routes a task to part-to-whole or when prompts ask how a total is composed; output a composition-chart shortlist and a backend recommendation. This family is doc-first in v1.
metadata:
  short_name: viz-part
  aliases: composition,stacked bar,part to whole,treemap,sunburst
---

# Part-to-Whole

Use this skill when the question is about composition of a whole rather than pure rank order.

## Default chart forms

- stacked bar for exact comparison across categories
- normalized stacked bar for share comparison
- treemap or sunburst for hierarchical composition

## Avoid or downgrade

- pie/doughnut unless the number of parts is tiny and exact reading is unimportant
- stacked bars when the real task is ranking rather than composition

## Publication-first backend matrix

### Doc-first in v1

- `ggplot2`: stacked bars and normalized composition views
- `Vega-Lite`: normalized stacked bars and simple composition views
- `PGFPlots`: LaTeX-native stacked bars for publication

### Not promised in v1

- no dedicated generator-backed code path
- hierarchical composition such as treemap or sunburst stays recommendation-level unless the user explicitly asks for a hand-authored backend implementation

## Shared workflow

1. Use the router’s caveat filter first.
2. If the requested chart is really about ranking, bounce back to `data-to-viz-comparison-ranking`.
3. Otherwise recommend the best backend and chart form, and only hand-author code if the user explicitly asks.

## Example

**Input**

- "我想看每个模型总错误里不同错误类型各占多少。"

**Actions**

1. Pick part-to-whole.
2. Prefer stacked or normalized stacked bars.
3. Recommend `ggplot2`, `Vega-Lite`, or `PGFPlots` depending on deliverable constraints.

**Output**

- A composition shortlist and a doc-first backend recommendation.
