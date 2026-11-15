
"""Transparent rotation scoring using explicitly classified crop inputs."""

WEIGHTS = {
    "water": 30,
    "soil_health": 25,
    "climate_resilience": 20,
    "crop_suitability": 15,
    "economics": 10,
}


def average(values):
    valid = [
        value for value in values
        if isinstance(value, (int, float)) and not isinstance(value, bool)
    ]
    return round(sum(valid) / len(valid), 2) if valid else None


def valid_rating(value):
    """Accept only numeric ratings from 1 to 5."""
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and 1 <= value <= 5
    )


def build_crop_scores(crops_by_id):
    """
    Convert crop profile ratings into 0-100 comparative scores.

    Water: lower water requirement produces a higher efficiency score.
    Climate resilience: average of heat and drought tolerance.
    Other criteria remain unavailable until evidence is supplied.
    """
    crop_scores = {}

    for crop_id, crop in crops_by_id.items():
        water_need = crop.get("water_need")
        heat = crop.get("heat_tolerance")
        drought = crop.get("drought_tolerance")

        water_score = (
            (6 - water_need) * 20
            if valid_rating(water_need)
            else None
        )

        climate_score = (
            round(average([heat, drought]) * 20, 2)
            if valid_rating(heat) and valid_rating(drought)
            else None
        )

        crop_scores[crop_id] = {
            "water": water_score,
            "soil_health": None,
            "climate_resilience": climate_score,
            "crop_suitability": None,
            "economics": None,
        }

    return crop_scores


def score_rotation(rotation, crops_by_id, crop_scores, context=None):
    from decision_engine.constraints import check_constraints

    context = context or {}
    checks = check_constraints(rotation, crops_by_id, context)

    if checks["status"] == "rejected":
        return {
            "rotation_id": rotation.get("id", "unknown"),
            "status": "rejected",
            "reject_reasons": checks["reject_reasons"],
            "scores": {key: None for key in WEIGHTS},
            "overall": None,
            "risks": [],
            "missing_info": checks["missing_info"],
            "confidence": "low",
            "needs_expert_review": True,
            "sources": [],
        }

    rotation_crop_ids = rotation.get("crops", [])
    component_scores = {}

    for component in WEIGHTS:
        values = [
            crop_scores.get(crop_id, {}).get(component)
            for crop_id in rotation_crop_ids
        ]
        component_scores[component] = average(values)

    available = [
        (component, score)
        for component, score in component_scores.items()
        if score is not None
    ]

    if available:
        used_weight = sum(WEIGHTS[key] for key, _ in available)
        overall = round(
            sum(score * WEIGHTS[key] for key, score in available)
            / used_weight,
            2,
        )
    else:
        overall = None

    missing_components = [
        key for key, value in component_scores.items()
        if value is None
    ]

    missing_info = checks["missing_info"] + [
        f"No {component} score is currently available."
        for component in missing_components
    ]

    # Two available criteria are not enough for medium or high confidence.
    # Inputs currently include team estimates and incomplete soil/economic data.
    confidence = "low"

    return {
        "rotation_id": rotation.get("id", "unknown"),
        "status": "ok",
        "reject_reasons": [],
        "scores": component_scores,
        "overall": overall,
        "risks": [],
        "missing_info": missing_info,
        "confidence": confidence,
        "needs_expert_review": True,
        "sources": [],
    }
