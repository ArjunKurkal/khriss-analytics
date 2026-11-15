#!/usr/bin/env python3
"""Build NYISO capacity stack v2 — EIA + manual corrections.

Mirrors ~/workspace/miso-capacity-stack/build_stack_v2.py: reads the v1
files, verifies v1 reproduces (anchor + v1 changelog), applies manual
corrections, rebuilds the changelog and stack, and writes v2 files
alongside (v1 files are never overwritten).

Corrections (3 named plant adjustments, 36 row-level changes; see
research_log.md for the evidence and per-item confidence). All three
are retirements that EIA-860M misses entirely: EIA carries NO planned
retirement for any of these units, so v1 forward retirements total
only 41.6 MW. No blanket retirement-delay override is applied (the PJM
Jan-2029 coal override was a PJM-only user scenario); every date below
rests on plant-specific NYISO/DEC evidence.
  A  ADD Danskammer Units 1-4 retirement, NY, gas, 532.0 MW (Jan 2027)
     — deactivation notice for Aug 1, 2026; NYISO Q1/Q2 2026 STARs
     required retention until at least Jan 15, 2027; Q3 2026 STAR
     (Oct 13, 2026) found the Lower Hudson Valley need no longer
     observed once CHPE demonstrated capability, withdrew the solution
     solicitation, and cleared Danskammer 1-4 to proceed with
     deactivation. Booked Jan 2027, the earliest date consistent with
     the retention floor. Exact deactivation date not yet published.
  B  ADD Gowanus Barges 2 & 3 retirement, NY, gas, 320.0 MW (May 2029)
     — 16 simple-cycle turbines (GT21-GT28, GT31-GT38, 20 MW each).
     DEC Peaker Rule (6 NYCRR Subpart 227-3) non-compliant peakers;
     NYISO designated them needed for reliability and on Apr 15, 2026
     extended the designation to May 1, 2029, the maximum extension
     the Peaker Rule allows; AlphaGen withdrew its deactivation
     notices Apr 16, 2026 to operate in the market until then. May 2029
     is the regulatory end of that extension.
  C  ADD Narrows Barges 1 & 2 retirement, NY, gas, 352.0 MW (May 2029)
     — 16 simple-cycle turbines (NT11-NT28, 22 MW each). Same
     determination as B. B + C together are NYISO's "608 MW" — that is
     their combined summer capability (608.7 MW); nameplate is
     672.0 MW, the basis of this stack.

Checked and KEPT at EIA values (detail in research_log.md): Empire
Wind 1 (810 MW, Sep 2027) and Sunrise Wind (924 MW, Oct 2027) — both
hit by the Apr 2025 and Dec 22, 2025 federal stop-work actions, both
cleared by federal-court injunctions (Empire Jan 15, 2026; Sunrise
Feb 2, 2026), construction resumed, and EIA's 2027 dates still match
developer/NYISO guidance; South Fork Wind (130.0 MW EIA nameplate,
publicly 132 MW) is already operating and in the anchor; the four
upstate nuclear units (no early retirement — Ginna and Nine Mile
Point 1 filed subsequent licence renewal to 2049 in 2026; no uprate
with a published MW/date); Mineral Basin Solar (401.6 MW, PA) and
Moonlight Flats Solar (250.0 MW, PA) — both verified as genuine NYISO
interconnections (NYSEG 345 kV Line 47), not BA-code errors; Cider
Solar, Alle-Catt Wind, Excelsior, and the largest battery projects
(NISA 300 MW, NY2 151.5 MW).
Excluded as TRANSMISSION, not generation: Champlain Hudson Power
Express (1,250 MW, in commercial operation May 13, 2026) and Clean
Path NY (1,300 MW line; Tier 4 contract terminated 2024).
Behind-the-meter scan: the only genuine co-located generation found
is the existing Greenidge/Vulcan Dresden plant (112.0 MW nameplate,
NYISO-approved BTM load up to 64 MW) — an anchor plant, not a forward
addition, and it exports to the grid under a NYISO operating
agreement, so the standing BTM zero-MW test (grid connection entirely
accounted for by the load) is not met and no exclusion is applied.
No forward co-located data-center generation was found.
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
# Asserted in main(). Cumulative = -1,204.0 MW.
EXPECTED_FLOW_DELTA = {
    2026: 0.0, 2027: -532.0, 2028: 0.0, 2029: -672.0, 2030: 0.0,
    2031: 0.0, 2032: 0.0, 2033: 0.0, 2034: 0.0, 2035: 0.0, 2036: 0.0,
}

DANSKAMMER_NOTE = (
    "ADD retirement: deactivation noticed for Aug 1, 2026; NYISO Q1/Q2 2026 "
    "STARs barred deactivation before Jan 15, 2027 (Interim Service Provider "
    "from Aug 1, 2026); Q3 2026 STAR (Oct 13, 2026) found the Lower Hudson "
    "Valley need no longer observed with CHPE demonstrated, withdrew the "
    "solution solicitation, and cleared Danskammer 1-4 to proceed. Booked "
    "Jan 2027 (earliest date consistent with the retention floor); exact "
    "deactivation date not yet published. EIA carries no planned retirement "
    "for this unit. Units 5-6 (2x2.7 MW oil standby) are not in the notice.")
DANSKAMMER_SRC = "NYISO Short-Term Reliability Process Report Apr 15, 2026; NYISO 2026 Q2/Q3 STARs"
DANSKAMMER_URL = "https://www.nyiso.com/documents/20142/15930753/2025-Q3-Short-Term-Reliability-Process-Report-Final.pdf"
BARGE_NOTE_G = (
    "ADD retirement: DEC Peaker Rule (6 NYCRR 227-3) simple-cycle unit. "
    "NYISO designated Gowanus 2&3 and Narrows 1&2 needed for reliability; "
    "Apr 15, 2026 NYISO extended the designation to May 1, 2029, the maximum "
    "extension the Peaker Rule allows, and AlphaGen withdrew its deactivation "
    "notices Apr 16, 2026 to operate in the market until then. Booked May 2029 "
    "(end of the maximum extension). EIA carries no planned retirement. "
    "NYISO's 608 MW figure for the four barges is summer capability "
    "(608.7 MW); this stack uses nameplate.")
BARGE_NOTE_N = BARGE_NOTE_G.replace("Gowanus 2&3 and Narrows 1&2",
                                    "Gowanus 2&3 and Narrows 1&2")
BARGE_SRC = "NYISO Short-Term Reliability Process Report Apr 15, 2026 (2025 Q3 STAR)"
BARGE_URL = DANSKAMMER_URL

# NEW_ROWS: (plant_name, generator_id, plant_id, state, fuel,
#            mw, year, month, note, source, source_url, confidence)
NEW_ROWS = []
for _gen, _mw in [("1", 72.0), ("2", 73.5), ("3", 147.1), ("4", 239.4)]:
    NEW_ROWS.append(("Danskammer Generating Station", _gen, 2480, "NY",
                     "Natural Gas", _mw, 2027, 1, DANSKAMMER_NOTE,
                     DANSKAMMER_SRC, DANSKAMMER_URL, "Medium"))
for _gen in ["GT21", "GT22", "GT23", "GT24", "GT25", "GT26", "GT27", "GT28",
             "GT31", "GT32", "GT33", "GT34", "GT35", "GT36", "GT37", "GT38"]:
    NEW_ROWS.append(("Gowanus Gas Turbines Generating", _gen, 2494, "NY",
                     "Natural Gas", 20.0, 2029, 5, BARGE_NOTE_G,
                     BARGE_SRC, BARGE_URL, "Medium-High"))
for _gen in ["NT11", "NT12", "NT13", "NT14", "NT15", "NT16", "NT17", "NT18",
             "NT21", "NT22", "NT23", "NT24", "NT25", "NT26", "NT27", "NT28"]:
    NEW_ROWS.append(("Narrows Gas Turbines Generating", _gen, 2499, "NY",
                     "Natural Gas", 22.0, 2029, 5, BARGE_NOTE_N,
                     BARGE_SRC, BARGE_URL, "Medium-High"))


def main():
    plants = pd.read_csv(BASE / "nyiso_capacity_plants.csv")
    stack_v1 = pd.read_csv(BASE / "nyiso_capacity_stack.csv")
    chg_v1 = pd.read_csv(BASE / "nyiso_capacity_changelog.csv")
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

    # --- plants v2: copy v1, add v2 columns
    p2 = plants.copy()
    p2["v2_mw_nameplate"] = p2["mw_nameplate"]
    p2["v2_effective_date"] = p2["effective_date"]
    p2["v2_status"] = p2["status"]
    p2["v2_type"] = p2["type"]
    p2["manual_change"] = False
    p2["manual_change_note"] = ""

    # New rows (added retirements of anchor units absent from v1 plants)
    new_df = pd.DataFrame([{
        "plant_name": pn, "plant_id": pid, "generator_id": gid,
        "state": st, "county": "", "region": "NYISO",
        "balancing_authority": "NYIS", "fuel": fu,
        "energy_source_code": "", "prime_mover_code": "", "technology": "",
        "mw_nameplate": mw, "mw_net_summer": np.nan, "type": "retirement",
        "status": "manual addition (v2)", "retirement_status": "",
        "source_sheet": src, "original_year": yr, "original_month": mo,
        "original_date": f"{yr:04d}-{mo:02d}", "effective_year": yr,
        "effective_month": mo, "effective_date": f"{yr:04d}-{mo:02d}",
        "v2_mw_nameplate": mw, "v2_effective_date": f"{yr:04d}-{mo:02d}",
        "v2_status": "manual addition (v2)", "v2_type": "retirement",
        "manual_change": True, "manual_change_note": note,
    } for (pn, gid, pid, st, fu, mw, yr, mo, note, src, url, conf) in NEW_ROWS])
    p2 = pd.concat([p2, new_df], ignore_index=True)
    print(f"  plants v2 rows: {len(p2)} (v1 {len(plants)} + {len(new_df)} new)")

    # --- changelog v2 from plants v2 (effective years 2026-2036)
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

    # --- assert the expected yearly flow deltas (v2 - v1)
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
             "corrections: Danskammer 1-4 retirement Jan 2027; Gowanus "
             "Barges 2&3 and Narrows Barges 1&2 retirements May 2029 under "
             "the DEC Peaker Rule maximum extension)")
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
    for (pn, gid, _pid, st, fu, mw, yr, mo, note, s, u, c) in NEW_ROWS:
        adj_rows.append({
            "plant": pn, "unit": str(gid), "state": st, "region": "NYISO",
            "fuel": fu, "v1_mw": "", "v1_date": "",
            "v2_mw": float(mw), "v2_date": f"{yr:04d}-{mo:02d}",
            "change_type": "add retirement", "reason": note,
            "classification": "manual correction",
            "source": s, "source_url": u, "confidence": c,
            "source_date": "2026-11-15", "date_accessed": "2026-11-15",
        })
    adj = pd.DataFrame(adj_rows)
    adj.to_csv(BASE / "manual_adjustments.csv", index=False)
    p2.to_csv(BASE / "nyiso_capacity_plants_v2.csv", index=False)
    stack2.to_csv(BASE / "nyiso_capacity_stack_v2.csv", index=False)
    chg2.to_csv(BASE / "nyiso_capacity_changelog_v2.csv", index=False)

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
        "named_adjustments_count": 3,
        "largest_manual_changes_mw": [
            {"plant": "Gowanus Barges 2&3 + Narrows Barges 1&2 retirement (May 2029)",
             "change": "add retirement", "mw": 672.0},
            {"plant": "Danskammer Units 1-4 retirement (Jan 2027)",
             "change": "add retirement", "mw": 532.0},
            {"plant": "Gowanus Barges 2&3 retirement (May 2029)",
             "change": "add retirement", "mw": 320.0},
            {"plant": "Narrows Barges 1&2 retirement (May 2029)",
             "change": "add retirement", "mw": 352.0},
        ],
        "not_added_flagged_candidates_mw": {
            "Gowanus/Narrows repowering, 3 new barges (AlphaGen RFI response; conceptual, earliest mid-2031, no regulatory filing)": 819.0,
            "NYPA advanced nuclear, 1 GW directed Jun 2025 (no site, design or date; master plan due Dec 2026)": 1000.0,
            "East River ESS battery, Astoria, 100 MW (PSC CPCN + ConEd ESSA; NOT in EIA Planned sheet; construction unverified)": 100.0,
            "Luyster Creek storage at Astoria Generating (AlphaGen proposal 126 MW; PSC filing 135 MW; not in EIA Planned)": 126.0,
            "AlphaGen Gowanus-site battery (proposal only)": 150.0,
            "Pinelawn Power deactivation, Long Island (ISP status ended May 15, 2026; outcome unresolved in sources)": 82.0,
            "Glenwood Landing GT4/GT5 retirements listed in NYISO 2026 Q4 STAR assumptions (Jun 2027, for assessment)": 106.0,
            "Port Jefferson GT2/GT3 retirements listed in NYISO 2026 Q4 STAR assumptions (for assessment)": 106.0,
            "Hell Gate Unit 2 (NYPA) IIFO Oct 1, 2026 (Q4 STAR assumptions; small, status code ambiguous)": 47.0,
            "FitzPatrick nuclear licence expires Oct 2034, inside the window (no retirement booked; subsequent renewal not yet filed, deadline Oct 2029)": 883.3,
            "Gowanus Barges 1&4 oil turbines, all out-of-service (320.0 MW nameplate kept in stack; formal status unclear)": 320.0,
        },
        "files": {
            "manual_adjustments": "manual_adjustments.csv",
            "plants_v2": "nyiso_capacity_plants_v2.csv",
            "stack_v2": "nyiso_capacity_stack_v2.csv",
            "changelog_v2": "nyiso_capacity_changelog_v2.csv",
            "summary_v2": "summary_v2.json",
            "research_log": "research_log.md",
            "readme_v2": "README_v2.md",
            "charts": ["01_stacked_area_v2.png", "02_net_change_forward_v2.png"],
        },
    }
    with open(BASE / "summary_v2.json", "w") as f:
        json.dump(summary, f, indent=2)
    print("  wrote manual_adjustments.csv, plants/changelog/stack v2 CSVs, "
          "summary_v2.json")

    # Wide frame for charts.
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
    ax.set_title("NYISO generation capacity stack by fuel, 2016-2036 — v2\n"
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
    ax.set_title("NYISO annual net capacity change by fuel, forward 2026-2036 — v2\n"
                 "(EIA-860M + manual retirements, nameplate)", fontsize=11)
    ax.legend(ncol=2, fontsize=9, loc="upper right")
    ax.grid(True, alpha=0.3, axis="y")
    fig.tight_layout()
    fig.savefig(BASE / "02_net_change_forward_v2.png", dpi=150)
    plt.close(fig)
    print("  charts written")


if __name__ == "__main__":
    w, c2 = main()
    make_charts(w, c2)
