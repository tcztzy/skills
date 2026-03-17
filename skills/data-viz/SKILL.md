---
name: data-viz
description: Route data-visualization tasks from chart choice to implementation across matplotlib, seaborn, plotnine, ggplot2, hvPlot, HoloViews, GeoViews, Panel, and Datashader. Use when prompts mention chart selection, chart critique, publication figures, dashboards, maps, gallery-style reproduction, or large-data plotting; output either a chart shortlist with caveats or runnable script(s)/app(s), and write `viz_manifest.json` when the generated script is executed with `--manifest`.
compatibility: Requires uv and Python 3.12+. Static Python workflows need pandas/numpy/matplotlib/seaborn/plotnine as appropriate. R workflows need Rscript with ggplot2 + readr + jsonlite. Interactive workflows need hvplot + holoviews + panel + bokeh; geo mode additionally needs geoviews + cartopy; large-data HoloViz rendering additionally needs datashader.
metadata:
  short_name: dataviz
  aliases: data to viz,chart chooser,chart critique,matplotlib,seaborn,plotnine,ggplot2,holoviz,hvplot,holoviews,geoviews,panel,datashader
---

# Data Viz

Use this skill as the top-level entrypoint for visualization work. Do not jump straight to a plotting library. First classify the task, then choose a chart family, run caveat checks, and only then choose the implementation stack.

This skill covers five output modes:

- chart selection and critique without code
- static publication or report graphics
- gallery-style recipe adaptation
- interactive exploration and dashboards
- geospatial or large-data visualization

## Routing Tree

1. Classify the request
   - If the user says "帮我选图", "which chart", "is this chart good", or "critique this viz", do chart selection and caveat review first. Do not write code unless explicitly asked.
   - If the user wants a figure for a paper, report, or slide deck, route to a static workflow.
   - If the user wants "something like this example" from a gallery, route through the recipe index and adapt the closest example instead of inventing a new chart from scratch.
   - If the user wants hover, zoom, linked views, widgets, filters, dashboards, or map tiles, route to HoloViz.
   - If the data is too dense for ordinary scatter/line plots, route to a HoloViz workflow with Datashader. Keep the task mode as `explore`, `geo`, or `app`; treat large-data as a rendering hint, not a separate mode.

2. Choose the chart family before the library
   - Use `references/chart-selection-guide.md` to map the question to one of the Data-to-Viz families: comparison/ranking, distribution, correlation, evolution, part-to-whole, map, flow, or multivariate.
   - If several families are plausible, list the top 2-3 candidates and explain the tradeoff in one sentence each.

3. Run the caveat filter
   - Use `references/chart-caveats.md` before committing to a chart type.
   - Explicitly reject pie/doughnut when ordered comparison is important.
   - Explicitly reject radar/spider when axis ordering changes the message or exact comparison matters.
   - Explicitly reject dual-axis unless the task is critique and you are explaining why it is misleading.
   - For dense scatter or line clouds, escalate to density/hexbin/Datashader instead of adding alpha blindly.

4. Choose the implementation stack
   - `matplotlib`: arrays, images, heatmaps, simulation traces, fine publication control, mixed raster/vector export.
   - `seaborn`: quick statistical summaries from tidy tables; a good default for report-grade Python charts with less boilerplate.
   - `plotnine`: grammar-of-graphics in Python when the user wants ggplot-like structure but the project is Python-first.
   - `ggplot2`: grammar-of-graphics in R when the project or example is R-first.
   - `hvplot`: default HoloViz entrypoint for interactive exploration on pandas/xarray-like data.
   - `HoloViews`: use when overlays, layouts, linked plots, or compositional objects are central.
   - `GeoViews`: use when CRS, projections, map tiles, or geographic semantics matter.
   - `Panel`: use when the deliverable is a dashboard or app.
   - `Datashader`: use when point/line density is too high for direct rendering.

5. Inventory the data
   - Arrays:
     ```bash
     UV_CACHE_DIR=/tmp/uv-cache XDG_CACHE_HOME=/tmp uv run --with numpy -s scripts/npy_inventory.py --dir /path/to/run --out inventory.json
     ```
   - Tabular data:
     ```bash
     UV_CACHE_DIR=/tmp/uv-cache XDG_CACHE_HOME=/tmp uv run --with pandas -s scripts/tabular_inventory.py --dir /path/to/run --out tabular_inventory.json
     ```
   - `tabular_inventory.py` is the routing input for static Python/R workflows and HoloViz workflows. It detects likely `x`, `y`, `group`, `facet`, `lat`, and `lon` columns.

