"""Climate logic: daily series with day-of-year baseline, and seasonal summaries.

Both outputs are computed from the same cached frame, so dates and units always agree.

Missing-data policy (also returned in every response):
  * -999 (and -99) are converted to null on ingest. No imputation anywhere.
  * Rain totals use observed days scaled to the full window length.
  * Heat days are counted on observed days only, so they are a lower bound.
  * A dry spell is broken by a missing day, so the longest run is a lower bound.
  * Baseline means and standard deviations skip null days.
"""

from __future__ import annotations

import math
from datetime import date, timedelta
from typing import Optional

import numpy as np
import pandas as pd

from .settings import Settings
from .store import Cache

VARS = {"rain_mm": "PRECTOTCORR", "t_mean": "T2M", "t_max": "T2M_MAX", "solar": "ALLSKY_SFC_SW_DWN"}
EXPECTED_UNITS = {"PRECTOTCORR": {"mm/day"}, "T2M": {"c"}, "T2M_MAX": {"c"}}

MISSING_POLICY = (
    "Fill values (-999, -99) are converted to null; nothing is imputed. Rain totals scale observed "
    "days to the full window. Heat days count observed days only (lower bound). Dry spells are "
    "broken by missing days (lower bound). Baselines skip null days."
)
GRID_NOTE = ("Gridded satellite and model estimate for the grid cell containing this point, "
             "not a measurement at an individual farm.")

# Reference leap-year calendar: gives every month-day (including Feb 29) a stable position 1..366.
_REF = pd.date_range("2024-01-01", "2024-12-31", freq="D")
MD_LABELS = [d.strftime("%m-%d") for d in _REF]
_LUT = {(d.month, d.day): d.dayofyear for d in _REF}


def _norm_unit(unit: Optional[str]) -> Optional[str]:
    if unit is None:
        return None
    return unit.strip().lower().replace("°", "").replace(" ", "")


def unit_warnings(units: dict) -> list:
    out = []
    for param, allowed in EXPECTED_UNITS.items():
        u = _norm_unit(units.get(param))
        if u is None:
            out.append(f"No unit reported for {param}.")
        elif u not in allowed:
            out.append(f"{param} unit is '{units.get(param)}', not the expected one of {sorted(allowed)}. "
                       "Nothing was converted; the response keeps the source unit.")
    return out


def derived_units(units: dict) -> dict:
    return {name: units.get(param) for name, param in VARS.items()}


def to_frame(cache: Cache) -> pd.DataFrame:
    df = pd.DataFrame({name: pd.to_numeric(cache.df[param], errors="coerce") for name, param in VARS.items()})
    df.index = cache.df.index
    return df


def _ref_doy(index: pd.DatetimeIndex) -> np.ndarray:
    return np.array([_LUT[(m, d)] for m, d in zip(index.month, index.day)], dtype=int)


def _circular_window(arr: np.ndarray, k: int) -> np.ndarray:
    if k <= 0:
        return arr
    return sum(np.roll(arr, s) for s in range(-k, k + 1))


def baseline_by_day(df: pd.DataFrame, y0: int, y1: int, smooth_days: int = 0) -> dict:
    """Mean, sample std and sample count per reference day-of-year, over baseline years y0..y1."""
    sub = df[(df.index.year >= y0) & (df.index.year <= y1)]
    idx = _ref_doy(sub.index)
    out = {}
    for col in df.columns:
        vals = sub[col].to_numpy(dtype=float)
        ok = ~np.isnan(vals)
        n = np.bincount(idx[ok], minlength=367)[1:367].astype(float)
        s = np.bincount(idx[ok], weights=vals[ok], minlength=367)[1:367]
        ss = np.bincount(idx[ok], weights=vals[ok] ** 2, minlength=367)[1:367]
        n, s, ss = (_circular_window(a, smooth_days) for a in (n, s, ss))
        with np.errstate(divide="ignore", invalid="ignore"):
            mean = np.where(n > 0, s / n, np.nan)
            var = np.where(n > 1, (ss - s ** 2 / n) / (n - 1), np.nan)
        std = np.sqrt(np.clip(var, 0, None))
        out[col] = {"mean": mean, "std": std, "n": n.astype(int)}
    return out


