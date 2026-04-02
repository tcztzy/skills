# Citation Workflow

Use this workflow to add or validate citations. The goal is coverage without hallucination.

## When to cite
- Summarize prior research or background facts.
- Use specific concepts, datasets, models, or optimizers.
- Compare results or baselines.
- Highlight gaps or motivate new directions.
- Support claims and conclusions.
- Suggest future work grounded in prior studies.

## Steps
1. **Identify gaps**: For each section, list claims that need citations, especially novelty framing and closest-comparison claims.
2. **Search**: Use a trusted source (Semantic Scholar or user-provided papers) to find candidates.
   - For batch Semantic Scholar sweeps, use `references/bibliography-harvest.md` and `scripts/citation_harvest.py`.
3. **Select**: Choose the most relevant and non-duplicative papers.
4. **Add to references**: Insert BibTeX entries and clean keys (ASCII-only, unique).
5. **Cite in text**: Place citations where the referenced claim appears.

## Guardrails
- Do not add citations you did not actually find.
- Do not duplicate existing citations under alternate keys.
- Prefer a diverse set of papers rather than only the most popular.
- Prefer the closest relevant comparisons over a long list of broad or prestigious but weakly connected citations.
- Do not omit or downplay key prior work just because it weakens the novelty story.
- Avoid copying text from sources verbatim.
- Record query strings and the query date in your notes when using the harvester.
