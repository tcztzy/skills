# Safeguards

## Safety posture

- Do not delete inputs.
- Do not fabricate values, smooth data without disclosure, or hide preprocessing in labels.
- Do not recommend a chart type without checking known caveats first.
- Do not use network access from generated plotting scripts.

## Output hygiene

- Only clean `figures/` or `apps/` when an explicit clean flag is provided.
- If cleaning is enabled, only remove output directories rooted under the current working directory.
- Write provenance to `viz_manifest.json` for every generated output bundle.

## Interactive export caveats

- Prefer standalone HTML exports where feasible.
- If an interaction requires a live Python process, say so explicitly in the generated script comments or manifest notes.
- Tile-backed maps may need network access at view time even if the export itself is local.

## Large-data caveats

- If downsampling or alpha-blending is the only way the chart becomes readable, prefer Datashader.
- Keep the full dataset as the source of truth; do not silently sample unless the user asks for it.
