"""Load-weighted version of the PJM winter HDD / cold-snap analysis.

Same cleaned data and same definitions as ../hdd_coldsnap.py (NOAA GHCN-Daily,
7 stations, winters 1996-2025, Dec-Jan-Feb; HDD = max(0, base - Tavg) per
station-day; cold snaps = consecutive-day runs with Tavg < 20F / < 32F),
but every cross-station average is weighted by PJM zonal peak load instead
of equal-weighted (1/7 each).

Weights: PJM Load Forecast Report, January 2026 (posted Jan 14, 2026),
Table B-2 "Winter Peak Load (MW) and Growth Rates for Each PJM Zone and
Geographic Region (2025/26 - 2045/46)", column "25/26" -- the weather-
normalised (WN) forecast winter peak, non-coincident, unrestricted, for each
zone. Source file: 2026-load-report-tables.xlsx
(https://www.pjm.com/-/media/DotCom/planning/res-adeq/load-forecast/2026-load-report-tables.xlsx).
Weights are the 7 zones' shares of their combined 25/26 winter peak
(83,022 MW). They are relative shares among these 7 zones ONLY, not of PJM:
the 7 zones are 58.3% of the sum of all 21 PJM zones' non-coincident
2025/26 winter peaks (142,390 MW).

Station -> PJM zone mapping:
  Chicago O'Hare  USW00094846 -> COMED  15,011 MW
  Pittsburgh Intl USW00094823 -> DLCO    1,982 MW  (Duquesne Light)
  Columbus        USW00014821 -> AEP    23,423 MW
  Philadelphia    USW00013739 -> PECO    6,619 MW
  Baltimore/Wash  USW00093721 -> BGE     5,855 MW
  Washington Reag USW00013743 -> PEPCO   5,353 MW
  Richmond Intl   USW00013740 -> DOM    24,779 MW  (Dominion/VEPCO)

Sensitivity weight sets (same table, other columns) are also computed for
the headline HDD65 mean: metered 24/25 actuals and Table F-3
weather-normalised 2024/25 loads.

Outputs (this directory only; no equal-weighted file is touched):
  load_weighted_hdd_yearly.csv, load_weighted_coldsnap_by_station_winter.csv,
  load_weighted_coldsnap_yearly.csv, load_weighted_hdd_coldsnap_summary.json,
  charts 01-03, README.md
"""
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

SRC = "/home/hatch/workspace/pjm-winter-temp/pjm_winter_daily.csv"
EQ_SUMMARY = "/home/hatch/workspace/pjm-winter-temp/hdd_coldsnap_summary.json"
OUT = "/home/hatch/workspace/pjm-winter-temp/load-weighted"

# --- zonal winter peak load (MW), PJM Load Forecast Report Jan 2026, Table B-2 ---
PEAK_MW_25_26 = {  # weather-normalised forecast winter peak 2025/26
    "USW00094846": 15011,  # COMED
    "USW00094823": 1982,   # DLCO (Duquesne Light)
    "USW00014821": 23423,  # AEP
    "USW00013739": 6619,   # PECO
    "USW00093721": 5855,   # BGE
    "USW00013743": 5353,   # PEPCO
    "USW00013740": 24779,  # DOM (Dominion)
}
ZONE = {
    "USW00094846": "COMED", "USW00094823": "DLCO", "USW00014821": "AEP",
    "USW00013739": "PECO", "USW00093721": "BGE", "USW00013743": "PEPCO",
    "USW00013740": "DOM",
}
# sensitivity weight sets (MW)
PEAK_MW_METERED_24_25 = {"USW00094846": 15183, "USW00094823": 2043,
                         "USW00014821": 23717, "USW00013739": 6835,
                         "USW00093721": 6464, "USW00013743": 5780,
                         "USW00013740": 24679}
PEAK_MW_F3_WN_24_25 = {"USW00094846": 14769.1, "USW00094823": 1992.2,
                       "USW00014821": 23062.4, "USW00013739": 6586.7,
                       "USW00093721": 5860.5, "USW00013743": 5366.3,
                       "USW00013740": 23341.2}

