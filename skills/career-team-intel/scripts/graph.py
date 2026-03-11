from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


def _as_str(x: Any) -> str:
    return "" if x is None else str(x)


def _join(values: Any) -> str:
    if values is None:
        return ""
    if isinstance(values, (list, tuple)):
        return ";".join(_as_str(v) for v in values if v not in (None, ""))
    return _as_str(values)


def _xml_escape(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )


@dataclass
class Node:
    id: str
    type: str
    label: str
    attrs: Dict[str, str]


@dataclass
class Edge:
    source: str
    target: str
    type: str
    label: str = ""
    attrs: Dict[str, str] | None = None


def load_extraction(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _bundle_meta(data: Dict[str, Any], bundle_dir: Path) -> Dict[str, str]:
    b = data.get("bundle") if isinstance(data.get("bundle"), dict) else {}
    t = data.get("target") if isinstance(data.get("target"), dict) else {}
    return {
        "bundle_id": _as_str((b or {}).get("id") or bundle_dir.name),
        "company": _as_str((t or {}).get("company") or ""),
        "bundle_path": str(bundle_dir),
    }


def _company_id(company: str) -> str:
    return f"company:{company}" if company else "company:unknown"


def _team_id(company: str, team: str, fallback: str) -> str:
    team = team.strip() if isinstance(team, str) else ""
    if team:
        return f"team:{company}|{team}"
    return f"team:{company}|{fallback}"


def _person_id(profile_url: str, company: str, team: str, name: str, role: str) -> str:
    if profile_url:
        return f"person:{profile_url}"
    # Fall back to a stable-ish composite key inside the bundle.
    return f"person:{company}|{team}|{name}|{role}".strip("|")


def _artifact_id(url: str, bundle_id: str, idx: int) -> str:
    return f"artifact:{url}" if url else f"artifact:{bundle_id}|{idx}"


def _lead_id(bundle_id: str, cand_idx: int, lead_idx: int) -> str:
    return f"lead:{bundle_id}|{cand_idx}|{lead_idx}"


def _priority_id(bundle_id: str, cand_idx: int, pri_idx: int) -> str:
    return f"priority:{bundle_id}|{cand_idx}|{pri_idx}"


def _kw_id(text: str) -> str:
    return f"kw:{text}"


def graph_from_extraction(data: Dict[str, Any], bundle_dir: Path) -> Tuple[List[Node], List[Edge]]:
    meta = _bundle_meta(data, bundle_dir)
    company = meta["company"]
    bundle_id = meta["bundle_id"]

    nodes: Dict[str, Node] = {}
    edges: List[Edge] = []

    def add_node(n: Node) -> None:
        if n.id in nodes:
            # Merge attrs non-destructively.
            for k, v in n.attrs.items():
                if k not in nodes[n.id].attrs or not nodes[n.id].attrs[k]:
                    nodes[n.id].attrs[k] = v
            return
        nodes[n.id] = n

    def add_edge(e: Edge) -> None:
        edges.append(e)

    # Company node.
    cid = _company_id(company)
    add_node(Node(id=cid, type="company", label=company or "Unknown Company", attrs={**meta}))

    # Artifacts (+ keywords from tags).
    artifacts = data.get("artifacts") or []
    if isinstance(artifacts, list):
        for ai, a in enumerate(artifacts):
            if not isinstance(a, dict):
                continue
            url = _as_str(a.get("url") or "")
            aid = _artifact_id(url, bundle_id, ai)
            st = _as_str(a.get("source_type") or "")
            published_at = _as_str(a.get("published_at") or "")
            title = _as_str(a.get("title") or "") or url or f"artifact {ai}"
            add_node(
                Node(
                    id=aid,
                    type="artifact",
                    label=title,
                    attrs={
                        **meta,
                        "source_type": st,
                        "url": url,
                        "published_at": published_at,
                        "author_name": _as_str(a.get("author_name") or ""),
                        "author_role": _as_str(a.get("author_role") or ""),
                        "author_org_or_team": _as_str(a.get("author_org_or_team") or ""),
                    },
                )
            )

            # Tag/keyword nodes.
            tags = a.get("tags") or []
            if isinstance(tags, list):
                for tag in tags:
                    tag_s = _as_str(tag).strip()
                    if not tag_s:
                        continue
                    kid = _kw_id(tag_s)
                    add_node(Node(id=kid, type="keyword", label=tag_s, attrs={}))
                    add_edge(Edge(source=aid, target=kid, type="artifact_tagged"))

            # Optional: connect artifact to person via author fields (no deanonymization).
            author_name = _as_str(a.get("author_name") or "").strip()
            author_role = _as_str(a.get("author_role") or "").strip()
            author_team = _as_str(a.get("author_org_or_team") or "").strip()
            if author_name:
                pid = _person_id("", company, author_team, author_name, author_role)
                add_node(
                    Node(
                        id=pid,
                        type="person",
                        label=author_name,
                        attrs={
                            **meta,
                            "name": author_name,
                            "role": author_role,
                            "team_hint": author_team,
                            "public_profile_url": "",
                        },
                    )
                )
                add_edge(Edge(source=aid, target=pid, type="artifact_authored_by"))

    # Candidate teams + people + leads + priorities + tech keywords.
    candidates = data.get("candidates") or []
    if isinstance(candidates, list):
        for ti, t in enumerate(candidates):
            if not isinstance(t, dict):
                continue
            team_name = _as_str(t.get("team_or_group") or "").strip()
            tid = _team_id(company, team_name, fallback=f"candidate-{ti}")
            add_node(
                Node(
                    id=tid,
                    type="team",
                    label=team_name or f"Candidate Team {ti}",
                    attrs={**meta, "product_area": _as_str(t.get("product_area") or "")},
                )
            )
            add_edge(Edge(source=cid, target=tid, type="company_has_team"))

            # People
            people = t.get("people") or []
            if isinstance(people, list):
                for pi, p in enumerate(people):
                    if not isinstance(p, dict):
                        continue
                    name = _as_str(p.get("name") or "").strip()
                    role = _as_str(p.get("role") or "").strip()
                    profile = _as_str(p.get("public_profile_url") or "").strip()
                    if not name and not profile:
                        continue
                    pid = _person_id(profile, company, team_name, name, role)
                    add_node(
                        Node(
                            id=pid,
                            type="person",
                            label=name or profile,
                            attrs={
                                **meta,
                                "name": name,
                                "role": role,
                                "public_profile_url": profile,
                                "why_relevant": _as_str(p.get("why_relevant") or ""),
                                "evidence_urls": _join(p.get("evidence_urls") or []),
                            },
                        )
                    )
                    add_edge(Edge(source=tid, target=pid, type="team_has_person", label=role))

            # Hiring leads
            leads = t.get("hiring_leads") or []
            if isinstance(leads, list):
                for li, l in enumerate(leads):
                    if not isinstance(l, dict):
                        continue
                    lid = _lead_id(bundle_id, ti, li)
                    role_title = _as_str(l.get("role_title") or "")
                    conf = _as_str(l.get("confidence") or "")
                    add_node(
                        Node(
                            id=lid,
                            type="hiring_lead",
                            label=role_title or f"hiring lead {li}",
                            attrs={
                                **meta,
                                "team_or_group": team_name,
                                "role_title": role_title,
                                "level": _as_str(l.get("level") or ""),
                                "location": _as_str(l.get("location") or ""),
                                "apply_url": _as_str(l.get("apply_url") or ""),
                                "confidence": conf,
                                "signal_summary": _as_str(l.get("signal_summary") or ""),
                                "evidence_urls": _join(l.get("evidence_urls") or []),
                                "next_step": _as_str(l.get("next_step") or ""),
                            },
                        )
                    )
                    add_edge(Edge(source=tid, target=lid, type="team_has_hiring_lead", label=conf))

                    # Evidence edges (lead -> artifacts when URLs match)
                    ev_urls = l.get("evidence_urls") or []
                    if isinstance(ev_urls, list):
                        for u in ev_urls:
                            u = _as_str(u).strip()
                            if not u:
                                continue
                            aid = _artifact_id(u, bundle_id, idx=-1)
                            # Ensure artifact node exists even if not in artifacts list.
                            add_node(Node(id=aid, type="artifact", label=u, attrs={**meta, "url": u}))
                            add_edge(Edge(source=lid, target=aid, type="lead_supported_by"))

            # Priorities
            priorities = t.get("team_priorities") or []
            if isinstance(priorities, list):
                for pri, pr in enumerate(priorities):
                    if not isinstance(pr, dict):
                        continue
                    prid = _priority_id(bundle_id, ti, pri)
                    text = _as_str(pr.get("priority") or "")
                    add_node(
                        Node(
                            id=prid,
                            type="priority",
                            label=text or f"priority {pri}",
                            attrs={
                                **meta,
                                "team_or_group": team_name,
                                "priority": text,
                                "notes": _as_str(pr.get("notes") or ""),
                                "evidence_urls": _join(pr.get("evidence_urls") or []),
                            },
                        )
                    )
                    add_edge(Edge(source=tid, target=prid, type="team_has_priority"))

            # Tech stack keywords (team -> keyword)
            tech = t.get("tech_stack_signals") or {}
            tech = tech if isinstance(tech, dict) else {}
            for bucket in ("languages", "frameworks", "infra", "data"):
                vals = tech.get(bucket) or []
                if not isinstance(vals, list):
                    continue
                for v in vals:
                    v = _as_str(v).strip()
                    if not v:
                        continue
                    kid = _kw_id(v)
                    add_node(Node(id=kid, type="keyword", label=v, attrs={"bucket": bucket}))
                    add_edge(Edge(source=tid, target=kid, type="team_uses_keyword", label=bucket))

    return list(nodes.values()), edges


def write_graph_json(path: Path, nodes: List[Node], edges: List[Edge]) -> None:
    payload = {
        "nodes": [
            {"id": n.id, "type": n.type, "label": n.label, **n.attrs}
            for n in nodes
        ],
        "edges": [
            {"source": e.source, "target": e.target, "type": e.type, "label": e.label, **(e.attrs or {})}
            for e in edges
        ],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_graph_graphml(path: Path, nodes: List[Node], edges: List[Edge]) -> None:
    # Keep keys minimal and stable.
    node_keys = [
        ("label", "string"),
        ("type", "string"),
        ("company", "string"),
        ("bundle_id", "string"),
        ("url", "string"),
        ("published_at", "string"),
        ("public_profile_url", "string"),
        ("confidence", "string"),
    ]
    edge_keys = [
        ("type", "string"),
        ("label", "string"),
    ]

    def nk(i: int) -> str:
        return f"dn{i}"

    def ek(i: int) -> str:
        return f"de{i}"

    lines: List[str] = []
    lines.append('<?xml version="1.0" encoding="UTF-8"?>')
    lines.append('<graphml xmlns="http://graphml.graphdrawing.org/xmlns">')
    for i, (name, typ) in enumerate(node_keys):
        lines.append(f'  <key id="{nk(i)}" for="node" attr.name="{_xml_escape(name)}" attr.type="{_xml_escape(typ)}"/>')
    for i, (name, typ) in enumerate(edge_keys):
        lines.append(f'  <key id="{ek(i)}" for="edge" attr.name="{_xml_escape(name)}" attr.type="{_xml_escape(typ)}"/>')
    lines.append('  <graph id="G" edgedefault="directed">')
    for n in nodes:
        lines.append(f'    <node id="{_xml_escape(n.id)}">')
        vals = {"label": n.label, "type": n.type, **n.attrs}
        for i, (name, _typ) in enumerate(node_keys):
            v = _as_str(vals.get(name, ""))
            if v:
                lines.append(f'      <data key="{nk(i)}">{_xml_escape(v)}</data>')
        lines.append("    </node>")
    for ei, e in enumerate(edges):
        lines.append(
            f'    <edge id="e{ei}" source="{_xml_escape(e.source)}" target="{_xml_escape(e.target)}">'
        )
        ev = {"type": e.type, "label": e.label}
        for i, (name, _typ) in enumerate(edge_keys):
            v = _as_str(ev.get(name, ""))
            if v:
                lines.append(f'      <data key="{ek(i)}">{_xml_escape(v)}</data>')
        lines.append("    </edge>")
    lines.append("  </graph>")
    lines.append("</graphml>")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_rank_people_csv(path: Path, nodes: List[Node], edges: List[Edge]) -> None:
    # Simple degree-based ranking. Good enough as a default heuristic.
    deg: Dict[str, int] = {}
    for e in edges:
        deg[e.source] = deg.get(e.source, 0) + 1
        deg[e.target] = deg.get(e.target, 0) + 1

    people = [n for n in nodes if n.type == "person"]
    rows = []
    for n in people:
        rows.append(
            {
                "person_id": n.id,
                "name": n.attrs.get("name", n.label),
                "role": n.attrs.get("role", ""),
                "public_profile_url": n.attrs.get("public_profile_url", ""),
                "team_hint": n.attrs.get("team_hint", ""),
                "bundle_id": n.attrs.get("bundle_id", ""),
                "company": n.attrs.get("company", ""),
                "degree": str(deg.get(n.id, 0)),
            }
        )

    rows.sort(key=lambda r: int(r.get("degree") or 0), reverse=True)

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(
            f,
            fieldnames=[
                "person_id",
                "name",
                "role",
                "public_profile_url",
                "team_hint",
                "bundle_id",
                "company",
                "degree",
            ],
        )
        w.writeheader()
        for r in rows:
            w.writerow(r)

