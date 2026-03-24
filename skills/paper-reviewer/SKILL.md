---
name: paper-reviewer
description: Review academic papers (PDF/LaTeX/Markdown) with a ScholarEval-inspired dimension pass and produce both structured peer-review JSON (NeurIPS-style fields) and a concise human-readable review with prioritized, actionable feedback. Use for comprehensive, targeted, or comparative paper evaluation while keeping output bounded.
---

# Paper Reviewer

## Overview
Use JSON as the consistency anchor, not the only deliverable.

Default behavior is dual output:
- `review.json` for machine parsing and automation.
- A concise, human-readable review in the conversation.

If the user is doing pre-submission self-positioning and mainly wants to decide whether to go, kill, pivot, or reshape the story before formal review, route to `research-impact-strategy` instead.

## Workflow
1. Extract text from PDF (if needed).
   ~~~bash
   UV_CACHE_DIR=/tmp/uv-cache XDG_CACHE_HOME=/tmp uv run --with pypdf -s scripts/extract_pdf_text.py --pdf paper.pdf --out paper.txt
   ~~~
2. Set evaluation scope and context.
   - Scope: `comprehensive`, `targeted`, or `comparative`.
   - Stage: early draft vs. near-submission.
   - Venue or discipline constraints if provided.
3. Run a dimension pass before scoring.
   - Problem formulation and research questions.
   - Literature positioning and gap identification.
   - Methodology and design rigor.
   - Data/sources quality and transparency.
   - Analysis quality and claim-evidence alignment.
   - Results presentation and interpretation.
   - Writing and organization quality.
   - Citation quality and balance.
4. Map findings into NeurIPS-style review JSON using `references/review.schema.json` and `references/review-prompt.md`.
5. Synthesize a concise chat review aligned to JSON judgments.
6. Unless the user explicitly asks for JSON-only, provide both outputs in the same turn.

## Dimension Mapping Rules
- `Originality` and `Contribution`: novelty, gap clarity, and practical/theoretical contribution.
- `Quality` and `Soundness`: method/data/analysis rigor and limitations handling.
- `Clarity` and `Presentation`: writing quality, organization, and result communication.
- `Significance`: impact potential and relevance to venue scope.
- `Overall` and `Decision`: integrated judgment; do not contradict dimension-level evidence.

## Human-Readable Chat Format
Use short sections:
- Overall verdict
- Main strengths
- Main weaknesses or risks
- Questions for authors
- Priority suggestions (ranked by impact)
- Confidence

## Scoring Guidance
- For 1-4 fields: use integers only and justify with dimension evidence.
- `Overall` (1-10): reflect holistic merit, not a simple mean.
- `Confidence` (1-5): rate certainty of your assessment based on evidence completeness.
- If evidence is missing, lower confidence and convert assumptions into explicit questions.

## Outputs
- `paper.txt`
- `review.json`
- Chat review summary (human-readable)

## Safeguards
- Do not fabricate citations or claims not present in the input.
- Keep quotes short and avoid reproducing large sections of the paper.
- Clearly separate evidence from inference when confidence is low.
- Prefer section/page pointers when available to make feedback auditable.

## Example
Input: "Review `paper.pdf` using NeurIPS-style criteria."

Actions:
1. Extract `paper.txt` from the PDF.
2. Run the dimension pass and map findings to schema fields.
3. Produce `review.json` against the schema.
4. Post a concise chat review with the six sections above.

Output:
- `review.json` (structured)
- Conversation summary (human-readable)

## Notes
- This skill is inspired by ScholarEval-style structured scholarly evaluation.
- Keep output bounded and evidence-linked; do not expand into unstructured long-form critique unless requested.

## References
- Review JSON schema: `references/review.schema.json`
- Review prompt: `references/review-prompt.md`
- Safeguards: `references/safeguards.md`
- ScholarEval paper: https://arxiv.org/abs/2510.16234
