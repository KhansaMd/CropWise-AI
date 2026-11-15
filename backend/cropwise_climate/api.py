"""FastAPI app. Run: uvicorn cropwise_climate.api:app --reload --port 8000"""

from __future__ import annotations

from datetime import date
from typing import Literal, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from . import climate
from .settings import load_regions, load_settings
from .store import CacheMissing, load_cache

app = FastAPI(title="FieldShift climate API", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["GET"], allow_headers=["*"])

SETTINGS = load_settings()
REGIONS = load_regions()


def _region(region_id: str) -> dict:
    if region_id not in REGIONS:
        raise HTTPException(404, f"Unknown region '{region_id}'. Known: {list(REGIONS)}")
    return REGIONS[region_id]


def _cache(region_id: str):
    try:
        return load_cache(SETTINGS, region_id)
    except CacheMissing as exc:
        raise HTTPException(503, str(exc))


@app.get("/api/health")
def health():
    status = {}
    for rid in REGIONS:
        try:
            c = load_cache(SETTINGS, rid)
            status[rid] = {"ok": True, "synthetic": c.synthetic, "cache_start": c.data_start.isoformat(),
                           "cache_end": c.data_end.isoformat(), "fetched_at": c.meta["fetched_at"],
                           "missing_pct": {p: m["missing_pct"] for p, m in c.meta["missing"].items()}}
        except CacheMissing:
            status[rid] = {"ok": False, "reason": "no cache file"}
    return {"serving": "synthetic" if SETTINGS.use_synthetic else "nasa_power_cache",
            "heat_threshold_c": SETTINGS.heat_threshold_c, "regions": status}


@app.get("/api/regions")
def regions():
    return {rid: {"name": r.get("name"), "state": r.get("state"), "lat": r["lat"], "lon": r["lon"],
                  "seasons": r["seasons"], "seasons_status": r.get("seasons_status")}
            for rid, r in REGIONS.items()}


@app.get("/api/climate")
def climate_daily(region: str,
                  start: Optional[date] = Query(None, description="YYYY-MM-DD"),
                  end: Optional[date] = Query(None, description="YYYY-MM-DD"),
                  baseline: bool = Query(True, description="include day-of-year baseline")):
    reg, cache = _region(region), _cache(region)
    try:
        return climate.daily_response(cache, reg, SETTINGS, start, end, baseline)
    except ValueError as exc:
        raise HTTPException(422, str(exc))


@app.get("/api/climate/summary")
def climate_summary(region: str,
                    season: Literal["kharif", "rabi", "summer"],
                    year: Optional[int] = Query(None, description="season start year; default latest complete"),
                    include_partial: bool = Query(False, description="allow an in-progress season")):
    reg, cache = _region(region), _cache(region)
    try:
        return climate.summarize(cache, reg, season, SETTINGS, year, include_partial)
    except KeyError as exc:
        raise HTTPException(422, str(exc))
    except ValueError as exc:
        raise HTTPException(422, str(exc))