def norm(d):
    tot = float(sum(d.values()))
    return {k: v / tot for k, v in d.items()}, tot

W, W_TOTAL = norm(PEAK_MW_25_26)
W_METERED, _ = norm(PEAK_MW_METERED_24_25)
W_F3, _ = norm(PEAK_MW_F3_WN_24_25)

df = pd.read_csv(SRC, parse_dates=["date"])
df = df.sort_values(["station", "date"]).reset_index(drop=True)
df["hdd65"] = (65.0 - df["tavg_f"]).clip(lower=0)
df["hdd60"] = (60.0 - df["tavg_f"]).clip(lower=0)
df["w"] = df["station"].map(W)

# --- per-winter load-weighted HDD / mean Tavg ---
# station winter totals, then weight them
sw = (df.groupby(["winter_year", "station"])
        .agg(hdd65=("hdd65", "sum"), hdd60=("hdd60", "sum"),
             mean_tavg=("tavg_f", "mean"), n_days=("tavg_f", "size"),
             station_name=("station_name", "first"))
        .reset_index())
sw["w"] = sw["station"].map(W)
sw["hdd65_contrib"] = sw["hdd65"] * sw["w"]
sw["hdd60_contrib"] = sw["hdd60"] * sw["w"]
w = (sw.groupby("winter_year")
       .agg(hdd65_lw=("hdd65_contrib", "sum"),
            hdd60_lw=("hdd60_contrib", "sum"),
            mean_tavg_lw=("mean_tavg", lambda x: float(np.average(x, weights=sw.loc[x.index, "w"]))),
            n_days_per_station=("n_days", "mean"))
       .reset_index())
# equal-weighted HDD65 for the same winters, for side-by-side comparison
eq = (sw.groupby("winter_year")
        .agg(hdd65_eq=("hdd65", "mean"), hdd60_eq=("hdd60", "mean"),
             mean_tavg_eq=("mean_tavg", "mean"))
        .reset_index())
w = w.merge(eq, on="winter_year")
w.to_csv(f"{OUT}/load_weighted_hdd_yearly.csv", index=False)

# sensitivity: headline mean HDD65 under the other weight sets
def headline(weights):
    s = sw.copy()
    s["w2"] = s["station"].map(weights)
    s["c"] = s["hdd65"] * s["w2"]
    return float(s.groupby("winter_year")["c"].sum().mean())
sens = {"metered_24_25": headline(W_METERED), "f3_wn_24_25": headline(W_F3)}

# --- per-month load-weighted HDD ---
m = (df.groupby(["month", "station"])
       .agg(hdd65_day=("hdd65", "mean")).reset_index())
m["w"] = m["station"].map(W)
m["hdd65_day_lw"] = m["hdd65_day"] * m["w"]
mm = m.groupby("month")["hdd65_day_lw"].sum().reset_index()
days = {12: 31, 1: 31, 2: 28.25}
mm["hdd65_per_winter_month_lw"] = [r["hdd65_day_lw"] * days[int(r["month"])] for _, r in mm.iterrows()]

# --- per-station HDD + contribution to the load-weighted total ---
s = (df.groupby(["station", "station_name", "region"])
       .agg(winters=("winter_year", "nunique"),
            hdd65_per_winter=("hdd65", lambda x: x.sum() / 30.0),
            hdd65_per_day=("hdd65", "mean"),
            mean_tavg=("tavg_f", "mean"))
       .reset_index())
s["zone"] = s["station"].map(ZONE)
s["peak_mw_25_26"] = s["station"].map(PEAK_MW_25_26)
s["weight"] = s["station"].map(W)
s["hdd65_contrib_per_winter"] = s["hdd65_per_winter"] * s["weight"]

