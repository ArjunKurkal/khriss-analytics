#!/usr/bin/env python3
"""Publish the LNG cargo feed for downstream consumers (Gas Fundies /
global gas S&D). See FEED.md for the full data dictionary.

Inputs (all local, produced by the forward collector):
  data/crossings/date=*/crossing-*.parquet   ship-level crossing events
  data/registry/lng_fleet.parquet            IMO-keyed LNG fleet registry
  data/vessels/vessels.parquet               live vessel registry (fallback
                                             capacity source by MMSI)

Outputs:
  data/feeds/lng_crossings.parquet   canonical per-crossing table (lake)
  data/feeds/lng_daily.json          daily aggregates (lake copy)
  data/feeds/lng_monthly.json        monthly aggregates (lake copy)
  feeds/lng_daily.json               repo-staged copies (small JSON)
  feeds/lng_monthly.json

Semantics that matter to consumers (also in FEED.md):
  - Only MEASURED crossings: rows exist only where the collector matched
    a hull against the LNG fleet registry (IMO > MMSI > name). There is
    no modelled LNG in this feed.
  - direction: "outbound" = Gulf -> Gulf of Oman (crossing the transit
    line eastbound); for Qatari/UAE liquefaction that is the loaded leg
    in normal trade, but the feed reports direction, not load status.
  - capacity_m3 is the hull's NAMEPLATE LNG capacity from the registry,
    not a measured cargo volume. Sum it as "nameplate capacity moved",
    never as cargo loaded.
  - AIS-visible only: hulls transiting dark are absent. Collection gaps
    are in logs/gaps.jsonl and are never backfilled.
  - An empty feed (no LNG crossings yet) is a valid state: the Parquet
    carries the schema with zero rows and the JSON carries empty rows
    plus a coverage block.

Run: .venv/bin/python src/lng_feed.py
"""
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CROSS_DIR = ROOT / "data" / "crossings"
REGISTRY_PQ = ROOT / "data" / "registry" / "lng_fleet.parquet"
VESSELS_PQ = ROOT / "data" / "vessels" / "vessels.parquet"
LAKE_OUT = ROOT / "data" / "feeds"
REPO_OUT = ROOT / "feeds"
REGION = "hormuz"
SCHEMA_VERSION = "1"

HEADER = {
    "feed": "hormuz-lng-crossings",
    "schema_version": SCHEMA_VERSION,
    "region": REGION,
    "source": ("hormuz-tracker forward collector (live AIS, Open Waters "
               "aggregate of AISStream + AISHub), LNG hulls identified by "
               "IMO-keyed fleet-registry match"),
    "semantics": {
        "measured_not_modelled": True,
        "direction": ("outbound = Gulf -> Gulf of Oman (eastbound across "
                      "the transit line); inbound = reverse. Direction "
                      "only - load status is not observed."),
        "capacity_m3": ("hull nameplate LNG capacity from the fleet "
                        "registry; NOT a measured cargo volume"),
        "coverage": ("AIS-visible transits only, from collector start "
                     "2026-11-15; gaps logged in logs/gaps.jsonl, never "
                     "backfilled"),
    },
}


def aggregate(rows: list[dict], key: str) -> list[dict]:
    """Group crossing rows by `key` ('date' or 'month') into aggregates."""
    groups: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        groups[r[key]].append(r)
    out = []
    for k in sorted(groups):
        g = rows_ = groups[k]
        by_class: dict[str, int] = defaultdict(int)
        for r in rows_:
            by_class[r.get("capacity_class") or "unknown"] += 1
        out.append({
            key: k,
            "transits_total": len(g),
            "outbound": sum(1 for r in g if r["direction"] == "outbound"),
            "inbound": sum(1 for r in g if r["direction"] == "inbound"),
            "capacity_m3_outbound": sum(
                r["capacity_m3"] or 0 for r in g
                if r["direction"] == "outbound"),
            "capacity_m3_inbound": sum(
                r["capacity_m3"] or 0 for r in g
                if r["direction"] == "inbound"),
            "by_capacity_class": dict(sorted(by_class.items())),
            "distinct_vessels": len({r["imo"] or r["mmsi"] for r in g}),
            "vessels": sorted({r["vessel_name"] for r in g
                               if r["vessel_name"]}),
        })
    return out


