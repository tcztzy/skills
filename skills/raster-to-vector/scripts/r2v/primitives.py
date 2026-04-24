import math
from pathlib import Path
from typing import cast

import cv2
import numpy as np
from PIL import Image

from .common import (
    BBox,
    IconProposal,
    LinePrimitive,
    Poly,
    PrimitivesJson,
    RectPrimitive,
    TextItem,
    median_rgb,
    nms,
    read_json,
    rgb_hex,
    text_like_conflict,
    write_json,
)
from .compose import draw_debug


def detect_rectangles(image: np.ndarray, min_area: int) -> list[RectPrimitive]:
    h, w = image.shape[:2]
    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    edges = cv2.Canny(cv2.GaussianBlur(gray, (3, 3), 0), 50, 140)
    edges = cv2.morphologyEx(
        edges, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8), iterations=2
    )
    contours, _ = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    rects: list[RectPrimitive] = []
    for contour in contours:
        x, y, rw, rh = cv2.boundingRect(contour)
        area = rw * rh
        if area < min_area or rw < 28 or rh < 22 or area > w * h * 0.92:
            continue
        contour_area = abs(cv2.contourArea(contour))
        rectangularity = contour_area / area if area else 0
        peri = cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, 0.03 * peri, True)
        if rectangularity < 0.58 and len(approx) not in {4, 5, 6, 7, 8}:
            continue
        pad = max(1, min(rw, rh) // 12)
        crop = image[
            max(0, y + pad) : min(h, y + rh - pad),
            max(0, x + pad) : min(w, x + rw - pad),
        ]
        border = np.concatenate(
            [
                image[max(0, y - 1) : min(h, y + 2), x : x + rw].reshape(-1, 3),
                image[max(0, y + rh - 2) : min(h, y + rh + 1), x : x + rw].reshape(
                    -1, 3
                ),
                image[y : y + rh, max(0, x - 1) : min(w, x + 2)].reshape(-1, 3),
                image[y : y + rh, max(0, x + rw - 2) : min(w, x + rw + 1)].reshape(
                    -1, 3
                ),
            ]
        )
        rects.append(
            {
                "id": f"container-{len(rects):04d}",
                "type": "roundrect",
                "bbox": [x, y, rw, rh],
                "rx": round(min(10, max(2, min(rw, rh) * 0.08)), 2),
                "fill": rgb_hex(
                    median_rgb(crop if crop.size else image[y : y + rh, x : x + rw])
                ),
                "stroke": rgb_hex(median_rgb(border)),
                "score": round(float(rectangularity), 3),
            }
        )
    return nms(rects, 0.72)


def rect_edge(line: Poly, rect: BBox, tol: float = 5) -> bool:
    (x1, y1), (x2, y2) = line
    rx, ry, rw, rh = rect
    horizontal = (
        abs(y1 - y2) <= tol and rx - tol <= min(x1, x2) and max(x1, x2) <= rx + rw + tol
    )
    vertical = (
        abs(x1 - x2) <= tol and ry - tol <= min(y1, y2) and max(y1, y2) <= ry + rh + tol
    )
    return (horizontal and (abs(y1 - ry) <= tol or abs(y1 - (ry + rh)) <= tol)) or (
        vertical and (abs(x1 - rx) <= tol or abs(x1 - (rx + rw)) <= tol)
    )


def triangle_centers(gray: np.ndarray) -> list[tuple[float, float]]:
    edges = cv2.Canny(gray, 60, 150)
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    centers: list[tuple[float, float]] = []
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        if w * h < 20 or w > 40 or h > 40:
            continue
        approx = cv2.approxPolyDP(contour, 0.08 * cv2.arcLength(contour, True), True)
        if len(approx) == 3:
            centers.append((x + w / 2, y + h / 2))
    return centers


def near_any(
    point: list[float], centers: list[tuple[float, float]], radius: float
) -> bool:
    return any(math.hypot(point[0] - cx, point[1] - cy) <= radius for cx, cy in centers)


def detect_lines(
    image: np.ndarray,
    rects: list[RectPrimitive],
    min_len: int,
    texts: list[TextItem] | None = None,
) -> list[LinePrimitive]:
    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    edges = cv2.Canny(cv2.GaussianBlur(gray, (3, 3), 0), 50, 150)
    raw = cv2.HoughLinesP(
        edges, 1, np.pi / 180, threshold=35, minLineLength=min_len, maxLineGap=8
    )
    if raw is None:
        return []
    heads = triangle_centers(gray)
    lines: list[LinePrimitive] = []
    for entry in raw.reshape(-1, 4):
        x1, y1, x2, y2 = [int(v) for v in entry]
        length = math.hypot(x2 - x1, y2 - y1)
        if length < min_len:
            continue
        points: Poly = [[x1, y1], [x2, y2]]
        if any(rect_edge(points, rect["bbox"]) for rect in rects):
            continue
        line_bbox: BBox = [
            min(x1, x2),
            min(y1, y2),
            abs(x2 - x1) or 1,
            abs(y2 - y1) or 1,
        ]
        if texts and text_like_conflict(line_bbox, texts, threshold=0.7):
            continue
        arrow_start = near_any(points[0], heads, 18)
        arrow_end = near_any(points[1], heads, 18) or not arrow_start
        line: LinePrimitive = {
            "id": f"connector-{len(lines):04d}",
            "type": "arrow" if arrow_start or arrow_end else "line",
            "points": points,
            "bbox": line_bbox,
            "score": round(length, 2),
        }
        if arrow_start:
            line["arrow_start"] = True
        if arrow_end:
            line["arrow_end"] = True
        lines.append(line)
    return nms(lines, 0.5)


def detect_icon_candidates(
    image: np.ndarray, texts: list[TextItem], rects: list[RectPrimitive]
) -> list[IconProposal]:
    bg = np.array(
        median_rgb(
            np.concatenate(
                [image[:2, :, :3].reshape(-1, 3), image[-2:, :, :3].reshape(-1, 3)]
            )
        ),
        dtype=np.int16,
    )
    delta = np.linalg.norm(image.astype(np.int16) - bg, axis=2)
    mask = (delta > 35).astype(np.uint8) * 255
    mask = cv2.morphologyEx(
        mask, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8), iterations=1
    )
    count, _, stats, _ = cv2.connectedComponentsWithStats(mask, connectivity=8)
    icons: list[IconProposal] = []
    h, w = image.shape[:2]
    for label in range(1, count):
        x, y, bw, bh, area = [int(v) for v in stats[label]]
        if area < 60 or bw < 8 or bh < 8 or bw > w * 0.22 or bh > h * 0.22:
            continue
        if bw / max(1, bh) > 8 or bh / max(1, bw) > 8:
            continue
        bbox: BBox = [x, y, bw, bh]
        if text_like_conflict(bbox, texts, threshold=0.72):
            continue
        icons.append(
            {
                "id": f"icon-{len(icons):04d}",
                "type": "icon",
                "label": "unresolved",
                "bbox": bbox,
                "source": "cv",
                "score": float(area),
            }
        )
    return nms(icons, 0.45)


def write_primitives_debug(
    image: Image.Image,
    rects: list[RectPrimitive],
    lines: list[LinePrimitive],
    icons: list[IconProposal],
    out_dir: Path,
) -> None:
    data: PrimitivesJson = {"containers": rects, "connectors": lines, "icons": icons}
    write_json(out_dir / "primitives.json", data)
    draw_debug(image, [*rects, *lines, *icons], out_dir / "primitives.png")


def load_primitives(
    out_dir: Path,
) -> tuple[list[RectPrimitive], list[LinePrimitive], list[IconProposal]]:
    path = out_dir / "primitives.json"
    if not path.exists():
        return [], [], []
    raw = read_json(path)
    if not isinstance(raw, dict):
        return [], [], []
    containers = raw.get("containers", [])
    connectors = raw.get("connectors", [])
    icons = raw.get("icons", [])
    return (
        cast(list[RectPrimitive], containers if isinstance(containers, list) else []),
        cast(list[LinePrimitive], connectors if isinstance(connectors, list) else []),
        cast(list[IconProposal], icons if isinstance(icons, list) else []),
    )
