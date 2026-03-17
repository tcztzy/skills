#!/usr/bin/env python3
"""
Generate a runnable seaborn data-to-viz skeleton from a tabular inventory.
"""

import argparse
import json
from pathlib import Path


TEMPLATE = """#!/usr/bin/env python3
\"\"\"
Auto-generated seaborn data-to-viz skeleton.

This script is intended as a starting point for tidy tabular data.

To run:
  uv run --with pandas --with seaborn --with matplotlib -s auto_data_to_viz.py --figures-dir "__FIGURES_DIR__" --manifest viz_manifest.json
\"\"\"

import argparse
import json
import os
import shutil
from pathlib import Path

import pandas as pd
import seaborn as sns


DEFAULT_MAX_PLOTS = __MAX_PLOTS__
MM_TO_INCH = 1 / 25.4
SINGLE_COLUMN_SIZE = (90 * MM_TO_INCH, 65 * MM_TO_INCH)
INVENTORY_JSON = r'''__INVENTORY_JSON__'''
INVENTORY = json.loads(INVENTORY_JSON)


def _configure_matplotlib() -> None:
    import matplotlib as mpl
    from matplotlib import font_manager

    available_fonts = set(font_manager.fontManager.get_font_names())
    cjk_candidates = [
        "PingFang SC",
        "Hiragino Sans GB",
        "STHeiti",
        "Heiti SC",
        "Microsoft YaHei",
        "SimHei",
        "Noto Sans CJK SC",
        "Source Han Sans SC",
        "WenQuanYi Zen Hei",
        "Arial Unicode MS",
    ]
    fallback_fonts = ["Arial", "Helvetica", "DejaVu Sans"]
    sans_fonts = [name for name in cjk_candidates if name in available_fonts]
    sans_fonts.extend(name for name in fallback_fonts if name not in sans_fonts)

    mpl.rcParams.update(
        {
            "font.size": 7,
            "font.family": "sans-serif",
            "font.sans-serif": sans_fonts,
            "axes.unicode_minus": False,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "savefig.bbox": "tight",
        }
    )


def _ensure_figures_dir(figures_dir: Path, clean: bool) -> Path:
    if not figures_dir.is_absolute():
        figures_dir = (Path(os.getcwd()) / figures_dir).resolve()
    else:
        figures_dir = figures_dir.resolve()

    if clean:
        cwd = Path(os.getcwd()).resolve()
        if cwd not in figures_dir.parents:
            raise RuntimeError(f"Refusing to clean figures outside CWD: {figures_dir}")
        if figures_dir.exists():
            shutil.rmtree(figures_dir)

    figures_dir.mkdir(parents=True, exist_ok=True)
    return figures_dir


def _resolve_path(entry: dict) -> Path:
    if entry.get("abs_path"):
        candidate = Path(entry["abs_path"])
        if candidate.exists():
            return candidate
    base_dir = INVENTORY.get("base_dir") or os.getcwd()
    return Path(base_dir) / entry.get("rel_path", "")


def _read_entry(entry: dict) -> pd.DataFrame:
    path = _resolve_path(entry)
    file_format = entry.get("file_format")
    if file_format == "csv":
        return pd.read_csv(path)
    if file_format == "tsv":
        return pd.read_csv(path, sep="\\t")
    if file_format == "jsonl":
        return pd.read_json(path, lines=True)
    if file_format == "json":
        return pd.read_json(path)
    raise RuntimeError(f"Unsupported format: {file_format}")


def _sanitize_stem(text: str) -> str:
    out: list[str] = []
    for char in text.lower():
        if char.isalnum():
            out.append(char)
        elif char in {" ", "_", "-", "."}:
            out.append("-")
    return "".join(out).strip("-") or "visualization"


def _is_evolution(entry: dict) -> bool:
    families = entry.get("recommended_chart_families", [])
    return isinstance(families, list) and "evolution" in families


def _build_plot(entry: dict, data_frame: pd.DataFrame):
    import matplotlib.pyplot as plt

    x_column = entry.get("likely_x")
    y_column = entry.get("likely_y")
    hue_column = entry.get("likely_group")
    facet_column = entry.get("likely_facet")
    title = Path(entry.get("rel_path") or "visualization").stem.replace("_", " ").replace("-", " ")

    if x_column and y_column and _is_evolution(entry):
        grid = sns.relplot(
            data=data_frame,
            x=x_column,
            y=y_column,
            hue=hue_column,
            col=facet_column,
            kind="line",
            height=2.6,
            aspect=1.35,
        )
        chart_family = "evolution"
    elif x_column and y_column and x_column in entry.get("categorical_columns", []):
        grid = sns.catplot(
            data=data_frame,
            x=x_column,
            y=y_column,
            hue=hue_column,
            col=facet_column,
            kind="bar",
            height=2.6,
            aspect=1.35,
        )
        chart_family = "comparison/ranking"
    elif x_column and y_column:
        grid = sns.relplot(
            data=data_frame,
            x=x_column,
            y=y_column,
            hue=hue_column,
            col=facet_column,
            kind="scatter",
            height=2.6,
            aspect=1.35,
        )
        chart_family = "correlation"
    elif y_column:
        grid = sns.displot(
            data=data_frame,
            x=y_column,
            hue=hue_column,
            col=facet_column,
            kind="hist",
            height=2.6,
            aspect=1.35,
        )
        chart_family = "distribution"
    else:
        category = entry.get("categorical_columns", [None])[0]
        if category is None:
            raise RuntimeError("No plottable columns found")
        grid = sns.catplot(
            data=data_frame,
            x=category,
            kind="count",
            height=2.6,
            aspect=1.35,
        )
        chart_family = "comparison/ranking"

    grid.figure.suptitle(title)
    grid.figure.tight_layout()
    return grid, chart_family, title


def _save_bundle(grid, stem: str, figures_dir: Path) -> dict[str, str]:
    pdf_path = figures_dir / f"{stem}.pdf"
    png_path = figures_dir / f"{stem}.png"
    grid.figure.savefig(pdf_path, format="pdf")
    grid.figure.savefig(png_path, format="png", dpi=300)
    return {
        "filename": pdf_path.name,
        "preview_filename": png_path.name,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Run the auto seaborn data-to-viz script.")
    ap.add_argument("--figures-dir", default="__FIGURES_DIR__", help="Output figures directory.")
    ap.add_argument("--clean", action="store_true", help="Clean figures-dir before plotting.")
    ap.add_argument("--max-plots", type=int, default=DEFAULT_MAX_PLOTS, help="Max quicklook plots to attempt.")
    ap.add_argument("--manifest", default=None, help="Optional viz_manifest.json output path.")
    args = ap.parse_args()

    _configure_matplotlib()
    sns.set_theme(style="whitegrid", context="paper")
    figures_dir = _ensure_figures_dir(Path(args.figures_dir), clean=bool(args.clean))

    entries = INVENTORY.get("entries", [])
    if not isinstance(entries, list):
        raise RuntimeError("INVENTORY.entries must be a list")

    items: list[dict[str, object]] = []
    total = max(0, min(int(args.max_plots), len(entries)))
    for index in range(total):
        entry = entries[index]
        try:
            data_frame = _read_entry(entry)
            grid, chart_family, title = _build_plot(entry, data_frame)
            stem = f"{index + 1:02d}-{_sanitize_stem(title)}"
            exported = _save_bundle(grid, stem, figures_dir)
            items.append(
                {
                    "id": f"viz-{index + 1:02d}",
                    "filename": exported["filename"],
                    "preview_filename": exported["preview_filename"],
                    "title": title,
                    "plot_system": "seaborn",
                    "chart_family": chart_family,
                    "task_mode": "static",
                    "interaction_level": "static",
                    "script_path": Path(__file__).name,
                    "data_sources": [str(_resolve_path(entry))],
                    "caption_suggestion": f"Quicklook {chart_family} view of {title}. Replace with a claim-driven caption before publication.",
                }
            )
            grid.figure.clf()
        except Exception as exc:
            print(f"[WARN] Plot {index + 1} failed: {exc}")

    if args.manifest:
        manifest_path = Path(args.manifest).expanduser().resolve()
        manifest_obj = {
            "generated_at": INVENTORY.get("generated_at"),
            "figures_dir": str(figures_dir),
            "apps_dir": None,
            "visualizations": items,
        }
        manifest_path.write_text(json.dumps(manifest_obj, indent=2), encoding="utf-8")
        print(f"[OK] Wrote manifest: {manifest_path}")

    print(f"[OK] Wrote figures to: {figures_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
"""


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Generate auto_data_to_viz.py seaborn skeleton.")
    ap.add_argument("--inventory", required=True, help="Input inventory JSON from tabular_inventory.py.")
    ap.add_argument("--out", required=True, help="Output path for auto_data_to_viz.py.")
    ap.add_argument("--figures-dir", default="figures", help="Figures directory (default: figures).")
    ap.add_argument("--max-plots", type=int, default=12, help="Max quicklook plots the script will attempt.")
    args = ap.parse_args(argv)

    inv_path = Path(args.inventory).expanduser().resolve()
    try:
        inv = json.loads(inv_path.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"[ERROR] Failed to read inventory JSON: {inv_path}: {exc}")
        return 2

    entries = inv.get("entries", [])
    if not isinstance(entries, list):
        print("[ERROR] inventory.entries must be a list")
        return 2

    embedded = {
        "base_dir": inv.get("base_dir"),
        "generated_at": inv.get("generated_at"),
        "entries": [
            {
                "rel_path": entry.get("rel_path"),
                "abs_path": entry.get("abs_path"),
                "file_format": entry.get("file_format"),
                "numeric_columns": entry.get("numeric_columns", []),
                "categorical_columns": entry.get("categorical_columns", []),
                "datetime_columns": entry.get("datetime_columns", []),
                "likely_x": entry.get("likely_x"),
                "likely_y": entry.get("likely_y"),
                "likely_group": entry.get("likely_group"),
                "likely_facet": entry.get("likely_facet"),
                "recommended_chart_families": entry.get("recommended_chart_families", []),
            }
            for entry in entries
            if isinstance(entry, dict) and (entry.get("rel_path") or entry.get("abs_path"))
        ],
    }

    inventory_json = json.dumps(embedded, indent=2)
    script = (
        TEMPLATE.replace("__FIGURES_DIR__", args.figures_dir)
        .replace("__MAX_PLOTS__", str(int(args.max_plots)))
        .replace("__INVENTORY_JSON__", inventory_json)
    )

    out_path = Path(args.out).expanduser().resolve()
    out_path.write_text(script, encoding="utf-8")
    print(f"[OK] Wrote skeleton: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
