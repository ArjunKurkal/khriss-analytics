"""Modelled monthly crude/products split and LNG estimate (Option 1).

PortWatch measures ONE tanker bucket and NO gas carriers. Per Arjun's
Option-1 decision (2026-11-15), the dashboard shows:
  * the measured tanker aggregate as the primary series (elsewhere);
  * here, a MODELLED monthly crude/products split - a band, never
    daily points - and a MODELLED monthly LNG estimate from the load
    side. Both are estimates with stated assumptions, not measurements.

Crude/products method
---------------------
1. Measured monthly tanker transits T_m (PortWatch n_tanker, both
   directions - PortWatch has no direction field).
2. Volume anchor (EIA World Oil Transit Chokepoints, Vortexa-based):
   crude+condensate share of Hormuz oil volume = 70.5% (2024:
   14.6/20.7 mb/d; H1 2025: 14.7/20.8 - consistent).
3. Convert volume share to COUNT share with average loaded parcel
   sizes (stated assumptions, fleet-typical):
     crude   1.30M bbl central (range 1.00-1.60: VLCC/Suezmax/Aframax mix)
     products 0.45M bbl central (range 0.35-0.60: LR2/LR1/MR mix)
   count share_crude = (Vc/Sc) / (Vc/Sc + Vp/Sp)
     central = (0.705/1.30) / (0.705/1.30 + 0.295/0.45) = 45.3%
     low     = (0.705/1.60) / (0.705/1.60 + 0.295/0.35) = 34.3%
     high    = (0.705/1.00) / (0.705/1.00 + 0.295/0.60) = 58.9%
   i.e. a +/-~12pp band, inside the accepted +/-10-15pp.
4. The split is applied to ALL tanker transits, assuming the ballast
   (inbound) fleet mix mirrors the loaded (outbound) mix. Products =
   T_m - crude, with the band inverted.

LNG method
----------
1. Volume anchor: EIA LNG through Hormuz = 11.4 Bcf/d (H1 2025).
2. Average cargo size: blended Qatar (Q-Max ~5.8, Q-Flex ~4.6,
   conventional ~3.1-3.7 Bcf) + Das Island (small ships) = 4.2 Bcf
   central. Loaded exits/day = 11.4 / 4.2 = 2.71 (~82/month).
   Cross-check: press-reported normal Qatar loadings 70-75/month plus
   Das Island ~8/month = 78-83/month. Consistent.
3. Band: +/-25% (the accepted +/-20-30%), covering cargo-size and
   volume-anchor uncertainty.
4. Total LNG transits ~= 2x loaded exits (ballast entries), stated.
5. The flat EIA-anchored rate is applied ONLY to pre-crisis months
   (Nov 2025 - Feb 2026). From Mar 2026 the strait was effectively
   closed and no free monthly volume anchor exists, so crisis months
   carry NO modelled line - only sparse sourced points where a count
   was reported (Oct 2026: 31 loaded exits, S&P Global via press).

Outputs: data/model/monthly_split.parquet, data/model/monthly_lng.parquet
"""
from __future__ import annotations

import calendar
import json
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

PROJECT = Path(__file__).resolve().parent.parent
PW = PROJECT / "data" / "portwatch" / "chokepoint_hormuz.parquet"
OUT = PROJECT / "data" / "model"

CRUDE_VOL_SHARE = 0.705
SHARE_CENTRAL, SHARE_LO, SHARE_HI = 0.453, 0.343, 0.589
LNG_BCFD = 11.4
LNG_CARGO_BCF = 4.2
LNG_BAND = 0.25
# Sourced crisis-period points: (month, loaded exits, source note)
LNG_SOURCED = [
    ("2026-10", 31, "S&P Global tanker tracking via press (Oct 2026)"),
]
WINDOW_START = "2025-11"  # trailing-12-month window (dashboard default)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    rows = pq.read_table(PW).to_pylist()

    # Monthly tanker totals in the window.
    monthly: dict[str, dict] = {}
    for r in rows:
        m = r["date"][:7]
        if m < WINDOW_START:
            continue
        d = monthly.setdefault(m, {"tanker": 0, "days": 0})
        d["tanker"] += r["n_tanker"]
        d["days"] += 1

    split = []
    for m in sorted(monthly):
        t = monthly[m]["tanker"]
        days = monthly[m]["days"]
        full = days == calendar.monthrange(int(m[:4]), int(m[5:7]))[1]
        split.append({
            "month": m, "days_observed": days, "month_complete": full,
            "tanker_transits_measured": t,
            "crude_share_central": SHARE_CENTRAL,
            "crude_est": round(t * SHARE_CENTRAL, 1),
            "crude_lo": round(t * SHARE_LO, 1),
            "crude_hi": round(t * SHARE_HI, 1),
            "products_est": round(t * (1 - SHARE_CENTRAL), 1),
            "products_lo": round(t * (1 - SHARE_HI), 1),
            "products_hi": round(t * (1 - SHARE_LO), 1),
        })
    pq.write_table(pa.table({k: [r[k] for r in split] for k in split[0]}),
                   OUT / "monthly_split.parquet")

    lng = []
    for m in sorted(monthly):
        days = monthly[m]["days"]
        rec = {"month": m, "loaded_exits_est": None, "loaded_lo": None,
               "loaded_hi": None, "transits_est": None,
               "basis": None, "source_note": None}
        if m <= "2026-02":  # pre-crisis: flat EIA-anchored rate
            per_day = LNG_BCFD / LNG_CARGO_BCF
            est = per_day * days
            rec.update({
                "loaded_exits_est": round(est, 1),
                "loaded_lo": round(est * (1 - LNG_BAND), 1),
                "loaded_hi": round(est * (1 + LNG_BAND), 1),
                "transits_est": round(est * 2, 1),
                "basis": "modelled_eia_anchor",
                "source_note": "EIA H1 2025 LNG 11.4 Bcf/d / 4.2 Bcf "
                               "avg cargo; flat rate, pre-crisis months",
            })
        lng.append(rec)
    for m, exits, note in LNG_SOURCED:
        for rec in lng:
            if rec["month"] == m:
                rec.update({"loaded_exits_est": float(exits),
                            "transits_est": float(exits * 2),
                            "basis": "sourced_count",
                            "source_note": note})
    lng = [r for r in lng if r["basis"] is not None or r["month"] <= "2026-10"]
    pq.write_table(pa.table({k: [r[k] for r in lng] for k in lng[0]}),
                   OUT / "monthly_lng.parquet")

    (OUT / "model_meta.json").write_text(json.dumps({
        "crude_vol_share_eia": CRUDE_VOL_SHARE,
        "crude_count_share": {"central": SHARE_CENTRAL, "lo": SHARE_LO,
                              "hi": SHARE_HI},
        "lng_bcfd_eia_h1_2025": LNG_BCFD,
        "lng_avg_cargo_bcf": LNG_CARGO_BCF,
        "lng_band_frac": LNG_BAND,
    }, indent=2))
    for r in split:
        print(r["month"], "tanker", r["tanker_transits_measured"],
              "crude est", r["crude_est"], f"[{r['crude_lo']}-{r['crude_hi']}]",
              "complete" if r["month_complete"] else "PARTIAL")
    for r in lng:
        print(r["month"], r["basis"], r["loaded_exits_est"], r["source_note"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
