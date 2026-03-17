#!/usr/bin/env python3
"""
Inventory tabular files under a directory.

Requires: pandas
Safe by default: samples headers and a bounded number of rows without modifying
inputs.
"""

import argparse
import datetime as dt
import json
import os
from pathlib import Path
from typing import Any


TABULAR_SUFFIXES = {
    ".csv": "csv",
    ".tsv": "tsv",
    ".json": "json",
    ".jsonl": "jsonl",
}


def _walk(base: Path) -> list[Path]:
    out: list[Path] = []
    for root, dirs, files in os.walk(base):
        dirs[:] = [directory for directory in dirs if directory not in {".git", "__pycache__", ".venv", "venv"}]
        for filename in files:
            path = Path(root) / filename
            if path.suffix.lower() in TABULAR_SUFFIXES:
                out.append(path)
    return out


def _read_sample(path: Path, file_format: str, sample_rows: int) -> Any:
    import pandas as pd

    if file_format == "csv":
        return pd.read_csv(path, nrows=sample_rows)
    if file_format == "tsv":
        return pd.read_csv(path, sep="\t", nrows=sample_rows)
    if file_format == "jsonl":
        return pd.read_json(path, lines=True).head(sample_rows)
    if file_format == "json":
        frame = pd.read_json(path)
        return frame.head(sample_rows)
    raise ValueError(f"Unsupported format: {file_format}")


def _count_rows(path: Path, file_format: str) -> int | None:
    if file_format in {"csv", "tsv"}:
        with path.open("r", encoding="utf-8", errors="ignore") as handle:
            return max(sum(1 for _ in handle) - 1, 0)
    if file_format == "jsonl":
        with path.open("r", encoding="utf-8", errors="ignore") as handle:
            return sum(1 for _ in handle)
    return None


def _classify_columns(frame: Any) -> tuple[list[dict[str, str]], list[str], list[str], list[str]]:
    from pandas.api.types import is_bool_dtype, is_datetime64_any_dtype, is_numeric_dtype

    columns: list[dict[str, str]] = []
    numeric_columns: list[str] = []
    categorical_columns: list[str] = []
    datetime_columns: list[str] = []

    for name in frame.columns:
        series = frame[name]
        column_name = str(name)
        columns.append({"name": column_name, "dtype": str(series.dtype)})
        if is_bool_dtype(series):
            categorical_columns.append(column_name)
        elif is_datetime64_any_dtype(series):
            datetime_columns.append(column_name)
        elif is_numeric_dtype(series):
            numeric_columns.append(column_name)
        else:
            categorical_columns.append(column_name)

    return columns, numeric_columns, categorical_columns, datetime_columns


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Inventory tabular files (safe, read-only).")
    ap.add_argument("--dir", required=True, help="Directory to scan for tabular files.")
    ap.add_argument("--out", required=True, help="Output inventory JSON path.")
    ap.add_argument(
        "--sample-rows",
        type=int,
        default=2000,
        help="Maximum number of rows to sample per file for schema inference.",
    )
    ap.add_argument(
        "--max-bytes",
        type=int,
        default=None,
        help="If set, skip files larger than this many bytes.",
    )
    args = ap.parse_args(argv)

    base = Path(args.dir).expanduser().resolve()
    if not base.exists() or not base.is_dir():
        print(f"[ERROR] Not a directory: {base}")
        return 2

    try:
        import pandas as pd  # noqa: F401
    except Exception as exc:
        print("[ERROR] pandas is required. Try: uv run --with pandas -s scripts/tabular_inventory.py --help")
        print(f"Details: {exc}")
        return 3

    entries: list[dict[str, Any]] = []
    for path in sorted(_walk(base)):
        rel_path = str(path.relative_to(base))
        size_bytes = path.stat().st_size if path.exists() else None
        file_format = TABULAR_SUFFIXES[path.suffix.lower()]
        info: dict[str, Any] = {
            "rel_path": rel_path,
            "abs_path": str(path),
            "file_format": file_format,
            "size_bytes": size_bytes,
        }

        if args.max_bytes is not None and size_bytes is not None and size_bytes > args.max_bytes:
            info["skipped"] = f"size_bytes {size_bytes} > max_bytes {args.max_bytes}"
            entries.append(info)
            continue

        try:
            frame = _read_sample(path, file_format=file_format, sample_rows=max(1, args.sample_rows))
            columns, numeric_columns, categorical_columns, datetime_columns = _classify_columns(frame)
            row_count = _count_rows(path, file_format=file_format)
            info["sampled_rows"] = int(len(frame))
            if row_count is not None:
                info["row_count"] = row_count
            info["columns"] = columns
            info["numeric_columns"] = numeric_columns
            info["categorical_columns"] = categorical_columns
            info["datetime_columns"] = datetime_columns
        except Exception as exc:
            info["error"] = str(exc)

        entries.append(info)

    out_obj = {
        "base_dir": str(base),
        "generated_at": dt.datetime.now().isoformat(timespec="seconds"),
        "entries": entries,
    }
    Path(args.out).write_text(json.dumps(out_obj, indent=2), encoding="utf-8")
    print(f"[OK] Wrote inventory: {args.out} ({len(entries)} entries)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
