# Chart Caveats

This file condenses the anti-pattern guidance from Data-to-Viz caveat pages and related large-data guidance.

## Reject by default

### Pie / doughnut

- Humans compare aligned lengths better than angles.
- Do not use pie or doughnut when the viewer must rank categories or compare small differences.
- Better defaults: bar, lollipop, or treemap.

### Radar / spider

- Axis order changes the shape and can change the story.
- Precise comparison is poor, especially across many variables or multiple series.
- Better defaults: grouped bar, heatmap, small multiples, or parallel coordinates for expert audiences.

### Dual-axis

- Scaling choices can manufacture or hide relationships.
- Use aligned small multiples, indexing/normalization, or separate panels instead.

## Escalate instead of forcing a bad static chart

### Overplotting

- Dense scatterplots or trajectory clouds should become hexbin, 2D density, or Datashader-backed views.

### Rainbow palette

- Avoid rainbow for ordered numeric data; use perceptually ordered palettes instead.

### Radial bar / circular bar

- Radial bar charts distort perceived length because outer bars look larger.
- Use ordinary bars unless the circular layout itself carries meaning.

### Calculation errors

- Percentages in part-to-whole charts must sum correctly.
- Labels, annotations, and area encodings must agree with the underlying numbers.

### Excess clutter

- Remove decoration that does not carry information: 3D effects, heavy borders, shadows, ornamental gradients.

### Ordered x-axis as disconnected dots

- When x is ordered in time or sequence, lines usually communicate the pattern more clearly than scattered points alone.

## Escalation triggers

- Need hover, zoom, linked filtering, or widgets: move to HoloViz.
- Need projections, tiles, or CRS-aware maps: move to GeoViews.
- Need to render full distributions from millions of points or curves: move to Datashader.
