---
name: latex-to-word
description: "Convert LaTeX (.tex) files to Word (.docx) using an automated preprocessing pipeline that resolves common pandoc incompatibilities such as custom commands, tabularx, and resizebox, minimizing manual cleanup afterward."
---

# LaTeX to Word (.docx) Conversion

Convert the user-specified `.tex` file to `.docx` using a preprocessing plus pandoc pipeline that preserves structure as much as possible and minimizes manual cleanup.

## Input

- `$ARGUMENTS`: path to the `.tex` file to convert, either relative or absolute

## Preflight Checks

1. Confirm that `pandoc` is installed by running `which pandoc`. If it is missing, ask the user to install it and retry.
2. Confirm that `python3` or `python` is available.
3. Confirm that the specified `.tex` file exists and is readable.

## Workflow

### Step 1: Analyze the source file

Read the full `.tex` file and identify the following pandoc-incompatible elements:

| Category | Detection method | Example |
|------|----------|------|
| Nonstandard document class | any class other than `article`, `report`, or `book` on the `\documentclass` line | `ctexart`, `IEEEtran` |
| Custom column types | `\newcolumntype{X}` | `\newcolumntype{Y}{...}` |
| `tabularx` environment | `\begin{tabularx}` | convert to `tabular` |
| `\resizebox` wrapper | `\resizebox{\textwidth}{!}{` or `\resizebox{\textwidth}{!}{%` | remove the wrapper and support both forms |
| `\allowbreak` | direct search | remove |
| `\ignorespaces` | direct search | remove |
| `\cmidrule(lr)` | `\cmidrule` followed by `(...)` trimming parameters | remove the trimming parameters |
| `\path{...}` | inside `\newcommand` definitions or body text | convert to `\texttt{...}` |
| Unnecessary formatting commands | `\setlist`, `\captionsetup`, `\hypersetup` | remove |
| Enumerate optional parameters | `\begin{enumerate}[label=...]` | simplify |
| `\renewcommand\tabularxcolumn` | direct search | remove |

Record every issue you find so the preprocessing script can be generated accurately.

### Step 2: Generate the preprocessing Python script

Generate `_preprocess_for_pandoc.py` in the same directory as the source file. The script must:

**Required general rules:**

```python
import re, os

src = r"<absolute source file path>"
dst = r"<same directory>/_for_pandoc.tex"

with open(src, 'r', encoding='utf-8') as f:
    content = f.read()

# === General rules ===

# 1. Replace a nonstandard document class with article
content = re.sub(
    r'\\documentclass(\[[^\]]*\])\{[^}]+\}',
    r'\\documentclass\1{article}',
    content
)

# 2. Remove \newcolumntype definition lines
content = re.sub(r'\\newcolumntype\{.\}.*\n', '', content)

# 3. Remove \renewcommand\tabularxcolumn and any directly related comment line above it
content = re.sub(
    r'(%.*tabularx.*\n)?\\renewcommand\\tabularxcolumn.*\n',
    '', content
)

# 4. Replace custom column markers such as C{...} with c inside column specs
content = re.sub(r'C\{[^}]+\}', 'c', content)

# 5. Convert tabularx to tabular after simplifying custom column markers
def simplify_tabularx(m):
    colspec = m.group(1)
    # Add more custom-column replacements here if the analysis found them
    colspec = colspec.replace('Y', 'l').replace('X', 'l')
    return r'\begin{tabular}{' + colspec + '}'

content = re.sub(
    r'\\begin\{tabularx\}\{[^}]+\}\{([^}]+)\}',
    simplify_tabularx, content
)
content = content.replace(r'\end{tabularx}', r'\end{tabular}')

# 6. Remove \resizebox{...}{!}{ wrappers, supporting forms with and without %
content = re.sub(r'\\resizebox\{[^}]+\}\{[^}]+\}\{%?\s*\n', '', content)
# Fix matching extra closing braces
# Pattern A: \end{tabular}} -> \end{tabular}
content = re.sub(r'(\\end\{tabular\})\}', r'\1', content)
# Pattern B: \end{tabular}\n    }\n -> \end{tabular}\n
content = re.sub(r'(\\end\{tabular\})\s*\n\s*\}', r'\1', content)

# 7. Remove \allowbreak
content = content.replace(r'\allowbreak', '')

# 8. Remove \ignorespaces
content = content.replace(r'\ignorespaces', '')

# 9. Convert \path{...} to \texttt{...} in both body text and \newcommand definitions
content = re.sub(r'\\path\{([^}]*)\}', r'\\texttt{\1}', content)

# 10. Remove formatting configuration commands
content = re.sub(r'\\setlist\{[^}]*\}', '', content)
content = re.sub(r'\\captionsetup\{[^}]*\}', '', content)
content = re.sub(r'\\hypersetup\{[^}]*\}', '', content)

# 11. Remove packages that are no longer needed
for pkg in ['tabularx', 'enumitem']:
    content = content.replace(r'\usepackage{' + pkg + '}', '')

# 12. Simplify enumerate environments that use optional parameters
content = re.sub(
    r'\\begin\{enumerate\}\[[^\]]+\]',
    r'\\begin{enumerate}', content
)

# 13. Simplify \cmidrule trimming parameters: \cmidrule(lr){2-3} -> \cmidrule{2-3}
content = re.sub(r'\\cmidrule\([^)]*\)', r'\\cmidrule', content)

# 14. Remove standalone \small lines
content = re.sub(r'\n\\small\n', '\n', content)

# 15. Collapse repeated blank lines
content = re.sub(r'\n{3,}', '\n\n', content)

with open(dst, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"Done: {dst}")
print(f"Size: {len(content)} chars")
```

