#!/usr/bin/env python3
"""
Export graph outputs from a single Career Team Intel bundle.

Input:  <bundle_dir>/extraction.json
Output: <bundle_dir>/graph/graph.json + graph.graphml + rank_people.csv
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
    p = argparse.ArgumentParser(description="Export graph outputs from extraction.json in a bundle folder.")
    p.add_argument("bundle_dir", help="Path to the bundle directory (contains extraction.json).")
    p.add_argument("--out", default="", help="Output directory (default: <bundle_dir>/graph).")
    args = p.parse_args()

    bundle_dir = Path(args.bundle_dir).expanduser().resolve()
    extraction_path = bundle_dir / "extraction.json"
    if not extraction_path.exists():
        raise SystemExit(f"Missing extraction.json: {extraction_path}")

    out_dir = Path(args.out).expanduser().resolve() if args.out else (bundle_dir / "graph")
    out_dir.mkdir(parents=True, exist_ok=True)

    data = load_extraction(extraction_path)
    nodes, edges = graph_from_extraction(data, bundle_dir)
    write_graph_json(out_dir / "graph.json", nodes, edges)
    write_graph_graphml(out_dir / "graph.graphml", nodes, edges)
    write_rank_people_csv(out_dir / "rank_people.csv", nodes, edges)

    print(str(out_dir))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

