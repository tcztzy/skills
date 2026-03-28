# Agent Map

Treat the skill-packaged worker definitions and scripts below as the source of truth for stage behavior and deterministic local behavior.

## Stage Mapping

- `retriever`
  - Worker definition: `agents/retriever.toml`
  - Dataset resolver: `scripts/resolve_paperbanana.py`
  - Preferred dataset asset: `assets/paperbanana/PaperBananaBench/`
  - Output keys: `top10_references`, optional `retrieved_examples`
- `planner`
  - Worker definition: `agents/planner.toml`
  - Dataset resolver: `scripts/resolve_paperbanana.py`
  - Preferred dataset asset: `assets/paperbanana/PaperBananaBench/`
  - Output key: `target_<task>_desc0`
- `stylist`
  - Worker definition: `agents/stylist.toml`
  - Style guide asset: `assets/style_guides/neurips2025_<task>_style_guide.md`
  - Input key: `target_<task>_desc0`
  - Output key: `target_<task>_stylist_desc0`
- `visualizer`
  - Worker definition: `agents/visualizer.toml`
  - Helper reference: `scripts/render_plot.py`
  - Output keys:
    - diagram: `<desc_key>_image`
    - plot: `<desc_key>_code`, `<desc_key>_image`
- `critic`
  - Worker definition: `agents/critic.toml`
  - Input selector: `source=planner|stylist` for round 0
  - Output keys: `target_<task>_critic_suggestions<N>`, `target_<task>_critic_desc<N>`
- `vanilla`
  - Worker definition: `agents/vanilla.toml`
  - Helper reference: `scripts/render_plot.py`
  - Output key: `vanilla_<task>_image`
- `polish`
  - Worker definition: `agents/polish.toml`
  - Helper references: `scripts/resolve_paperbanana.py`, `assets/style_guides/neurips2025_<task>_style_guide.md`
  - Output key: `suggestions_<task>`
- `polish_regen`
  - Worker definition: `agents/polish-regen.toml`
  - Output key: `polished_<task>_image`
- `eval_diagram`
  - Worker definition: `agents/eval-diagram.toml`
  - Overall helper: `scripts/compute_overall.py`
- `eval_plot`
  - Worker definition: `agents/eval-plot.toml`
  - Overall helper: `scripts/compute_overall.py`
- `chunk_summarizer`
  - Skill-packaged helper only. No dedicated packaged runtime stage.
- `extraction_repair`
  - Skill-packaged helper only. No dedicated packaged runtime stage.

## Actual Data Expectations

- Shared input keys:
  - `content`
  - `visual_intent`
  - optional `additional_info.rounded_ratio`
- Retrieval:
  - `top10_references` is the normalized handoff used by the planner.
  - `retrieved_examples` matters for manual diagram retrieval because the planner prefers full examples when they are already provided.
  - Supported `retrieval_setting` values are `auto`, `manual`, `random`, and `none`.
- Critic loop:
  - The parent must set `current_critic_round`.
  - Round 0 uses planner or stylist outputs.
  - Rounds 1..N consume the previous critic description and image.
  - If a critic round returns `revised_description = "No changes needed."`, carry the previous description forward instead of storing a literal no-op string.
- Polish:
  - `path_to_gt_image` must be relative to the benchmark task subdirectory.
  - Suggestion output key: `suggestions_<task>`
  - Regeneration output key: `polished_<task>_image`
- Evaluation:
  - `eval_image_field` must name the image field being scored.

## Recommended Artifact Layout

All paths below are relative to the run directory rooted in the caller's working directory.

- `shared/retrieval.json`
- `candidates/candidate_00/planner.txt`
- `candidates/candidate_00/planner_image.*`
- `candidates/candidate_00/planner_code.py`
- `candidates/candidate_00/stylist.txt`
- `candidates/candidate_00/stylist_image.*`
- `candidates/candidate_00/stylist_code.py`
- `candidates/candidate_00/critic_00.json`
- `candidates/candidate_00/critic_00.txt`
- `candidates/candidate_00/critic_00_image.*`
- `candidates/candidate_00/critic_00_code.py`
- `candidates/candidate_00/vanilla_image.*`
- `polish/suggestions.txt`
- `polish/polished_image.*`
- `evaluation/faithfulness.json`
- `evaluation/conciseness.json`
- `evaluation/readability.json`
- `evaluation/aesthetics.json`
- `evaluation/overall.json`
- `chunked_extraction/final_inputs.json`

Notes:

- `planner_code.py`, `stylist_code.py`, and `critic_*_code.py` are plot-only artifacts.
- `vanilla_image.*` is the only stable vanilla output in this skill. Do not assume a vanilla code artifact exists.
- Prefer stable basenames and let the extension follow the actual MIME type when writing image payloads to disk.
- If the workflow asks for canonical output, call `scripts/summarize_run.py`.
