"""Derived daily transit counts from the crossings Parquet store.

This is the only publication-shaped output of the forward collector:
counts by UTC date x direction x broad AIS vessel class. Ship-level
crossings and positions stay in the local data lake (AISStream
publishes no data licence; raw redistribution is not defensible).

Vessel class is re-joined from the latest vessel registry at derive
time, so a crossing recorded before the vessel's static data arrived
still gets its broad class once known. tanker_subtype is never derived:
AIS codes do not encode crude/products/LNG.

Usage: python3 src/daily_counts.py
Writes data/derived/daily_counts.csv and data/derived/daily_counts.json
"""
from __future__ import annotations

import json
from pathlib import Path

import pyarrow.dataset as ds
import pyarrow.parquet as pq

PROJECT = Path(__file__).resolve().parent.parent
CROSS_DIR = PROJECT / "data" / "crossings"
VESSEL_FILE = PROJECT / "data" / "vessels" / "vessels.parquet"
OUT_DIR = PROJECT / "data" / "derived"


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    if not CROSS_DIR.exists() or not any(CROSS_DIR.rglob("*.parquet")):
        (OUT_DIR / "daily_counts.json").write_text(
            json.dumps({"counts": [], "note": "no crossings recorded yet"},
                       indent=2))
        print("no crossings yet")
        return 0

    table = ds.dataset(CROSS_DIR, format="parquet",
                       partitioning="hive").to_table()
    rows = table.to_pylist()

    registry = {}
    if VESSEL_FILE.exists():
        for v in pq.read_table(VESSEL_FILE).to_pylist():
            registry[v["mmsi"]] = v

    from collections import Counter
    from datetime import datetime, timezone
    counts: Counter = Counter()
    for r in rows:
        v = registry.get(r["mmsi"], {})
        vclass = v.get("vessel_class") or r.get("vessel_class") or "unknown"
        day = datetime.fromtimestamp(r["crossing_ts"],
                                     timezone.utc).strftime("%Y-%m-%d")
        counts[(day, r["direction"], vclass)] += 1

    out = [{"date": d, "direction": dr, "vessel_class": vc, "transits": n}
           for (d, dr, vc), n in sorted(counts.items())]
    (OUT_DIR / "daily_counts.json").write_text(json.dumps(
        {"counts": out,
         "note": "AIS-visible transits only; broad AIS classes; "
                 "tanker subtype is not separable from AIS codes"},
        indent=2))
    with (OUT_DIR / "daily_counts.csv").open("w") as fh:
        fh.write("date,direction,vessel_class,transits\n")
        for r in out:
            fh.write(f"{r['date']},{r['direction']},{r['vessel_class']},"
                     f"{r['transits']}\n")
    print(f"{len(out)} count rows from {len(rows)} crossings")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
