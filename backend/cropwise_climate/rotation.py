"""Rotation comparison adapter for the CropWise AI decision engine."""

import json
from pathlib import Path

from decision_engine.scoring import build_crop_scores, score_rotation

BACKEND_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = BACKEND_ROOT / "data"

with (DATA_DIR / "decision_crops.json").open(encoding="utf-8") as f:
    crop_data = json.load(f)

with (DATA_DIR / "decision_regions.json").open(encoding="utf-8") as f:
    region_data = json.load(f)

CROPS_BY_ID = {
    crop["crop_id"]: crop
    for crop in crop_data["crops"]
}

CROP_SCORES = build_crop_scores(CROPS_BY_ID)


def compare_rotation(region_id: str, rotation_id: str) -> dict:
    regions = region_data["regions"]

    if region_id not in regions:
        raise KeyError(f"Unknown region: {region_id}")

    region = regions[region_id]
    rotations = region.get("rotations", [])

    rotation = next(
        (item for item in rotations if item.get("id") == rotation_id),
        None,
    )

    if rotation is None:
        raise LookupError(
            f"Rotation '{rotation_id}' not found in region '{region_id}'."
        )

    result = score_rotation(
        rotation=rotation,
        crops_by_id=CROPS_BY_ID,
        crop_scores=CROP_SCORES,
    )

    crop_evidence = []
    for crop_id in rotation.get("crops", []):
        crop = CROPS_BY_ID.get(crop_id)
        if crop is None:
            crop_evidence.append({
                "crop_id": crop_id,
                "status": "missing_crop_profile",
            })
            continue

        crop_evidence.append({
            "crop_id": crop_id,
            "name_en": crop.get("name_en"),
            "name_hi": crop.get("name_hi"),
            "source_url": crop.get("source_url"),
            "evidence": crop.get("evidence", {}),
        })

    return {
        "region_id": region_id,
        "state": region.get("state"),
        "district": region.get("district"),
        "rotation_id": rotation_id,
        "rotation_type": rotation.get("type"),
        "crops": rotation.get("crops", []),
        "label": rotation.get("label"),
        "decision_status": "provisional",
        "score_label": "Partial illustrative comparison score",
        "score_note": (
            "Illustrative team estimates only. "
            "Not a validated crop suitability score."
        ),
        "result": result,
        "crop_evidence": crop_evidence,
        "limitations": [
            "Crop ratings are illustrative team estimates, not verified agronomic measurements.",
            "Soil health, crop suitability and economics are not currently scored.",
            "This is an example comparison, not a farming recommendation.",
            "Expert review is required before practical agricultural use.",
        ],
    }
