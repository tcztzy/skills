import xml.etree.ElementTree as ET
from pathlib import Path
from typing import cast

from PIL import Image, ImageDraw

from .common import (
    BBoxDrawable,
    DEBUG_COLORS,
    DEFAULT_LAYER,
    DrawableElement,
    SVG_LAYERS,
    SVG_NS,
    Scene,
    SceneIcon,
    SceneLine,
    SceneRect,
    SceneText,
    num,
    tag,
)

ET.register_namespace("", SVG_NS)


def add_arrow_defs(root: ET.Element) -> None:
    defs = ET.SubElement(root, tag("defs"))
    marker = ET.SubElement(
        defs,
        tag("marker"),
        {
            "id": "arrow",
            "viewBox": "0 0 10 10",
            "refX": "9",
            "refY": "5",
            "markerWidth": "7",
            "markerHeight": "7",
            "orient": "auto-start-reverse",
        },
    )
    ET.SubElement(
        marker, tag("path"), {"d": "M 0 0 L 10 5 L 0 10 z", "fill": "context-stroke"}
    )


def add_text(parent: ET.Element, item: SceneText) -> None:
    x, y, w, h = item["bbox"]
    font_size = max(1.0, h * 0.78)
    base: dict[str, str] = {
        "id": item["id"],
        "x": num(x),
        "y": num(y + min(h * 0.82, font_size)),
        "font-family": "Arial, Helvetica, sans-serif",
        "font-size": num(font_size),
        "font-weight": "400",
        "fill": "#111111",
    }
    writing_mode = item.get("writing_mode")
    if writing_mode:
        base["writing-mode"] = writing_mode
    else:
        base["textLength"] = num(w)
        base["lengthAdjust"] = "spacingAndGlyphs"
    rotate = item.get("rotate")
    if rotate:
        base["transform"] = f"rotate({num(rotate)} {num(x + w / 2)} {num(y + h / 2)})"
    elem = ET.SubElement(parent, tag("text"), {k: v for k, v in base.items() if v})
    elem.text = item["text"]


def add_rect(parent: ET.Element, item: SceneRect) -> None:
    x, y, w, h = item["bbox"]
    base: dict[str, str] = {
        "id": item["id"],
        "x": num(x),
        "y": num(y),
        "width": num(w),
        "height": num(h),
        "fill": item["fill"],
        "stroke": item["stroke"],
        "stroke-width": "1.5",
    }
    if "rx" in item:
        base["rx"] = num(item["rx"])
    label = item.get("label")
    if label:
        base["data-label"] = label
    ET.SubElement(parent, tag("rect"), {k: v for k, v in base.items() if v != ""})


def add_path(parent: ET.Element, item: SceneLine) -> None:
    if not item["points"]:
        return
    head, *tail = item["points"]
    d = " ".join(
        [f"M {num(head[0])} {num(head[1])}", *[f"L {num(x)} {num(y)}" for x, y in tail]]
    )
    base: dict[str, str] = {
        "id": item["id"],
        "d": d,
        "fill": "none",
        "stroke": "#374151",
        "stroke-width": "1.5",
    }
    if item.get("arrow_end"):
        base["marker-end"] = "url(#arrow)"
    if item.get("arrow_start"):
        base["marker-start"] = "url(#arrow)"
    ET.SubElement(parent, tag("path"), {k: v for k, v in base.items() if v != ""})


def add_icon(parent: ET.Element, item: SceneIcon, scene_dir: Path) -> None:
    x, y, w, h = item["bbox"]
    group = ET.SubElement(
        parent,
        tag("g"),
        {"id": item["id"], "data-label": item["label"]},
    )
    source = item.get("svg")
    if not source:
        ET.SubElement(
            group,
            tag("rect"),
            {
                "x": num(x),
                "y": num(y),
                "width": num(w),
                "height": num(h),
                "fill": "none",
                "stroke": "#d00",
            },
        )
        return
    icon_path = Path(source)
    if not icon_path.is_absolute():
        icon_path = (scene_dir / icon_path).resolve()
    icon_root = ET.parse(icon_path).getroot()
    view_box = icon_root.get(
        "viewBox", f"0 0 {icon_root.get('width', w)} {icon_root.get('height', h)}"
    )
    parts = [float(part) for part in view_box.replace(",", " ").split()[:4]]
    sx = w / parts[2] if len(parts) == 4 and parts[2] else 1
    sy = h / parts[3] if len(parts) == 4 and parts[3] else 1
    group.set("transform", f"translate({num(x)} {num(y)}) scale({num(sx)} {num(sy)})")
    for child in list(icon_root):
        group.append(child)


def compose_svg(scene: Scene, scene_dir: Path, output: Path) -> None:
    width = int(scene["width"])
    height = int(scene["height"])
    root = ET.Element(
        tag("svg"),
        {
            "width": str(width),
            "height": str(height),
            "viewBox": f"0 0 {width} {height}",
            "version": "1.1",
        },
    )
    ET.SubElement(
        root,
        tag("rect"),
        {
            "id": "canvas-background",
            "x": "0",
            "y": "0",
            "width": str(width),
            "height": str(height),
            "fill": scene["background"],
        },
    )
    add_arrow_defs(root)
    layers = {name: ET.SubElement(root, tag("g"), {"id": name}) for name in SVG_LAYERS}
    for item in scene["elements"]:
        kind = item["type"]
        layer_name = DEFAULT_LAYER.get(kind, "unresolved")
        layer = layers[layer_name if layer_name in layers else "unresolved"]
        if kind == "text":
            add_text(layer, cast(SceneText, item))
        elif kind in {"rect", "roundrect"}:
            add_rect(layer, cast(SceneRect, item))
        elif kind in {"line", "arrow"}:
            add_path(layer, cast(SceneLine, item))
        elif kind == "icon":
            add_icon(layer, cast(SceneIcon, item), scene_dir)
    ET.ElementTree(root).write(output, encoding="utf-8", xml_declaration=True)


def draw_debug(
    image: Image.Image, elements: list[DrawableElement], output: Path
) -> None:
    canvas = image.convert("RGB")
    draw = ImageDraw.Draw(canvas)
    for item in elements:
        color = DEBUG_COLORS.get(item.get("type"), "magenta")
        if item["type"] in {"line", "arrow"}:
            line = cast(SceneLine, item)
            draw.line([tuple(p) for p in line["points"]], fill=color, width=2)
        if "bbox" in item:
            boxed = cast(BBoxDrawable, item)
            x, y, w, h = boxed["bbox"]
            draw.rectangle([x, y, x + w, y + h], outline=color, width=2)
            draw.text((x, max(0, y - 12)), item.get("id", ""), fill=color)
    canvas.save(output)
