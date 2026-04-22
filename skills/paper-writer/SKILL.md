---
name: paper-writer
description: Single entry point for drafting or revising scientific papers, generating profile-based LaTeX scaffolds, harvesting draft-local citations into BibTeX, and auditing figure-caption-figref alignment from paper PDFs. Use when writing or editing research papers, workshop submissions, technical reports, negative-results papers, venue-specific drafts such as standard conference papers and 4-page ICBINB manuscripts, manuscript-local bibliography repair, or figure QA while keeping claims grounded in experiment artifacts. When the manuscript is blocked by an evidence gap, actively recommend the smallest decisive supplementary experiment, and run simple statistics or lightweight analyses directly when the artifacts are already available. Route Zotero library management, collection export, and keep-updated bibliography sync to `zotero`.
metadata:
  short_name: paper-writer
  aliases: scientific-paper-writeup, paper-writeup, manuscript drafting, research writing, paper draft, writeup-normal, writeup-icbinb, ICBINB writeup, manuscript bibliography repair, manuscript citation harvest, figref audit
---

# Paper Writer

## Overview
Use this as the one research-manuscript skill in the repository.

It covers five bundled workflows:
- Draft or revise a manuscript directly in LaTeX or Markdown.
- Generate an offline-first LaTeX scaffold from structured artifacts using `scripts/writeup_scaffold.py`.
- Harvest candidate citations into JSON + BibTeX using `scripts/citation_harvest.py`.
- Extract figure-region images, captions, and figrefs into an audit bundle using `scripts/extract_figures_and_refs.py`.
- Prepare journal-submission support materials such as cover letters, reviewer suggestions, and resubmission notes.

When a draft is blocked by missing evidence, do not stay passive. Surface the gap explicitly, recommend the smallest experiment that would unblock the claim, and run the easy version yourself when it is already feasible from local code, logs, tables, or predictions.

Keep only genuinely adjacent tasks outside this skill:
- Use `research-impact-strategy` first if the story or central claim is still blurry.
- Use `zotero` when the job is library management, connector capture, or collection export.
- Use `paper-visualizer` to generate manuscript-ready figures.
- Use `academic-zh-en-translation` for bilingual manuscript translation.
- Use `latex-to-word` only when the deliverable must become `.docx`.
- Use `paper-reviewer` for bounded peer-review style evaluation.

## Draft / Revise Workflow
1. **Collect inputs**
   - Required: research idea or problem statement, experiment summaries/results, and available plots/tables.
   - Optional: prior draft, venue constraints (page limit, single/double column), and a references.bib file.

2. **Choose the target format**
   - Standard conference paper (multi-section, 6-8 pages, double-column).
   - Workshop/negative-results paper (shorter, single-column; emphasize pitfalls).
   - ICBINB-style short paper when the task explicitly targets that venue or format.
   - If unclear, ask for the target venue or page limit; otherwise default to a standard conference format.

3. **Outline sections**
   - Use the section guidance in `references/section-guidelines.md`.
   - Ensure every claim is supported by experiment logs or citations.

4. **Check for evidence gaps before polishing prose**
   - Look for claims that still need support, such as missing variability estimates, missing baseline comparisons, absent ablations, weak error analysis, or unclear robustness checks.
   - If a gap is real, treat it as a writing blocker rather than trying to write around it.
   - Prefer the smallest decisive addition that would make the paper more convincing.

5. **Draft the manuscript**
   - Write section by section.
   - Cite related work using existing references only. If new citations are needed, follow `references/citation-workflow.md` and the bundled bibliography helper in `references/bibliography-harvest.md`.
   - Do not invent results or citations.
   - Do not hide evidence gaps with vague wording. Either support the claim, soften the claim, or mark the need for a supplementary experiment.
   - Do not write local repository or filesystem paths in the manuscript body (for example `/Users/...` or checkout-specific paths). Refer to artifacts, scripts, or resources in paper-appropriate prose instead.

6. **Run a submission-readiness pass when journal fit matters**
   - Use `references/submission-readiness.md` when the paper is headed to a journal, a high-selectivity venue, or a resubmission round.
   - Tighten the title and abstract so they are concise, accurate, and not inflated.
   - Make the comparison to the closest prior work fair and prominent instead of relying on vague novelty language.
   - Ensure the main message is visible from the figures, captions, and figrefs without hunting through the text.
   - If the user needs them, draft a journal-specific cover letter, unbiased reviewer suggestions, and a clear resubmission note describing material changes.

