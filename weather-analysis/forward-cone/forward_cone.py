"""
Forward temperature cone for PJM winters — built on the existing cleaned NOAA data.
Basic Python libraries only: pandas / numpy / matplotlib.

Question: as a function of time from Dec 1 to Feb 28, on a given day with
starting temp X, what is the probability cone of forward temps in the next
1..14 days?

Inputs (no re-download):
  ../pjm_winter_daily.csv  (18,956 station-days, 7 stations, Dec-Feb 1995-96..2024-25)
  ../pjm_winter_climatology.csv  (pooled climatological mean by month-day)

Method:
  - Work within each station separately, never cross a winter boundary.
    A forward path starting in Dec/Jan/Feb stays in that same winter_year
    and ends by Feb 28/29 (target date must exist in the same station+winter).
  - Starting Tavg binned: <20, 20-30, 30-40, 40-50, >50 F.
  - Conditioning on calendar: pooled winter first, then by starting month
    Dec / Jan / Feb.
  - For each (bin, month group, horizon h=0..14): n, mean, median, std,
    p10/p25/p75/p90, P(T<20), P(T<32), P(T>50), plus the mean climatological
    temp on the target dates (dashed reference in the fan charts).

Outputs in this directory:
  forward_cone_summary.csv, forward_cone_stats.json, 01..04 PNG charts.
"""
import json
import os

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

BASE = os.path.dirname(os.path.abspath(__file__))
PARENT = os.path.dirname(BASE)

BIN_EDGES = [-1e9, 20, 30, 40, 50, 1e9]
BIN_LABELS = ["<20", "20-30", "30-40", "40-50", ">50"]
MONTH_LABELS = {12: "Dec", 1: "Jan", 2: "Feb"}
HORIZONS = list(range(0, 15))
BLUE = "#2c6e9b"


def bin_label(t):
    if t < 20:
        return "<20"
    if t < 30:
        return "20-30"
    if t < 40:
        return "30-40"
    if t < 50:
        return "40-50"
    return ">50"


def stats_of(vals):
    v = np.asarray(vals, dtype=float)
    v = v[~np.isnan(v)]
    if len(v) == 0:
        return None
    return {
        "n": int(len(v)),
        "mean": float(np.mean(v)),
        "median": float(np.median(v)),
        "std": float(np.std(v, ddof=1)) if len(v) > 1 else 0.0,
        "p10": float(np.quantile(v, 0.10)),
        "p25": float(np.quantile(v, 0.25)),
        "p75": float(np.quantile(v, 0.75)),
        "p90": float(np.quantile(v, 0.90)),
        "p_lt20": float(np.mean(v < 20)),
        "p_lt32": float(np.mean(v < 32)),
        "p_gt50": float(np.mean(v > 50)),
    }


