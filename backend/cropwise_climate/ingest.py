"""Ingestion CLI. Run this where power.larc.nasa.gov is reachable.

  python -m cropwise_climate.ingest --probe          # 5-day sample, prints the raw shape and units
  python -m cropwise_climate.ingest                  # all regions, 2016-01-01 to latest available
  python -m cropwise_climate.ingest --region punjab_ludhiana
  python -m cropwise_climate.ingest --synthetic      # offline fixtures for development only

Outputs data/cache/<region>.json (canonical) and data/cache/<region>.parquet.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime, timedelta

from .power import PowerError, fetch_raw, parse_response
from .settings import ROOT, load_regions, load_settings
from .store import build_cache_doc, write_cache


def _print_missing(doc: dict) -> None:
    dr = doc["date_range"]
    print(f"  range {dr['start']} to {dr['end']} ({dr['days']} days), "
          f"{dr['trailing_unpublished_days_trimmed']} unpublished trailing days trimmed")
    for param, info in doc["parameters"].items():
        m = doc["missing"][param]
        print(f"  {param:<18} units={info['units']!s:<14} missing {m['missing_days']:>4}/{m['total_days']} "
              f"({m['missing_pct']}%)  fill->null {m['fill_values_converted_to_null']}")
    for w in doc["warnings"]:
        print(f"  WARNING: {w}")


def probe(settings, regions) -> int:
    rid, reg = next(iter(regions.items()))
    start, end = date(2016, 1, 1), date(2016, 1, 5)
    print(f"Probing POWER for {rid} {start} to {end} ...")
    raw, url = fetch_raw(settings, reg["lat"], reg["lon"], start, end)
    out = ROOT / "data" / "probe_raw.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(raw, indent=1))
    print("URL:", url)
    print("Top-level keys:", sorted(raw.keys()))
    print("header:", json.dumps(raw.get("header"), indent=1)[:800])
    print("parameters block (units come from here):", json.dumps(raw.get("parameters"), indent=1)[:800])
    props = raw.get("properties") or {}
    print("properties keys:", sorted(props.keys()))
    for p, series in (props.get("parameter") or {}).items():
        print(f"  {p}: {dict(list(series.items())[:5])}")
    parsed = parse_response(raw, settings)
    print("Parsed OK. Units:", parsed.units, "Warnings:", parsed.warnings)
    print(f"Raw response saved to {out}. Send this file to the team if anything looks different.")
    return 0


def ingest_region(settings, rid: str, reg: dict, end: date) -> dict:
    start = datetime.strptime(settings.start, "%Y-%m-%d").date()
    raw, url = fetch_raw(settings, reg["lat"], reg["lon"], start, end)
    parsed = parse_response(raw, settings)
    return build_cache_doc(rid, reg, settings, parsed, url, start, end)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--region", action="append", help="region id (repeatable). Default: all")
    ap.add_argument("--end", help="YYYY-MM-DD. Default: yesterday (POWER lags real time by days)")
    ap.add_argument("--probe", action="store_true", help="fetch a 5-day sample and print the raw shape")
    ap.add_argument("--synthetic", action="store_true", help="write offline fixtures to data/synthetic")
    args = ap.parse_args(argv)

    settings, regions = load_settings(), load_regions()
    if args.synthetic:
        from .synthetic import write_all
        write_all(settings, regions)
        return 0
    if args.probe:
        return probe(settings, regions)

    ids = args.region or list(regions)
    unknown = [r for r in ids if r not in regions]
    if unknown:
        print(f"Unknown region(s): {unknown}. Known: {list(regions)}")
        return 2
    end = datetime.strptime(args.end, "%Y-%m-%d").date() if args.end else date.today() - timedelta(days=1)

    failures = 0
    for rid in ids:
        print(f"[{rid}] fetching {settings.start} to {end} ...")
        try:
            doc = ingest_region(settings, rid, regions[rid], end)
        except (PowerError, ValueError) as exc:
            print(f"  FAILED: {exc}")
            failures += 1
            continue
        path = write_cache(settings, doc)
        _print_missing(doc)
        print(f"  wrote {path}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
