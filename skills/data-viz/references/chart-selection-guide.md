# Chart Selection Guide

Use this guide before choosing a plotting library. Start from what the visualization needs to prove, then route to a chart family.

## Comparison / ranking

Use when the task is "who is bigger", "what is the order", or "how do groups compare".

- Default charts:
  - bar or lollipop for a small number of categories
  - dot plot / Cleveland plot when precise comparison matters
  - grouped interval plots when uncertainty matters
- Common libraries:
  - seaborn / plotnine / ggplot2 for tidy tables
  - matplotlib for heavily customized layouts

## Distribution

Use when the task is about spread, skew, tails, or differences between groups.

- Default charts:
  - histogram or density for one variable
  - box / violin / beeswarm combinations for grouped distributions
  - ridgeline only when many grouped densities must be compared in one frame
- Caveat:
  - do not use violin alone when sample size is tiny and individual points matter

## Correlation

Use when the task is about the relationship between two or more numeric variables.

- Default charts:
  - scatter for moderate sample sizes
  - hexbin / 2D density for dense point clouds
  - correlogram or pair plot for many numeric variables
- Escalate:
  - use Datashader when direct scatter no longer shows the distribution faithfully

## Evolution

Use when the x-axis is ordered in time or step sequence.

- Default charts:
  - line plot
  - connected scatter when the path between paired numeric states matters
  - area / stacked area only when cumulative composition is the point
- Caveat:
  - ordered x-values should usually be connected, not shown as isolated dots

## Part-to-whole

Use when the question is about composition of a total.

- Default charts:
  - stacked bars for exact comparison
  - treemap or sunburst for hierarchical composition
- Avoid:
  - pie and doughnut unless the number of parts is tiny and precise comparison is unimportant

## Map

Use when location is part of the message.

- Default charts:
  - point map for event or station locations
  - choropleth for normalized areal values
  - hexbin / density map for heavy point concentration
- Escalate:
  - use GeoViews when CRS, projections, tiles, or geographic overlays matter

## Flow

Use when the message is about movement, connection, or transition.

- Default charts:
  - Sankey for aggregated flows
  - arc/chord only when structure is more important than exact reading
  - network layouts for relational structure

## Multivariate

Use when several variables must be shown together and no simpler single-family chart is enough.

- Default charts:
  - heatmap
  - small multiples
  - parallel coordinates only when the audience can tolerate a more technical chart

## Decision shortcut

1. What is the main analytical claim?
2. Which chart family best answers that claim?
3. Which caveats could make that chart misleading?
4. Which library best fits the data shape and deliverable?
