from datetime import date

import numpy as np
import pandas as pd
import pytest

from conftest import UNITS_OK, constant_frame, make_cache
from fieldshift import climate


def test_baseline_mean_std_and_leap_day():
    df = pd.DataFrame({"rain_mm": np.nan, "t_mean": np.nan, "t_max": np.nan, "solar": np.nan},
                      index=pd.date_range("2016-01-01", "2025-12-31", freq="D"))
    for y, v in zip(range(2016, 2026), range(10)):           # Jan 1 value = year offset 0..9
        df.loc[f"{y}-01-01", "t_mean"] = float(v)
    b = climate.baseline_by_day(df, 2016, 2025)
    assert b["t_mean"]["mean"][0] == pytest.approx(4.5)
    assert b["t_mean"]["std"][0] == pytest.approx(np.std(range(10), ddof=1))
    assert b["t_mean"]["n"][0] == 10
    assert climate.MD_LABELS[59] == "02-29"
    assert b["t_mean"]["n"][59] == 0                          # no data on Feb 29 in this frame


def test_baseline_smoothing_pools_neighbours():
    df = pd.DataFrame({"rain_mm": 0.0, "t_mean": 0.0, "t_max": 0.0, "solar": 0.0},
                      index=pd.date_range("2016-01-01", "2020-12-31", freq="D"))
    df.loc[df.index.dayofyear == 10, "t_mean"] = 7.0
    sharp = climate.baseline_by_day(df, 2016, 2020, 0)["t_mean"]["mean"]
    smooth = climate.baseline_by_day(df, 2016, 2020, 1)["t_mean"]["mean"]
    assert sharp[9] == pytest.approx(7.0)
    assert smooth[9] == pytest.approx(7.0 / 3, rel=0.05)


def test_season_range_crosses_year():
    w = {"start": "11-01", "end": "04-30"}
    assert climate.season_range(w, 2025) == (date(2025, 11, 1), date(2026, 4, 30))
    assert climate.season_range({"start": "06-01", "end": "10-31"}, 2026) == (date(2026, 6, 1), date(2026, 10, 31))


def test_pick_instance_latest_complete_then_partial():
    k = {"start": "06-01", "end": "10-31"}
    r = {"start": "11-01", "end": "04-30"}
    ds, de = date(2016, 1, 1), date(2026, 11, 6)
    assert climate.pick_instance(k, ds, de) == (date(2026, 6, 1), date(2026, 10, 31), False)
    assert climate.pick_instance(r, ds, de) == (date(2025, 11, 1), date(2026, 4, 30), False)
    assert climate.pick_instance(r, ds, de, include_partial=True) == (date(2026, 11, 1), de, True)
    assert climate.pick_instance(k, ds, de, year=2026)[2] is False
    with pytest.raises(ValueError):
        climate.pick_instance(k, ds, de, year=2027)


def test_instance_metrics_dry_spell_heat_and_missing():
    df = pd.DataFrame({"rain_mm": 5.0, "t_mean": 30.0, "t_max": 36.0, "solar": 18.0},
                      index=pd.date_range("2026-06-01", "2026-06-30", freq="D"))
    df.loc["2026-06-05":"2026-06-14", "rain_mm"] = 0.5       # 10 dry days
    df.loc["2026-06-20", "rain_mm"] = np.nan                   # missing day
    df.loc["2026-06-10":"2026-06-12", "t_max"] = 41.0          # 3 heat days
    m = climate.instance_metrics(df, date(2026, 6, 1), date(2026, 6, 30), 40.0, 1.0, True)
    assert m["dry_spell_days"] == 10
    assert m["heat_days"] == 3
    assert m["missing_pct"] == pytest.approx(100 * 1 / 90)
    observed_sum = df["rain_mm"].sum()
    assert m["rain_total"] == pytest.approx(observed_sum * 30 / 29)   # scaled to the full window


def test_missing_day_breaks_dry_spell():
    df = pd.DataFrame({"rain_mm": 0.0, "t_mean": 30.0, "t_max": 36.0, "solar": 18.0},
                      index=pd.date_range("2026-06-01", "2026-06-10", freq="D"))
    df.loc["2026-06-05", "rain_mm"] = np.nan
    m = climate.instance_metrics(df, date(2026, 6, 1), date(2026, 6, 10), 40.0, 1.0, True)
    assert m["dry_spell_days"] == 5          # days 6 to 10; the gap breaks the run


