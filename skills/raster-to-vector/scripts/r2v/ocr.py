import csv
import json
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw

from .common import (
    JsonObject,
    OcrDebugJson,
    OcrJson,
    OcrRawJson,
    OcrText,
    TextItem,
    bbox_from_poly,
    border_rgb,
    box_fill,
    clean_json,
    json_items,
    normalize_poly,
    parse_float,
    parse_float_list,
    poly_angle,
    read_json,
    score_at,
    write_json,
)


def result_to_dict(result: object, scratch: Path) -> JsonObject:
    candidates: list[object] = []
    if isinstance(result, dict):
        candidates.append(result)
    for name in ("json", "to_dict", "dict"):
        if hasattr(result, name):
            attr = getattr(result, name)
            try:
                candidates.append(attr() if callable(attr) else attr)
            except TypeError:
                pass
    for candidate in candidates:
        cleaned = clean_json(candidate)
        if isinstance(cleaned, dict):
            return cleaned

    before = {p.resolve() for p in scratch.glob("*.json")}
    if hasattr(result, "save_to_json"):
        save_to_json = getattr(result, "save_to_json")
        if not callable(save_to_json):
            raise ValueError(f"cannot save PaddleOCR result object: {type(result)!r}")
        try:
            save_to_json(str(scratch))
        except TypeError:
            save_to_json(save_path=str(scratch))
        after = [p for p in scratch.glob("*.json") if p.resolve() not in before]
        if after:
            saved = read_json(max(after, key=lambda p: p.stat().st_mtime))
            if isinstance(saved, dict):
                return saved

    raise ValueError(f"cannot read PaddleOCR result object: {type(result)!r}")


def unwrap_res(raw: JsonObject) -> JsonObject:
    inner = raw.get("res")
    return inner if isinstance(inner, dict) else raw


def ocr_text(item: TextItem) -> OcrText:
    return {
        "id": item.id,
        "text": item.text,
        "bbox": item.bbox,
        "poly": item.poly,
        "score": item.score,
        "rotate": item.rotate,
        "writing_mode": item.writing_mode,
    }


def write_ocr_debug(image: Image.Image, texts: list[TextItem], out_dir: Path) -> None:
    items: list[OcrText] = []
    overlay = image.convert("RGB")
    draw = ImageDraw.Draw(overlay)
    csv_path = out_dir / "ocr-boxes.csv"
    for item in texts:
        x, y, w, h = item.bbox
        record = ocr_text(item)
        items.append(record)
        points = [tuple(p) for p in item.poly]
        draw.polygon(points, outline="#0057ff")
        draw.rectangle([x, y, x + w, y + h], outline="#ff2d55", width=2)
        draw.text(
            (x, max(0, y - 14)),
            f"{item.id} {item.score if item.score is not None else ''}",
            fill="#0057ff",
        )

    debug: OcrDebugJson = {"items": items}
    write_json(out_dir / "ocr-boxes.json", debug)
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "id",
                "text",
                "score",
                "bbox",
                "poly",
                "rotate",
                "writing_mode",
            ],
        )
        writer.writeheader()
        for record in items:
            writer.writerow(
                {
                    "id": record["id"],
                    "text": record["text"],
                    "score": record["score"],
                    "bbox": json.dumps(record["bbox"], ensure_ascii=False),
                    "poly": json.dumps(record["poly"], ensure_ascii=False),
                    "rotate": record["rotate"],
                    "writing_mode": record["writing_mode"],
                }
            )
    overlay.save(out_dir / "ocr-boxes.png")


