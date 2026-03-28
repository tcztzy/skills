# Bioinformatics Plot Style Guide (2023-2025)

## 1. Corpus Scope
- Journal: Bioinformatics
- Time window: 2023-01-01 to 2025-12-31
- Sample: 12 highly cited open-access papers with 2,711 total citations
- Figure evidence: 23 extracted figures, including 11 plots and 4 hybrids

## 2. Baseline Tone of Bioinformatics Plots
- Prefer multi-panel composite figures. A single figure usually carries performance, accuracy, runtime, and case views together instead of splitting every metric into a separate plot.
- Information density is high, but the reading path stays linear. A common order is overall comparison first, then local zoom-in, then supporting statistics.
- Tool papers often use a three-part narrative: method improvement, benchmark, and usage result. Plots should serve that structure rather than exist as isolated statistics.

## 3. Layout Rules
- Treat Figure 1 as the main narrative entrypoint. The first figure usually provides a method-and-results overview rather than a single chart.
- Use A/B/C/D panel labels and give each panel one comparison task.
- Mixing scatter, violin, heatmap, and genome-track panels in one figure is acceptable as long as the panels share one typography, line-width, and annotation logic.
- Common arrangements include overall view on top with local detail below, or algorithm comparison on the left with case visualization on the right.

## 4. Chart-Type Preferences
- For efficiency and accuracy comparison, prefer scatter, bar, and line charts rather than elaborate encodings.
- For cohort or matrix relationships, favor heatmaps or density heatmaps.
- For genomic position, favor genome plots or track-like horizontal layouts.
- For distribution differences, violin plots or histograms are common, rather than decorative box plots.

## 5. Visual Encoding
- Color should separate groups, not express brand identity. Most figures use a small number of high-contrast colors on a white background.
- Points, lines, error bars, and shaded bands can coexist, but a single panel usually does not stack too many visual variables.
- Result emphasis relies more on outline boxes, arrows, local highlights, or red markers than on making the whole figure highly saturated.
- Statistical figures often allow grayscale or low-saturation backgrounds so attention stays on the data layer.

## 6. Axes, Labels, and Text
- Axis titles should directly name the biological quantity or evaluation metric, such as runtime, correlation, occurrence, or RMSE.
- Panels often state the key takeaway directly, such as a pathway, gene locus, or high-level alteration, instead of delegating every explanation to the caption.
- Legends usually sit close to the panel rather than far away from the data.
- Typography is typically a plain sans-serif chosen for readability and compactness rather than display value.

## 7. Reusable Figure Templates
- Template A: overall benchmark on the left and case visualization on the right. Good for the main figure in an algorithm paper.
- Template B: workflow result on top and cohort heatmap or genome plot below. Good for bioinformatics pipelines tied to population-scale data.
- Template C: one column for accuracy or correlation and one column for runtime or efficiency. Good for tool updates or version comparisons.
- Template D: main result plot plus a neighboring interface screenshot or command-line output slice used only as support.

## 8. Common Plot Failure Modes
- Do not split every metric into a separate small file. That weakens the narrative compression expected in a paper figure.
- Do not use heavy grid lines, dark backgrounds, or decorative gradients. Highly cited Bioinformatics examples are overwhelmingly white-background publication figures.
- Do not make the color system look like a product poster. The journal is more receptive to empirical figures with a few functional colors.
- Do not omit biological context. Even a benchmark figure often includes a pathway, genome region, or sample cohort.

## 9. Representative Evidence
### Representative Plot Cases
- NanoPack2: population-scale evaluation of long-read sequencing data Fig. 1: Figure 1. Example of phasius output. This plot shows the haplotype phasing structure of chr7:142 000 000–146 000 000 for 92 individuals. Every horizontal line is from a single individual, with a change in color indicating the start of a new contiguously phased genomic segment. The annotation track (bottom) shows segmental duplications with grey bars, predictably breaking the phased blocks in the case of longer repetitive elements. An interactive example can be found at https://wdecoster.github.io/phasius.
- compleasm: a faster and more accurate reimplementation of BUSCO Fig. 1: Figure 1. (a) Comparison of the runtime of compleasm and BUSCO on real datasets. (b) The comparison of completeness reported by compleasm and BUSCO on HiFi assemblies of Metazoa genomes. (c) The comparison of completeness reported by compleasm and BUSCO on HiFi assemblies of Viridiplantae genomes. (d) The proportions of BUSCO genes with frameshifts reported by compleasm on datasets of different species.
- PyDESeq2: a python package for bulk RNA-seq differential expression analysis Fig. 1: Figure 1. (A) Signiﬁcantly differentially expressed genes (with padj  0:05 and jLFCj  2) according to PyDESeq2 and DESeq2. (B) Signiﬁcantly enriched pathways (padj  0:05) obtained with the fgsea package, using Wald statistics as gene-ranking metric. Only top 10 enriched pathways (according to adjusted P-value) of at least one cancer dataset are represented. If for a given cancer dataset, a pathway is not signiﬁcantly enriched, the corresponding square is left blank. The three pathways which are considered signiﬁcantly enriched in one implementation but not the other on a given TCGA dataset are highlighted by a surrounding box. (C) Distribution of relative log-likelihoods (LðPyDESeq2ÞLðDESeq2Þ jLðDESeq2Þj ), with corresponding cumulative distribution functions. (D) Time benchmark on an 8-core machine, averaged over 10 runs, using eight threads for each package. Numbers between parenthesis correspond to dataset sample sizes. (A–D) We refer to the Supplementary Appendix for additional details on the experiments.
- GeneGPT: augmenting large language models with domain tools for improved access to biomedical information Fig. 3: Figure 3. Performance changes of the ablation (left) and probing (right) experiments as compared to GeneGPT-full

