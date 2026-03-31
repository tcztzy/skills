#!/usr/bin/env python3
"""
Generate a runnable matplotlib publication-visualization skeleton from an inventory.json file.

This generator is intentionally dependency-light. The generated script requires
numpy + matplotlib to render figures.
"""

import argparse
import json
from pathlib import Path


TEMPLATE = """#!/usr/bin/env python3
\"\"\"
Auto-generated matplotlib publication-visualization skeleton.

This script is intended as a starting point. It will:
- load existing .npy data only
- write figures into a figures directory
- export both vector PDF and 300 dpi PNG previews
- optionally write viz_manifest.json

To run:
  uv run --with numpy --with matplotlib -s auto_data_to_viz.py --figures-dir "__FIGURES_DIR__" --manifest viz_manifest.json
\"\"\"

import argparse
import json
import os
import shutil
from pathlib import Path

import numpy as np


DEFAULT_CLEAN = __DEFAULT_CLEAN__
DEFAULT_MAX_PLOTS = __MAX_PLOTS__
MM_TO_INCH = 1 / 25.4
SINGLE_COLUMN_SIZE = (90 * MM_TO_INCH, 65 * MM_TO_INCH)

INVENTORY_JSON = r'''__INVENTORY_JSON__'''
INVENTORY = json.loads(INVENTORY_JSON)


def _safe_label(text: str) -> str:
    return text.replace("_", " ").replace("-", " ")


def _safe_stem(text: str) -> str:
    pieces: list[str] = []
    for char in text.lower():
        if char.isalnum():
            pieces.append(char)
        elif char in {" ", "_", "-", "."}:
            pieces.append("-")
    stem = "".join(pieces).strip("-")
    return stem or "figure"


def _resolve_path(entry: dict) -> Path:
    if entry.get("abs_path"):
        candidate = Path(entry["abs_path"])
        if candidate.exists():
            return candidate
    base_dir = INVENTORY.get("base_dir") or os.getcwd()
    return Path(base_dir) / entry.get("rel_path", "")


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


def _export_figure(fig, stem: str, figures_dir: Path) -> dict[str, str]:
    pdf_path = figures_dir / f"{stem}.pdf"
    png_path = figures_dir / f"{stem}.png"
    fig.savefig(pdf_path, format="pdf")
    fig.savefig(png_path, format="png", dpi=300)
    return {
        "filename": pdf_path.name,
        "preview_filename": png_path.name,
    }


def _chart_family(name: str, arr: np.ndarray) -> str:
    normalized = name.lower()
    if arr.ndim == 1 and any(token in normalized for token in {"epoch", "step", "time", "loss", "history", "curve"}):
        return "evolution"
    if arr.ndim == 1:
        return "distribution"
    if arr.ndim == 2:
        return "multivariate"
    return "comparison/ranking"


def _quicklook_plot(entry: dict, figures_dir: Path, idx: int) -> dict[str, object]:
    try:
        import matplotlib.pyplot as plt
    except Exception as exc:
        raise RuntimeError("matplotlib is required to plot. Install with: uv run --with matplotlib ...") from exc

    path = _resolve_path(entry)
    if not path.exists():
        raise FileNotFoundError(str(path))

    arr = np.load(path, mmap_mode="r", allow_pickle=False)
    name = Path(entry.get("rel_path") or path.name).stem
    display_name = _safe_label(name)
    figure_stem = f"{idx:02d}-{_safe_stem(name)}"

    fig, ax = plt.subplots(figsize=SINGLE_COLUMN_SIZE, constrained_layout=True)
    if arr.ndim == 1:
        ax.plot(arr, linewidth=1.25, color="#1f77b4")
        ax.set_xlabel("Index")
        ax.set_ylabel("Value")
        title = f"{display_name} (1D)"
    elif arr.ndim == 2:
        image = ax.imshow(arr, aspect="auto", cmap="cividis")
        fig.colorbar(image, ax=ax, shrink=0.85)
        ax.set_xlabel("Column")
        ax.set_ylabel("Row")
        title = f"{display_name} (2D heatmap)"
    else:
        ax.text(0.05, 0.5, f"ndim={arr.ndim} not plotted", fontsize=7)
        ax.axis("off")
        title = f"{display_name} (skipped)"

    ax.set_title(title)
    if ax.spines.get("top") is not None:
        ax.spines["top"].set_visible(False)
    if ax.spines.get("right") is not None:
        ax.spines["right"].set_visible(False)

    exported = _export_figure(fig, figure_stem, figures_dir)
    plt.close(fig)

    return {
        "id": f"viz-{idx:02d}",
        "filename": exported["filename"],
        "preview_filename": exported["preview_filename"],
        "title": title,
        "plot_system": "matplotlib",
        "chart_family": _chart_family(name, arr),
        "task_mode": "static",
        "interaction_level": "static",
        "script_path": Path(__file__).name,
        "data_sources": [str(path)],
        "caption_suggestion": f"Quicklook view of {display_name}. Replace with a claim-driven caption before publication.",
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Run the auto matplotlib publication-visualization script.")
    ap.add_argument("--figures-dir", default="__FIGURES_DIR__", help="Output figures directory.")
    ap.add_argument("--clean", dest="clean", action="store_true", default=DEFAULT_CLEAN, help="Clean figures-dir before plotting.")
    ap.add_argument("--no-clean", dest="clean", action="store_false", help="Do not clean figures-dir before plotting.")
    ap.add_argument("--max-plots", type=int, default=DEFAULT_MAX_PLOTS, help="Max quicklook plots to attempt.")
    ap.add_argument("--manifest", default=None, help="Optional viz_manifest.json output path.")
    args = ap.parse_args()

    _configure_matplotlib()
    figures_dir = _ensure_figures_dir(Path(args.figures_dir), clean=bool(args.clean))

    entries = INVENTORY.get("entries", [])
    if not isinstance(entries, list):
        raise RuntimeError("INVENTORY.entries must be a list")

    total = max(0, min(int(args.max_plots), len(entries)))
    items: list[dict[str, object]] = []
    for index in range(total):
        try:
            items.append(_quicklook_plot(entries[index], figures_dir, index + 1))
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
    ap = argparse.ArgumentParser(description="Generate auto_data_to_viz.py matplotlib skeleton.")
    ap.add_argument("--inventory", required=True, help="Input inventory.json from npy_inventory.py.")
    ap.add_argument("--out", required=True, help="Output path for auto_data_to_viz.py.")
    ap.add_argument("--figures-dir", default="figures", help="Figures directory (default: figures).")
    ap.add_argument(
        "--clean",
        action="store_true",
        help="Set generated script default to clean the figures dir before plotting (default: false).",
    )
    ap.add_argument(
        "--max-plots",
        type=int,
        default=12,
        help="Max quicklook plots the generated script will attempt (default: 12).",
    )
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
                "shape": entry.get("shape"),
                "dtype": entry.get("dtype"),
            }
            for entry in entries
            if isinstance(entry, dict) and (entry.get("rel_path") or entry.get("abs_path"))
        ],
    }

    inventory_json = json.dumps(embedded, indent=2)
    script = (
        TEMPLATE.replace("__FIGURES_DIR__", args.figures_dir)
        .replace("__DEFAULT_CLEAN__", "True" if args.clean else "False")
        .replace("__MAX_PLOTS__", str(int(args.max_plots)))
        .replace("__INVENTORY_JSON__", inventory_json)
    )

    out_path = Path(args.out).expanduser().resolve()
    out_path.write_text(script, encoding="utf-8")
    print(f"[OK] Wrote skeleton: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