6. Generate a runnable skeleton only after the route is stable
   - Matplotlib:
     ```bash
     UV_CACHE_DIR=/tmp/uv-cache XDG_CACHE_HOME=/tmp uv run --with numpy,matplotlib -s scripts/gen_matplotlib_skeleton.py --inventory inventory.json --out auto_data_viz.py --figures-dir figures
     ```
   - Seaborn:
     ```bash
     UV_CACHE_DIR=/tmp/uv-cache XDG_CACHE_HOME=/tmp uv run --with pandas,seaborn,matplotlib -s scripts/gen_seaborn_skeleton.py --inventory tabular_inventory.json --out auto_data_viz.py --figures-dir figures
     ```
   - Plotnine:
     ```bash
     UV_CACHE_DIR=/tmp/uv-cache XDG_CACHE_HOME=/tmp uv run --with pandas,plotnine -s scripts/gen_plotnine_skeleton.py --inventory tabular_inventory.json --out auto_data_viz.py --figures-dir figures
     ```
   - ggplot2:
     ```bash
     UV_CACHE_DIR=/tmp/uv-cache XDG_CACHE_HOME=/tmp uv run -s scripts/gen_ggplot2_skeleton.py --inventory tabular_inventory.json --out auto_data_viz.R --figures-dir figures
     ```
   - HoloViz explore:
     ```bash
     UV_CACHE_DIR=/tmp/uv-cache XDG_CACHE_HOME=/tmp uv run --with pandas,hvplot,holoviews,panel,bokeh -s scripts/gen_holoviz_skeleton.py --inventory tabular_inventory.json --mode explore --out auto_data_viz.py --apps-dir apps
     ```
   - HoloViz geo:
     ```bash
     UV_CACHE_DIR=/tmp/uv-cache XDG_CACHE_HOME=/tmp uv run --with pandas,hvplot,holoviews,panel,bokeh,geoviews,cartopy -s scripts/gen_holoviz_skeleton.py --inventory tabular_inventory.json --mode geo --out auto_data_viz.py --apps-dir apps
     ```
   - HoloViz app:
     ```bash
     UV_CACHE_DIR=/tmp/uv-cache XDG_CACHE_HOME=/tmp uv run --with pandas,hvplot,holoviews,panel,bokeh -s scripts/gen_holoviz_skeleton.py --inventory tabular_inventory.json --mode app --out auto_data_viz.py --apps-dir apps
     ```
   - If `tabular_inventory.json` reports `large_dataset_hint: true`, add `datashader` to the HoloViz runtime used to execute the generated script.

7. Execute the generated script to produce artifacts
   - Static matplotlib example:
     ```bash
     UV_CACHE_DIR=/tmp/uv-cache XDG_CACHE_HOME=/tmp uv run --with numpy,matplotlib -s auto_data_viz.py --figures-dir figures --manifest viz_manifest.json
     ```
   - Static seaborn example:
     ```bash
     UV_CACHE_DIR=/tmp/uv-cache XDG_CACHE_HOME=/tmp uv run --with pandas,seaborn,matplotlib -s auto_data_viz.py --figures-dir figures --manifest viz_manifest.json
     ```
   - Interactive HoloViz example:
     ```bash
     UV_CACHE_DIR=/tmp/uv-cache XDG_CACHE_HOME=/tmp uv run --with pandas,hvplot,holoviews,panel,bokeh -s auto_data_viz.py --mode explore --apps-dir apps --manifest viz_manifest.json
     ```
   - For geo execution, add `geoviews,cartopy`.
   - For large-data HoloViz execution, add `datashader`.

8. Finalize and validate
   - If you only scaffolded, return runnable script(s) and explain what command will produce `figures/`, `apps/`, and `viz_manifest.json`.
   - If the user asked for a full deliverable, run the generated script, then return the written `figures/` or `apps/` bundle and `viz_manifest.json`.
   - Use `references/static-figure-guidelines.md` for static export quality.
   - Use `references/viz-manifest.md` for provenance and output metadata.

## Output Contract

- If the task is chart choice or chart critique:
  - return a chart shortlist with caveats
  - do not generate code unless the user asks for it
- If the task is static graphics:
  - always output runnable script(s)
  - if you execute the generated script, output `figures/`
  - write `viz_manifest.json` when you execute the generated script with `--manifest`
- If the task is interactive or dashboarding:
  - always output runnable script(s)
  - if you execute the generated script, output `apps/`
  - write `viz_manifest.json` when you execute the generated script with `--manifest`

## Safeguards