def _cache_with_known_answer():
    """Baseline kharif: 5 mm/day, 30 C, 7 heat days. Current kharif 2026: 3.6 mm/day, 30.9 C, 12 heat days."""
    df = constant_frame()
    for y in range(2016, 2026):
        df.loc[f"{y}-06-01":f"{y}-10-31", "PRECTOTCORR"] = 5.0
        df.loc[f"{y}-06-01":f"{y}-10-31", "T2M"] = 30.0
        df.loc[f"{y}-07-01":f"{y}-07-07", "T2M_MAX"] = 41.0          # 7 heat days
    df.loc["2026-06-01":"2026-10-31", "PRECTOTCORR"] = 3.6
    df.loc["2026-06-01":"2026-10-31", "T2M"] = 30.9
    df.loc["2026-07-01":"2026-07-12", "T2M_MAX"] = 41.0              # 12 heat days
    df.loc["2026-08-01":"2026-08-14", "PRECTOTCORR"] = 0.2           # 14 day dry spell
    return make_cache(df)


def test_summary_known_answer(settings, regions):
    out = climate.summarize(_cache_with_known_answer(), regions["punjab_ludhiana"], "kharif", settings)
    assert out["period"] == "2026-06-01/2026-10-31"
    assert out["baseline_years"] == "2016-2025"
    assert out["temp_delta"] == 0.9
    assert out["heat_days"] == 12
    assert out["heat_days_normal"] == 7.0
    assert out["dry_spell_days"] == 14
    assert out["missing_pct"] == 0.0
    # rain: 14 days at 0.2 and 139 days at 3.6 vs 5 mm/day baseline
    expected = (14 * 0.2 + 139 * 3.6) / (153 * 5.0) * 100 - 100
    assert out["rain_pct"] == pytest.approx(expected, abs=0.1)
    assert out["units"]["rain_mm_total"] == "mm"
    assert out["details"]["baseline_years_used"] == list(range(2016, 2026))
    assert out["quality"]["confidence"] == "high"


def test_heat_threshold_is_configurable(settings, regions):
    import dataclasses
    cache = _cache_with_known_answer()
    lower = dataclasses.replace(settings, heat_threshold_c=36.0)
    out = climate.summarize(cache, regions["punjab_ludhiana"], "kharif", lower)
    assert out["thresholds"]["heat_t_max"] == 36.0
    assert out["heat_days"] == 153                                   # t_max 36 on every day counts at >= 36
    reg = dict(regions["punjab_ludhiana"], heat_threshold_c=42.0)   # per-region override wins
    assert climate.summarize(cache, reg, "kharif", settings)["heat_days"] == 0


def test_leave_current_year_out_of_baseline(settings, regions):
    out = climate.summarize(_cache_with_known_answer(), regions["punjab_ludhiana"], "kharif", settings, year=2025)
    assert 2025 not in out["details"]["baseline_years_used"]


def test_partial_season_uses_matching_baseline_days(settings, regions):
    out = climate.summarize(_cache_with_known_answer(), regions["punjab_ludhiana"], "rabi", settings,
                            include_partial=True)
    assert out["season_window"]["partial"] is True
    assert out["quality"]["confidence"] == "medium"
    assert any("in progress" in w for w in out["warnings"])


def test_unit_mismatch_is_not_converted_and_disables_heat(settings, regions):
    units = dict(UNITS_OK, T2M_MAX="K")
    cache = make_cache(constant_frame(), units=units)
    out = climate.summarize(cache, regions["punjab_ludhiana"], "kharif", settings)
    assert out["heat_days"] is None and out["heat_days_normal"] is None
    assert out["quality"]["confidence"] == "low"
    assert any("not the expected" in w for w in out["warnings"])
    assert out["units"]["source_parameters"]["T2M_MAX"] == "K"


def test_tamil_nadu_flags_unconfirmed_seasons(settings, regions):
    cache = make_cache(constant_frame(), region_id="tamilnadu_thanjavur")
    out = climate.summarize(cache, regions["tamilnadu_thanjavur"], "kharif", settings)
    assert out["season_window"]["status"] == "needs_confirmation"
    assert any("needs_confirmation" in w for w in out["warnings"])


def test_synthetic_data_is_flagged_everywhere(settings, regions):
    cache = make_cache(constant_frame(), synthetic=True)
    out = climate.summarize(cache, regions["punjab_ludhiana"], "kharif", settings)
    assert out["synthetic"] is True
    assert out["sources"][0].startswith("SYNTHETIC")
    assert out["warnings"][0].startswith("SYNTHETIC")


def test_summary_and_daily_share_units_and_dates(settings, regions):
    cache = _cache_with_known_answer()
    s = climate.summarize(cache, regions["punjab_ludhiana"], "kharif", settings)
    d = climate.daily_response(cache, regions["punjab_ludhiana"], settings)
    assert s["data_range"]["cache_end"] == d["date_range"]["cache_end"]
    assert s["units"]["source_parameters"]["PRECTOTCORR"] == "mm/day"
    assert d["units"]["rain_mm"] == s["units"]["source_parameters"]["PRECTOTCORR"]