def runs(series, thresh):
    """Longest / count / days-in-runs for consecutive True runs in a boolean series."""
    vals = (series < thresh).to_numpy()
    out = {"events": 0, "max_len": 0, "days_in_runs_ge3": 0, "days_in_runs_ge5": 0,
           "total_cold_days": int(vals.sum())}
    cur = 0
    for v in vals:
        if v:
            cur += 1
        else:
            if cur:
                out["events"] += 1
                out["max_len"] = max(out["max_len"], cur)
                if cur >= 3:
                    out["days_in_runs_ge3"] += cur
                if cur >= 5:
                    out["days_in_runs_ge5"] += cur
            cur = 0
    if cur:
        out["events"] += 1
        out["max_len"] = max(out["max_len"], cur)
        if cur >= 3:
            out["days_in_runs_ge3"] += cur
        if cur >= 5:
            out["days_in_runs_ge5"] += cur
    return out

# --- cold snaps per station, per winter (identical to equal-weighted file:
#     per-station runs do not depend on weights) ---
rows = []
for (st, wy), g in df.groupby(["station", "winter_year"]):
    g = g.sort_values("date")
    for thresh in (20, 32):
        r = runs(g["tavg_f"], thresh)
        rows.append({"station": st, "station_name": g["station_name"].iloc[0],
                     "region": g["region"].iloc[0], "zone": ZONE[st],
                     "weight": W[st], "winter_year": wy,
                     "thresh_f": thresh, **r})
cs = pd.DataFrame(rows)
cs.to_csv(f"{OUT}/load_weighted_coldsnap_by_station_winter.csv", index=False)

# --- load-weighted aggregates across stations, per winter ---
agg_rows = []
for thresh in (20, 32):
    sub = cs[cs["thresh_f"] == thresh].copy()
    for wy, g in sub.groupby("winter_year"):
        wts = g["weight"].to_numpy()
        agg_rows.append({
            "winter_year": wy, "thresh_f": thresh,
            "events_lw": float(np.average(g["events"], weights=wts)),
            "events_eq": float(g["events"].mean()),
            "max_len_max": int(g["max_len"].max()),
            "max_len_lw": float(np.average(g["max_len"], weights=wts)),
            "max_len_eq": float(g["max_len"].mean()),
            "days_ge3_lw": float(np.average(g["days_in_runs_ge3"], weights=wts)),
            "days_ge3_eq": float(g["days_in_runs_ge3"].mean()),
            "days_ge5_lw": float(np.average(g["days_in_runs_ge5"], weights=wts)),
            "days_ge5_eq": float(g["days_in_runs_ge5"].mean()),
            "cold_days_lw": float(np.average(g["total_cold_days"], weights=wts)),
            "cold_days_eq": float(g["total_cold_days"].mean()),
        })
agg = pd.DataFrame(agg_rows)

# pooled daily mean across stations (load-weighted), then runs per winter
pooled = (df.groupby("date")
            .apply(lambda g: float(np.average(g["tavg_f"], weights=g["w"])))
            .rename("pooled_tavg_lw").reset_index())
pooled = pooled.merge(df[["date", "winter_year"]].drop_duplicates(), on="date")
pooled = pooled.sort_values("date")
prows = []
for wy, g in pooled.groupby("winter_year"):
    for thresh in (20, 32):
        r = runs(g["pooled_tavg_lw"], thresh)
        prows.append({"winter_year": wy, "thresh_f": thresh, **r})
pooled_cs = pd.DataFrame(prows)
agg = agg.merge(pooled_cs[["winter_year", "thresh_f", "events", "max_len",
                           "days_in_runs_ge3", "days_in_runs_ge5"]]
               .rename(columns={"events": "pooled_events", "max_len": "pooled_max_len",
                                "days_in_runs_ge3": "pooled_days_ge3",
                                "days_in_runs_ge5": "pooled_days_ge5"}),
               on=["winter_year", "thresh_f"])
agg.to_csv(f"{OUT}/load_weighted_coldsnap_yearly.csv", index=False)