**Add these only when the analysis requires them:**

- If you find the pattern `\href{...}{\path{...}}`, replace the entire `\newcommand` definition with a pandoc-friendly version.
- If you find other custom column markers such as `L`, `R`, or `P{}`, add the corresponding replacements inside `simplify_tabularx`.
- If you find `\makecell`, keep it. Pandoc usually ignores it without failing.
- If you find `\multirow`, keep it. Pandoc has basic support, but complex merged cells may still need manual cleanup.
- If you find other table environments such as `tabulary` or `supertabular`, treat them similarly to `tabularx`.
- If the file uses BibTeX citations through `\cite`, decide whether `--bibliography` should also be passed to pandoc.

### Step 3: Run the preprocessing script

```bash
cd "<source directory>"
python _preprocess_for_pandoc.py
```

Confirm that `_for_pandoc.tex` was created, then quickly check:
- there are no remaining `tabularx`, `resizebox`, or `\allowbreak` fragments
- the `\begin{tabular}` column spec no longer contains custom column markers

### Step 4: Run the pandoc conversion

```bash
pandoc _for_pandoc.tex \
  -o "<output filename>.docx" \
  --from latex \
  --to docx \
  --resource-path="<source directory>" \
  --standalone
```

Output filename rule: use the same basename as the source file and change only the extension to `.docx`.
If that `.docx` file already exists and is locked, causing `Permission denied`, append `_new` to the basename.

### Step 5: Clean up temporary files

Delete:
- `_for_pandoc.tex`
- `_preprocess_for_pandoc.py`

### Step 6: Report the result

Report back to the user with:
1. the output file path and size
2. any pandoc warnings, if present
3. content that may still require manual cleanup:
   - table formatting such as column widths or alignment
   - tables that rely on `\multirow`
   - mixed-language typography
   - heading style hierarchy
   - complex multi-line equations

## Key Notes

- **Preserve `\newcommand` definitions**: pandoc expands most `\newcommand` definitions correctly, so do not delete or manually inline them without a clear reason.
- **Image paths**: set `--resource-path` to the source file directory so pandoc can resolve referenced images automatically.
- **Encoding**: always read and write as UTF-8.
- **Do not modify the source file**: all preprocessing must happen on the `_for_pandoc.tex` copy.
