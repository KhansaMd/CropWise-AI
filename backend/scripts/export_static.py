"""Precompute every endpoint response to static JSON files.

Use this if the frontend is a single Next.js app on Vercel: copy data/static/ into the app and
serve the files from route handlers (or import them). No Python is needed at runtime.

  python scripts/export_static.py            # from the real cache
  FIELDSHIFT_USE_SYNTHETIC=1 python scripts/export_static.py   # from fixtures (dev only)

Output:
  data/static/climate/<region>.json
  data/static/summary/<region>.<season>.json
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fieldshift import climate  # noqa: E402
from fieldshift.settings import ROOT, load_regions, load_settings  # noqa: E402
from fieldshift.store import CacheMissing, load_cache  # noqa: E402


def main() -> int:
    settings, regions = load_settings(), load_regions()
    out = ROOT / "data" / "static"
    (out / "climate").mkdir(parents=True, exist_ok=True)
    (out / "summary").mkdir(parents=True, exist_ok=True)
    failed = 0
    for rid, reg in regions.items():
        try:
            cache = load_cache(settings, rid)
        except CacheMissing as exc:
            print(f"skip {rid}: {exc}")
            failed += 1
            continue
        (out / "climate" / f"{rid}.json").write_text(
            json.dumps(climate.daily_response(cache, reg, settings), separators=(",", ":")))
        for season in reg["seasons"]:
            (out / "summary" / f"{rid}.{season}.json").write_text(
                json.dumps(climate.summarize(cache, reg, season, settings), indent=2))
        print(f"exported {rid}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
