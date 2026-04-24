import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, NotRequired, Protocol, TypedDict

import numpy as np
from PIL import Image


SVG_NS = "http://www.w3.org/2000/svg"
MODEL_ID = "mlx-community/sam3.1-bf16"
SVG_LAYERS = ["containers", "connectors", "icons", "text", "unresolved"]
DEFAULT_LAYER = {
    "text": "text",
    "rect": "containers",
    "roundrect": "containers",
    "line": "connectors",
    "arrow": "connectors",
    "icon": "icons",
}
DEBUG_COLORS = {
    "text": "blue",
    "roundrect": "green",
    "rect": "green",
    "line": "orange",
    "arrow": "orange",
    "icon": "red",
}
SVG_COUNT_TAGS = ["text", "rect", "path", "image", "g"]

type BBox = list[float]
type Point = list[float]
type Poly = list[Point]
type JsonScalar = str | int | float | bool | None
type JsonValue = JsonScalar | list[JsonValue] | dict[str, JsonValue]
type JsonObject = dict[str, JsonValue]
type IconAction = Literal["trace", "replace", "ignore", "unresolved"]


class OcrText(TypedDict):
    id: str
    text: str
    bbox: BBox
    poly: Poly
    score: float | None
    rotate: float
    writing_mode: str | None


class SceneText(TypedDict):
    id: str
    type: Literal["text"]
    text: str
    bbox: BBox
    rotate: NotRequired[float]
    writing_mode: NotRequired[str]


class SceneRect(TypedDict):
    id: str
    type: Literal["rect", "roundrect"]
    bbox: BBox
    fill: str
    stroke: str
    label: NotRequired[str]
    rx: NotRequired[float]


class RectPrimitive(SceneRect):
    score: float


class SceneLine(TypedDict):
    id: str
    type: Literal["line", "arrow"]
    points: Poly
    arrow_start: NotRequired[bool]
    arrow_end: NotRequired[bool]


class LinePrimitive(SceneLine):
    bbox: BBox
    score: float


class SceneIcon(TypedDict):
    id: str
    type: Literal["icon"]
    label: str
    bbox: BBox
    svg: NotRequired[str]


class IconProposal(SceneIcon):
    source: str
    score: float
    mask: NotRequired[str]


type SceneElement = SceneText | SceneRect | SceneLine | SceneIcon
type PrimitiveElement = RectPrimitive | LinePrimitive | IconProposal
type DrawableElement = SceneElement | PrimitiveElement
type BBoxDrawable = (
    SceneText | SceneRect | SceneIcon | RectPrimitive | LinePrimitive | IconProposal
)
type BBoxElement = RectPrimitive | LinePrimitive | IconProposal


class Scene(TypedDict):
    width: int
    height: int
    background: str
    elements: list[SceneElement]
    unresolved: list[str]


class PrimitivesJson(TypedDict):
    containers: list[RectPrimitive]
    connectors: list[LinePrimitive]
    icons: list[IconProposal]


class OcrJson(TypedDict):
    texts: list[OcrText]


class OcrRawJson(TypedDict):
    pages: list[JsonObject]


class OcrDebugJson(TypedDict):
    items: list[OcrText]


class NearbyText(TypedDict):
    id: str
    text: str
    bbox: BBox


class DescriptionItem(TypedDict):
    id: str
    crop: str
    nearby_text: list[NearbyText]
    label: str
    action: IconAction
    svg: str


class DescriptionRecord(TypedDict, total=False):
    label: str
    action: IconAction
    svg: str


type DescriptionMap = dict[str, DescriptionRecord]


class DescriptionsJson(TypedDict):
    icons: list[DescriptionItem]


class SamJson(TypedDict):
    prompts: list[str]
    threshold: float
    proposals: list[IconProposal]


class AuditJson(TypedDict):
    svg: str
    scene: str
    unresolved: list[str]
    svg_counts: dict[str, int]


class IconTraceJson(TypedDict):
    icons: list[IconProposal]
    unresolved: list[str]


class TimedStep(TypedDict):
    elapsed_ms: float


class PrepareStep(TimedStep):
    step: Literal["prepare"]
    input: str
    source: str
    size: list[int]


class OcrStep(TimedStep):
    step: Literal["ocr"]
    engine: str
    output: str
    boxes: str
    overlay: str
    text_items: int


class MaskPreviewStep(TimedStep):
    step: Literal["mask_preview"]
    output: str
    masked_items: int


class CvPrimitivesStep(TimedStep):
    step: Literal["cv_primitives"]
    containers: int
    connectors: int
    icon_candidates: int


