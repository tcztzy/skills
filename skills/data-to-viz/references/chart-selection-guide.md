# Chart Selection Guide

Use this guide inside `paper-visualizer` before choosing a backend. Start from the analytical claim, map to a chart family, then continue within the matching `paper-visualizer` route.

| Analytical claim | Family | Route inside skill | Typical chart forms |
| --- | --- | --- | --- |
| Who is bigger? What is the order? | comparison/ranking | `paper-visualizer` -> comparison/ranking | bar, lollipop, Cleveland dot, grouped interval |
| How is it distributed? | distribution | `paper-visualizer` -> distribution | histogram, density, box, violin, beeswarm, ridgeline |
| How do numeric variables relate? | correlation | `paper-visualizer` -> correlation | scatter, hexbin, 2D density, correlation matrix |
| How does it change over time or step order? | evolution | `paper-visualizer` -> evolution | line, connected scatter, area / stacked area |
| How is a whole composed? | part-to-whole | `paper-visualizer` -> part-to-whole | stacked bar, treemap, sunburst |
| How does geography matter? | map | `paper-visualizer` -> map | point map, choropleth, density / hex map |
| How do things move or connect? | flow | `paper-visualizer` -> flow | Sankey, alluvial, chord, network flow |
| How do several variables need to be shown together? | multivariate | `paper-visualizer` -> multivariate | heatmap, small multiples, pair plot, parallel coordinates |

## Router rules

1. Determine the analytical claim before looking at software names.
2. If several families are plausible, list the top 2-3 candidates and explain the tradeoff in one sentence each.
3. Run `chart-caveats.md` before locking the family.
4. Let the matching `paper-visualizer` route choose the backend.

## Special routing notes

- Dense scatter or line clouds stay in the correlation or evolution family; Datashader is a rendering fallback, not a new family.
- Geo tasks stay in the map family even when the preferred implementation is `GeoViews`.
- Backend names in the prompt are preference signals only. They do not override family mapping.
