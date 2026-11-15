
"""Hard-constraint checks for CropWise AI."""

REQUIRED_PROFILE_FIELDS = [
    "water_need",
    "heat_tolerance",
    "drought_tolerance",
    "ph_range",
    "soil_ok",
]


def check_constraints(rotation, crops_by_id, context=None):
    context = context or {}
    reject_reasons = []
    missing_info = []

    crop_ids = rotation.get("crops", [])

    if not crop_ids:
        reject_reasons.append("Rotation contains no crops.")

    allowed_crops = context.get("allowed_crops")
    soil_type = context.get("soil_type")

    for crop_id in crop_ids:
        crop = crops_by_id.get(crop_id)

        if crop is None:
            reject_reasons.append(f"Unknown crop profile: {crop_id}")
            continue

        if allowed_crops is not None and crop_id not in allowed_crops:
            reject_reasons.append(f"{crop_id} is excluded by the supplied crop restrictions.")

        soil_ok = crop.get("soil_ok")
        if soil_type and isinstance(soil_ok, list) and soil_type not in soil_ok:
            reject_reasons.append(
                f"{crop_id} is not listed as suitable for soil type {soil_type}."
            )

        for field in REQUIRED_PROFILE_FIELDS:
            if crop.get(field) is None:
                missing_info.append(f"{crop_id}: {field} has not been verified.")

    return {
        "status": "rejected" if reject_reasons else "ok",
        "reject_reasons": reject_reasons,
        "missing_info": missing_info,
        "needs_expert_review": bool(reject_reasons or missing_info),
    }
