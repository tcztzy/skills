# Local Validation Recipes

Use local Typst compilation as the final gate before claiming a document or snippet is correct.

## Compile Validation

Basic PDF compile:

```sh
typst compile --root . path/to/document.typ target/typst-check/document.pdf
```

If the document lives under another project root, set `--root` to the directory that should resolve imports and assets.

## Text Validation Through HTML

Use HTML export when wording, section ordering, labels, or text presence matters more than final page layout.

```sh
typst compile --root . --features html path/to/document.typ target/typst-check/document.html
rg -n "expected text" target/typst-check/document.html
```

This is useful for:

- heading text
- list item order
- cross-reference text
- generated wording that should appear exactly

## Visual Validation Through SVG

Use SVG export when layout matters.

Single-page output:

```sh
typst compile --root . path/to/document.typ target/typst-check/document.svg
```

Multi-page output:

```sh
typst compile --root . path/to/document.typ target/typst-check/document-{0p}.svg
```

Use SVG checks for:

- line breaks
- figure placement
- table width or overflow
- numbering layout
- emphasis, spacing, and alignment

## Playwright Follow-Up

Use Playwright only after SVG generation succeeds.

Preferred flow:

1. Export SVG.
2. Open the SVG directly if the runtime supports local files.
3. Otherwise create a tiny local HTML wrapper that embeds the SVG.
4. Inspect screenshots for layout regressions.

## Debugging Guidance

- If local compile fails, that is a blocking failure.
- Reduce the failing area to the smallest reproducible snippet.
- If the failure involves unfamiliar syntax, go back to MCP docs lookup.
- If the failure came from LaTeX conversion, re-check the converted snippet in isolation before reinserting it.

## Guardrails

- Do not use HTML export as proof of final layout quality.
- Do not skip local compile just because snippet-level MCP validation succeeded.
- Keep the validation output under a disposable `target/` or equivalent scratch directory.
