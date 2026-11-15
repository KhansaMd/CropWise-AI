"""Cache documents: build, write (JSON + parquet) and load.

One JSON file per region is the canonical cache. Everything the API serves is
computed from it, so both endpoints always share the same dates and units.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Optional

import pandas as pd

from .power import ParsedPower
from .settings import Settings


class CacheMissing(FileNotFoundError):
    pass


@dataclass
class Cache:
    region_id: str
    meta: dict
    df: pd.DataFrame     # index: daily DatetimeIndex, columns: POWER parameter names
    units: dict          # POWER parameter -> unit string from the API

    @property
    def data_start(self) -> date:
        return self.df.index.min().date()

    @property
    def data_end(self) -> date:
        return self.df.index.max().date()

    @property
    def synthetic(self) -> bool:
        return bool(self.meta.get("synthetic"))


def cache_dir(settings: Settings) -> Path:
    return settings.synthetic_dir if settings.use_synthetic else settings.cache_dir


def cache_path(settings: Settings, region_id: str) -> Path:
    return cache_dir(settings) / f"{region_id}.json"


def _missing_stats(df: pd.DataFrame, fill_counts: dict) -> dict:
    total = len(df)
    out = {}
    for col in df.columns:
        n_missing = int(df[col].isna().sum())
        out[col] = {
            "missing_days": n_missing,
            "total_days": total,
            "missing_pct": round(100.0 * n_missing / total, 2) if total else None,
            "fill_values_converted_to_null": int(fill_counts.get(col, 0)),
        }
    return out


def build_cache_doc(region_id: str, region: dict, settings: Settings, parsed: ParsedPower,
                    request_url: str, requested_start: date, requested_end: date,
                    synthetic: bool = False, fetched_at: Optional[str] = None) -> dict:
    df = pd.DataFrame(parsed.values, index=pd.to_datetime(parsed.dates))
    df = df.sort_index()
    df = df.reindex(pd.date_range(df.index.min(), df.index.max(), freq="D"))
    # Trim the trailing run of days where every parameter is still missing (data not yet published).
    has_any = df.notna().any(axis=1)
    if not has_any.any():
        raise ValueError(f"{region_id}: the response contains no data at all")
    last_valid = has_any[has_any].index.max()
    trimmed_tail = int((df.index > last_valid).sum())
    df = df.loc[:last_valid]
    last_by_param = {c: (df[c].last_valid_index().date().isoformat() if df[c].notna().any() else None)
                     for c in df.columns}

    header = parsed.header
    doc = {
        "schema_version": 1,
        "synthetic": synthetic,
        "region": region_id,
        "name": region.get("name"),
        "state": region.get("state"),
        "location": {"lat": region["lat"], "lon": region["lon"]},
        "fetched_at": fetched_at or datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "request": {
            "url": request_url,
            "community": settings.community,
            "parameters": list(settings.parameters),
            "start": requested_start.isoformat(),
            "end": requested_end.isoformat(),
        },
        "source": {
            "name": "NASA POWER (Prediction Of Worldwide Energy Resources), daily point API",
            "site": "https://power.larc.nasa.gov/",
            "api": header.get("api"),
            "title": header.get("title"),
            "sources": header.get("sources"),
            "time_standard": header.get("time_standard"),
            "fill_value": header.get("fill_value"),
            "messages": parsed.messages,
        },
        "parameters": {
            p: {"units": parsed.units.get(p), "longname": parsed.longnames.get(p)}
            for p in settings.parameters
        },
        "date_range": {
            "start": df.index.min().date().isoformat(),
            "end": df.index.max().date().isoformat(),
            "days": int(len(df)),
            "trailing_unpublished_days_trimmed": trimmed_tail,
            "last_valid_date_by_parameter": last_by_param,
        },
        "missing": _missing_stats(df, parsed.fill_counts),
        "warnings": list(parsed.warnings),
        "data": {"date": [d.date().isoformat() for d in df.index]},
    }
    for col in df.columns:
        doc["data"][col] = [None if pd.isna(v) else float(v) for v in df[col]]
    return doc


def write_cache(settings: Settings, doc: dict, directory: Optional[Path] = None) -> Path:
    out_dir = directory or cache_dir(settings)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{doc['region']}.json"
    path.write_text(json.dumps(doc, separators=(",", ":")))
    try:
        df = pd.DataFrame({k: v for k, v in doc["data"].items()})
        df["date"] = pd.to_datetime(df["date"])
        df.to_parquet(out_dir / f"{doc['region']}.parquet", index=False)
    except Exception as exc:  # parquet is a convenience copy, JSON is canonical
        print(f"  note: parquet not written ({exc})")
    return path


def doc_to_cache(doc: dict) -> Cache:
    data = doc["data"]
    df = pd.DataFrame({k: v for k, v in data.items() if k != "date"}, index=pd.to_datetime(data["date"]))
    df = df.astype(float)
    df = df.reindex(pd.date_range(df.index.min(), df.index.max(), freq="D"))
    df.index.name = "date"
    units = {p: info.get("units") for p, info in doc["parameters"].items()}
    meta = {k: v for k, v in doc.items() if k != "data"}
    return Cache(region_id=doc["region"], meta=meta, df=df, units=units)


_MEMO: dict = {}


def load_cache(settings: Settings, region_id: str) -> Cache:
    path = cache_path(settings, region_id)
    if not path.exists():
        hint = ("Run `python -m cropwise_climate.ingest` on a machine that can reach power.larc.nasa.gov, "
                "or set FIELDSHIFT_USE_SYNTHETIC=1 for development only.")
        raise CacheMissing(f"No cache for {region_id} at {path}. {hint}")
    key = (str(path), path.stat().st_mtime_ns)
    if key not in _MEMO:
        for old in [k for k in _MEMO if k[0] == str(path)]:
            del _MEMO[old]
        _MEMO[key] = doc_to_cache(json.loads(path.read_text()))
    return _MEMO[key]
