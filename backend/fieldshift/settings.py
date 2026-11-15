"""Settings and region loading. Everything editable lives in config.json and regions.json."""

from __future__ import annotations

import copy
import json
import os
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class Settings:
    base_url: str
    community: str
    parameters: tuple
    start: str
    timeout_s: float
    retries: int
    baseline_start: int
    baseline_end: int
    min_baseline_years: int
    baseline_smooth_days: int
    heat_threshold_c: float
    dry_day_mm: float
    fill_values: tuple
    missing_pct_medium: float
    missing_pct_low: float
    cache_dir: Path
    synthetic_dir: Path
    use_synthetic: bool


def _resolve(p: str) -> Path:
    path = Path(p)
    return path if path.is_absolute() else ROOT / path


def load_settings(path: Path | None = None) -> Settings:
    cfg = json.loads((path or ROOT / "config.json").read_text())
    power = cfg["power"]
    heat = float(os.environ.get("FIELDSHIFT_HEAT_THRESHOLD_C", cfg["heat_threshold_c"]))
    cache_dir = os.environ.get("FIELDSHIFT_CACHE_DIR", cfg["cache_dir"])
    use_syn = os.environ.get("FIELDSHIFT_USE_SYNTHETIC", "0") == "1"
    conf = cfg["confidence_heuristic"]
    return Settings(
        base_url=power["base_url"],
        community=power["community"],
        parameters=tuple(power["parameters"]),
        start=power["start"],
        timeout_s=float(power["timeout_s"]),
        retries=int(power["retries"]),
        baseline_start=int(cfg["baseline_years"][0]),
        baseline_end=int(cfg["baseline_years"][1]),
        min_baseline_years=int(cfg["min_baseline_years"]),
        baseline_smooth_days=int(cfg["baseline_smooth_days"]),
        heat_threshold_c=heat,
        dry_day_mm=float(cfg["dry_day_mm"]),
        fill_values=tuple(float(v) for v in cfg["fill_values"]),
        missing_pct_medium=float(conf["missing_pct_medium"]),
        missing_pct_low=float(conf["missing_pct_low"]),
        cache_dir=_resolve(cache_dir),
        synthetic_dir=_resolve(cfg["synthetic_dir"]),
        use_synthetic=use_syn,
    )


def load_regions(path: Path | None = None) -> dict:
    """Return {region_id: region_dict} with seasons merged from defaults."""
    raw = json.loads((path or ROOT / "regions.json").read_text())
    defaults = raw["defaults"]
    out = {}
    for rid, reg in raw["regions"].items():
        merged = copy.deepcopy(reg)
        seasons = copy.deepcopy(defaults["seasons"])
        seasons.update(reg.get("seasons", {}))
        merged["seasons"] = seasons
        merged.setdefault("seasons_status", defaults["seasons_status"])
        merged.setdefault("seasons_note", defaults["seasons_note"])
        merged["id"] = rid
        out[rid] = merged
    return out
