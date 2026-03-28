# Bioinformatics High-Impact Visual Style Guide (2023-2025)

## 1. Corpus-Level Findings
- This guide is based on 12 highly cited open-access Bioinformatics papers published from 2023 to 2025, along with their full text, 12 PDFs, and 23 extracted figures.
- Those papers accumulate 2,711 citations across genomics tools, protein structure, LLM-plus-biology, metagenomics, copy-number analysis, and related areas.
- Figure structure mix: 11 plots, 8 diagrams, and 4 hybrids.

## 2. One-Sentence Style Judgment
The dominant visual style in Bioinformatics is not conference-poster aesthetics. It is engineering-oriented method explanation plus dense results panels. When creating new figures in this journal style, prioritize clear method boundaries, strong benchmark content, and captions that can carry detail rather than decorative showmanship.

## 3. Narrative Structure Visible in the Papers
- High-frequency sections: abstract 12, introduction 12, methods 4, results 6, discussion 4, availability 12.
- High-frequency body terms: benchmark 25, workflow 5, pipeline 8, runtime 4, interactive 12, web_api 24, command_line 6, heatmap 5, correlation 52.
- This suggests that figure work is rarely just about beautifying results. It usually serves method explanation, usability communication, and performance comparison at the same time.

## 4. Overall Design Principles
- Let the first figure explain method boundaries before it emphasizes performance conclusions.
- Prefer multi-panel composite result figures instead of splitting one story into too many disconnected images.
- Put biological context directly in the figure, such as a genome locus, pathway, sample cohort, protein complex, or API/documentation reference.
- White backgrounds, publication-style restraint, and controlled color are the baseline. Emphasis should come from structure and local highlights, not decorative backgrounds.

## 5. Division of Labor Between Plots and Diagrams
- Plots handle quantitative comparison, cohort summaries, and region-level case views.
- Diagrams handle workflows, module boundaries, inputs and outputs, interfaces, and tool-usage explanation.
- Hybrid figures are a common compromise in Bioinformatics: the first panel explains the workflow and later panels report the benchmark evidence.

## 6. Recommended Figure Templates
- New tool paper: use a hybrid Figure 1 with workflow overview plus the core benchmark.
- Method-improvement paper: use a composite plot in Figure 1 or Figure 2 to highlight accuracy, runtime, and robustness.
- Database or web-platform paper: use a diagram for Figure 1 with interface screenshots, then follow with query-result plots.
- LLM or tool-augmented paper: explicitly show the prompt, tool call, retrieval, and source of truth, then use plots to report task performance.

## 7. Caption Evidence Synthesis
- Plot captions repeatedly use result-oriented terms such as comparison, runtime, correlation, heatmap, genome plot, and cohort.
- Diagram captions more often center on workflow, overview, algorithm, output, viewer, and API or tool use.
- Hybrid captions often combine overview, benchmark, commands, web interface, and confidence comparison within a single figure description.

## 8. Delivery Guidance
- If you will keep building new figures from this run, start with the combination of a hybrid first figure plus plot-based result figures.
- If you can produce only one figure, default to a hybrid because it best matches the habits seen in the highly cited sample.
- Prepare captions at publication quality. Do not expect the figure alone to carry every method detail.
