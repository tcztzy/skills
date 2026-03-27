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
- Cite page numbers for layout and figure/table issues when possible.

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