7. **LaTeX QA and formatting**
   - Follow `references/latex-quality.md` for common issues.
   - Verify figures exist and references are consistent.
   - If figure/text alignment is the main QA problem, use `references/figure-audit.md` and `scripts/extract_figures_and_refs.py` before editing captions or figrefs by hand.
   - Respect page limits and venue layout constraints.

8. **Safeguards and integrity checks**
   - Use `references/safeguards.md` to validate factuality, attribution, and responsible disclosure.

## Evidence-Gap and Supplementary Experiment Workflow
Use this when the manuscript is bottlenecked by missing support for an otherwise important claim.

1. **Classify the gap**
   - Simple: statistics or slicing that can be computed from existing artifacts, such as means and standard deviations across seeds, confidence intervals, significance tests, win rates, proportions, sample counts, error buckets, or a missing summary table.
   - Lightweight: a short rerun, a small ablation, a missing baseline on existing outputs, or a simple robustness check that should finish quickly with current code and data access.
   - Heavy: long retraining, new dataset collection, major annotation work, or anything that materially changes scope, compute, or timeline.

2. **Default to action, not only advice**
   - For simple gaps, run the analysis directly if the needed artifacts are already present locally. This includes simple statistics, aggregation, plotting, and error breakdowns.
   - For lightweight gaps, actively recommend the experiment and execute it when it is low-risk, cheap, and clearly within the current workspace setup.
   - For heavy gaps, do not launch it silently. Tell the user why it is important, propose the smallest decisive version, and explain what claim it would validate.

3. **Prefer the smallest decisive experiment**
   - Ask which uncertainty matters most for acceptance: effect size stability, baseline fairness, ablation necessity, robustness, or failure mode characterization.
   - Reduce broad ideas like "more experiments" into one narrow intervention with a clear expected manuscript payoff.
   - If a claim is not central enough to justify new work, weaken or remove the claim instead of expanding the project.

4. **Integrate results honestly**
   - Record the method, sample definition, and any assumptions made in the supplementary analysis.
   - Update the manuscript text, tables, figures, and limitations together so the new evidence is reflected consistently.
   - If the new result is negative or mixed, keep it and adjust the claim accordingly.

## Submission Support Workflow
Use this when the user wants help beyond the manuscript itself, such as a cover letter, reviewer suggestions, associate-editor suggestions, or a resubmission note.

1. **Collect submission context**
   - Target journal or venue, audience, and whether this is a fresh submission, resubmission, or transfer.
   - Optional but useful: prior reviews, editor comments, rejected cover letter, and requested journal-transfer target.
2. **Run the readiness checklist**
   - Use `references/submission-readiness.md`.
3. **Draft supporting materials**
   - Cover letter: explain why the work matters to the journal's readers, not just the immediate subfield.
   - Reviewer suggestions: propose technically competent, conflict-screened reviewers only when the user asks.
   - Associate-editor suggestions: provide them only when the venue uses them and the user asks.
   - Resubmission note: state what changed and why the new version is materially different.
4. **Check journal specificity**
   - Remove stale journal names or generic boilerplate.
   - Avoid suggesting transfers to journals that are obviously outside scope.
5. **Hand back a submission packet**
   - Return the manuscript deltas plus the supporting text as separate deliverables so the user can review them independently.

## Bibliography Helper Workflow
Use this when the draft has citation gaps or a weak `references.bib`, not when the main job is Zotero library management, collection export, or keep-updated BibTeX sync.

1. **Identify citation gaps**
   - Mark each unsupported claim using `references/citation-workflow.md`.
2. **Prepare queries**
   - Put one query per line in `queries.txt`, or pass repeated `--query` flags.
3. **Run the harvester**
   - `uv run -s scripts/citation_harvest.py --online --in queries.txt --out-json citations.json --out-bib citations.bib`
4. **Review and merge**
   - Inspect `citations.json`, prune false positives, and merge vetted entries into `references.bib`.
   - Clean BibTeX keys if they collide with existing entries.
   - Make sure the closest prior work is included explicitly; do not keep only flattering or high-prestige comparisons.
5. **Apply safeguards**
   - Follow `references/bibliography-harvest-safeguards.md`.

