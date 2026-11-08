# Review JSON Schema (NeurIPS-style)

The canonical machine-validatable contract is `review.schema.json`. This file is its human-readable field-order and scoring summary; if they ever disagree, fix this summary rather than overriding the JSON schema.

Produce valid JSON with the following fields **in this order**:
- `Summary` (string)
- `Strengths` (list of strings)
- `Weaknesses` (list of strings)
- `Originality` (int 1-4)
- `Quality` (int 1-4)
- `Clarity` (int 1-4)
- `Significance` (int 1-4)
- `Questions` (list of strings)
- `Limitations` (list of strings)
- `Ethical Concerns` (boolean)
- `Soundness` (int 1-4)
- `Presentation` (int 1-4)
- `Contribution` (int 1-4)
- `Overall` (int 1-10)
- `Confidence` (int 1-5)
- `Decision` (string; must be `Accept` or `Reject`)

## Rating scales
- 1-4: low/poor to very high/excellent (use integers only)
- Overall 1-10 (use integers only):
  - 1 unintelligible; 2 catastrophic violation of established fact or basic logic; 3 fundamentally unsound; 4 major repair; 5 borderline below venue standard
  - 6 minimum publishable at the target venue; 7 solid/typical published; 8 strong; 9 exceptional/editor-highlight worthy; 10 top-end intrinsic contribution and evidence with a coherent claim-to-evidence chain, decisive validation, boundary awareness, and no central unresolved weakness
- Apply `../SKILL.md` with the selected same-type published papers as `>= 6` anchors and selected, fully reviewed cover exemplars as `10` anchors. Use the same evidence criteria for controls and manuscript; retain demonstrated errors and report any calibration conflict rather than forcing a score by identity.
- With the binary schema, `Overall` 1-5 maps to `Reject` and 6-10 maps to `Accept`. Put revision advice in the narrative.
- Apply the complete definitions and evidence requirements in `../SKILL.md` and any matching `references/<issn>.md`; do not score by criticism count.
- Confidence 1-5: low to absolute

## Guardrails
- Keep the review specific to the provided paper text.
- Do not invent results, claims, or citations not present in the paper.
- Avoid long verbatim quotes.
- For list fields such as `Strengths`, `Weaknesses`, `Questions`, and `Limitations`, append concrete locators whenever the item refers to a specific passage or visual element.
