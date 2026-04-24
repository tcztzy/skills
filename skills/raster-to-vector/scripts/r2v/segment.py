import os
import platform
from pathlib import Path
from typing import cast

import numpy as np
from PIL import Image

from .common import (
    DescriptionMap,
    IconProposal,
    MODEL_ID,
    SamJson,
    SupportsToList,
    json_items,
    read_json,
    write_json,
)


def supported_sam_host() -> bool:
    return platform.system() == "Darwin" and platform.machine() == "arm64"


def require_sam_host() -> None:
    if not supported_sam_host():
        raise RuntimeError(
            "unsupported platform: local segmentation requires Apple Silicon macOS"
        )


def as_array(value: object) -> np.ndarray:
    if value is None:
        return np.array([])
    if hasattr(value, "tolist"):
        return np.array(cast(SupportsToList, value).tolist())
    return np.array(value)


def run_sam(
    image: Image.Image,
    prompts: list[str],
    threshold: float,
    out_dir: Path,
    save_masks: bool,
) -> tuple[list[IconProposal], str]:
    require_sam_host()
    os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")

    from mlx_vlm.models.sam3.generate import Sam3Predictor
    from mlx_vlm.models.sam3_1.processing_sam3_1 import Sam31Processor
    from mlx_vlm.utils import get_model_path, load_model

    model_path = get_model_path(MODEL_ID)
    model = load_model(model_path)
    processor = Sam31Processor.from_pretrained(str(model_path))
    predictor = Sam3Predictor(model, processor, score_threshold=threshold)
    mask_dir = out_dir / "masks"
    if save_masks:
        mask_dir.mkdir(parents=True, exist_ok=True)

    proposals: list[IconProposal] = []
    for prompt in prompts:
        result = predictor.predict(image, text_prompt=prompt)
        boxes = as_array(getattr(result, "boxes", None))
        scores = as_array(getattr(result, "scores", None))
        masks = as_array(getattr(result, "masks", None))
        if boxes.size == 0:
            continue
        for index, box in enumerate(boxes):
            score = float(scores[index]) if scores.size > index else None
            if score is not None and score < threshold:
                continue
            x1, y1, x2, y2 = [float(v) for v in box[:4]]
            item: IconProposal = {
                "id": f"sam-{len(proposals):04d}",
                "type": "icon",
                "label": prompt,
                "bbox": [
                    round(x1, 2),
                    round(y1, 2),
                    round(x2 - x1, 2),
                    round(y2 - y1, 2),
                ],
                "source": "segmenter",
                "score": round(score, 4) if score is not None else 1.0,
            }
            if save_masks and masks.size and masks.shape[0] > index:
                mask = masks[index]
                if mask.shape != (image.height, image.width):
                    mask_img = Image.fromarray(
                        (mask > 0).astype(np.uint8) * 255
                    ).resize(image.size)
                else:
                    mask_img = Image.fromarray((mask > 0).astype(np.uint8) * 255)
                mask_path = mask_dir / f"{item['id']}.png"
                mask_img.save(mask_path)
                item["mask"] = str(mask_path.relative_to(out_dir))
            proposals.append(item)

    sam: SamJson = {"prompts": prompts, "threshold": threshold, "proposals": proposals}
    write_json(out_dir / "sam.json", sam)
    return proposals, "sam3-local"


def infer_icon_label(
    icon: IconProposal,
    descriptions: DescriptionMap | None = None,
) -> str:
    if descriptions and icon.get("id") in descriptions:
        item = descriptions[icon["id"]]
        label = str(item.get("label") or "").strip()
        if label:
            return label
    if icon.get("label") and icon["label"] != "unresolved":
        return str(icon["label"])
    return "unresolved"


def load_sam_icons(out_dir: Path) -> list[IconProposal]:
    path = out_dir / "sam.json"
    if not path.exists():
        return []
    icons: list[IconProposal] = []
    for item in json_items(read_json(path), "proposals"):
        if not isinstance(item, dict):
            continue
        icon = cast(IconProposal, cast(object, dict(item)))
        icon.setdefault("type", "icon")
        icon.setdefault("label", "unresolved")
        icon.setdefault("source", "segmenter")
        icons.append(icon)
    return icons
