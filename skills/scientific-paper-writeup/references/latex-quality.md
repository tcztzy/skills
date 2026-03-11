# LaTeX Quality Checklist

## Common issues to prevent
- Unescaped special characters: `& % $ # _ { } ~ ^ \\`.
- Unmatched braces or environments.
- Duplicate figure/table labels or references.
- Missing figure files or mismatched filenames.
- Broken bibliography blocks or missing `references.bib`.
- Removing required `\\graphicspath` directives.

## Recommended checks
1. **Compile early and often** with `pdflatex`/`bibtex` (or the project's build system).
2. **Run a linter** like `chktex` to catch syntax and style issues.
3. **Verify figures**:
   - All `\\includegraphics{...}` entries exist on disk.
   - Unused figures are either removed or moved to the appendix.
4. **Respect page limits**:
   - Keep the main text within the page limit.
   - Move extra plots/tables to the appendix.
5. **Bibliography hygiene**:
   - Keep references in `\\begin{filecontents}{references.bib} ... \\end{filecontents}` if the template requires it.
   - Use only vetted citations and do not hallucinate entries.
