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
First, evaluate these dimensions from the paper text:
- problem formulation
- literature positioning
- methodology/design
- data/source quality
- analysis and claim-evidence alignment
- results presentation and interpretation
- writing/presentation quality
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
- Questions for authors
- Priority suggestions (ranked by impact)
- Confidence rationale

In <JSON>:
- Follow the schema in references/review-json-schema.md exactly (field names, order, integer ranges).
- Keep Decision as only Accept or Reject.
- Ensure scores are consistent with evidence in REVIEW NOTES.

Here is the paper text:
```
{PASTE_PAPER_TEXT_HERE}
```
~~~

## Optional: ensemble
Generate 3-5 independent reviews (different seeds/temps), then aggregate:
- average numeric fields (round to nearest int)
- union strengths/weaknesses/questions (deduplicate)
- write a short meta rationale in REVIEW NOTES
