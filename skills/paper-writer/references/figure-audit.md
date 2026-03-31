# Figure / Caption / Figref Audit

Use this helper when figure-text alignment is the main manuscript QA problem and you want an auditable bundle before editing the draft.

## Workflow
1. Extract the audit bundle.
   ```bash
   uv run --with PyMuPDF -s scripts/extract_figures_and_refs.py \
     --pdf paper.pdf --out-dir audit_out --max-pages 50 --dpi 150
   ```
2. Review the bundle with `references/figure-audit-checklist.md`.
3. Edit the paper.
   - Fix caption mismatches.
   - Add or tighten figrefs in the main text.
   - Move sparse or redundant figures to the appendix.
4. Keep the safeguards in `references/figure-audit-safeguards.md` in scope.

## Outputs
- `audit_out/figures.json`
- `audit_out/images/*.png`

## Notes
- The extractor does not try to infer scientific conclusions.
- It is designed for human or LLM-assisted review after extraction.
- See `references/figure-extraction-output-schema.md` for the JSON structure.
