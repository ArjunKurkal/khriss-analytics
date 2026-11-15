#!/usr/bin/env python3
"""Build MISO capacity stack v2 — EIA + manual corrections.

Mirrors ~/workspace/pjm-capacity-stack/build_stack_v2.py: reads the v1
files, verifies v1 reproduces (anchor + v1 changelog, total and by
region), applies manual corrections, rebuilds the changelog and stack,
and writes v2 files alongside (v1 files are never overwritten).

Corrections (12 named adjustments, 26 row-level changes; see
research_log.md for the evidence and per-item confidence):
  A  ADD Cayuga Energy Complex CC1/CC2, IN, gas, 2x738 MW (Sep 2029 / May 2030)
  B  ADD Cayuga coal Units 1/2 retirement, IN, 2x531 MW (Jan 2030 / Jan 2031)
  C  ADD Legend Power Station, TX, gas, 754 MW (Jul 2028) — EIA BA code
     ERCO is an error; Entergy Texas is MISO (PUCT Docket 56693: MISO
     determines Legend's transmission upgrades)
  D  ADD DTE Handy (1,400 MW, Dec 2031) + Milan (700 MW, Dec 2032), MI, gas
  E  ADD Consumers Energy Karn + Thetford, MI, gas, 2x750 MW (2031)
  F  ADD Fermi 2 uprate, MI, nuclear, +177 MW (2036)
  G  FUEL SWITCH Belle River ST1/ST2, MI, coal->gas, 2x697.5 MW (2026)
  H  FUEL SWITCH AES Petersburg ST3/4, IN, coal->gas, 2x670.9 MW (2026)
  I  RETIME J.H. Campbell Units 1-3, MI, coal, 1,560.8 MW, Nov 2026 -> Feb 2027
     (DOE Order No. 202-26-51, Nov 13, 2026, in effect to Feb 12, 2027)
  J  RETIME Traceview, MS, gas, 819.4 MW, Aug 2028 -> Dec 2029
  K  RETIME Gerald Andrus Unit 1, MS, gas, 781.4 MW, Jun 2035 -> May 2028
  L  RETIME Steel River Solar Phase 3, AR, solar 500 MW + battery 250 MW,
     Jul 2030 -> Dec 2029

Arithmetic note (coordinator correction of the v2 researcher's table):
the researcher double-counted Belle River's coal retirement as a NEW
retirement. It is a RETIME (v1 already had it, Dec 2028 -> Dec 2026),
so the cumulative coal-retirement delta is Cayuga 1,062 + Petersburg
1,341.8 = 2,403.8 MW, not 3,798.8 MW. Correct net 2036 effect is
+6,340.0 MW (Gas +8,566.8; Coal -2,403.8; Nuclear +177.0), not the
researcher's +4,945.0 MW. The 2028 flow delta is +548.2 MW (Legend +754,
Traceview -819.4, Andrus -781.4, Belle River coal out of 2028 +1,395),
not -846.8 MW. The build asserts the corrected yearly flow deltas.
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
REGIONS = ["North", "Central", "South"]
FUEL_COLORS = {
    "Coal": "#3b3b3b", "Natural Gas": "#d95f02", "Nuclear": "#7570b3",
    "Hydro": "#1b9e77", "Pumped Storage": "#66a61e", "Wind": "#377eb8",
    "Solar": "#e6ab02", "Oil": "#a6761d", "Battery Storage": "#e7298a",
    "Other": "#999999",
}
REGION_COLORS = {"North": "#377eb8", "Central": "#e6ab02", "South": "#d95f02"}

# Expected yearly FLOW deltas (v2 net changelog - v1 net changelog), MW.
# Asserted in main(). Cumulative = +6,340.0 MW (see header note).
EXPECTED_FLOW_DELTA = {
    2026: 1560.8, 2027: -1560.8, 2028: 548.2, 2029: 2307.4, 2030: -543.0,
    2031: 2369.0, 2032: 700.0, 2033: 0.0, 2034: 0.0, 2035: 781.4, 2036: 177.0,
}

# ---------------- Manual corrections ----------------
# EDITS: (plant_name exact, generator_id, new_mw, new_eff (y, mo),
#         new_status, note, source, source_url, confidence)
# new_mw / new_eff / new_status may be None (leave unchanged).
EDITS = [
    # I. Campbell retime (DOE Order No. 202-26-51)
    ("J H Campbell", "1", None, (2027, 2), None,
     "Retime Nov 2026 -> Feb 2027: DOE Order No. 202-26-51 (Nov 13, 2026) "
     "keeps Campbell available Nov 15, 2026-Feb 12, 2027. Feb 2027 is the "
     "current order's expiry, not a new retirement date; further renewal "
     "likely; D.C. Circuit vacated the first order Sep 11, 2026.",
     "DOE / energy.gov press release Nov 14, 2026",
     "https://www.energy.gov/articles/energy-secretary-keeps-critical-coal-fired-generation-operational-ahead-winter-midwest",
     "Medium-High"),
    ("J H Campbell", "2", None, (2027, 2), None,
     "Retime Nov 2026 -> Feb 2027 (see Unit 1).",
     "DOE Order No. 202-26-51",
     "https://www.energy.gov/articles/energy-secretary-keeps-critical-coal-fired-generation-operational-ahead-winter-midwest",
     "Medium-High"),
    ("J H Campbell", "3", None, (2027, 2), None,
     "Retime Nov 2026 -> Feb 2027 (see Unit 1).",
     "DOE Order No. 202-26-51",
     "https://www.energy.gov/articles/energy-secretary-keeps-critical-coal-fired-generation-operational-ahead-winter-midwest",
     "Medium-High"),
    # J. Traceview retime
    ("Traceview Advanced Power Station", "CT1", None, (2029, 12), None,
     "Retime Aug 2028 -> Dec 2029 (month placeholder; year published). "
     "Entergy project page: construction 2026, in-service 2029; MDEQ air "
     "permit issued Oct 14, 2026.",
     "Entergy project page; POWER Magazine Oct 2025",
     "https://www.powermag.com/entergy-mississippi-adding-third-gas-fired-power-plant-to-superpower-strategy/",
     "Medium-High"),
    ("Traceview Advanced Power Station", "ST1", None, (2029, 12), None,
     "Retime Aug 2028 -> Dec 2029 (see CT1).",
     "Entergy project page; POWER Magazine Oct 2025",
     "https://www.powermag.com/entergy-mississippi-adding-third-gas-fired-power-plant-to-superpower-strategy/",
     "Medium-High"),
    # K. Gerald Andrus retime
    ("Gerald Andrus", "1", None, (2028, 5), None,
     "Retime Jun 2035 -> May 2028: Entergy states Gerald Andrus retires "
     "when Delta Blues comes online in 2028 (Delta Blues is May 2028 in EIA).",
     "Entergy Delta Blues groundbreaking release",
     "https://www.entergy.com/news/entergy-mississippi-breaks-ground-on-delta-blues-advanced-power-station",
     "Medium-High"),
    # L. Steel River Solar Phase 3 retime
    ("Steel River Solar Phase 3", "SRSP3", None, (2029, 12), None,
     "Retime Jul 2030 -> Dec 2029 (month placeholder; year published). "
     "Developer: full three-phase project (2.45 GWdc solar, 2.9 GWh "
     "storage) completes by 2029; phases 1-2 broke ground Jul 14, 2026.",
     "Reuters Jun 11, 2026; NACleanEnergy",
     "https://www.reuters.com/legal/litigation/cypress-creek-secures-35-billion-one-largest-us-solar-storage-projects-2026-06-11/",
     "Medium"),
    ("Steel River Solar Phase 3", "SRSB3", None, (2029, 12), None,
     "Retime Jul 2030 -> Dec 2029 (see SRSP3).",
     "Reuters Jun 11, 2026; NACleanEnergy",
     "https://www.reuters.com/legal/litigation/cypress-creek-secures-35-billion-one-largest-us-solar-storage-projects-2026-06-11/",
     "Medium"),
    # G. Belle River fuel switch: coal retirements Dec 2028 -> Dec 2026
    # (gas additions are NEW_ROWS below).
    ("Belle River", "ST1", None, (2026, 12), None,
     "Fuel switch coal->gas: Unit 1 converted Dec 2025, booked Dec 2026 "
     "(anchor boundary; EIA still shows coal). DTE 2022 IRP moved coal "
     "exit from 2028 to 2026; $135m pre-approved Jul 2023.",
     "Utility Dive; Global Energy Monitor",
     "https://www.utilitydive.com/news/dte-energy-resource-plan-irp-solar-coal-michigan-psc/635781/",
     "Medium-High"),
    ("Belle River", "ST2", None, (2026, 12), None,
     "Fuel switch coal->gas: Unit 2 converts Dec 2026.",
     "Utility Dive; Global Energy Monitor",
     "https://www.utilitydive.com/news/dte-energy-resource-plan-irp-solar-coal-michigan-psc/635781/",
     "Medium-High"),
]

# NEW_ROWS: (plant_name, generator_id, plant_id, state, region, fuel,
#            mw, year, month, type, status, source_sheet, note,
#            source, source_url, confidence)
NEW_ROWS = [
    # A. Cayuga CC (not in EIA Planned sheet)
    ("Cayuga Energy Complex", "CC1", None, "IN", "Central", "Natural Gas",
     738.0, 2029, 9, "addition", "manual addition (v2)",
     "IURC Cause No. 46193 CPCN",
     "ADD: 2x738 MW winter CC, CPCN approved Oct 29, 2025, ~$3.33bn, "
     "broke ground May 2026. CC1 in service Sep 1, 2029. Grid-connected "
     "utility plant replacing coal; MISO Generator Replacement Request R1044.",
     "IURC OUCC case page; Duke Pinegar testimony, Cause No. 46193",
     "https://www.in.gov/oucc/electric/key-cases-by-utility/duke-energy-rates/cayuga-generating-station-cpcn",
     "High"),
    ("Cayuga Energy Complex", "CC2", None, "IN", "Central", "Natural Gas",
     738.0, 2030, 5, "addition", "manual addition (v2)",
     "IURC Cause No. 46193 CPCN",
     "ADD: CC2 in service May 29, 2030 (see CC1).",
     "IURC OUCC case page; Duke Pinegar testimony, Cause No. 46193",
     "https://www.in.gov/oucc/electric/key-cases-by-utility/duke-energy-rates/cayuga-generating-station-cpcn",
     "High"),
    # B. Cayuga coal retirements (EIA has no planned retirement for them)
    ("Cayuga", "1", 1001, "IN", "Central", "Coal",
     531.0, 2030, 1, "retirement", "manual addition (v2)",
     "Duke Nov 2024 IRP preferred portfolio",
     "ADD retirement: IRP retires Cayuga coal Unit 1 by the start of 2030. "
     "Flag: Jun 2025 settlement requires a feasibility study on selling "
     "the coal units to a third party for continued operation; OUCC says "
     "'will retire by 2032'.",
     "Global Energy Monitor (summarises IRP + settlement + Oct 2025 approval)",
     "https://www.gem.wiki/Cayuga_Generating_Station",
     "Medium"),
    ("Cayuga", "2", 1001, "IN", "Central", "Coal",
     531.0, 2031, 1, "retirement", "manual addition (v2)",
     "Duke Nov 2024 IRP preferred portfolio",
     "ADD retirement: IRP retires Cayuga coal Unit 2 by the start of 2031 "
     "(see Unit 1 flag).",
     "Global Energy Monitor",
     "https://www.gem.wiki/Cayuga_Generating_Station",
     "Medium"),
    # C. Legend (EIA Planned plant 68053, 754 MW, Jul 2028, but BA coded ERCO)
    ("Legend Power Station", "1", 68053, "TX", "South", "Natural Gas",
     754.0, 2028, 7, "addition", "manual addition (v2)",
     "EIA Planned sheet plant 68053 (BA code corrected ERCO -> MISO)",
     "ADD: 754 MW CCCT, Port Arthur, Jefferson Co. PUCT approved Sep 11, "
     "2025 ($1.6bn); broke ground Apr 2026; in service mid-2028. Entergy "
     "Texas is MISO (PUCT Docket 56693: MISO determines Legend's "
     "transmission upgrades; sister plants Orange County/Lone Star are "
     "coded BA=MISO). EIA BA=ERCO is a respondent error.",
     "Entergy; PUCT Docket 56693; Utility Dive",
     "https://www.entergy.com/news/entergy-texas-receives-puct-approval-for-two-power-plants-to-support-southeast-texas-growth",
     "High"),
    # D. DTE Handy + Milan (IRP proposal, MPSC review pending)
    ("DTE Handy Township", "1", None, "MI", "Central", "Natural Gas",
     1400.0, 2031, 12, "addition", "manual addition (v2)",
     "DTE 20-year IRP filed with MPSC Sep 24, 2026",
     "ADD: 1,400 MW CC, Livingston Co., $3.9bn, online by end-2031, "
     "replacing Monroe coal. IRP proposal, not approval (MPSC review up "
     "to 360 days). Grid-connected; driven partly by ~2.4 GW new load "
     "incl. Oracle/Google contracts, sited separately, grid-injected.",
     "DTE release; Planet Detroit / Canary Media",
     "https://www.dteenergy.com/us/en/newsroom/2026/Powering-the-next-generation--DTE-lays-out-plan-to-deliver-a-cleaner,-reliable-energy-future-for-Michigan-customers.html",
     "Medium"),
    ("DTE Milan Township", "1", None, "MI", "Central", "Natural Gas",
     700.0, 2032, 12, "addition", "manual addition (v2)",
     "DTE 20-year IRP filed with MPSC Sep 24, 2026",
     "ADD: 700 MW CC, Monroe Co., $2.5bn, online by end-2032 (see Handy).",
     "DTE release; Planet Detroit / Canary Media",
     "https://www.dteenergy.com/us/en/newsroom/2026/Powering-the-next-generation--DTE-lays-out-plan-to-deliver-a-cleaner,-reliable-energy-future-for-Michigan-customers.html",
     "Medium"),
    # E. Consumers Karn + Thetford (IRP proposal; split/date assumed)
    ("Consumers Energy Karn", "1", None, "MI", "Central", "Natural Gas",
     750.0, 2031, 12, "addition", "manual addition (v2)",
     "Consumers IRP filed Jun 2026 (announced Mar 11, 2026)",
     "ADD: 750 MW, Karn site (Bay Co.). Total 1.5 GW across Karn + "
     "Thetford is verified; per-unit 750/750 split and Dec 2031 date are "
     "assumed placeholders (completion 'around 2031' per secondary "
     "summaries). MPSC approval pending.",
     "Consumers / Barchart",
     "https://www.barchart.com/story/news/694093/consumers-energy-unveils-electric-supply-plan-to-keep-energy-reliable-and-bills-lower",
     "Low-Medium"),
    ("Consumers Energy Thetford", "1", None, "MI", "Central", "Natural Gas",
     750.0, 2031, 12, "addition", "manual addition (v2)",
     "Consumers IRP filed Jun 2026 (announced Mar 11, 2026)",
     "ADD: 750 MW, Thetford Township site (Genesee Co.). See Karn note "
     "on assumed split/date.",
     "Consumers / Barchart",
     "https://www.barchart.com/story/news/694093/consumers-energy-unveils-electric-supply-plan-to-keep-energy-reliable-and-bills-lower",
     "Low-Medium"),
    # F. Fermi 2 uprate (IRP proposal)
    ("Fermi 2", "1", None, "MI", "Central", "Nuclear",
     177.0, 2036, 1, "addition", "manual addition (v2)",
     "DTE 20-year IRP filed with MPSC Sep 24, 2026",
     "ADD (uprate): +177 MW to existing Fermi 2 nuclear plant, 'beginning "
     "in 2036' (Jan 2036 placeholder). IRP proposal, not yet approved.",
     "DTE release",
     "https://www.dteenergy.com/us/en/newsroom/2026/Powering-the-next-generation--DTE-lays-out-plan-to-deliver-a-cleaner,-reliable-energy-future-for-Michigan-customers.html",
     "Medium"),
    # G. Belle River gas additions (fuel switch; coal retirements retimed above)
    ("Belle River (gas conversion)", "ST1", 6034, "MI", "Central",
     "Natural Gas", 697.5, 2026, 12, "addition", "manual addition (v2)",
     "DTE 2022 IRP (fuel switch)",
     "ADD gas: Unit 1 converted Dec 2025, booked Dec 2026 (anchor "
     "boundary). See Belle River EDIT.",
     "Utility Dive; Global Energy Monitor",
     "https://www.utilitydive.com/news/dte-energy-resource-plan-irp-solar-coal-michigan-psc/635781/",
     "Medium-High"),
    ("Belle River (gas conversion)", "ST2", 6034, "MI", "Central",
     "Natural Gas", 697.5, 2026, 12, "addition", "manual addition (v2)",
     "DTE 2022 IRP (fuel switch)",
     "ADD gas: Unit 2 converts Dec 2026.",
     "Utility Dive; Global Energy Monitor",
     "https://www.utilitydive.com/news/dte-energy-resource-plan-irp-solar-coal-michigan-psc/635781/",
     "Medium-High"),
    # H. Petersburg fuel switch (v1 has no Petersburg coal rows)
    ("AES Petersburg (gas conversion)", "ST3", 994, "IN", "Central",
     "Natural Gas", 670.9, 2026, 6, "addition", "manual addition (v2)",
     "IURC approval Nov 2024; AES",
     "ADD gas: Unit 3 outage Feb 2026, COD Jun 2026. $1.1bn conversion; "
     "first Indiana IOU to stop burning coal.",
     "Indiana Capital Chronicle; AES",
     "https://indianacapitalchronicle.com/2024/11/06/aes-indiana-wins-approval-for-natural-gas-conversion/",
     "High"),
    ("AES Petersburg (gas conversion)", "4", 994, "IN", "Central",
     "Natural Gas", 670.9, 2026, 12, "addition", "manual addition (v2)",
     "IURC approval Nov 2024; AES",
     "ADD gas: Unit 4 outage Jun 2026, completion Oct 2026, COD Dec 2026 "
     "(month Medium confidence).",
     "Indiana Capital Chronicle; AES",
     "https://indianacapitalchronicle.com/2024/11/06/aes-indiana-wins-approval-for-natural-gas-conversion/",
     "High"),
    ("AES Petersburg", "ST3", 994, "IN", "Central", "Coal",
     670.9, 2026, 6, "retirement", "manual addition (v2)",
     "IURC approval Nov 2024; AES",
     "ADD coal retirement: Unit 3 leaves coal Jun 2026 (fuel switch). "
     "EIA nameplate 670.9 MW (not the ~1,052 MW figure in the PJM log).",
     "Indiana Capital Chronicle; AES",
     "https://indianacapitalchronicle.com/2024/11/06/aes-indiana-wins-approval-for-natural-gas-conversion/",
     "High"),
    ("AES Petersburg", "4", 994, "IN", "Central", "Coal",
     670.9, 2026, 12, "retirement", "manual addition (v2)",
     "IURC approval Nov 2024; AES",
     "ADD coal retirement: Unit 4 leaves coal Dec 2026 (fuel switch).",
     "Indiana Capital Chronicle; AES",
     "https://indianacapitalchronicle.com/2024/11/06/aes-indiana-wins-approval-for-natural-gas-conversion/",
     "High"),
]


def main():
    plants = pd.read_csv(BASE / "miso_capacity_plants.csv")
    stack_v1 = pd.read_csv(BASE / "miso_capacity_stack.csv")
    stackr_v1 = pd.read_csv(BASE / "miso_capacity_stack_by_region.csv")
    chg_v1 = pd.read_csv(BASE / "miso_capacity_changelog.csv")
    chgr_v1 = pd.read_csv(BASE / "miso_capacity_changelog_by_region.csv")
    with open(BASE / "summary.json") as f:
        s1 = json.load(f)

    # --- sanity check: v1 stack == anchor + cumulative v1 changelog
    # (total and by region)
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
    print("v1 stack reproduces from anchor + v1 changelog (total + regions): OK")

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
        "state": st, "county": "", "region": rg,
        "balancing_authority": "MISO", "fuel": fu,
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

    # --- changelog v2 from plants v2 (effective years 2026-2036, non-excluded)
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
                    "year": y, "region": rg, "fuel": f,
                    "additions_mw": round(float(ar["v2_mw_nameplate"].sum()), 1),
                    "additions_count": int(len(ar)),
                    "retirements_mw": round(float(rr["v2_mw_nameplate"].sum()), 1),
                    "retirements_count": int(len(rr)),
                    "net_mw": round(float(ar["v2_mw_nameplate"].sum()
                                    - rr["v2_mw_nameplate"].sum()), 1),
                })
    chg2 = pd.DataFrame(rows)
    chg2r = pd.DataFrame(rows_r)

    # --- assert the corrected yearly flow deltas (v2 - v1)
    for y in range(2026, 2037):
        d = round(float(chg2[chg2["year"] == y]["net_mw"].sum()
                        - chg_v1[chg_v1["year"] == y]["net_mw"].sum()), 1)
        assert abs(d - EXPECTED_FLOW_DELTA[y]) < 0.05, (y, d, EXPECTED_FLOW_DELTA[y])
    print("  yearly flow deltas match the corrected table: OK "
          f"(cumulative {sum(EXPECTED_FLOW_DELTA.values()):+,.1f} MW)")

    # --- stack v2: trailing unchanged, forward = anchor + cumulative v2 changelog
    stack_rows, stackr_rows = [], []
    for y in range(2016, 2026):
        for _, r in stack_v1[stack_v1["year"] == y].iterrows():
            stack_rows.append({"year": int(r["year"]), "fuel": r["fuel"],
                               "mw": float(r["mw"]), "period": "trailing",
                               "anchor_year": bool(r["anchor_year"]),
                               "source_note": r["source_note"]})
        for _, r in stackr_v1[stackr_v1["year"] == y].iterrows():
            stackr_rows.append({"year": int(r["year"]), "region": r["region"],
                                "fuel": r["fuel"], "mw": float(r["mw"]),
                                "period": "trailing",
                                "anchor_year": bool(r["anchor_year"]),
                                "source_note": r["source_note"]})
    note2 = ("EIA-860M Dec-31-2025 anchor + v2 changelog (EIA-860M + manual "
             "corrections: Cayuga, Legend, DTE/Consumers gas, Fermi 2 uprate, "
             "Belle River/Petersburg fuel switches, Campbell/Traceview/"
             "Andrus/Steel River retimes)")
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
                stackr_rows.append({"year": y, "region": rg, "fuel": f,
                                    "mw": v, "period": "forward",
                                    "anchor_year": False, "source_note": note2})
    stack2 = pd.DataFrame(stack_rows)
    stack2r = pd.DataFrame(stackr_rows)
    # Regional sums == MISO total, every year and fuel.
    for y in range(2016, 2037):
        for f in FUELS + ["Total"]:
            s = round(sum(float(stack2r[
                (stack2r["year"] == y) & (stack2r["region"] == rg)
                & (stack2r["fuel"] == f)]["mw"].iloc[0]) for rg in REGIONS), 1)
            t = float(stack2[(stack2["year"] == y)
                             & (stack2["fuel"] == f)]["mw"].iloc[0])
            assert abs(s - t) < 0.1, (y, f, s, t)
    print("  regional stacks sum to MISO total (all years/fuels): OK")

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
            "region": orig["region"], "fuel": orig["fuel"],
            "v1_mw": float(orig["mw_nameplate"]),
            "v1_date": orig["effective_date"],
            "v2_mw": float(new_mw) if new_mw is not None
                     else float(orig["mw_nameplate"]),
            "v2_date": f"{new_eff[0]:04d}-{new_eff[1]:02d}" if new_eff
                       else orig["effective_date"],
            "change_type": "retime", "reason": note,
            "classification": "manual correction",
            "source": src, "source_url": url, "confidence": conf,
            "source_date": "2026-11-14", "date_accessed": "2026-11-14",
        })
    for (pn, gid, _pid, st, rg, fu, mw, yr, mo, typ, _status, _ss, note,
         s, u, c) in NEW_ROWS:
        if typ == "addition":
            ct = ("add (fuel switch)" if "gas conversion" in pn else "add")
        else:
            ct = ("add retirement (fuel switch)" if pn == "AES Petersburg"
                  else "add retirement")
        adj_rows.append({
            "plant": pn, "unit": str(gid), "state": st, "region": rg,
            "fuel": fu, "v1_mw": "", "v1_date": "",
            "v2_mw": float(mw), "v2_date": f"{yr:04d}-{mo:02d}",
            "change_type": ct, "reason": note,
            "classification": "manual correction",
            "source": s, "source_url": u, "confidence": c,
            "source_date": "2026-11-14", "date_accessed": "2026-11-14",
        })
    adj = pd.DataFrame(adj_rows)
    adj.to_csv(BASE / "manual_adjustments.csv", index=False)
    p2.to_csv(BASE / "miso_capacity_plants_v2.csv", index=False)
    stack2.to_csv(BASE / "miso_capacity_stack_v2.csv", index=False)
    stack2r.to_csv(BASE / "miso_capacity_stack_by_region_v2.csv", index=False)
    chg2.to_csv(BASE / "miso_capacity_changelog_v2.csv", index=False)
    chg2r.to_csv(BASE / "miso_capacity_changelog_by_region_v2.csv",
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
    summary = {
        "version": "v2",
        "built": "2026-11-14",
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
        "yearly_totals_by_region_mw_v2": tot2r,
        "manual_adjustments_count": len(adj_rows),
        "named_adjustments_count": 12,
        "largest_manual_changes_mw": [
            {"plant": "Cayuga Energy Complex (new CC)", "change": "add",
             "mw": 1476.0},
            {"plant": "DTE Handy + Milan (new gas)", "change": "add",
             "mw": 2100.0},
            {"plant": "J.H. Campbell retime 2026->2027", "change": "retime",
             "mw": 1560.8},
            {"plant": "Consumers Energy Karn + Thetford (new gas)",
             "change": "add", "mw": 1500.0},
            {"plant": "Belle River fuel switch (coal->gas)",
             "change": "fuel switch", "mw": 1395.0},
            {"plant": "AES Petersburg fuel switch (coal->gas)",
             "change": "fuel switch", "mw": 1341.8},
            {"plant": "Cayuga coal Units 1/2 retirement",
             "change": "add retirement", "mw": 1062.0},
            {"plant": "Traceview retime 2028->2029", "change": "retime",
             "mw": 819.4},
            {"plant": "Gerald Andrus retime 2035->2028", "change": "retime",
             "mw": 781.4},
            {"plant": "Legend Power Station (new gas)", "change": "add",
             "mw": 754.0},
            {"plant": "Steel River Solar Phase 3 retime 2030->2029",
             "change": "retime", "mw": 750.0},
            {"plant": "Fermi 2 uprate", "change": "add", "mw": 177.0},
        ],
        "not_added_flagged_candidates_mw": {
            "Vista Sands 300 MW BESS (in PSC approval; MW/date split unverified)": 300.0,
            "Constellation-Google nuclear uprates (MISO share of ~890 MW unknown)": 890.0,
            "R.S. Nelson Unit 6 coal retirement (~615 MW, 2028?, unverified)": 615.0,
            "White Bluff coal (retire vs convert to gas peaking unresolved)": None,
            "Schahfer-site CCGT + data center (advocacy claim 2,300 MW, unverified)": 2300.0,
            "Schahfer Units 17/18 coal (kept Dec 2026 in v2; high delay risk, DOE orders)": 847.0,
        },
        "coordinator_arithmetic_note": (
            "The v2 researcher's year-by-year table double-counted Belle "
            "River's coal retirement as a NEW retirement; it is a retime "
            "(v1 already had it, Dec 2028 -> Dec 2026). Correct net 2036 "
            "effect is +6,340.0 MW (Gas +8,566.8; Coal -2,403.8; Nuclear "
            "+177.0), not +4,945.0 MW; correct 2028 flow delta is +548.2 MW, "
            "not -846.8 MW. Asserted in the build."),
        "files": {
            "manual_adjustments": "manual_adjustments.csv",
            "plants_v2": "miso_capacity_plants_v2.csv",
            "stack_v2": "miso_capacity_stack_v2.csv",
            "stack_by_region_v2": "miso_capacity_stack_by_region_v2.csv",
            "changelog_v2": "miso_capacity_changelog_v2.csv",
            "changelog_by_region_v2": "miso_capacity_changelog_by_region_v2.csv",
            "summary_v2": "summary_v2.json",
            "research_log": "research_log.md",
            "readme_v2": "README_v2.md",
            "charts": ["01_stacked_area_v2.png", "02_net_change_forward_v2.png",
                       "03_regions_stacked_v2.png", "04_regional_totals_v2.png"],
        },
    }
    with open(BASE / "summary_v2.json", "w") as f:
        json.dump(summary, f, indent=2)
    print("  wrote manual_adjustments.csv, plants/changelog/stack v2 CSVs, "
          "summary_v2.json")

    # Wide frames for charts.
    wide = stack2.pivot(index="year", columns="fuel", values="mw").reset_index()
    wide_r = stack2r.pivot_table(index="year", columns=["region", "fuel"],
                                 values="mw").reset_index()
    return wide, wide_r, chg2, stack2, stack2r


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
    ax.text(2025.95, bottom.max() * 0.97, "Today (Nov 2026)\nanchor Dec 31, 2025",
            fontsize=9, va="top")
    ax.set_xlim(2016, 2036)
    ax.set_ylabel("Installed capacity (GW)")
    ax.set_xlabel("Year (Dec 31 position; 2026-2036 = anchor + v2 changelog)")
    ax.set_title("MISO generation capacity stack by fuel, 2016-2036 — v2\n"
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
    ax.set_title("MISO annual net capacity change by fuel, forward 2026-2036 — v2\n"
                 "(EIA-860M + manual additions/retirements, nameplate)", fontsize=11)
    ax.legend(ncol=2, fontsize=9, loc="upper right")
    ax.grid(True, alpha=0.3, axis="y")
    fig.tight_layout()
    fig.savefig(BASE / "02_net_change_forward_v2.png", dpi=150)
    plt.close(fig)

    fig, axes = plt.subplots(3, 1, figsize=(12, 13), sharex=True)
    for ax, rg in zip(axes, REGIONS):
        bottom = np.zeros(len(years))
        for f in STACK_ORDER:
            vals = wide_r[(rg, f)].values / 1000.0
            ax.fill_between(years, bottom, bottom + vals,
                            label=f, color=FUEL_COLORS[f], alpha=0.9)
            bottom += vals
        ax.axvline(2025.9, color="black", linestyle="--", linewidth=1.2)
        ax.set_ylabel("GW")
        ax.set_title(f"MISO {rg} — capacity stack by fuel, 2016-2036 (GW) — v2",
                     fontsize=11)
        ax.grid(True, alpha=0.3)
        ax.legend(ncol=5, fontsize=8, loc="upper left")
    axes[-1].set_xlabel("Year (Dec 31 position)")
    fig.tight_layout()
    fig.savefig(BASE / "03_regions_stacked_v2.png", dpi=150)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(12, 6))
    for rg in REGIONS:
        ax.plot(years, wide_r[(rg, "Total")].values / 1000.0,
                label=rg, color=REGION_COLORS[rg], linewidth=2)
    ax.plot(years, wide["Total"].values / 1000.0,
            label="MISO total", color="black", linewidth=2, linestyle="--")
    ax.axvline(2025.9, color="black", linestyle="--", linewidth=1.2)
    ax.set_ylabel("Installed capacity (GW)")
    ax.set_xlabel("Year (Dec 31 position)")
    ax.set_title("MISO capacity by region, 2016-2036 — v2", fontsize=11)
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(BASE / "04_regional_totals_v2.png", dpi=150)
    plt.close(fig)
    print("  charts written")


if __name__ == "__main__":
    w, wr, c2, s2, s2r = main()
    make_charts(w, wr, c2)