class SegmentationStep(TimedStep):
    step: Literal["segmentation"]
    status: str
    prompts: list[str]
    proposals: int
    merged_icons: int
    output: str


class IconsStep(TimedStep):
    step: Literal["icons"]
    total: int
    unresolved: int
    trace_log: str
    primitives: str


class ComposeStep(TimedStep):
    step: Literal["compose"]
    scene: str
    svg: str
    debug: NotRequired[str]
    elements: int


type StepRecord = (
    PrepareStep
    | OcrStep
    | MaskPreviewStep
    | CvPrimitivesStep
    | SegmentationStep
    | IconsStep
    | ComposeStep
)


class StepsJson(TypedDict):
    steps: list[StepRecord]


class ReportArtifacts(TypedDict):
    source: str
    ocr: str
    ocr_raw: str
    ocr_boxes: str
    ocr_boxes_csv: str
    ocr_overlay: str
    primitives: str
    primitives_overlay: str
    icon_trace: str
    steps: str
    scene: str
    masked: NotRequired[str]
    debug: NotRequired[str]


class ReportJson(TypedDict):
    input: str
    output_svg: str
    text_items: int
    containers: int
    connectors: int
    icons: int
    unresolved: list[str]
    sam: str
    elapsed_ms: float
    artifacts: ReportArtifacts


class SupportsToList(Protocol):
    def tolist(self) -> object: ...


@dataclass
class TextItem:
    id: str
    text: str
    bbox: BBox
    poly: Poly
    score: float | None
    rotate: float
    writing_mode: str | None


def tag(name: str) -> str:
    return f"{{{SVG_NS}}}{name}"


def num(value: float | int | str) -> str:
    if isinstance(value, str):
        return value
    rounded = round(float(value), 3)
    return str(int(rounded)) if rounded == int(rounded) else str(rounded)


def parse_float(value: object) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int | float):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return None
    return None


def parse_float_list(value: object, length: int) -> list[float] | None:
    if not isinstance(value, list) or len(value) < length:
        return None
    parsed: list[float] = []
    for item in value[:length]:
        number = parse_float(item)
        if number is None:
            return None
        parsed.append(number)
    return parsed


