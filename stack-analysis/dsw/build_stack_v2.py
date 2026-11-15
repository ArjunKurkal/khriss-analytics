#!/usr/bin/env python3
"""Build DSW capacity stack v2 — EIA + manual corrections.

Mirrors ~/workspace/miso-capacity-stack/build_stack_v2.py: reads the v1
files, verifies v1 reproduces (anchor + v1 changelog), applies manual
corrections, rebuilds the changelog and stack, and writes v2 files
alongside (v1 files are never overwritten).

Corrections (9 named adjustments, 18 row-level changes; see
research_log.md for evidence and per-item confidence):
  A  RETIME Four Corners Units 4/5, NM, coal, 1,636.2 MW,
     Dec 2031 -> Dec 2038 (APS 2026 IRP + NTEC coal-supply agreement;
     2038 is outside the 2026-2036 window, so the retirement leaves
     the v2 changelog)
  B  FUEL SWITCH Coronado CO1/CO2, AZ, coal->gas, 821.8 MW (2029)
  C  FUEL SWITCH Springerville Units 1/2, AZ, coal->gas, 849.6 MW (2030)
  D  FUEL SWITCH Springerville Unit 4, AZ, coal->gas, 458.1 MW (2029)
  E  ADD Springerville Unit 3 retirement, AZ, coal, 458.1 MW (2031)
  F  FUEL SWITCH Apache Station ST3, AZ, coal->gas, 204.0 MW (2027)
  G  ADD Cholla gas repower, AZ, gas, 387.0 MW (2030)
  H  ADD Desert Sun Power Plant, AZ, gas, 1,238.0 MW (2032)
  I  ADD Project Baccara, AZ, gas, 744.0 MW (2028) — co-located with a
     data center but grid-selling / grid-connected, so counted in full
     under the standing behind-the-meter rule (see research_log.md)

Expected yearly FLOW deltas (v2 net changelog - v1 net changelog) are
asserted in main(). Cumulative = +5,218.5 MW.
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
EXPECTED_FLOW_DELTA = {
    2026: 0.0, 2027: 424.8, 2028: 744.0, 2029: 0.0, 2030: 387.0,
    2031: 1178.1, 2032: 2484.6, 2033: 0.0, 2034: 0.0, 2035: 0.0, 2036: 0.0,
}

# EDITS: (plant_name, generator_id, new_mw, new_eff (y, mo), new_status,
#         note, source, source_url, confidence)
EDITS = [
    ("Four Corners", "4", None, (2038, 12), None,
     "Retime Dec 2031 -> Dec 2038: APS announced Oct 2026 it will operate "
     "Four Corners beyond 2031; NTEC coal-supply agreement signed Sep 2026 "
     "enables operation through 2038; APS 2026 IRP (filed Nov 2026) base "
     "case is 'FC Extended to 2038'. 2038 is outside the stack window, so "
     "the retirement leaves the 2026-2036 changelog. Other owners "
     "(PNM/TEP/SRP) still plan 2031 exits from their shares, but EIA "
     "reports the full plant at its location and APS is the operator.",
     "APS announcement Oct 2, 2026; APS 2026 IRP via Utility Dive Nov 4, 2026",
     "https://www.utilitydive.com/news/aps-sales-double-by-2041-proposes-extending-coal-use-to-2038/873648/",
     "Medium-High"),
    ("Four Corners", "5", None, (2038, 12), None,
     "Retime Dec 2031 -> Dec 2038 (see Unit 4).",
     "APS announcement Oct 2, 2026; APS 2026 IRP via Utility Dive",
     "https://www.utilitydive.com/news/aps-sales-double-by-2041-proposes-extending-coal-use-to-2038/873648/",
     "Medium-High"),
    ("Coronado", "CO1", None, (2029, 12), None,
     "Fuel switch coal->gas: SRP Board approved Jun 24, 2025 converting "
     "both Coronado units to gas, expected complete late 2029 (was a "
     "Dec 2032 coal retirement in EIA). Gas additions are NEW_ROWS.",
     "SRP Board Jun 2025; Global Energy Monitor; Sierra Club ACC comments Jul 2, 2026",
     "https://www.gem.wiki/Coronado_Generating_Station",
     "Medium-High"),
    ("Coronado", "CO2", None, (2029, 12), None,
     "Fuel switch coal->gas: Unit 2 converts by late 2029 (see CO1).",
     "SRP Board Jun 2025; Global Energy Monitor",
     "https://www.gem.wiki/Coronado_Generating_Station",
     "Medium-High"),
    ("Springerville", "1", None, (2030, 12), None,
     "Fuel switch coal->gas: TEP announced Jul 29, 2025 converting "
     "Springerville Units 1 and 2 to gas by 2030; ACC approved the CEC "
     "amendment Mar 2026 (was a Dec 2027 coal retirement in EIA). "
     "Gas additions are NEW_ROWS.",
     "TEP Jul 2025; ACC Decision (CEC amendment, Feb 5, 2026 staff filing)",
     "http://docket.images.azcc.gov/E000049241.pdf?i=1771641153246",
     "Medium-High"),
    ("Springerville", "2", None, (2030, 12), None,
     "Fuel switch coal->gas: Unit 2 converts by 2030 (see Unit 1; was "
     "Dec 2032 in EIA).",
     "TEP Jul 2025; ACC CEC amendment",
     "http://docket.images.azcc.gov/E000049241.pdf?i=1771641153246",
     "Medium-High"),
]

# NEW_ROWS: (plant_name, generator_id, plant_id, state, fuel, mw, year,
#            month, type, status, source_sheet, note, source,
#            source_url, confidence)
NEW_ROWS = [
    ("Coronado (gas conversion)", "CO1", 6177, "AZ", "Natural Gas",
     410.9, 2029, 12, "addition", "manual addition (v2)",
     "SRP Board approval Jun 24, 2025 (fuel switch)",
     "ADD gas: Coronado Unit 1 converted to gas, complete late 2029.",
     "SRP Board Jun 2025; Global Energy Monitor",
     "https://www.gem.wiki/Coronado_Generating_Station", "Medium-High"),
    ("Coronado (gas conversion)", "CO2", 6177, "AZ", "Natural Gas",
     410.9, 2029, 12, "addition", "manual addition (v2)",
     "SRP Board approval Jun 24, 2025 (fuel switch)",
     "ADD gas: Coronado Unit 2 converted to gas, complete late 2029.",
     "SRP Board Jun 2025; Global Energy Monitor",
     "https://www.gem.wiki/Coronado_Generating_Station", "Medium-High"),
    ("Springerville (gas conversion)", "1", 8223, "AZ", "Natural Gas",
     424.8, 2030, 12, "addition", "manual addition (v2)",
     "TEP conversion plan; ACC CEC amendment Mar 2026",
     "ADD gas: Springerville Unit 1 converted to gas by 2030.",
     "TEP Jul 2025; ACC CEC amendment",
     "http://docket.images.azcc.gov/E000049241.pdf?i=1771641153246",
     "Medium-High"),
    ("Springerville (gas conversion)", "2", 8223, "AZ", "Natural Gas",
     424.8, 2030, 12, "addition", "manual addition (v2)",
     "TEP conversion plan; ACC CEC amendment Mar 2026",
     "ADD gas: Springerville Unit 2 converted to gas by 2030.",
     "TEP Jul 2025; ACC CEC amendment",
     "http://docket.images.azcc.gov/E000049241.pdf?i=1771641153246",
     "Medium-High"),
    ("Springerville", "4", 8223, "AZ", "Coal",
     458.1, 2029, 12, "retirement", "manual addition (v2)",
     "SRP Board vote Nov 2025 (fuel switch)",
     "ADD coal retirement: SRP (Unit 4 owner) board voted Nov 2025 to "
     "convert Unit 4 from coal to gas by 2029. EIA has no planned "
     "retirement for Unit 4.",
     "SRP Board Nov 2025; Sierra Club ACC comments Jul 2, 2026",
     "https://docket.images.azcc.gov/E000052876.pdf?i=1784141247161",
     "Medium"),
    ("Springerville (gas conversion)", "4", 8223, "AZ", "Natural Gas",
     458.1, 2029, 12, "addition", "manual addition (v2)",
     "SRP Board vote Nov 2025 (fuel switch)",
     "ADD gas: Springerville Unit 4 converted to gas by 2029.",
     "SRP Board Nov 2025; Sierra Club ACC comments Jul 2, 2026",
     "https://docket.images.azcc.gov/E000052876.pdf?i=1784141247161",
     "Medium"),
    ("Springerville", "3", 8223, "AZ", "Coal",
     458.1, 2031, 12, "retirement", "manual addition (v2)",
     "Tri-State announcement Dec 2023",
     "ADD retirement: Tri-State G&T (Unit 3 owner) announced Dec 2023 "
     "that Unit 3 retires in 2031, replaced with renewables. EIA has no "
     "planned retirement for Unit 3.",
     "Tri-State Dec 2023; Global Energy Monitor",
     "https://Www.gem.wiki/Springerville_Generating_Station", "Medium"),
    ("Apache Station", "ST3", 160, "AZ", "Coal",
     204.0, 2027, 12, "retirement", "manual addition (v2)",
     "AEPCO Sep 2024 commitment (fuel switch)",
     "ADD coal retirement: AEPCO announced Sep 2024 it will stop burning "
     "coal at Apache ST3 by end-2027 and transition the unit to gas. "
     "FLAG: Jun 2026 DOE allocated $20.8m to modernize the coal unit, "
     "which could extend coal life; AEPCO has not confirmed a change "
     "and remains bound by USDA New ERA grant obligations (coal-free, "
     "-70% emissions by 2031). EIA has no planned retirement for ST3.",
     "AEPCO Sep 2024; Global Energy Monitor; State Affairs Jun 2026",
     "https://www.gem.wiki/Apache_Generating_Station", "Low-Medium"),
    ("Apache Station (gas conversion)", "ST3", 160, "AZ", "Natural Gas",
     204.0, 2027, 12, "addition", "manual addition (v2)",
     "AEPCO Sep 2024 commitment (fuel switch)",
     "ADD gas: Apache ST3 transitions to gas by end-2027 (see coal row).",
     "AEPCO Sep 2024; Global Energy Monitor",
     "https://www.gem.wiki/Apache_Generating_Station", "Low-Medium"),
    ("Cholla (gas repower)", "1", 113, "AZ", "Natural Gas",
     387.0, 2030, 12, "addition", "manual addition (v2)",
     "APS 2026 IRP preferred plan (filed Nov 2026)",
     "ADD: APS repowers the retired Cholla site (Units 1 and 3) to gas "
     "as a 387 MW facility by 2030, per the APS 2026 IRP. The Jul 2026 "
     "announcement said ~380 MW with in-service 2029; the IRP figure/"
     "date is used as the latest filed plan. Cholla coal retired "
     "Mar 2025 and is correctly out of the anchor.",
     "APS 2026 IRP via Utility Dive Nov 4, 2026; ACC Jul 2, 2026",
     "https://www.utilitydive.com/news/aps-sales-double-by-2041-proposes-extending-coal-use-to-2038/873648/",
     "Medium"),
    ("Desert Sun Power Plant", "1", None, "AZ", "Natural Gas",
     1238.0, 2032, 12, "addition", "manual addition (v2)",
     "APS 2026 IRP preferred plan (filed Nov 2026)",
     "ADD: 1,238 MW combined-cycle facility at Gila Bend in 2032 to "
     "serve large-customer subscription load, per APS 2026 IRP. Site "
     "was announced Oct 30, 2025 as up to 2,000 MW in two phases "
     "(Phase 1 late 2030); APS's 2025 All-Source RFP describes ~1,660 MW "
     "at the site and the May 2026 Title V permit application describes "
     "2x 7HA.02 1x1 CC at 530 MW unfired / 630 MW duct-fired each. The "
     "IRP's 1,238 MW / 2032 is the filed preferred-plan figure used "
     "here. Utility grid plant (subscription is a financing model; the "
     "plant interconnects to the APS grid) — NOT behind-the-meter, "
     "counted in full. Distinct from Copia Power's Saddleback "
     "Generation Station (1,250 MW, Maricopa/Tonopah, in EIA v1).",
     "APS 2026 IRP via Utility Dive Nov 4, 2026; APS newsroom Oct 30, 2025",
     "https://newsroom.aps.com/aps-uses-growth-pays-for-growth-model-to-develop-new-natural-gas-plant/",
     "Medium"),
    ("Project Baccara", "1", None, "AZ", "Natural Gas",
     744.0, 2028, 6, "addition", "manual addition (v2)",
     "Maricopa County air permit applications 2026; ACC CEC Feb 2026",
     "ADD: 744 MW gas plant (Takanock / Montera) co-located with the "
     "Project Eagle data center in Glendale/Waddell, AZ. BTM ANALYSIS: "
     "NOT excluded under the standing rule — Baccara will sell power to "
     "the grid / local electrical district and connect to an APS "
     "substation (by 2030); the data center is initially served by an "
     "interim utility (grid) connection. The grid connection is not "
     "entirely accounted for by the co-located load, and the generation "
     "is independently grid-connected, so it counts in full. Counter-"
     "consideration: Maricopa County initially treated plant + data "
     "center as a single emissions source because the plant exists "
     "mostly to serve the data center initially. Jun 2028 is a "
     "placeholder (construction from 2026; first data center early "
     "2028). Not in EIA Planned.",
     "Arizona Republic Oct 30, 2026",
     "https://www.azcentral.com/story/news/environment/2026/10/30/how-az-data-center-project-could-alter-air-pollution-rules/92270770007/",
     "Low-Medium"),
]


def main():
    plants = pd.read_csv(BASE / "dsw_capacity_plants.csv")
    stack_v1 = pd.read_csv(BASE / "dsw_capacity_stack.csv")
    chg_v1 = pd.read_csv(BASE / "dsw_capacity_changelog.csv")
    with open(BASE / "summary.json") as f:
        s1 = json.load(f)

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

    for (name, gen, new_mw, new_eff, new_status, note, _s, _u, _c) in EDITS:
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

    new_df = pd.DataFrame([{
        "plant_name": pn, "plant_id": pid, "generator_id": gid,
        "state": st, "county": "", "region": "DSW",
        "balancing_authority": "", "fuel": fu,
        "energy_source_code": "", "prime_mover_code": "", "technology": "",
        "mw_nameplate": mw, "mw_net_summer": np.nan, "type": typ,
        "status": status, "retirement_status": "",
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

    stack_rows = []
    for y in range(2016, 2026):
        for _, r in stack_v1[stack_v1["year"] == y].iterrows():
            stack_rows.append({"year": int(r["year"]), "fuel": r["fuel"],
                               "mw": float(r["mw"]), "period": "trailing",
                               "anchor_year": bool(r["anchor_year"]),
                               "source_note": r["source_note"]})
    note2 = ("EIA-860M Dec-31-2025 anchor + v2 changelog (EIA-860M + manual "
             "corrections: Four Corners extension, Coronado/Springerville/"
             "Apache fuel switches, Springerville 3 retirement, Cholla "
             "repower, Desert Sun, Project Baccara)")
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

    adj_rows = []
    for (name, gen, new_mw, new_eff, _ns, note, src, url, conf) in EDITS:
        orig = plants[(plants["plant_name"] == name)
                      & (plants["generator_id"].astype(str) == str(gen))].iloc[0]
        adj_rows.append({
            "plant": name, "unit": str(gen), "state": orig["state"],
            "region": "DSW", "fuel": orig["fuel"],
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
        if typ == "addition":
            ct = ("add (fuel switch)" if "gas conversion" in pn or "gas repower" in pn
                  else "add")
        else:
            ct = ("add retirement (fuel switch)" if pn in
                  ("Springerville", "Apache Station") else "add retirement")
        adj_rows.append({
            "plant": pn, "unit": str(gid), "state": st, "region": "DSW",
            "fuel": fu, "v1_mw": "", "v1_date": "",
            "v2_mw": float(mw), "v2_date": f"{yr:04d}-{mo:02d}",
            "change_type": ct, "reason": note,
            "classification": "manual correction",
            "source": s, "source_url": u, "confidence": c,
            "source_date": "2026-11-15", "date_accessed": "2026-11-15",
        })
    adj = pd.DataFrame(adj_rows)
    adj.to_csv(BASE / "manual_adjustments.csv", index=False)
    p2.to_csv(BASE / "dsw_capacity_plants_v2.csv", index=False)
    stack2.to_csv(BASE / "dsw_capacity_stack_v2.csv", index=False)
    chg2.to_csv(BASE / "dsw_capacity_changelog_v2.csv", index=False)

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
        "named_adjustments_count": 9,
        "largest_manual_changes_mw": [
            {"plant": "Four Corners retime 2031->2038", "change": "retime (out of window)", "mw": 1636.2},
            {"plant": "Desert Sun Power Plant (new gas)", "change": "add", "mw": 1238.0},
            {"plant": "Springerville Units 1+2 fuel switch (coal->gas)", "change": "fuel switch", "mw": 849.6},
            {"plant": "Coronado fuel switch (coal->gas)", "change": "fuel switch", "mw": 821.8},
            {"plant": "Project Baccara (new gas, co-located data center)", "change": "add", "mw": 744.0},
            {"plant": "Springerville Unit 4 fuel switch (coal->gas)", "change": "fuel switch", "mw": 458.1},
            {"plant": "Springerville Unit 3 retirement", "change": "add retirement", "mw": 458.1},
            {"plant": "Cholla gas repower", "change": "add", "mw": 387.0},
            {"plant": "Apache Station ST3 fuel switch (coal->gas)", "change": "fuel switch", "mw": 204.0},
        ],
        "not_added_flagged_candidates_mw": {
            "APS IRP generic CTs/uprates 2026-2030 (partly already in EIA as Red Hawk/Coolidge expansions; adding would double-count)": 1107.0,
            "Desert Sun site capacity beyond IRP 1,238 MW (site up to 2,000 MW; Phase 2 undated)": 762.0,
            "TEP 2026 IRP new gas by 2041 (no named plant/date)": 300.0,
            "Palo Verde uprate studied in ANL/INL report (~100 MW case; APS says most uprates already completed; no proposal)": 100.0,
            "Four Corners CCS retrofit (NTEC FEED study; DOE funding cancelled Oct 2025)": None,
            "SpaceX/Tombstone 6 GW Cochise County data-center campus (load only, no generation, unapproved Nov 2026)": None,
        },
        "files": {
            "manual_adjustments": "manual_adjustments.csv",
            "plants_v2": "dsw_capacity_plants_v2.csv",
            "stack_v2": "dsw_capacity_stack_v2.csv",
            "changelog_v2": "dsw_capacity_changelog_v2.csv",
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
    import sys
    sys.path.insert(0, str(BASE))
    import importlib.util
    spec = importlib.util.spec_from_file_location("bs", BASE / "build_stack.py")
    bs = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(bs)
    bs.make_charts(wide.rename(columns={c: c for c in wide.columns}),
                   chg2, suffix="_v2")
    print("  charts written")


if __name__ == "__main__":
    w, c2 = main()
    # Build wide frame in build_stack format for charting
    import pandas as pd
    stack2 = pd.read_csv(BASE / "dsw_capacity_stack_v2.csv")
    wide = stack2.pivot(index="year", columns="fuel", values="mw").reset_index()
    chg2 = pd.read_csv(BASE / "dsw_capacity_changelog_v2.csv")
    import importlib.util
    spec = importlib.util.spec_from_file_location("bs", BASE / "build_stack.py")
    bs = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(bs)
    bs.make_charts(wide, chg2, suffix="_v2")
