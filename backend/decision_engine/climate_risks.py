
"""Descriptive climate indicators from NASA POWER observations.

These are observational flags, not crop-specific suitability scores.
"""

def assess_climate_risks(summary):
    rain_change = summary.get("rain_pct_vs_baseline")
    temp_change = summary.get("temp_delta_c")
    dry_spell = summary.get("longest_dry_spell_days")
    heat_days = summary.get("heat_days")
    normal_heat_days = summary.get("heat_days_normal")

    flags = []

    if rain_change is not None and rain_change < 0:
        flags.append({
            "indicator": "rainfall_below_baseline",
            "observed_value": rain_change,
            "unit": "%",
            "message": "Seasonal rainfall was below its historical baseline."
        })

    if temp_change is not None and temp_change > 0:
        flags.append({
            "indicator": "temperature_above_baseline",
            "observed_value": temp_change,
            "unit": "°C",
            "message": "Mean temperature was above its historical baseline."
        })

    if dry_spell is not None and dry_spell > 0:
        flags.append({
            "indicator": "dry_spell_observed",
            "observed_value": dry_spell,
            "unit": "days",
            "message": "A consecutive dry spell was observed."
        })

    if (
        heat_days is not None
        and normal_heat_days is not None
        and heat_days > normal_heat_days
    ):
        flags.append({
            "indicator": "heat_days_above_normal",
            "observed_value": heat_days,
            "historical_normal": normal_heat_days,
            "unit": "days",
            "message": "Heat days exceeded the historical normal."
        })

    return {
        "season": summary.get("season"),
        "season_year": summary.get("season_year"),
        "complete": summary.get("complete", False),
        "climate_flags": flags,
        "needs_expert_review": True,
        "interpretation_note": (
            "These indicators describe observed climate conditions. "
            "They do not establish crop suitability or predict yield."
        )
    }
