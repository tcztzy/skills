# Paper Visualizer Workflows

## Support Matrix

- Supported by this skill:
  - `full`
  - `planner_critic`
  - `planner_stylist`
  - `planner`
  - `vanilla`
  - `polish`
  - `evaluate`
- Experimental skill-only helpers:
  - `chunked_extraction`
- Unsupported in this skill:
  - `refine`

## Shared Rules

- Root all workflow artifacts at `runs/paper-visualizer/<run_id>/` relative to the current working directory.
- Always write `runs/paper-visualizer/<run_id>/workflow_spec.json`, even if it is a minimal manifest created by the orchestrator.
- Persist each stage output before invoking the next stage.
- Use the actual workflow data keys and stage outputs described in `references/agent-map.md`.
- Default to a single candidate directory: `candidates/candidate_00/`.
- Cap critic rounds at 3 because the current visualizer contract supports only rounds `0..2`.
- Provide `additional_info.rounded_ratio` for diagram and polish render paths, and preferably for vanilla diagram runs.
- For plot renders, save both code and image when the visualizer stage exposes both. Do not promise code artifacts for `vanilla`.
- Runtime stages load packaged style guides from `assets/style_guides/`.
- If a required style guide asset is missing or stale, refresh the matching file under `assets/style_guides/` before running stylist or polish.
- Resolve benchmark assets with the packaged `scripts/resolve_paperbanana.py` rather than assuming a fixed on-disk location.
  The resolver has only three priority levels: explicit `--dataset-dir`, packaged skill assets under `assets/paperbanana/`, then the current working directory target.

## Full

1. Resolve dataset access.
2. Run retriever once and write `shared/retrieval.json`.
3. Respect `retrieval_setting`:
   - `none` returns empty references.
   - `manual` uses `agent_selected_12.json` only for diagrams; plots degrade to no references.
   - `random` samples up to 10 ids from `ref.json`.
   - `auto` uses the normal retriever worker.
4. Under `candidates/candidate_00/`, write `planner.txt`.
5. Render planner output.
6. If stylist is enabled, write `stylist.txt` and render stylist output.
7. If critic is enabled, run the critic loop.
8. Round 0 uses `stylist` when stylist ran, otherwise `planner`.
9. Later rounds use the previous critic description and image.
10. If suggestions are exactly `No changes needed.`, reuse the previous image rather than rerendering.
11. If the critic also returns `revised_description = No changes needed.`, carry the previous description text forward.

## Planner Critic

1. Run planner.
2. Render planner output.
3. Run the critic loop with planner as round-0 source.

## Planner Stylist

1. Run planner.
2. Run stylist.
3. Render both planner and stylist outputs.

## Planner

1. Run planner.
2. Render planner output.

## Vanilla

1. Ensure `additional_info.rounded_ratio` is present for diagram runs.
2. Run the dedicated vanilla stage directly.
3. Write the rendered output under `candidates/candidate_00/`.
4. For plots, note that the stable vanilla stage returns the image only.

## Polish

1. Resolve `path_to_gt_image` against the benchmark task directory.
2. Load `assets/style_guides/neurips2025_<task>_style_guide.md`.
3. Run the suggestion stage and write `polish/suggestions.txt`.
4. If suggestions are `No changes needed`, stop and record that the original image was retained.
5. If the source image cannot be resolved or the suggestion list is empty, fail the run instead of regenerating blindly.
6. Otherwise run regeneration and write the polished image artifact under `polish/`.

## Evaluate

1. Run one comparison each for `faithfulness`, `conciseness`, `readability`, and `aesthetics`.
2. Write each output to `evaluation/<dimension>.json`.
3. Compute `evaluation/overall.json` locally using `scripts/compute_overall.py`.
4. Aggregate everything into the final summary.

## Chunked Extraction

1. Only run this when the user explicitly asks for it or already provides chunked inputs.
2. Create chunk files under `chunked_extraction/`.
3. Run one chunk summarizer per chunk.
4. Merge summaries.
5. Run the extraction repair worker.
6. Write `chunked_extraction/final_inputs.json` with `content` and `visual_intent` keys so the output can flow directly into the packaged generation agents.

## Refine

- Do not use `refine`. This skill does not provide a refine backend or edit-mode visualizer helper.
