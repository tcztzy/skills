---
name: scientific-paper-writeup
description: Drafting or revising scientific papers (LaTeX or Markdown) from experiment logs, ideas, plots, and citations with section-by-section guidance, citation hygiene, page-limit constraints, and LaTeX QA. Use when writing or editing research papers, workshop submissions, technical reports, or negative-results papers, especially when accuracy and reproducibility matter.
---

# Scientific Paper Writeup

## Overview
Turn experiment artifacts (idea notes, logs/summaries, plots, and references) into a coherent scientific paper with rigorous citation, honest reporting, and LaTeX-quality checks.

If the main problem is that the paper lacks a single strong story, or you need to decide the core claim, title/introduction/conclusion positioning, or whether the project should be reframed before drafting, use `research-impact-strategy` first.

## Workflow
1. **Collect inputs**
   - Required: research idea or problem statement, experiment summaries/results, and available plots/tables.
   - Optional: prior draft, venue constraints (page limit, single/double column), and a references.bib file.

2. **Choose the target format**
   - Standard conference paper (multi-section, 6-8 pages, double-column).
   - Workshop/negative-results paper (shorter, single-column; emphasize pitfalls).
   - If unclear, ask for the target venue or page limit; otherwise default to a standard conference format.

3. **Outline sections**
   - Use the section guidance in `references/section-guidelines.md`.
   - Ensure every claim is supported by experiment logs or citations.

4. **Draft the manuscript**
   - Write section by section.
   - Cite related work using existing references only. If new citations are needed, follow `references/citation-workflow.md`.
   - Do not invent results or citations.
   - Do not write local repository or filesystem paths in the manuscript body (for example `/Users/...` or checkout-specific paths). Refer to artifacts, scripts, or resources in paper-appropriate prose instead.

5. **LaTeX QA and formatting**
   - Follow `references/latex-quality.md` for common issues.
   - Verify figures exist and references are consistent.
   - Respect page limits and venue layout constraints.

6. **Safeguards and integrity checks**
   - Use `references/safeguards.md` to validate factuality, attribution, and responsible disclosure.

## Request checklist for users
- Target venue or page limit (if any)
- Desired format (standard vs. negative-results / workshop)
- Inputs available: idea text, summaries/logs, plots, citations
- Output format: LaTeX (preferred) or Markdown

## Output expectations
- A complete manuscript (LaTeX or Markdown), with all sections filled.
- Citations only from provided references.bib or vetted sources.
- Honest reporting of negative or inconclusive results.
- The main text must not include local repository or filesystem paths; rewrite them as reader-facing descriptions if the source material contains such paths.

## References
- Section guidance: `references/section-guidelines.md`
- Citation workflow: `references/citation-workflow.md`
- LaTeX quality checks: `references/latex-quality.md`
- Safeguards checklist: `references/safeguards.md`
