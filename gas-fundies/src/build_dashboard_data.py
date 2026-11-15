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


MWH_PER_MMBTU = 3.41214  # 1 MWh = 3.41214 MMBtu


def global_price_section(curated: Path, out: dict) -> None:
    """Front-month CME settlements: TTF (EUR contract, converted at the ECB
    EUR/USD reference rate), TFU cross-check, JKM. Capture starts
    2026-11-12 — the CME feed retains only ~5 business days, so the series
    accrues daily and has no earlier history. Spreads vs Henry Hub spot
    are computed only on dates where both legs exist."""
    path = curated / "prices_cme_settlements.parquet"
    fx_path = curated / "fx_eurusd_daily.parquet"
    if not path.exists() or not fx_path.exists():
        return
    cme = read_parquet(path)
    cme["trade_date"] = pd.to_datetime(cme["trade_date"])
    cme["contract_date"] = pd.to_datetime(cme["contract_date"])
    front = (cme.sort_values("contract_date")
             .groupby(["trade_date", "product"]).first().reset_index())
    piv = front.pivot_table(index="trade_date", columns="product",
                            values="settle").sort_index()
    if "TTF_EUR" not in piv.columns:
        return
    fx = read_parquet(fx_path).sort_values("date")
    merged = pd.merge_asof(piv.reset_index(), fx, left_on="trade_date",
                           right_on="date", direction="backward").drop(columns="date")
    merged["ttf_usd"] = merged["TTF_EUR"] / MWH_PER_MMBTU * merged["eur_usd"]
    dates = _dates(merged["trade_date"])
    section = {"dates": dates,
               "ttf_eur_mwh": _round(merged["TTF_EUR"], 3),
               "ttf_usd_mmbtu": _round(merged["ttf_usd"], 3),
               "fx_eurusd": _round(merged["eur_usd"], 4)}
    if "TTF_USD" in merged.columns:
        section["tfu_usd_mmbtu"] = _round(merged["TTF_USD"], 3)
    if "JKM" in merged.columns:
        section["jkm_usd_mmbtu"] = _round(merged["JKM"], 3)
        section["jkm_minus_ttf"] = _round(merged["JKM"] - merged["ttf_usd"], 3)
    labels = front[front["product"] == "TTF_EUR"].sort_values("trade_date")
    section["ttf_front_contract"] = labels["contract_month"].tolist()
    out["global_prices"] = section

    last = merged.iloc[-1]
    snap = {"global_price_date": last["trade_date"].strftime("%Y-%m-%d"),
            "ttf_front_eur_mwh": round(float(last["TTF_EUR"]), 3),
            "ttf_front_usd_mmbtu": round(float(last["ttf_usd"]), 3)}
    if "JKM" in merged.columns and pd.notna(last["JKM"]):
        snap["jkm_front_usd_mmbtu"] = round(float(last["JKM"]), 3)
    out.setdefault("snapshot", {}).update(snap)

    hh_path = curated / "price_henry_hub_daily.parquet"
    if hh_path.exists():
        hh = read_parquet(hh_path)[["period", "henry_hub_usd_mmbtu"]]
        hh["period"] = pd.to_datetime(hh["period"])
        both = merged.merge(hh, left_on="trade_date", right_on="period",
                            how="inner").sort_values("trade_date")
        if not both.empty:
            out["global_prices"]["ttf_minus_hh"] = {
                "dates": _dates(both["trade_date"]),
                "values": _round(both["ttf_usd"] - both["henry_hub_usd_mmbtu"], 3)}


JODI_REGIONS = ["North America", "Europe", "Asia-Pacific", "Middle East",
                "FSU", "Rest of World"]