- Never fabricate numbers or redraw data by hand.
- Never recommend a chart type before checking caveats.
- Do not keep exploratory quicklooks in a final paper figure folder.
- Do not overwrite existing `figures/` or `apps/` unless the user explicitly asks for cleaning or passes `--clean`.
- For interactive exports, prefer self-contained HTML where feasible and note when live Python callbacks are required.
- For geo exports, do not claim the artifact is fully offline if it still depends on external tile servers at view time.

## Examples

### Example A: chart choice only

**Input**

- "帮我选图，不要写代码。我要比较 6 个模型在 3 个数据集上的准确率和方差。"

**Actions**

1. Route to chart selection, not script generation.
2. Map the task to `comparison/ranking`.
3. Reject pie/radar/dual-axis.
4. Recommend grouped bar, Cleveland dot/lollipop, and faceted interval plot.

**Output**

- A shortlist of chart families plus one-sentence caveats for each.

### Example B: static Python report figure

**Input**

- `metrics.csv` with `model`, `dataset`, `seed`, `accuracy`

**Actions**

1. Run `scripts/tabular_inventory.py`
2. Route to `seaborn` or `plotnine`
3. Generate the skeleton
4. Run the generated script with `--manifest viz_manifest.json`
5. Replace quicklook defaults with a claim-driven grouped summary before publication

### Example C: gallery-style adaptation

**Input**

- "我想做一个 python graph gallery 那种 ridgeline"

**Actions**

1. Use `references/gallery-recipe-index.md`
2. Match the request to distribution / ridgeline
3. Route to `seaborn` unless the user requests another library
4. Adapt the recipe to the actual dataset instead of copying decorative choices blindly

### Example D: interactive geo exploration

**Input**

- `stations.csv` with `longitude`, `latitude`, `city`, `count`

**Actions**

1. Run `scripts/tabular_inventory.py`
2. Detect `lat/lon`
3. Route to HoloViz geo mode
4. Generate `auto_data_viz.py` with `--mode geo`
5. Run the generated script with `geoviews,cartopy` and `--manifest viz_manifest.json`
6. Export an HTML app and note whether map tiles still require network access

## FAQ

### Q: Matplotlib 中文显示成方块、乱码，或者出现 `Glyph ... missing` 怎么办？

**A**

- The generated matplotlib skeleton auto-detects common installed Chinese fonts and uses them as `font.sans-serif` fallbacks.
- It also sets `axes.unicode_minus = False` to avoid Unicode minus issues.
- If glyphs are still missing, install `Noto Sans CJK SC` or `Source Han Sans SC` and rerun the script.

### Q: 为什么 PNG 正常，但 PDF 里的中文字体或文字轮廓不稳定？

**A**

- Static Python skeletons use `pdf.fonttype = 42` and `ps.fonttype = 42`.
- If the venue requires a specific typeface, explicitly move that font to the front of the fallback list in the generated script.
- If the font is not installed system-wide, register it in Python with `matplotlib.font_manager.addfont()`.

### Q: 什么时候不要用 pie、radar、dual-axis？

**A**

- Avoid pie/doughnut when readers need ordered comparison or small differences.
- Avoid radar/spider when axis order changes interpretation or exact comparison matters.
- Avoid dual-axis for explanatory graphics; use aligned small multiples or normalized comparisons instead.
- See `references/chart-caveats.md` before approving any of these.

### Q: 什么时候要升级到 HoloViz / GeoViews？

**A**

- Upgrade to HoloViz when hover, zoom, linked views, browser interactivity, or a dashboard deliverable is part of the requirement.
- Upgrade to GeoViews when coordinates, tiles, CRS, projections, or geographic overlays matter.
- Upgrade to Datashader when you are subsampling or alpha-blending millions of points just to make a scatter or trajectory readable.

### Q: seaborn、plotnine、ggplot2 怎么选？

**A**

- Pick `seaborn` for fast Python reporting charts with sensible defaults.
- Pick `plotnine` if the user wants grammar-of-graphics structure but the project stays in Python.
- Pick `ggplot2` if the project is already in R or the reference example is R-first.

## References

- Chart selection guide: `references/chart-selection-guide.md`
- Chart caveats: `references/chart-caveats.md`
- Gallery recipe index: `references/gallery-recipe-index.md`
- HoloViz ecosystem map: `references/holoviz-ecosystem.md`
- Static figure guidance: `references/static-figure-guidelines.md`
- Official and primary sources: `references/official-sources.md`
- Manifest format: `references/viz-manifest.md`
- Manifest schema: `references/viz_manifest.schema.json`
- Safeguards: `references/safeguards.md`
