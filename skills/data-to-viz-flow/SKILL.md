---
name: data-to-viz-flow
description: Design flow visuals such as Sankey, alluvial, chord, and transition-oriented network views. Use after `data-to-viz` routes a task to flow or when prompts ask about movement, transfer, transition, or connection volume; output a flow-chart shortlist and a backend recommendation. This family is doc-first in v1.
metadata:
  short_name: viz-flow
  aliases: sankey,alluvial,chord,flow diagram,transition
---

# Flow

Use this skill when the message is about movement, transfer, transition, or connection rather than static composition or simple ranking.

## Default chart forms

- Sankey for aggregated flows
- alluvial when the stages are ordered and categorical
- chord or arc only when structure matters more than precise reading
- network flow view when relational structure is the point

## Avoid or downgrade

- Sankey when exact quantitative reading is secondary to a simpler comparison
- chord diagrams when the audience needs exact decoding

## Publication-first backend matrix

### Doc-first in v1

- `TikZ`: publication and LaTeX-native flow schematics
- `D3`: custom browser flow diagrams
- `Vega`: declarative flow implementations when the marks/links fit Vega better than simpler chart families

### Not promised in v1

- no generator-backed path
- no pure diagram tooling such as Mermaid or Graphviz inside this skill family

## Shared workflow

1. Confirm the task is truly flow, not part-to-whole or ranking.
2. Recommend the chart form first.
3. Pick `TikZ`, `D3`, or `Vega` based on publication vs browser needs.
4. If the user wants implementation, hand-author in the chosen backend rather than claiming a generator-backed path exists.

## Example

**Input**

- "我要一个 Sankey 图来展示用户从入口页面流向不同转化路径。"

**Actions**

1. Pick the flow family.
2. Keep the chart shortlist narrow: Sankey or alluvial.
3. Recommend `TikZ`, `D3`, or `Vega` depending on deliverable constraints.

**Output**

- A flow shortlist and a doc-first backend recommendation.