def run_paddle_ocr(image_path: Path, out_dir: Path) -> list[TextItem]:
    from paddleocr import PaddleOCR

    ocr = PaddleOCR(
        use_doc_orientation_classify=False,
        use_doc_unwarping=False,
        use_textline_orientation=True,
    )
    raw_pages: list[JsonObject] = []
    texts: list[TextItem] = []
    with tempfile.TemporaryDirectory() as tmp:
        scratch = Path(tmp)
        for page in ocr.predict(str(image_path)):
            page_raw = result_to_dict(page, scratch)
            raw_pages.append(page_raw)
            res = unwrap_res(page_raw)
            rec_texts = res.get("rec_texts", [])
            rec_polys_value = res.get("rec_polys", res.get("dt_polys", []))
            rec_boxes_value = res.get("rec_boxes", [])
            rec_polys = rec_polys_value if isinstance(rec_polys_value, list) else []
            rec_boxes = rec_boxes_value if isinstance(rec_boxes_value, list) else []
            scores = res.get("rec_scores")
            angles_value = res.get("textline_orientation_angles", [])
            angles = angles_value if isinstance(angles_value, list) else []
            if not isinstance(rec_texts, list):
                continue
            for index, value in enumerate(rec_texts):
                text = str(value).strip()
                if not text:
                    continue
                poly = normalize_poly(
                    rec_polys[index] if index < len(rec_polys) else None,
                    rec_boxes[index] if index < len(rec_boxes) else None,
                )
                bbox = bbox_from_poly(poly)
                angle = poly_angle(poly)
                if isinstance(angles, list) and index < len(angles):
                    raw_angle = parse_float(angles[index])
                    if raw_angle is not None and raw_angle >= 0:
                        angle = raw_angle
                writing_mode = (
                    "tb"
                    if bbox[3] > bbox[2] * 1.45 and len(text) > 1 and abs(angle) < 10
                    else None
                )
                texts.append(
                    TextItem(
                        id=f"text-{len(texts):04d}",
                        text=text,
                        bbox=[round(x, 2) for x in bbox],
                        poly=[[round(x, 2), round(y, 2)] for x, y in poly],
                        score=score_at(scores, index),
                        rotate=0.0 if writing_mode else angle,
                        writing_mode=writing_mode,
                    )
                )

    ocr_raw: OcrRawJson = {"pages": raw_pages}
    write_json(out_dir / "ocr.raw.json", ocr_raw)
    ocr_json: OcrJson = {
        "texts": [ocr_text(item) for item in texts],
    }
    write_json(out_dir / "ocr.json", ocr_json)
    return texts


def mask_text(image: Image.Image, texts: list[TextItem], out_path: Path) -> Image.Image:
    result = image.copy()
    draw = ImageDraw.Draw(result)
    fallback = border_rgb(image)
    for item in texts:
        fill = box_fill(image, item.bbox, fallback)
        x, y, w, h = item.bbox
        draw.rectangle([max(0, x - 2), max(0, y - 2), x + w + 2, y + h + 2], fill=fill)
        draw.polygon([tuple(p) for p in item.poly], fill=fill)
    result.save(out_path)
    return result


def text_items_from_json(path: Path) -> list[TextItem]:
    if not path.exists():
        return []
    texts: list[TextItem] = []
    for index, item in enumerate(json_items(read_json(path), "texts", "items")):
        if not isinstance(item, dict):
            continue
        text = str(item.get("text", "")).strip()
        if not text:
            continue
        bbox_value = item.get("bbox", [0, 0, 1, 1])
        bbox = parse_float_list(bbox_value, 4) or [0.0, 0.0, 1.0, 1.0]
        fallback = [bbox[0], bbox[1], bbox[0] + bbox[2], bbox[1] + bbox[3]]
        poly = normalize_poly(item.get("poly"), fallback)
        score_value = item.get("score")
        score = parse_float(score_value) if score_value is not None else None
        writing_value = item.get("writing_mode")
        rotate = parse_float(item.get("rotate", 0)) or 0.0
        texts.append(
            TextItem(
                id=str(item.get("id", f"text-{index:04d}")),
                text=text,
                bbox=bbox,
                poly=poly,
                score=score,
                rotate=rotate,
                writing_mode=writing_value if isinstance(writing_value, str) else None,
            )
        )
    return texts
