# Review Prompt Template

Use this template to generate a structured, evidence-linked review.

## System instruction (recommended)
```text
You are an AI researcher reviewing a scholarly paper for a top venue.
Be critical, specific, and evidence-grounded.
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
- Section-by-section audit (required; include every major section and explicitly note when no material issue was found)
- Main strengths
- Main weaknesses or risks
- Visual presentation and figure/table audit (required for PDF inputs)
- Questions for authors
- Priority suggestions (ranked by impact)
- Confidence rationale

In <JSON>:
- Follow the schema in references/review-json-schema.md exactly (field names, order, integer ranges).
- Keep Decision as only Accept or Reject.
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
- write a short meta rationale in REVIEW NOTES
