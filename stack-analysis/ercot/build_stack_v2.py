#!/usr/bin/env python3
"""Build ERCOT capacity stack v2 — EIA + manual corrections.

Mirrors ~/workspace/miso-capacity-stack/build_stack_v2.py: reads the v1
files, verifies v1 reproduces (anchor + v1 changelog), applies manual
corrections, rebuilds the changelog and stack, and writes v2 files
alongside (v1 files are never overwritten).

Corrections (6 named adjustments; see research_log.md for evidence):
  A  EXCLUDE Legend Power Station, TX, gas, 754 MW (Jul 2028) — EIA BA
     code ERCO is an error; Entergy Texas is MISO (PUCT Docket 56693:
     MISO determines Legend's transmission upgrades). The mirror image
     of MISO v2 adjustment C, which added it to MISO.
  B  EXCLUDE Project Matador Gas Plant (PMG), TX, gas, 11,679.3 MW
     (157 units: 1,287.3 MW 2027, 1,560 MW 2028, 8,832 MW Dec 2030) —
     Fermi America HyperGrid, Carson County (Texas
     Panhandle = SPP/Xcel territory, not ERCOT), a behind-the-meter
     private grid for co-located data centres with no ERCOT
     interconnection. 0 MW of grid addition under the standing BTM
     rule; the ERCO BA code is also wrong for the location.
  C  EXCLUDE Project Matador Nuclear, TX, nuclear, 4,468 MW
     (2,234 MW Dec 2031 + 2,234 MW Dec 2032) — same campus as B.
  D  FUEL SWITCH J K Spruce Unit 2, TX, coal->gas, 922.5 MW (Dec 2028):
     CPS Energy board plan (Jan 2023) retires Spruce 1 (already in v1)
     and converts Spruce 2 to gas by 2028; EIA has neither the coal
     retirement nor the gas addition for Unit 2.
  E  FUEL SWITCH / REPOWER Coleto Creek, TX, coal 622.4 MW out +
     gas 630 MW in (Dec 2026): Vistra retires the coal unit by end-2026
     and is repowering the site to gas (~630 MW, under construction,
     completion expected end-2026). EIA has neither side.
  F  ADD Rayburn Energy Station II, TX, gas, 570 MW (Dec 2028):
     finalized Texas Energy Fund loan (PUCT, Jun 4, 2026) to Rayburn
     Country Electric Cooperative; absent from the EIA Planned sheet
     (verified in-file). Month is a placeholder; year per PUCT.

No blanket retirement-delay override is applied (the PJM Jan-2029 coal
override was a PJM-only user scenario). Retirements move only on
plant-specific evidence.
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
# Asserted in main(). Cumulative = -16,323.7 MW.
EXPECTED_FLOW_DELTA = {
    2026: 7.6, 2027: -1287.3, 2028: -1744.0, 2029: 0.0, 2030: -8832.0,
    2031: -2234.0, 2032: -2234.0, 2033: 0.0, 2034: 0.0, 2035: 0.0,
    2036: 0.0,
}

# ---------------- Exclusions (v1 rows removed from the v2 changelog) ----
# (plant_name, expected_mw, change_type, note, source, source_url, confidence)
EXCLUDES = [
    ("Legend Power Station", 754.0, "exclude (BA correction)",
     "EXCLUDE: EIA BA code ERCO is an error. Entergy Texas operates on "
     "the MISO grid; PUCT Docket 56693 states MISO determines Legend's "
     "transmission network upgrades; PUCT approved the plant Sep 11, "
     "2025 for MISO service (Port Arthur, Jefferson Co.). Counted in "
     "MISO v2 instead (adjustment C there).",
     "Entergy; PUCT Docket 56693; Utility Dive",
     "https://www.entergy.com/news/entergy-texas-receives-puct-approval-for-two-power-plants-to-support-southeast-texas-growth",
     "High"),
    ("Project Matador Gas Plant (PMG)", 11679.3, "exclude (BTM)",
     "EXCLUDE (BTM + BA): Fermi America HyperGrid campus, Carson Co. "
     "(Amarillo / Texas Panhandle = SPP territory served by Xcel, not "
     "ERCOT). Company describes a behind-the-meter private grid for "
     "co-located AI data centres with no grid interconnection queue "
     "position; under the standing BTM rule a co-located plant whose "
     "grid connection is entirely accounted for by the load counts as "
     "0 MW of grid addition. 157 EIA units totalling 11,679.3 MW "
     "(1,287.3 MW in 2027, 1,560 MW in 2028, 8,832 MW Dec 2030), "
     "all status P.",
     "Fermi America Q3 2025 shareholder letter (SEC filing); DEPLOY registry",
     "https://www.sec.gov/Archives/edgar/data/2071778/000121390025108289/ea026472101ex99-1_fermi.htm",
     "High"),
    ("Project Matador Nuclear", 4468.0, "exclude (BTM)",
     "EXCLUDE (BTM + BA): four ~1,117 MW AP1000 units at the same "
     "Fermi HyperGrid campus as the Matador gas plant (see PMG note). "
     "Private behind-the-meter grid in SPP territory; not ERCOT "
     "capacity. NRC licensing only; nuclear timeline has slipped per "
     "Nov 2026 reporting.",
     "Fermi America Q3 2025 shareholder letter (SEC filing); DEPLOY registry",
     "https://registry.deploy.report/datacenters/fermi-amarillo-texas",
     "High"),
]

# NEW_ROWS: (plant_name, generator_id, state, county, fuel, mw, year,
#            month, type, note, source, source_url, confidence)
NEW_ROWS = [
    ("J K Spruce", "2", "TX", "Bexar", "Coal", 922.5, 2028, 12,
     "retirement",
     "ADD coal retirement (fuel switch): CPS Energy board plan (Jan "
     "2023) ends coal at Spruce in 2028 — Unit 1 retires (already in "
     "v1, Dec 2028) and Unit 2 converts to gas. EIA nameplate 922.5 MW. "
     "EIA carries no planned retirement for Unit 2.",
     "CPS Energy FY2025 financial statements; Global Energy Monitor",
     "https://www.gem.wiki/Spruce_Unit_2",
     "Medium-High"),
    ("J K Spruce (gas conversion)", "2", "TX", "Bexar", "Natural Gas",
     922.5, 2028, 12, "addition",
     "ADD gas (fuel switch): Spruce Unit 2 converted from coal to gas "
     "in 2028 (see coal retirement). Booked at the EIA coal nameplate; "
     "GEM lists the gas configuration at ~922.6 MW.",
     "CPS Energy FY2025 financial statements; Global Energy Monitor",
     "https://www.gem.wiki/Spruce_Unit_2",
     "Medium-High"),
    ("Coleto Creek", "1", "TX", "Goliad", "Coal", 622.4, 2026, 12,
     "retirement",
     "ADD coal retirement (repower): Vistra retires the Coleto Creek "
     "coal unit by end-2026 (Q2 2026 10-Q) and repowers the site to "
     "gas. EIA nameplate 622.4 MW; EIA carries no planned retirement.",
     "Vistra Sep 29, 2025 release; Vistra Q2 2026 10-Q",
     "http://investor.vistracorp.com/2025-09-29-Vistra-Announces-Plans-to-Build-New-Gas-Fueled-Dispatchable-Power-Units-in-the-Permian-Basin",
     "Medium-High"),
    ("Coleto Creek (gas repower)", "1", "TX", "Goliad", "Natural Gas",
     630.0, 2026, 12, "addition",
     "ADD gas (repower): Vistra is converting Coleto Creek from coal "
     "to gas, restoring ~630 MW of dispatchable generation; conversion "
     "underway, completion expected by end-2026. Booked at Vistra's "
     "~630 MW (GEM lists 600 MW; range noted in research_log.md).",
     "Vistra Sep 29, 2025 release; Power Texas Forward",
     "https://powertexasforward.com/",
     "Medium"),
    ("Rayburn Energy Station II", "1", "TX", "Grayson", "Natural Gas",
     570.0, 2028, 12, "addition",
     "ADD: 570 MW gas plant, Rayburn Country Electric Cooperative, "
     "finalized Texas Energy Fund In-ERCOT loan Jun 4, 2026 ($411m), "
     "operations 2028. Absent from the EIA Planned sheet (verified "
     "in-file: no Rayburn addition). Dec 2028 month is a placeholder; "
     "year per PUCT.",
     "PUCT Texas Energy Fund page (updated Nov 14, 2026)",
     "https://www.puc.texas.gov/industry/electric/business/texas-energy-fund/",
     "Medium"),
]


def main():
    plants = pd.read_csv(BASE / "ercot_capacity_plants.csv")
    stack_v1 = pd.read_csv(BASE / "ercot_capacity_stack.csv")
    chg_v1 = pd.read_csv(BASE / "ercot_capacity_changelog.csv")
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

    adj_rows = []
    # --- exclusions
    for (name, exp_mw, ctype, note, src, url, conf) in EXCLUDES:
        idx = p2.index[p2["plant_name"] == name]
        assert len(idx) > 0, name
        tot = round(float(p2.loc[idx, "mw_nameplate"].sum()), 1)
        assert abs(tot - exp_mw) < 0.05, (name, tot, exp_mw)
        for i in idx:
            p2.loc[i, "v2_type"] = "excluded"
            p2.loc[i, "manual_change"] = True
            p2.loc[i, "manual_change_note"] = note
            orig = p2.loc[i]
            adj_rows.append({
                "plant": name, "unit": str(orig["generator_id"]),
                "state": orig["state"], "region": "ERCOT",
                "fuel": orig["fuel"],
                "v1_mw": float(orig["mw_nameplate"]),
                "v1_date": orig["effective_date"],
                "v2_mw": 0.0, "v2_date": "",
                "change_type": ctype, "reason": note,
                "classification": "manual correction",
                "source": src, "source_url": url, "confidence": conf,
                "source_date": "2026-11-15", "date_accessed": "2026-11-15",
            })
        print(f"  excluded {name}: {len(idx)} units, {tot:,.1f} MW")

    # --- new rows
    spruce_pid = plants.loc[plants["plant_name"] == "J K Spruce",
                            "plant_id"]
    spruce_pid = spruce_pid.iloc[0] if len(spruce_pid) else None
    pid_map = {"J K Spruce": spruce_pid,
               "J K Spruce (gas conversion)": spruce_pid}
    new_df = pd.DataFrame([{
        "plant_name": pn, "plant_id": pid_map.get(pn), "generator_id": gid,
        "state": st, "county": cty, "region": "ERCOT",
        "balancing_authority": "ERCO", "fuel": fu,
        "energy_source_code": "", "prime_mover_code": "", "technology": "",
        "mw_nameplate": mw, "mw_net_summer": np.nan, "type": typ,
        "status": "manual addition (v2)", "retirement_status": "",
        "source_sheet": src, "original_year": yr, "original_month": mo,
        "original_date": f"{yr:04d}-{mo:02d}", "effective_year": yr,
        "effective_month": mo, "effective_date": f"{yr:04d}-{mo:02d}",
        "v2_mw_nameplate": mw, "v2_effective_date": f"{yr:04d}-{mo:02d}",
        "v2_status": "manual addition (v2)", "v2_type": typ,
        "manual_change": True, "manual_change_note": note,
    } for (pn, gid, st, cty, fu, mw, yr, mo, typ, note, src, _u, _c)
        in NEW_ROWS])
    p2 = pd.concat([p2, new_df], ignore_index=True)
    for (pn, gid, st, _cty, fu, mw, yr, mo, typ, note, src, url, conf) \
            in NEW_ROWS:
        if typ == "addition":
            ct = ("add (fuel switch)" if "conversion" in pn or "repower" in pn
                  else "add")
        else:
            ct = "add retirement (fuel switch)"
        adj_rows.append({
            "plant": pn, "unit": str(gid), "state": st, "region": "ERCOT",
            "fuel": fu, "v1_mw": "", "v1_date": "",
            "v2_mw": float(mw), "v2_date": f"{yr:04d}-{mo:02d}",
            "change_type": ct, "reason": note,
            "classification": "manual correction",
            "source": src, "source_url": url, "confidence": conf,
            "source_date": "2026-11-15", "date_accessed": "2026-11-15",
        })
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
        assert abs(d - EXPECTED_FLOW_DELTA[y]) < 0.05, (
            y, d, EXPECTED_FLOW_DELTA[y])
    print("  yearly flow deltas match the expected table: OK "
          f"(cumulative {sum(EXPECTED_FLOW_DELTA.values()):+,.1f} MW)")

    # --- stack v2: trailing unchanged, forward = anchor + cumulative v2
    stack_rows = []
    for y in range(2016, 2026):
        for _, r in stack_v1[stack_v1["year"] == y].iterrows():
            stack_rows.append({"year": int(r["year"]), "fuel": r["fuel"],
                               "mw": float(r["mw"]), "period": "trailing",
                               "anchor_year": bool(r["anchor_year"]),
                               "source_note": r["source_note"]})
    note2 = ("EIA-860M Dec-31-2025 anchor + v2 changelog (EIA-860M + manual "
             "corrections: Legend BA exclusion, Matador BTM exclusions, "
             "Spruce/Coleto Creek fuel switches, Rayburn II addition)")
    running = {f: float(anchor[f]) for f in FUELS}
    for y in range(2026, 2037):
        net = chg2[chg2["year"] == y]
        for f in FUELS:
            running[f] += float(net.loc[net["fuel"] == f, "net_mw"].iloc[0])
        for f in FUELS + ["Total"]:
            v = round(sum(running.values()), 1) if f == "Total" \
                else round(running[f], 1)
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
    adj = pd.DataFrame(adj_rows)
    adj.to_csv(BASE / "manual_adjustments.csv", index=False)
    p2.to_csv(BASE / "ercot_capacity_plants_v2.csv", index=False)
    stack2.to_csv(BASE / "ercot_capacity_stack_v2.csv", index=False)
    chg2.to_csv(BASE / "ercot_capacity_changelog_v2.csv", index=False)

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
        "named_adjustments_count": 6,
        "largest_manual_changes_mw": [
            {"plant": "Project Matador Gas Plant (PMG) BTM exclusion",
             "change": "exclude", "mw": 11679.3},
            {"plant": "Project Matador Nuclear BTM exclusion",
             "change": "exclude", "mw": 4468.0},
            {"plant": "J K Spruce Unit 2 fuel switch (coal->gas)",
             "change": "fuel switch", "mw": 922.5},
            {"plant": "Legend Power Station BA correction exclusion",
             "change": "exclude", "mw": 754.0},
            {"plant": "Coleto Creek repower (coal out 622.4 / gas in 630.0)",
             "change": "fuel switch", "mw": 630.0},
            {"plant": "Rayburn Energy Station II addition",
             "change": "add", "mw": 570.0},
        ],
        "not_added_flagged_candidates_mw": {
            "WattBridge / Continental Resources TxEF loan, West Texas gas (452 MW, loan Oct 7, 2026 — after the EIA vintage; plant/date unverified)": 452.0,
            "Anthropic / Caterpillar behind-the-meter gas generators (1,700 MW equipment deal announced Nov 2026; no single plant or date)": 1700.0,
            "Crusoe / Stargate Abilene on-site gas (~360 MW, operating behind-the-meter, permitted for on-site use only; not in EIA and excluded by the BTM rule)": 360.0,
            "Liberty Thermal + Bullock Gas, Hill County (1,400 MW each, ERCOT queue only, data-centre-linked, 2032)": 2800.0,
            "Vast Sands Power (880 MW, Ward Co., in v1/v2) may be Vistra's 860 MW Permian Basin TxEF project (identity unverified; kept at EIA MW/date)": 880.0,
            "Fermi Matador capacity beyond EIA (company claims ~6 GW air-permitted, up to 11-17 GW campus; unquantified, BTM)": None,
        },
        "files": {
            "manual_adjustments": "manual_adjustments.csv",
            "plants_v2": "ercot_capacity_plants_v2.csv",
            "stack_v2": "ercot_capacity_stack_v2.csv",
            "changelog_v2": "ercot_capacity_changelog_v2.csv",
            "summary_v2": "summary_v2.json",
            "research_log": "research_log.md",
            "readme_v2": "README_v2.md",
            "charts": ["01_stacked_area_v2.png",
                       "02_net_change_forward_v2.png"],
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
    ax.set_title("ERCOT generation capacity stack by fuel, 2016-2036 — v2\n"
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
    ax.set_title("ERCOT annual net capacity change by fuel, forward 2026-2036 — v2\n"
                 "(EIA-860M + manual additions/retirements/exclusions, nameplate)",
                 fontsize=11)
    ax.legend(ncol=2, fontsize=9, loc="upper right")
    ax.grid(True, alpha=0.3, axis="y")
    fig.tight_layout()
    fig.savefig(BASE / "02_net_change_forward_v2.png", dpi=150)
    plt.close(fig)
    print("  charts written")


if __name__ == "__main__":
    w, c2 = main()
    make_charts(w, c2)
