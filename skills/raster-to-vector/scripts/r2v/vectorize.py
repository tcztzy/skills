from pathlib import Path
from typing import cast

import cv2
import numpy as np
import vtracer
from PIL import Image

from .common import (
    BBox,
    DescriptionItem,
    DescriptionMap,
    DescriptionRecord,
    DescriptionsJson,
    IconProposal,
    IconTraceJson,
    LinePrimitive,
    RectPrimitive,
    Scene,
    SceneElement,
    SceneIcon,
    SceneLine,
    SceneRect,
    SceneText,
    TextItem,
    bbox_text_label,
    border_rgb,
    json_items,
    load_image,
    nearest_texts,
    nms,
    read_json,
    resolved,
    rgb_hex,
    write_json,
)
from .ocr import text_items_from_json
from .primitives import load_primitives
from .segment import infer_icon_label, load_sam_icons


def crop_box(
    bbox: BBox, size: tuple[int, int], pad: int = 3
) -> tuple[int, int, int, int]:
    x, y, w, h = bbox
    return (
        max(0, int(x) - pad),
        max(0, int(y) - pad),
        min(size[0], int(x + w) + pad),
        min(size[1], int(y + h) + pad),
    )


def load_descriptions(path: Path) -> DescriptionMap:
    if not path.exists():
        return {}
    descriptions: DescriptionMap = {}
    for item in json_items(read_json(path), "icons"):
        if isinstance(item, dict) and item.get("id"):
            descriptions[str(item["id"])] = cast(DescriptionRecord, cast(object, item))
    return descriptions


def preprocess_icon_crop(image: Image.Image, bbox: BBox, out_path: Path) -> None:
    x1, y1, x2, y2 = crop_box(bbox, image.size, pad=4)
    crop = image.crop((x1, y1, x2, y2)).convert("RGB")
    arr = np.array(crop)
    border = np.concatenate(
        [
            arr[:2].reshape(-1, 3),
            arr[-2:].reshape(-1, 3),
            arr[:, :2].reshape(-1, 3),
            arr[:, -2:].reshape(-1, 3),
        ]
    )
    bg = np.median(border, axis=0)
    delta = np.linalg.norm(arr.astype(np.float32) - bg.astype(np.float32), axis=2)
    mask = (delta > 24).astype(np.uint8) * 255
    kernel = np.ones((2, 2), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=1)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)
    smoothed = cv2.bilateralFilter(arr, 5, 30, 30)
    result = np.full_like(smoothed, 255)
    result[mask > 0] = smoothed[mask > 0]
    pil = Image.fromarray(result).resize(
        (max(1, crop.width * 4), max(1, crop.height * 4)), Image.Resampling.LANCZOS
    )
    pil.quantize(colors=8).convert("RGB").save(out_path)


def trace_icon_crops(
    image: Image.Image,
    icons: list[IconProposal],
    descriptions: DescriptionMap,
    out_dir: Path,
    trace_icons: bool,
) -> list[str]:
    trace_dir = out_dir / "icons"
    trace_dir.mkdir(parents=True, exist_ok=True)
    kept: list[IconProposal] = []
    unresolved: list[str] = []
    for icon in icons:
        decision = descriptions.get(icon["id"], {})
        icon["label"] = infer_icon_label(icon, descriptions)
        action = decision.get("action", "trace")
        if action == "ignore":
            continue
        kept.append(icon)
        if action == "unresolved":
            unresolved.append(icon["id"])
            continue
        replacement = decision.get("svg")
        if action == "replace" and replacement:
            icon["svg"] = str(replacement)
            icon["source"] = "agent-provided"
            continue

        if not trace_icons or action == "replace":
            unresolved.append(icon["id"])
            continue

        x1, y1, x2, y2 = crop_box(icon["bbox"], image.size)
        if x2 <= x1 or y2 <= y1:
            unresolved.append(icon["id"])
            continue
        crop_path = trace_dir / f"{icon['id']}.prep.png"
        svg_path = trace_dir / f"{icon['id']}.svg"
        raw_crop_path = trace_dir / f"{icon['id']}.png"
        image.crop((x1, y1, x2, y2)).save(raw_crop_path)
        preprocess_icon_crop(image, icon["bbox"], crop_path)
        vtracer.convert_image_to_svg_py(
            str(crop_path),
            str(svg_path),
            colormode="color",
            hierarchical="stacked",
            filter_speckle=12,
            color_precision=6,
            layer_difference=16,
            mode="spline",
            corner_threshold=90,
            length_threshold=6.0,
            max_iterations=10,
            splice_threshold=45,
            path_precision=1,
        )
        icon["svg"] = str(svg_path.relative_to(out_dir))
        icon["source"] = "vtracer-crop"
        unresolved.append(icon["id"])
    icons[:] = kept
    return unresolved


