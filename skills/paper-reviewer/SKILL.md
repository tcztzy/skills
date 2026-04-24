---
name: paper-reviewer
description: Review academic papers (PDF/LaTeX/Markdown) with a ScholarEval-inspired dimension pass and produce both structured peer-review JSON (NeurIPS-style fields) and a concise human-readable review with prioritized, actionable feedback. Use for comprehensive, targeted, or comparative paper evaluation while keeping output bounded.
---

# Paper Reviewer

## Overview
Use JSON as the consistency anchor, not the only deliverable.

Default review standard is careful close reading:
- Cover every major section in paper order; do not focus only on the sections that already look suspicious.
- Read prose-heavy sections sentence by sentence. For equation-, table-, or figure-heavy passages, inspect claim by claim, equation by equation, or panel by panel.
- Record explicit evidence for each finding while reading so the final verdict can point to exact locations.
- If a section has no material problems after close reading, say that explicitly instead of leaving it unmentioned.
- Treat close reading as artifact-gated: prepare and complete `close_reading_audit.jsonl`, then validate it before scoring or writing the final review.

For PDF inputs, default to a visual-first review:
- Render page images and inspect them directly.
- Treat text extraction as optional support for dense passages, not the main evidence source.
- If a dedicated `pdf` skill is available in the session, use it first for rendering or layout-sensitive PDF inspection. Use this skill's bundled renderer as the local fallback.

Default behavior is dual output:
- `review.json` for machine parsing and automation.
- A concise, human-readable review in the conversation.

If the user is doing pre-submission self-positioning and mainly wants to decide whether to go, kill, pivot, or reshape the story before formal review, route to `research-impact-strategy` instead.
If the user wants a pre-submission readiness pass, keep the same bounded format but pay extra attention to title/abstract discipline, closest-prior-work comparison, figure-first readability, and any cover-letter or resubmission materials the user provides.

## Workflow
1. If the input is a PDF, render page images first.
   - Prefer the session's `pdf` skill for PDF rendering or page-level inspection when available.
   - Fallback to this local renderer when no suitable PDF helper is available:
   ~~~bash
   uv run scripts/render_pdf_pages.py --pdf paper.pdf --out-dir paper_pages
   ~~~
2. Prepare the deterministic close-reading ledger before scoring.
   - For PDF input, create audit units directly from the PDF's page/block structure:
   ~~~bash
   uv run --with PyMuPDF scripts/close_reading_audit.py prepare --pdf paper.pdf --out close_reading_audit.jsonl --coverage coverage_map.json
   ~~~
   - For LaTeX, Markdown, or extracted text, use the text source instead:
   ~~~bash
   uv run scripts/close_reading_audit.py prepare --text paper.txt --out close_reading_audit.jsonl --coverage coverage_map.json
   ~~~
   - While reviewing, fill every JSONL row with `review_status` (`ok`, `issue`, `question`, or `na`) and a short `review_note`. Use `finding_ids` to link rows to final weaknesses, questions, or suggestions when relevant.
   - Do not score or write the final review while any row is still `todo`.
3. Run a visual pass over the rendered pages before scoring.
   - Layout, whitespace balance, and page rhythm.
   - Typography, font size, contrast, and crowding.
   - Figure, table, and chart readability.
   - Caption alignment, panel labels, and figure/table callouts.
   - Cropping, overflow, awkward breaks, and other production issues.
4. Extract text only if needed for searchability, dense methods, equations, or precise wording checks.
   ~~~bash
   uv run --with pypdf -s scripts/extract_pdf_text.py --pdf paper.pdf --out paper.txt
   ~~~
5. Build or refine the coverage map before scoring.
   - Enumerate the paper's major sections in order: title/abstract, introduction, related work, method, experiments/results, discussion/limitations, conclusion, appendix/supplement when present.
   - Note the page range or figure/table/equation identifiers for each section as you go.
   - Review each section sequentially and keep a record for every section, including sections where no material issues are found.
   - Use `coverage_map.json` from the audit script as the initial map, then correct section names or ranges manually if the PDF heading heuristic is imperfect.
6. Set evaluation scope and context.
   - Scope: `comprehensive`, `targeted`, or `comparative`.
   - Stage: early draft vs. near-submission.
   - Venue or discipline constraints if provided.
   - Whether this is a submission-readiness check and whether cover letters, prior reviews, or reviewer suggestions are included.
7. Run a dimension pass before scoring.
   - Problem formulation and research questions.
   - Title/abstract reasonableness and audience fit.
   - Literature positioning and gap identification.
   - Fairness and prominence of comparison to the closest prior work.
   - Methodology and design rigor.
   - Data/sources quality and transparency.
   - Analysis quality and claim-evidence alignment.
   - Results presentation and interpretation.
   - Writing and organization quality.
   - Visual presentation quality: layout, tables, figures, charts, and caption consistency.
   - Citation quality and balance.
   - Within each section, test whether each sentence or claim is accurate, supported, scoped correctly, and connected to surrounding claims.
