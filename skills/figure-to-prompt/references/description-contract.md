# Description contract

Write concrete natural language, using normalized coordinates when they remove ambiguity. Coordinates refer to the extracted image, origin at top left, x increasing right and y increasing down. Record the native pixel dimensions. Measured values and visual estimates must be distinguished.

## Source and claim

- Figure ID, source/version, URL or local path, page and crop, caption location and relevant paragraph/section.
- Role, visible support, unsupported inference, and proposed disposition.
- Source type: conceptual diagram, measured chart, real captured UI, author-declared mock, or unknown.

## Canvas and visual grammar

Describe aspect ratio, background, margins, panel count/order, panel bounds, alignment, gutters and empty regions. Specify typeface category and approximate relative sizes, line weights, arrowhead shape, corners, fills, strokes and color meaning. Do not call estimated colors/font families exact. Preserve a legend even if it repeats a nearby label.

## Element inventory

Describe each element in reading order: position and dimensions, shape, fill/stroke, exact text and line breaks, alignment, icon geometry or asset identity, and overlapping/occluding elements. Include complete text separately when dense labels would interrupt the spatial description.

For every meaningful connector give source, target, direction, attachment side, route, crossings, solid/dashed style and verbatim label. Distinguish data flow, execution order, ownership and provenance predicates. In PROV, `output → activity [wasGeneratedBy]` is not the same arrow as an execution flow `activity → output`.

## Charts

List axis limits, scale type, ticks, units, categories/order, series/legend mapping, values available in the source, markers, line geometry, error bars and what they mean, n, annotations and exclusions. With an undigitized line plot, describe the visible trajectory as approximate and mark its sample values unavailable. Never invent a complete dataset to make a prompt seem complete.

## Software screens

Record viewport, browser/OS chrome, navigation selection, panes, scroll positions, visible text, controls and their shown states. Capture selected artifact/session IDs and meaningful status transitions only when observable. Separate a display of a state from proof that the underlying operation happened. Preserve the difference between approved, saved, draft, scientifically supported and successful execution.

## Prompt and review

Use: intended use; source versus redesign; canvas/layout; objects/edges; verbatim labels/data; typography/color; required invariants; exclusions; uncertain details. A strict reconstruction preserves visible defects; a redesign explicitly changes them. Do not render external captions inside a figure unless reproducing a source whose panel captions are part of the image.

After any requested generation, compare the original and candidate at the intended display size. Check object count, graph topology, text, data marks, cropped content and evidential claims before aesthetics. Record failures without inventing an overall fidelity percentage. The untested state is “prompt prepared; reconstruction not validated.”

## Behavioral checks

- An abstract-only article: inventory as inaccessible; no invented visual description.
- A figure with an unreadable axis label: preserve a localized uncertainty, rather than supplying a plausible unit.
- A PROV graph: retain predicate direction even when it points opposite the workflow's reading order.
- A mock dashboard with p-values: transcribe visible values, but do not treat them as measured evidence.
- A memory approval screen: approval changes write authority, not the scientific truth or necessarily the concept's draft status.
- A cropped screenshot: do not invent controls below the crop. A redesign may add a proposed control only when labeled and justified.
