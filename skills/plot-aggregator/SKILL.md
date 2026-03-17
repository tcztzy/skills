---
name: plot-aggregator
description: Create publication-ready scientific figures from experiment outputs using matplotlib or ggplot2. Use when prompts mention paper figures, final plots, multi-panel figure assembly, run-result aggregation, or plot manifests; output reproducible plot script(s), a figures/ directory, and a source-grounded manifest.
compatibility: Requires uv and Python 3.12+. Matplotlib workflow needs numpy + matplotlib. ggplot2 workflow needs Rscript with ggplot2 + readr + jsonlite. Network is optional and only needed when a venue-specific figure spec must be looked up.
metadata:
  short_name: plot-agg
  aliases: paper plots,figure pipeline,matplotlib,ggplot2
---

# Paper Plot Aggregator

Use this skill to turn experiment outputs into a small, reproducible figure pipeline for a paper. The skill supports two plotting systems:

- `matplotlib` for array-centric data (`.npy`, matrices, heatmaps, simulation traces) or when the repo is already Python-first.
- `ggplot2` for tidy tabular data (`.csv`, `.tsv`, `.json`, `.jsonl`) or when the paper workflow is already R-first.

If the project already has one plotting stack, stay in that stack unless the data shape strongly argues otherwise.

## Workflow

1. Confirm the figure target
   - If the user names a venue, use that venue's official author instructions.
   - If no venue is named, use the cross-venue baseline in `references/plot-guidelines.md`.
   - Before plotting, write a figure plan with one row per intended panel: `figure_id`, `claim`, `source files`, `plot type`, `x/y/color mapping`, `summary statistic`, `error bar definition`, and `export formats`.

2. Choose the plotting system
   - Choose `matplotlib` when inputs are mostly arrays, images, or precomputed tensors, or when you need fine manual control over axes, insets, and mixed raster/vector export.
   - Choose `ggplot2` when inputs are tidy tables and the core task is grouping, faceting, statistical summaries, or publication-ready categorical comparisons.
   - For mixed projects, it is acceptable to use both, but keep each figure family in one system and record the chosen system in the manifest.

3. Inventory the data
   - Array inventory:
     ```bash
     UV_CACHE_DIR=/tmp/uv-cache XDG_CACHE_HOME=/tmp uv run --with numpy -s scripts/npy_inventory.py --dir /path/to/run --out inventory.json
     ```
   - Tabular inventory:
     ```bash
     UV_CACHE_DIR=/tmp/uv-cache XDG_CACHE_HOME=/tmp uv run --with pandas -s scripts/tabular_inventory.py --dir /path/to/run --out tabular_inventory.json
     ```
   - If the run folder contains both array and tabular data, run both inventories and decide figure-by-figure which source is authoritative.

4. Generate a plotting skeleton
   - Matplotlib skeleton:
     ```bash
     UV_CACHE_DIR=/tmp/uv-cache XDG_CACHE_HOME=/tmp uv run --with numpy,matplotlib -s scripts/gen_aggregator_skeleton.py --inventory inventory.json --out auto_plot_aggregator.py --figures-dir figures
     ```
   - ggplot2 skeleton:
     ```bash
     UV_CACHE_DIR=/tmp/uv-cache XDG_CACHE_HOME=/tmp uv run -s scripts/gen_ggplot2_skeleton.py --inventory tabular_inventory.json --out auto_plot_aggregator.R --figures-dir figures
     ```
   - The generated skeleton is only a starting point. Replace generic quicklooks with claim-driven panels before calling the figure final.

5. Run and refine the generated script
   - Matplotlib:
     ```bash
     UV_CACHE_DIR=/tmp/uv-cache XDG_CACHE_HOME=/tmp uv run --with numpy,matplotlib -s auto_plot_aggregator.py --figures-dir figures --manifest plot_manifest.json
     ```
   - ggplot2:
     ```bash
     Rscript auto_plot_aggregator.R --figures-dir figures --manifest plot_manifest.json
     ```
   - Edit the generated script until each saved figure matches a concrete sentence in the paper. Do not keep exploratory plots in the final `figures/` folder.

6. Apply paper-ready defaults
   - Prefer vector export for line art and graphs (`.pdf`, optionally `.svg`). Keep a `.png` preview for review workflows.
   - Use a single sans-serif family across the paper figures unless the venue says otherwise.
   - Use perceptually uniform colour scales for continuous values and colour-blind-safe discrete palettes for grouped data.
   - State what error bars mean and where `n` comes from.
   - Keep font sizes, stroke widths, axis labeling, and panel tags consistent across all figures.

