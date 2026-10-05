---
name: latex-to-word
description: Convert LaTeX files to Word with a deterministic preprocessing script and pandoc. Use when producing DOCX from TeX that may contain custom classes, tabularx, resizebox, custom column types, citations, images, or other pandoc compatibility issues.
---

# LaTeX to Word

Preserve the source file. Preprocess to a separate `.tex` file, convert that copy,
and report any constructs that still need manual review.

## Workflow

1. Resolve the source path and intended `.docx` output.
2. Check that `python3` and `pandoc` are available.
3. Inspect the source for bibliography files, image paths, custom macros, complex
   tables, and nonstandard environments.
4. Run the packaged preprocessor from this skill directory:

```bash
python3 scripts/preprocess_latex.py SOURCE.tex --output SOURCE.pandoc.tex
```

Use `--force` only when replacing that intermediate file is safe. The script:

- normalizes nonstandard document classes to `article`
- removes unneeded `tabularx` packages and list configuration
- converts simple `tabularx` (including position options), common column markers,
  balanced `resizebox` wrappers, `path`, and
  `cmidrule` patterns
- reports remaining complex constructs instead of pretending they converted
  cleanly

5. Review the rewrite counts and warnings. Search the intermediate file for any
   reported unsupported constructs before conversion.
6. Run pandoc:

```bash
pandoc SOURCE.pandoc.tex \
  --from=latex \
  --to=docx \
  --standalone \
  --resource-path=SOURCE_DIRECTORY \
  --output=OUTPUT.docx
```

If the document uses BibTeX, add `--citeproc --bibliography=REFERENCES.bib` and the requested
CSL or citation options. Preserve resource paths needed by included images.
7. Confirm that the DOCX exists and is nonempty. Inspect pandoc warnings and, when
   practical, open or render the result to check headings, equations, figures,
   citations, and tables.
8. Remove the intermediate `.pandoc.tex` only after a successful conversion and
   only if the user does not need it for debugging.

## Safety and output rules

- Never modify the original `.tex`.
- Do not overwrite an existing DOCX without permission; choose a new output name.
- Preserve `\newcommand` and custom column definitions unless a specific incompatibility is proven.
- Complex `tabularx` column specifications are preserved and reported for review.
  Common markers are approximations: `X`/`Y`/`L`/`P` become left aligned,
  `C` becomes centered, and `R` becomes right aligned; verify the result.
- Treat `multirow`, `makecell`, `tabulary`, `supertabular`, complex merged cells,
  and mixed-language typography as manual-review risks.
- Report the output path, file size, pandoc warnings, and remaining cleanup.
