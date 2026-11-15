"""Build the mock for GET /api/climate/summary from the real schema.

The mock is produced by the real summarize() on synthetic fixtures, then the headline numbers are
overwritten with the example values from the brief. Keys and structure therefore match the real
endpoint exactly. Every mock carries _mock: true so it cannot be mistaken for data.
"""

import json
import os
import sys
from pathlib import Path

os.environ["FIELDSHIFT_USE_SYNTHETIC"] = "1"
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fieldshift import climate  # noqa: E402
from fieldshift.settings import ROOT, load_regions, load_settings  # noqa: E402
from fieldshift.store import load_cache  # noqa: E402

NOTICE = ("MOCK. Example numbers for building against the schema. Not NASA data. "
          "The real endpoint returns the same keys with computed values.")


def main() -> None:
    settings, regions = load_settings(), load_regions()
    out = ROOT / "mock"
    out.mkdir(exist_ok=True)

    reg = regions["punjab_ludhiana"]
    s = climate.summarize(load_cache(settings, "punjab_ludhiana"), reg, "kharif", settings)
    s["period"] = "2026-06-01/2026-10-31"
    s.update({"rain_pct": -28.0, "temp_delta": 0.9, "dry_spell_days": 14, "heat_days": 12,
              "heat_days_normal": 7.0, "missing_pct": 0.4})
    s["quality"]["confidence"] = "high"
    # keep the details block consistent with the overridden headline numbers
    s["details"].update({"rain_mm_total": 520.0, "rain_mm_total_normal": 722.2, "t_mean": 29.4,
                         "t_mean_normal": 28.5, "dry_spell_days_normal": 9.0,
                         "missing_pct_by_parameter": {"rain_mm": 0.4, "t_mean": 0.4, "t_max": 0.4, "solar": 0.4}})
    s["data_range"].update({"period_start": "2026-06-01", "period_end": "2026-10-31"})
    s["season_window"]["partial"] = False
    s["_mock"] = True
    s["_mock_notice"] = NOTICE
    (out / "summary.punjab_ludhiana.kharif.json").write_text(json.dumps(s, indent=2))

    everything = {}
    for rid, r in regions.items():
        cache = load_cache(settings, rid)
        for season in r["seasons"]:
            item = climate.summarize(cache, r, season, settings)
            item["_mock"] = True
            item["_mock_notice"] = NOTICE + " Values here come from SYNTHETIC fixtures."
            everything[f"{rid}.{season}"] = item
    (out / "summary.all_regions_all_seasons.synthetic.json").write_text(json.dumps(everything, indent=2))
    print("wrote", sorted(p.name for p in out.iterdir()))


if __name__ == "__main__":
    main()