def _num(x, nd=2):
    if x is None:
        return None
    try:
        f = float(x)
    except (TypeError, ValueError):
        return None
    return None if math.isnan(f) else round(f, nd) + 0.0   # + 0.0 turns -0.0 into 0.0


def _source_block(cache: Cache) -> dict:
    meta = cache.meta
    return {
        "name": meta["source"]["name"],
        "site": meta["source"]["site"],
        "community": meta["request"]["community"],
        "parameters": {p: {"units": cache.units.get(p), "longname": info.get("longname")}
                       for p, info in meta["parameters"].items()},
        "api": meta["source"].get("api"),
        "underlying_sources": meta["source"].get("sources"),
        "time_standard": meta["source"].get("time_standard"),
        "fill_value": meta["source"].get("fill_value"),
        "request_url": meta["request"]["url"],
        "fetched_at": meta["fetched_at"],
        "synthetic": bool(meta.get("synthetic")),
    }


def _sources_strings(cache: Cache) -> list:
    meta = cache.meta
    params = ",".join(meta["request"]["parameters"])
    first = (f"{meta['source']['name']}, community {meta['request']['community']}, "
             f"parameters {params}, {cache.data_start.isoformat()} to {cache.data_end.isoformat()}, "
             f"fetched {meta['fetched_at']}, {meta['source']['site']}")
    if cache.synthetic:
        return ["SYNTHETIC FIXTURE, NOT NASA DATA. " + first]
    return [first]


def _common_warnings(cache: Cache, region: dict) -> list:
    warns = list(cache.meta.get("warnings", [])) + unit_warnings(cache.units)
    if cache.synthetic:
        warns.insert(0, "SYNTHETIC FIXTURE DATA. Not NASA data. For development only.")
    warns.append(GRID_NOTE)
    return warns


def daily_response(cache: Cache, region: dict, settings: Settings, start: Optional[date] = None,
                   end: Optional[date] = None, include_baseline: bool = True) -> dict:
    df = to_frame(cache)
    lo = max(start, cache.data_start) if start else cache.data_start
    hi = min(end, cache.data_end) if end else cache.data_end
    if lo > hi:
        raise ValueError(f"Requested range is outside the cached range {cache.data_start} to {cache.data_end}")
    win = df.loc[pd.Timestamp(lo):pd.Timestamp(hi)]
    series = []
    for ts, row in win.iterrows():
        series.append({"date": ts.date().isoformat(), **{k: _num(row[k]) for k in VARS}})

    resp = {
        "region": region["id"],
        "name": region.get("name"),
        "state": region.get("state"),
        "location": {"lat": region["lat"], "lon": region["lon"], "note": GRID_NOTE},
        "synthetic": cache.synthetic,
        "date_range": {"start": lo.isoformat(), "end": hi.isoformat(), "days": int(len(win)),
                       "cache_start": cache.data_start.isoformat(), "cache_end": cache.data_end.isoformat()},
        "units": derived_units(cache.units),
        "field_sources": VARS,
        "missing": {
            "policy": MISSING_POLICY,
            "by_parameter_over_cache": {p: cache.meta["missing"][p] for p in cache.meta["missing"]},
            "missing_pct_in_returned_range": {
                k: _num(100.0 * win[k].isna().sum() / len(win), 2) for k in VARS},
        },
        "source": _source_block(cache),
        "sources": _sources_strings(cache),
        "warnings": _common_warnings(cache, region),
        "series": series,
    }
    if include_baseline:
        b = baseline_by_day(df, settings.baseline_start, settings.baseline_end, settings.baseline_smooth_days)
        resp["baseline"] = {
            "years": f"{settings.baseline_start}-{settings.baseline_end}",
            "method": ("Mean and sample standard deviation per calendar day across baseline years, "
                       "null days skipped. Position in 'doy_ref' counts a leap year (Feb 29 = day 60), "
                       "so join to the series by 'md' (MM-DD), not by day-of-year."),
            "smooth_days": settings.baseline_smooth_days,
            "by_day": [
                {"md": MD_LABELS[i], "doy_ref": i + 1,
                 **{k: {"mean": _num(b[k]["mean"][i]), "std": _num(b[k]["std"][i]), "n": int(b[k]["n"][i])}
                    for k in VARS}}
                for i in range(366)
            ],
        }
    return resp


# ---------- seasons ----------

def _md(s: str) -> tuple:
    m, d = s.split("-")
    return int(m), int(d)


