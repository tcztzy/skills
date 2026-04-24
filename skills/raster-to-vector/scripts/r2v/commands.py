import argparse
import json
import sys
import time
import xml.etree.ElementTree as ET
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

import numpy as np
from PIL import Image

from .common import (
    AuditJson,
    ComposeStep,
    IconProposal,
    LinePrimitive,
    ReportArtifacts,
    ReportJson,
    RectPrimitive,
    SVG_COUNT_TAGS,
    Scene,
    SceneElement,
    StepRecord,
    StepsJson,
    TextItem,
    load_image,
    nms,
    resolved,
    tag,
    write_json,
)
from .compose import compose_svg, draw_debug
from .ocr import mask_text, run_paddle_ocr, text_items_from_json, write_ocr_debug
from .primitives import (
    detect_icon_candidates,
    detect_lines,
    detect_rectangles,
    write_primitives_debug,
)
from .segment import require_sam_host, run_sam, supported_sam_host
from .vectorize import (
    assemble_scene,
    load_descriptions,
    load_scene,
    prepare_source,
    scene_elements,
    make_scene,
    trace_icon_crops,
    write_describe_template,
    write_icon_trace,
)


type SamMode = Literal["on", "off", "auto"]


@dataclass(frozen=True)
class RunOptions:
    input_path: Path
    out_dir: Path
    sam: SamMode
    sam_prompt: list[str]
    sam_threshold: float
    save_masks: bool
    mask_preview: bool
    trace_icons: bool
    debug: bool
    detect_icons: bool
    min_rect_area: int
    min_line_length: int

    @classmethod
    def from_args(cls, args: argparse.Namespace) -> "RunOptions":
        sam: SamMode = args.sam if args.sam in {"on", "off", "auto"} else "on"
        return cls(
            input_path=resolved(args.input),
            out_dir=resolved(args.out_dir),
            sam=sam,
            sam_prompt=[str(prompt) for prompt in args.sam_prompt],
            sam_threshold=float(args.sam_threshold),
            save_masks=bool(args.save_masks),
            mask_preview=bool(args.mask_preview),
            trace_icons=bool(args.trace_icons),
            debug=bool(args.debug),
            detect_icons=bool(args.detect_icons),
            min_rect_area=int(args.min_rect_area),
            min_line_length=int(args.min_line_length),
        )


@dataclass(frozen=True)
class RunPaths:
    out_dir: Path
    source: Path
    masked: Path
    final_svg: Path
    scene: Path
    report: Path
    debug: Path
    steps: Path

    @classmethod
    def from_out_dir(cls, out_dir: Path) -> "RunPaths":
        return cls(
            out_dir=out_dir,
            source=out_dir / "source.png",
            masked=out_dir / "masked.png",
            final_svg=out_dir / "final.svg",
            scene=out_dir / "scene.json",
            report=out_dir / "report.json",
            debug=out_dir / "debug.png",
            steps=out_dir / "steps.json",
        )

    def artifacts(self, mask_preview: bool, debug: bool) -> ReportArtifacts:
        artifacts: ReportArtifacts = {
            "source": str(self.source),
            "ocr": str(self.out_dir / "ocr.json"),
            "ocr_raw": str(self.out_dir / "ocr.raw.json"),
            "ocr_boxes": str(self.out_dir / "ocr-boxes.json"),
            "ocr_boxes_csv": str(self.out_dir / "ocr-boxes.csv"),
            "ocr_overlay": str(self.out_dir / "ocr-boxes.png"),
            "primitives": str(self.out_dir / "primitives.json"),
            "primitives_overlay": str(self.out_dir / "primitives.png"),
            "icon_trace": str(self.out_dir / "icon-trace.json"),
            "steps": str(self.steps),
            "scene": str(self.scene),
        }
        if mask_preview:
            artifacts["masked"] = str(self.masked)
        if debug:
            artifacts["debug"] = str(self.debug)
        return artifacts


