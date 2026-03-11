---
name: zotero
description: Capture (Zotero Connector), manage, search, and export Zotero libraries and citations using Zotero desktop + Better BibTeX, the Zotero Web API, a local Zotero data directory, or user-provided export files. Use when tasks mention Zotero, Zotero Connector, Better BibTeX, collections, BibTeX/BibLaTeX auto-export (keep updated), citations, bibliographies, or reference management.
---

# Zotero

## Principles

- Prefer read-only operations unless the user explicitly requests writes (edits, deletes, moves, tagging).
- Ask for the minimum credentials or files needed to complete the task.
- Confirm output format and scope before exporting or formatting citations.
- Treat Better BibTeX auto-export `.bib` files as generated artifacts: do not edit by hand. Adjust Zotero items/collections/citekeys and let Better BibTeX update the export.

## Quick intake

Ask the user:

1) Goal: capture from websites, clean/dedupe, analyze, or export citations / `.bib`?
2) Access method: Zotero desktop via MCP server (zotero), Web API, local Zotero data directory, or exported file.
3) Scope: user library or group library; collections or whole library.
4) For website capture: which URLs/DOIs, and is Zotero Connector installed?
5) For Better BibTeX: which collection should auto-export, and where is the exported `.bib` file located?
6) For writes: confirm the exact changes and get explicit approval.

## Website capture workflow (Zotero Connector)

Use this when the user wants to save papers directly from publisher pages (for example Nature) into Zotero.

1) Confirm Zotero desktop is installed and running.
2) Confirm Zotero Connector is installed in the browser.
3) Open the article page and click the Zotero Connector button to save to Zotero.
4) If prompted, pick the destination collection; then confirm the item appears in Zotero.

Notes:
- If Zotero desktop is closed, the Connector can save to zotero.org and later sync to the desktop app; attachment behavior depends on Connector settings (see references/connector.md).
- For pages listing multiple items, the Connector shows a folder icon so the user can select which items to save.

## Browser automation (optional)

If the user needs to capture many items from websites:

- Prefer Zotero Connector for high-fidelity capture, but expect a human click unless you have an explicit, interactive browser automation setup.
- If automating is required, use a real browser automation tool (for example Playwright) to:
  1) Visit each URL (login if needed)
  2) Download citation files (RIS/BibTeX) or extract identifiers (DOI/PMID)
  3) Import into Zotero (or use Zotero "Add Item(s) by Identifier")

## Better BibTeX workflow (collection-scoped, keep-updated exports)

Use this when the user wants a `.bib`/`.biblatex` export that stays in sync with a Zotero collection.

1) Confirm the Better BibTeX plugin is installed (Zotero should show a Better BibTeX preferences tab/menu).
2) In Zotero, right-click the target collection -> Export Collection...
3) Choose format "Better BibTeX" (or "Better BibLaTeX"), enable "Keep updated", and choose the output path.
4) To change what appears in the export, change Zotero (collection membership, item metadata, tags, citation keys). Do not edit the exported file directly.
5) To review/remove an auto-export, open Zotero settings/preferences -> Better BibTeX -> Automatic exports (see references/better-bibtex.md).

## MCP server workflow

1) Confirm the MCP server is configured and running (name: zotero).
2) If using local mode, ask the user to enable Zotero local API and keep Zotero running.
3) Prefer MCP tools for search, metadata, and full text, then summarize results.

## Web API workflow

1) Request a Zotero API key plus the user or group library ID and confirm the library is accessible.
2) Use the Web API base URL and versioning guidance in references/web-api.md.
3) List collections or items first to validate access, then filter by query, tag, or collection.
4) For exports or citations, use the API export and citation formats from references/web-api.md and confirm the citation style.

## Local data directory workflow

1) Ask the user to locate the data directory via Zotero settings (see references/data-directory.md).
2) Request a copy of zotero.sqlite (read-only) if analysis is needed; avoid writing to the live database.
3) If attachments are needed, request the storage/ subfolder or specific item keys.

## Export file workflow

1) Ask for the export file format (for example BibTeX, RIS, CSL JSON) and the file itself.
2) Parse the file and proceed with analysis, conversion, or citation formatting.
3) If the file is a Better BibTeX auto-export, do not edit it directly; change Zotero and let the export update instead.

## Example

Input:
"Keep a BibTeX export for my Zotero collection 'My Paper' synced to `refs.bib`, and update the citekeys for 3 items."

Actions:
1) Confirm Better BibTeX is installed and identify the target collection.
2) Create a "Keep updated" export for that collection to `refs.bib`.
3) For the 3 items, set/pin citation keys in Zotero (see references/better-bibtex.md) and confirm the export updates.

Output:
- The Zotero collection continuously auto-exports to `refs.bib`.
- Citekey changes are made in Zotero (not by editing `refs.bib`).

## Output checklist

- Summarize the access method and scope used.
- Provide counts (items or collections) when feasible.
- State the export or citation format and any style used.
- If a Better BibTeX auto-export is involved, name the Zotero collection bound to the exported file and the file path.
- If changes were requested, restate what was changed and what remains.