7. Validate before calling the figure done
   - Check the final figure size at the likely publication width, not just on a large monitor.
   - Check grayscale readability for heatmaps and dense scatter plots.
   - Confirm legends do not overlap data and that abbreviations are expanded in labels or captions.
   - Confirm every figure in `figures/` is backed by real files listed in the manifest.
   - If the venue has stricter specs than the baseline here, the venue wins.

## Output Contract

- `figures/` with paper-candidate exports
- `auto_plot_aggregator.py` and/or `auto_plot_aggregator.R`
- `plot_manifest.json` aligned with `references/plot-manifest.md`

## Safeguards

- Read-only on inputs; write only to the requested output locations.
- Do not fabricate numbers, smooth traces without disclosure, or relabel axes to hide preprocessing.
- Do not overwrite an existing `figures/` directory unless the user explicitly asks for cleaning or passes `--clean`.

## Examples

### Example A: `matplotlib` for training curves and heatmaps

**Input**

- A run directory containing `train_loss.npy`, `val_loss.npy`, and `attention_map.npy`

**Actions**

1. Run `scripts/npy_inventory.py`
2. Generate `auto_plot_aggregator.py`
3. Replace generic quicklooks with:
   - one line plot for train/validation loss
   - one heatmap with a perceptually uniform colormap
4. Export `pdf + png`
5. Write `plot_manifest.json`

**Output**

- `figures/fig-01-loss.pdf`
- `figures/fig-01-loss.png`
- `figures/fig-02-attention.pdf`
- `plot_manifest.json`

### Example B: `ggplot2` for ablations and grouped summaries

**Input**

- `metrics.csv` with columns `model`, `seed`, `task`, `accuracy`

**Actions**

1. Run `scripts/tabular_inventory.py`
2. Generate `auto_plot_aggregator.R`
3. Replace generic quicklooks with a grouped summary figure:
   - aggregate over `seed`
   - show mean with explicit error bars
   - facet by `task` if needed
4. Export `pdf + png`
5. Record source files, stat notes, and caption suggestions in the manifest

**Output**

- `figures/fig-03-ablation.pdf`
- `figures/fig-03-ablation.png`
- `plot_manifest.json`

## FAQ

### Q: Matplotlib 中文显示成方块、乱码，或者出现 `Glyph ... missing` 怎么办？

**A**

- 本 skill 生成的 `matplotlib` 骨架现在会自动探测本机已安装的常见中文字体，并优先使用它们作为 `font.sans-serif` fallback。
- 默认候选包括 `PingFang SC`、`Hiragino Sans GB`、`STHeiti`、`Microsoft YaHei`、`SimHei`、`Noto Sans CJK SC`、`Source Han Sans SC`、`WenQuanYi Zen Hei`。
- 骨架还会设置 `axes.unicode_minus = False`，避免负号因为字体不含 `U+2212` 而显示异常。
- 如果仍然缺字，先安装 `Noto Sans CJK SC` 或 `Source Han Sans SC`，再重新运行脚本。

### Q: 为什么 PNG 正常，但 PDF 里的中文字体不对或不稳定？

**A**

- 骨架默认设置了 `pdf.fonttype = 42` 和 `ps.fonttype = 42`，尽量保持矢量导出时的文本兼容性。
- 如果投稿方要求特定字体，或者自动探测选中的字体不符合版式要求，就在生成后的脚本里显式把目标字体放到 `font.sans-serif` 列表最前面。
- 如果系统没有安装目标字体，可在生成后的脚本里用 `matplotlib.font_manager.addfont()` 注册本地字体文件，再设置对应 family。

### Q: ggplot2 也会自动解决中文字体吗？

**A**

- 目前自动中文字体探测只加在 `matplotlib` 骨架里。
- 对 `ggplot2`，请在生成后的脚本里显式设置 `theme(text = element_text(family = "..."))`，并使用系统里已经安装的中文字体。

## References

- Paper-ready plot guidance: `references/plot-guidelines.md`
- Official source links: `references/official-sources.md`
- Plot manifest format: `references/plot-manifest.md`
- Plot manifest schema: `references/plot_manifest.schema.json`
- Safeguards: `references/safeguards.md`
