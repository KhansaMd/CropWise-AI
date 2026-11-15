import dataclasses
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from fieldshift import api

client = TestClient(api.app)
SUMMARY_KEYS = {"region", "season", "period", "baseline_years", "rain_pct", "temp_delta", "dry_spell_days",
                "heat_days", "heat_days_normal", "missing_pct", "units", "sources"}


def test_health_and_regions():
    h = client.get("/api/health").json()
    assert h["serving"] == "synthetic"
    assert set(h["regions"]) == {"punjab_ludhiana", "bihar_samastipur", "maharashtra_akola",
                                 "tamilnadu_thanjavur"}
    assert client.get("/api/regions").json()["tamilnadu_thanjavur"]["seasons_status"] == "needs_confirmation"


def test_climate_daily_shape():
    r = client.get("/api/climate", params={"region": "bihar_samastipur", "start": "2025-01-01", "end": "2025-01-10"})
    assert r.status_code == 200
    body = r.json()
    assert len(body["series"]) == 10
    assert set(body["series"][0]) == {"date", "rain_mm", "t_mean", "t_max", "solar"}
    assert set(body["units"]) == {"rain_mm", "t_mean", "t_max", "solar"}
    assert len(body["baseline"]["by_day"]) == 366
    assert set(body["baseline"]["by_day"][0]["t_mean"]) == {"mean", "std", "n"}
    assert body["missing"]["policy"] and body["source"]["site"] and body["synthetic"] is True


def test_climate_without_baseline_is_smaller():
    r = client.get("/api/climate", params={"region": "punjab_ludhiana", "baseline": "false"}).json()
    assert "baseline" not in r


def test_summary_shape_for_every_region_and_season():
    for region in api.REGIONS:
        for season in ("kharif", "rabi", "summer"):
            r = client.get("/api/climate/summary", params={"region": region, "season": season})
            assert r.status_code == 200, (region, season, r.text)
            assert SUMMARY_KEYS <= set(r.json())


def test_errors():
    assert client.get("/api/climate", params={"region": "nope"}).status_code == 404
    assert client.get("/api/climate/summary", params={"region": "punjab_ludhiana", "season": "monsoon"}).status_code == 422
    assert client.get("/api/climate", params={"region": "punjab_ludhiana", "start": "2030-01-01"}).status_code == 422
    assert client.get("/api/climate/summary",
                      params={"region": "punjab_ludhiana", "season": "kharif", "year": 2030}).status_code == 422


def test_missing_cache_returns_503_with_hint(tmp_path, monkeypatch):
    empty = dataclasses.replace(api.SETTINGS, use_synthetic=False, cache_dir=tmp_path)
    monkeypatch.setattr(api, "SETTINGS", empty)
    r = client.get("/api/climate", params={"region": "punjab_ludhiana"})
    assert r.status_code == 503
    assert "fieldshift.ingest" in r.json()["detail"]


def test_mock_has_same_keys_as_real_endpoint():
    mock_path = Path(__file__).resolve().parent.parent / "mock" / "summary.punjab_ludhiana.kharif.json"
    if not mock_path.exists():
        pytest.skip("run scripts/make_mock.py first")
    mock = json.loads(mock_path.read_text())
    real = client.get("/api/climate/summary", params={"region": "punjab_ludhiana", "season": "kharif"}).json()
    assert set(mock) - {"_mock", "_mock_notice"} == set(real)
    assert set(mock["units"]) == set(real["units"])
