---
name: figure-to-prompt
description: Inspect published or manuscript figures, map their visual evidence to the surrounding text, and write detailed reconstruction or redesign prompts. Use for figure reverse description, figure-text alignment, and screenshot critique before image generation; not for generating scientific data or vector tracing.
---

# Figure to Prompt

Produce an inspectable account of what a figure shows, what the manuscript asks it to establish, and how to reconstruct its composition. A reconstruction specification and a proposed improvement are different outputs: preserve the source in the first and label changes in the second.

## Grounding

- Resolve the manuscript's figure, caption, callouts and relevant method/result paragraphs. For LaTeX, follow included files and distinguish inline TikZ from external images.
- For literature, verify title, DOI, publication version, issue date and online date separately. Record access limits. Do not describe a figure from an abstract alone.
- Preserve publisher image assets when available. For PDFs, inspect complete pages, then extract native images or render a reviewed page rectangle; vector figures are not necessarily embedded image objects. Keep page numbers, crop coordinates, source URL and file digest. A caption detector is only a candidate locator, especially with `Fig.` captions, multiple columns and multi-panel figures.
- Open every saved figure and relevant detail crop. Preserve legends, panel letters, arrowheads and text; explicitly flag source clipping and unreadable labels. OCR proposes text and geometry; visual inspection confirms them. Do not infer missing digits, p-values or identifiers.

## Analyze before prompting

For every numbered figure, identify:

1. The reader's question and the figure's single main job: explain a mechanism, show an interaction, establish a measured result, or provide an inspectable artifact example.
2. The exact manuscript location making the corresponding claim, and the visible evidence that supports it.
3. The limit of that evidence. A mock dashboard is not a measured experiment; a successful tool event is not scientific validation; a screenshot cannot establish hidden persistence, authorization or accessibility behavior.
4. Omissions, contradictions and ambiguity between figure, caption and body. Keep the observed picture separate from the author's stated interpretation and your proposed change.

Use [the description contract](references/description-contract.md) for the detailed blueprint. Apply only the chart, diagram or UI fields that the source needs. Dense figures may use a shared style section plus a complete per-panel inventory, but the final generation prompt must be self-contained or explicitly assembled from named sections.

## Deliver

Keep an overview, a complete numbered-figure inventory, inspected source images, per-figure analysis, and copyable prompts in the requested output location. For each prompt say whether it is source reconstruction, a manuscript-grounded new diagram, or a UI redesign concept.

For charts, retain the data/code as the source of truth; describe marks and values without claiming an image model will reproduce quantitative geometry. For actual software evidence, specify a real capture state and keep any generated UI mock clearly labeled as a design concept. Propose a UI change only when it addresses a visible reader/user problem supported by the existing screen or code.

Do not promise pixel identity from prose. Say which labels, geometry, icons or plot samples remain uncertain and whether a generation-and-comparison pass has actually run. If the user requested prompts for review, finish at that reviewable boundary. When generation is requested, use the available image-generation tool and evaluate the result against the saved blueprint before claiming fidelity.

When a venue is named, verify its current image/AI instructions before recommending publication use. Do not preserve a remembered blanket policy: distinguish explanatory diagrams, data visualizations, runtime screenshots and graphical abstracts. Vectorization does not change an image's evidence status or origin.

## Acceptance

The inspected source set matches the inventory; the blueprint specifies every visible panel and consequential connection; exact and uncertain text are separated; figure-to-text claims have locators; redesigns do not invent product capabilities or scientific results; and any reported validation describes what actually ran.
