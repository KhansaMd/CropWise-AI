# Field Shift climate backend (NASA POWER)

Serves two outputs from one cached dataset per district, so dates and units always match:

1. `GET /api/climate?region=<id>` daily series for charts, plus day-of-year baseline (mean, std).
2. `GET /api/climate/summary?region=<id>&season=<kharif|rabi|summer>` seasonal summary for the scoring engine.

Regions: `punjab_ludhiana`, `bihar_samastipur`, `maharashtra_akola`, `tamilnadu_thanjavur`.

## STATUS: read first

NASA POWER could not be reached from the sandbox where this was written. The ingest code and the response parser are written from the documented API shape and tested only against a POWER-shaped fake response. Run the probe on a machine with internet before trusting it.

## Run

```bash
pip install -r requirements.txt
python -m cropwise_climate.ingest --probe          # 5-day sample, prints raw structure, saves data/probe_raw.json
python -m cropwise_climate.ingest                  # all regions, 2016-01-01 to yesterday, writes data/cache/*.json + .parquet
python -m cropwise_climate.ingest --region punjab_ludhiana
uvicorn cropwise_climate.api:app --port 8000
pytest -q
```

Development without network: `python -m cropwise_climate.ingest --synthetic` then `FIELDSHIFT_USE_SYNTHETIC=1 uvicorn cropwise_climate.api:app`. Synthetic data is flagged `"synthetic": true` and starts every warnings list with SYNTHETIC. Never demo it as real.

The ingest prints % missing per parameter. Commit `data/cache/` so the demo never calls the live API.

## Config

- `config.json`: POWER community (AG), parameters, baseline years (2016-2025), `heat_threshold_c` (default 40, a team assumption, editable), `dry_day_mm` (1.0), fill values (-999, -99).
- `regions.json`: coordinates and season windows (kharif Jun-Oct, rabi Nov-Apr, summer Mar-Jun). Per-region overrides allowed for `seasons` and `heat_threshold_c`. Thanjavur is marked `needs_confirmation`.
- Env overrides: `FIELDSHIFT_HEAT_THRESHOLD_C`, `FIELDSHIFT_CACHE_DIR`, `FIELDSHIFT_USE_SYNTHETIC`.

## Summary endpoint

Required keys: region, season, period, baseline_years, rain_pct, temp_delta, dry_spell_days, heat_days, heat_days_normal, missing_pct, units, sources. Extra keys (synthetic, season_window, thresholds, details, data_range, missing_data_policy, quality, source_metadata, location, warnings) can be ignored.

- Default instance: latest season fully inside the cached data. `year=2025` picks one (rabi is labelled by start year). `include_partial=true` allows an in-progress season.
- The season being scored is excluded from its own baseline.
- `heat_days_normal` is the mean over baseline years.
- `rain_pct` compares the season rain total with the baseline mean total.

## Missing-data policy (returned in every response)

Fill values become null. Nothing is imputed. Rain totals scale observed days to the full window. Heat days are observed counts (lower bound). Dry spells are broken by missing days. Baselines skip nulls. Trailing days where every parameter is missing (POWER publishes with a 2-7 day lag) are trimmed and reported. `quality.confidence` drops with missing %, few baseline years, partial seasons or unit warnings.

## Units

Passed through from the API response, never converted. If units differ from the expected (C, mm/day), a warning is returned; if T2M_MAX is not C, heat days are returned as null. Note solar units depend on the community (AG vs RE).

## Caveats

POWER values are about 0.5 degree grid-cell estimates, not farm measurements. The 40 C threshold is not validated. Season windows overlap in Mar-Apr and June. Thanjavur seasons need a regional source (TNAU, local KVK). Coordinates are approximate; check on a map.

## Next.js / Vercel

`python scripts/export_static.py` writes `data/static/climate/<region>.json` and `data/static/summary/<region>.<season>.json`, which a Next.js route handler or static file can serve for a single deployment.

## Mock

`mock/summary.punjab_ludhiana.kharif.json` has the agreed example numbers, same keys as the real endpoint, flagged `_mock: true`. `mock/summary.all_regions_all_seasons.synthetic.json` is computed from synthetic data.
