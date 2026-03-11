# Public Source Map (What To Collect + What To Extract)

Goal: find teams that match the user's focus and have credible signs of hiring, using only public, explicitly professional information.

Always capture: (1) URL, (2) date, (3) who said it (if any), (4) the exact claim you rely on.

## Highest-signal sources (start here)

### Official job req (company careers site)
- Extract: req ID, role title/level, org/team (if stated), location/remote, core responsibilities, must-haves, nice-to-haves, posted/updated date, application link.
- Interpretation: strongest evidence that headcount exists; team name may still be missing or generic.

### Public "we're hiring" post by the team lead / hiring manager (LinkedIn/X/etc.)
- Extract: role + level + location + how to apply + time posted + whether they mention a req/link.
- Interpretation: strong intent signal, but still verify with an official req when possible.

### Recruiter post explicitly tied to an org/team/req
- Extract: org/team, role, location, req link/ID, contact method.
- Interpretation: strong; recruiters can be noisy, so keep it tied to a specific req.

## Team-understanding sources (what the team cares about)

### Engineering / product / research blog posts
- Extract: problem domain, constraints (latency/cost/privacy/reliability), success metrics, tech stack clues, authors + their roles/teams (if disclosed), date.
- Interpretation: great for tailoring resume bullets and outreach angles; not a hiring signal by itself.

### Public talks (conference videos, slides, podcasts)
- Extract: topic, “what we shipped / what we’re building”, trade-offs, speaker role/team (only if explicitly stated), date.
- Interpretation: shows current priorities and decision criteria; useful for interview prep.

### Public open-source repos (GitHub orgs)
- Extract: active repos, languages/tools, recent commits/releases, open issues, maintainers/reviewers (by their public profile), “CONTRIBUTING” norms.
- Interpretation: reveals stack + working style; can be used to propose a small, relevant contribution (optional).

### Papers / arXiv / conference proceedings (research-heavy teams)
- Extract: topics, keywords, author affiliations, code/data links, recency, repeated coauthor clusters (as *research-group* signals, not identity linking).
- Interpretation: map to subgroups/labs; useful for PhD/MS candidates.

## Low-signal / noisy sources (use carefully)

### Job board aggregators / reposts
- Extract: original source link if present, posted date, duplicates.
- Interpretation: often stale or duplicated; treat as “pointer only” until you find the official req.

### General employee posts (not HM/EM/TL)
- Extract: what they explicitly say (e.g., “my team is hiring, talk to X”), date.
- Interpretation: medium signal at best unless tied to an official req.

## Sources to avoid

- Anything that attempts to deanonymize pseudonyms, scrape private profiles, or aggregate personal data without consent.
- “Leaked” headcount spreadsheets, internal org charts, paid data-broker dossiers.
- Content behind paywalls/ToS restrictions that require circumvention.

## Minimal collection checklist (per target team)

- 1-2 official req links (or a note that none could be found yet).
- 2-5 artifacts showing current priorities (blog/talk/repo/paper).
- 1-3 hiring intent artifacts (leader/recruiter post) with dates.
- A short “unknowns” list to validate in outreach (team name, level, location, interview loop).
