# HoloViz Ecosystem Map

Use this file to decide how deep into the HoloViz stack to go.

In this repo, HoloViz is treated as a family-level compatibility backend, mainly for map and dense-data paths. It is no longer the top-level organizing principle for the entire `data-to-viz` skill.

## hvPlot

- The default entrypoint for interactive exploration on pandas/xarray-like data.
- Best when the user wants quick interactivity with minimal code and already has tabular data.
- Good first stop for line, scatter, hist, heatmap, and simple map exploration.

## HoloViews

- The compositional layer for overlays, layouts, linked views, and richer object semantics.
- Choose it when the task is about combining elements, not just making a single plot.
- Relevant concepts: overlays (`*`), layouts (`+`), linked brushing, declarative elements.

## GeoViews

- Geographic extension on top of HoloViews with CRS-aware elements and Cartopy-based projections.
- Choose it when the plot needs projections, map tiles, coastlines, borders, or geographic data types.

## Panel

- App and dashboard layer for turning plots into shareable browser experiences.
- Choose it when the deliverable is a dashboard, report app, or multi-view HTML artifact.
- Use `save(..., resources=INLINE)` for portable static HTML when live Python callbacks are unnecessary.
- Inline Panel/Bokeh assets do not automatically inline tile servers; map tiles may still need network access unless you replace or cache them.

## Datashader

- Large-data rendering pipeline for preserving distribution when direct browser plotting breaks down.
- Choose it when you would otherwise subsample or alpha-blend millions of points or curves.
- Best paired with HoloViews/hvPlot for interactive zooming into large datasets.
- If you route to Datashader-backed rendering, make sure `datashader` is explicitly installed in the runtime used to execute the generated script.

## Decision rules

- One plot, quick interaction: start with `hvplot`.
- Several linked or overlaid views: step up to `HoloViews`.
- Map semantics or projections: step up to `GeoViews`.
- Dashboard or app deliverable: wrap with `Panel`.
- Browser cannot faithfully display the data volume: add `Datashader`.
