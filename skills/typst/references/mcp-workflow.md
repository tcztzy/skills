# Typst MCP Workflow

This skill expects a Typst MCP server named `typst` or an equivalent Typst-focused MCP endpoint.

Use MCP for the shortest feedback loop that can answer the question before escalating to full local compilation.

## Tool Map

- `list_docs_chapters()`
  - Use first when the relevant Typst docs area is unclear.
  - Good for broad questions such as tables, math, figures, references, layout, and scripting.

- `get_docs_chapter(route)`
  - Use after selecting one documentation chapter.
  - Prefer this over guessing syntax from memory.

- `get_docs_chapters(routes)`
  - Use when a task spans a small number of connected areas, for example layout plus figures, or math plus scripting.

- `latex_snippet_to_typst(latex_snippet)`
  - Use when the source idea is easier to draft in LaTeX.
  - Best for equations, aligned math, theorem-like fragments, and short tables.

- `check_if_snippet_is_valid_typst_syntax(typst_snippet)`
  - Use before inserting a non-trivial snippet into the real document.
  - Use again after manual cleanup of converted output.

- `typst_to_image(typst_snippet)`
  - Use for isolated visual snippets when local appearance matters.
  - Best for quick preview of diagrams, boxed callouts, aligned layouts, or delicate spacing.

## Recommended Sequences

### Unknown syntax or API

1. `list_docs_chapters()`
2. `get_docs_chapter(route)`
3. Copy the smallest relevant pattern.
4. Adapt it locally.
5. Validate the adapted snippet.

### LaTeX to Typst conversion

1. Write the smallest correct LaTeX fragment.
2. Convert it with `latex_snippet_to_typst(...)`.
3. Clean up the Typst result to fit the local document style.
4. Validate the result with `check_if_snippet_is_valid_typst_syntax(...)`.
5. Insert it into the real file and run local compile.

### Snippet visual debugging

1. Reduce the problem to the smallest Typst snippet.
2. Validate syntax.
3. Render with `typst_to_image(...)`.
4. Adjust spacing or structure.
5. Move the fixed snippet back into the full document and run local compile.

## Notes

- If multiple snippets need the same operation, use the plural MCP variants when available.
- MCP is the preferred docs and snippet layer, but it does not replace whole-project validation.
- When MCP output conflicts with actual local compile behavior, trust the local Typst compiler and then re-check the docs chapter that informed the snippet.