@dataclass
class PipelineState:
    options: RunOptions
    paths: RunPaths
    source: Image.Image
    started: float = field(default_factory=time.perf_counter)
    steps: list[StepRecord] = field(default_factory=list)
    texts: list[TextItem] = field(default_factory=list)
    rects: list[RectPrimitive] = field(default_factory=list)
    lines: list[LinePrimitive] = field(default_factory=list)
    icons: list[IconProposal] = field(default_factory=list)
    unresolved: list[str] = field(default_factory=list)
    scene: Scene | None = None
    sam_status: str = "off"

    def elapsed(self, started: float) -> float:
        return round((time.perf_counter() - started) * 1000, 2)

    def add_step(self, step: StepRecord) -> None:
        self.steps.append(step)

    def require_scene(self) -> Scene:
        if self.scene is None:
            raise RuntimeError("scene not built")
        return self.scene


@dataclass(frozen=True)
class RunReport:
    state: PipelineState

    def to_json(self) -> ReportJson:
        scene = self.state.require_scene()
        return {
            "input": str(self.state.options.input_path),
            "output_svg": str(self.state.paths.final_svg),
            "text_items": len(self.state.texts),
            "containers": len(self.state.rects),
            "connectors": len(self.state.lines),
            "icons": len(self.state.icons),
            "unresolved": scene["unresolved"],
            "sam": self.state.sam_status,
            "elapsed_ms": round((time.perf_counter() - self.state.started) * 1000, 2),
            "artifacts": self.state.paths.artifacts(
                self.state.options.mask_preview,
                self.state.options.debug,
            ),
        }

    def write(self) -> None:
        steps: StepsJson = {"steps": self.state.steps}
        write_json(self.state.paths.steps, steps)
        write_json(self.state.paths.report, self.to_json())


def prepare_pipeline(options: RunOptions) -> PipelineState:
    options.out_dir.mkdir(parents=True, exist_ok=True)
    paths = RunPaths.from_out_dir(options.out_dir)
    source = load_image(options.input_path)
    state = PipelineState(options=options, paths=paths, source=source)
    t0 = time.perf_counter()
    source.save(paths.source)
    if options.sam == "on":
        require_sam_host()
    state.add_step(
        {
            "step": "prepare",
            "elapsed_ms": state.elapsed(t0),
            "input": str(options.input_path),
            "source": str(paths.source),
            "size": [source.width, source.height],
        }
    )
    return state


def run_ocr_stage(state: PipelineState) -> None:
    t0 = time.perf_counter()
    state.texts = run_paddle_ocr(state.paths.source, state.paths.out_dir)
    write_ocr_debug(state.source, state.texts, state.paths.out_dir)
    state.add_step(
        {
            "step": "ocr",
            "elapsed_ms": state.elapsed(t0),
            "engine": "paddleocr",
            "output": str(state.paths.out_dir / "ocr.json"),
            "boxes": str(state.paths.out_dir / "ocr-boxes.json"),
            "overlay": str(state.paths.out_dir / "ocr-boxes.png"),
            "text_items": len(state.texts),
        }
    )


def maybe_run_mask_preview(state: PipelineState) -> None:
    if not state.options.mask_preview:
        return
    t0 = time.perf_counter()
    mask_text(state.source, state.texts, state.paths.masked)
    state.add_step(
        {
            "step": "mask_preview",
            "elapsed_ms": state.elapsed(t0),
            "output": str(state.paths.masked),
            "masked_items": len(state.texts),
        }
    )


def run_primitives_stage(state: PipelineState) -> None:
    t0 = time.perf_counter()
    image = np.array(state.source.convert("RGB"))
    state.rects = detect_rectangles(image, state.options.min_rect_area)
    state.lines = detect_lines(
        image,
        state.rects,
        state.options.min_line_length,
        state.texts,
    )
    state.icons = (
        detect_icon_candidates(image, state.texts, state.rects)
        if state.options.detect_icons
        else []
    )
    state.add_step(
        {
            "step": "cv_primitives",
            "elapsed_ms": state.elapsed(t0),
            "containers": len(state.rects),
            "connectors": len(state.lines),
            "icon_candidates": len(state.icons),
        }
    )


