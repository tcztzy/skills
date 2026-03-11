# Extraction Schema (Public, Professional Intel)

Use this schema to normalize what you read so you can compare teams, rank leads, and cite evidence cleanly.

## Core principles

- Prefer facts you can cite with a URL + date.
- Separate “claims” (what a source says) from “inferences” (your interpretation).
- Do not record private or sensitive personal data; keep it professional.

## Minimal JSON shape (suggested)

```json
{
  "bundle": {
    "id": "",
    "created_at": "",
    "source_notes": ""
  },
  "target": {
    "company": "",
    "role_type": "",
    "level": "",
    "focus_keywords": [],
    "constraints": {
      "location": "",
      "remote_ok": null,
      "visa": ""
    }
  },
  "artifacts": [
    {
      "source_type": "official_req | leader_post | recruiter_post | blog | talk | repo | paper | other",
      "title": "",
      "url": "",
      "published_at": "",
      "author_name": "",
      "author_role": "",
      "author_org_or_team": "",
      "extracted_claims": [
        {
          "claim": "",
          "evidence_excerpt": ""
        }
      ],
      "tags": ["hiring", "infra", "llm", "security"]
    }
  ],
  "candidates": [
    {
      "team_or_group": "",
      "product_area": "",
      "people": [
        {
          "name": "",
          "role": "",
          "public_profile_url": "",
          "why_relevant": "",
          "evidence_urls": []
        }
      ],
      "hiring_leads": [
        {
          "role_title": "",
          "level": "",
          "location": "",
          "apply_url": "",
          "signal_summary": "",
          "evidence_urls": [],
          "score": {
            "authority": 0,
            "recency": 0,
            "specificity": 0,
            "corroboration": 0,
            "penalty": 0,
            "total": 0
          },
          "confidence": "high | medium | low",
          "next_step": ""
        }
      ],
      "team_priorities": [
        {
          "priority": "",
          "evidence_urls": [],
          "notes": ""
        }
      ],
      "tech_stack_signals": {
        "languages": [],
        "frameworks": [],
        "infra": [],
        "data": []
      },
      "open_questions": []
    }
  ],
  "notes": {
    "uncertainties": [],
    "do_not_do": []
  }
}
```

## Claim vs inference (write explicitly)

- Claim example: “The post says the team is hiring an ‘inference engineer’ in SF.”
- Inference example: “Given their recent latency talk + infra repos, the interview likely includes performance debugging.”
