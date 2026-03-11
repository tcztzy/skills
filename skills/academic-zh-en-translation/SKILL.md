---
name: academic-zh-en-translation
description: Translate academic papers, theses, dissertations, abstracts, literature reviews, methods, results, captions, and reviewer responses between Chinese and English with source-faithful completeness, discipline-appropriate terminology, and target-language academic idiom. Use whenever the user asks for 中英互译/英中互译 of journal articles or doctoral/master's thesis text and cares about fidelity, no omissions, natural academic tone, or avoiding literal translation.
metadata:
  short_name: academic-translation
  aliases: 中英互译, 英中互译, 学术翻译, 论文翻译, thesis translation, dissertation translation
---

# Academic Zh-En Translation

## Overview
Translate for academic use, not for decorative bilingual prose.

- Preserve every claim, qualifier, limitation, citation relation, table or figure reference, unit, abbreviation definition, and structural cue that matters to meaning.
- Rewrite at sentence and paragraph level whenever literal transfer would reduce clarity or violate target-language academic norms.
- Never add evidence, novelty, certainty, criticism, or rhetorical flourish that the source does not contain.
- If the source is ambiguous, corrupted, or internally inconsistent, flag the issue briefly instead of guessing.

When you need source-backed rationale for style decisions, read [`references/research-notes.md`](references/research-notes.md).

## Default Output
- If the user asks only for translation, return the translation only.
- If the user asks for checking or polishing, return:
  1. the translation;
  2. a short note on unresolved ambiguities or terminology risks.
- Do not silently omit titles, subtitles, keywords, footnotes, acknowledgements, appendix labels, caption notes, or bracketed statistical information.

## Workflow
1. Identify the translation direction and genre.
   - Journal article, conference paper, doctoral dissertation, master's thesis, abstract, chapter, reviewer response, figure caption, table note, or slide-ready summary.
2. Build a structure map before rewriting.
   - Title
   - Abstract
   - Keywords
   - Headings and subheadings
   - Main text
   - Figure and table captions
   - Notes, references, and appendix labels if included in scope
3. Extract a terminology sheet.
   - Terms of art
   - Institution names
   - Dataset, method, model, and instrument names
   - Abbreviations and first-use expansions
   - Units, symbols, and statistical notation
   - Reference style and author-name normalization targets if the output includes a bibliography
4. Distinguish true references from explanatory notes before rewriting.
   - Do not force sample-definition notes, variable notes, or editorial metadata into the reference list just because PDF extraction merged them.
   - If the source mixes notes and references on the page, preserve both, but keep their functions separate in English.
5. Translate section by section.
   - Keep local coherence inside each paragraph.
   - Keep global coherence across repeated terms and claims.
6. Run a completeness check.
   - Nothing added
   - Nothing omitted
   - Nothing strengthened or weakened by accident
7. Run a target-language check.
   - Sounds like academic writing in the target language
   - Not a word-for-word shadow of the source

## High-Risk Zones
- Abstracts and conclusions:
  Keep the claim strength exact. These sections are where overstatement and omission most often happen.
- Literature review and discussion:
  Preserve contrast, citation scope, and hedging. Do not turn `may`, `might`, `appears to`, `suggests`, `is associated with` into stronger claims.
- Methods and results:
  Preserve sample sizes, conditions, variable names, units, figure and table numbering, and statistical markers.
- Headings and captions:
  Keep numbering, hierarchy, and cross-references aligned with the source.
- Long documents:
  Maintain one stable term per concept unless the discipline genuinely uses variants.

## 中译英
目标不是把中文“搬”成英文，而是把原文学术信息完整、准确、自然地写成英文。

### 中译英原则
- 先看论证关系，再译句子表面。
  - 识别研究目的、方法、结果、结论、限制、评价对象、比较关系、因果关系、让步关系。
- 允许改写句法，不允许改写事实。
  - 可以拆长句、补出英文必须显化的主语或逻辑连接。
  - 不可以新增实验结果、创新点、因果强度、态度色彩。
- 忠实不是僵硬。
  - 英文读者难以直接理解的汉语流水句、并列堆叠、过长前置定语，需要重组。
  - 目标是英文论文的可读性，不是逐词对应。
- 术语统一优先于局部辞藻。
  - 同一概念不要在不同段落随意改写成多个英文说法。

### 中译英写法
- 优先使用明确动词，而不是空泛名词化表达。
  - 倾向于写 `X was measured`、`we estimated X`、`the results show`，少写空洞套话。
- 删除无信息量的起手式，除非用户明确要求保留。
  - 如原文中的“本文”“笔者”“文章首先”如果只承担填充作用，通常不必机械译成 `In this paper`、`The author`。
- 处理标题、作者简介、期刊眉题等前置元信息时，优先保留对英文读者有功能性的内容。
  - 标题、作者、机构、摘要、关键词等必须完整。
  - 作者简介中通常保留职位、机构、研究方向；性别、籍贯等若只服务中文期刊惯例而用户又未要求逐项镜像，可压缩处理，但要意识到这是面向英文读者的改写，不是逐项对照译。
- 根据学术英语常规处理时态和语气。
  - 方法和具体操作通常用过去时。
  - 普遍事实、图表所示、稳定性结论可按上下文使用现在时或现在完成时。
  - 不确定、趋势、解释性结论保留审慎语气，如 `may`、`might`、`suggests`、`is likely to`。
- 尽量避免臃肿前置修饰链。
  - 汉语里连续名词压缩的信息，英文里常需要拆成 `of` 结构、介词短语、定语从句或同位语。
