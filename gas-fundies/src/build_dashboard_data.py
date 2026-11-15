"""Emit dashboard/data.json from the curated Parquet tables.

Static dashboard contract: one JSON file, small enough for GitHub Pages.
Every section is optional — a table that has not been pulled yet is
simply absent, and the dashboard hides its panel. Numbers are rounded
to 2 dp (prices 3 dp); dates are ISO strings.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "shared"))
from khriss_data.config import project_data          # noqa: E402
from khriss_data.io import read_parquet              # noqa: E402

HERE = Path(__file__).resolve().parents[1]
OUT = HERE / "dashboard" / "data.json"


def _round(df: pd.DataFrame, nd: int = 2) -> list:
    return df.round(nd).where(pd.notna(df), None).values.tolist()


def _dates(idx) -> list:
    return [pd.Timestamp(d).strftime("%Y-%m-%d") for d in idx]


def balance_section(curated: Path, out: dict) -> None:
    path = curated / "balance_monthly.parquet"
    if not path.exists():
        return
    b = read_parquet(path)
    b["month"] = pd.to_datetime(b["month"])
    b = b.sort_values("month")
    cols = [c for c in ["dry_production", "imports_pipeline", "imports_lng",
                        "total_supply", "residential", "commercial",
                        "industrial", "power_burn", "other_consumption",
                        "consumption_total_reported", "exports_pipeline",
                        "exports_lng", "lng_feedgas_estimate", "total_demand",
                        "supply_minus_demand", "storage_change_reported_bcfd",
                        "balancing_item_bcfd"] if c in b.columns]
    out["balance"] = {"dates": _dates(b["month"]), "unit": "Bcf/d",
                      "series": {c: _round(b[c]) for c in cols}}
    latest = b.iloc[-1]
    out.setdefault("snapshot", {})["balance_month"] = latest["month"].strftime("%Y-%m")
    out["snapshot"].update({
        "dry_production_bcfd": round(float(latest["dry_production"]), 2),
        "total_supply_bcfd": round(float(latest["total_supply"]), 2),
        "total_demand_bcfd": round(float(latest["total_demand"]), 2),
        "power_burn_bcfd": round(float(latest["power_burn"]), 2),
        "lng_feedgas_bcfd": round(float(latest["lng_feedgas_estimate"]), 2),
        "supply_minus_demand_bcfd": round(float(latest["supply_minus_demand"]), 2),
    })
    tail = b.tail(24).copy()
    tail["month"] = tail["month"].dt.strftime("%Y-%m")
    out["balance_table"] = {
        "columns": ["month"] + cols,
        "rows": [[r["month"]] + [None if pd.isna(r[c]) else round(float(r[c]), 2)
                                  for c in cols] for _, r in tail.iterrows()],
    }


def production_section(curated: Path, out: dict) -> None:
    path = curated / "production_by_region.parquet"
    if not path.exists():
        return
    p = read_parquet(path)
    piv = p.pivot_table(index="month", columns="region",
                        values="dry_production_bcfd").sort_index()
    out["production_by_region"] = {
        "dates": _dates(piv.index), "unit": "Bcf/d",
        "series": {c: _round(piv[c]) for c in piv.columns}}


def storage_section(curated: Path, out: dict) -> None:
    path = curated / "storage_weekly.parquet"
    if not path.exists():
        return
    s = read_parquet(path)
    s["week_ending"] = pd.to_datetime(s["week_ending"])
    l48 = s[s["region"] == "Lower 48"].sort_values("week_ending").copy()
    if l48.empty:
        return
    l48["woy"] = l48["week_ending"].dt.isocalendar().week.astype(int)
    hist = l48[l48["week_ending"] < l48["week_ending"].max() - pd.DateOffset(years=5)]
    band = hist.groupby("woy")["working_gas_bcf"].agg(
        avg5="mean", min5="min", max5="max")
    recent = l48[l48["week_ending"] >= l48["week_ending"].max() - pd.DateOffset(years=3)]
    out["storage"] = {
        "dates": _dates(recent["week_ending"]),
        "lower48_bcf": _round(recent["working_gas_bcf"], 0),
        "band_weeks": band.index.tolist(),
        "avg5_bcf": _round(band["avg5"], 0),
        "min5_bcf": _round(band["min5"], 0),
        "max5_bcf": _round(band["max5"], 0),
        "recent_woy": recent["woy"].tolist(),
    }
    regions = {}
    for region, g in s.groupby("region"):
        g = g.sort_values("week_ending").tail(260)
        regions[region] = {"dates": _dates(g["week_ending"]),
                           "bcf": _round(g["working_gas_bcf"], 0)}
    out["storage_regions"] = regions
    last = l48.iloc[-1]
    prev = l48.iloc[-2]
    woy_avg = band.loc[last["woy"], "avg5"] if last["woy"] in band.index else float("nan")
    out.setdefault("snapshot", {}).update({
        "storage_week": last["week_ending"].strftime("%Y-%m-%d"),
        "storage_lower48_bcf": float(last["working_gas_bcf"]),
        "storage_wow_bcf": float(last["working_gas_bcf"] - prev["working_gas_bcf"]),
        "storage_vs_5yr_avg_bcf": (None if pd.isna(woy_avg)
                                   else round(float(last["working_gas_bcf"] - woy_avg), 0)),
    })


def price_section(curated: Path, out: dict) -> None:
    path = curated / "price_henry_hub_daily.parquet"
    if not path.exists():
        return
    p = read_parquet(path).sort_values("period")
    p = p[p["period"] >= p["period"].max() - pd.DateOffset(years=5)]
    out["price"] = {"dates": _dates(p["period"]),
                    "henry_hub_usd_mmbtu": _round(p["henry_hub_usd_mmbtu"], 3)}
    last = p.iloc[-1]
    out.setdefault("snapshot", {}).update({
        "price_date": last["period"].strftime("%Y-%m-%d"),
        "henry_hub_usd_mmbtu": float(last["henry_hub_usd_mmbtu"])})


def rigs_section(curated: Path, out: dict) -> None:
    path = curated / "rigs_weekly.parquet"
    if not path.exists():
        return
    r = read_parquet(path)
    if "drill_for" in r.columns:
        r = r[r["drill_for"] == "Total"]
    basins = r[r["geography_type"] == "basin"]
    if basins.empty:
        return
    piv = basins.pivot_table(index="week", columns="geography",
                             values="rigs_total").sort_index()
    out["rigs"] = {"dates": _dates(piv.index),
                   "series": {c: _round(piv[c], 0) for c in piv.columns}}
    nat = r[r["geography_type"] == "national"].sort_values("week")
    if not nat.empty:
        out.setdefault("snapshot", {})["rigs_total_us"] = int(nat.iloc[-1]["rigs_total"])
        out["snapshot"]["rigs_week"] = pd.Timestamp(nat.iloc[-1]["week"]).strftime("%Y-%m-%d")


def main() -> None:
    _, curated = project_data("gas-fundies")
    out: dict = {"generated_at": pd.Timestamp.now("UTC").strftime("%Y-%m-%dT%H:%M:%SZ"),
                 "snapshot": {}}
    balance_section(curated, out)
    production_section(curated, out)
    storage_section(curated, out)
    price_section(curated, out)
    rigs_section(curated, out)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out))
    size_kb = OUT.stat().st_size / 1024
    print(f"dashboard data: {OUT} ({size_kb:.0f} KB), sections: "
          f"{sorted(k for k in out if k not in ('generated_at', 'snapshot'))}")


if __name__ == "__main__":
    main()
