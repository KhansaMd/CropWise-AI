import os
import sys
from pathlib import Path

os.environ["FIELDSHIFT_USE_SYNTHETIC"] = "1"
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import numpy as np
import pandas as pd
import pytest

from fieldshift.settings import load_regions, load_settings
from fieldshift.store import Cache


@pytest.fixture(scope="session", autouse=True)
def synthetic_fixtures():
    settings = load_settings()
    if not (settings.synthetic_dir / "punjab_ludhiana.json").exists():
        from fieldshift.synthetic import write_all
        write_all(settings, load_regions())


@pytest.fixture
def settings():
    return load_settings()


@pytest.fixture
def regions():
    return load_regions()


UNITS_OK = {"T2M": "C", "T2M_MAX": "C", "PRECTOTCORR": "mm/day", "ALLSKY_SFC_SW_DWN": "MJ/m^2/day"}


def make_cache(df: pd.DataFrame, units=None, synthetic=False, region_id="punjab_ludhiana") -> Cache:
    """Build a Cache directly from a frame with POWER parameter columns."""
    units = units or UNITS_OK
    meta = {
        "region": region_id, "synthetic": synthetic, "fetched_at": "2026-11-14T00:00:00+00:00",
        "request": {"url": "test://", "community": "AG", "parameters": list(UNITS_OK)},
        "source": {"name": "NASA POWER test", "site": "https://power.larc.nasa.gov/", "api": None,
                   "sources": None, "time_standard": None, "fill_value": -999},
        "parameters": {p: {"units": units.get(p), "longname": p} for p in UNITS_OK},
        "missing": {p: {"missing_days": int(df[p].isna().sum()), "total_days": len(df),
                        "missing_pct": 0.0, "fill_values_converted_to_null": 0} for p in UNITS_OK},
        "warnings": [],
    }
    df = df.copy()
    df.index.name = "date"
    return Cache(region_id=region_id, meta=meta, df=df, units=units)


def constant_frame(start="2016-01-01", end="2026-11-06", t2m=30.0, tmax=36.0, rain=5.0, solar=18.0):
    idx = pd.date_range(start, end, freq="D")
    return pd.DataFrame({"T2M": t2m, "T2M_MAX": tmax, "PRECTOTCORR": rain, "ALLSKY_SFC_SW_DWN": solar},
                        index=idx, dtype=float)