# --- overall summary ---
eq_sum = json.load(open(EQ_SUMMARY))
a20 = agg[agg["thresh_f"] == 20]
a32 = agg[agg["thresh_f"] == 32]
overall = {
    "method": "load-weighted by PJM zonal winter peak load (see weights below)",
    "source": "PJM Load Forecast Report, January 2026 (posted Jan 14, 2026), Table B-2, column 25/26 (weather-normalised forecast winter peak, non-coincident, unrestricted)",
    "source_url_tables": "https://www.pjm.com/-/media/DotCom/planning/res-adeq/load-forecast/2026-load-report-tables.xlsx",
    "source_url_report": "https://www.pjm.com/-/media/DotCom/library/reports-notices/load-forecast/2026-load-report.ashx",
    "peak_basis": "winter peak (weather-normalised forecast, 2025/26)",
    "weights": {s["station_name"]: {"zone": s["zone"], "peak_mw_25_26": float(s["peak_mw_25_26"]),
                                     "weight": round(float(s["weight"]), 5)}
                for _, s in s.iterrows()},
    "weights_total_mw_7_zones": W_TOTAL,
    "seven_zones_share_of_all_21_zones_noncoincident_25_26": 83022 / 142390,
    "seven_zones_sum_mw_vs_rto_coincident_forecast_25_26": 83022 / 137670,
    "hdd65_lw_per_winter_mean": float(w["hdd65_lw"].mean()),
    "hdd65_lw_per_winter_min": float(w["hdd65_lw"].min()),
    "hdd65_lw_per_winter_max": float(w["hdd65_lw"].max()),
    "hdd65_lw_min_winter": int(w.loc[w["hdd65_lw"].idxmin(), "winter_year"]),
    "hdd65_lw_max_winter": int(w.loc[w["hdd65_lw"].idxmax(), "winter_year"]),
    "hdd65_lw_1996_2005": float(w[w["winter_year"] <= 2005]["hdd65_lw"].mean()),
    "hdd65_lw_2006_2015": float(w[(w["winter_year"] >= 2006) & (w["winter_year"] <= 2015)]["hdd65_lw"].mean()),
    "hdd65_lw_2016_2025": float(w[w["winter_year"] >= 2016]["hdd65_lw"].mean()),
    "hdd65_lw_per_day_mean": float(df.groupby("date").apply(lambda g: float(np.average(g["hdd65"], weights=g["w"]))).mean()),
    "hdd60_lw_per_winter_mean": float(w["hdd60_lw"].mean()),
    "mean_tavg_lw_overall": float(df.groupby("date").apply(lambda g: float(np.average(g["tavg_f"], weights=g["w"]))).mean()),
    "monthly_hdd65_per_winter_month_lw": {str(int(r["month"])): round(float(r["hdd65_per_winter_month_lw"]), 1) for _, r in mm.iterrows()},
    "monthly_hdd65_per_day_lw": {str(int(r["month"])): round(float(r["hdd65_day_lw"]), 2) for _, r in mm.iterrows()},
    "per_station_hdd65_per_winter_and_contrib": {
        r["station_name"]: {"hdd65_per_winter": round(float(r["hdd65_per_winter"]), 1),
                            "weight": round(float(r["weight"]), 4),
                            "contrib_to_lw_total": round(float(r["hdd65_contrib_per_winter"]), 1)}
        for _, r in s.iterrows()},
    "coldsnap_lt20_events_per_winter_lw": float(a20["events_lw"].mean()),
    "coldsnap_lt20_mean_longest_run_lw": float(a20["max_len_lw"].mean()),
    "coldsnap_lt20_longest_run_any_station_winter": int(cs[cs["thresh_f"] == 20]["max_len"].max()),
    "coldsnap_lt20_longest_run_winter": int(cs.loc[cs[cs["thresh_f"] == 20]["max_len"].idxmax(), "winter_year"]),
    "coldsnap_lt20_longest_run_station": str(cs.loc[cs[cs["thresh_f"] == 20]["max_len"].idxmax(), "station_name"]),
    "coldsnap_lt20_days_in_ge3_runs_per_winter_lw": float(a20["days_ge3_lw"].mean()),
    "coldsnap_lt20_days_in_ge5_runs_per_winter_lw": float(a20["days_ge5_lw"].mean()),
    "coldsnap_lt32_events_per_winter_lw": float(a32["events_lw"].mean()),
    "coldsnap_lt32_mean_longest_run_lw": float(a32["max_len_lw"].mean()),
    "coldsnap_lt32_longest_run_any_station_winter": int(cs[cs["thresh_f"] == 32]["max_len"].max()),
    "coldsnap_lt32_days_in_ge3_runs_per_winter_lw": float(a32["days_ge3_lw"].mean()),
    "pooled_lw_lt20_longest_run": int(pooled_cs[pooled_cs["thresh_f"] == 20]["max_len"].max()),
    "pooled_lw_lt20_longest_run_winter": int(pooled_cs.loc[pooled_cs[pooled_cs["thresh_f"] == 20]["max_len"].idxmax(), "winter_year"]),
    "pooled_lw_lt32_longest_run": int(pooled_cs[pooled_cs["thresh_f"] == 32]["max_len"].max()),
    "pooled_lw_lt32_longest_run_winter": int(pooled_cs.loc[pooled_cs[pooled_cs["thresh_f"] == 32]["max_len"].idxmax(), "winter_year"]),
    "sensitivity_headline_hdd65_mean": {"primary_25_26_wn_forecast": float(w["hdd65_lw"].mean()),
                                        "metered_24_25_actuals": sens["metered_24_25"],
                                        "f3_wn_24_25": sens["f3_wn_24_25"]},
    "equal_weighted_comparison": {
        "hdd65_per_winter_mean_eq": eq_sum["hdd65_per_station_per_winter_mean"],
        "hdd65_per_winter_mean_lw": float(w["hdd65_lw"].mean()),
        "hdd65_decadal_eq": [eq_sum["hdd65_per_station_per_winter_1996_2005"],
                             eq_sum["hdd65_per_station_per_winter_2006_2015"],
                             eq_sum["hdd65_per_station_per_winter_2016_2025"]],
        "hdd65_decadal_lw": [float(w[w["winter_year"] <= 2005]["hdd65_lw"].mean()),
                             float(w[(w["winter_year"] >= 2006) & (w["winter_year"] <= 2015)]["hdd65_lw"].mean()),
                             float(w[w["winter_year"] >= 2016]["hdd65_lw"].mean())],
        "coldsnap_lt20_events_eq": eq_sum["coldsnap_lt20_per_station_avg_events_per_winter"],
        "coldsnap_lt20_events_lw": float(a20["events_lw"].mean()),
        "coldsnap_lt20_mean_longest_eq": eq_sum["coldsnap_lt20_per_station_avg_max_len"],
        "coldsnap_lt20_mean_longest_lw": float(a20["max_len_lw"].mean()),
        "coldsnap_lt20_days_ge3_eq": eq_sum["coldsnap_lt20_days_in_ge3_runs_per_station_per_winter"],
        "coldsnap_lt20_days_ge3_lw": float(a20["days_ge3_lw"].mean()),
        "coldsnap_lt20_days_ge5_eq": eq_sum["coldsnap_lt20_days_in_ge5_runs_per_station_per_winter"],
        "coldsnap_lt20_days_ge5_lw": float(a20["days_ge5_lw"].mean()),
        "coldsnap_lt32_events_eq": eq_sum["coldsnap_lt32_per_station_avg_events_per_winter"],
        "coldsnap_lt32_events_lw": float(a32["events_lw"].mean()),
        "coldsnap_lt32_mean_longest_eq": eq_sum["coldsnap_lt32_per_station_avg_max_len"],
        "coldsnap_lt32_mean_longest_lw": float(a32["max_len_lw"].mean()),
        "pooled_lt20_longest_eq": eq_sum["pooled_lt20_longest_run"],
        "pooled_lt20_longest_lw": int(pooled_cs[pooled_cs["thresh_f"] == 20]["max_len"].max()),
        "pooled_lt32_longest_eq": eq_sum["pooled_lt32_longest_run"],
        "pooled_lt32_longest_lw": int(pooled_cs[pooled_cs["thresh_f"] == 32]["max_len"].max()),
    },
    "coldest_hdd_winters_lw": w.nlargest(5, "hdd65_lw")[["winter_year", "hdd65_lw"]].to_dict("records"),
    "warmest_hdd_winters_lw": w.nsmallest(5, "hdd65_lw")[["winter_year", "hdd65_lw"]].to_dict("records"),
}
with open(f"{OUT}/load_weighted_hdd_coldsnap_summary.json", "w") as f:
    json.dump(overall, f, indent=2, default=str)

