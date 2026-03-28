# Bioinformatics Diagram Style Guide (2023-2025)

## 1. Corpus Scope
- Journal: Bioinformatics
- Time window: 2023-01-01 to 2025-12-31
- Sample: 12 highly cited open-access papers with full text and captions
- Figure evidence: 8 diagrams and 4 hybrid figures

## 2. Baseline Tone of Bioinformatics Diagrams
- A diagram here is not a decorative concept sketch. It is an executable workflow view that usually maps directly to tool modules, inputs and outputs, commands, or API calls.
- The first figure often serves an onboarding role: it teaches the system boundary before the paper moves into benchmarks and results.
- The journal favors engineering-oriented storytelling, so diagrams frequently include data objects, commands, modules, web interfaces, or protein viewers in the same figure.

## 3. Structure and Reading Path
- Default to a left-to-right or top-to-bottom flow. Avoid complex loops.
- Module containers are usually rectangles or rounded rectangles. Hierarchy comes mainly from position and grouping, not decoration.
- A common structure is a two-layer figure: overall workflow plus local screenshots or local algorithm detail.
- If interface screenshots appear, they are evidence only and should not overpower the core workflow.

## 4. Lines and Connectivity
- Connecting lines should express data flow, operation order, or reasoning sequence rather than an abstract relationship network.
- Keep arrows short and direct. Avoid elaborate curves.
- Secondary information can sit in gray boxes, dashed boxes, or side notes while the main path remains visually dominant.
- For API or tool-augmented papers, split the prompt, documentation, tool call, and response into explicit stages.

## 5. Color and Hierarchy
- Use color to separate module roles such as input, core algorithm, output, and supporting notes rather than assigning a different color to every node.
- Large background areas should stay light, usually white with a few pale section blocks.
- Reuse colors consistently for the same biological object or software component so the same entity does not change color across panels.
- Reserve highlights for key results, failure cases, or final outputs. Do not style every box as an emphasized element.

## 6. Text Strategy
- Node labels should use actions or concrete entities such as operation, workflow, inference algorithm, or commands rather than vague abstractions.
- Text density may be higher than in a typical machine-learning conference schematic, but it still needs module boundaries so the whole figure does not read like a paragraph.
- Commands, APIs, and software function names are legitimate first-class information in bioinformatics tool papers and can appear directly in the figure.
- Captions often carry the detail, so text inside the figure should contain only the structural information the reader must see immediately.

## 7. Reusable Figure Templates
- Template A: input data -> core processing module -> benchmark or output results. Good for the first figure of a new tool paper.
- Template B: main workflow plus a right-side interface screenshot or structure viewer. Good for databases, web servers, and viewer-style work.
- Template C: prompt / documentation / tool execution as a three-stage chain. Good for LLM-plus-bioinformatics-tools papers.
- Template D: workflow as the first panel and performance plots in later panels. Good for the very common Bioinformatics hybrid figure.

## 8. Common Diagram Failure Modes
- Do not turn the figure into abstract branding art. The diagram should resolve to data objects, commands, and module boundaries.
- Do not let arrows loop around the figure. The dominant journal style emphasizes one-way steps and module responsibilities.
- Do not use overly dark backgrounds or large saturated color blocks; they blur the process hierarchy.
- Do not pack a full sentence of explanation into one node. Complex detail belongs in the caption.

## 9. Representative Evidence
### Representative Diagram Cases
- CoverM: read alignment statistics for metagenomics Fig. 1: Figure 1. CoverM operation. In “contig” mode, reads are aligned to contigs, alignments are sorted by reference position, a “Mosdepth array” is constructed and then coverage statistics are calculated for each contig. In “genome” mode, a Mosdepth array is similarly constructed for each contig in the genome, and then coverage statistics are reported for each genome.
- RCSB protein Data Bank: exploring protein 3D similarities via comprehensive structural alignments Fig. 1: Figure 1. Output of the pairwise alignment application. (A) Summary of aligned chains. (B) 3D Structure-based scores (Root-Mean-Square-Deviation or RMSD in Ångstrom Units; TM-score, range 0.00–1.00). (C) Sequence-based scores (% identity, number of aligned residues). (D) Toggle visibility of aligned chain, all polymers, and all ligands via 1st, 2nd, and 3rd box buttons, respectively. (E) Structurally aligned sequence regions in a darker shade, regions aligned only at sequence level in a lighter shade, non-aligned gaps are left empty. (F) 3D visualization of aligned structures. (G) Tools to export and share alignment.
- GeneGPT: augmenting large language models with domain tools for improved access to biomedical information Fig. 1: Figure 1. (Left) GeneGPT uses NCBI Web API documentations and demonstrations in the prompt for in-context learning. (Right) Examples of GeneGPT answering GeneTuring and GeneHop questions with NCBI Web APIs
- GeneGPT: augmenting large language models with domain tools for improved access to biomedical information Fig. 2: Figure 2. GeneGPT inference algorithm

