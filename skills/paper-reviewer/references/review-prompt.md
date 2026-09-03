# Review Prompt Template

Use this template to generate a structured, evidence-linked review.

## System instruction (recommended)
```text
You are an AI researcher reviewing a scholarly paper against its stated target venue or, if none is stated, general field norms.
Be critical, specific, and evidence-grounded.
Calibrate severity and the overall score against recent comparable published work; do not equate the number of criticisms with rejection.
Do not hallucinate claims, citations, or results.
```

## User prompt
~~~text
If the input is a PDF, use rendered page images as the primary evidence source.
Inspect the page images directly before scoring, including:
- page layout and whitespace balance
- typography, contrast, and skimmability
- figure, table, and chart readability
- caption alignment, panel labels, and callout consistency
- overflow, clipping, crowding, or other production issues

Use extracted text only as a secondary aid for dense sections, equations, or precise wording checks.

Before scoring, use `coverage_map.json` and `close_reading_audit.jsonl` as the coverage anchor. Review every audit unit in reading order. For prose-heavy sections, read sentence by sentence. For equation-, figure-, or table-heavy passages, review claim by claim and cross-check the referenced visual or formula directly.

For every row in `close_reading_audit.jsonl`, fill `review_status` with `ok`, `issue`, `question`, or `na` and add a short `review_note`. When a section has no material issue after close reading, state that explicitly in the ledger and in the notes instead of omitting the section.

Run the validator before producing a final verdict:
```bash
uv run scripts/close_reading_audit.py validate --audit close_reading_audit.jsonl
```
If validation fails, complete the missing rows first. If the review cannot be completed in the current turn, report the exact uncovered unit/page/section ranges instead of presenting a complete review.

Before scoring, identify the target journal, ISSN, and article type when available. Load `references/<issn>.md` and the matching public calibration cache under `~/.paper-reviewer/<issn>/` when present. State which positive controls were used. If no journal-specific evidence is available, say that the score uses the global rubric rather than silently assuming a top-venue bar. Record publication and official-cover status separately, but do not use either status in the dimension pass or provisional score.

First, evaluate these dimensions from the rendered paper pages and any supplemental text:
- problem formulation
- literature positioning
- methodology/design
- data/source quality
- analysis and claim-evidence alignment
- results presentation and interpretation
- writing/presentation quality
- visual presentation quality (layout, figures, tables, charts, captions)
- citation quality and balance

Then respond in this format:

REVIEW JSON:
```json
<JSON>
```

REVIEW NOTES:
- Overall verdict
- Calibration basis
- Section-by-section audit (required; include every major section and explicitly note when no material issue was found)
- Main strengths
- Main weaknesses or risks
- Visual presentation and figure/table audit (required for PDF inputs)
- Questions for authors
- Priority suggestions (ranked by impact)
- Confidence rationale

In <JSON>:
- Follow the canonical schema in `references/review.schema.json` exactly; use `references/review-json-schema.md` as its human-readable field-order summary.
- Keep Decision as only Accept or Reject.
- Apply the complete evidence-based `Overall` anchors in SKILL.md and any journal-specific calibration reference. In particular, 1 means the central paper cannot be understood because of language/notation/organization; 2 means a comprehensible paper has a catastrophic core violation of established fact or basic logic; 6 is the minimum publishable target-venue standard; and 10 requires top-end intrinsic contribution and evidence rather than a status label.
- Justify a provisional score without using publication or cover status. Then run the status post-validators from SKILL.md: a verified current, non-retracted published version judged against its publishing venue should finish at least 6, and a verified official cover article should finish at 10. A failure requires comparative re-review and an evidence-based correction; never cite the status itself as merit or clamp the score without locating overlooked intrinsic evidence.
- With binary decisions, map Overall 1-5 to Reject and 6-10 to Accept; put revision advice in REVIEW NOTES.
- Score fatality and claim impact, not criticism count. Optional analyses, ordinary limitations, and understandable language errors do not justify scores 1 or 2.
- Ensure scores are consistent with evidence in REVIEW NOTES.
- Cite page numbers for all findings when possible, not only layout and figure/table issues.
- Every strength, weakness, question, and limitation should include the narrowest reliable locator available, such as section heading plus page number, and preferably a paragraph/sentence cue or figure/table/equation identifier.
- Do not leave a major section unreported in REVIEW NOTES.
- Do not claim full close-reading coverage unless `close_reading_audit.py validate` passes.

Here is the review evidence (rendered page images first, then any supplemental extracted text):
```
{PASTE_REVIEW_EVIDENCE_HERE}
```
~~~

## Optional: ensemble
Generate 3-5 independent reviews (different seeds/temps), then aggregate:
- average numeric fields (round to nearest int)
- union strengths/weaknesses/questions (deduplicate)
- reapply the global and journal-specific status post-validators after aggregation
- write a short meta rationale in REVIEW NOTES
