"""
PJM winter temperature distribution analysis — free NOAA GHCN-Daily data.
Basic Python libraries only: pandas / numpy / matplotlib (+ seaborn, already installed).

Region: PJM Interconnection — 7 representative GHCN-Daily stations.
Period: Winters Dec-Jan-Feb, 1995-96 through 2024-25 (winter_year 1996-2025).
  winter_year = year of Jan/Feb (Dec Y belongs to winter Y+1).
Source: NOAA GHCN-Daily .dly files
  https://www.ncei.noaa.gov/pub/data/ghcn/daily/all/<station>.dly
  No key. TMAX/TMIN/TAVG in tenths of degC, converted to degF.
  TAVG where present, else (TMAX+TMIN)/2. Range = TMAX-TMIN.
  Values with a non-blank quality flag are excluded.
Outputs: cleaned CSV + 5 PNG charts + summary JSON in this directory.
"""
import json
import math
import os
import urllib.request
from datetime import date

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

BASE = os.path.dirname(os.path.abspath(__file__))
URL = "https://www.ncei.noaa.gov/pub/data/ghcn/daily/all/{}.dly"

STATIONS = {
    "USW00013739": ("Philadelphia Intl, PA", "East"),
    "USW00094823": ("Pittsburgh Intl, PA", "West"),
    "USW00093721": ("Baltimore/Washington Intl, MD", "East"),
    "USW00013743": ("Washington Reagan, DC", "East"),
    "USW00014821": ("Columbus, OH", "West"),
    "USW00094846": ("Chicago O'Hare, IL", "West"),
    "USW00013740": ("Richmond Intl, VA", "Central"),
}
# NOTE (2026-11-14 correction): the initial station list used three wrong IDs,
# verified against NOAA ghcnd-stations.txt:
#   USW00013722 = Raleigh AP, NC (not Pittsburgh) — replaced by USW00094823 Pittsburgh Intl ASOS
#   USW00013737 = Norfolk Intl, VA (not Richmond) — replaced by USW00013740 Richmond Intl
#   USW00014819 = Chicago Midway AP (not O'Hare) — replaced by USW00094846 Chicago O'Hare Intl
# The first run's pooled stats were therefore biased warm (Raleigh/Norfolk) and were discarded.

WINTER_MONTHS = {12, 1, 2}
START_DEC_YEAR = 1995   # Dec 1995 ... Feb 2025
END_FEB_YEAR = 2025

def c10_to_f(v):
    return v / 10.0 * 9.0 / 5.0 + 32.0

