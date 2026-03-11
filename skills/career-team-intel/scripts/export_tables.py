#!/usr/bin/env python3
"""
Export analysis-friendly CSV tables from a single Career Team Intel bundle.

Input:  <bundle_dir>/extraction.json
Output: <bundle_dir>/tables/*.csv   (default)
"""

from __future__ import annotations

import argparse
from pathlib import Path

from tables import TABLE_FIELDS, load_extraction, rows_from_extraction, write_csv


def main() -> int:
    p = argparse.ArgumentParser(description="Export CSV tables from extraction.json in a bundle folder.")
    p.add_argument("bundle_dir", help="Path to the bundle directory (contains extraction.json).")
    p.add_argument(
        "--out",
        default="",
        help="Output directory for CSV tables (default: <bundle_dir>/tables).",
    )
    args = p.parse_args()

    bundle_dir = Path(args.bundle_dir).expanduser().resolve()
    extraction_path = bundle_dir / "extraction.json"
    if not extraction_path.exists():
        raise SystemExit(f"Missing extraction.json: {extraction_path}")

    out_dir = Path(args.out).expanduser().resolve() if args.out else (bundle_dir / "tables")
    data = load_extraction(extraction_path)
    tables = rows_from_extraction(data, bundle_dir)

    for name, rows in tables.items():
        write_csv(out_dir / f"{name}.csv", TABLE_FIELDS[name], rows)

    print(str(out_dir))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