def main():
    df = pd.read_csv(os.path.join(PARENT, "pjm_winter_daily.csv"), parse_dates=["date"])
    df = df.dropna(subset=["tavg_f"]).sort_values(["station", "date"]).reset_index(drop=True)
    print(f"rows: {len(df)}, stations: {df['station'].nunique()}, "
          f"dates {df['date'].min().date()} to {df['date'].max().date()}")

    # Climatology: pooled mean Tavg by month-day
    clim = pd.read_csv(os.path.join(PARENT, "pjm_winter_climatology.csv"), index_col=0)
    clim_mean = {idx: float(row["mean"]) for idx, row in clim.iterrows()}
    overall_clim = float(df["tavg_f"].mean())

    # Lookup (station, date) -> (tavg, winter_year)
    lookup = {}
    for row in df.itertuples(index=False):
        lookup[(row.station, row.date)] = (float(row.tavg_f), int(row.winter_year))

    # Build forward pairs
    records = []
    for row in df.itertuples(index=False):
        station, start_date, wy = row.station, row.date, int(row.winter_year)
        start_t = float(row.tavg_f)
        start_bin = bin_label(start_t)
        start_month = MONTH_LABELS[int(row.month)]
        start_md = start_date.strftime("%m-%d")
        for h in HORIZONS:
            if h == 0:
                fwd_t, fwd_wy = start_t, wy
                fwd_date = start_date
            else:
                fwd_date = start_date + pd.Timedelta(days=h)
                hit = lookup.get((station, fwd_date))
                if hit is None:
                    continue
                fwd_t, fwd_wy = hit
                if fwd_wy != wy:
                    continue
            records.append({
                "station": station, "start_date": start_date, "winter_year": wy,
                "start_month": start_month, "start_tavg": start_t,
                "start_bin": start_bin, "horizon": h, "fwd_tavg": fwd_t,
                "clim_fwd": clim_mean.get(fwd_date.strftime("%m-%d"), np.nan),
            })
    pairs = pd.DataFrame(records)
    print(f"forward pairs (incl. h=0): {len(pairs):,}")
    pairs.to_csv(os.path.join(BASE, "forward_cone_pairs.csv"), index=False)

    # ---- Summary table: one row per (bin, month group, horizon) ----
    rows = []
    month_groups = [("ALL", None), ("Dec", "Dec"), ("Jan", "Jan"), ("Feb", "Feb")]
    bin_groups = BIN_LABELS + ["ALL"]
    for bin_lab in bin_groups:
        sub_bin = pairs if bin_lab == "ALL" else pairs[pairs["start_bin"] == bin_lab]
        for mg_lab, mg_val in month_groups:
            sub = sub_bin if mg_val is None else sub_bin[sub_bin["start_month"] == mg_val]
            if len(sub) == 0:
                continue
            for h in HORIZONS:
                s = sub[sub["horizon"] == h]
                if len(s) == 0:
                    continue
                st = stats_of(s["fwd_tavg"].values)
                rows.append({
                    "start_bin": bin_lab, "start_month": mg_lab, "horizon": h,
                    "n": st["n"],
                    "start_median": float(s["start_tavg"].median()),
                    "start_mean": float(s["start_tavg"].mean()),
                    "clim_mean": float(s["clim_fwd"].mean()),
                    "mean": st["mean"], "median": st["median"], "std": st["std"],
                    "p10": st["p10"], "p25": st["p25"], "p75": st["p75"], "p90": st["p90"],
                    "width_p90_p10": st["p90"] - st["p10"],
                    "width_p75_p25": st["p75"] - st["p25"],
                    "p_lt20": st["p_lt20"], "p_lt32": st["p_lt32"], "p_gt50": st["p_gt50"],
                })
    summ = pd.DataFrame(rows)
    summ.to_csv(os.path.join(BASE, "forward_cone_summary.csv"), index=False)
    print(f"summary rows: {len(summ)}")

    # ---- Persistence / autocorrelation check (within station+winter) ----
    df_sorted = df.sort_values(["station", "winter_year", "date"]).reset_index(drop=True)
    autocorr = {}
    for lag in [1, 2, 3, 7, 14]:
        df_sorted[f"lag{lag}"] = df_sorted.groupby(["station", "winter_year"])["tavg_f"].shift(lag)
        autocorr[f"lag{lag}"] = float(
            df_sorted[["tavg_f", f"lag{lag}"]].corr().iloc[0, 1])
    autocorr_by_month = {}
    for m_lab in ["Dec", "Jan", "Feb"]:
        sub = df_sorted[df_sorted["month"] == {"Dec": 12, "Jan": 1, "Feb": 2}[m_lab]]
        autocorr_by_month[m_lab] = float(sub[["tavg_f", "lag1"]].corr().iloc[0, 1])

    # Cone widths at h=1,3,7,14 by bin (pooled) + median reversion
    widths = {}
    medians = {}
    for bin_lab in BIN_LABELS:
        widths[bin_lab] = {}
        medians[bin_lab] = {}
        for h in [1, 3, 7, 14]:
            r = summ[(summ["start_bin"] == bin_lab) & (summ["start_month"] == "ALL")
                     & (summ["horizon"] == h)].iloc[0]
            widths[bin_lab][f"h{h}"] = float(r["width_p90_p10"])
            medians[bin_lab][f"h{h}"] = float(r["median"])
    start_medians = {b: float(summ[(summ["start_bin"] == b) & (summ["start_month"] == "ALL")
                                   & (summ["horizon"] == 0)]["start_median"].iloc[0])
                     for b in BIN_LABELS}
    n_starts = {b: int(summ[(summ["start_bin"] == b) & (summ["start_month"] == "ALL")
                            & (summ["horizon"] == 0)]["n"].iloc[0]) for b in BIN_LABELS}
    n_starts_month = {}
    for mg in ["Dec", "Jan", "Feb"]:
        n_starts_month[mg] = {b: int(summ[(summ["start_bin"] == b) & (summ["start_month"] == mg)
                                          & (summ["horizon"] == 0)]["n"].iloc[0]) for b in BIN_LABELS}

    # Jan 15 exact-date check (for plot 4 justification)
    jan15 = df[(df["date"].dt.month == 1) & (df["date"].dt.day == 15)]
    jan15_n = {lab: int(((jan15["tavg_f"] >= lo) & (jan15["tavg_f"] < hi)).sum())
               for lab, (lo, hi) in {"~20F": (17.5, 22.5), "~35F": (32.5, 37.5),
                                     "~50F": (47.5, 52.5)}.items()}

    extra = {
        "overall_clim_mean_f": overall_clim,
        "autocorr_lag": autocorr,
        "autocorr_lag1_by_start_month": autocorr_by_month,
        "n_starts_pooled": n_starts,
        "n_starts_by_month": n_starts_month,
        "start_median_by_bin": start_medians,
        "cone_width_p90_p10_pooled": widths,
        "median_forward_pooled": medians,
        "jan15_exact_n_by_target": jan15_n,
        "jan10_20_window_n_by_bin": {
            b: int(((df[(df["date"].dt.month == 1) & (df["date"].dt.day.between(10, 20))]["tavg_f"]
                    .apply(bin_label) == b)).sum()) for b in BIN_LABELS},
    }
    with open(os.path.join(BASE, "forward_cone_stats.json"), "w") as f:
        json.dump(extra, f, indent=2)
    print(json.dumps(extra, indent=2))

    # ---------------- Plots ----------------
    plt.rcParams.update({"figure.dpi": 150, "axes.grid": True, "grid.alpha": 0.3})

    def fan_ax(ax, sub, title, n_label):
        """sub: summary rows for one (bin, month) group, horizons 0..14."""
        sub = sub.sort_values("horizon")
        h = sub["horizon"].values
        ax.fill_between(h, sub["p10"], sub["p90"], color=BLUE, alpha=0.18, label="10th–90th pct")
        ax.fill_between(h, sub["p25"], sub["p75"], color=BLUE, alpha=0.32, label="25th–75th pct")
        ax.plot(h, sub["median"], color=BLUE, lw=2, marker="o", ms=3, label="Median")
        ax.plot(h, sub["clim_mean"], color="darkred", ls="--", lw=1.4, label="Climatology")
        ax.plot([0], [sub.loc[sub["horizon"] == 0, "start_median"].iloc[0]],
                marker="D", color="black", ms=5, zorder=5)
        ax.set_xlim(0, 14)
        ax.set_ylim(0, 70)
        ax.set_xticks(range(0, 15, 2))
        ax.set_title(title, fontsize=10)
        ax.text(0.98, 0.04, n_label, transform=ax.transAxes, ha="right",
                va="bottom", fontsize=8)

    # 1. Fan charts by starting bin, pooled winter (5 panels)
    fig, axes = plt.subplots(5, 1, figsize=(10, 12), sharex=True)
    for ax, bin_lab in zip(axes, BIN_LABELS):
        sub = summ[(summ["start_bin"] == bin_lab) & (summ["start_month"] == "ALL")]
        w14 = sub.loc[sub["horizon"] == 14, "width_p90_p10"].iloc[0]
        fan_ax(ax, sub,
               f"Starting Tavg {bin_lab}°F — pooled winter (start median "
               f"{start_medians[bin_lab]:.1f}°F)",
               f"n starts = {n_starts[bin_lab]:,}  •  p90−p10 at day 14 = {w14:.1f}°F")
        ax.set_ylabel("Forward Tavg (°F)")
    axes[-1].set_xlabel("Days ahead")
    axes[0].legend(loc="upper left", fontsize=8, framealpha=0.9)
    fig.suptitle("PJM winter forward temperature cone — by starting temperature "
                 "(pooled Dec–Feb, 1995-96 to 2024-25)", fontsize=12)
    fig.tight_layout(rect=[0, 0, 1, 0.97])
    fig.savefig(os.path.join(BASE, "01_fan_pooled.png"))
    plt.close(fig)

    # 2. Fan charts split by starting month for key bins
    key_bins = ["<20", "30-40", ">50"]
    fig, axes = plt.subplots(3, 3, figsize=(13, 10), sharex=True, sharey=True)
    for i, bin_lab in enumerate(key_bins):
        for j, mg in enumerate(["Dec", "Jan", "Feb"]):
            ax = axes[i, j]
            sub = summ[(summ["start_bin"] == bin_lab) & (summ["start_month"] == mg)]
            fan_ax(ax, sub, f"{bin_lab}°F start — {mg}",
                   f"n = {n_starts_month[mg][bin_lab]:,}")
            if i == 2:
                ax.set_xlabel("Days ahead")
            if j == 0:
                ax.set_ylabel("Forward Tavg (°F)")
    axes[0, 0].legend(loc="upper left", fontsize=8, framealpha=0.9)
    fig.suptitle("Forward temperature cone by starting month — cold (<20°F), "
                 "mid (30–40°F), warm (>50°F) starts", fontsize=12)
    fig.tight_layout(rect=[0, 0, 1, 0.97])
    fig.savefig(os.path.join(BASE, "02_fan_by_month.png"))
    plt.close(fig)

    # 3. Heatmaps: median forward temp at h=1,3,7,14 + cone width at h=7,14
    months = ["Dec", "Jan", "Feb", "ALL"]
    def mat(col, h):
        return np.array([[float(summ[(summ["start_bin"] == b) & (summ["start_month"] == m)
                                     & (summ["horizon"] == h)][col].iloc[0])
                          for m in months] for b in BIN_LABELS])
    panels = [
        ("Median forward Tavg, day +1", mat("median", 1), "RdYlBu_r", 15, 55, "{:.0f}"),
        ("Median forward Tavg, day +3", mat("median", 3), "RdYlBu_r", 15, 55, "{:.0f}"),
        ("Median forward Tavg, day +7", mat("median", 7), "RdYlBu_r", 15, 55, "{:.0f}"),
        ("Median forward Tavg, day +14", mat("median", 14), "RdYlBu_r", 15, 55, "{:.0f}"),
        ("Cone width p90−p10, day +7", mat("width_p90_p10", 7), "Blues", 10, 40, "{:.0f}"),
        ("Cone width p90−p10, day +14", mat("width_p90_p10", 14), "Blues", 10, 40, "{:.0f}"),
    ]
    fig, axes = plt.subplots(3, 2, figsize=(12, 11))
    for ax, (title, data, cmap, vmin, vmax, fmt) in zip(axes.flat, panels):
        im = ax.imshow(data, cmap=cmap, vmin=vmin, vmax=vmax, aspect="auto")
        ax.set_xticks(range(len(months)))
        ax.set_xticklabels(["Dec", "Jan", "Feb", "Pooled"])
        ax.set_yticks(range(len(BIN_LABELS)))
        ax.set_yticklabels([f"{b}°F" for b in BIN_LABELS])
        ax.set_title(title, fontsize=10)
        for i in range(len(BIN_LABELS)):
            for j in range(len(months)):
                ax.text(j, i, fmt.format(data[i, j]), ha="center", va="center",
                        fontsize=9, color="black" if cmap == "Blues" else "white" if 25 < data[i, j] < 45 else "black")
        fig.colorbar(im, ax=ax, shrink=0.85)
    fig.suptitle("Forward cone at a glance — median forward temp and cone width "
                 "by starting bin and starting month (°F)", fontsize=12)
    fig.tight_layout(rect=[0, 0, 1, 0.97])
    fig.savefig(os.path.join(BASE, "03_heatmap_median_width.png"))
    plt.close(fig)

    # 4. Example cones: starts in the Jan 10–20 window (exact Jan 15 is too thin:
    #    n=18 at ~20°F, n=40 at ~35°F, n=5 at ~50°F)
    jan_pairs = pairs[(pairs["start_month"] == "Jan")
                      & (pairs["start_date"].dt.day.between(10, 20))]
    # Recompute stats for this window from the pairs frame
    fig, axes = plt.subplots(1, 3, figsize=(13, 5), sharey=True)
    for ax, bin_lab in zip(axes, ["<20", "30-40", ">50"]):
        s = jan_pairs[jan_pairs["start_bin"] == bin_lab]
        agg = []
        for h in HORIZONS:
            sh = s[s["horizon"] == h]
            st = stats_of(sh["fwd_tavg"].values)
            agg.append({"horizon": h, "median": st["median"], "p10": st["p10"],
                        "p25": st["p25"], "p75": st["p75"], "p90": st["p90"],
                        "clim_mean": float(sh["clim_fwd"].mean()),
                        "start_median": float(sh["start_tavg"].median()), "n": st["n"]})
        agg = pd.DataFrame(agg)
        fan_ax(ax, agg, f"Jan 10–20 start, {bin_lab}°F",
               f"n starts = {agg.loc[0, 'n']:,}")
        ax.set_xlabel("Days ahead")
    axes[0].set_ylabel("Forward Tavg (°F)")
    axes[0].legend(loc="upper left", fontsize=8, framealpha=0.9)
    fig.suptitle("Example forward cones — starts Jan 10–20 (exact Jan 15 is too thin: "
                 "n=5 for ~50°F starts)", fontsize=11)
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    fig.savefig(os.path.join(BASE, "04_example_jan_window.png"))
    plt.close(fig)

    print("charts done")


if __name__ == "__main__":
    main()
