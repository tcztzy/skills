#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "PyMuPDF>=1.24",
# ]
# ///
"""
Render PDF pages to PNGs for image-based review.

This script writes page images into --out-dir and a manifest JSON file that
records the rendered page paths and dimensions.
"""

import argparse
import json
from pathlib import Path


PageRecord = dict[str, int | str]


def render_pages(pdf_path: Path, out_dir: Path, dpi: int, max_pages: int | None) -> list[PageRecord]:
    import fitz  # type: ignore[import-not-found]

    document = fitz.open(str(pdf_path))
    scale = dpi / 72
    matrix = fitz.Matrix(scale, scale)
    total_pages = document.page_count
    limit = min(total_pages, max_pages) if max_pages is not None else total_pages

    out_dir.mkdir(parents=True, exist_ok=True)
    rendered_pages: list[PageRecord] = []

    for page_index in range(limit):
        page_number = page_index + 1
        page = document.load_page(page_index)
        pixmap = page.get_pixmap(matrix=matrix, alpha=False)
        image_path = out_dir / f"page-{page_number:03d}.png"
        pixmap.save(str(image_path))
        rendered_pages.append(
            {
                "page": page_number,
                "image_path": str(image_path),
                "width_px": pixmap.width,
                "height_px": pixmap.height,
                "rotation_deg": page.rotation,
            }
        )

    return rendered_pages


def write_manifest(manifest_path: Path, pdf_path: Path, dpi: int, pages: list[PageRecord]) -> None:
    manifest: dict[str, str | int | list[PageRecord]] = {
        "source_pdf": str(pdf_path),
        "dpi": dpi,
        "rendered_pages": len(pages),
        "pages": pages,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Render PDF pages to PNGs for review.")
    parser.add_argument("--pdf", required=True, help="Input PDF path.")
    parser.add_argument("--out-dir", required=True, help="Directory for rendered PNGs.")
    parser.add_argument(
        "--manifest",
        default=None,
        help="Optional manifest JSON path. Defaults to <out-dir>/manifest.json.",
    )
    parser.add_argument("--dpi", type=int, default=180, help="Render DPI. Default: 180.")
    parser.add_argument("--max-pages", type=int, default=None, help="Optional page limit.")
    args = parser.parse_args(argv)

    if args.dpi <= 0:
        print("[ERROR] --dpi must be positive.")
        return 2
    if args.max_pages is not None and args.max_pages <= 0:
        print("[ERROR] --max-pages must be positive when provided.")
        return 2

    pdf_path = Path(args.pdf).expanduser().resolve()
    if not pdf_path.exists():
        print(f"[ERROR] PDF not found: {pdf_path}")
        return 2

    out_dir = Path(args.out_dir).expanduser().resolve()
    manifest_path = (
        Path(args.manifest).expanduser().resolve()
        if args.manifest is not None
        else out_dir / "manifest.json"
    )

    try:
        pages = render_pages(pdf_path=pdf_path, out_dir=out_dir, dpi=args.dpi, max_pages=args.max_pages)
        write_manifest(manifest_path=manifest_path, pdf_path=pdf_path, dpi=args.dpi, pages=pages)
    except Exception as exc:
        print(f"[ERROR] Render failed: {exc}")
        return 3

    print(f"[OK] Wrote {len(pages)} page images to: {out_dir}")
    print(f"[OK] Wrote manifest: {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
