# Graph / Relationship Analysis (Optional)

Use graph outputs when you want to:
- see who connects to which team(s) and which evidence,
- avoid missing the "right person to message",
- rank candidates by evidence/connectedness across many bundles.

This is **professional-intel only**. Do not attempt identity linking beyond what the person explicitly discloses publicly.

## Node types

- `company`: a company (one per bundle target)
- `team`: a team or group inside a company
- `person`: a decision maker / recruiter / IC (professional identity)
- `artifact`: a public source (req, post, blog, talk, repo, paper)
- `hiring_lead`: a specific hiring opportunity signal (one per lead in `hiring_leads`)
- `priority`: a team priority item (one per entry in `team_priorities`)
- `keyword`: tags/tech/keywords extracted from artifacts + stack signals

## Edge types (directed)

- `company_has_team`: company -> team
- `team_has_person`: team -> person (role in edge label)
- `person_mentions_hiring`: person -> hiring_lead (when the lead is tied to that person)
- `lead_supported_by`: hiring_lead -> artifact (evidence URL)
- `team_has_priority`: team -> priority
- `team_uses_keyword`: team -> keyword (tech/keywords)
- `artifact_tagged`: artifact -> keyword
- `artifact_authored_by`: artifact -> person (when author is known)

## Interpretation heuristics

- High-confidence lead clusters: a `hiring_lead` node connected to both (a) `artifact` = official req and (b) `artifact` = leader/recruiter post, plus a `person` node with authority.
- Outreach targets: `person` nodes with many edges to strong leads + recent artifacts tend to be best first contacts.
- Ambiguity flags: nodes with missing URLs, missing dates, or only weak signals should be treated as “needs verification”.

## Export formats

The scripts can export:
- `graph.json` (nodes/edges for programmatic analysis)
- `graph.graphml` (import into Gephi)
- `rank_people.csv` (quick ranking of who to contact)