# --- charts ---
# 01: HDD65 by winter, load-weighted vs equal-weighted
plt.figure(figsize=(10, 4.5))
x = w["winter_year"]
plt.bar(x - 0.2, w["hdd65_eq"], width=0.4, color="#9db8c9", label="Equal-weighted")
plt.bar(x + 0.2, w["hdd65_lw"], width=0.4, color="#2c6e9b", label="Load-weighted (zonal winter peak)")
plt.axhline(overall["hdd65_lw_per_winter_mean"], color="#c0392b", ls="--",
            label=f"LW mean {overall['hdd65_lw_per_winter_mean']:.0f}")
plt.xlabel("Winter (year of Jan-Feb)"); plt.ylabel("HDD65 per winter")
plt.title("PJM winter heating degree days (base 65F), load-weighted vs equal-weighted, 1996-2025")
plt.legend(); plt.tight_layout()
plt.savefig(f"{OUT}/01_hdd_by_winter_lw_vs_eq.png", dpi=150); plt.close()

# 02: cold snaps, days in >=3-day sub-20F runs, LW vs EQ
plt.figure(figsize=(10, 4.5))
plt.plot(a20["winter_year"], a20["days_ge3_eq"], marker="o", color="#9db8c9", label="Equal-weighted")
plt.plot(a20["winter_year"], a20["days_ge3_lw"], marker="o", color="#2c6e9b", label="Load-weighted")
plt.plot(a20["winter_year"], a20["max_len_lw"], marker="s", color="#c0392b", label="LW mean longest <20F run (days)")
plt.xlabel("Winter (year of Jan-Feb)"); plt.ylabel("Days")
plt.title("PJM cold snaps: sub-20F runs, load-weighted vs equal-weighted, 1996-2025")
plt.legend(); plt.tight_layout()
plt.savefig(f"{OUT}/02_coldsnap_lw_vs_eq.png", dpi=150); plt.close()

