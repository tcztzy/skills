# Section Guidelines

Use this reference to outline and draft each section. Default to the standard conference style unless the user specifies a workshop or negative-results format.

## Standard conference paper (default)
- **Title**: Short, informative, preferably under two lines.
- **Abstract**: One paragraph TL;DR; motivation, method, key results; no citations unless required by venue.
- **Introduction**: Context, problem statement, why it matters, contributions, and a brief summary of findings.
- **Related Work**: Compare/contrast with closest prior work; include multiple citations.
- **Background** (optional): Definitions, problem setup, or theory needed to understand the method.
- **Method**: Clear description of the proposed approach and how it tests the hypothesis.
- **Experimental Setup**: Data, baselines, evaluation metrics, and key implementation details (avoid hardware unless requested).
- **Experiments / Results**: Report results truthfully, include plots/tables, discuss failures or negative outcomes.
- **Conclusion**: Summarize findings, limitations, and future work.
- **Appendix**: Extra details that do not fit the main text (extra plots, ablations, hyperparameters).

## Workshop / negative-results format (pitfalls and failures)
- **Goal**: Emphasize pitfalls, negative or inconclusive results, and lessons learned.
- **Format**: Shorter, often single-column; strict page limits for the main text.
- **No acknowledgements**: Do not add an acknowledgements section.
- **Minimize itemize/enumerate**: Use only when necessary and substantive.
- **Figures**: Keep a small number (e.g., up to four) in the main text; move the rest to the appendix.

Section notes for negative-results papers:
- **Abstract**: Highlight the challenge or failure and why it matters in practice.
- **Introduction**: Motivation focused on real-world consequences and why the pitfall is important.
- **Related Work**: Cite studies with similar pitfalls or failures.
- **Method / Problem Discussion**: Focus on the context that led to the failure and the attempted fixes.
- **Experiments**: Present negative or inconclusive results honestly; avoid spin.
- **Conclusion**: Extract lessons learned and suggest next steps.

## Cross-section integrity rules
- Every claim must be supported by experimental evidence or citations.
- Clearly label negative or inconclusive results.
- Avoid overstating contributions when evidence is limited.
