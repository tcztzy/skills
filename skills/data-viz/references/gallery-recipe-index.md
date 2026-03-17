# Gallery Recipe Index

Use this file when the user asks for "something like this gallery example" or wants a recognizable chart pattern quickly.

## How to use the galleries

- Start from chart family, not from decorative style.
- Use Python Graph Gallery or R Graph Gallery as recipe inspiration, then adapt the example to the actual data schema, labels, and claims.
- Prefer gallery examples that already match the needed chart family and data shape.

## Python route

- Python Graph Gallery:
  [https://python-graph-gallery.com/](https://python-graph-gallery.com/)
- Good fits:
  - seaborn for quick statistical charts and styled report graphics
  - matplotlib when the gallery example needs manual annotation or custom axes work
  - plotnine when the requested style is grammar-of-graphics-like

## R route

- R Graph Gallery:
  [https://r-graph-gallery.com/](https://r-graph-gallery.com/)
- Good fits:
  - ggplot2 for most static chart families
  - ggplot2 extensions when the gallery example depends on a known extension such as GGally or ggExtra

## Family-to-recipe mapping

- Comparison / ranking:
  - grouped bar, lollipop, Cleveland dot, interval chart
- Distribution:
  - histogram, density, violin + swarm, ridgeline
- Correlation:
  - scatter, bubble, correlogram, hexbin, 2D density
- Evolution:
  - line, connected scatter, area, stacked area
- Part-to-whole:
  - treemap, stacked bar, sunburst
- Map:
  - point map, choropleth, bubble map, hexbin map
- Flow:
  - Sankey, arc diagram, chord diagram, network

## Adaptation checklist

1. Keep the chart family, not the original dataset.
2. Replace stylistic choices that hurt readability.
3. Recompute summaries and labels from the actual input files.
4. If the example depends on a package outside the chosen stack, call that out explicitly before copying the pattern.
