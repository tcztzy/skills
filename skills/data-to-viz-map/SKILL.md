---
name: data-to-viz-map
description: Design map visuals such as point maps, choropleths, and dense geographic views. Use after `data-to-viz` routes a task to map or when prompts ask for locations, stations, spatial density, choropleths, or geospatial overlays; output a map-chart shortlist or a backend recommendation plus the shared map generator path.
metadata:
  short_name: viz-map
  aliases: map,choropleth,point map,geo map,geospatial
---

# Map

Use this skill when geographic location is part of the message.

## Default chart forms

- point map for events or stations
- choropleth for normalized areal values
- density / hex map for heavy point concentration

## Avoid or downgrade

- raw counts on choropleths when the unit area differs substantially
- decorative tile layers when they do not help the message

## Publication-first backend matrix

### Generator-backed compatibility path in v1

- `GeoViews` / `hvPlot` / `Datashader`: use the shared `../data-to-viz/scripts/gen_holoviz_skeleton.py --mode geo` path

### Doc-first in v1

- `Vega-Lite`: paper-first browser-native static or exported maps
- `PGFPlots`: LaTeX-native publication maps when the workflow already lives inside TeX

## Shared execution path

1. Run `../data-to-viz/scripts/tabular_inventory.py`.
2. Confirm `likely_lat` and `likely_lon`.
3. Use `../data-to-viz/scripts/gen_holoviz_skeleton.py --mode geo`.
4. Add `datashader` when the point density is high enough that direct plotting fails.
5. When exporting HTML, state clearly whether tile-backed maps still require network access at view time.

## Example

**Input**

- "Plot station latitude, longitude, and traffic volume on an interactive map."

**Actions**

1. Pick the map family.
2. Prefer a point map or density map.
3. Use the shared GeoViews-compatible generator-backed path.

**Output**

- A map shortlist or a route to the shared geo generator path, with tile/network caveats when needed.