def download(station):
    path = os.path.join(BASE, f"{station}.dly")
    if os.path.exists(path) and os.path.getsize(path) > 100_000:
        print(f"{station}: using cached {path}")
        return path
    print(f"{station}: downloading ...")
    req = urllib.request.Request(URL.format(station), headers={"User-Agent": "Muse-PJM-analysis/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r, open(path, "wb") as f:
        f.write(r.read())
    print(f"{station}: {os.path.getsize(path):,} bytes")
    return path

def parse_dly(path, station):
    # .dly fixed width: ID 0:11, YEAR 11:15, MONTH 15:17, ELEMENT 17:21,
    # per day d (0..30): value 21+d*8 : 26+d*8, mflag 26+d*8, qflag 27+d*8, sflag 28+d*8
    rows = {}
    with open(path, encoding="utf-8", errors="ignore") as f:
        for line in f:
            if len(line) < 21:
                continue
            element = line[17:21]
            if element not in ("TMAX", "TMIN", "TAVG"):
                continue
            try:
                year = int(line[11:15]); month = int(line[15:17])
            except ValueError:
                continue
            if month not in WINTER_MONTHS:
                continue
            # winter window: Dec 1995 - Feb 2025
            if month == 12 and not (START_DEC_YEAR <= year <= 2024):
                continue
            if month in (1, 2) and not (1996 <= year <= END_FEB_YEAR):
                continue
            for d in range(31):
                off = 21 + d * 8
                if off + 5 > len(line):
                    break
                try:
                    val = int(line[off:off+5])
                except ValueError:
                    continue
                qflag = line[off+6] if off+6 < len(line) else " "
                if val == -9999 or qflag != " ":
                    continue
                try:
                    dt = date(year, month, d + 1)
                except ValueError:
                    continue
                rows.setdefault(dt, {})[element] = c10_to_f(val)
    recs = []
    for dt, vals in sorted(rows.items()):
        tmax = vals.get("TMAX"); tmin = vals.get("TMIN"); tavg = vals.get("TAVG")
        if tavg is None and tmax is not None and tmin is not None:
            tavg = (tmax + tmin) / 2.0
        rng = (tmax - tmin) if (tmax is not None and tmin is not None) else np.nan
        winter_year = dt.year + 1 if dt.month == 12 else dt.year
        recs.append({
            "station": station, "date": dt, "winter_year": winter_year,
            "month": dt.month, "tavg_f": tavg, "tmax_f": tmax,
            "tmin_f": tmin, "range_f": rng,
        })
    return pd.DataFrame(recs)

def stats_series(s):
    s = s.dropna()
    return {
        "n": int(len(s)), "mean": float(s.mean()), "median": float(s.median()),
        "std": float(s.std()), "skew": float(s.skew()),
        "p10": float(s.quantile(0.10)), "p25": float(s.quantile(0.25)),
        "p75": float(s.quantile(0.75)), "p90": float(s.quantile(0.90)),
        "min": float(s.min()), "max": float(s.max()),
        "share_lt0": float((s < 0).mean()), "share_lt10": float((s < 10).mean()),
        "share_lt20": float((s < 20).mean()), "share_lt32": float((s < 32).mean()),
        "share_gt50": float((s > 50).mean()), "share_gt60": float((s > 60).mean()),
    }

def trend(x, y):
    """OLS slope per decade, r, and t-stat (no scipy)."""
    x = np.asarray(x, dtype=float); y = np.asarray(y, dtype=float)
    n = len(x)
    slope, intercept = np.polyfit(x, y, 1)
    r = float(np.corrcoef(x, y)[0, 1]) if n > 2 else float("nan")
    yhat = slope * x + intercept
    resid = y - yhat
    dof = n - 2
    s2 = float(np.sum(resid**2) / dof) if dof > 0 else float("nan")
    se = math.sqrt(s2 / np.sum((x - x.mean())**2)) if n > 2 else float("nan")
    t = slope / se if se and se > 0 else float("nan")
    # |t| > ~2.05 is roughly p<0.05 for dof~28
    return {"slope_per_year": float(slope), "slope_per_decade": float(slope*10),
            "r": r, "t_stat": float(t), "n": int(n),
            "significant_approx_p05": bool(abs(t) > 2.05) if t == t else False}

def main():
    all_frames = []
    coverage = {}
    for station, (name, region) in STATIONS.items():
        path = download(station)
        df = parse_dly(path, station)
        df["station_name"] = name
        df["region"] = region
        all_frames.append(df)
        # expected winter days: 30 winters x (31+31+28) + 8 leap Feb days = 2708
        expected = 2708
        n_tavg = int(df["tavg_f"].notna().sum())
        n_range = int(df["range_f"].notna().sum())
        coverage[station] = {
            "name": name, "region": region,
            "rows_parsed": int(len(df)), "expected_days": expected,
            "tavg_days": n_tavg, "tavg_coverage_pct": round(100*n_tavg/expected, 2),
            "range_days": n_range, "range_coverage_pct": round(100*n_range/expected, 2),
            "date_min": str(df["date"].min()) if len(df) else None,
            "date_max": str(df["date"].max()) if len(df) else None,
        }
        print(station, name, f"tavg {n_tavg}/{expected} = {100*n_tavg/expected:.1f}%")

    df = pd.concat(all_frames, ignore_index=True)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values(["date", "station"]).reset_index(drop=True)
    # Keep only days with a tavg for the main distribution; range needs both.
    df.to_csv(os.path.join(BASE, "pjm_winter_daily.csv"), index=False)
    print(f"cleaned CSV rows: {len(df)}")

    tavg = df["tavg_f"].dropna()
    rng = df["range_f"].dropna()

    summary = {}
    summary["stations"] = coverage
    summary["period"] = "Winters Dec-Jan-Feb, winter_year 1996-2025 (Dec 1995 - Feb 2025)"
    summary["total_station_days_expected"] = 7 * 2708
    summary["total_rows"] = int(len(df))
    summary["total_tavg_days"] = int(tavg.notna().sum())
    summary["overall_coverage_pct"] = round(100*int(tavg.notna().sum())/(7*2708), 2)
    summary["overall_tavg"] = stats_series(tavg)
    summary["overall_range"] = stats_series(rng)

    # By month
    by_month = {}
    for m, label in [(12, "Dec"), (1, "Jan"), (2, "Feb")]:
        sub = df[df["month"] == m]
        by_month[label] = {
            "tavg": stats_series(sub["tavg_f"]),
            "range": stats_series(sub["range_f"]),
        }
    summary["by_month"] = by_month

    # By station (tavg)
    by_station = {}
    for st, sub in df.groupby("station"):
        by_station[STATIONS[st][0]] = stats_series(sub["tavg_f"])
    summary["by_station_tavg"] = by_station

    # Yearly winter stats (pooled daily across stations)
    yearly = []
    for wy, sub in df.groupby("winter_year"):
        s = sub["tavg_f"].dropna()
        yearly.append({
            "winter_year": int(wy), "n_days": int(len(s)),
            "mean_tavg_f": float(s.mean()), "median_tavg_f": float(s.median()),
            "p10_tavg_f": float(s.quantile(0.10)), "p90_tavg_f": float(s.quantile(0.90)),
            "share_lt20": float((s < 20).mean()), "share_lt10": float((s < 10).mean()),
            "cold_days_lt20_per_station": float((s < 20).sum() / sub["station"].nunique()),
            "cold_days_lt10_per_station": float((s < 10).sum() / sub["station"].nunique()),
            "mean_range_f": float(sub["range_f"].mean()),
        })
    ydf = pd.DataFrame(yearly)
    ydf.to_csv(os.path.join(BASE, "pjm_winter_yearly.csv"), index=False)
    summary["yearly"] = yearly
    summary["trend_winter_mean"] = trend(ydf["winter_year"], ydf["mean_tavg_f"])
    summary["trend_cold_share_lt20"] = trend(ydf["winter_year"], ydf["share_lt20"])
    summary["trend_cold_days_lt10"] = trend(ydf["winter_year"], ydf["cold_days_lt10_per_station"])

    # Periods: winter_year 1996-2005, 2006-2015, 2016-2025
    periods = {"1996-2005": (1996, 2005), "2006-2015": (2006, 2015), "2016-2025": (2016, 2025)}
    by_period = {}
    for label, (a, b) in periods.items():
        sub = df[(df["winter_year"] >= a) & (df["winter_year"] <= b)]
        by_period[label] = {"tavg": stats_series(sub["tavg_f"]), "range": stats_series(sub["range_f"])}
    summary["by_period"] = by_period

    # Climatology: mean tavg by calendar date Dec 1 - Feb 28/29
    df["month_day"] = df["date"].dt.strftime("%m-%d")
    clim = df.groupby("month_day")["tavg_f"].agg(["mean", "median", lambda s: s.quantile(0.10), lambda s: s.quantile(0.90), "count"])
    clim.columns = ["mean", "median", "p10", "p90", "count"]
    # order Dec 1..31, Jan 1..31, Feb 1..29
    order = [f"12-{d:02d}" for d in range(1, 32)] + [f"01-{d:02d}" for d in range(1, 32)] + [f"02-{d:02d}" for d in range(1, 30)]
    clim = clim.reindex(order)
    clim["rolling15_mean"] = clim["mean"].rolling(15, center=True, min_periods=1).mean()
    clim["rolling15_p10"] = clim["p10"].rolling(15, center=True, min_periods=1).mean()
    clim["rolling15_p90"] = clim["p90"].rolling(15, center=True, min_periods=1).mean()
    clim.to_csv(os.path.join(BASE, "pjm_winter_climatology.csv"))
    summary["climatology"] = {
        "coldest_date": str(clim["rolling15_mean"].idxmin()),
        "coldest_rolling15_mean_f": float(clim["rolling15_mean"].min()),
        "warmest_date": str(clim["rolling15_mean"].idxmax()),
        "warmest_rolling15_mean_f": float(clim["rolling15_mean"].max()),
        "dec1_rolling15_f": float(clim.loc["12-01", "rolling15_mean"]),
        "jan15_rolling15_f": float(clim.loc["01-15", "rolling15_mean"]),
        "feb28_rolling15_f": float(clim.loc["02-28", "rolling15_mean"]),
    }

    # Range vs tavg bins
    bins = [-30, 0, 10, 20, 30, 40, 50, 60, 80]
    labels = ["<0", "0-10", "10-20", "20-30", "30-40", "40-50", "50-60", ">60"]
    tmp = df.dropna(subset=["tavg_f", "range_f"]).copy()
    tmp["tavg_bin"] = pd.cut(tmp["tavg_f"], bins=bins, labels=labels)
    rb = tmp.groupby("tavg_bin", observed=True)["range_f"].agg(["mean", "median", "count"])
    summary["range_by_tavg_bin"] = {k: {"mean_range_f": float(v["mean"]), "median_range_f": float(v["median"]), "n": int(v["count"])} for k, v in rb.iterrows()}
    summary["range_by_month"] = {k: {"mean": float(v["range"]["mean"]), "median": float(v["range"]["median"])} for k, v in by_month.items()}

    with open(os.path.join(BASE, "summary.json"), "w") as f:
        json.dump(summary, f, indent=2)
    print(json.dumps({k: summary[k] for k in ["period", "total_tavg_days", "overall_coverage_pct", "overall_tavg", "trend_winter_mean"]}, indent=2))

    # ---------------- Plots ----------------
    plt.rcParams.update({"figure.dpi": 150, "axes.grid": True, "grid.alpha": 0.3})
    sns.set_style("whitegrid")

    # 1. Overall histogram + KDE
    fig, ax = plt.subplots(figsize=(9, 5))
    sns.histplot(tavg, bins=45, kde=True, ax=ax, color="#2c6e9b")
    ax.axvline(tavg.mean(), color="red", ls="--", lw=1.5, label=f"Mean {tavg.mean():.1f}°F")
    ax.axvline(tavg.median(), color="darkorange", ls=":", lw=1.5, label=f"Median {tavg.median():.1f}°F")
    ax.set_title("PJM winter daily average temperature — all stations pooled\nDec–Feb, winters 1995-96 to 2024-25 (n=%d station-days)" % len(tavg))
    ax.set_xlabel("Daily average temperature (°F)")
    ax.set_ylabel("Station-days")
    ax.legend()
    fig.tight_layout(); fig.savefig(os.path.join(BASE, "01_overall_tavg_hist.png")); plt.close(fig)

    # 2. By month
    fig, axes = plt.subplots(1, 2, figsize=(11, 5))
    for m, label, col in [(12, "Dec", "#5b8db2"), (1, "Jan", "#2c6e9b"), (2, "Feb", "#8fb8d8")]:
        sns.histplot(df[df["month"] == m]["tavg_f"], bins=35, kde=True, ax=axes[0], color=col, label=label, alpha=0.45)
    axes[0].set_title("Overlapping histograms by month")
    axes[0].set_xlabel("Daily average temperature (°F)"); axes[0].set_ylabel("Station-days"); axes[0].legend()
    data_m = [df[df["month"] == m]["tavg_f"].dropna().values for m in (12, 1, 2)]
    axes[1].boxplot(data_m, labels=["Dec", "Jan", "Feb"], patch_artist=True)
    axes[1].set_title("Boxplot by month"); axes[1].set_ylabel("Daily average temperature (°F)")
    fig.suptitle("PJM winter daily average temperature by month (Dec–Feb, 1995-96 to 2024-25)")
    fig.tight_layout(); fig.savefig(os.path.join(BASE, "02_by_month.png")); plt.close(fig)

    # 3. Time: decadal distributions + yearly mean with band
    fig, axes = plt.subplots(2, 1, figsize=(10, 8), sharex=False)
    for label, col in [("1996-2005", "#8fb8d8"), ("2006-2015", "#2c6e9b"), ("2016-2025", "#c0392b")]:
        a, b = periods[label]
        sub = df[(df["winter_year"] >= a) & (df["winter_year"] <= b)]["tavg_f"]
        sns.histplot(sub, bins=35, kde=True, ax=axes[0], color=col, label=f"{label} (mean {sub.mean():.1f}°F)", alpha=0.4)
    axes[0].set_title("Distribution shape by period — overlapping histograms + KDE")
    axes[0].set_xlabel("Daily average temperature (°F)"); axes[0].set_ylabel("Station-days"); axes[0].legend()
    axes[1].plot(ydf["winter_year"], ydf["mean_tavg_f"], marker="o", color="#2c6e9b", label="Winter mean Tavg")
    axes[1].fill_between(ydf["winter_year"], ydf["p10_tavg_f"], ydf["p90_tavg_f"], color="#2c6e9b", alpha=0.18, label="10th–90th percentile band")
    # trend line
    tr = summary["trend_winter_mean"]
    xs = ydf["winter_year"].values
    axes[1].plot(xs, np.polyval(np.polyfit(xs, ydf["mean_tavg_f"], 1), xs), color="red", ls="--",
                 label=f"Trend {tr['slope_per_decade']:+.2f}°F/decade")
    axes[1].set_title("Yearly winter mean Tavg with 10th–90th percentile band")
    axes[1].set_xlabel("Winter year (year of Jan/Feb)"); axes[1].set_ylabel("Temperature (°F)"); axes[1].legend()
    fig.suptitle("PJM winter temperature — how the distribution changes over time")
    fig.tight_layout(); fig.savefig(os.path.join(BASE, "03_time_trends.png")); plt.close(fig)

    # 4. Climatology through winter
    fig, ax = plt.subplots(figsize=(10, 5))
    x = np.arange(len(clim))
    ax.fill_between(x, clim["rolling15_p10"], clim["rolling15_p90"], color="#2c6e9b", alpha=0.18, label="10th–90th pct (15-day smoothed)")
    ax.plot(x, clim["rolling15_mean"], color="#2c6e9b", lw=2, label="15-day rolling climatological mean")
    ax.plot(x, clim["mean"], color="gray", lw=0.7, alpha=0.6, label="Daily climatological mean")
    ax.set_xticks([0, 30, 61, 89])
    ax.set_xticklabels(["Dec 1", "Dec 31", "Jan 31", "Feb 28"])
    ax.set_title("Climatological daily mean temperature through a PJM winter\nMean across 30 winters and 7 stations, Dec 1 – Feb 28")
    ax.set_xlabel("Day of winter"); ax.set_ylabel("Daily average temperature (°F)")
    ax.legend(); ax.set_xlim(0, len(clim)-1)
    fig.tight_layout(); fig.savefig(os.path.join(BASE, "04_climatology.png")); plt.close(fig)

    # 5. Range
    fig, axes = plt.subplots(1, 2, figsize=(11, 5))
    sns.histplot(rng, bins=35, kde=True, ax=axes[0], color="#2c6e9b")
    axes[0].axvline(rng.mean(), color="red", ls="--", label=f"Mean {rng.mean():.1f}°F")
    axes[0].set_title("Daily temperature range (Tmax − Tmin)")
    axes[0].set_xlabel("Daily range (°F)"); axes[0].set_ylabel("Station-days"); axes[0].legend()
    rb_df = pd.DataFrame(summary["range_by_tavg_bin"]).T
    axes[1].plot(range(len(rb_df)), rb_df["mean_range_f"].values, marker="o", color="#2c6e9b")
    axes[1].set_xticks(range(len(rb_df))); axes[1].set_xticklabels(rb_df.index, rotation=30)
    axes[1].set_title("Mean daily range vs daily average temperature")
    axes[1].set_xlabel("Daily average temperature bin (°F)"); axes[1].set_ylabel("Mean daily range (°F)")
    for i, v in enumerate(rb_df["mean_range_f"].values):
        axes[1].annotate(f"{v:.1f}", (i, v), textcoords="offset points", xytext=(0, 6), ha="center", fontsize=8)
    fig.suptitle("PJM winter daily temperature range (Dec–Feb, 1995-96 to 2024-25)")
    fig.tight_layout(); fig.savefig(os.path.join(BASE, "05_range.png")); plt.close(fig)

    print("plots done")
    print("climatology:", summary["climatology"])
    print("by_month:", json.dumps(by_month, indent=2))
    print("by_period:", json.dumps(by_period, indent=2))

if __name__ == "__main__":
    main()