8. Validate the completed close-reading ledger.
   ~~~bash
   uv run scripts/close_reading_audit.py validate --audit close_reading_audit.jsonl
   ~~~
   - If validation fails, continue the close reading and fix the missing rows. Do not present a final verdict until validation passes.
   - If the paper is too long to complete in the current turn, report the validated coverage gap explicitly instead of implying a complete review.
9. Map findings into NeurIPS-style review JSON using `references/review.schema.json` and `references/review-prompt.md`.
10. Synthesize a concise chat review aligned to JSON judgments.
11. Unless the user explicitly asks for JSON-only, provide both outputs in the same turn.

## Optional Parallel Close Reading
Use subagents only when the active environment permits them and the user has explicitly allowed subagents.

- Split work by disjoint page ranges, sections, or unit ID ranges from `coverage_map.json`.
- Give each subagent only its assigned rendered pages/source units and ask for completed `close_reading_audit.jsonl` rows plus evidence-linked findings for that range.
- Merge returned rows into the main ledger, then run the validator locally.
- Keep scoring, final verdict, and conflict resolution in the coordinator pass. Subagents support coverage; they do not replace the validation gate.

## Dimension Mapping Rules
- `Originality` and `Contribution`: novelty, gap clarity, and practical/theoretical contribution.
- `Quality` and `Soundness`: method/data/analysis rigor and limitations handling.
- `Clarity` and `Presentation`: writing quality, organization, result communication, and visual presentation quality.
- `Significance`: impact potential and relevance to venue scope.
- `Overall` and `Decision`: integrated judgment; do not contradict dimension-level evidence.

## Human-Readable Chat Format
Use short sections:
- Overall verdict
- Section-by-section audit (required: include every major section; if no material issue is found, say so explicitly)
- Main strengths
- Main weaknesses or risks
- Submission-readiness risks (required when the task is near-submission)
- Visual presentation and figure/table audit (required for PDF inputs)
- Questions for authors
- Priority suggestions (ranked by impact)
- Confidence

Location requirement for the chat review:
- Every weakness, strength, question, and priority suggestion must include a concrete locator.
- Minimum locator: section heading plus page number.
- Prefer richer locators when possible: paragraph number, sentence cue, quoted phrase, figure/table/equation identifier, or panel label.
- If exact sentence boundaries are unclear in the PDF, use the narrowest reliable pointer and say so.

## Scoring Guidance
- For 1-4 fields: use integers only and justify with dimension evidence.
- `Overall` (1-10): reflect holistic merit, not a simple mean.
- `Confidence` (1-5): rate certainty of your assessment based on evidence completeness.
- If image resolution or visual evidence is insufficient, lower confidence and convert assumptions into explicit questions.
- Do not turn a vague concern into a scored weakness unless you can anchor it to a concrete passage, visual element, or section-level evidence.

## Outputs
- `paper_pages/` (for PDF inputs)
- `coverage_map.json`
- `close_reading_audit.jsonl`
- `review.json`
- Chat review summary (human-readable)
- Optional `paper.txt` only when supplementary extraction is needed

## Safeguards
- Do not fabricate citations or claims not present in the input.
- Keep quotes short and avoid reproducing large sections of the paper.
- Clearly separate evidence from inference when confidence is low.
- Prefer page pointers for all findings, not only layout and figure/table issues, to make feedback auditable.
- Do not silently skip sections. If a reviewed section appears sound, state that no material issues were identified there.
- If you cannot localize a concern precisely enough to be actionable, downgrade it to a question or uncertainty rather than presenting it as a firm defect.
- Do not override a failed `close_reading_audit.py validate` result with prose claims of completion.

## Example
Input: "Review `paper.pdf` using NeurIPS-style criteria."

Actions:
1. Render `paper_pages/` from the PDF.
2. Generate `coverage_map.json` and `close_reading_audit.jsonl`.
3. Inspect the page images for layout, figures, tables, charts, and caption alignment.
4. Extract `paper.txt` only if the visual pass leaves ambiguities in dense sections.
5. Complete and validate `close_reading_audit.jsonl`.
6. Run the dimension pass and map findings to schema fields.
7. Produce `review.json` against the schema.
8. Post a concise chat review with the required section-by-section audit and visual section.

Output:
- `paper_pages/` (rendered PNGs)
- `coverage_map.json`
- `close_reading_audit.jsonl`
- `review.json` (structured)
- Conversation summary (human-readable)

## Notes
- This skill is inspired by ScholarEval-style structured scholarly evaluation.
- Keep output bounded and evidence-linked; do not expand into unstructured long-form critique unless requested.
- For LaTeX or Markdown papers, prefer reviewing the compiled PDF when available so layout and figures are visible.
- Use the dedicated `pdf` skill for generic PDF manipulation when it is available; keep this skill focused on review criteria and evidence synthesis.
- If submission materials are provided, review them for journal specificity, resubmission hygiene, and obvious conflict-of-interest risk, but keep the output concise.

## References
- Review JSON schema: `references/review.schema.json`
- Review prompt: `references/review-prompt.md`
- Safeguards: `references/safeguards.md`
- Visual checklist: `references/visual-review-checklist.md`
- ScholarEval paper: https://arxiv.org/abs/2510.16234
