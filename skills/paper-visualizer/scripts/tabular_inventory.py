#!/usr/bin/env python3
"""
Inventory tabular files under a directory and infer likely visualization roles.

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
X_KEYWORDS = ("epoch", "step", "iteration", "iter", "time", "timestamp", "date", "year", "month", "day")
Y_KEYWORDS = (
    "value",
    "score",
    "metric",
    "loss",
    "accuracy",
    "precision",
    "recall",
    "f1",
    "count",
    "amount",
    "rate",
    "price",
    "temperature",
)
GROUP_KEYWORDS = (
    "model",
    "method",
    "group",
    "category",
    "class",
    "variant",
    "condition",
    "seed",
    "region",
    "city",
    "country",
    "segment",
    "split",
)
FACET_KEYWORDS = ("dataset", "task", "panel", "scenario", "region", "split", "subset", "fold", "site")
LAT_KEYWORDS = ("lat", "latitude")
LON_KEYWORDS = ("lon", "lng", "long", "longitude")


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
        return pd.read_json(path).head(sample_rows)
    raise ValueError(f"Unsupported format: {file_format}")


def _count_rows(path: Path, file_format: str) -> int | None:
    if file_format in {"csv", "tsv"}:
        with path.open("r", encoding="utf-8", errors="ignore") as handle:
            return max(sum(1 for _ in handle) - 1, 0)
    if file_format == "jsonl":
        with path.open("r", encoding="utf-8", errors="ignore") as handle:
            return sum(1 for _ in handle)
    return None


def _normalize_name(name: str) -> str:
    lowered = name.lower()
    return "".join(char if char.isalnum() else " " for char in lowered)


def _keyword_score(name: str, keywords: tuple[str, ...]) -> int:
    normalized = _normalize_name(name)
    tokens = normalized.split()
    best = 0
    for keyword in keywords:
        if normalized == keyword:
            best = max(best, 3)
        elif keyword in tokens:
            best = max(best, 2)
        elif keyword in normalized:
            best = max(best, 1)
    return best


def _sample_unique_counts(frame: Any) -> dict[str, int]:
    unique_counts: dict[str, int] = {}
    for name in frame.columns:
        try:
            unique_counts[str(name)] = int(frame[name].nunique(dropna=True))
        except Exception:
            unique_counts[str(name)] = 0
    return unique_counts


def _pick_best(
    columns: list[str],
    keywords: tuple[str, ...],
    unique_counts: dict[str, int],
    *,
    exclude: set[str] | None = None,
    prefer_low_cardinality: bool = False,
    max_unique: int | None = None,
) -> str | None:
    exclude = exclude or set()
    best_name: str | None = None
    best_score = -1
    for name in columns:
        if name in exclude:
            continue
        unique_count = unique_counts.get(name, 0)
        if max_unique is not None and unique_count > max_unique:
            continue
        score = _keyword_score(name, keywords)
        if prefer_low_cardinality and 1 < unique_count <= 20:
            score += 2
        elif prefer_low_cardinality and unique_count > 20:
            score -= 1
        if score > best_score:
            best_name = name
            best_score = score
    if best_score <= 0:
        return None
    return best_name


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


def _infer_roles(
    numeric_columns: list[str],
    categorical_columns: list[str],
    datetime_columns: list[str],
    unique_counts: dict[str, int],
) -> dict[str, Any]:
    likely_x = _pick_best(datetime_columns, X_KEYWORDS, unique_counts) or _pick_best(
        numeric_columns,
        X_KEYWORDS,
        unique_counts,
    )
    if likely_x is None and datetime_columns:
        likely_x = datetime_columns[0]
    if likely_x is None and numeric_columns:
        likely_x = numeric_columns[0]

    likely_y = _pick_best(numeric_columns, Y_KEYWORDS, unique_counts, exclude={likely_x} if likely_x else set())
    if likely_y is None:
        for candidate in numeric_columns:
            if candidate != likely_x:
                likely_y = candidate
                break
    if likely_y is None and numeric_columns:
        likely_y = numeric_columns[0]

    likely_group = _pick_best(
        categorical_columns,
        GROUP_KEYWORDS,
        unique_counts,
        exclude={likely_x, likely_y} - {None},
        prefer_low_cardinality=True,
        max_unique=20,
    )
    if likely_group is None:
        for candidate in categorical_columns:
            if candidate not in {likely_x, likely_y} and 1 < unique_counts.get(candidate, 0) <= 20:
                likely_group = candidate
                break

    likely_facet = _pick_best(
        categorical_columns,
        FACET_KEYWORDS,
        unique_counts,
        exclude={likely_x, likely_y, likely_group} - {None},
        prefer_low_cardinality=True,
        max_unique=8,
    )
    if likely_facet is None:
        for candidate in categorical_columns:
            if candidate not in {likely_x, likely_y, likely_group} and 1 < unique_counts.get(candidate, 0) <= 8:
                likely_facet = candidate
                break

    lat_candidates = numeric_columns + categorical_columns
    likely_lat = _pick_best(lat_candidates, LAT_KEYWORDS, unique_counts)
    likely_lon = _pick_best(lat_candidates, LON_KEYWORDS, unique_counts)

    return {
        "likely_x": likely_x,
        "likely_y": likely_y,
        "likely_group": likely_group,
        "likely_facet": likely_facet,
        "likely_lat": likely_lat,
        "likely_lon": likely_lon,
    }


def _recommended_chart_families(
    *,
    numeric_columns: list[str],
    categorical_columns: list[str],
    datetime_columns: list[str],
    likely_lat: str | None,
    likely_lon: str | None,
) -> list[str]:
    if likely_lat and likely_lon:
        return ["map", "correlation"]
    if datetime_columns:
        return ["evolution", "comparison/ranking"]
    if len(numeric_columns) >= 2 and categorical_columns:
        return ["comparison/ranking", "correlation", "distribution"]
    if len(numeric_columns) >= 2:
        return ["correlation", "distribution"]
    if numeric_columns and categorical_columns:
        return ["comparison/ranking", "distribution", "part-to-whole"]
    if len(categorical_columns) >= 2:
        return ["part-to-whole", "flow"]
    if numeric_columns:
        return ["distribution"]
    return ["comparison/ranking"]


def _supported_task_modes(
    *,
    row_count: int | None,
    likely_lat: str | None,
    likely_lon: str | None,
) -> list[str]:
    modes = ["static", "explore", "app"]
    if likely_lat and likely_lon:
        modes.append("geo")
    return modes


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
            unique_counts = _sample_unique_counts(frame)
            row_count = _count_rows(path, file_format=file_format)
            roles = _infer_roles(numeric_columns, categorical_columns, datetime_columns, unique_counts)
            chart_families = _recommended_chart_families(
                numeric_columns=numeric_columns,
                categorical_columns=categorical_columns,
                datetime_columns=datetime_columns,
                likely_lat=roles["likely_lat"],
                likely_lon=roles["likely_lon"],
            )

            info["sampled_rows"] = int(len(frame))
            if row_count is not None:
                info["row_count"] = row_count
            info["columns"] = columns
            info["numeric_columns"] = numeric_columns
            info["categorical_columns"] = categorical_columns
            info["datetime_columns"] = datetime_columns
            info["sample_unique_values"] = unique_counts
            info["large_dataset_hint"] = bool(row_count is not None and row_count >= 100_000)
            info["recommended_chart_families"] = chart_families
            info["supported_task_modes"] = _supported_task_modes(
                row_count=row_count,
                likely_lat=roles["likely_lat"],
                likely_lon=roles["likely_lon"],
            )
            info.update(roles)
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
