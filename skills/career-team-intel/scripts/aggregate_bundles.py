#!/usr/bin/env python3
"""
Aggregate multiple Career Team Intel bundles into merged CSV tables.

This script scans for extraction.json files under a root directory and produces:
  <out>/artifacts.csv, claims.csv, candidates.csv, people.csv, hiring_leads.csv, priorities.csv
"""

from __future__ import annotations

import argparse
from pathlib import Path

from tables import TABLE_FIELDS, load_extraction, rows_from_extraction, write_csv


def main() -> int:
    p = argparse.ArgumentParser(description="Aggregate extraction.json bundles into merged CSV tables.")
    p.add_argument("root_dir", help="Root directory to scan for extraction.json files.")
    p.add_argument(
        "--out",
        default="",
        help="Output directory (default: <root_dir>/career-team-intel-aggregate).",
    )
    args = p.parse_args()

    root_dir = Path(args.root_dir).expanduser().resolve()
    out_dir = Path(args.out).expanduser().resolve() if args.out else (root_dir / "career-team-intel-aggregate")
    out_dir.mkdir(parents=True, exist_ok=True)

    extraction_paths = sorted(root_dir.rglob("extraction.json"))
    if not extraction_paths:
        raise SystemExit(f"No extraction.json found under: {root_dir}")

    merged = {name: [] for name in TABLE_FIELDS.keys()}

    for extraction_path in extraction_paths:
        bundle_dir = extraction_path.parent
        try:
            data = load_extraction(extraction_path)
        except Exception:
            # Skip unreadable bundles; keep aggregation resilient.
            continue
        tables = rows_from_extraction(data, bundle_dir)
        for name, rows in tables.items():
            merged[name].extend(rows)

    for name, rows in merged.items():
        write_csv(out_dir / f"{name}.csv", TABLE_FIELDS[name], rows)

    print(str(out_dir))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

