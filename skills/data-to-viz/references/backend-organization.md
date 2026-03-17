# Backend Organization

This skill family is organized family-first, not backend-first.

## Core rule

- First choose the Data-to-Viz family.
- Then, inside that family, choose the backend.
- Do not split the top-level skill tree by `matplotlib` / `seaborn` / `ggplot2` / `TikZ` / `GeoViews`.

## Why

- Families capture the user’s analytical intent.
- Backends are implementation options inside a family.
- The same backend can serve several families.
- The same family can have different best backends depending on deliverable, publication constraints, and runtime environment.

## Publication-first backend scope in v1

### First-class generator-backed backends

- `matplotlib`
- `seaborn`
- `plotnine`
- `ggplot2`

### Paper-first doc-level backends

- `Vega-Lite`
- `Observable Plot`
- `TikZ`
- `PGFPlots`

### Compatibility / specialized paths

- `GeoViews`
- `Datashader`
- `hvPlot`
- `HoloViews`
- `Panel`

These remain valid, but only as family-specific implementation options, mainly for map and dense-data compatibility paths.

## v1 boundaries

- `part-to-whole` and `flow` are doc-first; they do not promise code generation for every backend.
- `TikZ` / `PGFPlots` are family-level backends, not a standalone top-level skill.
- `Plotly`, `ECharts`, `Bokeh`, and dashboard-first tooling are out of the v1 core path.
