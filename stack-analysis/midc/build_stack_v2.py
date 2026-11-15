#!/usr/bin/env python3
"""Build MIDC capacity stack v2 — EIA + manual corrections.

Mirrors ~/workspace/miso-capacity-stack/build_stack_v2.py: reads the v1
files, verifies v1 reproduces (anchor + v1 changelog), applies manual
corrections, rebuilds the changelog and stack, and writes v2 files
alongside (v1 files are never overwritten).

Corrections (2 named adjustments, 3 row-level changes; see
research_log.md for the evidence and per-item confidence):
  A  FUEL SWITCH TransAlta Centralia Generation Unit 2, WA,
     coal -> gas, 729.9 MW. EIA carries NO retirement and NO conversion
     for the unit. Coal burn ceased end-Dec 2025 (WA law / 2011
     TransAlta MOA); DOE FPA 202(c) emergency orders hold the unit
     available as coal through Dec 12, 2026 with zero generation, so
     the coal retirement is booked Dec 2026 (anchor-boundary treatment,
     cf. MISO v2 Belle River). The gas conversion (TransAlta-PSE
     16-year tolling agreement, Dec 9, 2025; 700 MW contracted, 723 MW
     max net per the Jul 31, 2026 SEPA MDNS; ~$600m; FID early 2027)
     is booked as a gas addition at the EIA nameplate 729.9 MW in
     Dec 2028 (target COD late 2028), cf. MISO v2 fuel switches, which
     kept nameplate MW unchanged across the switch.
  B  ADD Columbia Generating Station extended power uprate, WA,
     nuclear, +186.0 MW (162 MW EPU + 24 MW efficiency), Dec 2031.
     BPA approved implementation May 2025 (~$700m); staged across the
     2027/2029/2031 refuelling outages and booked at completion; NRC
     licence amendment request to be submitted 2028; plant licensed
     through 2043. Not in the EIA Planned sheet.

Checked with NO adjustment (evidence in research_log.md):
  - Colstrip Units 3/4, MT, coal, 1,647.4 MW: NO retirement added.
    PSE (25%) and Avista (15%) transferred their shares to
    NorthWestern Energy effective Jan 1, 2026 (WA UTC Final Order 05,
    Docket UE-240729, treats the transfer as PSE's CETA "retirement"
    from Washington supply — an ownership exit, not a unit shutdown);
    NorthWestern (now ~55%) states it will operate the units to
    ~2042 (MT DEQ Rosebud AM5 EA, Jan 2026, uses 2042). PGE plans to
    exit its 20% by end-2029 and PacifiCorp its 10% around 2030 —
    ownership exits, not retirements. EIA carries no retirement date;
    v1 and v2 agree.
  - Every EIA Planned unit >= 200 MW was web-checked (Sunstone,
    Deschutes, Cedar Island, Haymaker, Hop Hill, Blacks Creek,
    Obsidian, Nolin Hills, Lower Snake, Royal Slope, Salmonfly, Arco,
    Centralia BESS, Greenwater, Tualatin, Anthelope Hills): all kept
    at EIA MW/date, several with paper-project / slip-risk flags.
  - Behind-the-meter scan: no >= 200 MW BTM exclusion found. The only
    quantified BTM generation is the 12 MW VoltaGrid mobile gas plant
    at the Vantage data-center campus in Quincy, WA (Grant PUD,
    Jan 2026; temporary bridge to 2029) — below the large-plant
    threshold, not in EIA, and 0 MW under the BTM rule in any case.
    Sunstone (Amazon-owned after the Pine Gate bankruptcy) and Blacks
    Creek (Meta/Kuna PPA via Idaho Power) are grid-connected plants
    serving data-center load through the grid — counted in full, per
    the standing rule (cf. MISO v2 Meta/Entergy).

Expected yearly FLOW deltas (v2 net changelog - v1 net changelog):
2026 -729.9 (Centralia coal out); 2028 +729.9 (Centralia gas in);
2031 +186.0 (Columbia uprate); all other years 0. Cumulative +186.0 MW.
The build asserts these.
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
EXPECTED_FLOW_DELTA = {
    2026: -729.9, 2027: 0.0, 2028: 729.9, 2029: 0.0, 2030: 0.0,
    2031: 186.0, 2032: 0.0, 2033: 0.0, 2034: 0.0, 2035: 0.0, 2036: 0.0,
}

# ---------------- Manual corrections ----------------
# EDITS: (plant_name exact, generator_id, new_mw, new_eff (y, mo),
#         new_status, note, source, source_url, confidence)
# No retimes in MIDC v2: every large EIA forward unit checked was kept
# at its EIA date (see research_log.md KEEP list).
EDITS = []

# NEW_ROWS: (plant_name, generator_id, plant_id, state, region, fuel,
#            mw, year, month, type, status, source_sheet, note,
#            source, source_url, confidence)
NEW_ROWS = [
    # A1. Centralia coal retirement (EIA has no planned retirement)
    ("Transalta Centralia Generation", "2", 3845, "WA", "MIDC", "Coal",
     729.9, 2026, 12, "retirement", "manual addition (v2)",
     "TransAlta-PSE tolling agreement Dec 9, 2025; SEPA MDNS Jul 31, 2026",
     "ADD coal retirement: Unit 2 ceased coal burn end-Dec 2025 (WA law / "
     "2011 TransAlta MOA; last coal burned Dec 2025, zero generation "
     "since). DOE FPA 202(c) emergency orders hold it available as coal "
     "through Dec 12, 2026, so the retirement is booked Dec 2026 at the "
     "anchor boundary (cf. MISO v2 Belle River). EIA carries no planned "
     "retirement for the unit.",
     "TransAlta Form 6-K Dec 9, 2025; WA Ecology/SWCAA SEPA MDNS Jul 31, 2026",
     "http://pdf.secdatabase.com/1333/0001171843-25-007842.pdf",
     "Medium-High"),
    # A2. Centralia gas addition (fuel switch)
    ("Transalta Centralia Generation (gas conversion)", "2", 3845, "WA",
     "MIDC", "Natural Gas",
     729.9, 2028, 12, "addition", "manual addition (v2)",
     "TransAlta-PSE tolling agreement Dec 9, 2025; SEPA MDNS Jul 31, 2026",
     "ADD gas (fuel switch): 16-year fixed-price tolling agreement with "
     "Puget Sound Energy (signed Dec 9, 2025) converts Unit 2 to natural "
     "gas; 700 MW contracted capacity, 723 MW maximum net per the SEPA "
     "MDNS; ~$600m capex; target COD late 2028 (booked Dec 2028); FID "
     "expected early 2027 after WUTC approval; operates to end-2044. "
     "Booked at the EIA nameplate 729.9 MW (stack basis is nameplate; "
     "cf. MISO v2 fuel switches, which kept nameplate unchanged).",
     "TransAlta Form 6-K Dec 9, 2025; WA Ecology/SWCAA SEPA MDNS Jul 31, 2026",
     "https://www.swcleanair.gov/docs/SEPA/Determinations/2026-07-31 TransAlta Generation - Ecology SEPA MDNS Determination.pdf",
     "Medium-High"),
    # B. Columbia Generating Station extended power uprate
    ("Columbia Generating Station", "2", 371, "WA", "MIDC", "Nuclear",
     186.0, 2031, 12, "addition", "manual addition (v2)",
     "BPA approval of EPU implementation, May 2025",
     "ADD (uprate): Extended Power Uprate +186 MW (162 MW EPU + 24 MW "
     "energy-efficiency upgrades), ~$700m, approved for implementation "
     "by BPA May 2025 after 18 months of analysis. Staged across the "
     "2027/2029/2031 refuelling outages (~30 modifications); booked at "
     "completion, Dec 2031. NRC licence amendment request to be "
     "submitted 2028. Plant licensed through 2043; subsequent licence "
     "renewal planned. Not in the EIA Planned sheet. (Operator states "
     "current output 1,207 MW vs EIA nameplate 1,200.0 MW; the uprate "
     "increment is unaffected.)",
     "ANS Nuclear Newswire Oct 1, 2026; POWER Magazine May 23, 2025",
     "https://www.ans.org/news/2026-10-01/article-8410/modernizing-for-more-megawatts-columbias-epu-journey/",
     "Medium-High"),
]


def main():
    plants = pd.read_csv(BASE / "midc_capacity_plants.csv")
    stack_v1 = pd.read_csv(BASE / "midc_capacity_stack.csv")
    chg_v1 = pd.read_csv(BASE / "midc_capacity_changelog.csv")
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
        "state": st, "county": "", "region": rg,
        "balancing_authority": "BPAT", "fuel": fu,
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
             "corrections: Centralia coal-to-gas fuel switch, Columbia "
             "Generating Station extended power uprate)")
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
            "source_date": "2026-11-15", "date_accessed": "2026-11-15",
        })
    for (pn, gid, _pid, st, rg, fu, mw, yr, mo, typ, _status, _ss, note,
         s, u, c) in NEW_ROWS:
        if typ == "addition":
            ct = ("add (fuel switch)" if "gas conversion" in pn else "add")
        else:
            ct = "add retirement (fuel switch)"
        adj_rows.append({
            "plant": pn, "unit": str(gid), "state": st, "region": rg,
            "fuel": fu, "v1_mw": "", "v1_date": "",
            "v2_mw": float(mw), "v2_date": f"{yr:04d}-{mo:02d}",
            "change_type": ct, "reason": note,
            "classification": "manual correction",
            "source": s, "source_url": u, "confidence": c,
            "source_date": "2026-11-15", "date_accessed": "2026-11-15",
        })
    adj = pd.DataFrame(adj_rows)
    adj.to_csv(BASE / "manual_adjustments.csv", index=False)
    p2.to_csv(BASE / "midc_capacity_plants_v2.csv", index=False)
    stack2.to_csv(BASE / "midc_capacity_stack_v2.csv", index=False)
    chg2.to_csv(BASE / "midc_capacity_changelog_v2.csv", index=False)

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
        "named_adjustments_count": 2,
        "largest_manual_changes_mw": [
            {"plant": "Transalta Centralia Generation Unit 2 coal retirement (fuel switch)",
             "change": "add retirement", "mw": 729.9},
            {"plant": "Transalta Centralia Generation Unit 2 gas conversion (fuel switch)",
             "change": "add", "mw": 729.9},
            {"plant": "Columbia Generating Station extended power uprate",
             "change": "add", "mw": 186.0},
        ],
        "checked_no_adjustment": {
            "Colstrip Units 3/4 coal (1,647.4 MW)": "No retirement added. "
                "PSE/Avista shares transferred to NorthWestern Jan 1, 2026 "
                "(ownership exit under WA CETA, not a shutdown); operator "
                "intends operation to ~2042. PGE exit by end-2029 and "
                "PacifiCorp exit ~2030 are ownership exits, not retirements.",
        },
        "not_added_flagged_candidates_mw": {
            "Cascade Advanced Energy Facility SMR, initial 4x80 MW phase (Energy Northwest/X-energy/Amazon; pre-application, construction permit application targeted end-2026, operations 2030s)": 320.0,
            "Cascade Advanced Energy Facility SMR, full 12-unit build-out": 960.0,
            "Badger Mountain Pumped Storage, WA (500 MW, planning/development per WA PEIS)": 500.0,
            "Haymaker Hybrid wind, MT (kept at EIA 630 MW Oct 2031; Clearway/PSE 25-yr PPA describes a 315 MW facility with COD by 2028 — MW and date conflict, unverified)": 630.0,
            "Obsidian Solar Center, OR (kept at EIA Dec 2028; EFSC extended construction-start deadline to Feb 25, 2028 after the original was missed for lack of interconnection — completion can run 3 years from commencement, slip risk)": 400.0,
            "Colstrip Units 3/4, MT (kept operating in v2; no retirement in window — see checked_no_adjustment)": 1647.4,
            "VoltaGrid BTM gas at Vantage Quincy data-center campus, WA (12 MW mobile, temporary bridge to 2029; not in EIA; counts 0 under the BTM rule)": 12.0,
            "Puget Sound Energy undisclosed-site gas turbines for data-center load (reported via Sightline/Riverkeeper; MW and site undisclosed)": None,
        },
        "btm_scan_finding": "No behind-the-meter exclusion >= 200 MW found. "
            "Sunstone Solar (Amazon-owned via Pine Gate Chapter 11, Feb 2026) "
            "and Blacks Creek Solar (Meta Kuna data-center PPA via Idaho "
            "Power) are grid-connected plants serving data-center load "
            "through the grid and are counted in full. The only quantified "
            "BTM generation is VoltaGrid's 12 MW temporary mobile gas plant "
            "at Quincy, WA (0 MW under the rule; immaterial, not in EIA).",
        "files": {
            "manual_adjustments": "manual_adjustments.csv",
            "plants_v2": "midc_capacity_plants_v2.csv",
            "stack_v2": "midc_capacity_stack_v2.csv",
            "changelog_v2": "midc_capacity_changelog_v2.csv",
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
    ax.set_title("MIDC generation capacity stack by fuel, 2016-2036 — v2\n"
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
    ax.set_title("MIDC annual net capacity change by fuel, forward 2026-2036 — v2\n"
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
