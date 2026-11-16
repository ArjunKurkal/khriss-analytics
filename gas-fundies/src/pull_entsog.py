"""ENTSOG Transparency Platform daily pipeline flows — Europe layer.

Free public API, no key: https://transparency.entsog.eu/api/v1/
operationalData (xlsx download route). Physical Flow only, gas-day
resolution.

Point topology is the hard part: both TSOs at a border usually report
the same physical flow, so raw point data double-counts. The mapping
used here is the JRC's eurogastp topology (European Commission Joint
Research Centre, EUPL-licensed; package `eurogastp` by proggy/JRC):
config/ENTSOG_TP_Network_v4.xlsx, sheet ITP, maps every
(operator, point, direction) leg to a named edge (from_node -> to_node)
with a per-indicator aggregation rule. Aggregation mirrors eurogastp:
legs ruled 0 are excluded; if a leg is ruled 1 it is the sole reporter
("take"); otherwise all legs of the edge share one rule — sum, av
(mean), min or max.

Scope v1: EXTERNAL edges only — exactly one endpoint inside the EU27 —
i.e. the import/export corridors (Norway, Russia legacy routes, North
Africa, TAP/TurkStream, GB interconnectors, Swiss transit, Balkans).
Internal EU borders can be added with --scope all (449 legs).

Values: API reports kWh/d; stored as GWh/d. Requests are batched
(~160 pointDirections per monthly request) to stay inside the API's
60-second execution cap. Seed from 2022-01-01; incremental runs re-pull
the trailing 14 days (flows are revised).
"""
from __future__ import annotations

import argparse
import io
import sys
import time
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "shared"))
from khriss_data.config import project_data  # noqa: E402

API = "https://transparency.entsog.eu/api/v1/operationalData.xlsx"
TOPO_CSV = (Path(__file__).resolve().parents[1] / "config"
            / "entsog_topo_itp.csv")
TOPO = Path(__file__).resolve().parents[1] / "config" / "ENTSOG_TP_Network_v4.xlsx"
EU27 = {"AT", "BE", "BG", "CZ", "DE", "DK", "EE", "ES", "FR", "GR", "HR",
        "HU", "IE", "SK", "PT", "IT", "PL", "LU", "MT", "LV", "LT", "FI",
        "SI", "RO", "SE", "NL", "CY"}
GB_NODES = {"UK", "NI", "BBL", "IUK"}
SEED_START = date(2022, 1, 1)
BATCH_LEGS = 160


def load_legs(scope: str) -> pd.DataFrame:
    if TOPO_CSV.exists():
        itp = pd.read_csv(TOPO_CSV)
    else:
        itp = pd.read_excel(TOPO, sheet_name="ITP", engine="openpyxl")
    itp = itp[itp["edge_name"].notna()]
    itp = itp[itp["flow"].notna() & (itp["flow"].astype(str) != "0")].copy()
    itp["pd_id"] = (itp["operatorKey"] + itp["pointKey"]
                    + itp["directionKey"]).str.lower()
    if scope == "external":
        # EU27 external borders, plus GB-touching edges (added
        # 2026-11-15): the GB market's interconnectors land on the
        # virtual BBL/IUK nodes or the UK/NI country nodes, so edges
        # touching any of them are GB supply lines (Langeled NO->UK,
        # BBL NL->UK, IUK BE->UK, IE->UK). They are stored in the same
        # tables; the dashboard's EU27 inflow aggregation filters on
        # to_node in EU27, so GB edges never contaminate EU corridors.
        mask = [((f in EU27) != (t in EU27)) or f in GB_NODES or t in GB_NODES
                for f, t in zip(itp["from_node"], itp["to_node"])]
        itp = itp[mask]
    return itp[["pd_id", "operatorKey", "pointKey", "directionKey",
                "edge_name", "from_node", "to_node", "flow"]].rename(
                    columns={"flow": "rule"})


def month_chunks(start: date, end: date):
    cur = start.replace(day=1)
    while cur <= end:
        nxt = (cur.replace(day=28) + timedelta(days=4)).replace(day=1)
        yield max(cur, start), min(nxt - timedelta(days=1), end)
        cur = nxt


