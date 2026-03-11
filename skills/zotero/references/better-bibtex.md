# Better BibTeX notes

Use these notes when the user wants a `.bib`/`.biblatex` export that stays synced with a Zotero **collection**.

## Core rule

Treat the exported `.bib` file as a **generated artifact**:

- Don't edit it by hand (changes will be overwritten).
- Make changes in Zotero (items/collections/citation keys), then let Better BibTeX update the export.

## Set up a keep-updated export (recommended)

1) Confirm Better BibTeX is installed (Zotero should show a Better BibTeX preferences tab/menu).
2) Right-click the target collection -> **Export Collection...**
3) Choose format **Better BibTeX** (or **Better BibLaTeX**).
4) Enable **Keep updated**.
5) Choose the output file path (for example a project-local `refs.bib`).

## Manage existing auto-exports

Better BibTeX stores “keep updated” exports as **automatic exports** in Zotero preferences.

- If an export keeps regenerating a file you deleted, remove/disable the export in:
  Zotero settings/preferences -> **Better BibTeX** -> **Automatic exports**

## Citation keys (citekeys)

Better BibTeX assigns citation keys; you can pin/override them for stability.

- To pin a key for an item, put a line like this in the item's **Extra** field:
  `Citation Key: mykey`
- Prefer changing citekeys in Zotero rather than post-processing the exported `.bib`.

## Links

- https://retorque.re/zotero-better-bibtex/exporting/
- https://retorque.re/zotero-better-bibtex/installation/preferences/automatic-export/
- https://retorque.re/zotero-better-bibtex/citing/
- https://github.com/retorquere/zotero-better-bibtex/discussions/2826