def jodi_section(curated: Path, out: dict) -> None:
    """Global/regional monthly balance from JODI Gas (Bcf/d). Self-reported
    national statistics; the regional balancing item is shown, and the
    reporter count is shipped so thin recent months are legible."""
    path = curated / "jodi_region_monthly.parquet"
    if not path.exists():
        return
    r = read_parquet(path)
    r = r[r["month"] >= "2015-01-01"].sort_values("month")
    months = pd.DatetimeIndex(sorted(r["month"].unique()))
    dates = _dates(months)
    prod, bal, lng = {}, {}, {}
    for region in JODI_REGIONS:
        sub = r[r["region"] == region].set_index("month").reindex(months)
        prod[region] = _round(sub["production_bcfd"])
        bal[region] = _round(sub["balancing_item_bcfd"])
        lng[region] = _round(sub["exports_lng_bcfd"])
    glob = r[r["region"] == "Global"].set_index("month").reindex(months)
    out["jodi"] = {
        "dates": dates, "unit": "Bcf/d",
        "production_by_region": prod,
        "balancing_by_region": bal,
        "lng_exports_by_region": lng,
        "global_deliveries": _round(glob["deliveries_bcfd"]),
        "global_balancing": _round(glob["balancing_item_bcfd"]),
        "countries_reporting": [int(x) for x in glob["countries_reporting"]],
        "vintage": int(read_parquet(curated / "jodi_country_monthly.parquet")
                       ["vintage"].iloc[0]),
    }
    covered = glob[glob["countries_reporting"] >= 50]
    if not covered.empty:
        last = covered.iloc[-1]
        out.setdefault("snapshot", {}).update({
            "jodi_month": last.name.strftime("%Y-%m"),
            "global_production_bcfd": round(float(last["production_bcfd"]), 1),
            "global_deliveries_bcfd": round(float(last["deliveries_bcfd"]), 1),
            "global_balancing_bcfd": round(float(last["balancing_item_bcfd"]), 2),
        })


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


GWH_PER_BCF = 303.6  # at 1,036 Btu/cf
EU27_NODES = {"AT", "BE", "BG", "CZ", "DE", "DK", "EE", "ES", "FR", "GR",
              "HR", "HU", "IE", "SK", "PT", "IT", "PL", "LU", "MT", "LV",
              "LT", "FI", "SI", "RO", "SE", "NL", "CY"}
CORRIDORS = {
    "Norway": {"NO"},
    "Russia legacy routes": {"RU", "BY", "UA", "PLYAM", "RUKAL"},
    "North Africa": {"DZ", "MA", "LY", "TN"},
    "Türkiye / TAP": {"TR", "TAP", "TBP", "IGB"},
    "United Kingdom": {"UK", "IUK"},
}


def europe_section(curated: Path, out: dict) -> None:
    """Europe daily layer: GIE storage + LNG terminals, ENTSOG pipeline
    inflows to the EU27 by corridor (Bcf/d). GIE data is shown under
    GIE's attribution condition."""
    sec: dict = {}
    sp = curated / "gie_storage_daily.parquet"
    if sp.exists():
        s = read_parquet(sp)
        eu = s[s["scope"] == "eu"].sort_values("gas_day")
        if not eu.empty:
            sec["storage"] = {
                "dates": _dates(eu["gas_day"]),
                "twh": _round(eu["gas_in_storage_twh"], 1),
                "full_pct": _round(eu["full_pct"], 1),
            }
            last = eu.iloc[-1]
            out.setdefault("snapshot", {}).update({
                "eu_storage_twh": round(float(last["gas_in_storage_twh"]), 1),
                "eu_storage_full_pct": round(float(last["full_pct"]), 1),
                "eu_storage_date": pd.Timestamp(last["gas_day"]).strftime("%Y-%m-%d"),
            })
    lp = curated / "gie_lng_daily.parquet"
    if lp.exists():
        lng = read_parquet(lp)
        eu = lng[lng["scope"] == "eu"].sort_values("gas_day")
        if not eu.empty:
            sec["lng"] = {
                "dates": _dates(eu["gas_day"]),
                "sendout_bcfd": _round(eu["send_out_gwh"] / GWH_PER_BCF),
                "inventory_twh": _round(eu["lng_inventory_gwh"] / 1000, 1),
            }
            last = eu.iloc[-1]
            out.setdefault("snapshot", {}).update({
                "eu_lng_sendout_bcfd": round(
                    float(last["send_out_gwh"]) / GWH_PER_BCF, 2),
                "eu_lng_date": pd.Timestamp(last["gas_day"]).strftime("%Y-%m-%d"),
            })
    bp = curated / "entsog_border_daily.parquet"
    if bp.exists():
        b = read_parquet(bp)
        b = b[b["to_node"].isin(EU27_NODES)]
        b["corridor"] = "Other external"
        for name, nodes in CORRIDORS.items():
            b.loc[b["from_node"].isin(nodes), "corridor"] = name
        piv = (b.groupby([b["gas_day"], "corridor"])["flow_gwh_d"].sum()
               .unstack(fill_value=0) / GWH_PER_BCF)
        names = [c for c in CORRIDORS if c in piv.columns]
        if "Other external" in piv.columns:
            names.append("Other external")
        sec["inflows"] = {"dates": _dates(piv.index),
                          "series": {n: _round(piv[n]) for n in names}}
        recent = piv.tail(30).mean()
        if "Norway" in recent:
            out.setdefault("snapshot", {})["norway_inflow_bcfd_30d"] = round(
                float(recent["Norway"]), 2)
    if sec:
        out["europe"] = sec


