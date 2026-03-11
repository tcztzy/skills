from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple


def _join(values: Any) -> str:
    if values is None:
        return ""
    if isinstance(values, (list, tuple)):
        return ";".join(str(v) for v in values if v not in (None, ""))
    return str(values)


def load_extraction(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def bundle_meta(data: Dict[str, Any], bundle_dir: Path) -> Dict[str, str]:
    b = (data.get("bundle") or {}) if isinstance(data.get("bundle"), dict) else {}
    t = (data.get("target") or {}) if isinstance(data.get("target"), dict) else {}
    return {
        "bundle_id": str(b.get("id") or bundle_dir.name),
        "bundle_created_at": str(b.get("created_at") or ""),
        "company": str(t.get("company") or ""),
        "bundle_path": str(bundle_dir),
    }


TABLE_FIELDS: Dict[str, List[str]] = {
    "artifacts": [
        "bundle_id",
        "bundle_created_at",
        "company",
        "bundle_path",
        "artifact_index",
        "source_type",
        "published_at",
        "title",
        "url",
        "author_name",
        "author_role",
        "author_org_or_team",
        "tags",
        "claim_count",
    ],
    "claims": [
        "bundle_id",
        "company",
        "bundle_path",
        "artifact_index",
        "claim_index",
        "artifact_url",
        "claim",
        "evidence_excerpt",
    ],
    "candidates": [
        "bundle_id",
        "company",
        "bundle_path",
        "candidate_index",
        "team_or_group",
        "product_area",
        "open_questions",
        "tech_languages",
        "tech_frameworks",
        "tech_infra",
        "tech_data",
    ],
    "people": [
        "bundle_id",
        "company",
        "bundle_path",
        "candidate_index",
        "team_or_group",
        "person_index",
        "name",
        "role",
        "public_profile_url",
        "why_relevant",
        "evidence_urls",
    ],
    "hiring_leads": [
        "bundle_id",
        "company",
        "bundle_path",
        "candidate_index",
        "team_or_group",
        "lead_index",
        "role_title",
        "level",
        "location",
        "apply_url",
        "signal_summary",
        "evidence_urls",
        "score_authority",
        "score_recency",
        "score_specificity",
        "score_corroboration",
        "score_penalty",
        "score_total",
        "confidence",
        "next_step",
    ],
    "priorities": [
        "bundle_id",
        "company",
        "bundle_path",
        "candidate_index",
        "team_or_group",
        "priority_index",
        "priority",
        "notes",
        "evidence_urls",
    ],
}


def rows_from_extraction(data: Dict[str, Any], bundle_dir: Path) -> Dict[str, List[Dict[str, str]]]:
    meta = bundle_meta(data, bundle_dir)

    artifacts_rows: List[Dict[str, str]] = []
    claims_rows: List[Dict[str, str]] = []
    candidates_rows: List[Dict[str, str]] = []
    people_rows: List[Dict[str, str]] = []
    leads_rows: List[Dict[str, str]] = []
    priorities_rows: List[Dict[str, str]] = []

    artifacts = data.get("artifacts") or []
    if isinstance(artifacts, list):
        for ai, a in enumerate(artifacts):
            if not isinstance(a, dict):
                continue
            claims = a.get("extracted_claims") or []
            artifacts_rows.append(
                {
                    **meta,
                    "artifact_index": str(ai),
                    "source_type": str(a.get("source_type") or ""),
                    "published_at": str(a.get("published_at") or ""),
                    "title": str(a.get("title") or ""),
                    "url": str(a.get("url") or ""),
                    "author_name": str(a.get("author_name") or ""),
                    "author_role": str(a.get("author_role") or ""),
                    "author_org_or_team": str(a.get("author_org_or_team") or ""),
                    "tags": _join(a.get("tags") or []),
                    "claim_count": str(len(claims)) if isinstance(claims, list) else "0",
                }
            )

            if isinstance(claims, list):
                for ci, c in enumerate(claims):
                    if not isinstance(c, dict):
                        continue
                    claims_rows.append(
                        {
                            "bundle_id": meta["bundle_id"],
                            "company": meta["company"],
                            "bundle_path": meta["bundle_path"],
                            "artifact_index": str(ai),
                            "claim_index": str(ci),
                            "artifact_url": str(a.get("url") or ""),
                            "claim": str(c.get("claim") or ""),
                            "evidence_excerpt": str(c.get("evidence_excerpt") or ""),
                        }
                    )

    candidates = data.get("candidates") or []
    if isinstance(candidates, list):
        for ti, t in enumerate(candidates):
            if not isinstance(t, dict):
                continue
            team = str(t.get("team_or_group") or "")

            tech = t.get("tech_stack_signals") or {}
            tech = tech if isinstance(tech, dict) else {}

            candidates_rows.append(
                {
                    "bundle_id": meta["bundle_id"],
                    "company": meta["company"],
                    "bundle_path": meta["bundle_path"],
                    "candidate_index": str(ti),
                    "team_or_group": team,
                    "product_area": str(t.get("product_area") or ""),
                    "open_questions": _join(t.get("open_questions") or []),
                    "tech_languages": _join(tech.get("languages") or []),
                    "tech_frameworks": _join(tech.get("frameworks") or []),
                    "tech_infra": _join(tech.get("infra") or []),
                    "tech_data": _join(tech.get("data") or []),
                }
            )

            people = t.get("people") or []
            if isinstance(people, list):
                for pi, p in enumerate(people):
                    if not isinstance(p, dict):
                        continue
                    people_rows.append(
                        {
                            "bundle_id": meta["bundle_id"],
                            "company": meta["company"],
                            "bundle_path": meta["bundle_path"],
                            "candidate_index": str(ti),
                            "team_or_group": team,
                            "person_index": str(pi),
                            "name": str(p.get("name") or ""),
                            "role": str(p.get("role") or ""),
                            "public_profile_url": str(p.get("public_profile_url") or ""),
                            "why_relevant": str(p.get("why_relevant") or ""),
                            "evidence_urls": _join(p.get("evidence_urls") or []),
                        }
                    )

            leads = t.get("hiring_leads") or []
            if isinstance(leads, list):
                for li, l in enumerate(leads):
                    if not isinstance(l, dict):
                        continue
                    s = l.get("score") or {}
                    s = s if isinstance(s, dict) else {}
                    leads_rows.append(
                        {
                            "bundle_id": meta["bundle_id"],
                            "company": meta["company"],
                            "bundle_path": meta["bundle_path"],
                            "candidate_index": str(ti),
                            "team_or_group": team,
                            "lead_index": str(li),
                            "role_title": str(l.get("role_title") or ""),
                            "level": str(l.get("level") or ""),
                            "location": str(l.get("location") or ""),
                            "apply_url": str(l.get("apply_url") or ""),
                            "signal_summary": str(l.get("signal_summary") or ""),
                            "evidence_urls": _join(l.get("evidence_urls") or []),
                            "score_authority": str(s.get("authority") or 0),
                            "score_recency": str(s.get("recency") or 0),
                            "score_specificity": str(s.get("specificity") or 0),
                            "score_corroboration": str(s.get("corroboration") or 0),
                            "score_penalty": str(s.get("penalty") or 0),
                            "score_total": str(s.get("total") or 0),
                            "confidence": str(l.get("confidence") or ""),
                            "next_step": str(l.get("next_step") or ""),
                        }
                    )

            priorities = t.get("team_priorities") or []
            if isinstance(priorities, list):
                for pri, pr in enumerate(priorities):
                    if not isinstance(pr, dict):
                        continue
                    priorities_rows.append(
                        {
                            "bundle_id": meta["bundle_id"],
                            "company": meta["company"],
                            "bundle_path": meta["bundle_path"],
                            "candidate_index": str(ti),
                            "team_or_group": team,
                            "priority_index": str(pri),
                            "priority": str(pr.get("priority") or ""),
                            "notes": str(pr.get("notes") or ""),
                            "evidence_urls": _join(pr.get("evidence_urls") or []),
                        }
                    )

    return {
        "artifacts": artifacts_rows,
        "claims": claims_rows,
        "candidates": candidates_rows,
        "people": people_rows,
        "hiring_leads": leads_rows,
        "priorities": priorities_rows,
    }


def write_csv(path: Path, fieldnames: List[str], rows: Iterable[Dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({k: ("" if r.get(k) is None else r.get(k, "")) for k in fieldnames})