def fetch_chunk(pd_ids: list[str], frm: date, to: date) -> pd.DataFrame:
    params = {
        "forceDownload": "true",
        "pointDirection": ",".join(pd_ids),
        "from": frm.isoformat(), "to": to.isoformat(),
        "indicator": "Physical Flow", "periodType": "day",
        "timezone": "CET", "periodize": "0", "limit": "-1",
        "isTransportData": "true", "dataset": "1",
    }
    r = None
    for attempt in range(3):
        try:
            r = requests.get(API, params=params,
                             headers={"User-Agent": "Mozilla/5.0"},
                             timeout=180)
            break
        except requests.exceptions.RequestException:
            if attempt == 2:
                raise
            time.sleep(5 * (attempt + 1))
    if r.status_code == 404 or r.content == b'{"message":"No Data Available"}':
        return pd.DataFrame()
    r.raise_for_status()
    df = pd.read_excel(io.BytesIO(r.content), engine="openpyxl")
    if df.empty:
        return df
    df = df[df["indicator"] == "Physical Flow"]
    df["gas_day"] = pd.to_datetime(df["periodFrom"]).dt.normalize()
    df["pd_id"] = (df["operatorKey"] + df["pointKey"]
                   + df["directionKey"]).str.lower()
    df["lastUpdateDateTime"] = pd.to_datetime(df["lastUpdateDateTime"])
    df = (df.sort_values("lastUpdateDateTime")
          .drop_duplicates(subset=["pd_id", "gas_day"], keep="last"))
    non_kwh = df.loc[df["unit"] != "kWh/d", "unit"].unique()
    if len(non_kwh):
        print(f"  warning: non-kWh/d units present: {non_kwh} (rows kept, "
              "converted as if kWh/d only where unit == kWh/d)")
        df = df[df["unit"] == "kWh/d"]
    return df[["pd_id", "gas_day", "value"]].rename(
        columns={"value": "flow_kwh_d"})


def aggregate_edges(raw: pd.DataFrame, legs: pd.DataFrame) -> pd.DataFrame:
    m = raw.merge(legs, on="pd_id", how="inner")
    m["flow_gwh_d"] = m["flow_kwh_d"] / 1e6
    out = []
    for (edge, day), g in m.groupby(["edge_name", "gas_day"]):
        take = g[g["rule"].astype(str) == "1"]
        if not take.empty:
            val = take["flow_gwh_d"].iloc[0]
        else:
            rule = str(g["rule"].iloc[0])
            if rule == "sum":
                val = g["flow_gwh_d"].sum()
            elif rule == "min":
                val = g["flow_gwh_d"].min()
            elif rule == "max":
                val = g["flow_gwh_d"].max()
            else:  # "av" / "mean"
                val = g["flow_gwh_d"].mean()
        out.append({"gas_day": day, "edge_name": edge,
                    "from_node": g["from_node"].iloc[0],
                    "to_node": g["to_node"].iloc[0],
                    "flow_gwh_d": val})
    return pd.DataFrame(out)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scope", choices=["external", "all"], default="external")
    args = ap.parse_args()
    _, curated = project_data("gas-fundies")
    path = curated / "entsog_edge_daily.parquet"
    legs = load_legs(args.scope)
    print(f"ENTSOG {args.scope}: {len(legs)} legs, "
          f"{legs['edge_name'].nunique()} edges")

    existing = pd.read_parquet(path) if path.exists() else None
    if existing is not None and not existing.empty:
        start = (existing["gas_day"].max() - timedelta(days=14)).date()
    else:
        start = SEED_START
    end = date.today()
    pd_ids = sorted(legs["pd_id"].unique())
    batches = [pd_ids[i:i + BATCH_LEGS]
               for i in range(0, len(pd_ids), BATCH_LEGS)]

    frames = []
    for frm, to in month_chunks(start, end):
        for b in batches:
            raw = fetch_chunk(b, frm, to)
            if not raw.empty:
                frames.append(aggregate_edges(raw, legs))
            time.sleep(0.5)
        print(f"  {frm} .. {to} done")
    if not frames:
        print("ENTSOG: no data returned")
        return
    new = pd.concat(frames, ignore_index=True)
    if existing is not None and not existing.empty:
        merged = pd.concat([existing, new], ignore_index=True)
    else:
        merged = new
    merged = (merged.drop_duplicates(subset=["gas_day", "edge_name"],
                                     keep="last")
              .sort_values(["edge_name", "gas_day"]).reset_index(drop=True))
    merged.to_parquet(path, index=False)

    border = (merged.groupby(["gas_day", "from_node", "to_node"],
                             as_index=False)["flow_gwh_d"].sum())
    border.to_parquet(curated / "entsog_border_daily.parquet", index=False)
    print(f"ENTSOG edges: {len(merged)} rows through "
          f"{merged['gas_day'].max().date()}; borders: {len(border)} rows")


if __name__ == "__main__":
    main()