DOE_REGIONS = {
    "Europe": {"United Kingdom", "Netherlands", "Spain", "France", "Italy",
               "Germany", "Poland", "Belgium", "Portugal", "Greece",
               "Croatia", "Lithuania", "Malta", "Finland", "Sweden",
               "Norway", "Denmark", "Ireland", "Turkey", "Türkiye"},
    "Asia": {"Japan", "South Korea", "Korea, South", "China", "India",
             "Taiwan", "Thailand", "Singapore", "Pakistan", "Bangladesh",
             "Philippines", "Indonesia", "Malaysia", "Vietnam", "Myanmar"},
    "Middle East": {"Jordan", "Kuwait", "United Arab Emirates", "Israel",
                    "Bahrain", "Oman"},
    "Africa": {"Egypt", "Senegal", "Mauritania", "Morocco", "Nigeria",
               "Togo", "Mozambique"},
}


def doe_section(curated: Path, out: dict) -> None:
    """US LNG exports by destination region (Bcf/month) from the DOE
    cargo file — exports only (re-exports excluded), destination as
    reported at departure."""
    path = curated / "doe_lng_cargoes.parquet"
    if not path.exists():
        return
    c = read_parquet(path).dropna(subset=["date"])
    if c.empty:
        return
    region_of = {}
    for region, countries in DOE_REGIONS.items():
        for country in countries:
            region_of[country] = region
    c["region"] = c["country"].map(region_of).fillna("Latin America & other")
    c["month"] = pd.to_datetime(c["date"]).dt.to_period("M").dt.to_timestamp()
    piv = (c.groupby(["month", "region"])["exports_bcf"].sum()
           .unstack(fill_value=0))
    names = [r for r in ["Europe", "Asia", "Middle East", "Africa",
                         "Latin America & other"] if r in piv.columns]
    out["doe"] = {"dates": _dates(piv.index), "unit": "Bcf/month",
                  "series": {n: _round(piv[n], 1) for n in names}}


