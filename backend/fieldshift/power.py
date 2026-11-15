"""NASA POWER daily point client and parser.

The response shape handled here is the documented POWER JSON layout:
  properties.parameter.<PARAM>.<YYYYMMDD> = value
  parameters.<PARAM>.units / longname      (units come from the API, never assumed)
  header.fill_value / sources / api / time_standard
Run `python -m fieldshift.ingest --probe` once against the live API to confirm
this shape. If anything differs, the probe prints exactly what to report.
"""

from __future__ import annotations

import math
import time
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional

import requests

from .settings import Settings


class PowerError(RuntimeError):
    pass


@dataclass
class ParsedPower:
    dates: list
    values: dict                 # PARAM -> list[Optional[float]] aligned with dates
    units: dict                  # PARAM -> Optional[str], straight from the API
    longnames: dict
    header: dict
    messages: list
    fill_counts: dict            # PARAM -> number of fill values converted to null
    absent_params: list = field(default_factory=list)
    warnings: list = field(default_factory=list)


def build_params(settings: Settings, lat: float, lon: float, start: date, end: date) -> dict:
    return {
        "parameters": ",".join(settings.parameters),
        "community": settings.community,
        "longitude": lon,
        "latitude": lat,
        "start": start.strftime("%Y%m%d"),
        "end": end.strftime("%Y%m%d"),
        "format": "JSON",
    }


def fetch_raw(settings: Settings, lat: float, lon: float, start: date, end: date,
              session: Optional[requests.Session] = None):
    """GET one daily point request. Returns (json, final_url). Retries on 429 and 5xx."""
    sess = session or requests.Session()
    params = build_params(settings, lat, lon, start, end)
    last_err = None
    for attempt in range(settings.retries):
        try:
            resp = sess.get(settings.base_url, params=params, timeout=settings.timeout_s)
        except requests.RequestException as exc:
            last_err = f"network error: {exc}"
            time.sleep(2 ** attempt)
            continue
        if resp.status_code == 200:
            return resp.json(), resp.url
        if resp.status_code == 429 or resp.status_code >= 500:
            last_err = f"HTTP {resp.status_code}: {resp.text[:200]}"
            time.sleep(2 ** (attempt + 1))
            continue
        raise PowerError(f"HTTP {resp.status_code} from POWER: {resp.text[:500]}")
    raise PowerError(f"POWER request failed after {settings.retries} attempts: {last_err}")


def _to_number(value, fill_values) -> tuple:
    """Return (number_or_None, was_fill)."""
    if value is None:
        return None, False
    try:
        num = float(value)
    except (TypeError, ValueError):
        return None, False
    if math.isnan(num):
        return None, False
    if num in fill_values:
        return None, True
    return num, False


def parse_response(raw: dict, settings: Settings) -> ParsedPower:
    props = raw.get("properties") or {}
    par = props.get("parameter") or {}
    if not par:
        raise PowerError(
            "No properties.parameter block in the POWER response. Top-level keys: "
            f"{sorted(raw.keys())}. Messages: {raw.get('messages')}"
        )
    header = raw.get("header") or {}
    fill_values = set(settings.fill_values)
    if header.get("fill_value") is not None:
        try:
            fill_values.add(float(header["fill_value"]))
        except (TypeError, ValueError):
            pass

    all_dates = set()
    for p in settings.parameters:
        all_dates.update((par.get(p) or {}).keys())
    dates = sorted(all_dates)
    values, fill_counts, absent, warnings = {}, {}, [], []
    for p in settings.parameters:
        series = par.get(p)
        if series is None:
            absent.append(p)
            values[p] = [None] * len(dates)
            fill_counts[p] = 0
            continue
        col, fills = [], 0
        for d in dates:
            num, was_fill = _to_number(series.get(d), fill_values)
            col.append(num)
            fills += int(was_fill)
        values[p] = col
        fill_counts[p] = fills

    meta_params = raw.get("parameters") or {}
    units = {p: (meta_params.get(p) or {}).get("units") for p in settings.parameters}
    longnames = {p: (meta_params.get(p) or {}).get("longname") for p in settings.parameters}
    for p, u in units.items():
        if u is None:
            warnings.append(f"No units returned by the API for {p}; unit-dependent fields are disabled.")
    if absent:
        warnings.append(f"Parameters missing from the API response: {absent}")

    parsed_dates = [datetime.strptime(d, "%Y%m%d").date() for d in dates]
    return ParsedPower(
        dates=parsed_dates,
        values=values,
        units=units,
        longnames=longnames,
        header=header,
        messages=list(raw.get("messages") or []),
        fill_counts=fill_counts,
        absent_params=absent,
        warnings=warnings,
    )
