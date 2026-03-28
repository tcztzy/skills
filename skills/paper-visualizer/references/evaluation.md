# Evaluation Notes

## Model-Evaluated Dimensions

- `faithfulness`
- `conciseness`
- `readability`
- `aesthetics`

In this skill, these four dimensions are the only ones that should consume a model call.

## Per-Dimension Output Contract

Write each result as JSON with:

- `comparison_reasoning`
- `winner`

For these four dimensions, valid `winner` values are:

- `Human`
- `Model`
- `Both are good`
- `Both are bad`

`Tie` is not a normal per-dimension outcome in this skill's per-dimension logic.

## Diagram Evaluation

- Use `eval_diagram`.
- For `faithfulness` and `conciseness`, pass the methodology section, caption, human image, and model image.
- For `readability` and `aesthetics`, the visual comparison still needs the caption for context, but the emphasis is on the images.

## Plot Evaluation

- Use `eval_plot`.
- For `faithfulness` and `conciseness`, pass the raw data, visual intent, human image, and model image.
- For `readability` and `aesthetics`, keep the same image pair and supporting plot intent.
- For plot `faithfulness`, the valid winners are only `Human` and `Both are good`, because the human plot is the ground-truth rendering of the provided raw data.

## Deterministic Overall Rule

Do not spend a fifth model call on `overall`. Compute it locally with `scripts/compute_overall.py`.

Tier helper:

- If both outcomes are the same clear winner, return that winner.
- If both outcomes are the same neutral value (`Both are good` or `Both are bad`), return `Tie`.
- If one outcome is `Model` and the other is neutral, return `Model`.
- If one outcome is `Human` and the other is neutral, return `Human`.
- All other mixes return `Tie`.

Overall rule:

1. Compute Tier 1 from `faithfulness` and `readability`.
2. If Tier 1 returns `Model` or `Human`, stop there.
3. Otherwise compute Tier 2 from `conciseness` and `aesthetics`.
4. Use the Tier 2 outcome as `overall`.

## Overall Output Convention

Write `evaluation/overall.json` as:

```json
{
  "comparison_reasoning": "Rule-based calculation: ...",
  "winner": "Model"
}
```

For `overall`, valid winners are:

- `Human`
- `Model`
- `Tie`
