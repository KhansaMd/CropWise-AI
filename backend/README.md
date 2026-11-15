# Field Shift climate backend (NASA POWER)

Serves two outputs from one cached dataset per district, so dates and units always match:

1. `GET /api/climate?region=<id>` daily series for charts, plus day-of-year baseline (mean, std).
2. `GET /api/climate/summary?region=<id>&season=<kharif|rabi|summer>` seasonal summary for the scoring engine.

Also: `GET /api/regions` and `GET /api/health`.

Regions: `punjab_ludhiana`, `bihar_samastipur`, `maharashtra_akola`, `tamilnadu_thanjavur`.

## Status

Verified against the live NASA POWER Daily API (v2.10.3) on 2026-11-15:

- Response shape, parameter names and units match what the code expects: T2M and T2M_MAX in C, PRECTOTCORR in mm/day, ALLSKY_SFC_SW_DWN in MJ/m^2/day. Fill value is -999 (no -99 seen).
- All four districts are cached from 2016-01-01 to 2026-11-12 in `data/cache/`.
- There are no gaps inside the history. Missing values are only at the end of the range, where POWER has not published yet: temperature and rain lag about 2 days, solar about 4 days.
- 26 automated tests pass (`pytest -q`). The tests use a POWER-shaped fake response and synthetic fixtures, not live calls.

## Run

```bash
pip install -r requirements.txt
python -m cropwise_climate.ingest --probe    # 5-day sample, prints raw structure, saves data/probe_raw.json
python -m cropwise_climate.ingest            # all regions, 2016-01-01 to yesterday, writes data/cache/*.json + .parquet
python -m cropwise_climate.ingest --region punjab_ludhiana
uvicorn cropwise_climate.api:app --port 8000
pytest -q
```

Development without network: `python -m cropwise_climate.ingest --synthetic` then `FIELDSHIFT_USE_SYNTHETIC=1 uvicorn cropwise_climate.api:app`. Synthetic data is flagged `"synthetic": true` and starts every warnings list with SYNTHETIC. Never demo it as real.

The ingest prints % missing per parameter. `data/cache/` is committed so the demo never calls the live API.

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

Fill values become null. Nothing is imputed. Rain totals scale observed days to the full window. Heat days are observed counts (lower bound). Dry spells are broken by missing days. Baselines skip nulls. Trailing days where every parameter is missing are trimmed and reported. `quality.confidence` drops with missing %, few baseline years, partial seasons or unit warnings.

## Units

Passed through from the API response, never converted. If units differ from the expected (C, mm/day), a warning is returned; if T2M_MAX is not C, heat days are returned as null. Note solar units depend on the community (AG vs RE).

## Validation: Punjab 2022 heat event (Ludhiana)

Checked on the real cache, using the 2016-2025 baseline with the scored year left out:

- Summer window (2022-03-01 to 2022-06-30): mean temperature +1.7 C, rain -48.2%, 64 heat days against a normal of 47, longest dry spell 61 days.
- Rabi 2021-22 (2021-11-01 to 2022-04-30): 17 heat days against a normal of 6.3. Rain was +23.2% that season, so the signal is heat, not drought.
- April 2022 had the highest mean daily maximum temperature of the ten years (40.8 C; the next highest was 2025 at 40.0 C).
- March 2022 is not the standout in this data, because POWER is a smoothed grid product. Describe 2022 as a clearly hotter and drier than normal season, not a record.

Reproduce: `GET /api/climate/summary?region=punjab_ludhiana&season=summer&year=2022` and `...&season=rabi&year=2021` (FastAPI version only).

## Caveats

- POWER values are grid-cell estimates from reanalysis and satellite products, not farm measurements. The API reports its underlying sources as MERRA2, GEOSIT, SYN1DEG, FLASHFLUX and POWER.
- The 40 C heat threshold is a team assumption and is not validated. POWER's daily maximum is a grid average, so it can read lower than a weather station. In Thanjavur it rarely reaches 40 C, so heat days carry little signal there.
- Season windows overlap in Mar-Apr and June.
- Thanjavur seasons need a regional source (TNAU, local KVK).
- Coordinates are approximate district centre points, checked against OpenStreetMap. Three of the four land on the city centre.

## Next.js / Vercel

Vercel cannot run the FastAPI server. For a single Next.js deployment, export the data into the app:

```bash
python scripts/export_next.py --next-dir ../frontend
```

This copies the cached results into the app and adds `/api/regions`, `/api/climate` and `/api/climate/summary` route handlers with the same URLs and response shapes. The static summary is always the latest complete season (`year` and `include_partial` are rejected). Re-run it after every new ingest.

`python scripts/export_static.py` writes the same data as plain files under `data/static/` if you want to serve them another way.

## Mock

`mock/summary.punjab_ludhiana.kharif.json` has the agreed example numbers, same keys as the real endpoint, flagged `_mock: true`. `mock/summary.all_regions_all_seasons.synthetic.json` is computed from synthetic data.

## Data and credits

- Climate data: NASA POWER (Prediction Of Worldwide Energy Resources), Daily API, https://power.larc.nasa.gov/. Community AG, parameters T2M, T2M_MAX, PRECTOTCORR, ALLSKY_SFC_SW_DWN, 2016-01-01 to 2026-11-12. The data is a NASA open data product.
- District location check: OpenStreetMap contributors (Nominatim), https://www.openstreetmap.org/copyright.
- Software: FastAPI, uvicorn, pandas, NumPy, PyArrow, requests, httpx, pytest (all open source).

License: MIT, see `LICENSE` at the repository root.
