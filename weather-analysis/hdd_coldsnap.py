"""Extension of the PJM winter-temp analysis (source: pjm_winter_daily.csv,
NOAA GHCN-Daily, 7 stations, winters 1996-2025, Dec-Jan-Feb).

Computes, from the already-downloaded cleaned data only:
- Heating degree days, base 65F (HDD65 = max(0, 65 - Tavg)), per station-day,
  summarised per winter, per month, and per station.
- Cold snaps: consecutive-day runs with Tavg < 20F and < 32F, per station
  and for the equal-weighted 7-station pooled daily mean.
- Also HDD60 as a sensitivity check (base 60F).

No new downloads, no load weights (load data not in the cleaned file;
load-weighting is a separate step needing PJM zonal load).
"""
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

SRC = "/home/hatch/workspace/pjm-winter-temp/pjm_winter_daily.csv"
OUT = "/home/hatch/workspace/pjm-winter-temp"

df = pd.read_csv(SRC, parse_dates=["date"])
df = df.sort_values(["station", "date"]).reset_index(drop=True)
df["hdd65"] = (65.0 - df["tavg_f"]).clip(lower=0)
df["hdd60"] = (60.0 - df["tavg_f"]).clip(lower=0)

# --- per-winter HDD (per station, then averaged across stations) ---
w = (
    df.groupby("winter_year")
    .agg(n_station_days=("hdd65", "size"),
         hdd65_per_station=("hdd65", "sum"),
         hdd60_per_station=("hdd60", "sum"),
         mean_tavg=("tavg_f", "mean"))
    .reset_index()
)
w["hdd65_per_station"] = w["hdd65_per_station"] / 7.0
w["hdd60_per_station"] = w["hdd60_per_station"] / 7.0
w["n_days_per_station"] = w["n_station_days"] / 7.0
w.to_csv(f"{OUT}/pjm_winter_hdd_yearly.csv", index=False)

# --- per-month HDD ---
m = (
    df.groupby("month")
    .agg(hdd65_per_station_day=("hdd65", "mean"),
         hdd65_per_station_month=("hdd65", "sum"))
    .reset_index()
)
# days per month per station per winter: Dec 31, Jan 31, Feb 28.25 avg
days = {12: 31, 1: 31, 2: 28.25}
m["hdd65_per_station_per_winter_month"] = [
    row["hdd65_per_station_day"] * days[int(row["month"])] for _, row in m.iterrows()
]

# --- per-station HDD ---
s = (
    df.groupby(["station", "station_name", "region"])
    .agg(winters=("winter_year", "nunique"),
         hdd65_per_winter=("hdd65", lambda x: x.sum() / 30.0),
         hdd65_per_day=("hdd65", "mean"),
         mean_tavg=("tavg_f", "mean"))
    .reset_index()
)

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

# --- cold snaps per station, per winter ---
rows = []
for (st, wy), g in df.groupby(["station", "winter_year"]):
    g = g.sort_values("date")
    for thresh in (20, 32):
        r = runs(g["tavg_f"], thresh)
        rows.append({"station": st, "station_name": g["station_name"].iloc[0],
                     "region": g["region"].iloc[0], "winter_year": wy,
                     "thresh_f": thresh, **r})
cs = pd.DataFrame(rows)
cs.to_csv(f"{OUT}/pjm_winter_coldsnap_by_station_winter.csv", index=False)

snap = {}
for thresh in (20, 32):
    sub = cs[cs["thresh_f"] == thresh]
    agg = sub.groupby("winter_year").agg(
        events_per_station=("events", "mean"),
        max_len_max=("max_len", "max"),
        max_len_mean=("max_len", "mean"),
        days_ge3_per_station=("days_in_runs_ge3", "mean"),
        days_ge5_per_station=("days_in_runs_ge5", "mean"),
        cold_days_per_station=("total_cold_days", "mean")).reset_index()
    snap[str(thresh)] = agg

# pooled daily mean across stations, then runs per winter
pooled = df.groupby("date").agg(pooled_tavg=("tavg_f", "mean"),
                                 winter_year=("winter_year", "first")).reset_index()
pooled = pooled.sort_values("date")
prows = []
for wy, g in pooled.groupby("winter_year"):
    for thresh in (20, 32):
        r = runs(g["pooled_tavg"], thresh)
        prows.append({"winter_year": wy, "thresh_f": thresh, **r})
pooled_cs = pd.DataFrame(prows)

