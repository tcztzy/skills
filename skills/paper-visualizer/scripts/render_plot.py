#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "matplotlib>=3.10.8",
# ]
# ///

import argparse
import io
from pathlib import Path
import re
from typing import Any

import matplotlib.pyplot as plt

PYTHON_FENCE_RE = re.compile(r"```python(.*?)```", re.DOTALL)


def strip_python_fence(code_text: str) -> str:
    match = PYTHON_FENCE_RE.search(code_text)
    return match.group(1).strip() if match else code_text.strip()


def render_plot_code_to_jpeg(
    code_text: str,
    *,
    dpi: int = 200,
) -> bytes | None:
    plt.switch_backend("Agg")
    plt.close("all")
    plt.rcdefaults()

    try:
        exec_globals: dict[str, Any] = {}
        exec(strip_python_fence(code_text), exec_globals)
        if not plt.get_fignums():
            return None

        buffer = io.BytesIO()
        plt.savefig(buffer, format="jpeg", bbox_inches="tight", dpi=dpi)
        buffer.seek(0)
        return buffer.read()
    except Exception:
        return None
    finally:
        plt.close("all")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Render matplotlib code to a JPEG artifact."
    )
    parser.add_argument(
        "--code-file",
        type=Path,
        required=True,
        help="Path to a file containing matplotlib code.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="JPEG output path.",
    )
    parser.add_argument(
        "--dpi",
        type=int,
        default=200,
        help="Raster DPI for the rendered JPEG.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    code_text = args.code_file.read_text(encoding="utf-8")
    image_bytes = render_plot_code_to_jpeg(code_text, dpi=args.dpi)
    if image_bytes is None:
        return 1

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(image_bytes)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
