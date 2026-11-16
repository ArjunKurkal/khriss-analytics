"""Pull IMF PortWatch daily series into the local data lake (Parquet).

Sources (public ArcGIS REST, no auth):
  * Daily_Chokepoints_Data - Strait of Hormuz (portid='chokepoint6'),
    full history. Fields are counts by 5 vessel classes + DWT capacity.
    NO direction, NO crude/products split, NO gas carriers (see audit).
  * Daily_Ports_Data - daily port calls + import/export tonnage by the
    same 5 classes, for the Gulf validation ports in PORTS below.

Fetches go through curl: urllib via this VM's egress proxy truncates
chunked responses at exactly 32 KiB (observed 2026-11-15).

Usage: .venv/bin/python src/pull_portwatch.py
Writes:
  data/portwatch/chokepoint_hormuz.parquet
  data/portwatch/ports.parquet
  data/portwatch/pull_meta.json
"""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

PROJECT = Path(__file__).resolve().parent.parent
OUT = PROJECT / "data" / "portwatch"
HOST = "https://services9.arcgis.com/weJ1QsnbMYJlCHdG/arcgis/rest/services"

# Validation ports: Gulf load ports inside the strait + Fujairah
# (outside the strait = bypass control). Ras Tanura / Ras Laffan ids are
# resolved by exact-name query at pull time (see resolve_port).
PORT_NAMES = ["Ras Tanura", "Ras Laffan", "Jebel Ali", "Fujairah",
              "Jubail", "Mina Al Ahmadi", "Basrah Oil Terminal",
              "Khor Fakkan"]


def fetch_json(url: str) -> dict:
    out = subprocess.run(["curl", "-s", "--max-time", "120", url],
                         capture_output=True, timeout=150, check=True)
    return json.loads(out.stdout)


def query_all(service: str, where: str, fields: str) -> list[dict]:
    """Page through an ArcGIS query (2000-row pages, ordered by date)."""
    rows: list[dict] = []
    offset = 0
    while True:
        from urllib.parse import urlencode
        params = {"where": where, "outFields": fields,
                  "orderByFields": "date ASC", "resultOffset": offset,
                  "resultRecordCount": 2000, "f": "json"}
        url = f"{HOST}/{service}/FeatureServer/0/query?{urlencode(params)}"
        data = fetch_json(url)
        if "error" in data:
            raise RuntimeError(f"ArcGIS error for {service}: {data['error']}")
        feats = data.get("features", [])
        rows.extend(f["attributes"] for f in feats)
        if not data.get("exceededTransferLimit") or not feats:
            return rows
        offset += len(feats)


def resolve_port(name: str) -> tuple[str, str] | None:
    """Exact portname match in Daily_Ports_Data (distinct values)."""
    from urllib.parse import urlencode
    params = {"where": f"portname = '{name}'",
              "outFields": "portid,portname,country",
              "returnDistinctValues": "true", "f": "json"}
    url = f"{HOST}/Daily_Ports_Data/FeatureServer/0/query?{urlencode(params)}"
    data = fetch_json(url)
    feats = data.get("features", [])
    if not feats:
        return None
    a = feats[0]["attributes"]
    return a["portid"], a["country"]


def ms_to_date(v) -> str:
    """ArcGIS returns this service's date as epoch ms in some queries and
    as an ISO string in others; accept both."""
    if isinstance(v, (int, float)):
        return datetime.fromtimestamp(v / 1000, timezone.utc).strftime("%Y-%m-%d")
    s = str(v)
    return s[:10]


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    meta: dict = {"pulled_at": datetime.now(timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ")}

    # --- Chokepoint series -------------------------------------------------
    fields = ("date,year,month,day,portid,portname,n_container,n_dry_bulk,"
              "n_general_cargo,n_roro,n_tanker,n_cargo,n_total,"
              "capacity_container,capacity_dry_bulk,capacity_general_cargo,"
              "capacity_roro,capacity_tanker,capacity_cargo,capacity")
    rows = query_all("Daily_Chokepoints_Data",
                     "portid='chokepoint6'", fields)
    for r in rows:
        r["date"] = ms_to_date(r["date"])
    rows.sort(key=lambda r: r["date"])
    table = pa.table({k: [r[k] for r in rows] for k in rows[0].keys()})
    pq.write_table(table, OUT / "chokepoint_hormuz.parquet")
    meta["chokepoint"] = {"rows": len(rows), "first": rows[0]["date"],
                          "last": rows[-1]["date"]}
    print(f"chokepoint: {len(rows)} rows {rows[0]['date']}..{rows[-1]['date']}")

    # --- Ports --------------------------------------------------------------
    pfields = ("date,portid,portname,country,portcalls_container,"
               "portcalls_dry_bulk,portcalls_general_cargo,portcalls_roro,"
               "portcalls_tanker,portcalls,export_tanker,export_container,"
               "export_dry_bulk,export,import_tanker,import")
    all_ports: list[dict] = []
    meta["ports"] = {}
    for name in PORT_NAMES:
        resolved = resolve_port(name)
        if not resolved:
            meta["ports"][name] = "NOT FOUND by exact name"
            print(f"port {name}: NOT FOUND")
            continue
        portid, country = resolved
        prows = query_all("Daily_Ports_Data", f"portid='{portid}'", pfields)
        for r in prows:
            r["date"] = ms_to_date(r["date"])
        prows.sort(key=lambda r: r["date"])
        all_ports.extend(prows)
        meta["ports"][name] = {"portid": portid, "country": country,
                               "rows": len(prows),
                               "first": prows[0]["date"] if prows else None,
                               "last": prows[-1]["date"] if prows else None}
        print(f"port {name} ({portid}, {country}): {len(prows)} rows")
    if all_ports:
        keys = list(all_ports[0].keys())
        table = pa.table({k: [r.get(k) for r in all_ports] for k in keys})
        pq.write_table(table, OUT / "ports.parquet")

    (OUT / "pull_meta.json").write_text(json.dumps(meta, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