- 用常见、明确的学术词汇，不故作高深。
  - 不为了“像论文”而滥用冷僻大词。
- 避免无必要的身份标签或国别标签。
  - 若“外国学者”“国内学者”等标签对论证不构成实质区分，优先改成 `some scholars`、`prior studies` 等更中性的英文表达。
- 文献综述中的引文叙述尽量自然地融入句子。
  - 优先使用 `Li et al. (2017) argue ...`、`As Sanfilippo (2010) argues ...` 这类整合式叙述，而不是在正文里反复堆全名。
- 删去模糊尾巴和无效强调，只保留真正有信息量的限定语。
  - 如 `interpolation methods` 往往好于 `interpolation and similar methods`；没有范围作用的 `in particular`、`also`、`in a certain sense` 应谨慎保留。
- 摘要尤其要克制。
  - 不把摘要译成宣传文案。
  - 不补写原文没有出现的结论。
  - 关键词与中文关键词逐项对应，除非用户另有规范要求。
- 图表、公式、编号、缩写首现规则必须保留。
  - 若正文首次定义缩写，英文中也要首次定义。
  - 变量名、单位、显著性标记不得随意变形。
- 表题和小标题要给英文读者直接可懂的结构。
  - 与其写压缩型标签，不如写明比较维度或分组依据，如 `... in different income groups`。
- 参考文献若需要规范化，先确定一种作者名格式并全表一致。
  - 不要一部分中文作者用全拼，一部分用首字母缩写；若做期刊式规范化，要整表统一。

### 中译英常见修正动作
- 把一个汉语长句拆成两到三句英文短句。
- 把“随着……，……；并且……；从而……”拆成更清楚的层级关系。
- 把“对……进行研究/分析/探讨”改成更直接的英文动词。
- 把评价性模糊词压实为原文真实力度，不夸大为 `prove`、`demonstrate conclusively` 一类表述。

## English-to-Chinese
Translate for Chinese academic readability, not for formal lexical mirroring.

### English-to-Chinese principles
- Read for argument, evidence, and stance before rewriting the sentence.
- Preserve modality exactly.
  - `may`, `might`, `could`, `appears to`, `suggests`, `is associated with`, and `is consistent with` should not collapse into one stronger Chinese verb.
- Prefer native academic Chinese over Euro-Chinese.
  - Reorder information when needed.
  - Break deeply nested clauses.
  - Convert heavy nominal chains into more readable Chinese syntax.
- Keep the prose objective.
  - Chinese academic writing usually sounds better when it is concise, impersonal, and third-person in tone.
- Keep technical terms stable.
  - If a term has a standard Chinese rendering, use it consistently.
  - If the field has no stable rendering, give the English in parentheses at first mention.

### English-to-Chinese writing moves
- Do not mechanically reproduce every connective.
  - English often states relations explicitly; Chinese can sometimes absorb them into word order or punctuation.
- Rebuild information flow for Chinese readers.
  - Move conditions, time frames, or premises forward when that makes the sentence easier to read.
- Translate discourse moves semantically, not literally.
  - `This study found that ...` may become `研究发现……` or `结果表明……` depending on context.
  - `The present study` does not need a rigid calque every time.
- Avoid literary or emotional Chinese.
  - Use disciplined academic phrasing, not ornate rhetoric.
- Keep abstracts self-contained.
  - Do not translate an abstract into a chapter roadmap.
  - Do not insert background that belongs in the introduction unless the source abstract already includes it.
- Preserve references to tables, figures, equations, appendices, and supplementary material exactly.

### English-to-Chinese common repairs
- Turn a long chain like `high-resolution satellite-based land surface temperature retrieval model` into a readable Chinese modifier-head structure.
- Convert passive-heavy English into clearer Chinese while keeping responsibility and evidential scope intact.
- Merge repetitive shell phrases if they do not carry meaning.
- Keep contrast markers visible when they affect interpretation: `however`, `by contrast`, `nevertheless`, `whereas`.

## Dissertation And Thesis Notes
- Treat chapter titles, section titles, abstract, acknowledgements, and appendix labels as part of the document logic, not as disposable formatting.
- If translating a doctoral dissertation abstract, keep the innovation point, method, result, and conclusion all present.
- If translating figure or table titles inside a dissertation, keep numbering and cross-references synchronized.
- If the user asks for a defense-ready version, preserve formal tone and institutional naming exactly.

## Validation Checklist
- All explicit content preserved
- No accidental strengthening or weakening
- No dropped keywords or abbreviations
- No literal phrasing that blocks target-language comprehension
- No invented data, citations, or limitations
- Terminology consistent across title, abstract, body, and captions
- True references kept distinct from explanatory notes
- Front matter rewritten for English readability without accidental loss of functional information
- Narrative citations and bibliography name formatting handled consistently

## Examples
**Example 1**

Input:
`请把这段博士论文摘要译成英文，只给英文版本，不要解释。要求忠实、不遗漏、不要写得像宣传稿。`

Actions:
1. Extract the objective, method, result, conclusion, and keywords.
2. Build a stable terminology sheet.
3. Rewrite into idiomatic academic English without adding hype.

Output:
An English abstract and aligned `Keywords`, with all source claims preserved.

**Example 2**

Input:
`Translate the following discussion paragraph from my paper into Chinese. Keep the hedging, citation relationships, and contrast with prior work.`

Actions:
1. Mark claim strength and citation scope.
2. Rebuild sentence order for Chinese readability.
3. Preserve the cautious tone and the comparison with earlier studies.

Output:
A Chinese discussion paragraph that reads naturally in academic Chinese and keeps the original evidential stance.