## Figure Audit Workflow
Use this when caption clarity, missing figrefs, or figure redundancy is the main manuscript issue.

1. **Extract an audit bundle**
   - `uv run --with PyMuPDF -s scripts/extract_figures_and_refs.py --pdf paper.pdf --out-dir audit_out --max-pages 50 --dpi 150`
2. **Review the bundle**
   - Use `references/figure-audit-checklist.md` with `audit_out/figures.json` and `audit_out/images/*.png`.
3. **Make edits to the paper**
   - Fix caption mismatches, missing figrefs, confusing legends, and appendix placement.
4. **Apply safeguards**
   - Follow `references/figure-audit-safeguards.md`.

## Scaffold Workflow
Use this when the user already has structured artifacts and wants a fast paper skeleton instead of free-form drafting.

1. **Prepare structured inputs**
   - Idea JSON: `references/idea.schema.json`
   - Summary JSON: `references/summary.schema.json`
   - Optional summary Markdown
   - Optional plot manifest: `references/plot_manifest.schema.json`
2. **Choose a scaffold profile**
   - `conference`: default standard paper scaffold. Accepts the legacy aliases `standard` and `normal`.
   - `icbinb`: compact 4-page ICBINB scaffold.
3. **Generate the scaffold**
   - Offline first:
   - `uv run -s scripts/writeup_scaffold.py --profile conference --idea-json idea.json --summary-json summary.json --plots-manifest plot_manifest.json --out-dir writeup_out`
   - Optional LLM drafting:
   - `uv run --with openai -s scripts/writeup_scaffold.py --profile icbinb --idea-json idea.json --summary-json summary.json --out-dir writeup_out --online --model gpt-4o-mini`
4. **Review the generated `paper.tex`**
   - Fill remaining `TBD.` sections.
   - Verify that captions, claims, and section emphasis still match the evidence.
5. **Run the normal QA pass**
   - Use `references/latex-quality.md` and `references/safeguards.md` before treating the scaffold as submission-ready.

## Request checklist for users
- Target venue or page limit (if any)
- Target journal audience and whether this is a new submission, resubmission, or transfer
- Desired format (standard vs. negative-results / workshop)
- Inputs available: idea text, summaries/logs, plots, citations
- Whether local code, predictions, result tables, or logs are available for quick supplementary analyses or statistics
- Output format: LaTeX (preferred) or Markdown
- Whether the user also needs a cover letter, reviewer suggestions, or a resubmission note
- If structured artifacts exist, whether the user wants a scaffold profile (`conference` or `icbinb`)

## Output expectations
- A complete manuscript (LaTeX or Markdown), with all sections filled.
- Or a scaffolded `paper.tex` generated from structured artifacts and ready for manual completion.
- Optional submission-support materials such as a cover letter, reviewer suggestions, or a resubmission note.
- When needed, a narrowly scoped supplementary analysis or experiment plan, and the computed result directly if it was simple enough to run from existing artifacts.
- Citations only from provided references.bib or vetted sources.
- Honest reporting of negative or inconclusive results.
- The main text must not include local repository or filesystem paths; rewrite them as reader-facing descriptions if the source material contains such paths.

## References
- Section guidance: `references/section-guidelines.md`
- Citation workflow: `references/citation-workflow.md`
- Submission-readiness checklist: `references/submission-readiness.md`
- Bibliography helper workflow: `references/bibliography-harvest.md`
- Bibliography helper safeguards: `references/bibliography-harvest-safeguards.md`
- LaTeX quality checks: `references/latex-quality.md`
- Figure audit workflow: `references/figure-audit.md`
- Figure audit checklist: `references/figure-audit-checklist.md`
- Figure extraction output schema: `references/figure-extraction-output-schema.md`
- Figure audit safeguards: `references/figure-audit-safeguards.md`
- Safeguards checklist: `references/safeguards.md`
- Idea schema: `references/idea.schema.json`
- Summary schema: `references/summary.schema.json`
- Plot manifest schema: `references/plot_manifest.schema.json`
- Scaffold templates: `references/conference_template.tex`, `references/icbinb_template.tex`
- Citation harvester: `scripts/citation_harvest.py`
- Figure extractor: `scripts/extract_figures_and_refs.py`
- Offline-first scaffold runner: `scripts/writeup_scaffold.py`