def maybe_run_segmentation(state: PipelineState) -> None:
    if state.options.sam == "off" or not supported_sam_host():
        return
    t0 = time.perf_counter()
    sam_icons, state.sam_status = run_sam(
        state.source,
        state.options.sam_prompt,
        state.options.sam_threshold,
        state.paths.out_dir,
        state.options.save_masks,
    )
    state.icons = nms([*sam_icons, *state.icons], 0.45)
    state.add_step(
        {
            "step": "segmentation",
            "elapsed_ms": state.elapsed(t0),
            "status": state.sam_status,
            "prompts": state.options.sam_prompt,
            "proposals": len(sam_icons),
            "merged_icons": len(state.icons),
            "output": str(state.paths.out_dir / "sam.json"),
        }
    )


def run_icons_stage(state: PipelineState) -> None:
    t0 = time.perf_counter()
    descriptions = load_descriptions(state.paths.out_dir / "descriptions.json")
    state.unresolved = trace_icon_crops(
        state.source,
        state.icons,
        descriptions,
        state.paths.out_dir,
        trace_icons=state.options.trace_icons,
    )
    write_icon_trace(state.paths.out_dir, state.icons, state.unresolved)
    write_primitives_debug(
        state.source,
        state.rects,
        state.lines,
        state.icons,
        state.paths.out_dir,
    )
    state.add_step(
        {
            "step": "icons",
            "elapsed_ms": state.elapsed(t0),
            "total": len(state.icons),
            "unresolved": len(set(state.unresolved)),
            "trace_log": str(state.paths.out_dir / "icon-trace.json"),
            "primitives": str(state.paths.out_dir / "primitives.json"),
        }
    )


def run_compose_stage(state: PipelineState) -> None:
    t0 = time.perf_counter()
    elements: list[SceneElement] = scene_elements(
        state.rects,
        state.lines,
        state.icons,
        state.texts,
    )
    state.scene = make_scene(state.source, elements, state.unresolved)
    write_json(state.paths.scene, state.scene)
    compose_svg(state.scene, state.paths.out_dir, state.paths.final_svg)
    if state.options.debug:
        draw_debug(state.source, elements, state.paths.debug)
    compose_step: ComposeStep = {
        "step": "compose",
        "elapsed_ms": state.elapsed(t0),
        "scene": str(state.paths.scene),
        "svg": str(state.paths.final_svg),
        "elements": len(elements),
    }
    if state.options.debug:
        compose_step["debug"] = str(state.paths.debug)
    state.add_step(compose_step)


def print_run_summary(state: PipelineState) -> None:
    scene = state.require_scene()
    print(f"svg={state.paths.final_svg}")
    print(f"scene={state.paths.scene}")
    print(f"ocr={state.paths.out_dir / 'ocr.json'}")
    print(
        f"text={len(state.texts)} containers={len(state.rects)} connectors={len(state.lines)} icons={len(state.icons)} unresolved={len(scene['unresolved'])}"
    )
    print(f"sam={state.sam_status}")


def build_scene(args: argparse.Namespace) -> int:
    state = prepare_pipeline(RunOptions.from_args(args))
    run_ocr_stage(state)
    maybe_run_mask_preview(state)
    run_primitives_stage(state)
    maybe_run_segmentation(state)
    run_icons_stage(state)
    run_compose_stage(state)
    RunReport(state).write()
    print_run_summary(state)
    return 0


def cmd_ocr(args: argparse.Namespace) -> int:
    out_dir = resolved(args.out_dir)
    source = prepare_source(args.input, out_dir)
    texts = run_paddle_ocr(out_dir / "source.png", out_dir)
    write_ocr_debug(source, texts, out_dir)
    print(f"ocr={out_dir / 'ocr.json'}")
    print(f"text={len(texts)}")
    return 0