def clean_json(value: object) -> JsonValue:
    if value is None or isinstance(value, str | int | float | bool):
        return value
    if isinstance(value, np.ndarray):
        return clean_json(value.tolist())
    if isinstance(value, np.generic):
        return clean_json(value.item())
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(k): clean_json(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [clean_json(v) for v in value]
    return str(value)


def write_json(path: Path, data: object) -> None:
    path.write_text(json.dumps(clean_json(data), indent=2, ensure_ascii=False) + "\n")


def read_json(path: Path) -> JsonValue:
    return clean_json(json.loads(path.read_text()))


def resolved(path: Path) -> Path:
    return path.expanduser().resolve()


def json_items(raw: JsonValue, *keys: str) -> list[JsonValue]:
    if not isinstance(raw, dict):
        return raw if isinstance(raw, list) else []
    for key in keys:
        value = raw.get(key)
        if isinstance(value, list):
            return value
    return []


def bbox_from_poly(poly: Poly) -> BBox:
    xs = [float(p[0]) for p in poly]
    ys = [float(p[1]) for p in poly]
    x1, x2 = min(xs), max(xs)
    y1, y2 = min(ys), max(ys)
    return [x1, y1, max(1.0, x2 - x1), max(1.0, y2 - y1)]


def normalize_poly(value: object | None, fallback_box: object | None = None) -> Poly:
    if value is not None:
        points = clean_json(value)
        if isinstance(points, list) and points:
            poly: Poly = []
            for point in points[:4]:
                pair = parse_float_list(point, 2)
                if pair:
                    poly.append([pair[0], pair[1]])
            if poly:
                return poly
    if fallback_box is not None:
        raw_box = clean_json(fallback_box)
        box = parse_float_list(raw_box, 4)
        if box:
            x1, y1, x2, y2 = box
            return [[x1, y1], [x2, y1], [x2, y2], [x1, y2]]
    return [[0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 1.0]]


def poly_angle(poly: Poly) -> float:
    if len(poly) < 2:
        return 0.0
    dx = poly[1][0] - poly[0][0]
    dy = poly[1][1] - poly[0][1]
    angle = math.degrees(math.atan2(dy, dx))
    if abs(angle) < 2:
        return 0.0
    return round(angle, 2)


def score_at(values: object | None, index: int) -> float | None:
    if values is None:
        return None
    data = clean_json(values)
    if not isinstance(data, list) or index >= len(data):
        return None
    score = parse_float(data[index])
    return round(score, 4) if score is not None else None


def load_image(path: Path) -> Image.Image:
    image = Image.open(path)
    if image.mode == "RGB":
        return image.copy()
    rgba = image.convert("RGBA")
    base = Image.new("RGBA", rgba.size, (255, 255, 255, 255))
    base.alpha_composite(rgba)
    return base.convert("RGB")


def median_rgb(values: np.ndarray) -> tuple[int, int, int]:
    flat = values.reshape(-1, values.shape[-1])
    rgb = np.median(flat[:, :3], axis=0)
    return int(rgb[0]), int(rgb[1]), int(rgb[2])


def border_rgb(image: Image.Image) -> tuple[int, int, int]:
    arr = np.array(image.convert("RGB"))
    h, w = arr.shape[:2]
    band = max(2, min(h, w) // 120)
    samples = np.concatenate(
        [
            arr[:band, :, :3].reshape(-1, 3),
            arr[-band:, :, :3].reshape(-1, 3),
            arr[:, :band, :3].reshape(-1, 3),
            arr[:, -band:, :3].reshape(-1, 3),
        ]
    )
    return median_rgb(samples)


def box_fill(
    image: Image.Image, bbox: BBox, fallback: tuple[int, int, int]
) -> tuple[int, int, int]:
    arr = np.array(image.convert("RGB"))
    h, w = arr.shape[:2]
    x, y, bw, bh = bbox
    x1 = max(0, int(x) - 4)
    y1 = max(0, int(y) - 4)
    x2 = min(w - 1, int(x + bw) + 4)
    y2 = min(h - 1, int(y + bh) + 4)
    samples: list[np.ndarray] = []
    if y1 > 0:
        samples.append(arr[y1 : y1 + 1, x1:x2])
    if y2 < h - 1:
        samples.append(arr[y2 : y2 + 1, x1:x2])
    if x1 > 0:
        samples.append(arr[y1:y2, x1 : x1 + 1])
    if x2 < w - 1:
        samples.append(arr[y1:y2, x2 : x2 + 1])
    if not samples:
        return fallback
    return median_rgb(np.concatenate([s.reshape(-1, 3) for s in samples if s.size]))


def bbox_intersection_area(a: BBox, b: BBox) -> float:
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    x1, y1 = max(ax, bx), max(ay, by)
    x2, y2 = min(ax + aw, bx + bw), min(ay + ah, by + bh)
    return max(0.0, x2 - x1) * max(0.0, y2 - y1)


def bbox_iou(a: BBox, b: BBox) -> float:
    inter = bbox_intersection_area(a, b)
    union = a[2] * a[3] + b[2] * b[3] - inter
    return inter / union if union else 0.0


def bbox_intersection_ratio(inner: BBox, outer: BBox) -> float:
    inter = bbox_intersection_area(inner, outer)
    return inter / max(1.0, inner[2] * inner[3])


def bbox_center(bbox: BBox) -> tuple[float, float]:
    x, y, w, h = bbox
    return x + w / 2, y + h / 2


def nearest_texts(bbox: BBox, texts: list[TextItem], limit: int) -> list[TextItem]:
    cx, cy = bbox_center(bbox)
    return sorted(
        texts,
        key=lambda t: math.hypot(
            cx - bbox_center(t.bbox)[0], cy - bbox_center(t.bbox)[1]
        ),
    )[:limit]


def bbox_text_label(bbox: BBox, texts: list[TextItem]) -> str | None:
    inside = [
        text
        for text in texts
        if (text.score is None or text.score >= 0.5)
        and bbox_intersection_ratio(text.bbox, bbox) >= 0.65
    ]
    if not inside:
        return None
    inside.sort(key=lambda item: (item.bbox[1], item.bbox[0]))
    return " ".join(item.text for item in inside[:4])


def text_like_conflict(
    bbox: BBox, texts: list[TextItem], threshold: float = 0.6
) -> bool:
    for text in texts:
        if len(text.text.strip()) < 2:
            continue
        if text.score is not None and text.score < 0.85:
            continue
        if bbox_intersection_ratio(bbox, text.bbox) >= threshold:
            return True
    return False


def nms[T: BBoxElement](items: list[T], threshold: float) -> list[T]:
    kept: list[T] = []
    for item in sorted(items, key=lambda item: float(item["score"]), reverse=True):
        if all(bbox_iou(item["bbox"], other["bbox"]) < threshold for other in kept):
            kept.append(item)
    return kept


def rgb_hex(rgb: tuple[int, int, int]) -> str:
    return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"
