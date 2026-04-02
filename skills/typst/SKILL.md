---
name: typst
description: Draft, convert, debug, and validate Typst documents. Use when working with `.typ` or `.typst` files, migrating LaTeX snippets to Typst, fixing Typst syntax, checking rendered output, or authoring reports, slides, posters, and templates where `typst-mcp` can provide docs lookup, conversion, syntax checks, and snippet previews before final local `typst compile` verification.
metadata:
  short_name: typst
  aliases: typst-writing, typst-document, typst-compile, latex-to-typst
---

# Typst

## Overview

Use this as the single Typst-document skill in the repository.

It combines two layers:

- `typst-mcp` for documentation lookup, LaTeX-to-Typst conversion, snippet syntax checks, and quick image previews.
- A Tinymist-style local validation loop built around `typst compile`, HTML export, and SVG export for final verification.

Treat MCP as the fast iteration layer and local compilation as the final source of truth.

## Use This Skill When

- Authoring or revising `.typ` or `.typst` files.
- Translating LaTeX equations, tables, or short fragments into Typst.
- Fixing Typst syntax or unfamiliar constructs.
- Inspecting whether rendered text, numbering, line breaks, or layout match intent.
- Building or editing Typst-based papers, reports, slides, posters, or reusable templates.

## Workflow

1. Classify the task before choosing tools.
   - Unknown Typst syntax or API: query Typst docs through MCP first.
   - LaTeX fragment or equation migration: convert through MCP, then clean up.
   - Typst snippet debugging: validate syntax through MCP before editing larger files.
   - Full-document authoring or review: edit locally, then compile locally.

2. Prefer MCP for retrieval and small-unit iteration.
   - Start with `list_docs_chapters()` when you do not know the relevant Typst docs area.
   - Read only the needed chapter with `get_docs_chapter(route)` or `get_docs_chapters(routes)`.
   - If LaTeX is easier to express, draft the fragment in LaTeX and convert it with `latex_snippet_to_typst(...)`.
   - Validate any non-trivial snippet with `check_if_snippet_is_valid_typst_syntax(...)`.

3. Author incrementally.
   - Copy the smallest working pattern from docs or from the converted snippet.
   - Adapt one construct at a time instead of writing a large unvalidated block.
   - Keep imports, labels, references, and show/set rules close to the content they affect until the structure stabilizes.

4. Use snippet preview when layout is the question.
   - For isolated diagrams or visually delicate snippets, render with `typst_to_image(...)`.
   - Use this for quick feedback on spacing, emphasis, and local composition before touching the full document.

5. Run local compile after each meaningful edit.
   - `typst-mcp` validates snippets, not the whole project graph.
   - Before claiming a document is correct, compile the actual file locally with `typst compile`.
   - If the document uses relative imports or assets, compile with the correct `--root`.

6. Inspect output at the right layer.
   - PDF compile confirms the document builds.
   - HTML export is for checking rendered text, section order, and wording-sensitive output.
   - SVG export is for checking layout, numbering, line breaks, figure placement, and visual regressions.

## MCP-First Routing

Use the `typst` MCP server as the default knowledge and snippet-validation backend.

- Docs discovery and syntax lookup: `references/mcp-workflow.md`
- Local compile, HTML, and SVG verification: `references/local-validation.md`

Preferred routing:

- Unknown syntax, function, or package behavior:
  - `list_docs_chapters()`
  - `get_docs_chapter(route)` or `get_docs_chapters(routes)`
- LaTeX to Typst migration:
  - `latex_snippet_to_typst(...)`
  - `check_if_snippet_is_valid_typst_syntax(...)`
- Snippet debugging:
  - `check_if_snippet_is_valid_typst_syntax(...)`
- Snippet visual preview:
  - `typst_to_image(...)`

If the MCP server is unavailable, continue with local Typst tooling and say that docs lookup or conversion was done without MCP assistance.

## Guardrails

- Prefer official Typst documentation surfaced through MCP over memory.
- Do not treat Tinymist or editor diagnostics as the source of truth.
- Do not send non-trivial Typst code back to the user without either MCP syntax validation or local compile evidence.
- Treat MCP syntax validation as snippet-level confidence only; whole-document correctness still requires local compile.
- Keep command examples platform-neutral by using placeholder paths and forward slashes.
- Use `{p}` or `{0p}` in multi-page SVG output paths.
- Treat HTML export as a validation aid, not a production rendering contract.

## Output Expectations

- Return the final Typst code or file edits.
- State whether MCP docs lookup, MCP conversion, or MCP syntax validation was used.
- State the exact local verification step that passed, especially `typst compile`.
- If visual quality was part of the task, mention whether HTML, SVG, or image preview was checked.

## References

- MCP tool routing and usage patterns: `references/mcp-workflow.md`
- Local compile and rendering validation recipes: `references/local-validation.md`
