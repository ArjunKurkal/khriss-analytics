"""Hormuz LNG feed ingest — Phase 3 integration with the Hormuz tracker.

Two layers, kept separate and labelled, per the feed contract in
~/workspace/hormuz-tracker/FEED.md (schema 1) and the global scope
memo:

1. MEASURED (forward): ship-level LNG carrier transits of the Strait
   of Hormuz from the hormuz-tracker forward collector (live AIS,
   IMO-keyed fleet-registry match), copied from
   hormuz-tracker/data/feeds/lng_crossings.parquet. Direction only —
   load status is not observed; capacity_m3 is hull nameplate, not a
   measured cargo volume. Collection began 2026-11-15; gaps are never
   backfilled. An empty crossings file is a valid state.

2. MODELLED (history): hormuz-tracker/data/model/monthly_lng.parquet,
   copied as-is — basis and source_note preserved verbatim, uncertainty
   band always shipped. Months with no published estimate stay null;
   they are not interpolated.

Reconciliation (printed, not forced): Hormuz loaded LNG exits should
approximate Qatar + UAE LNG exports. Modelled loaded exits are
converted at the model's own anchor (4.2 Bcf per cargo) and compared
with JODI EXPLNG for QA+AE at JODI's lag. Persistent divergence beyond
the band is a finding, not a number to plug.
"""
from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "shared"))
from khriss_data.config import project_data  # noqa: E402

HORMUZ = Path.home() / "workspace" / "hormuz-tracker" / "data"
BCF_PER_CARGO = 4.2  # the modelled series' own EIA anchor


def main() -> None:
    _, curated = project_data("gas-fundies")
    feeds = curated.parent / "feeds"
    feeds.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")

    crossings_src = HORMUZ / "feeds" / "lng_crossings.parquet"
    crossings = pd.read_parquet(crossings_src)
    crossings.to_parquet(feeds / "hormuz_lng_crossings.parquet", index=False)
    if crossings.empty:
        daily = pd.DataFrame(columns=["date", "transits_total", "outbound",
                                      "inbound", "capacity_m3_outbound",
                                      "basis"])
        monthly = pd.DataFrame(columns=["month", "transits_total", "outbound",
                                        "inbound", "capacity_m3_outbound",
                                        "basis"])
    else:
        c = crossings.copy()
        c["is_out"] = (c["direction"] == "outbound").astype(int)
        daily = (c.groupby("date").agg(
            transits_total=("imo", "size"), outbound=("is_out", "sum"),
            capacity_m3_outbound=("capacity_m3",
                                  lambda s: s[c.loc[s.index, "is_out"] == 1].sum()))
            .reset_index())
        daily["inbound"] = daily["transits_total"] - daily["outbound"]
        daily["basis"] = "measured_collector"
        monthly = (c.groupby("month").agg(
            transits_total=("imo", "size"), outbound=("is_out", "sum"),
            capacity_m3_outbound=("capacity_m3",
                                  lambda s: s[c.loc[s.index, "is_out"] == 1].sum()))
            .reset_index())
        monthly["inbound"] = monthly["transits_total"] - monthly["outbound"]
        monthly["basis"] = "measured_collector"
    daily.to_parquet(feeds / "hormuz_lng_daily.parquet", index=False)
    monthly.to_parquet(feeds / "hormuz_lng_measured_monthly.parquet",
                       index=False)
    print(f"Hormuz measured: {len(crossings)} crossings copied; "
          f"{len(daily)} days, {len(monthly)} months")

    modelled = pd.read_parquet(HORMUZ / "model" / "monthly_lng.parquet")
    modelled["retrieved_at"] = now
    modelled.to_parquet(feeds / "hormuz_lng_modelled_monthly.parquet",
                        index=False)
    est = modelled.dropna(subset=["loaded_exits_est"])
    print(f"Hormuz modelled: {len(modelled)} months copied, "
          f"{len(est)} with published estimates "
          f"({est['month'].min()} .. {est['month'].max()})")

    # Reconciliation vs JODI Qatar + UAE LNG exports.
    jodi_path = curated / "jodi_country_monthly.parquet"
    if jodi_path.exists() and not est.empty:
        jodi = pd.read_parquet(jodi_path)
        cols = [c for c in jodi.columns if "lng" in c.lower()]
        exp_col = ("exports_lng_bcfd" if "exports_lng_bcfd" in jodi.columns
                   else next((c for c in cols if "export" in c.lower()),
                             None))
        if exp_col:
            qa = jodi[jodi["country"].isin(["QA", "AE"])]
            monthly_jodi = (qa.groupby("month")[exp_col].sum()
                            .rename("jodi_qa_ae_lng_exports_bcfd")
                            .reset_index())
            monthly_jodi["month"] = pd.to_datetime(
                monthly_jodi["month"]).dt.strftime("%Y-%m")
            rec = est.merge(monthly_jodi, on="month", how="inner")
            if not rec.empty:
                rec["modelled_bcfd"] = (rec["loaded_exits_est"]
                                        * BCF_PER_CARGO
                                        / pd.to_datetime(rec["month"]).dt.days_in_month)
                rec["diff_pct"] = (100 * (rec["modelled_bcfd"]
                                   - rec["jodi_qa_ae_lng_exports_bcfd"])
                                   / rec["jodi_qa_ae_lng_exports_bcfd"])
                print("Reconciliation, modelled Hormuz exits vs JODI "
                      "QA+AE LNG exports (Bcf/d):")
                print(rec[["month", "modelled_bcfd",
                           "jodi_qa_ae_lng_exports_bcfd", "diff_pct"]]
                      .round(2).to_string(index=False))
            else:
                print("Reconciliation: no overlapping months yet")
        else:
            print(f"Reconciliation skipped: no LNG export column in JODI "
                  f"country file (columns with 'lng': {cols})")


if __name__ == "__main__":
    main()