### Plot Panels Worth Borrowing from Hybrid Figures
- ADMET-AI: a machine learning ADMET platform for evaluation of large-scale chemical libraries Fig. 1: Figure 1. Overview of ADMET-AI. (A) An illustration of training an ADMET-AI graph neural network Chemprop-RDKit model. (B) The overall rank of ADMET-AI models on the Therapeutics Data Commons ADMET leaderboard of 22 ADMET datasets. Representative overall categories predicted by ADMET-AI are shown below. Error bars indicate standard error across datasets. (C) The computational efficiency of ADMET-AI. Left panel, the time (in seconds, median of three trials) for the ADMET-AI web server and other common ADMET web servers to make predictions on 1, 10, 100, or 1000 molecules from the DrugBank reference set. ADMETboost and PreADMET are limited to one molecule. Since pkCSM and SwissADME are limited to 100 and 200 molecules, respectively, their 1000 molecule times are computed as 100 molecule time ×10. Right panel, the time (in hours, median of three trials) for the ADMET-AI web server and various hardware configurations running the ADMET-AI local command line tool to make predictions on 1 million molecules from the DrugBank reference set (1000 copies of the 1000 molecule DrugBank set). Since the ADMET-AI web server is currently limited to 1000 molecules, its 1 million molecule time is computed as 1000 molecule time ×1000. (D) Commands needed to install and run the local version of ADMET-AI, either as a command line tool or as a Python module. (E) Predictions displayed on the ADMET-AI website (admet.ai.greenstonebio.com).
- FoldX force field revisited, an improved version Fig. 1: Figure 1. Summary of the FoldX optimization procedure. (A) Dataset curation requirements and global correlation for FoldX v1 versus v10. (B) R Pearson correlation for the different FoldX versions (v1–v10M) developed in this work (see Table 1 for version-specific correlation values). (C) Accuracy for v10, X-axis is FoldX error calculated in kcal/mol.
- actifpTM: a refined confidence metric of AlphaFold2 predictions involving flexible regions Fig. 1: Figure 1. actifpTM in the AF2 pipeline helps correcting bias from flexible flanking regions. (A) Predictions of MDM2-p53 with p53 peptides of length 14 (15–29) and 34 (5–28) [green and orange, respectively; the native peptide is colored in dark magenta, PDB ID: 1YCR (Kussie et al. 1996)] demonstrate the decrease in ipTM for the longer peptide, even though it is slightly more accurate than the short one (rmsBB_if: RMSD across peptide interface backbone atoms). (B) The predicted error matrices for each error bin (the first three and the last error bins are shown out of 64) are very similar for the short and long peptide predictions, except for the high error for the flanking regions present only in the longer peptide (white regions). This does not support the large drop in ipTM value upon elongation of the peptide. (C) In the last steps, the pairwise pTM-score matrix (see Supplementary Fig. S1 for calculation) is multiplied by the actifpTM normalized residue weights, then summed for every residue (row-wise). (D) As with the original TM-score, the maximum of the values along the sequence is selected as the final actifpTM score. (E–G) Comparison of ipTM and actifpTM values for example systems. The peptides were predicted with three different lengths: only the motif region, adding flanking regions of same length as the motif, or adding flanking regions twice the motif length (Lee et al. 2024). On all panels, dark magenta denotes experimentally resolved peptides, and modeled peptides are colored according to AF2 pLDDT. (E) When the modeled conformation of the defined region of the peptide does not change, actifpTM provides very similar scores, while ipTM demonstrates a considerable decrease [SIAH1 & CACYBP, PDB ID: 2A25 (Santelli et al. 2005)]. (F) actifpTM provides a similar score for similar predictions but drops appropriately upon less confident predictions [MAPK & SH3BP5, PDB ID: 4H3B (Laughlin et al. 2012)]. (G) actifpTM tracks slight changes in conformation more appropriately than ipTM, by not taking into account residues outside the interface. Upon extensions, the peptide prediction became more confident by introducing a beta-hairpin structure in the flanking regions. Unlike actifpTM, ipTM completely misses the overall (Continued)
- actifpTM: a refined confidence metric of AlphaFold2 predictions involving flexible regions Fig. 1: Figure 1. Continued increase in prediction confidence [KEAP1 & NF2L2, PDB ID: 3ZGC (H€orer et al. 2013)]. (H) With a strict threshold (indicated in parentheses), actifpTM has a higher acceptance rate than the other metrics that can be calculated from AF2 confidence outputs, in particular for predictions that include flanking regions of the peptide. For all structure visualization ChimeraX v1.8 (Meng et al. 2023) was used.