def scene_text(item: TextItem) -> SceneText:
    record: SceneText = {
        "id": item.id,
        "type": "text",
        "text": item.text,
        "bbox": item.bbox,
    }
    if item.rotate:
        record["rotate"] = item.rotate
    if item.writing_mode:
        record["writing_mode"] = item.writing_mode
    return record


def scene_elements(
    rects: list[RectPrimitive],
    lines: list[LinePrimitive],
    icons: list[IconProposal],
    texts: list[TextItem],
) -> list[SceneElement]:
    elements: list[SceneElement] = []
    for rect in rects:
        scene_rect: SceneRect = {
            "id": rect["id"],
            "type": rect["type"],
            "bbox": rect["bbox"],
            "fill": rect["fill"],
            "stroke": rect["stroke"],
        }
        label = bbox_text_label(rect["bbox"], texts)
        if label:
            scene_rect["label"] = label
        if "rx" in rect:
            scene_rect["rx"] = rect["rx"]
        elements.append(scene_rect)
    for line in lines:
        scene_line: SceneLine = {
            "id": line["id"],
            "type": line["type"],
            "points": line["points"],
        }
        if line.get("arrow_start"):
            scene_line["arrow_start"] = True
        if line.get("arrow_end"):
            scene_line["arrow_end"] = True
        elements.append(scene_line)
    for icon in icons:
        scene_icon: SceneIcon = {
            "id": icon["id"],
            "type": "icon",
            "label": icon["label"],
            "bbox": icon["bbox"],
        }
        if "svg" in icon:
            scene_icon["svg"] = icon["svg"]
        elements.append(scene_icon)
    elements.extend(scene_text(item) for item in texts)
    return elements


def make_scene(
    source: Image.Image,
    elements: list[SceneElement],
    unresolved: list[str],
) -> Scene:
    scene: Scene = {
        "width": source.width,
        "height": source.height,
        "background": rgb_hex(border_rgb(source)),
        "elements": elements,
        "unresolved": sorted(set(unresolved)),
    }
    return scene


def load_scene(path: Path) -> Scene:
    raw = read_json(path)
    if not isinstance(raw, dict):
        raise ValueError(f"invalid scene JSON: {path}")
    return cast(Scene, cast(object, raw))


def write_icon_trace(
    out_dir: Path, icons: list[IconProposal], unresolved: list[str]
) -> None:
    trace: IconTraceJson = {"icons": icons, "unresolved": sorted(set(unresolved))}
    write_json(out_dir / "icon-trace.json", trace)


def prepare_source(input_path: Path, out_dir: Path) -> Image.Image:
    out_dir.mkdir(parents=True, exist_ok=True)
    source = load_image(resolved(input_path))
    source.save(out_dir / "source.png")
    return source


def write_describe_template(out_dir: Path) -> None:
    texts = text_items_from_json(out_dir / "ocr.json")
    _, _, icons = load_primitives(out_dir)
    icons = nms([*load_sam_icons(out_dir), *icons], 0.45)
    source = load_image(out_dir / "source.png")
    crop_dir = out_dir / "describe-crops"
    crop_dir.mkdir(parents=True, exist_ok=True)
    items: list[DescriptionItem] = []
    for icon in icons:
        x1, y1, x2, y2 = crop_box(icon["bbox"], source.size)
        crop_path = crop_dir / f"{icon['id']}.png"
        source.crop((x1, y1, x2, y2)).save(crop_path)
        nearby = nearest_texts(icon["bbox"], texts, 6)
        items.append(
            {
                "id": icon["id"],
                "crop": str(crop_path),
                "nearby_text": [
                    {"id": t.id, "text": t.text, "bbox": t.bbox} for t in nearby
                ],
                "label": "" if icon["label"] == "unresolved" else icon["label"],
                "action": "trace",
                "svg": "",
            }
        )
    descriptions: DescriptionsJson = {"icons": items}
    write_json(out_dir / "describe-input.json", descriptions)
    if not (out_dir / "descriptions.json").exists():
        write_json(out_dir / "descriptions.json", descriptions)


def assemble_scene(out_dir: Path, trace_icons: bool) -> Scene:
    source = load_image(out_dir / "source.png")
    texts = text_items_from_json(out_dir / "ocr.json")
    rects, lines, icons = load_primitives(out_dir)
    icons = nms([*load_sam_icons(out_dir), *icons], 0.45)
    descriptions = load_descriptions(out_dir / "descriptions.json")
    unresolved = trace_icon_crops(
        source,
        icons,
        descriptions,
        out_dir,
        trace_icons=trace_icons,
    )
    write_icon_trace(out_dir, icons, unresolved)
    scene = make_scene(
        source,
        scene_elements(rects, lines, icons, texts),
        unresolved,
    )
    write_json(out_dir / "scene.json", scene)
    return scene