def season_range(window: dict, year: int) -> tuple:
    """Season instance labelled by its start year. Windows may cross the new year (rabi)."""
    sm, sd = _md(window["start"])
    em, ed = _md(window["end"])
    start = date(year, sm, sd)
    end = date(year if (em, ed) >= (sm, sd) else year + 1, em, ed)
    return start, end


def pick_instance(window: dict, data_start: date, data_end: date, year: Optional[int] = None,
                  include_partial: bool = False) -> tuple:
    """Return (start, end, partial). Default: the latest season that is fully inside the cached data."""
    if year is not None:
        s, e = season_range(window, year)
        if s > data_end:
            raise ValueError(f"Season starting {s} is after the last cached day {data_end}")
        if s < data_start:
            raise ValueError(f"Season starting {s} begins before the cached data ({data_start})")
        return (s, e, False) if e <= data_end else (s, data_end, True)
    for y in range(data_end.year, data_start.year - 1, -1):
        s, e = season_range(window, y)
        if s < data_start:
            continue
        if e <= data_end:
            return s, e, False
        if include_partial and s <= data_end:
            return s, data_end, True
    raise ValueError("No season instance found inside the cached data")


def longest_run(flags: np.ndarray) -> int:
    best = cur = 0
    for f in flags:
        cur = cur + 1 if f else 0
        best = max(best, cur)
    return int(best)


def instance_metrics(df: pd.DataFrame, s: date, e: date, heat_c: float, dry_mm: float,
                     temp_ok: bool) -> dict:
    n_window = (e - s).days + 1
    w = df.loc[pd.Timestamp(s):pd.Timestamp(e)]
    rain = w["rain_mm"]
    obs = int(rain.notna().sum())
    rain_total = float(rain.sum() * n_window / obs) if obs else float("nan")
    miss_cells = int(sum(n_window - int(w[c].notna().sum()) for c in ("rain_mm", "t_mean", "t_max")))
    heat_days = int((w["t_max"] >= heat_c).sum()) if temp_ok else None
    dry = longest_run(((rain < dry_mm) & rain.notna()).to_numpy())
    return {
        "days": n_window,
        "rain_total": rain_total,
        "t_mean": float(w["t_mean"].mean()) if w["t_mean"].notna().any() else float("nan"),
        "heat_days": heat_days,
        "dry_spell_days": dry,
        "missing_pct": 100.0 * miss_cells / (n_window * 3),
        "missing_by_param": {c: _num(100.0 * (n_window - int(w[c].notna().sum())) / n_window, 2)
                             for c in VARS},
    }


def _mean(values: list) -> float:
    vals = [v for v in values if v is not None and not math.isnan(v)]
    return float(np.mean(vals)) if vals else float("nan")