def japan_section(curated: Path, out: dict) -> None:
    """Japan LNG imports by origin (Mt/month), MOF via UN Comtrade."""
    path = curated / "japan_lng_imports_monthly.parquet"
    if not path.exists():
        return
    j = read_parquet(path)
    top = ["Australia", "United States", "Malaysia", "Russia", "Qatar"]
    piv = (j[j["partner_code"] != 0]
           .pivot_table(index="month", columns="partner",
                        values="net_wgt_tonnes", aggfunc="sum")
           .fillna(0) / 1e6)
    series = {}
    for name in top:
        if name in piv.columns:
            series[name] = _round(piv[name], 2)
    named = [n for n in top if n in piv.columns]
    series["Other"] = _round(piv.drop(columns=named).sum(axis=1), 2)
    world = (j[j["partner_code"] == 0].set_index("month")
             ["net_wgt_tonnes"].reindex(piv.index) / 1e6)
    out["japan"] = {"dates": _dates(piv.index), "unit": "Mt/month",
                    "series": series, "total": _round(world, 2)}
    last_month = piv.index.max()
    qa = j[(j["partner"] == "Qatar") & (j["month"] == last_month)]
    out.setdefault("snapshot", {}).update({
        "japan_imports_mt": round(float(world.loc[last_month]), 2),
        "japan_month": last_month.strftime("%Y-%m"),
        "japan_qatar_kt": round(float(qa["net_wgt_tonnes"].sum()) / 1000, 0)
        if not qa.empty else 0.0,
    })


def hormuz_section(curated: Path, out: dict) -> None:
    """Hormuz LNG: modelled monthly history (basis labels preserved)
    plus measured collector crossings as they accrue."""
    feeds = curated.parent / "feeds"
    mp = feeds / "hormuz_lng_modelled_monthly.parquet"
    if not mp.exists():
        return
    m = read_parquet(mp)
    sec = {
        "months": [pd.Period(mo, freq="M").to_timestamp().strftime("%Y-%m-%d")
                   for mo in m["month"]],
        "loaded_exits_est": _round(m["loaded_exits_est"], 1),
        "loaded_lo": _round(m["loaded_lo"], 1),
        "loaded_hi": _round(m["loaded_hi"], 1),
        "basis": [b if isinstance(b, str) else None for b in m["basis"]],
        "source_note": [s if isinstance(s, str) else None
                        for s in m["source_note"]],
    }
    dp = feeds / "hormuz_lng_measured_monthly.parquet"
    if dp.exists():
        d = read_parquet(dp)
        if not d.empty:
            sec["measured"] = {
                "months": [pd.Period(mo, freq="M").to_timestamp()
                           .strftime("%Y-%m-%d") for mo in d["month"]],
                "outbound": [int(x) for x in d["outbound"]],
                "inbound": [int(x) for x in d["inbound"]],
            }
    out["hormuz"] = sec
    est = m.dropna(subset=["loaded_exits_est"])
    if not est.empty:
        last = est.iloc[-1]
        out.setdefault("snapshot", {}).update({
            "hormuz_loaded_exits": float(last["loaded_exits_est"]),
            "hormuz_month": str(last["month"]),
            "hormuz_basis": str(last["basis"]),
        })


def _sanitize(obj):
    """Recursively convert NaN/Infinity floats to None.

    Strict JSON (what browsers parse) has no NaN/Infinity literals; Python's
    json module emits them by default, which silently breaks the dashboard.
    Missing values must ship as null, which Plotly renders as gaps.
    """
    import math
    if isinstance(obj, float):
        return obj if math.isfinite(obj) else None
    if isinstance(obj, dict):
        return {k: _sanitize(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_sanitize(v) for v in obj]
    return obj


def main() -> None:
    _, curated = project_data("gas-fundies")
    out: dict = {"generated_at": pd.Timestamp.now("UTC").strftime("%Y-%m-%dT%H:%M:%SZ"),
                 "snapshot": {}}
    balance_section(curated, out)
    production_section(curated, out)
    storage_section(curated, out)
    price_section(curated, out)
    global_price_section(curated, out)
    jodi_section(curated, out)
    europe_section(curated, out)
    doe_section(curated, out)
    japan_section(curated, out)
    hormuz_section(curated, out)
    rigs_section(curated, out)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(_sanitize(out), allow_nan=False))
    size_kb = OUT.stat().st_size / 1024
    print(f"dashboard data: {OUT} ({size_kb:.0f} KB), sections: "
          f"{sorted(k for k in out if k not in ('generated_at', 'snapshot'))}")


if __name__ == "__main__":
    main()