def load_crossing_rows() -> list[dict]:
    """LNG crossings from the lake, enriched with registry capacity."""
    import pyarrow.parquet as pq

    registry_by_imo, registry_by_mmsi = {}, {}
    if REGISTRY_PQ.exists():
        reg = pq.read_table(REGISTRY_PQ).to_pylist()
        for r in reg:
            if r.get("imo"):
                registry_by_imo[int(r["imo"])] = r
            if r.get("mmsi"):
                registry_by_mmsi[int(r["mmsi"])] = r
    vessel_cap = {}
    if VESSELS_PQ.exists():
        for v in pq.read_table(VESSELS_PQ).to_pylist():
            vessel_cap[v["mmsi"]] = (v.get("lng_capacity_class"),
                                     v.get("lng_capacity_m3"))

    rows = []
    files = sorted(CROSS_DIR.glob("date=*/crossing-*.parquet"))
    for f in files:
        for r in pq.read_table(f).to_pylist():
            if r.get("vessel_class") != "lng_carrier":
                continue
            reg = None
            if r.get("imo") and int(r["imo"]) in registry_by_imo:
                reg = registry_by_imo[int(r["imo"])]
            elif r["mmsi"] in registry_by_mmsi:
                reg = registry_by_mmsi[r["mmsi"]]
            cap_class = reg["capacity_class"] if reg else None
            cap_m3 = reg["capacity_m3"] if reg else None
            if cap_class is None:
                cap_class, cap_m3 = vessel_cap.get(
                    r["mmsi"], (None, None))
            ts = float(r["crossing_ts"])
            dt = datetime.fromtimestamp(ts, timezone.utc)
            rows.append({
                "crossing_ts": ts,
                "crossing_time": dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "date": dt.strftime("%Y-%m-%d"),
                "month": dt.strftime("%Y-%m"),
                "mmsi": int(r["mmsi"]),
                "vessel_name": r.get("vessel_name"),
                "imo": int(r["imo"]) if r.get("imo") else None,
                "capacity_class": cap_class,
                "capacity_m3": cap_m3,
                "direction": r["direction"],
                "region": REGION,
            })
    rows.sort(key=lambda r: r["crossing_ts"])
    return rows


def main() -> int:
    import pyarrow as pa
    import pyarrow.parquet as pq

    rows = load_crossing_rows()
    LAKE_OUT.mkdir(parents=True, exist_ok=True)
    REPO_OUT.mkdir(parents=True, exist_ok=True)

    schema = pa.schema([
        ("crossing_ts", pa.float64()), ("crossing_time", pa.string()),
        ("date", pa.string()), ("month", pa.string()),
        ("mmsi", pa.int64()), ("vessel_name", pa.string()),
        ("imo", pa.int64()), ("capacity_class", pa.string()),
        ("capacity_m3", pa.int64()), ("direction", pa.string()),
        ("region", pa.string()),
    ])
    tbl = pa.Table.from_pylist(rows, schema=schema)
    pq.write_table(tbl, LAKE_OUT / "lng_crossings.parquet")

    generated = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    coverage = {
        "crossings_total": len(rows),
        "first_crossing": rows[0]["crossing_time"] if rows else None,
        "last_crossing": rows[-1]["crossing_time"] if rows else None,
    }
    daily = {**HEADER, "generated_at": generated, "coverage": coverage,
             "rows": aggregate(rows, "date")}
    monthly = {**HEADER, "generated_at": generated, "coverage": coverage,
               "rows": aggregate(rows, "month")}
    for name, payload in [("lng_daily.json", daily),
                          ("lng_monthly.json", monthly)]:
        text = json.dumps(payload, indent=1)
        (LAKE_OUT / name).write_text(text)
        (REPO_OUT / name).write_text(text)
    print(f"lng feed: {len(rows)} measured LNG crossings "
          f"({coverage['first_crossing']} .. {coverage['last_crossing']})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