def cmd_segment(args: argparse.Namespace) -> int:
    out_dir = resolved(args.out_dir)
    source = prepare_source(args.input, out_dir)
    proposals, status = run_sam(
        source, args.sam_prompt, args.sam_threshold, out_dir, args.save_masks
    )
    print(f"sam={out_dir / 'sam.json'}")
    print(f"status={status} proposals={len(proposals)}")
    return 0


def cmd_primitives(args: argparse.Namespace) -> int:
    out_dir = resolved(args.out_dir)
    source = prepare_source(args.input, out_dir)
    texts = text_items_from_json(out_dir / "ocr.json")
    image = np.array(source.convert("RGB"))
    rects = detect_rectangles(image, args.min_rect_area)
    lines = detect_lines(image, rects, args.min_line_length, texts)
    icons = detect_icon_candidates(image, texts, rects) if args.detect_icons else []
    write_primitives_debug(source, rects, lines, icons, out_dir)
    print(f"primitives={out_dir / 'primitives.json'}")
    print(f"containers={len(rects)} connectors={len(lines)} icons={len(icons)}")
    return 0


def cmd_describe(args: argparse.Namespace) -> int:
    out_dir = resolved(args.run_dir)
    write_describe_template(out_dir)
    print(f"describe_input={out_dir / 'describe-input.json'}")
    print(f"descriptions={out_dir / 'descriptions.json'}")
    return 0


def cmd_vectorize(args: argparse.Namespace) -> int:
    out_dir = resolved(args.run_dir)
    scene = assemble_scene(out_dir, trace_icons=args.trace_icons)
    print(f"scene={out_dir / 'scene.json'}")
    print(f"elements={len(scene['elements'])} unresolved={len(scene['unresolved'])}")
    return 0


def cmd_compose(args: argparse.Namespace) -> int:
    out_dir = resolved(args.run_dir)
    scene_path = out_dir / "scene.json"
    output = resolved(args.output) if args.output else out_dir / "final.svg"
    compose_svg(load_scene(scene_path), out_dir, output)
    print(f"svg={output}")
    return 0


def cmd_audit(args: argparse.Namespace) -> int:
    out_dir = resolved(args.run_dir)
    svg_path = out_dir / "final.svg"
    scene_path = out_dir / "scene.json"
    report_path = out_dir / "audit.json"
    scene = load_scene(scene_path) if scene_path.exists() else None
    counts: dict[str, int] = dict.fromkeys(SVG_COUNT_TAGS, 0)
    if svg_path.exists():
        root = ET.parse(svg_path).getroot()
        for name in counts:
            counts[name] = len(root.findall(".//" + tag(name)))
    audit: AuditJson = {
        "svg": str(svg_path),
        "scene": str(scene_path),
        "unresolved": scene["unresolved"] if scene else [],
        "svg_counts": counts,
    }
    write_json(report_path, audit)
    print(f"audit={report_path}")
    print(
        f"unresolved={len(audit['unresolved'])} image={counts['image']} text={counts['text']}"
    )
    return 0


def add_common_input_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("input", type=Path)
    parser.add_argument("--out-dir", type=Path, default=Path("r2v-run"))


def add_cv_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--no-detect-icons", dest="detect_icons", action="store_false")
    parser.add_argument("--min-rect-area", type=int, default=1200)
    parser.add_argument("--min-line-length", type=int, default=28)
    parser.set_defaults(detect_icons=True)


def add_sam_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--sam-prompt",
        action="append",
        default=["icon", "logo", "database icon", "server icon", "cloud icon"],
    )
    parser.add_argument("--sam-threshold", type=float, default=0.3)
    parser.add_argument("--save-masks", action="store_true")


def run_cli(func: Callable[[argparse.Namespace], int], args: argparse.Namespace) -> int:
    try:
        return func(args)
    except (
        OSError,
        RuntimeError,
        ValueError,
        json.JSONDecodeError,
        ET.ParseError,
    ) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
