from decision_engine.validation import validate_explanation

"""Bilingual explanations based on calculated results only."""

CROP_HI = {
    "rice": "धान",
    "wheat": "गेहूँ",
    "maize": "मक्का",
    "mustard": "सरसों",
    "soybean": "सोयाबीन",
    "chickpea": "चना",
    "cotton": "कपास",
    "black_gram": "उड़द",
    "sesame": "तिल",
}

FIELD_HI = {
    "water_need": "पानी की आवश्यकता",
    "heat_tolerance": "गर्मी सहनशीलता",
    "drought_tolerance": "सूखा सहनशीलता",
    "ph_range": "मिट्टी का pH स्तर",
    "soil_ok": "मिट्टी की उपयुक्तता",
}

CONFIDENCE_HI = {
    "low": "कम",
    "medium": "मध्यम",
    "high": "उच्च",
}


LABEL_HI = {
    "crop_rotation": "फसल चक्र",
    "rainfall": "वर्षा",
    "irrigation": "सिंचाई",
    "soil_health": "मिट्टी का स्वास्थ्य",
    "climate_resilience": "जलवायु सहनशीलता",
    "risks": "जोखिम",
    "confidence": "विश्वास स्तर",
    "needs_expert_review": "विशेषज्ञ की समीक्षा आवश्यक है",
    "dry_spell": "लगातार सूखे दिन",
    "extreme_heat_days": "अत्यधिक गर्म दिन",
    "team_estimate": "टीम का अनुमान",
}

DISCLAIMER_HI = (
    "यह केवल उदाहरण के लिए तुलना है, खेती की सिफारिश नहीं।"
)



def build_explanation(rotation, result, language="en"):
    crops = rotation.get("crops", [])
    score = result.get("overall")
    confidence = result.get("confidence", "low")
    missing = result.get("missing_info", [])
    rejected = result.get("reject_reasons", [])
    exploratory = rotation.get("evidence_status") == "exploratory"

    if language == "hi":
        crop_names = " → ".join(CROP_HI.get(c, c) for c in crops)

        lines = [
            f"फसल क्रम: {crop_names}",
            f"जाँच स्थिति: {'अस्वीकृत' if result['status'] == 'rejected' else 'प्रारंभिक जाँच पास'}",
            f"कुल स्कोर: {'उपलब्ध नहीं' if score is None else score}",
            f"{LABEL_HI['confidence']}: {CONFIDENCE_HI.get(confidence, confidence)}",
            "यह केवल उदाहरण तुलना है, खेती की सिफारिश नहीं।",
        ]

        if missing:
            lines.append("सत्यापन के लिए आवश्यक जानकारी:")
            for item in missing[:5]:
                if ": " in item:
                    crop, field = item.split(": ", 1)
                    field = field.replace(" has not been verified.", "")
                    lines.append(
                        f"- {CROP_HI.get(crop, crop)}: "
                        f"{FIELD_HI.get(field, field)} सत्यापित नहीं है।"
                    )
                else:
                    lines.append(f"- {item}")

        if exploratory:
            lines.append("इस फसल क्रम का स्थानीय कृषि स्रोतों से सत्यापन बाकी है।")

        if rejected:
            lines.append("अस्वीकृति के कारण:")
            lines.extend(f"- {reason}" for reason in rejected)

        if result.get("needs_expert_review"):
            lines.append("कृषि विशेषज्ञ की समीक्षा आवश्यक है।")

        return "\n".join(lines)

    lines = [
        f"Crop sequence: {' -> '.join(crops)}",
        f"Check status: {'rejected' if result['status'] == 'rejected' else 'basic checks passed'}",
        f"Overall score: {score if score is not None else 'Not available'}",
        f"Confidence: {confidence}",
        "Example comparison only, not a farming recommendation.",
    ]

    if missing:
        lines.append("Information still needed:")
        lines.extend(f"- {item}" for item in missing[:5])

    if exploratory:
        lines.append("Exploratory rotation: local agricultural verification is still required.")

    if rejected:
        lines.append("Rejection reasons:")
        lines.extend(f"- {reason}" for reason in rejected)

    if result.get("needs_expert_review"):
        lines.append("Expert review is required before practical use.")

    return "\n".join(lines)

def build_validated_explanation(rotation, result, language="en", candidate=None):
    """
    Use a generated candidate only if its numeric claims are supported.
    Otherwise return the deterministic bilingual template.
    """

    fallback = build_explanation(rotation, result, language)

    if candidate is None:
        return fallback

    if validate_explanation(candidate, result):
        return candidate

    return fallback
