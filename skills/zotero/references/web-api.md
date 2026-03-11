# Zotero Web API notes

Use these notes as a quick reminder. Refer to the Zotero Web API docs for full details.

## Key facts

- Base URL: https://api.zotero.org
- API versioning: set "Zotero-API-Version: 3" (recommended) or use the "v=3" URL parameter.
- Authentication: provide an API key via "Zotero-API-Key: <key>" or "Authorization: Bearer <key>".
- Library scope: use /users/<userID>/... for user libraries and /groups/<groupID>/... for group libraries.
- Exports and citations: use the "format" and "include" parameters; common formats include BibTeX, BibLaTeX, RIS, CSL JSON, and CSV.

## Links

- https://www.zotero.org/support/dev/web_api/v3/start
- https://www.zotero.org/support/dev/web_api/v3/basics