# --- overall summary ---
overall = {
    "hdd65_per_station_per_winter_mean": float(w["hdd65_per_station"].mean()),
    "hdd65_per_station_per_winter_min": float(w["hdd65_per_station"].min()),
    "hdd65_per_station_per_winter_max": float(w["hdd65_per_station"].max()),
    "hdd65_min_winter": int(w.loc[w["hdd65_per_station"].idxmin(), "winter_year"]),
    "hdd65_max_winter": int(w.loc[w["hdd65_per_station"].idxmax(), "winter_year"]),
    "hdd65_per_station_per_winter_1996_2005": float(w[w["winter_year"] <= 2005]["hdd65_per_station"].mean()),
    "hdd65_per_station_per_winter_2006_2015": float(w[(w["winter_year"] >= 2006) & (w["winter_year"] <= 2015)]["hdd65_per_station"].mean()),
    "hdd65_per_station_per_winter_2016_2025": float(w[w["winter_year"] >= 2016]["hdd65_per_station"].mean()),
    "hdd65_per_day_mean": float(df["hdd65"].mean()),
    "hdd60_per_station_per_winter_mean": float(w["hdd60_per_station"].mean()),
    "monthly_hdd65_per_winter_month": {str(int(r["month"])): round(float(r["hdd65_per_station_per_winter_month"]), 1)
                                       for _, r in m.iterrows()},
    "monthly_hdd65_per_day": {str(int(r["month"])): round(float(r["hdd65_per_station_day"]), 2)
                              for _, r in m.iterrows()},
    "per_station_hdd65_per_winter": {r["station_name"]: round(float(r["hdd65_per_winter"]), 1)
                                     for _, r in s.iterrows()},
    "coldsnap_lt20_per_station_avg_events_per_winter": float(snap["20"]["events_per_station"].mean()),
    "coldsnap_lt20_per_station_avg_max_len": float(snap["20"]["max_len_mean"].mean()),
    "coldsnap_lt20_longest_run_any_station_winter": int(cs[cs["thresh_f"] == 20]["max_len"].max()),
    "coldsnap_lt20_longest_run_winter": int(cs.loc[cs[cs["thresh_f"] == 20]["max_len"].idxmax(), "winter_year"]),
    "coldsnap_lt20_longest_run_station": str(cs.loc[cs[cs["thresh_f"] == 20]["max_len"].idxmax(), "station_name"]),
    "coldsnap_lt20_days_in_ge3_runs_per_station_per_winter": float(snap["20"]["days_ge3_per_station"].mean()),
    "coldsnap_lt20_days_in_ge5_runs_per_station_per_winter": float(snap["20"]["days_ge5_per_station"].mean()),
    "coldsnap_lt32_per_station_avg_events_per_winter": float(snap["32"]["events_per_station"].mean()),
    "coldsnap_lt32_per_station_avg_max_len": float(snap["32"]["max_len_mean"].mean()),
    "coldsnap_lt32_longest_run_any_station_winter": int(cs[cs["thresh_f"] == 32]["max_len"].max()),
    "coldsnap_lt32_days_in_ge3_runs_per_station_per_winter": float(snap["32"]["days_ge3_per_station"].mean()),
    "pooled_lt20_longest_run": int(pooled_cs[pooled_cs["thresh_f"] == 20]["max_len"].max()),
    "pooled_lt20_longest_run_winter": int(pooled_cs.loc[pooled_cs[pooled_cs["thresh_f"] == 20]["max_len"].idxmax(), "winter_year"]),
    "pooled_lt32_longest_run": int(pooled_cs[pooled_cs["thresh_f"] == 32]["max_len"].max()),
    "pooled_lt32_longest_run_winter": int(pooled_cs.loc[pooled_cs[pooled_cs["thresh_f"] == 32]["max_len"].idxmax(), "winter_year"]),
    "coldest_hdd_winters": w.nlargest(5, "hdd65_per_station")[["winter_year", "hdd65_per_station"]].to_dict("records"),
    "warmest_hdd_winters": w.nsmallest(5, "hdd65_per_station")[["winter_year", "hdd65_per_station"]].to_dict("records"),
}
with open(f"{OUT}/hdd_coldsnap_summary.json", "w") as f:
    json.dump(overall, f, indent=2, default=str)

# --- charts ---
plt.figure(figsize=(10, 4.5))
plt.bar(w["winter_year"], w["hdd65_per_station"], color="#2c6e9b")
plt.axhline(overall["hdd65_per_station_per_winter_mean"], color="#c0392b", ls="--",
            label=f"30-winter mean {overall['hdd65_per_station_per_winter_mean']:.0f}")
plt.xlabel("Winter (year of Jan-Feb)"); plt.ylabel("HDD65 per station per winter")
plt.title("PJM winter heating degree days (base 65F), equal-weighted 7 stations, 1996-2025")
plt.legend(); plt.tight_layout()
plt.savefig(f"{OUT}/06_hdd_by_winter.png", dpi=150); plt.close()

plt.figure(figsize=(10, 4.5))
plt.plot(snap["20"]["winter_year"], snap["20"]["days_ge3_per_station"], marker="o", label="Days in >=3-day runs <20F")
plt.plot(snap["20"]["winter_year"], snap["20"]["max_len_mean"], marker="s", label="Mean longest <20F run (days)")
plt.xlabel("Winter (year of Jan-Feb)"); plt.ylabel("Days per station")
plt.title("PJM cold snaps: sub-20F runs, per-station average, 1996-2025")
plt.legend(); plt.tight_layout()
plt.savefig(f"{OUT}/07_coldsnap.png", dpi=150); plt.close()

print(json.dumps(overall, indent=2, default=str))
print("winters:", len(w), "| station-winters:", len(cs))