### Diagram Panels Worth Borrowing from Hybrid Figures
- ADMET-AI: a machine learning ADMET platform for evaluation of large-scale chemical libraries Fig. 1: Figure 1. Overview of ADMET-AI. (A) An illustration of training an ADMET-AI graph neural network Chemprop-RDKit model. (B) The overall rank of ADMET-AI models on the Therapeutics Data Commons ADMET leaderboard of 22 ADMET datasets. Representative overall categories predicted by ADMET-AI are shown below. Error bars indicate standard error across datasets. (C) The computational efficiency of ADMET-AI. Left panel, the time (in seconds, median of three trials) for the ADMET-AI web server and other common ADMET web servers to make predictions on 1, 10, 100, or 1000 molecules from the DrugBank reference set. ADMETboost and PreADMET are limited to one molecule. Since pkCSM and SwissADME are limited to 100 and 200 molecules, respectively, their 1000 molecule times are computed as 100 molecule time ×10. Right panel, the time (in hours, median of three trials) for the ADMET-AI web server and various hardware configurations running the ADMET-AI local command line tool to make predictions on 1 million molecules from the DrugBank reference set (1000 copies of the 1000 molecule DrugBank set). Since the ADMET-AI web server is currently limited to 1000 molecules, its 1 million molecule time is computed as 1000 molecule time ×1000. (D) Commands needed to install and run the local version of ADMET-AI, either as a command line tool or as a Python module. (E) Predictions displayed on the ADMET-AI website (admet.ai.greenstonebio.com).
- FoldX force field revisited, an improved version Fig. 1: Figure 1. Summary of the FoldX optimization procedure. (A) Dataset curation requirements and global correlation for FoldX v1 versus v10. (B) R Pearson correlation for the different FoldX versions (v1–v10M) developed in this work (see Table 1 for version-specific correlation values). (C) Accuracy for v10, X-axis is FoldX error calculated in kcal/mol.
- actifpTM: a refined confidence metric of AlphaFold2 predictions involving flexible regions Fig. 1: Figure 1. actifpTM in the AF2 pipeline helps correcting bias from flexible flanking regions. (A) Predictions of MDM2-p53 with p53 peptides of length 14 (15–29) and 34 (5–28) [green and orange, respectively; the native peptide is colored in dark magenta, PDB ID: 1YCR (Kussie et al. 1996)] demonstrate the decrease in ipTM for the longer peptide, even though it is slightly more accurate than the short one (rmsBB_if: RMSD across peptide interface backbone atoms). (B) The predicted error matrices for each error bin (the first three and the last error bins are shown out of 64) are very similar for the short and long peptide predictions, except for the high error for the flanking regions present only in the longer peptide (white regions). This does not support the large drop in ipTM value upon elongation of the peptide. (C) In the last steps, the pairwise pTM-score matrix (see Supplementary Fig. S1 for calculation) is multiplied by the actifpTM normalized residue weights, then summed for every residue (row-wise). (D) As with the original TM-score, the maximum of the values along the sequence is selected as the final actifpTM score. (E–G) Comparison of ipTM and actifpTM values for example systems. The peptides were predicted with three different lengths: only the motif region, adding flanking regions of same length as the motif, or adding flanking regions twice the motif length (Lee et al. 2024). On all panels, dark magenta denotes experimentally resolved peptides, and modeled peptides are colored according to AF2 pLDDT. (E) When the modeled conformation of the defined region of the peptide does not change, actifpTM provides very similar scores, while ipTM demonstrates a considerable decrease [SIAH1 & CACYBP, PDB ID: 2A25 (Santelli et al. 2005)]. (F) actifpTM provides a similar score for similar predictions but drops appropriately upon less confident predictions [MAPK & SH3BP5, PDB ID: 4H3B (Laughlin et al. 2012)]. (G) actifpTM tracks slight changes in conformation more appropriately than ipTM, by not taking into account residues outside the interface. Upon extensions, the peptide prediction became more confident by introducing a beta-hairpin structure in the flanking regions. Unlike actifpTM, ipTM completely misses the overall (Continued)
- actifpTM: a refined confidence metric of AlphaFold2 predictions involving flexible regions Fig. 1: Figure 1. Continued increase in prediction confidence [KEAP1 & NF2L2, PDB ID: 3ZGC (H€orer et al. 2013)]. (H) With a strict threshold (indicated in parentheses), actifpTM has a higher acceptance rate than the other metrics that can be calculated from AF2 confidence outputs, in particular for predictions that include flanking regions of the peptide. For all structure visualization ChimeraX v1.8 (Meng et al. 2023) was used.
