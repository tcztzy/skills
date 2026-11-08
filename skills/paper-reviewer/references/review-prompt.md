# Review request packet

Build the request offline from the installed skill directory:

```sh
python scripts/close_reading_audit.py packet --request request.json --out review-packet.json
```

`request.json` supplies the following data (replace the example values):

```json
{
  "scope": "targeted",
  "target": "Venue, article type, stage, and agreed acceptance",
  "controls": [],
  "evidence": "Inspected passages, visual evidence, findings, and completed ledger"
}
```

Add `"issn": "2352-7110"` for a bundled journal profile. Supply actual evidence
content; an inaccessible local path cannot stand in for the material.

The command embeds SKILL.md and the canonical JSON schema verbatim in
`instructions`; the request and requested journal profile travel as serialized
`input` data. It resolves
files from its own installed location, rejects missing sources and invalid scopes,
and refuses to overwrite an output. The packet is usable without filesystem tools;
references to further evidence still require that evidence in the request.

Deliver the complete generated packet through an approved external executor after
separate user approval. This command makes no model call and grants no approval.
