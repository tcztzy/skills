# Chart Selection Guide

Use this guide in the router before choosing a backend. Start from the analytical claim, map to a Data-to-Viz family, then hand off to the matching family skill.

| Analytical claim | Family | Route to skill | Typical chart forms |
| --- | --- | --- | --- |
| Who is bigger? What is the order? | comparison/ranking | `data-to-viz-comparison-ranking` | bar, lollipop, Cleveland dot, grouped interval |
| How is it distributed? | distribution | `data-to-viz-distribution` | histogram, density, box, violin, beeswarm, ridgeline |
| How do numeric variables relate? | correlation | `data-to-viz-correlation` | scatter, hexbin, 2D density, correlation matrix |
| How does it change over time or step order? | evolution | `data-to-viz-evolution` | line, connected scatter, area / stacked area |
| How is a whole composed? | part-to-whole | `data-to-viz-part-to-whole` | stacked bar, treemap, sunburst |
| How does geography matter? | map | `data-to-viz-map` | point map, choropleth, density / hex map |
| How do things move or connect? | flow | `data-to-viz-flow` | Sankey, alluvial, chord, network flow |
| How do several variables need to be shown together? | multivariate | `data-to-viz-multivariate` | heatmap, small multiples, pair plot, parallel coordinates |

## Router rules

1. Determine the analytical claim before looking at software names.
2. If several families are plausible, list the top 2-3 candidates and explain the tradeoff in one sentence each.
3. Run `chart-caveats.md` before locking the family.
4. Let the family skill choose the backend.

## Special routing notes

- Dense scatter or line clouds stay in `data-to-viz-correlation` or `data-to-viz-evolution`; Datashader is a rendering fallback, not a new family.
- Geo tasks stay in `data-to-viz-map` even when the preferred implementation is `GeoViews`.
- Backend names in the prompt are preference signals only. They do not override family mapping.
