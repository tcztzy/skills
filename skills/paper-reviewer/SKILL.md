---
name: paper-reviewer
description: Review academic papers (PDF/LaTeX/Markdown) with a ScholarEval-inspired dimension pass and produce both structured peer-review JSON (NeurIPS-style fields) and a concise human-readable review with prioritized, actionable feedback. Use for comprehensive, targeted, or comparative paper evaluation while keeping output bounded.
---

# Paper Reviewer

## Overview
Use JSON as the consistency anchor, not the only deliverable.

For PDF inputs, default to a visual-first review:
- Render page images and inspect them directly.
- Treat text extraction as optional support for dense passages, not the main evidence source.
- If a dedicated `pdf` skill is available in the session, use it first for rendering or layout-sensitive PDF inspection. Use this skill's bundled renderer as the local fallback.

Default behavior is dual output:
- `review.json` for machine parsing and automation.
- A concise, human-readable review in the conversation.

If the user is doing pre-submission self-positioning and mainly wants to decide whether to go, kill, pivot, or reshape the story before formal review, route to `research-impact-strategy` instead.

## Workflow
1. If the input is a PDF, render page images first.
   - Prefer the session's `pdf` skill for PDF rendering or page-level inspection when available.
   - Fallback to this local renderer when no suitable PDF helper is available:
   ~~~bash
   uv run scripts/render_pdf_pages.py --pdf paper.pdf --out-dir paper_pages
   ~~~
2. Run a visual pass over the rendered pages before scoring.
   - Layout, whitespace balance, and page rhythm.
   - Typography, font size, contrast, and crowding.
   - Figure, table, and chart readability.
   - Caption alignment, panel labels, and figure/table callouts.
   - Cropping, overflow, awkward breaks, and other production issues.
3. Extract text only if needed for searchability, dense methods, equations, or precise wording checks.
   ~~~bash
   uv run --with pypdf -s scripts/extract_pdf_text.py --pdf paper.pdf --out paper.txt
   ~~~
4. Set evaluation scope and context.
   - Scope: `comprehensive`, `targeted`, or `comparative`.
   - Stage: early draft vs. near-submission.
   - Venue or discipline constraints if provided.
5. Run a dimension pass before scoring.
   - Problem formulation and research questions.
   - Literature positioning and gap identification.
   - Methodology and design rigor.
   - Data/sources quality and transparency.
   - Analysis quality and claim-evidence alignment.
   - Results presentation and interpretation.
   - Writing and organization quality.
   - Visual presentation quality: layout, tables, figures, charts, and caption consistency.
   - Citation quality and balance.
6. Map findings into NeurIPS-style review JSON using `references/review.schema.json` and `references/review-prompt.md`.
7. Synthesize a concise chat review aligned to JSON judgments.
8. Unless the user explicitly asks for JSON-only, provide both outputs in the same turn.

## Dimension Mapping Rules
- `Originality` and `Contribution`: novelty, gap clarity, and practical/theoretical contribution.
- `Quality` and `Soundness`: method/data/analysis rigor and limitations handling.
- `Clarity` and `Presentation`: writing quality, organization, result communication, and visual presentation quality.
- `Significance`: impact potential and relevance to venue scope.
- `Overall` and `Decision`: integrated judgment; do not contradict dimension-level evidence.

## Human-Readable Chat Format
Use short sections:
- Overall verdict
- Main strengths
- Main weaknesses or risks
- Visual presentation and figure/table audit (required for PDF inputs)
- Questions for authors
- Priority suggestions (ranked by impact)
- Confidence

## Scoring Guidance
- For 1-4 fields: use integers only and justify with dimension evidence.
- `Overall` (1-10): reflect holistic merit, not a simple mean.
- `Confidence` (1-5): rate certainty of your assessment based on evidence completeness.
- If image resolution or visual evidence is insufficient, lower confidence and convert assumptions into explicit questions.

## Outputs
- `paper_pages/` (for PDF inputs)
- `review.json`
- Chat review summary (human-readable)
- Optional `paper.txt` only when supplementary extraction is needed

## Safeguards
- Do not fabricate citations or claims not present in the input.
- Keep quotes short and avoid reproducing large sections of the paper.
- Clearly separate evidence from inference when confidence is low.
- Prefer page pointers for layout and figure/table findings when available to make feedback auditable.

## Example
Input: "Review `paper.pdf` using NeurIPS-style criteria."

Actions:
1. Render `paper_pages/` from the PDF.
2. Inspect the page images for layout, figures, tables, charts, and caption alignment.
3. Extract `paper.txt` only if the visual pass leaves ambiguities in dense sections.
4. Run the dimension pass and map findings to schema fields.
5. Produce `review.json` against the schema.
6. Post a concise chat review with the required visual section.

Output:
- `paper_pages/` (rendered PNGs)
- `review.json` (structured)
- Conversation summary (human-readable)

## Notes
- This skill is inspired by ScholarEval-style structured scholarly evaluation.
- Keep output bounded and evidence-linked; do not expand into unstructured long-form critique unless requested.
- For LaTeX or Markdown papers, prefer reviewing the compiled PDF when available so layout and figures are visible.
- Use the dedicated `pdf` skill for generic PDF manipulation when it is available; keep this skill focused on review criteria and evidence synthesis.

## References
- Review JSON schema: `references/review.schema.json`
- Review prompt: `references/review-prompt.md`
- Safeguards: `references/safeguards.md`
- Visual checklist: `references/visual-review-checklist.md`
- ScholarEval paper: https://arxiv.org/abs/2510.16234
