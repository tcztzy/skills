import argparse
from pathlib import Path

from . import (
    add_common_input_args,
    add_cv_args,
    add_sam_args,
    build_scene,
    cmd_audit,
    cmd_compose,
    cmd_describe,
    cmd_ocr,
    cmd_primitives,
    cmd_segment,
    cmd_vectorize,
    run_cli,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Raster diagrams to editable SVG.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run = subparsers.add_parser("run", help="run full pipeline")
    add_common_input_args(run)
    add_cv_args(run)
    add_sam_args(run)
    run.add_argument("--sam", choices=("on", "off", "auto"), default="on")
    run.add_argument("--no-trace-icons", dest="trace_icons", action="store_false")
    run.add_argument("--mask-preview", action="store_true")
    run.add_argument("--debug", action="store_true")
    run.set_defaults(func=build_scene, trace_icons=True)

    ocr = subparsers.add_parser("ocr", help="run OCR stage")
    add_common_input_args(ocr)
    ocr.set_defaults(func=cmd_ocr)

    segment = subparsers.add_parser("segment", help="run segmentation stage")
    add_common_input_args(segment)
    add_sam_args(segment)
    segment.set_defaults(func=cmd_segment)

    primitives = subparsers.add_parser("primitives", help="detect CV primitives")
    add_common_input_args(primitives)
    add_cv_args(primitives)
    primitives.set_defaults(func=cmd_primitives)

    describe = subparsers.add_parser(
        "describe", help="create icon description manifest"
    )
    describe.add_argument("--run-dir", type=Path, default=Path("r2v-run"))
    describe.set_defaults(func=cmd_describe)

    vectorize = subparsers.add_parser("vectorize", help="assemble semantic scene")
    vectorize.add_argument("--run-dir", type=Path, default=Path("r2v-run"))
    vectorize.add_argument("--no-trace-icons", dest="trace_icons", action="store_false")
    vectorize.set_defaults(func=cmd_vectorize, trace_icons=True)

    compose = subparsers.add_parser("compose", help="render scene.json to SVG")
    compose.add_argument("--run-dir", type=Path, default=Path("r2v-run"))
    compose.add_argument("--output", type=Path)
    compose.set_defaults(func=cmd_compose)

    audit = subparsers.add_parser("audit", help="audit generated SVG")
    audit.add_argument("--run-dir", type=Path, default=Path("r2v-run"))
    audit.set_defaults(func=cmd_audit)

    args = parser.parse_args()
    return run_cli(args.func, args)


if __name__ == "__main__":
    raise SystemExit(main())
