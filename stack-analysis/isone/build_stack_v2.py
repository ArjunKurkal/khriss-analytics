#!/usr/bin/env python3
"""Build ISO-NE capacity stack v2 — EIA + manual corrections.

Mirrors ~/workspace/miso-capacity-stack/build_stack_v2.py: reads the v1
files, verifies v1 reproduces (anchor + v1 changelog), applies manual
corrections, rebuilds the changelog and stack, and writes v2 files
alongside (v1 files are never overwritten).

Corrections (2 named adjustments, 3 row-level changes; see
research_log.md for the evidence and per-item confidence):
  A  RETIME Merrimack Units 1/2, NH, coal, 459.2 MW: EIA planned
     retirements Dec 2027 / May 2028 -> Sep 2026 (booked). The plant —
     New England's last coal plant — actually ceased operations on
     Sep 12, 2025, ahead of its 2028 settlement deadline. Because v2
     never restates the EIA anchor (MISO/PJM convention), the retirement
     is booked in Sep 2026, the first forward year; on a true
     Dec-31-2025 basis the anchor's coal (and total) is overstated by
     459.2 MW. Timing-only within the window: the 2036 total is
     unaffected by this item.
  B  RESIZE Revolution Wind, RI, wind, 715.0 -> 704.0 MW (date unchanged,
     Nov 2026). EIA's Planned sheet carries 715 MW; the project is
     65 x ~10.8 MW = 704 MW and reached full operation on Nov 5, 2026
     (Orsted), after two federal stop-work orders (Aug 22 and Dec 22,
     2025) were both enjoined by federal courts (Sep 22, 2025 and
     Jan 12, 2026).

No blanket retirement-delay override is applied. No behind-the-meter
exclusion was found among the forward plants: every large forward
project is grid-connected; the one data-center-adjacent item (a 350 MW
load study at the retired Merrimack site) is a load, not generation.
Checked-but-not-added items (Middletown ~767.9 MW, Millstone Unit 2
licence expiry 2035, Form Energy Lincoln 85 MW, SouthCoast Wind,
New England Wind) are logged in research_log.md and summary_v2.json as
flagged candidates — never silently dropped.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

BASE = Path(__file__).resolve().parent
ANCHOR_YEAR = 2025
FUELS = ["Coal", "Natural Gas", "Nuclear", "Hydro", "Pumped Storage",
         "Wind", "Solar", "Oil", "Battery Storage", "Other"]
STACK_ORDER = ["Coal", "Natural Gas", "Nuclear", "Hydro", "Pumped Storage",
               "Oil", "Wind", "Solar", "Battery Storage", "Other"]
FUEL_COLORS = {
    "Coal": "#3b3b3b", "Natural Gas": "#d95f02", "Nuclear": "#7570b3",
    "Hydro": "#1b9e77", "Pumped Storage": "#66a61e", "Wind": "#377eb8",
    "Solar": "#e6ab02", "Oil": "#a6761d", "Battery Storage": "#e7298a",
    "Other": "#999999",
}

# Expected yearly FLOW deltas (v2 net changelog - v1 net changelog), MW.
# 2026: Merrimack retirement pulled in (-459.2) + Revolution resize (-11.0).
# 2027/2028: Merrimack retirements moved out (+113.6 / +345.6).
# Cumulative = -11.0 MW (the 2036 v2-v1 difference).
EXPECTED_FLOW_DELTA = {
    2026: -470.2, 2027: 113.6, 2028: 345.6, 2029: 0.0, 2030: 0.0,
    2031: 0.0, 2032: 0.0, 2033: 0.0, 2034: 0.0, 2035: 0.0, 2036: 0.0,
}

# EDITS: (plant_name exact, generator_id, new_mw, new_eff (y, mo),
#         new_status, note, source, source_url, confidence)
EDITS = [
    ("Merrimack", "1", None, (2026, 9), None,
     "Retime Dec 2027 -> Sep 2026 (booked): Merrimack Station ceased "
     "operations Sep 12, 2025 — New England's last coal plant closed "
     "ahead of its Jun 2028 EPA/CLF/Sierra Club settlement deadline. "
     "EIA-860M Sep 2026 still lists Unit 1 as operating with a Dec 2027 "
     "planned retirement — stale. Booked in the first forward year "
     "because v2 does not restate the EIA anchor; the anchor overstates "
     "true Dec-31-2025 coal by 459.2 MW (both units).",
     "WAMC / Northeast Public Radio, Nov 19, 2025; Global Energy Monitor",
     "https://www.wamc.org/show/earth-wise/2025-11-19/the-last-coal-power-in-new-england",
     "High"),
    ("Merrimack", "2", None, (2026, 9), None,
     "Retime May 2028 -> Sep 2026 (booked). See Unit 1. EIA lists Unit 2 "
     "as (OS) out of service with a May 2028 planned retirement.",
     "WAMC / Northeast Public Radio, Nov 19, 2025; Global Energy Monitor",
     "https://www.gem.wiki/Merrimack_Station",
     "High"),
    ("Revolution Wind", "REVWD", 704.0, None, None,
     "Resize 715.0 -> 704.0 MW (date unchanged, Nov 2026): the project "
     "is 65 Siemens Gamesa turbines totalling 704 MW (400 MW RI + 304 MW "
     "CT) and reached full operation Nov 5, 2026 (Orsted). It survived "
     "two BOEM stop-work orders (Aug 22, 2025 and Dec 22, 2025), both "
     "enjoined (Sep 22, 2025; Jan 12, 2026). First power Mar 14, 2026; "
     "final turbine installed Sep 18, 2026. A federal remand request on "
     "the 2023 COP approval (filed Oct 9, 2026) remains pending — noted, "
     "not treated as a cancellation.",
     "Providence Journal, Nov 5, 2026; Nature World News, Nov 10, 2026",
     "https://www.providencejournal.com/story/news/local/rhode-island/2026/11/05/revolution-wind-targeted-by-trump-is-now-complete-and-selling-power-to-utilities/92615688007/",
     "High"),
]
NEW_ROWS = []


def main():
    plants = pd.read_csv(BASE / "isone_capacity_plants.csv")
    stack_v1 = pd.read_csv(BASE / "isone_capacity_stack.csv")
    chg_v1 = pd.read_csv(BASE / "isone_capacity_changelog.csv")
    with open(BASE / "summary.json") as f:
        s1 = json.load(f)

    # --- sanity check: v1 stack == anchor + cumulative v1 changelog
    anchor = stack_v1[stack_v1["year"] == ANCHOR_YEAR].set_index("fuel")["mw"].to_dict()
    running = {f: float(anchor[f]) for f in FUELS}
    for y in range(2026, 2037):
        net = chg_v1[chg_v1["year"] == y]
        for f in FUELS:
            running[f] += float(net.loc[net["fuel"] == f, "net_mw"].iloc[0])
        v1row = stack_v1[stack_v1["year"] == y]
        for f in FUELS:
            v = float(v1row.loc[v1row["fuel"] == f, "mw"].iloc[0])
            assert abs(v - running[f]) < 0.05, (y, f, v, running[f])
    print("v1 stack reproduces from anchor + v1 changelog: OK")

    # --- plants v2
    p2 = plants.copy()
    p2["v2_mw_nameplate"] = p2["mw_nameplate"]
    p2["v2_effective_date"] = p2["effective_date"]
    p2["v2_status"] = p2["status"]
    p2["v2_type"] = p2["type"]
    p2["manual_change"] = False
    p2["manual_change_note"] = ""

    def find_rows(name, gen):
        m = (p2["plant_name"] == name)
        if gen is not None:
            m = m & (p2["generator_id"].astype(str) == str(gen))
        return p2.index[m]

    for (name, gen, new_mw, new_eff, new_status, note, _src, _url,
         _conf) in EDITS:
        idx = find_rows(name, gen)
        assert len(idx) == 1, (name, gen, len(idx))
        i = idx[0]
        if new_mw is not None:
            p2.loc[i, "v2_mw_nameplate"] = new_mw
        if new_eff is not None:
            y, mo = new_eff
            p2.loc[i, "v2_effective_date"] = f"{y:04d}-{mo:02d}"
        if new_status is not None:
            p2.loc[i, "v2_status"] = new_status
        p2.loc[i, "manual_change"] = True
        p2.loc[i, "manual_change_note"] = note
    print(f"  applied {len(EDITS)} edits, {len(NEW_ROWS)} new rows")
    print(f"  plants v2 rows: {len(p2)} (v1 {len(plants)})")

    # --- changelog v2
    act = p2[p2["v2_type"].isin(["addition", "retirement"])].copy()
    act["v2_year"] = act["v2_effective_date"].str.slice(0, 4).astype(int)
    act = act[(act["v2_year"] >= 2026) & (act["v2_year"] <= 2036)]
    rows = []
    for y in range(2026, 2037):
        for f in FUELS:
            sub = act[(act["v2_year"] == y) & (act["fuel"] == f)]
            adds = sub[sub["v2_type"] == "addition"]
            rets = sub[sub["v2_type"] == "retirement"]
            rows.append({
                "year": y, "fuel": f,
                "additions_mw": round(float(adds["v2_mw_nameplate"].sum()), 1),
                "additions_count": int(len(adds)),
                "retirements_mw": round(float(rets["v2_mw_nameplate"].sum()), 1),
                "retirements_count": int(len(rets)),
                "net_mw": round(float(adds["v2_mw_nameplate"].sum()
                                - rets["v2_mw_nameplate"].sum()), 1),
            })
    chg2 = pd.DataFrame(rows)

    for y in range(2026, 2037):
        d = round(float(chg2[chg2["year"] == y]["net_mw"].sum()
                        - chg_v1[chg_v1["year"] == y]["net_mw"].sum()), 1)
        assert abs(d - EXPECTED_FLOW_DELTA[y]) < 0.05, (y, d, EXPECTED_FLOW_DELTA[y])
    print("  yearly flow deltas match the expected table: OK "
          f"(cumulative {sum(EXPECTED_FLOW_DELTA.values()):+,.1f} MW)")

    # --- stack v2: trailing unchanged, forward = anchor + cumulative v2 changelog
    stack_rows = []
    for y in range(2016, 2026):
        for _, r in stack_v1[stack_v1["year"] == y].iterrows():
            stack_rows.append({"year": int(r["year"]), "fuel": r["fuel"],
                               "mw": float(r["mw"]), "period": "trailing",
                               "anchor_year": bool(r["anchor_year"]),
                               "source_note": r["source_note"]})
    note2 = ("EIA-860M Dec-31-2025 anchor + v2 changelog (EIA-860M + manual "
             "corrections: Merrimack coal retime to Sep 2026 booked; "
             "Revolution Wind resized 715 -> 704 MW)")
    running = {f: float(anchor[f]) for f in FUELS}
    for y in range(2026, 2037):
        net = chg2[chg2["year"] == y]
        for f in FUELS:
            running[f] += float(net.loc[net["fuel"] == f, "net_mw"].iloc[0])
        for f in FUELS + ["Total"]:
            v = round(sum(running.values()), 1) if f == "Total" else round(running[f], 1)
            stack_rows.append({"year": y, "fuel": f, "mw": v,
                               "period": "forward", "anchor_year": False,
                               "source_note": note2})
    stack2 = pd.DataFrame(stack_rows)
    tot2 = stack2[stack2["fuel"] == "Total"].set_index("year")["mw"].round(1).to_dict()
    tot1 = stack_v1[stack_v1["fuel"] == "Total"].set_index("year")["mw"].round(1).to_dict()
    print("  yearly totals v1 -> v2:")
    for y in range(2025, 2037):
        print(f"    {y}: {tot1[y]:,.1f} -> {tot2[y]:,.1f}  ({tot2[y]-tot1[y]:+,.1f})")

    # --- write outputs
    adj_rows = []
    for (name, gen, new_mw, new_eff, _ns, note, src, url, conf) in EDITS:
        orig = plants[(plants["plant_name"] == name)
                      & (plants["generator_id"].astype(str) == str(gen))].iloc[0]
        ct = "resize" if new_mw is not None and new_eff is None else "retime"
        adj_rows.append({
            "plant": name, "unit": str(gen), "state": orig["state"],
            "region": orig["region"], "fuel": orig["fuel"],
            "v1_mw": float(orig["mw_nameplate"]),
            "v1_date": orig["effective_date"],
            "v2_mw": float(new_mw) if new_mw is not None
                     else float(orig["mw_nameplate"]),
            "v2_date": f"{new_eff[0]:04d}-{new_eff[1]:02d}" if new_eff
                       else orig["effective_date"],
            "change_type": ct, "reason": note,
            "classification": "manual correction",
            "source": src, "source_url": url, "confidence": conf,
            "source_date": "2026-11-15", "date_accessed": "2026-11-15",
        })
    adj = pd.DataFrame(adj_rows)
    adj.to_csv(BASE / "manual_adjustments.csv", index=False)
    p2.to_csv(BASE / "isone_capacity_plants_v2.csv", index=False)
    stack2.to_csv(BASE / "isone_capacity_stack_v2.csv", index=False)
    chg2.to_csv(BASE / "isone_capacity_changelog_v2.csv", index=False)

    def agg(df, col):
        return {f: round(float(df[df["fuel"] == f][col].sum()), 1)
                for f in FUELS}
    v1_add = agg(chg_v1, "additions_mw"); v2_add = agg(chg2, "additions_mw")
    v1_ret = agg(chg_v1, "retirements_mw"); v2_ret = agg(chg2, "retirements_mw")
    summary = {
        "version": "v2",
        "built": "2026-11-15",
        "anchor_unchanged_mw": s1["anchor"]["total_mw"],
        "anchor_source": s1["anchor"]["basis"],
        "anchor_caveat_merrimack": "The EIA anchor includes Merrimack coal "
            "(459.2 MW) at Dec 31, 2025, but the plant actually ceased "
            "operations Sep 12, 2025. On a true Dec-31-2025 basis the anchor "
            "total is 37,778.9 MW and coal is 0.0 MW. v2 keeps the EIA anchor "
            "(build convention) and books the retirement in Sep 2026.",
        "v1_forward_2026_2036": {
            "additions_mw": round(float(chg_v1["additions_mw"].sum()), 1),
            "additions_count": int(chg_v1["additions_count"].sum()),
            "retirements_mw": round(float(chg_v1["retirements_mw"].sum()), 1),
            "retirements_count": int(chg_v1["retirements_count"].sum()),
            "net_mw": round(float(chg_v1["net_mw"].sum()), 1),
            "additions_by_fuel_mw": v1_add, "retirements_by_fuel_mw": v1_ret,
        },
        "v2_forward_2026_2036": {
            "additions_mw": round(float(chg2["additions_mw"].sum()), 1),
            "additions_count": int(chg2["additions_count"].sum()),
            "retirements_mw": round(float(chg2["retirements_mw"].sum()), 1),
            "retirements_count": int(chg2["retirements_count"].sum()),
            "net_mw": round(float(chg2["net_mw"].sum()), 1),
            "additions_by_fuel_mw": v2_add, "retirements_by_fuel_mw": v2_ret,
        },
        "delta_v2_minus_v1_mw": {
            "additions": round(float(chg2["additions_mw"].sum()
                                   - chg_v1["additions_mw"].sum()), 1),
            "retirements": round(float(chg2["retirements_mw"].sum()
                                     - chg_v1["retirements_mw"].sum()), 1),
            "net": round(float(chg2["net_mw"].sum()
                             - chg_v1["net_mw"].sum()), 1),
            "by_fuel_net_mw": {f: round(v2_add[f] - v2_ret[f]
                                       - (v1_add[f] - v1_ret[f]), 1)
                               for f in FUELS},
        },
        "yearly_totals_mw": {"v1": {str(k): v for k, v in tot1.items()},
                             "v2": {str(k): v for k, v in tot2.items()}},
        "manual_adjustments_count": len(adj_rows),
        "named_adjustments_count": 2,
        "largest_manual_changes_mw": [
            {"plant": "Merrimack Units 1+2 retime 2027/2028->2026 (actual closure Sep 2025)",
             "change": "retime", "mw": 459.2},
            {"plant": "Revolution Wind resize 715->704 MW",
             "change": "resize", "mw": 11.0},
        ],
        "not_added_flagged_candidates_mw": {
            "Middletown Units 2/3/4 (CT, oil/gas steam, EIA status OS 'not expected to return'; NEPGA lists ~750 MW closure by mid-2028; no owner/ISO deactivation filing found)": 767.9,
            "Millstone Unit 2 licence expiry Jul 2035 (Dominion intends subsequent renewal to 2055; retirement risk flagged by Dominion itself if no post-2029 contract; CT zero-carbon procurement pending)": 909.9,
            "Form Energy Lincoln, ME iron-air battery (85 MW / 8,500 MWh, DOE-backed; construction starts 2028, no in-service date; not in EIA-860M)": 85.0,
            "SouthCoast Wind (offshore MA, ~2,400 MW; COP remanded Nov 4, 2025; developer paused Apr 2026; no signed contract; not in EIA-860M)": 2400.0,
            "New England Wind 1+2 (offshore MA, Avangrid; COP remand sought by DOI; contracts unsigned; not in EIA-860M)": None,
            "Merrimack site redevelopment (Granite Shore 'renewable energy park': ~100 MW solar + battery storage announced Oct 2025; MW/date unverified; plus a 350 MW data-center load viability study — a load, not generation)": 100.0,
            "Sunrise Wind (924 MW, under construction) — delivers to NYISO (Long Island), not ISO-NE; excluded by balancing authority, listed here so it is not mistaken for an omission": 924.0,
            "South Fork Wind (132 MW, operating since Mar 2024) — delivers to NYISO (East Hampton, NY); EIA codes it BA=NYIS; correctly excluded": 132.0,
        },
        "files": {
            "manual_adjustments": "manual_adjustments.csv",
            "plants_v2": "isone_capacity_plants_v2.csv",
            "stack_v2": "isone_capacity_stack_v2.csv",
            "changelog_v2": "isone_capacity_changelog_v2.csv",
            "summary_v2": "summary_v2.json",
            "research_log": "research_log.md",
            "readme_v2": "README_v2.md",
            "charts": ["01_stacked_area_v2.png", "02_net_change_forward_v2.png"],
        },
    }
    with open(BASE / "summary_v2.json", "w") as f:
        json.dump(summary, f, indent=2)
    print("  wrote manual_adjustments.csv, plants/changelog/stack v2 CSVs, summary_v2.json")

    wide = stack2.pivot(index="year", columns="fuel", values="mw").reset_index()
    return wide, chg2


def make_charts(wide, chg2):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    years = wide["year"].values
    fig, ax = plt.subplots(figsize=(12, 6.5))
    bottom = np.zeros(len(years))
    for f in STACK_ORDER:
        vals = wide[f].values / 1000.0
        ax.fill_between(years, bottom, bottom + vals,
                        label=f, color=FUEL_COLORS[f], alpha=0.9)
        bottom += vals
    ax.axvline(2025.9, color="black", linestyle="--", linewidth=1.5)
    ax.text(2025.95, bottom.max() * 0.97, "Today (Nov 2026)\nanchor Dec 31, 2025",
            fontsize=9, va="top")
    ax.set_xlim(2016, 2036)
    ax.set_ylabel("Installed capacity (GW)")
    ax.set_xlabel("Year (Dec 31 position; 2026-2036 = anchor + v2 changelog)")
    ax.set_title("ISO-NE generation capacity stack by fuel, 2016-2036 — v2\n"
                 "EIA-860M anchor + changelog + manual corrections (nameplate)",
                 fontsize=11)
    ax.legend(ncol=2, fontsize=9, loc="upper left")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(BASE / "01_stacked_area_v2.png", dpi=150)
    plt.close(fig)

    fwd = chg2[chg2["year"] >= 2026]
    piv = fwd.pivot(index="year", columns="fuel", values="net_mw") / 1000.0
    piv = piv.reindex(columns=STACK_ORDER).fillna(0.0)
    fig, ax = plt.subplots(figsize=(12, 6))
    bottom = np.zeros(len(piv))
    top = np.zeros(len(piv))
    for f in STACK_ORDER:
        v = piv[f].values
        pos = np.where(v > 0, v, 0)
        neg = np.where(v < 0, v, 0)
        ax.bar(piv.index, pos, bottom=top, label=f, color=FUEL_COLORS[f], width=0.75)
        top += pos
        ax.bar(piv.index, neg, bottom=bottom, color=FUEL_COLORS[f], width=0.75)
        bottom += neg
    ax.axhline(0, color="black", linewidth=0.8)
    pos_tot = float(piv.clip(lower=0).sum(axis=1).max())
    neg_tot = float(piv.clip(upper=0).sum(axis=1).min())
    ax.set_ylim(neg_tot * 1.12 - 0.2, pos_tot * 1.08 + 0.3)
    ax.set_ylabel("Net capacity change (GW / year)")
    ax.set_xlabel("Year")
    ax.set_title("ISO-NE annual net capacity change by fuel, forward 2026-2036 — v2\n"
                 "(EIA-860M + manual corrections, nameplate)", fontsize=11)
    ax.legend(ncol=2, fontsize=9, loc="upper right")
    ax.grid(True, alpha=0.3, axis="y")
    fig.tight_layout()
    fig.savefig(BASE / "02_net_change_forward_v2.png", dpi=150)
    plt.close(fig)
    print("  charts written")


if __name__ == "__main__":
    w, c2 = main()
    make_charts(w, c2)
