#!/usr/bin/env python3
"""Build CAISO capacity stack v2 — EIA + manual corrections.

Mirrors ~/workspace/miso-capacity-stack/build_stack_v2.py: reads the v1
files, verifies v1 reproduces (anchor + v1 changelog), applies manual
corrections, rebuilds the changelog and stack, and writes v2 files
alongside (v1 files are never overwritten).

Corrections (3 named adjustments, 4 row-level changes; see
research_log.md for the evidence and per-item confidence):
  A  ADD Diablo Canyon Unit 1 retirement, CA, nuclear, 1,159.0 MW (Oct 2029)
     — EIA-860M shows NO planned retirement for Diablo Canyon. SB 846
     (2022) and CPUC Decision 23-12-036 authorise extended operations
     only until Oct 31, 2029 (Unit 1) / Oct 31, 2030 (Unit 2); the CEC's
     July 2026 SB 846 Operations Assessment confirms those dates are the
     current state-law end of operations. The NRC's Apr 2026 20-year
     licence renewal (to 2044/2045) does not change state authorisation;
     no extension bill has been enacted.
  B  ADD Diablo Canyon Unit 2 retirement, CA, nuclear, 1,164.0 MW (Oct 2030)
  C  RETIME Ormond Beach Units 1/2, CA, gas, 2x806.0 MW, Jan 2027 ->
     Dec 2026 — the State Water Board's OTC Policy final compliance date
     for Ormond Beach is Dec 31, 2026 (Aug 15, 2023 amendment, contingent
     on Strategic Reliability Reserve participation); DWR's ESSRRP
     contracts sunset at end-2026 and Nov 2026 reporting confirms all
     three SRR plants (Alamitos, Huntington Beach, Ormond Beach) retire
     Dec 31, 2026. EIA's Jan 2027 is one month late. Alamitos Units 3/4/5
     and Huntington Beach Unit 2 already sit at Dec 2026 in EIA — kept.

No blanket retirement-delay override is applied (the PJM Jan-2029 coal
override was a PJM-only user scenario). Retirements move only on
plant-specific evidence.

Behind-the-meter rule: no co-located data-center generation plant whose
grid connection is entirely accounted for by its load was found in the
CAISO footprint (see research_log.md), so no BTM exclusion is applied.
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
# Asserted in main(). Cumulative = -2,323.0 MW.
EXPECTED_FLOW_DELTA = {
    2026: -1612.0, 2027: 1612.0, 2028: 0.0, 2029: -1159.0, 2030: -1164.0,
    2031: 0.0, 2032: 0.0, 2033: 0.0, 2034: 0.0, 2035: 0.0, 2036: 0.0,
}

# ---------------- Manual corrections ----------------
# EDITS: (plant_name exact, generator_id, new_mw, new_eff (y, mo),
#         new_status, note, source, source_url, confidence)
EDITS = [
    # C. Ormond Beach retime (OTC final compliance Dec 31, 2026)
    ("Ormond Beach", "1", None, (2026, 12), None,
     "Retime Jan 2027 -> Dec 2026: State Water Board OTC Policy final "
     "compliance date for Ormond Beach is Dec 31, 2026 (amendment adopted "
     "Aug 15, 2023, contingent on ESSRRP participation from Jan 1, 2024). "
     "DWR confirmed in Oct/Nov 2026 that the Strategic Reliability Reserve "
     "contracts sunset at end-2026 and the plants retire Dec 31, 2026.",
     "State Water Board SACCWIS Final 2026 Report (Mar 20, 2026); "
     "Enverus CAISO Winter Outlook Nov 5, 2026",
     "https://www.waterboards.ca.gov/water_issues/programs/ocean/cwa316/saccwis/docs/2026/26saccwisrptf.pdf",
     "Medium-High"),
    ("Ormond Beach", "2", None, (2026, 12), None,
     "Retime Jan 2027 -> Dec 2026 (see Unit 1).",
     "State Water Board SACCWIS Final 2026 Report (Mar 20, 2026)",
     "https://www.waterboards.ca.gov/water_issues/programs/ocean/cwa316/saccwis/docs/2026/26saccwisrptf.pdf",
     "Medium-High"),
]

# NEW_ROWS: (plant_name, generator_id, plant_id, state, fuel,
#            mw, year, month, type, status, source_sheet, note,
#            source, source_url, confidence)
NEW_ROWS = [
    # A/B. Diablo Canyon retirements (EIA has no planned retirement)
    ("Diablo Canyon", "1", 6099, "CA", "Nuclear",
     1159.0, 2029, 10, "retirement", "manual addition (v2)",
     "SB 846 (2022); CPUC Decision 23-12-036 (Dec 2023)",
     "ADD retirement: EIA-860M shows no planned retirement for Diablo "
     "Canyon. SB 846 and CPUC D.23-12-036 authorise extended operations "
     "only until Oct 31, 2029 for Unit 1. CEC SB 846 Operations "
     "Assessment, July 2026 update, confirms. NRC renewed the federal "
     "licences in Apr 2026 to Nov 2044, but state authorisation still "
     "ends Oct 2029; extension beyond requires new legislation (none "
     "enacted as of Nov 2026).",
     "CEC Diablo Canyon SB 846 Operations Assessment, 2026 Update "
     "(CEC-700-2026-031, Jul 2026)",
     "https://efiling.energy.ca.gov/GetDocument.aspx?tn=271510&DocumentContentId=109055",
     "High"),
    ("Diablo Canyon", "2", 6099, "CA", "Nuclear",
     1164.0, 2030, 10, "retirement", "manual addition (v2)",
     "SB 846 (2022); CPUC Decision 23-12-036 (Dec 2023)",
     "ADD retirement: Unit 2 authorised only until Oct 31, 2030 "
     "(see Unit 1). NRC federal licence runs to Aug 2045; state "
     "authorisation ends Oct 2030 absent new legislation.",
     "CEC Diablo Canyon SB 846 Operations Assessment, 2026 Update "
     "(CEC-700-2026-031, Jul 2026)",
     "https://efiling.energy.ca.gov/GetDocument.aspx?tn=271510&DocumentContentId=109055",
     "High"),
]


def main():
    plants = pd.read_csv(BASE / "caiso_capacity_plants.csv")
    stack_v1 = pd.read_csv(BASE / "caiso_capacity_stack.csv")
    chg_v1 = pd.read_csv(BASE / "caiso_capacity_changelog.csv")
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
    print(f"  applied {len(EDITS)} edits")

    # New rows
    new_df = pd.DataFrame([{
        "plant_name": pn, "plant_id": pid, "generator_id": gid,
        "state": st, "county": "", "balancing_authority": "CISO",
        "fuel": fu, "energy_source_code": "", "prime_mover_code": "",
        "technology": "", "mw_nameplate": mw, "mw_net_summer": np.nan,
        "type": typ, "status": status, "retirement_status": "",
        "source_sheet": src, "original_year": yr, "original_month": mo,
        "original_date": f"{yr:04d}-{mo:02d}", "effective_year": yr,
        "effective_month": mo, "effective_date": f"{yr:04d}-{mo:02d}",
        "v2_mw_nameplate": mw, "v2_effective_date": f"{yr:04d}-{mo:02d}",
        "v2_status": status, "v2_type": typ, "manual_change": True,
        "manual_change_note": note,
    } for (pn, gid, pid, st, fu, mw, yr, mo, typ, status, src, note,
            _s, _u, _c) in NEW_ROWS])
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
             "corrections: Diablo Canyon retirements added per SB 846 / "
             "CPUC D.23-12-036; Ormond Beach retimed to the Dec 31, 2026 "
             "OTC compliance date)")
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
        adj_rows.append({
            "plant": name, "unit": str(gen), "state": orig["state"],
            "region": "", "fuel": orig["fuel"],
            "v1_mw": float(orig["mw_nameplate"]),
            "v1_date": orig["effective_date"],
            "v2_mw": float(new_mw) if new_mw is not None
                     else float(orig["mw_nameplate"]),
            "v2_date": f"{new_eff[0]:04d}-{new_eff[1]:02d}" if new_eff
                       else orig["effective_date"],
            "change_type": "retime", "reason": note,
            "classification": "manual correction",
            "source": src, "source_url": url, "confidence": conf,
            "source_date": "2026-11-15", "date_accessed": "2026-11-15",
        })
    for (pn, gid, _pid, st, fu, mw, yr, mo, typ, _status, _ss, note,
         s, u, c) in NEW_ROWS:
        adj_rows.append({
            "plant": pn, "unit": str(gid), "state": st, "region": "",
            "fuel": fu, "v1_mw": "", "v1_date": "",
            "v2_mw": float(mw), "v2_date": f"{yr:04d}-{mo:02d}",
            "change_type": "add retirement", "reason": note,
            "classification": "manual correction",
            "source": s, "source_url": u, "confidence": c,
            "source_date": "2026-11-15", "date_accessed": "2026-11-15",
        })
    adj = pd.DataFrame(adj_rows)
    adj.to_csv(BASE / "manual_adjustments.csv", index=False)
    p2.to_csv(BASE / "caiso_capacity_plants_v2.csv", index=False)
    stack2.to_csv(BASE / "caiso_capacity_stack_v2.csv", index=False)
    chg2.to_csv(BASE / "caiso_capacity_changelog_v2.csv", index=False)

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
            {"plant": "Ormond Beach retime 2027->2026", "change": "retime",
             "mw": 1612.0},
            {"plant": "Diablo Canyon Unit 2 retirement (added)",
             "change": "add retirement", "mw": 1164.0},
            {"plant": "Diablo Canyon Unit 1 retirement (added)",
             "change": "add retirement", "mw": 1159.0},
        ],
        "not_added_flagged_candidates_mw": {
            "Diablo Canyon operation to 2044/2045 under NRC renewed licences (requires new state legislation; 2045 coalition campaigning, no bill enacted)": 2323.0,
            "Eagle Mountain Pumped Storage, CA (1,300 MW, FERC-licensed, pre-construction; construction deadline stayed to Jun 2028 start / Jun 2031 completion; CAISO queue withdrawn; no COD or financing)": 1300.0,
            "Chokecherry and Sierra Madre Wind, WY (3,550.5 MW in EIA at Dec 2031-Dec 2033; Global Energy Monitor phases suggest 2029-2031, ~2 years earlier; TransWest Express energisation late 2029; dates kept at EIA, timing risk flagged)": 3550.5,
            "SunZia Wind, NM (EIA codes full 3,650.2 MW to CISO; CAISO 2026 Summer Assessment counts CAISO's share as 3,167 MW — 483.2 MW attribution difference, kept at EIA BA basis)": 483.2,
            "Whale Rock Pumped Storage, CA (600 MW in EIA Planned at Dec 2027, status P — regulatory approvals not initiated; paper project, kept with flag)": 600.0,
        },
        "files": {
            "manual_adjustments": "manual_adjustments.csv",
            "plants_v2": "caiso_capacity_plants_v2.csv",
            "stack_v2": "caiso_capacity_stack_v2.csv",
            "changelog_v2": "caiso_capacity_changelog_v2.csv",
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
    ax.set_title("CAISO generation capacity stack by fuel, 2016-2036 — v2\n"
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
    ax.set_title("CAISO annual net capacity change by fuel, forward 2026-2036 — v2\n"
                 "(EIA-860M + manual additions/retirements, nameplate)", fontsize=11)
    ax.legend(ncol=2, fontsize=9, loc="upper right")
    ax.grid(True, alpha=0.3, axis="y")
    fig.tight_layout()
    fig.savefig(BASE / "02_net_change_forward_v2.png", dpi=150)
    plt.close(fig)
    print("  charts written")


if __name__ == "__main__":
    w, c2 = main()
    make_charts(w, c2)
