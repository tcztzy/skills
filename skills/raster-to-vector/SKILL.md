---
name: raster-to-vector
description: "Convert raster architecture diagrams, screenshots, flowcharts, UI diagrams, scanned figures, charts, and rendered PDF pages into presentation-ready editable SVG. Use PP-OCR text geometry, local segmentation, CV primitives, optional image understanding, agent-provided icon replacements, and per-element fallback tracing; never ship a final full-canvas embedded PNG as vectorization."
---

# Raster To Vector

Goal: editable SVG for slides: selectable text, editable boxes/arrows, grouped icons, and obvious unresolved items.

No bundled icons. The scripts never fetch icon replacements. If replacement icons are needed, the agent may obtain suitable SVGs separately and point `descriptions.json` entries at those files.

Forbidden final state: full source PNG embedded as meaningful output.

## One Shot

```bash
cd ./scripts
uv run python -m r2v run input.png --out-dir r2v-run --debug
```

## Step Debug

```bash
cd ./scripts
uv run python -m r2v ocr input.png --out-dir r2v-run

uv run python -m r2v segment input.png --out-dir r2v-run

uv run python -m r2v primitives input.png --out-dir r2v-run

uv run python -m r2v describe --run-dir r2v-run

uv run python -m r2v vectorize --run-dir r2v-run

uv run python -m r2v compose --run-dir r2v-run

uv run python -m r2v audit --run-dir r2v-run
```

## Pipeline

1. `ocr`: PP-OCRv5 on original image. Save polygons, bbox, confidence, overlay.
2. `segment`: local segmentation on original image. Do not use OCR-masked image.
3. `primitives`: CV containers/connectors/icon candidates on original image. OCR boxes are conflict hints only.
4. `describe`: create crop + nearby-text manifest for agent/image understanding. The agent labels each icon proposal and chooses an action in `descriptions.json`.
5. `vectorize`: apply agent decisions from `descriptions.json`; use agent-provided SVG paths, ignore false positives, or fallback trace isolated unresolved crops.
6. `compose`: render `scene.json` to editable SVG.
7. `audit`: count SVG elements and flag unresolved/full-canvas raster issues.

## Artifacts

- `source.png`
- `ocr.json`, `ocr.raw.json`, `ocr-boxes.json`, `ocr-boxes.csv`, `ocr-boxes.png`
- `sam.json`, optional `masks/`
- `primitives.json`, `primitives.png`
- `describe-input.json`, editable `descriptions.json`
- `icon-trace.json`, fallback traced `icons/`
- `scene.json`, `final.svg`, `audit.json`, `report.json`

## Rules

OCR happens early, but does not erase image before segmentation.

Masking text is off by default. Use `--mask-preview` only for debug preview, not for SAM input.

VTracer is last fallback. Prefer source-matched SVG supplied by the agent in `descriptions.json`. If traced crop looks irregular, keep item unresolved instead of pretending it is clean.

Natural-language image understanding helps label icons and group elements. It must not override geometry; coordinates come from OCR/SAM/CV.

`scene.json` is the semantic edit protocol. Text elements carry `text`; container elements may carry `label` inferred from enclosed OCR text; icon elements carry `label` from SAM prompts or agent decisions. Connectors currently carry geometry and arrow direction only.

For each icon proposal, the agent edits `descriptions.json`:

- `label`: semantic name, e.g. `gear`, `search`, `database`, `AWS Lambda`
- `action`: `replace`, `trace`, `ignore`, or `unresolved`
- `svg`: path to an agent-provided SVG, required for `replace`

If the user explicitly asks to replace icons, the agent may fetch/download/create SVGs outside these scripts, save them under the run directory, then edit `descriptions.json`:

```json
{"id":"icon-0003","label":"database cylinder","action":"replace","svg":"icons/database.svg"}
```

Do not assume the raster image used any particular external icon set.

Final response must state SVG path, mode, unresolved count/items, and whether segmentation ran.
