#!/usr/bin/env python3
"""
Aggregate multiple Career Team Intel bundles into one merged graph.

Scans for extraction.json under root_dir and outputs:
  <out>/graph.json + graph.graphml + rank_people.csv
"""

from __future__ import annotations

import argparse
from pathlib import Path

from graph import (
    graph_from_extraction,
    load_extraction,
    write_graph_graphml,
    write_graph_json,
    write_rank_people_csv,
)


def main() -> int:
    p = argparse.ArgumentParser(description="Aggregate bundles into one merged graph.")
    p.add_argument("root_dir", help="Root directory to scan for extraction.json files.")
    p.add_argument(
        "--out",
        default="",
        help="Output directory (default: <root_dir>/career-team-intel-graph).",
    )
    args = p.parse_args()

    root_dir = Path(args.root_dir).expanduser().resolve()
    out_dir = Path(args.out).expanduser().resolve() if args.out else (root_dir / "career-team-intel-graph")
    out_dir.mkdir(parents=True, exist_ok=True)

    extraction_paths = sorted(root_dir.rglob("extraction.json"))
    if not extraction_paths:
        raise SystemExit(f"No extraction.json found under: {root_dir}")

    # Merge by node id; keep first label/type, fill missing attrs.
    nodes_by_id = {}
    edges = []
    for extraction_path in extraction_paths:
        bundle_dir = extraction_path.parent
        try:
            data = load_extraction(extraction_path)
        except Exception:
            continue
        nodes, es = graph_from_extraction(data, bundle_dir)
        for n in nodes:
            if n.id not in nodes_by_id:
                nodes_by_id[n.id] = n
            else:
                existing = nodes_by_id[n.id]
                for k, v in n.attrs.items():
                    if k not in existing.attrs or not existing.attrs[k]:
                        existing.attrs[k] = v
        edges.extend(es)

    nodes = list(nodes_by_id.values())
    write_graph_json(out_dir / "graph.json", nodes, edges)
    write_graph_graphml(out_dir / "graph.graphml", nodes, edges)
    write_rank_people_csv(out_dir / "rank_people.csv", nodes, edges)

    print(str(out_dir))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

