"""Synthetic fixtures for development and tests. NOT NASA DATA.

Generates a fake POWER-shaped response and sends it through the real parser and
cache builder, so tests exercise the same code path. Every file is flagged
"synthetic": true and the API repeats that warning in every response.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from datetime import date

from .power import parse_response
from .settings import Settings
from .store import build_cache_doc, write_cache

# (mean temp C, seasonal amplitude C, peak day of year, rain scale, monsoon wet-day prob)
PROFILES = {
    "punjab_ludhiana": (24.5, 11.0, 160, 0.9, 0.35),
    "bihar_samastipur": (26.0, 7.5, 150, 1.2, 0.55),
    "maharashtra_akola": (27.5, 6.0, 130, 0.9, 0.45),
    "tamilnadu_thanjavur": (28.5, 3.0, 140, 1.0, 0.30),
}
DEFAULT_PROFILE = (26.0, 7.0, 150, 1.0, 0.4)
FIXTURE_END = date(2026, 11, 10)
UNPUBLISHED_TAIL_DAYS = 4


def fake_power_response(region_id: str, start: date = date(2016, 1, 1), end: date = FIXTURE_END,
                        seed_offset: int = 0, missing_rate: float = 0.004) -> dict:
    rng = np.random.default_rng(sum(map(ord, region_id)) + seed_offset)
    mean_t, amp, peak, rain_scale, wet_p = PROFILES.get(region_id, DEFAULT_PROFILE)
    days = pd.date_range(start, end, freq="D")
    doy = days.dayofyear.to_numpy()
    seasonal = np.cos(2 * np.pi * (doy - peak) / 365.25)
    monsoon = (doy >= 160) & (doy <= 275)
    t2m = mean_t + amp * seasonal - 2.0 * monsoon + rng.normal(0, 1.2, len(days))
    t2m_max = t2m + 6.0 + rng.normal(0, 1.0, len(days))
    wet = rng.random(len(days)) < np.where(monsoon, wet_p, 0.05)
    rain = np.where(wet, rng.exponential(np.where(monsoon, 14.0, 4.0) * rain_scale), 0.0)
    solar = 18.0 - 6.0 * monsoon * rng.random(len(days)) + 3.0 * seasonal + rng.normal(0, 0.8, len(days))
    solar = np.clip(solar, 3.0, 30.0)

    def series(arr):
        out = {}
        for d, v in zip(days, arr):
            out[d.strftime("%Y%m%d")] = float(round(v, 2))
        return out

    par = {"T2M": series(t2m), "T2M_MAX": series(t2m_max),
           "PRECTOTCORR": series(rain), "ALLSKY_SFC_SW_DWN": series(solar)}
    keys = list(par["T2M"].keys())
    for name, ser in par.items():
        for k in rng.choice(keys, size=int(len(keys) * missing_rate), replace=False):
            ser[str(k)] = -999.0
    for k in keys[-UNPUBLISHED_TAIL_DAYS:]:   # mimic the publication lag: whole tail is fill value
        for ser in par.values():
            ser[k] = -999.0
    return {
        "type": "Feature",
        "properties": {"parameter": par},
        "header": {"title": "SYNTHETIC FIXTURE (not NASA data)", "api": {"name": "synthetic", "version": "0"},
                   "sources": ["SYNTHETIC"], "fill_value": -999, "time_standard": "LST"},
        "messages": ["synthetic fixture"],
        "parameters": {
            "T2M": {"units": "C", "longname": "Temperature at 2 Meters"},
            "T2M_MAX": {"units": "C", "longname": "Temperature at 2 Meters Maximum"},
            "PRECTOTCORR": {"units": "mm/day", "longname": "Precipitation Corrected"},
            "ALLSKY_SFC_SW_DWN": {"units": "MJ/m^2/day",
                                  "longname": "All Sky Surface Shortwave Downward Irradiance"},
        },
    }


def write_all(settings: Settings, regions: dict) -> None:
    for rid, reg in regions.items():
        raw = fake_power_response(rid)
        parsed = parse_response(raw, settings)
        doc = build_cache_doc(rid, reg, settings, parsed, "synthetic://fixture", date(2016, 1, 1),
                              FIXTURE_END, synthetic=True, fetched_at="2026-11-14T00:00:00+00:00")
        path = write_cache(settings, doc, directory=settings.synthetic_dir)
        print(f"wrote SYNTHETIC fixture {path}")
