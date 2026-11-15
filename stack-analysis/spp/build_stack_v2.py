#!/usr/bin/env python3
"""Build SPP capacity stack v2 — EIA + manual corrections.

Mirrors ~/workspace/miso-capacity-stack/build_stack_v2.py: reads the v1
files, verifies v1 reproduces (anchor + v1 changelog, Combined and by
East/West), applies manual corrections, rebuilds the changelog and
stack, and writes v2 files alongside (v1 files are never overwritten).

Corrections (5 named adjustments, 10 row-level changes; see
research_log.md for the evidence and per-item confidence):
  A  ADD Gaines County CTG, TX, East, gas, 1,160 MW (Dec 2028) —
     SPS self-build project in NMPRC Case 25-00066-UT, approved by
     NMPRC and PUCT in 2026; NOT in the EIA Planned sheet. MW is the
     filing's winter-max figure (see research log basis note).
  B  ADD Tolk Station CTG, TX, East, gas, 928 MW (Apr 2029) — same
     SPS case and approvals; NOT in EIA Planned. Winter-max basis.
  C  RETIME Craig (CO) Unit 3, West, coal, 534.8 MW,
     Dec 2029 -> Jan 2028 (Tri-State ERP: Units 2 and 3 retire in
     2028; DOE Order 202-25-14B states the same. EIA's Unit 2 date,
     Sep 2028, already matches and is kept.)
  D  RETIME Tolk Units 1/2, East, coal, 2x567.9 MW,
     Dec 2028 -> Mar 2029 (NMPRC approved the 3-month delay in
     May 2026; PUCT decisions followed in Oct 2026.)
  E  RETIME Rawhide new gas units G/H/LM3/LM4/LM5, West, gas,
     5x44.6 MW, Mar 2028 -> Dec 2029 (Platte River's Jul 2026 update
     to owner communities puts the ~200 MW aeroderivative turbines
     in 2029, the Rawhide coal retirement year; month placeholder.)

Expected yearly FLOW deltas (v2 net changelog - v1 net changelog):
  2028: +1,538.0  (Gaines +1,160.0; Tolk coal out of 2028 +1,135.8;
                   Craig 3 into 2028 -534.8; Rawhide GT out -223.0)
  2029:   +550.0  (Tolk CT +928.0; Craig 3 out of 2029 +534.8;
                   Rawhide GT into 2029 +223.0; Tolk coal in -1,135.8)
  all other years 0. Cumulative 2036 effect +2,088.0 MW (the two SPS
  gas additions; the three retimes net to zero). Asserted in main().

Checked and KEPT with sources (no row change; see research_log.md):
Craig Unit 1 Dec 2026 (DOE order chain 202-25-14 -> 202-26-49 runs
through Dec 25, 2026 — EIA's date is consistent); Bison Generation
Station 1,518 MW EIA nameplate 2029/2030 (Basin nominal 1,470 MW);
Evergy Viola/McNew 765 MW each (KCC-approved; 705 MW nominal);
Horizon/Williams Creek 480 MW nameplate (CSU nominal 400 MW at
altitude; site relocated in 2026, delay risk flagged); Rawhide coal
Dec 2029; Comanche (CO) Unit 3 Dec 2030; Ray D Nixon Dec 2029.
No behind-the-meter exclusion was found in either BAA.
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
REGIONS = ["East", "West"]
FUEL_COLORS = {
    "Coal": "#3b3b3b", "Natural Gas": "#d95f02", "Nuclear": "#7570b3",
    "Hydro": "#1b9e77", "Pumped Storage": "#66a61e", "Wind": "#377eb8",
    "Solar": "#e6ab02", "Oil": "#a6761d", "Battery Storage": "#e7298a",
    "Other": "#999999",
}
REGION_COLORS = {"East": "#377eb8", "West": "#d95f02"}

EXPECTED_FLOW_DELTA = {
    2026: 0.0, 2027: 0.0, 2028: 1538.0, 2029: 550.0, 2030: 0.0,
    2031: 0.0, 2032: 0.0, 2033: 0.0, 2034: 0.0, 2035: 0.0, 2036: 0.0,
}

# EDITS: (plant_name exact, generator_id, new_mw, new_eff (y, mo),
#         new_status, note, source, source_url, confidence)
EDITS = [
    # C. Craig Unit 3 retime
    ("Craig (CO)", "3", None, (2028, 1), None,
     "Retime Dec 2029 -> Jan 2028: Tri-State's Dec 2023 Electric "
     "Resource Plan retires Craig Units 2 and 3 in 2028 (Unit 3 in "
     "January 2028, Unit 2 in September 2028), reaffirmed Apr 2025; "
     "DOE Order No. 202-25-14B (Jun 24, 2026) likewise states Units 2 "
     "and 3 'are slated to retire in 2028'. EIA's Dec 2029 is stale; "
     "EIA's Unit 2 date (Sep 2028) already matches and is kept.",
     "DOE Order No. 202-25-14B; Global Energy Monitor (Tri-State ERP)",
     "https://www.energy.gov/documents/order-addressing-arguments-raised-rehearing-202-25-14b",
     "Medium-High"),
    # D. Tolk retime
    ("Tolk", "1", None, (2029, 3), None,
     "Retime Dec 2028 -> Mar 2029: NMPRC approved SPS's request in "
     "May 2026 to delay Tolk's coal retirement to March 2029 (a "
     "three-month extension, through Mar 31, 2029, sought in Case "
     "25-00066-UT); PUCT approvals followed in Oct 2026.",
     "Global Energy Monitor (NMPRC May 2026); SPS Case 25-00066-UT testimony",
     "https://www.gem.wiki/Tolk_Station",
     "High"),
    ("Tolk", "2", None, (2029, 3), None,
     "Retime Dec 2028 -> Mar 2029 (see Unit 1).",
     "Global Energy Monitor (NMPRC May 2026)",
     "https://www.gem.wiki/Tolk_Station",
     "High"),
    # E. Rawhide new gas retime (5 units)
    ("Rawhide", "G", None, (2029, 12), None,
     "Retime Mar 2028 -> Dec 2029 (month placeholder; year per "
     "source): Platte River's Jul 28, 2026 update to owner "
     "communities schedules '200 MW aeroderivative turbines' in "
     "2029, alongside the Rawhide Unit 1 coal retirement. EIA's "
     "Mar 2028 reflects the older IRP schedule.",
     "City of Longmont council communication, Jul 28, 2026 (PRPA update)",
     "https://longmont.primegov.com/api/compilemeetingattachmenthistory/historyattachment/?historyId=a5615ea6-b3ae-44cf-9b36-963e0fe79269",
     "Medium"),
    ("Rawhide", "H", None, (2029, 12), None,
     "Retime Mar 2028 -> Dec 2029 (see unit G).",
     "City of Longmont council communication, Jul 28, 2026 (PRPA update)",
     "https://longmont.primegov.com/api/compilemeetingattachmenthistory/historyattachment/?historyId=a5615ea6-b3ae-44cf-9b36-963e0fe79269",
     "Medium"),
    ("Rawhide", "LM3", None, (2029, 12), None,
     "Retime Mar 2028 -> Dec 2029 (see unit G).",
     "City of Longmont council communication, Jul 28, 2026 (PRPA update)",
     "https://longmont.primegov.com/api/compilemeetingattachmenthistory/historyattachment/?historyId=a5615ea6-b3ae-44cf-9b36-963e0fe79269",
     "Medium"),
    ("Rawhide", "LM4", None, (2029, 12), None,
     "Retime Mar 2028 -> Dec 2029 (see unit G).",
     "City of Longmont council communication, Jul 28, 2026 (PRPA update)",
     "https://longmont.primegov.com/api/compilemeetingattachmenthistory/historyattachment/?historyId=a5615ea6-b3ae-44cf-9b36-963e0fe79269",
     "Medium"),
    ("Rawhide", "LM5", None, (2029, 12), None,
     "Retime Mar 2028 -> Dec 2029 (see unit G).",
     "City of Longmont council communication, Jul 28, 2026 (PRPA update)",
     "https://longmont.primegov.com/api/compilemeetingattachmenthistory/historyattachment/?historyId=a5615ea6-b3ae-44cf-9b36-963e0fe79269",
     "Medium"),
]

# NEW_ROWS: (plant_name, generator_id, plant_id, state, region,
#            fuel, mw, year, month, type, status, source_sheet, note,
#            source, source_url, confidence)
NEW_ROWS = [
    # A. Gaines County CTG (not in EIA Planned sheet)
    ("Gaines County CTG", "CTG", None, "TX", "East", "Natural Gas",
     1160.0, 2028, 12, "addition", "manual addition (v2)",
     "SPS NMPRC Case 25-00066-UT self-build filing",
     "ADD: SPS (Xcel) gas CT plant, Gaines County, TX, 1,160 MW "
     "winter-max per SPS's Case 25-00066-UT self-build table, "
     "operation Dec 1, 2028. NMPRC approved SPS's construction "
     "programme in summer 2026 and the PUCT approved the two Texas "
     "gas plants with cost caps in Oct 2026. Not in the EIA Planned "
     "sheet (verified in-file). MW basis is the filing's winter max, "
     "not an EIA nameplate — see research log.",
     "SPS Case 25-00066-UT testimony (Table 1, SPS self-build projects); CleanTechnica (PUCT approval, Oct 1, 2026)",
     "https://www.synapse-energy.com/sites/default/files/25-00066%20NMDOJ%20Direct%20Testimony%20Devi%20Glick%2025-105.pdf",
     "Medium"),
    # B. Tolk Station CTG (not in EIA Planned sheet)
    ("Tolk Station CTG", "CTG", None, "TX", "East", "Natural Gas",
     928.0, 2029, 4, "addition", "manual addition (v2)",
     "SPS NMPRC Case 25-00066-UT self-build filing",
     "ADD: SPS gas CT plant at the Tolk Station site, Lamb County, "
     "TX, 928 MW winter-max per the same filing, operation Apr 2, "
     "2029. Approvals as for Gaines County CTG. Not in the EIA "
     "Planned sheet. Global Energy Monitor lists a 1,325 MW Tolk "
     "gas unit as pre-construction — the filing figure is used and "
     "the discrepancy is flagged in the research log.",
     "SPS Case 25-00066-UT testimony (Table 1); CleanTechnica (PUCT approval, Oct 1, 2026)",
     "https://www.synapse-energy.com/sites/default/files/25-00066%20NMDOJ%20Direct%20Testimony%20Devi%20Glick%2025-105.pdf",
     "Medium"),
]


def main():
    plants = pd.read_csv(BASE / "spp_capacity_plants.csv")
    stack_v1 = pd.read_csv(BASE / "spp_capacity_stack.csv")
    stackr_v1 = pd.read_csv(BASE / "spp_capacity_stack_by_eastwest.csv")
    chg_v1 = pd.read_csv(BASE / "spp_capacity_changelog.csv")
    chgr_v1 = pd.read_csv(BASE / "spp_capacity_changelog_by_eastwest.csv")
    with open(BASE / "summary.json") as f:
        s1 = json.load(f)

    # --- sanity: v1 stack == anchor + cumulative v1 changelog
    anchor = stack_v1[stack_v1["year"] == ANCHOR_YEAR].set_index("fuel")["mw"].to_dict()
    anchor_r = {}
    for rg in REGIONS:
        for f in FUELS:
            anchor_r[(rg, f)] = float(stackr_v1[
                (stackr_v1["year"] == ANCHOR_YEAR)
                & (stackr_v1["region"] == rg)
                & (stackr_v1["fuel"] == f)]["mw"].iloc[0])
    running = {f: float(anchor[f]) for f in FUELS}
    running_r = {(rg, f): float(anchor_r[(rg, f)])
                 for rg in REGIONS for f in FUELS}
    for y in range(2026, 2037):
        net = chg_v1[chg_v1["year"] == y]
        netr = chgr_v1[chgr_v1["year"] == y]
        for f in FUELS:
            running[f] += float(net.loc[net["fuel"] == f, "net_mw"].iloc[0])
            for rg in REGIONS:
                running_r[(rg, f)] += float(netr.loc[
                    (netr["region"] == rg) & (netr["fuel"] == f),
                    "net_mw"].iloc[0])
        v1row = stack_v1[stack_v1["year"] == y]
        for f in FUELS:
            v = float(v1row.loc[v1row["fuel"] == f, "mw"].iloc[0])
            assert abs(v - running[f]) < 0.05, (y, f, v, running[f])
        for rg in REGIONS:
            for f in FUELS:
                v = float(stackr_v1[
                    (stackr_v1["year"] == y) & (stackr_v1["region"] == rg)
                    & (stackr_v1["fuel"] == f)]["mw"].iloc[0])
                assert abs(v - running_r[(rg, f)]) < 0.05, (y, rg, f)
    print("v1 stack reproduces from anchor + v1 changelog (Combined + East/West): OK")

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
    print(f"  applied {len(EDITS)} edits")

    new_df = pd.DataFrame([{
        "plant_name": pn, "plant_id": pid, "generator_id": gid,
        "state": st, "county": "", "region": rg, "east_west": rg,
        "balancing_authority": "SWPP", "fuel": fu,
        "energy_source_code": "", "prime_mover_code": "", "technology": "",
        "mw_nameplate": mw, "mw_net_summer": np.nan, "type": typ,
        "status": status, "retirement_status": "",
        "source_sheet": src, "original_year": yr, "original_month": mo,
        "original_date": f"{yr:04d}-{mo:02d}", "effective_year": yr,
        "effective_month": mo, "effective_date": f"{yr:04d}-{mo:02d}",
        "v2_mw_nameplate": mw, "v2_effective_date": f"{yr:04d}-{mo:02d}",
        "v2_status": status, "v2_type": typ, "manual_change": True,
        "manual_change_note": note,
    } for (pn, gid, pid, st, rg, fu, mw, yr, mo, typ, status, src, note,
            _s, _u, _c) in NEW_ROWS])
    p2 = pd.concat([p2, new_df], ignore_index=True)
    print(f"  plants v2 rows: {len(p2)} (v1 {len(plants)} + {len(new_df)} new)")

    # --- changelog v2
    act = p2[p2["v2_type"].isin(["addition", "retirement"])].copy()
    act["v2_year"] = act["v2_effective_date"].str.slice(0, 4).astype(int)
    act = act[(act["v2_year"] >= 2026) & (act["v2_year"] <= 2036)]
    rows, rows_r = [], []
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
            for rg in REGIONS:
                srg = sub[sub["region"] == rg]
                ar = srg[srg["v2_type"] == "addition"]
                rr = srg[srg["v2_type"] == "retirement"]
                rows_r.append({
                    "year": y, "region": rg, "east_west": rg, "fuel": f,
                    "additions_mw": round(float(ar["v2_mw_nameplate"].sum()), 1),
                    "additions_count": int(len(ar)),
                    "retirements_mw": round(float(rr["v2_mw_nameplate"].sum()), 1),
                    "retirements_count": int(len(rr)),
                    "net_mw": round(float(ar["v2_mw_nameplate"].sum()
                                    - rr["v2_mw_nameplate"].sum()), 1),
                })
    chg2 = pd.DataFrame(rows)
    chg2r = pd.DataFrame(rows_r)

    for y in range(2026, 2037):
        d = round(float(chg2[chg2["year"] == y]["net_mw"].sum()
                        - chg_v1[chg_v1["year"] == y]["net_mw"].sum()), 1)
        assert abs(d - EXPECTED_FLOW_DELTA[y]) < 0.05, (y, d, EXPECTED_FLOW_DELTA[y])
    print("  yearly flow deltas match the expected table: OK "
          f"(cumulative {sum(EXPECTED_FLOW_DELTA.values()):+,.1f} MW)")

    # --- stack v2
    stack_rows, stackr_rows = [], []
    for y in range(2016, 2026):
        for _, r in stack_v1[stack_v1["year"] == y].iterrows():
            stack_rows.append({"year": int(r["year"]), "fuel": r["fuel"],
                               "mw": float(r["mw"]), "period": "trailing",
                               "anchor_year": bool(r["anchor_year"]),
                               "source_note": r["source_note"]})
        for _, r in stackr_v1[stackr_v1["year"] == y].iterrows():
            stackr_rows.append({"year": int(r["year"]), "region": r["region"],
                                "east_west": r["east_west"],
                                "fuel": r["fuel"], "mw": float(r["mw"]),
                                "period": "trailing",
                                "anchor_year": bool(r["anchor_year"]),
                                "source_note": r["source_note"]})
    note2 = ("EIA-860M Dec-31-2025 anchor (post-expansion footprint) + "
             "v2 changelog (EIA-860M + manual corrections: SPS Gaines "
             "County / Tolk CTG additions, Craig 3 / Tolk / Rawhide GT "
             "retimes)")
    running = {f: float(anchor[f]) for f in FUELS}
    running_r = {(rg, f): float(anchor_r[(rg, f)])
                 for rg in REGIONS for f in FUELS}
    for y in range(2026, 2037):
        net = chg2[chg2["year"] == y]
        netr = chg2r[chg2r["year"] == y]
        for f in FUELS:
            running[f] += float(net.loc[net["fuel"] == f, "net_mw"].iloc[0])
            for rg in REGIONS:
                running_r[(rg, f)] += float(netr.loc[
                    (netr["region"] == rg) & (netr["fuel"] == f),
                    "net_mw"].iloc[0])
        for f in FUELS + ["Total"]:
            v = round(sum(running.values()), 1) if f == "Total" else round(running[f], 1)
            stack_rows.append({"year": y, "fuel": f, "mw": v,
                               "period": "forward", "anchor_year": False,
                               "source_note": note2})
        for rg in REGIONS:
            for f in FUELS + ["Total"]:
                v = round(sum(running_r[(rg, ff)] for ff in FUELS), 1) \
                    if f == "Total" else round(running_r[(rg, f)], 1)
                stackr_rows.append({"year": y, "region": rg, "east_west": rg,
                                    "fuel": f, "mw": v, "period": "forward",
                                    "anchor_year": False, "source_note": note2})
    stack2 = pd.DataFrame(stack_rows)
    stack2r = pd.DataFrame(stackr_rows)
    for y in range(2016, 2037):
        for f in FUELS + ["Total"]:
            s = round(sum(float(stack2r[
                (stack2r["year"] == y) & (stack2r["region"] == rg)
                & (stack2r["fuel"] == f)]["mw"].iloc[0]) for rg in REGIONS), 1)
            t = float(stack2[(stack2["year"] == y)
                             & (stack2["fuel"] == f)]["mw"].iloc[0])
            assert abs(s - t) < 0.1, (y, f, s, t)
    print("  East + West == Combined in v2 stack (all years/fuels): OK")

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
            "region": orig["region"], "east_west": orig["east_west"],
            "fuel": orig["fuel"],
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
    for (pn, gid, _pid, st, rg, fu, mw, yr, mo, typ, _status, _ss, note,
         s, u, c) in NEW_ROWS:
        adj_rows.append({
            "plant": pn, "unit": str(gid), "state": st, "region": rg,
            "east_west": rg, "fuel": fu, "v1_mw": "", "v1_date": "",
            "v2_mw": float(mw), "v2_date": f"{yr:04d}-{mo:02d}",
            "change_type": "add", "reason": note,
            "classification": "manual correction",
            "source": s, "source_url": u, "confidence": c,
            "source_date": "2026-11-15", "date_accessed": "2026-11-15",
        })
    adj = pd.DataFrame(adj_rows)
    adj.to_csv(BASE / "manual_adjustments.csv", index=False)
    p2.to_csv(BASE / "spp_capacity_plants_v2.csv", index=False)
    stack2.to_csv(BASE / "spp_capacity_stack_v2.csv", index=False)
    stack2r.to_csv(BASE / "spp_capacity_stack_by_eastwest_v2.csv", index=False)
    chg2.to_csv(BASE / "spp_capacity_changelog_v2.csv", index=False)
    chg2r.to_csv(BASE / "spp_capacity_changelog_by_eastwest_v2.csv",
                 index=False)

    def agg(df, col):
        return {f: round(float(df[df["fuel"] == f][col].sum()), 1)
                for f in FUELS}
    v1_add = agg(chg_v1, "additions_mw"); v2_add = agg(chg2, "additions_mw")
    v1_ret = agg(chg_v1, "retirements_mw"); v2_ret = agg(chg2, "retirements_mw")
    tot2r = {rg: {str(y): round(float(stack2r[
        (stack2r["year"] == y) & (stack2r["region"] == rg)
        & (stack2r["fuel"] == "Total")]["mw"].iloc[0]), 1)
        for y in range(2016, 2037)} for rg in REGIONS}
    tot1r = {rg: {str(y): round(float(stackr_v1[
        (stackr_v1["year"] == y) & (stackr_v1["region"] == rg)
        & (stackr_v1["fuel"] == "Total")]["mw"].iloc[0]), 1)
        for y in range(2016, 2037)} for rg in REGIONS}
    summary = {
        "version": "v2",
        "built": "2026-11-15",
        "anchor_unchanged_mw": s1["anchor"]["total_mw"],
        "anchor_by_region_mw": s1["anchor"]["by_region_mw"],
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
        "yearly_totals_by_region_mw_v1": tot1r,
        "yearly_totals_by_region_mw_v2": tot2r,
        "manual_adjustments_count": len(adj_rows),
        "named_adjustments_count": 5,
        "largest_manual_changes_mw": [
            {"plant": "Gaines County CTG (new SPS gas, TX, East)",
             "change": "add", "mw": 1160.0},
            {"plant": "Tolk coal Units 1/2 retime 2028->2029",
             "change": "retime", "mw": 1135.8},
            {"plant": "Tolk Station CTG (new SPS gas, TX, East)",
             "change": "add", "mw": 928.0},
            {"plant": "Craig (CO) Unit 3 retime 2029->2028",
             "change": "retime", "mw": 534.8},
            {"plant": "Rawhide new gas retime 2028->2029",
             "change": "retime", "mw": 223.0},
        ],
        "not_added_flagged_candidates_mw": {
            "Tri-State Craig-site replacement gas (ERP, at Craig Station, CO, West; date not pinned)": 307.0,
            "Tri-State Craig-site battery storage (ERP; date not pinned)": 200.0,
            "SPP ERAS queue pool (13.3 GW submitted Oct 2025; not itemised to plant/MW/date)": 13300.0,
            "Comanche (OK) PSO new CC 1,372.8 MW in EIA at (P) status (kept in v1/v2; approval unverified)": 1372.8,
            "Naples Power Plant (AECC) 900 MW in EIA at (P) status (kept; approval unverified)": 900.0,
            "Horizon/Williams Creek 100 MW battery (CSU campus plan; no EIA row found)": 100.0,
            "SPS life extensions requested for Nichols 1/2, Maddox 1, Plant X 4 (Case 25-00066-UT; approval status unclear; EIA dates kept)": None,
            "Tri-State plants under PSCO/PNM BAs excluded by the boundary rule (sensitivity, not a candidate)": 882.1,
        },
        "files": {
            "manual_adjustments": "manual_adjustments.csv",
            "plants_v2": "spp_capacity_plants_v2.csv",
            "stack_v2": "spp_capacity_stack_v2.csv",
            "stack_by_eastwest_v2": "spp_capacity_stack_by_eastwest_v2.csv",
            "changelog_v2": "spp_capacity_changelog_v2.csv",
            "changelog_by_eastwest_v2": "spp_capacity_changelog_by_eastwest_v2.csv",
            "summary_v2": "summary_v2.json",
            "research_log": "research_log.md",
            "readme_v2": "README_v2.md",
            "charts": ["01_stacked_area_v2.png", "02_net_change_forward_v2.png",
                       "03_eastwest_stacked_v2.png", "04_eastwest_totals_v2.png"],
        },
    }
    with open(BASE / "summary_v2.json", "w") as f:
        json.dump(summary, f, indent=2)
    print("  wrote manual_adjustments.csv, plants/changelog/stack v2 CSVs, "
          "summary_v2.json")

    wide = stack2.pivot(index="year", columns="fuel", values="mw").reset_index()
    wide_r = stack2r.pivot_table(index="year", columns=["region", "fuel"],
                                 values="mw").reset_index()
    return wide, wide_r, chg2


def make_charts(wide, wide_r, chg2):
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
    ax.text(2025.95, bottom.max() * 0.97,
            "Today (Nov 2026)\nanchor Dec 31, 2025", fontsize=9, va="top")
    ax.set_xlim(2016, 2036)
    ax.set_ylabel("Installed capacity (GW)")
    ax.set_xlabel("Year (Dec 31 position; 2026-2036 = anchor + v2 changelog)")
    ax.set_title("SPP generation capacity stack by fuel, 2016-2036 — v2\n"
                 "EIA-860M anchor (post-expansion footprint) + changelog + "
                 "manual corrections (nameplate)", fontsize=11)
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
    ax.set_title("SPP annual net capacity change by fuel, forward 2026-2036 — v2\n"
                 "(EIA-860M + manual additions/retimes, nameplate)", fontsize=11)
    ax.legend(ncol=2, fontsize=9, loc="upper right")
    ax.grid(True, alpha=0.3, axis="y")
    fig.tight_layout()
    fig.savefig(BASE / "02_net_change_forward_v2.png", dpi=150)
    plt.close(fig)

    fig, axes = plt.subplots(2, 1, figsize=(12, 10), sharex=True)
    for ax, rg in zip(axes, REGIONS):
        bottom = np.zeros(len(years))
        for f in STACK_ORDER:
            vals = wide_r[(rg, f)].values / 1000.0
            ax.fill_between(years, bottom, bottom + vals,
                            label=f, color=FUEL_COLORS[f], alpha=0.9)
            bottom += vals
        ax.axvline(2025.9, color="black", linestyle="--", linewidth=1.2)
        ax.set_ylabel("GW")
        note = " (pro-forma before Apr 2026)" if rg == "West" else ""
        ax.set_title(f"SPP {rg} — capacity stack by fuel, 2016-2036 (GW)"
                     f"{note} — v2", fontsize=11)
        ax.grid(True, alpha=0.3)
        ax.legend(ncol=5, fontsize=8, loc="upper left")
    axes[-1].set_xlabel("Year (Dec 31 position)")
    fig.tight_layout()
    fig.savefig(BASE / "03_eastwest_stacked_v2.png", dpi=150)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(12, 6))
    for rg in REGIONS:
        ax.plot(years, wide_r[(rg, "Total")].values / 1000.0,
                label=rg, color=REGION_COLORS[rg], linewidth=2)
    ax.plot(years, wide["Total"].values / 1000.0,
            label="SPP total", color="black", linewidth=2, linestyle="--")
    ax.axvline(2025.9, color="black", linestyle="--", linewidth=1.2)
    ax.set_ylabel("Installed capacity (GW)")
    ax.set_xlabel("Year (Dec 31 position)")
    ax.set_title("SPP capacity by East/West, 2016-2036 — v2", fontsize=11)
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(BASE / "04_eastwest_totals_v2.png", dpi=150)
    plt.close(fig)
    print("  charts written")


if __name__ == "__main__":
    w, wr, c2 = main()
    make_charts(w, wr, c2)