def summarize(cache: Cache, region: dict, season: str, settings: Settings, year: Optional[int] = None,
              include_partial: bool = False) -> dict:
    if season not in region["seasons"]:
        raise KeyError(f"Season '{season}' is not defined for {region['id']}. "
                       f"Defined: {list(region['seasons'])}")
    window = region["seasons"][season]
    df = to_frame(cache)
    s, e, partial = pick_instance(window, cache.data_start, cache.data_end, year, include_partial)
    heat_c = float(region.get("heat_threshold_c", settings.heat_threshold_c))
    unit_warns = unit_warnings(cache.units)
    temp_ok = _norm_unit(cache.units.get("T2M_MAX")) == "c"
    cur = instance_metrics(df, s, e, heat_c, settings.dry_day_mm, temp_ok)

    n_days = cur["days"]
    base_years, base = [], []
    for y in range(settings.baseline_start, settings.baseline_end + 1):
        if y == s.year:        # leave the current instance out of its own baseline
            continue
        bs, be = season_range(window, y)
        if partial:            # compare like with like: same number of days from the season start
            be = min(be, bs + timedelta(days=n_days - 1))
        if bs < cache.data_start or be > cache.data_end:
            continue
        base_years.append(y)
        base.append(instance_metrics(df, bs, be, heat_c, settings.dry_day_mm, temp_ok))

    rain_base = _mean([b["rain_total"] for b in base])
    rain_pct = None if (math.isnan(rain_base) or rain_base == 0 or math.isnan(cur["rain_total"])) \
        else 100.0 * (cur["rain_total"] - rain_base) / rain_base
    tmean_base = _mean([b["t_mean"] for b in base])
    temp_delta = None if math.isnan(tmean_base) or math.isnan(cur["t_mean"]) else cur["t_mean"] - tmean_base
    heat_normal = _mean([b["heat_days"] for b in base]) if temp_ok else float("nan")
    dry_normal = _mean([b["dry_spell_days"] for b in base])

    warnings = _common_warnings(cache, region)
    if region.get("seasons_status") != "confirmed":
        warnings.append(f"Season windows for {region['id']} are '{region.get('seasons_status')}': "
                        f"{region.get('seasons_note')}")
    if partial:
        warnings.append(f"Season still in progress: {n_days} days to {e}. Baseline uses the same "
                        "number of days from the season start.")
    if not temp_ok:
        warnings.append("T2M_MAX is not reported in C, so heat_days and heat_days_normal are null.")
    if len(base_years) < settings.min_baseline_years:
        warnings.append(f"Only {len(base_years)} baseline years available "
                        f"(minimum recommended {settings.min_baseline_years}).")
    heat_note = ("Heat threshold is a team assumption, not a validated agronomic value. "
                 "Edit config.json (heat_threshold_c) or regions.json.")

    miss = cur["missing_pct"]
    if miss >= settings.missing_pct_low or len(base_years) < settings.min_baseline_years or not temp_ok:
        confidence = "low"
    elif miss >= settings.missing_pct_medium or partial or unit_warns:
        confidence = "medium"
    else:
        confidence = "high"

    rain_unit = cache.units.get("PRECTOTCORR")
    total_unit = None
    if rain_unit and rain_unit.strip().lower().endswith("/day"):
        total_unit = rain_unit.strip()[:-4]
    units = {
        "rain_pct": "%",
        "temp_delta": cache.units.get("T2M") or "C",
        "dry_spell_days": "days",
        "heat_days": "days",
        "heat_days_normal": "days",
        "missing_pct": "%",
        "rain_mm_total": total_unit,
        "t_mean": cache.units.get("T2M"),
        "source_parameters": {p: cache.units.get(p) for p in cache.meta["request"]["parameters"]},
    }
    return {
        "region": region["id"],
        "season": season,
        "period": f"{s.isoformat()}/{e.isoformat()}",
        "baseline_years": f"{settings.baseline_start}-{settings.baseline_end}",
        "rain_pct": _num(rain_pct, 1),
        "temp_delta": _num(temp_delta, 1),
        "dry_spell_days": cur["dry_spell_days"],
        "heat_days": cur["heat_days"],
        "heat_days_normal": _num(heat_normal, 1),
        "missing_pct": _num(miss, 1),
        "units": units,
        "sources": _sources_strings(cache),
        "synthetic": cache.synthetic,
        "season_window": {**window, "status": region.get("seasons_status"),
                          "partial": partial, "days_in_period": n_days},
        "thresholds": {"heat_t_max": heat_c, "heat_t_max_unit": "C",
                       "heat_threshold_is_assumption": True, "heat_threshold_note": heat_note,
                       "dry_day_rain_below": settings.dry_day_mm,
                       "dry_day_unit": cache.units.get("PRECTOTCORR")},
        "details": {
            "rain_mm_total": _num(cur["rain_total"], 1),
            "rain_mm_total_normal": _num(rain_base, 1),
            "t_mean": _num(cur["t_mean"], 2),
            "t_mean_normal": _num(tmean_base, 2),
            "dry_spell_days_normal": _num(dry_normal, 1),
            "baseline_years_used": base_years,
            "missing_pct_by_parameter": cur["missing_by_param"],
        },
        "data_range": {"cache_start": cache.data_start.isoformat(), "cache_end": cache.data_end.isoformat(),
                       "period_start": s.isoformat(), "period_end": e.isoformat()},
        "missing_data_policy": MISSING_POLICY,
        "quality": {"confidence": confidence,
                    "confidence_note": ("Heuristic from missing data, baseline length and partial season. "
                                        "Treat low as 'insufficient data' in scoring."),
                    "partial_season": partial},
        "source_metadata": _source_block(cache),
        "location": {"lat": region["lat"], "lon": region["lon"], "name": region.get("name"),
                     "state": region.get("state"), "note": GRID_NOTE},
        "warnings": warnings,
    }
