---
name: career-team-intel
description: Proactively research target companies, teams, and hiring decision makers (EM/TL/HM/recruiters) for job seeking using public, explicitly professional sources; interpret hiring-intent signals such as leader "we're hiring" posts, score confidence, and produce a team brief, contact map, outreach messages, and resume alignment. Use when applying to large companies with many teams and you need to determine which team is hiring, what they care about, and how to tailor outreach and interview preparation. Do not deanonymize pseudonymous accounts or infer private life; only use publicly disclosed professional information.
---

# Career Team Intel

Use this skill to turn scattered public signals into a practical, evidence-linked plan for:
- which team(s) to target inside a large company,
- who the likely hiring decision makers are (in their *professional* capacity),
- whether a team is plausibly hiring *now* (and how confident you are),
- what to say (resume bullets + outreach + interview prep) that matches the team's publicly stated priorities.

This workflow is intentionally multi-stage (collect -> extract -> retrieve -> verify -> score -> write), mirroring the reliable parts of multi-stage LLM retrieval/verification pipelines, without doing any identity deanonymization.

Method mapping (adapted safely for career use):
- Extract “micro-signals” from text (team priorities, constraints, hiring intent).
- Retrieve candidates (teams/reqs/decision makers) via broad search, then narrow.
- Verify with primary sources + cross-checking.
- Calibrate confidence with an explicit score (so you don’t overfit to vibes).

## Hard Rules (Non-Negotiable)

- Only use **public** information that is clearly **professional** and **explicitly disclosed** (e.g., LinkedIn job posts, official job reqs, public talks, public GitHub orgs).
- Do **not** link pseudonymous accounts to real identities; do **not** infer private life; do **not** use data brokers/leaks.
- Always record **URLs** and **dates** for every claim; prefer **corroboration** over clever inference.
- If a source is ambiguous (stale post, vague “we’re growing”), treat it as a weak signal and ask for a req/link.
- Write briefs, outreach, and interview-prep materials in professional English unless the user explicitly requests another language.

## Inputs To Ask For (Minimal)

- Target company (or a shortlist).
- Role type + level (e.g., “Research Engineer L5”, “SWE infra senior”).
- Focus keywords (3-10) and “avoid” keywords (optional).
- Constraints: location/timezone, remote/onsite, visa, start date, compensation bands (optional).
- Your strongest 2-3 proof points (projects/papers/metrics) to align messaging.

## Workflow (Public Team/Leader Intel)

### 1) Define a “Query Pack”

- Turn the user inputs into 5-15 search queries combining: company + product + role + focus keywords + (team/org names if known).
- Also add “hiring intent” queries: `we're hiring`, `hiring`, `headcount`, `req`, `join my team`.
- Write the query pack into your notes so it can be re-used.

### 2) Collect Public Artifacts (With Provenance)

- Use the source map in `references/source-map.md` to decide where to look and what to extract.
- For every artifact, capture: source type, URL, author (if any), post date, and the exact hiring/team/tech claims you’ll rely on.
- Prefer primary sources (official job reqs, official blogs, talks, GitHub org repos) over reposts/aggregators.

### 3) Extract Structured Facts (So You Can Compare/Rank)

- Normalize each artifact into the schema in `references/extraction-schema.md`.
- Focus on: team mission, current projects, tech stack, constraints, success metrics, hiring intent, and “how to apply/contact”.
- Treat `extraction.json` as the **source of truth**; the `.md` files are the “view layer” for humans.

### 4) Retrieve Candidate Teams + Decision Makers (Professional Only)

- Build a candidate list of teams and relevant people:
  - Hiring manager / EM / TL / group lead (when explicitly stated).
  - Recruiters *for that org* (when explicitly tied to the req/team).
  - Adjacent ICs who publish team work (good for informational chats, not “please hire me”).
- For each candidate, attach 1-3 evidence links and the extracted facts.

### 5) Verify + Interpret Hiring Signals (Avoid False Positives)

- Use `references/hiring-signals.md` to classify each signal as strong/medium/weak and compute an overall confidence.
- Practical verification rules:
  - If there is a fresh leader post **and** a matching official req, treat as high confidence.
  - If there is only a leader post without a req, treat as medium until you confirm (ask for the req/link).
  - If a post is old, vague, or generic (“always hiring”), treat as weak unless corroborated.
  - If there are credible negative signals (freeze/layoffs), downgrade confidence.

### 6) Produce Outputs (Evidence-Linked)

Generate deliverables using `references/output-templates.md`:
- `team_brief.md`: 1-page summary per target team (what, why now, what success looks like, how you fit).
- `hiring_signals.md`: timeline of signals with dates + confidence.
- `people_map.md`: who to contact, why them, what to ask, and what to send.
- `resume_alignment.md`: team priorities -> your proof points -> proposed resume bullets.
- `outreach_messages.md`: short messages tailored to the evidence (no overfamiliarity).
- `interview_prep.md`: likely topics + your stories aligned to their public work.

## Handling Tricky User Requests (Safety Gate)

- If the user asks you to “find someone’s anonymous account”, “connect a pseudonym to a real person”, “dig up private life”, or “scrape non-public info”, refuse that part and offer the closest safe alternative:
  - Use the person’s publicly disclosed professional channels (LinkedIn, official talks, official GitHub org).
  - Focus on team-level signals and official reqs.

## Optional Helper Script

- Use `scripts/new_intel_bundle.py` to scaffold an output folder with the template files (no web access; just structure).
- Use `scripts/export_tables.py` to export `.csv` tables from one filled bundle for analysis.
- Use `scripts/aggregate_bundles.py` to merge many bundles into one set of `.csv` tables.
- Use `scripts/export_graph.py` to export `graph.json/graph.graphml` for relationship analysis (Gephi/D3).
- Use `scripts/aggregate_graph.py` to merge many bundles into one relationship graph.

## Data Analysis (Make It Easy Later)

- Do **not** plan to parse the narrative `.md` files; they are for reading/sharing.
- Put all structured facts into `extraction.json`, then export analysis-friendly tables:
  - Single bundle -> `scripts/export_tables.py <bundle_dir>`
  - Many bundles -> `scripts/aggregate_bundles.py <root_dir>`
- For graph-based analysis, see `references/graph-analysis.md`.

## References

- `references/source-map.md`: where to look + what to extract per source type.
- `references/hiring-signals.md`: signal taxonomy + scoring + interpretation rules.
- `references/extraction-schema.md`: structured schema (fields + examples).
- `references/output-templates.md`: templates for deliverables (brief, map, outreach, alignment).
- `references/graph-analysis.md`: node/edge types + heuristics for relationship analysis.