# 03: weights vs equal weight, and per-station HDD65
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 6.5), sharex=False)
s_sorted = s.sort_values("weight", ascending=True)
ax1.barh(s_sorted["station_name"] + " (" + s_sorted["zone"] + ")", s_sorted["weight"], color="#2c6e9b")
ax1.axvline(1 / 7, color="#c0392b", ls="--", label="Equal weight (1/7 = 0.143)")
ax1.set_xlabel("Weight (share of 7-zone winter peak)")
ax1.set_title("Zonal winter-peak weights vs equal weight")
ax1.legend()
ax2.barh(s_sorted["station_name"] + " (" + s_sorted["zone"] + ")", s_sorted["hdd65_per_winter"], color="#5b8ca8")
for i, (_, r) in enumerate(s_sorted.iterrows()):
    ax2.text(r["hdd65_per_winter"] + 40, i, f"contrib {r['hdd65_contrib_per_winter']:.0f}", va="center", fontsize=8)
ax2.set_xlim(0, 3850)
ax2.set_xlabel("HDD65 per winter (station mean, 1996-2025)")
ax2.set_title("Per-station HDD65 and its contribution to the load-weighted total")
plt.tight_layout()
plt.savefig(f"{OUT}/03_weights_and_station_hdd.png", dpi=150); plt.close()

print(json.dumps(overall, indent=2, default=str))
print("winters:", len(w))
