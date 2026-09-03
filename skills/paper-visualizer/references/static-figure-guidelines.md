# Static Figure Guidelines

This file covers static outputs for papers, reports, and slide decks. If a target venue is named, the venue's current author instructions override this baseline.

## Core defaults

- Use vector export for line art and text-heavy figures when possible.
- Keep a PNG preview at an explicit dpi for review workflows.
- Design around final display size instead of whatever looks good on a large monitor.
- Use accessible palettes and avoid rainbow scales for ordered numeric data.
- State what error bars mean and how `n` was computed.

## Python static stacks

- `matplotlib` for full control, arrays, annotations, insets, and mixed raster/vector layouts.
- `seaborn` for report-grade statistical summaries on tidy data.
- `plotnine` when the user wants grammar-of-graphics structure in Python.

## R static stack

- `ggplot2` is the first-class R static stack in this skill.

## Publication-specific notes

- For multilingual labels, set fonts explicitly and validate the final PDF.
- For dense scatterplots, switch to 2D density, hexbin, or Datashader-backed workflows instead of forcing alpha to do all the work.
- For multi-panel figures, keep axes, fonts, stroke widths, and legend treatment consistent across panels.
