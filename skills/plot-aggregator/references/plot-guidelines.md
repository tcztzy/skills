# Plot Guidelines (Paper-Ready)

This file distills stable guidance from official Matplotlib, ggplot2, Nature, and PLOS documentation. It was refreshed on 2026-03-17. If a target venue is known, the venue's current author instructions override this baseline.

## Grounding and correctness

- Plot only from real data files. Do not invent summary numbers or redraw curves by hand.
- Every plotted transformation must be reproducible from a script and recorded in `plot_manifest.json`.
- If a panel uses statistical summaries, record the aggregation rule, error bar definition, and exact source files.

## Cross-venue baseline

- Prefer vector outputs for graphs, line art, and mixed text/line figures. Nature explicitly asks for editable vector artwork for graphs and says not to rasterize line art or text.
- Keep a raster preview only as a companion export. Nature asks for images at `300 dpi` or higher; PLOS asks for `300-600 dpi`.
- Design around common journal widths. Nature's guidance is roughly `89-90 mm` for single-column figures and `180-183 mm` for double-column figures, with text around `5-7 pt` at final size.
- Use one sans-serif family consistently across the paper figures. Nature recommends Arial or Helvetica.
- Avoid red-green contrasts and avoid rainbow colour scales.
- Define error bars explicitly and report exact `n` values in the manuscript or figure legend.

## Matplotlib defaults

- Use `savefig()` with explicit filenames and formats. The official API supports `png`, `pdf`, `svg`, and more, and `bbox_inches="tight"` is the normal way to trim whitespace.
- Prefer perceptually uniform continuous colormaps such as `viridis`, `cividis`, `magma`, `inferno`, or `plasma`.
- Use `constrained_layout=True` or another explicit layout strategy before export so legends and colour bars remain inside the page budget.
- For Chinese labels, prefer an installed CJK font fallback and set `axes.unicode_minus = False` if the selected font does not reliably cover the Unicode minus glyph.
- When you need editable vector text, set `pdf.fonttype = 42` and `ps.fonttype = 42`.

## ggplot2 defaults

- Use `ggsave()` with explicit `width`, `height`, `units`, and `dpi` for raster previews. `ggsave()` infers the device from the filename extension, so saving both `.pdf` and `.png` is straightforward.
- Use `labs()` so axes and legends show full variable names; use `caption` for source notes or caveats.
- Use a complete theme such as `theme_bw()` or `theme_minimal()` as a starting point, then refine with `theme()` for consistent fonts, spacing, grids, and legends.
- Prefer `scale_*_viridis_*()` for continuous or ordered colour scales. For discrete palettes, use `scale_*_brewer()` or a manually chosen colour-blind-safe palette.

## Figure QA checklist

- Labels: axis labels, legend titles, units, and panel tags are present and consistent.
- Layout: no clipped labels, overlapping legends, or excess whitespace.
- Colour: continuous scales are perceptually ordered; grouped palettes remain distinguishable in grayscale when possible.
- Statistics: error bars and `n` are defined somewhere the reader can find quickly.
- Export: vector `pdf` exists for line art; raster previews are at an explicit dpi.

## When to escalate to venue-specific rules

- The paper has a named venue or journal.
- The figure contains microscopy, photographic, or layered raster content.
- The figure uses many small panels and is close to the venue's minimum text size.
- The venue specifies exact file types, line widths, panel label rules, or colour-space rules.
