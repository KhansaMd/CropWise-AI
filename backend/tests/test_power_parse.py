from datetime import date

import pytest

from cropwise_climate.ingest import ingest_region  # noqa: F401  (import check)
from cropwise_climate.power import PowerError, parse_response
from cropwise_climate.store import build_cache_doc, doc_to_cache


def raw_response():
    return {
        "type": "Feature",
        "properties": {"parameter": {
            "T2M": {"20160101": 10.5, "20160102": -999, "20160103": 11.0, "20160104": -999},
            "T2M_MAX": {"20160101": 15.0, "20160102": 16.0, "20160103": 17.0, "20160104": -999},
            "PRECTOTCORR": {"20160101": 0.0, "20160102": 2.5, "20160103": -999, "20160104": -999},
            "ALLSKY_SFC_SW_DWN": {"20160101": 12.0, "20160102": -99, "20160103": 13.0, "20160104": -999},
        }},
        "header": {"fill_value": -999, "sources": ["MERRA2"], "api": {"name": "POWER Daily API", "version": "v2"}},
        "messages": [],
        "parameters": {"T2M": {"units": "C", "longname": "Temp"}, "T2M_MAX": {"units": "C", "longname": "Tmax"},
                       "PRECTOTCORR": {"units": "mm/day", "longname": "Rain"},
                       "ALLSKY_SFC_SW_DWN": {"units": "kW-hr/m^2/day", "longname": "Solar"}},
    }


def test_fill_values_become_null_and_units_pass_through(settings):
    p = parse_response(raw_response(), settings)
    assert p.values["T2M"] == [10.5, None, 11.0, None]
    assert p.values["ALLSKY_SFC_SW_DWN"][1] is None            # -99 handled too
    assert p.fill_counts["T2M"] == 2
    assert p.units["ALLSKY_SFC_SW_DWN"] == "kW-hr/m^2/day"      # unit passed through, not rewritten
    assert p.dates[0] == date(2016, 1, 1)


def test_missing_parameter_is_reported(settings):
    raw = raw_response()
    del raw["properties"]["parameter"]["T2M_MAX"]
    p = parse_response(raw, settings)
    assert p.absent_params == ["T2M_MAX"]
    assert any("T2M_MAX" in w for w in p.warnings)


def test_missing_units_warn(settings):
    raw = raw_response()
    raw["parameters"]["PRECTOTCORR"] = {}
    p = parse_response(raw, settings)
    assert p.units["PRECTOTCORR"] is None
    assert any("PRECTOTCORR" in w for w in p.warnings)


def test_unexpected_shape_raises_with_keys(settings):
    with pytest.raises(PowerError) as err:
        parse_response({"foo": 1}, settings)
    assert "foo" in str(err.value)


def test_cache_doc_trims_unpublished_tail_and_reports_missing_pct(settings, regions):
    p = parse_response(raw_response(), settings)
    doc = build_cache_doc("punjab_ludhiana", regions["punjab_ludhiana"], settings, p, "url",
                          date(2016, 1, 1), date(2016, 1, 4))
    # 4th day has every parameter missing, so it is trimmed as not yet published
    assert doc["date_range"]["end"] == "2016-01-03"
    assert doc["date_range"]["trailing_unpublished_days_trimmed"] == 1
    assert doc["missing"]["T2M"]["missing_days"] == 1
    assert doc["missing"]["T2M"]["missing_pct"] == pytest.approx(33.33, abs=0.01)
    cache = doc_to_cache(doc)
    assert cache.units["PRECTOTCORR"] == "mm/day"
    assert len(cache.df) == 3
