#!/usr/bin/env python3
"""Build MISO capacity stack v1 — EIA-only, regionalized.

Mirrors the PJM v1 method (~/workspace/pjm-capacity-stack/build_stack.py):
trailing + forward 10-year stack 2016-2036 by fuel (Coal, Natural Gas,
Nuclear, Hydro, Pumped Storage, Wind, Solar, Oil, Battery Storage, Other),
nameplate MW throughout, anchor Dec 31 2025, forward = anchor + changelog.

MISO differences from PJM (documented, not hidden):
- Anchor: NO clean external anchor by fuel exists for MISO. Potomac
  Economics' 2025 State of the Market publishes exact MW by fuel only in
  UCAP (Table 1) and ICAP only as shares (Figure 34); MISO's Fact Sheet
  gives a 207 GW total with whole-percent shares, inconsistent with the
  SOM's own wind/solar nameplate figures. Per the task brief, the anchor
  is therefore the EIA-860M Operating-sheet snapshot, adjusted to
  Dec 31 2025 (minus units in service Jan-Sep 2026, plus 2026 retired
  actuals), nameplate MW, all statuses. It is EIA-derived, stated
  explicitly; the SOM-derived ~180 GW ICAP cross-check is in summary.json
  and README.md. Do NOT present the anchor as a MISO/IMM publication.
- Trailing 2016-2025: no published ICAP-by-fuel history exists, so the
  trailing is RECONSTRUCTED from EIA unit-level data (Operating Year and
  Retirement Year), labelled estimated. It is not a MISO publication.
- Regionalization: MISO North / Central / South subregions, LRZ-based
  (resource-adequacy/operations definition — NOT the four-way MTEP
  planning regions West/Central/East/South). North = LRZ 1+3, Central =
  LRZ 2+4+5+6+7, South = LRZ 8+9+10. Plants are assigned by state, with
  Wisconsin split by Local Balancing Authority (entity) then county,
  because western WI is North (LRZ 1) and eastern/northern WI is Central
  (LRZ 2). Every regional total is asserted to sum to the MISO total.
- No RMR-style override: the PJM coal-delay-to-Jan-2029 override was a
  user-directed scenario, not a general rule. MISO coal retirements are
  taken at their EIA dates; any that look RMR-extended are flagged in
  the research log, not re-dated.

Changelog source: EIA-860M September 2026 vintage (data as of Sep 30, 2026;
released Oct 23, 2026), Balancing Authority Code == MISO, same file the
PJM stack used: ~/workspace/pjm-capacity-stack/raw/eia860m_sep2026.xlsx
(also copied to raw/ here).
Additions: units in service in 2026 (Operating sheet, Operating Year
== 2026) + Planned sheet units, Planned Operation Year 2026-2031.
Retirements: Retired sheet actuals with Retirement Year == 2026 +
Operating sheet planned retirements, Planned Retirement Year 2026-2036.

The build asserts: (1) snapshot(2025) == anchor exactly (internal
consistency of the trailing reconstruction); (2) regional stacks sum to
the MISO total every year and fuel; (3) forward stack == anchor +
cumulative changelog.
"""
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd

BASE = Path(__file__).resolve().parent
RAW = BASE / "raw"
EIA_FILE = Path("/home/hatch/workspace/pjm-capacity-stack/raw/eia860m_sep2026.xlsx")
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

# ---------------- Regions ----------------
# LRZ-based subregions (resource-adequacy/operations definition):
#   North = LRZ 1 + 3; Central = LRZ 2 + 4 + 5 + 6 + 7; South = LRZ 8 + 9 + 10.
# State mapping (MISO portion only). Sources: MISO CarbonFlow Table 5
# (LBA->LRZ->Subregion); MISO Apr 2026 Long-Term Load Forecast White Paper
# (per-LRZ state descriptors); MISO Phase III Clean Power Plan analysis §4.3.
STATE_TO_REGION = {
    # North (LRZ 1, 3)
    "ND": "North", "SD": "North", "MN": "North", "IA": "North",
    "MT": "North",   # eastern MT sliver only (MDU, LRZ 1)
    # Central (LRZ 2, 4, 5, 6, 7)
    "MI": "Central", "IL": "Central", "MO": "Central", "IN": "Central",
    "KY": "Central",
    # South (LRZ 8, 9, 10)
    "AR": "South", "LA": "South", "MS": "South", "TX": "South",  # eastern TX only
}
# Wisconsin is split: western WI = LRZ 1 (North), eastern/northern WI =
# LRZ 2 (Central). Assign by Local Balancing Authority via Entity Name
# first (LBA lists from Tariff Attachment VV / CarbonFlow Table 5), then
# by county for entities not in the LBA lists (IPPs etc.).
WI_LRZ1_ENTITIES = {  # LRZ 1 LBAs: DPC, GRE, MDU, MP, NSP, OTP, SMP
    "Dairyland Power Coop",
    "Northern States Power Co - Minnesota",
    "Northern States Power Co - Wisconsin",
    "Great River Energy",
    "Otter Tail Power Co",
    "Montana-Dakota Utilities Co",
    "Minnesota Power",
    "Southern Minnesota Municipal Power Agency",
}
WI_LRZ2_ENTITIES = {  # LRZ 2 LBAs: ALTE, MGE, MIUP, UPPC, WEC, WPS
    "Wisconsin Electric Power Co",
    "Wisconsin Public Service Corp",
    "Wisconsin Power & Light Co",
    "Madison Gas & Electric Co",
    "Upper Michigan Energy Resources Corp",
    "Alliant Energy",
}
# Fallback counties for WI plants whose entity is in neither list:
# northwestern/western WI (NSP/Dairyland territory) -> North, rest -> Central.
WI_NORTH_COUNTIES = {
    "Buffalo", "Trempealeau", "La Crosse", "Vernon", "Monroe", "Jackson",
    "Crawford", "Chippewa", "Eau Claire", "Dunn", "Pepin", "Pierce",
    "St. Croix", "Polk", "Barron", "Rusk", "Burnett", "Washburn",
    "Sawyer", "Douglas", "Bayfield", "Ashland", "Price", "Taylor", "Iron",
}
# Plant-level overrides where the owner's LBA disagrees with the plant's
# location in the transmission system (LRZ follows location, not owner).
# RockGen Energy Center (3x187 MW gas, Dane County, owned by Dairyland
# Power Coop, an LRZ-1 LBA) sits in Alliant (ALTE) service territory around
# Cambridge, WI — LRZ 2, Central. 561 MW. This is the only such case in
# the BA=MISO Operating sheet.
WI_OVERRIDES = {
    ("RockGen Energy Center", "Dane"): "Central",
}


def region_of(row):
    """LRZ-based subregion for one EIA plant row."""
    st = row["Plant State"]
    if st == "WI":
        ov = WI_OVERRIDES.get(
            (str(row.get("Plant Name", "")).strip(),
             str(row.get("County", "")).strip()))
        if ov:
            return ov
        ent = str(row.get("Entity Name", "")).strip()
        if ent in WI_LRZ1_ENTITIES:
            return "North"
        if ent in WI_LRZ2_ENTITIES:
            return "Central"
        county = str(row.get("County", "")).strip()
        return "North" if county in WI_NORTH_COUNTIES else "Central"
    if st in STATE_TO_REGION:
        return STATE_TO_REGION[st]
    raise ValueError(f"No MISO region mapping for state {st!r} "
                     f"(plant {row.get('Plant Name')})")


def wi_assignment_diagnostics(miso_op):
    """How much WI capacity was assigned by each rule (MW, units)."""
    wi = miso_op[miso_op["Plant State"] == "WI"].copy()
    out = {"wi_total_mw": round(wi["Nameplate Capacity (MW)"].sum(), 1),
           "wi_total_units": int(len(wi))}
    wi["rule"] = "county fallback"
    wi.loc[wi["Entity Name"].isin(WI_LRZ1_ENTITIES), "rule"] = "entity LRZ1"
    wi.loc[wi["Entity Name"].isin(WI_LRZ2_ENTITIES), "rule"] = "entity LRZ2"
    ov_mask = wi.apply(
        lambda r: (str(r["Plant Name"]).strip(), str(r["County"]).strip())
        in WI_OVERRIDES, axis=1)
    wi.loc[ov_mask, "rule"] = "plant override"
    for rule in ["entity LRZ1", "entity LRZ2", "plant override",
                 "county fallback"]:
        sub = wi[wi["rule"] == rule]
        out[f"wi_{rule.replace(' ', '_')}_mw"] = round(
            sub["Nameplate Capacity (MW)"].sum(), 1)
        out[f"wi_{rule.replace(' ', '_')}_units"] = int(len(sub))
    # Fallback split, by region.
    fb = wi[wi["rule"] == "county fallback"]
    for rg in REGIONS:
        sub = fb[fb.apply(region_of, axis=1) == rg]
        out[f"wi_county_fallback_{rg.lower()}_mw"] = round(
            sub["Nameplate Capacity (MW)"].sum(), 1)
    return out


# ---------------- EIA-860M ----------------
COAL_ESC = {"ANT", "BIT", "LIG", "SUB", "WC"}
OIL_ESC = {"DFO", "RFO", "JF", "KER", "PC"}


def eia_fuel(row):
    esc, pm = row["Energy Source Code"], row["Prime Mover Code"]
    if pm in ("BA", "FW"):
        return "Battery Storage"
    if pm == "PS":
        return "Pumped Storage"
    if esc == "NUC":
        return "Nuclear"
    if esc == "SUN":
        return "Solar"
    if esc == "WND":
        return "Wind"
    if esc == "WAT":
        return "Hydro"
    if esc == "NG":
        return "Natural Gas"
    if esc in COAL_ESC:
        return "Coal"
    if esc in OIL_ESC:
        return "Oil"
    return "Other"


def load_eia_sheet(name):
    df = pd.read_excel(EIA_FILE, sheet_name=name, header=2)
    for c in ["Nameplate Capacity (MW)", "Net Summer Capacity (MW)",
              "Net Winter Capacity (MW)"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df


def _plant_row(r, typ, status_label, year, month, source, region):
    """One unit-level changelog row from an EIA-860M record."""
    return {
        "plant_name": r["Plant Name"],
        "plant_id": r["Plant ID"],
        "generator_id": str(r["Generator ID"]),
        "state": r["Plant State"],
        "county": r.get("County", ""),
        "region": region,
        "balancing_authority": r["Balancing Authority Code"],
        "fuel": r["fuel"],
        "energy_source_code": r["Energy Source Code"],
        "prime_mover_code": r["Prime Mover Code"],
        "technology": r.get("Technology", ""),
        "mw_nameplate": round(float(r["Nameplate Capacity (MW)"]), 1),
        "mw_net_summer": (round(float(r["Net Summer Capacity (MW)"]), 1)
                          if pd.notna(r.get("Net Summer Capacity (MW)"))
                          else None),
        "type": typ,
        "status": r.get("Status", status_label),
        "retirement_status": status_label,
        "source_sheet": source,
        "original_year": year,
        "original_month": month,
        "original_date": f"{year:04d}-{month:02d}",
        "effective_year": year,
        "effective_month": month,
        "effective_date": f"{year:04d}-{month:02d}",
    }


# ---------------- Anchor (EIA-derived, Dec 31 2025) ----------------
def build_anchor(op, rt):
    """Anchor = EIA Operating snapshot adjusted to Dec 31, 2025.

    Operating sheet as of Sep 30, 2026, minus units in service in 2026,
    plus Retired-sheet actual retirements in 2026 (those units were
    operating at Dec 31, 2025). Nameplate MW, all statuses. Returns
    (anchor_by_fuel, anchor_by_region_fuel, diagnostics).
    """
    diag = {}
    miso_op = op[op["Balancing Authority Code"] == "MISO"].copy()
    miso_rt = rt[rt["Balancing Authority Code"] == "MISO"].copy()
    diag["eia_operating_miso_units"] = int(len(miso_op))
    diag["eia_operating_miso_nameplate_mw"] = round(
        miso_op["Nameplate Capacity (MW)"].sum(), 1)
    diag["eia_operating_miso_netsummer_mw"] = round(
        miso_op["Net Summer Capacity (MW)"].sum(), 1)
    op_only = miso_op[miso_op["Status"] == "(OP) Operating"]
    diag["eia_operating_miso_op_only_nameplate_mw"] = round(
        op_only["Nameplate Capacity (MW)"].sum(), 1)
    diag["eia_operating_miso_op_only_netsummer_mw"] = round(
        op_only["Net Summer Capacity (MW)"].sum(), 1)
    diag["eia_operating_miso_nonop_nameplate_mw"] = round(
        miso_op[miso_op["Status"] != "(OP) Operating"]
        ["Nameplate Capacity (MW)"].sum(), 1)
    diag["eia_operating_miso_by_fuel_nameplate"] = {
        f: round(v, 1) for f, v in
        miso_op.groupby("fuel")["Nameplate Capacity (MW)"].sum().items()}
    diag["eia_operating_miso_by_fuel_netsummer"] = {
        f: round(v, 1) for f, v in
        miso_op.groupby("fuel")["Net Summer Capacity (MW)"].sum().items()}

    # BA boundary cross-check: MW in MISO-footprint states under other BAs.
    miso_states = ["ND", "SD", "MN", "WI", "MI", "IA", "IL", "IN", "MO",
                   "KY", "AR", "LA", "MS", "TX", "MT"]
    in_states = op[op["Plant State"].isin(miso_states)]
    out_ba = in_states[in_states["Balancing Authority Code"] != "MISO"]
    diag["ba_boundary_in_footprint_states_not_miso_mw"] = round(
        out_ba["Nameplate Capacity (MW)"].sum(), 1)
    diag["ba_boundary_in_footprint_states_not_miso_units"] = int(len(out_ba))
    diag["ba_boundary_in_footprint_states_not_miso_by_ba_mw"] = {
        k: round(v, 1) for k, v in
        out_ba.groupby("Balancing Authority Code")
        ["Nameplate Capacity (MW)"].sum().items()}
    ba_out = miso_op[~miso_op["Plant State"].isin(miso_states)]
    diag["ba_boundary_miso_ba_outside_footprint_mw"] = round(
        ba_out["Nameplate Capacity (MW)"].sum(), 1)
    diag["ba_boundary_miso_ba_outside_footprint_units"] = int(len(ba_out))
    diag["ba_boundary_miso_ba_outside_footprint_states"] = sorted(
        ba_out["Plant State"].unique().tolist())

    # Adjustment to Dec 31, 2025.
    in_service_2026 = miso_op[pd.to_numeric(
        miso_op["Operating Year"], errors="coerce") == 2026]
    rt26 = miso_rt[pd.to_numeric(
        miso_rt["Retirement Year"], errors="coerce") == 2026]
    diag["anchor_less_in_service_2026_mw"] = round(
        in_service_2026["Nameplate Capacity (MW)"].sum(), 1)
    diag["anchor_less_in_service_2026_units"] = int(len(in_service_2026))
    diag["anchor_less_in_service_2026_by_fuel"] = {
        f: round(v, 1) for f, v in
        in_service_2026.groupby("fuel")["Nameplate Capacity (MW)"]
        .sum().items()}
    diag["anchor_plus_retired_2026_mw"] = round(
        rt26["Nameplate Capacity (MW)"].sum(), 1)
    diag["anchor_plus_retired_2026_units"] = int(len(rt26))
    diag["anchor_plus_retired_2026_by_fuel"] = {
        f: round(v, 1) for f, v in
        rt26.groupby("fuel")["Nameplate Capacity (MW)"].sum().items()}

    base = miso_op[pd.to_numeric(
        miso_op["Operating Year"], errors="coerce") <= 2025].copy()
    anchor_by_fuel = {
        f: round(base[base["fuel"] == f]["Nameplate Capacity (MW)"].sum()
                 + rt26[rt26["fuel"] == f]["Nameplate Capacity (MW)"].sum(), 1)
        for f in FUELS}
    anchor_total = round(sum(anchor_by_fuel.values()), 1)
    # Region split of the anchor.
    base["region"] = base.apply(region_of, axis=1)
    rt26 = rt26.copy()
    rt26["region"] = rt26.apply(region_of, axis=1)
    anchor_by_region_fuel = {}
    for rg in REGIONS:
        for f in FUELS:
            anchor_by_region_fuel[(rg, f)] = round(
                base[(base["region"] == rg) & (base["fuel"] == f)]
                ["Nameplate Capacity (MW)"].sum()
                + rt26[(rt26["region"] == rg) & (rt26["fuel"] == f)]
                ["Nameplate Capacity (MW)"].sum(), 1)
    # Regional sums must equal the fuel totals.
    for f in FUELS:
        s = round(sum(anchor_by_region_fuel[(rg, f)] for rg in REGIONS), 1)
        assert abs(s - anchor_by_fuel[f]) < 0.05, (f, s, anchor_by_fuel[f])
    diag["anchor_total_mw"] = anchor_total
    diag["anchor_by_fuel_mw"] = anchor_by_fuel
    diag["anchor_by_region_mw"] = {
        rg: round(sum(anchor_by_region_fuel[(rg, f)] for f in FUELS), 1)
        for rg in REGIONS}
    return anchor_by_fuel, anchor_by_region_fuel, diag, base, rt26


# ---------------- Trailing (reconstructed from EIA unit data) ----------------
def trailing_reconstructed(op, rt):
    """Dec-31 snapshots 2016-2025 reconstructed from EIA unit-level data.

    For year Y: Operating-sheet units with Operating Year <= Y, plus
    Retired-sheet units with Operating Year <= Y < Retirement Year.
    Planned Retirement Year is deliberately NOT used: it reflects plans
    as of Sep 2026, not history (a slipped plan would wrongly remove a
    unit from earlier snapshots). Labelled estimated in the outputs.
    Returns (DataFrame year x fuel x region, notes dict).
    """
    miso_op = op[op["Balancing Authority Code"] == "MISO"].copy()
    miso_rt = rt[rt["Balancing Authority Code"] == "MISO"].copy()
    miso_op["region"] = miso_op.apply(region_of, axis=1)
    miso_rt["region"] = miso_rt.apply(region_of, axis=1)
    miso_op["_oy"] = pd.to_numeric(miso_op["Operating Year"], errors="coerce")
    miso_rt["_oy"] = pd.to_numeric(miso_rt["Operating Year"], errors="coerce")
    miso_rt["_ry"] = pd.to_numeric(miso_rt["Retirement Year"], errors="coerce")
    assert miso_op["_oy"].notna().all(), "Operating Year missing on Operating"
    assert miso_rt["_oy"].notna().all(), "Operating Year missing on Retired"
    assert miso_rt["_ry"].notna().all(), "Retirement Year missing on Retired"
    rows = []
    for y in range(2016, 2026):
        snap_op = miso_op[miso_op["_oy"] <= y]
        snap_rt = miso_rt[(miso_rt["_oy"] <= y) & (miso_rt["_ry"] > y)]
        snap = pd.concat([snap_op, snap_rt], ignore_index=True)
        r = {"year": y, "period": "trailing",
             "source_note": "EIA-860M reconstructed Dec-31 snapshot "
                            "(unit Operating Year / Retirement Year). Estimated."}
        for f in FUELS:
            r[f] = round(
                snap[snap["fuel"] == f]["Nameplate Capacity (MW)"].sum(), 1)
        r["Total"] = round(snap["Nameplate Capacity (MW)"].sum(), 1)
        for rg in REGIONS:
            for f in FUELS:
                r[f"{rg} {f}"] = round(
                    snap[(snap["region"] == rg) & (snap["fuel"] == f)]
                    ["Nameplate Capacity (MW)"].sum(), 1)
            r[f"{rg} Total"] = round(
                snap[snap["region"] == rg]["Nameplate Capacity (MW)"].sum(), 1)
        rows.append(r)
    return pd.DataFrame(rows)


# ---------------- Forward changelog (EIA) ----------------
def eia_changelog(op, pl, rt):
    """Forward changelog from EIA-860M (BA == MISO). No RMR override.

    Additions: units in service in 2026 (Operating, Operating Year == 2026)
    + Planned sheet units, Planned Operation Year 2026-2031.
    Retirements: Retired sheet actuals with Retirement Year == 2026 +
    Operating sheet planned retirements, Planned Retirement Year 2026-2036.
    Returns (changelog_df, changelog_by_region_df, plants_df, diagnostics).
    """
    miso_op = op[op["Balancing Authority Code"] == "MISO"].copy()
    miso_pl = pl[pl["Balancing Authority Code"] == "MISO"].copy()
    miso_rt = rt[rt["Balancing Authority Code"] == "MISO"].copy()
    miso_op["region"] = miso_op.apply(region_of, axis=1)
    miso_pl["region"] = miso_pl.apply(region_of, axis=1)
    miso_rt["region"] = miso_rt.apply(region_of, axis=1)

    diag = {}
    diag["eia_planned_miso_units"] = int(len(miso_pl))
    diag["eia_planned_miso_nameplate_mw"] = round(
        miso_pl["Nameplate Capacity (MW)"].sum(), 1)
    diag["eia_planned_miso_by_status_mw"] = {
        k: round(v, 1) for k, v in
        miso_pl.groupby("Status")["Nameplate Capacity (MW)"].sum().items()}
    diag["eia_planned_under_construction_mw"] = round(
        miso_pl[miso_pl["Status"].str.contains(
            "Under construction|Construction complete", na=False)]
        ["Nameplate Capacity (MW)"].sum(), 1)
    diag["eia_planned_max_operation_year"] = int(pd.to_numeric(
        miso_pl["Planned Operation Year"], errors="coerce").max())

    # ---- Additions ----
    adds = []
    in_service_2026 = miso_op[pd.to_numeric(
        miso_op["Operating Year"], errors="coerce") == 2026]
    for _, r in in_service_2026.iterrows():
        adds.append(_plant_row(
            r, "addition", "addition", int(r["Operating Year"]),
            int(pd.to_numeric(r["Operating Month"], errors="coerce") or 1),
            "Operating sheet: in service Jan-Sep 2026", r["region"]))
    for _, r in miso_pl.iterrows():
        y = pd.to_numeric(r["Planned Operation Year"], errors="coerce")
        m = pd.to_numeric(r["Planned Operation Month"], errors="coerce")
        if pd.isna(y):
            continue
        adds.append(_plant_row(r, "addition", "addition", int(y),
                               int(m) if not pd.isna(m) else 1,
                               "Planned sheet", r["region"]))
    adds_df = pd.DataFrame(adds)

    # ---- Retirements ----
    rets = []
    rt26 = miso_rt[pd.to_numeric(
        miso_rt["Retirement Year"], errors="coerce") == 2026]
    for _, r in rt26.iterrows():
        rets.append(_plant_row(
            r, "retirement", "retired (actual)",
            int(r["Retirement Year"]),
            int(pd.to_numeric(r["Retirement Month"], errors="coerce") or 1),
            "Retired sheet: actual Jan-Sep 2026", r["region"]))
    pr = miso_op[pd.to_numeric(
        miso_op["Planned Retirement Year"], errors="coerce").notna()].copy()
    for _, r in pr.iterrows():
        y = int(pd.to_numeric(r["Planned Retirement Year"], errors="coerce"))
        m = pd.to_numeric(r["Planned Retirement Month"], errors="coerce")
        rets.append(_plant_row(r, "retirement", "planned retirement", y,
                               int(m) if not pd.isna(m) else 1,
                               "Operating sheet: planned retirement",
                               r["region"]))
    rets_df = pd.DataFrame(rets)

    # Overlap guards (would double-count if > 0).
    key = lambda d: set(zip(d["Plant ID"].astype(str),
                            d["Generator ID"].astype(str)))
    diag["overlap_operating2026_vs_planned2026_units"] = len(
        key(in_service_2026) & key(miso_pl[
            miso_pl["Planned Operation Year"] == 2026]))
    diag["overlap_retired2026_vs_plannedret2026_units"] = len(
        key(rt26) & key(miso_op[pd.to_numeric(
            miso_op["Planned Retirement Year"], errors="coerce") == 2026]))

    plants = pd.concat([adds_df, rets_df], ignore_index=True)
    plants = plants.sort_values(["effective_year", "type", "fuel",
                                 "plant_name"])

    # ---- Changelog by year x fuel (MISO total) ----
    cl_rows = []
    for y in range(2026, 2037):
        for f in FUELS:
            a = adds_df[(adds_df["effective_year"] == y)
                        & (adds_df["fuel"] == f)]
            r = rets_df[(rets_df["effective_year"] == y)
                        & (rets_df["fuel"] == f)]
            cl_rows.append({
                "year": y, "fuel": f,
                "additions_mw": round(a["mw_nameplate"].sum(), 1),
                "additions_count": int(len(a)),
                "retirements_mw": round(r["mw_nameplate"].sum(), 1),
                "retirements_count": int(len(r)),
                "net_mw": round(a["mw_nameplate"].sum()
                                - r["mw_nameplate"].sum(), 1),
            })
    changelog = pd.DataFrame(cl_rows)
    # ---- Changelog by year x region x fuel ----
    clr_rows = []
    for y in range(2026, 2037):
        for rg in REGIONS:
            for f in FUELS:
                a = adds_df[(adds_df["effective_year"] == y)
                            & (adds_df["region"] == rg)
                            & (adds_df["fuel"] == f)]
                r = rets_df[(rets_df["effective_year"] == y)
                            & (rets_df["region"] == rg)
                            & (rets_df["fuel"] == f)]
                clr_rows.append({
                    "year": y, "region": rg, "fuel": f,
                    "additions_mw": round(a["mw_nameplate"].sum(), 1),
                    "additions_count": int(len(a)),
                    "retirements_mw": round(r["mw_nameplate"].sum(), 1),
                    "retirements_count": int(len(r)),
                    "net_mw": round(a["mw_nameplate"].sum()
                                    - r["mw_nameplate"].sum(), 1),
                })
    changelog_region = pd.DataFrame(clr_rows)
    diag["planned_total_mw_2026_2036"] = round(
        adds_df[adds_df["effective_year"].between(2026, 2036)]
        ["mw_nameplate"].sum(), 1)
    diag["retirements_2026_actual_mw"] = round(
        rt26["Nameplate Capacity (MW)"].sum(), 1)
    return changelog, changelog_region, plants, diag, adds_df, rets_df


# ---------------- Build, outputs, charts ----------------
def build_stack(trailing_df, changelog, changelog_region, anchor_by_fuel,
                anchor_by_region_fuel):
    """Forward stack: anchor (Dec 31, 2025) + cumulative net changelog.

    Returns (stack_wide_total, stack_long_total, stack_long_region).
    Asserts regional stacks sum to the MISO total every year and fuel.
    """
    rows = []
    running = {f: float(anchor_by_fuel[f]) for f in FUELS}
    running_r = {(rg, f): float(anchor_by_region_fuel[(rg, f)])
                 for rg in REGIONS for f in FUELS}
    for y in range(2026, 2037):
        net = changelog[changelog["year"] == y]
        netr = changelog_region[changelog_region["year"] == y]
        for f in FUELS:
            running[f] += float(net.loc[net["fuel"] == f, "net_mw"].iloc[0])
            for rg in REGIONS:
                running_r[(rg, f)] += float(netr.loc[
                    (netr["region"] == rg) & (netr["fuel"] == f),
                    "net_mw"].iloc[0])
        r = {"year": y, "period": "forward",
             "source_note": "EIA-860M Dec-31-2025 anchor + EIA-860M changelog "
                            "(effective dates, nameplate MW)"}
        r.update({f: round(running[f], 1) for f in FUELS})
        r["Total"] = round(sum(running.values()), 1)
        for rg in REGIONS:
            for f in FUELS:
                r[f"{rg} {f}"] = round(running_r[(rg, f)], 1)
            r[f"{rg} Total"] = round(
                sum(running_r[(rg, f)] for f in FUELS), 1)
        rows.append(r)
    fwd = pd.DataFrame(rows)
    stack_wide = pd.concat(
        [trailing_df, fwd], ignore_index=True)

    # Assertion: regional stacks sum to the MISO total, every year and fuel.
    for _, r in stack_wide.iterrows():
        for f in FUELS + ["Total"]:
            s = round(sum(r[f"{rg} {f}"] for rg in REGIONS), 1)
            assert abs(s - r[f]) < 0.1, (r["year"], f, s, r[f])

    # Long formats.
    long_rows = []
    for _, r in stack_wide.iterrows():
        for f in FUELS + ["Total"]:
            long_rows.append({
                "year": int(r["year"]), "fuel": f,
                "mw": round(float(r[f]), 1),
                "period": r["period"],
                "anchor_year": bool(r["year"] == ANCHOR_YEAR),
                "source_note": r["source_note"],
            })
    long_total = pd.DataFrame(long_rows)
    long_region_rows = []
    for _, r in stack_wide.iterrows():
        for rg in REGIONS:
            for f in FUELS + ["Total"]:
                long_region_rows.append({
                    "year": int(r["year"]), "region": rg, "fuel": f,
                    "mw": round(float(r[f"{rg} {f}"]), 1),
                    "period": r["period"],
                    "anchor_year": bool(r["year"] == ANCHOR_YEAR),
                    "source_note": r["source_note"],
                })
    long_region = pd.DataFrame(long_region_rows)
    return stack_wide, long_total, long_region


def make_charts(stack_wide, changelog):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    years = stack_wide["year"].values
    # 1. Stacked area, MISO total, 2016-2036, GW.
    fig, ax = plt.subplots(figsize=(12, 6.5))
    bottom = np.zeros(len(years))
    for f in STACK_ORDER:
        vals = stack_wide[f].values / 1000.0
        ax.fill_between(years, bottom, bottom + vals,
                        label=f, color=FUEL_COLORS[f], alpha=0.9)
        bottom += vals
    ax.axvline(2025.9, color="black", linestyle="--", linewidth=1.5)
    ax.text(2025.95, bottom.max() * 0.97, "Today (Nov 2026)\nanchor Dec 31, 2025",
            fontsize=9, va="top")
    ax.set_xlim(2016, 2036)
    ax.set_ylabel("Installed capacity (GW)")
    ax.set_xlabel("Year (Dec 31 position; 2026-2036 = anchor + EIA-860M changelog)")
    ax.set_title("MISO generation capacity stack by fuel, 2016-2036 — v1\n"
                 "EIA-860M Dec-31-2025 anchor + EIA-860M changelog (nameplate)",
                 fontsize=11)
    ax.legend(ncol=2, fontsize=9, loc="upper left")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(BASE / "01_stacked_area.png", dpi=150)
    plt.close(fig)

    # 2. Forward net change by fuel/year.
    fwd = changelog[changelog["year"] >= 2026]
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
    ax.set_title("MISO annual net capacity change by fuel, forward 2026-2036 — v1\n"
                 "(EIA-860M additions/retirements, nameplate)", fontsize=11)
    ax.legend(ncol=2, fontsize=9, loc="upper right")
    ax.grid(True, alpha=0.3, axis="y")
    fig.tight_layout()
    fig.savefig(BASE / "02_net_change_forward.png", dpi=150)
    plt.close(fig)

    # 3. Per-region stacked areas (3 panels).
    fig, axes = plt.subplots(3, 1, figsize=(12, 13), sharex=True)
    for ax, rg in zip(axes, REGIONS):
        bottom = np.zeros(len(years))
        for f in STACK_ORDER:
            vals = stack_wide[f"{rg} {f}"].values / 1000.0
            ax.fill_between(years, bottom, bottom + vals,
                            label=f, color=FUEL_COLORS[f], alpha=0.9)
            bottom += vals
        ax.axvline(2025.9, color="black", linestyle="--", linewidth=1.2)
        ax.set_ylabel("GW")
        ax.set_title(f"MISO {rg} — capacity stack by fuel, 2016-2036 (GW)",
                     fontsize=11)
        ax.grid(True, alpha=0.3)
        ax.legend(ncol=5, fontsize=8, loc="upper left")
    axes[-1].set_xlabel("Year (Dec 31 position)")
    fig.tight_layout()
    fig.savefig(BASE / "03_regions_stacked.png", dpi=150)
    plt.close(fig)

    # 4. Regional totals, GW lines.
    fig, ax = plt.subplots(figsize=(12, 6))
    for rg in REGIONS:
        ax.plot(years, stack_wide[f"{rg} Total"].values / 1000.0,
                label=rg, color=REGION_COLORS[rg], linewidth=2)
    ax.plot(years, stack_wide["Total"].values / 1000.0,
            label="MISO total", color="black", linewidth=2, linestyle="--")
    ax.axvline(2025.9, color="black", linestyle="--", linewidth=1.2)
    ax.set_ylabel("Installed capacity (GW)")
    ax.set_xlabel("Year (Dec 31 position)")
    ax.set_title("MISO capacity by region, 2016-2036 — v1", fontsize=11)
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(BASE / "04_regional_totals.png", dpi=150)
    plt.close(fig)
    print("  charts written")


def main():
    op = load_eia_sheet("Operating")
    pl = load_eia_sheet("Planned")
    rt = load_eia_sheet("Retired")
    for df in (op, pl, rt):
        df["fuel"] = df.apply(eia_fuel, axis=1)

    anchor_by_fuel, anchor_by_region_fuel, adiag, _, _ = build_anchor(op, rt)
    print(f"  anchor Dec 31 2025: {adiag['anchor_total_mw']:,.1f} MW "
          f"(EIA-derived, nameplate)")
    print(f"  anchor by region: {adiag['anchor_by_region_mw']}")
    wi_diag = wi_assignment_diagnostics(
        op[op["Balancing Authority Code"] == "MISO"])
    print(f"  WI assignment: entity LRZ1 {wi_diag['wi_entity_LRZ1_mw']:,.1f} MW, "
          f"entity LRZ2 {wi_diag['wi_entity_LRZ2_mw']:,.1f} MW, "
          f"override {wi_diag['wi_plant_override_mw']:,.1f} MW, "
          f"county fallback {wi_diag['wi_county_fallback_mw']:,.1f} MW")

    trailing_df = trailing_reconstructed(op, rt)
    # Internal consistency: reconstructed 2025 snapshot == anchor exactly.
    snap25 = trailing_df[trailing_df["year"] == 2025].iloc[0]
    assert abs(snap25["Total"] - adiag["anchor_total_mw"]) < 0.05, (
        snap25["Total"], adiag["anchor_total_mw"])
    for f in FUELS:
        assert abs(snap25[f] - anchor_by_fuel[f]) < 0.05, (f, snap25[f])
    for rg in REGIONS:
        assert abs(snap25[f"{rg} Total"]
                   - adiag["anchor_by_region_mw"][rg]) < 0.05, rg
    print("  trailing reconstruction reproduces the anchor at 2025: OK")

    changelog, changelog_region, plants, cdiag, adds_df, rets_df = \
        eia_changelog(op, pl, rt)
    print(f"  forward additions 2026-2036: "
          f"{cdiag['planned_total_mw_2026_2036']:,.1f} MW "
          f"({len(adds_df)} units); retirements: "
          f"{rets_df[rets_df['effective_year'].between(2026, 2036)]['mw_nameplate'].sum():,.1f} MW "
          f"({len(rets_df[rets_df['effective_year'].between(2026, 2036)])} units)")

    stack_wide, long_total, long_region = build_stack(
        trailing_df, changelog, changelog_region, anchor_by_fuel,
        anchor_by_region_fuel)
    print("  regional stacks sum to MISO total (all years/fuels): OK")

    # ---- Write outputs (v1 files only; v2 never overwrites these) ----
    plants.to_csv(BASE / "miso_capacity_plants.csv", index=False)
    long_total.to_csv(BASE / "miso_capacity_stack.csv", index=False)
    long_region.to_csv(BASE / "miso_capacity_stack_by_region.csv", index=False)
    changelog.to_csv(BASE / "miso_capacity_changelog.csv", index=False)
    changelog_region.to_csv(BASE / "miso_capacity_changelog_by_region.csv",
                            index=False)

    def agg(df, col):
        return {f: round(float(df[df["fuel"] == f][col].sum()), 1)
                for f in FUELS}
    fwd_add = agg(changelog, "additions_mw")
    fwd_ret = agg(changelog, "retirements_mw")
    tot = stack_wide.set_index("year")["Total"].round(1).to_dict()
    summary = {
        "version": "v1",
        "built": "2026-11-14",
        "anchor": {
            "basis": "EIA-860M Operating-sheet snapshot adjusted to Dec 31, 2025 "
                     "(minus in-service Jan-Sep 2026, plus retired actuals 2026). "
                     "EIA-derived; no clean published MISO ICAP-by-fuel anchor exists.",
            "total_mw": adiag["anchor_total_mw"],
            "by_fuel_mw": adiag["anchor_by_fuel_mw"],
            "by_region_mw": adiag["anchor_by_region_mw"],
            "capacity_definition": "Nameplate MW, all statuses (OP/SB/OA/OS).",
            "cross_checks": {
                "somm_derived_icap_mw": "~180,000 (Potomac Economics 2025 SOM "
                    "Figure 34 ICAP shares scaled to SOM wind ~31.5 GW / solar "
                    "~18 GW nameplate anchors; derivation, not a published table)",
                "miso_fact_sheet_dec2025_mw": 207000,
                "miso_fact_sheet_note": "MISO Fact Sheet Jan 2026 total includes "
                    "demand response and a broader footprint; do not mix with SOM shares.",
                "eia_operating_sep2026_nameplate_mw": adiag["eia_operating_miso_nameplate_mw"],
                "eia_operating_sep2026_netsummer_mw": adiag["eia_operating_miso_netsummer_mw"],
            },
        },
        "trailing": {
            "basis": "Reconstructed Dec-31 snapshots from EIA unit-level data "
                     "(Operating Year / Retirement Year). Estimated; not a MISO publication.",
            "yearly_totals_mw": {str(int(y)): round(float(v), 1)
                                 for y, v in tot.items() if y <= 2025},
        },
        "forward_2026_2036": {
            "additions_mw": round(float(changelog["additions_mw"].sum()), 1),
            "additions_count": int(changelog["additions_count"].sum()),
            "retirements_mw": round(float(changelog["retirements_mw"].sum()), 1),
            "retirements_count": int(changelog["retirements_count"].sum()),
            "net_mw": round(float(changelog["net_mw"].sum()), 1),
            "additions_by_fuel_mw": fwd_add,
            "retirements_by_fuel_mw": fwd_ret,
            "additions_by_region_mw": {
                rg: round(float(changelog_region[
                    changelog_region["region"] == rg]["additions_mw"].sum()), 1)
                for rg in REGIONS},
            "retirements_by_region_mw": {
                rg: round(float(changelog_region[
                    changelog_region["region"] == rg]["retirements_mw"].sum()), 1)
                for rg in REGIONS},
            "net_by_region_mw": {
                rg: round(float(changelog_region[
                    changelog_region["region"] == rg]["net_mw"].sum()), 1)
                for rg in REGIONS},
        },
        "yearly_totals_mw": {str(int(k)): round(float(v), 1)
                             for k, v in tot.items()},
        "yearly_totals_by_region_mw": {
            rg: {str(int(y)): round(float(
                stack_wide[stack_wide["year"] == y][f"{rg} Total"].iloc[0]), 1)
                for y in range(2016, 2037)} for rg in REGIONS},
        "regions": {
            "definition": "MISO North/Central/South subregions, LRZ-based "
                          "(resource-adequacy/operations definition). North = LRZ 1+3; "
                          "Central = LRZ 2+4+5+6+7; South = LRZ 8+9+10. NOT the MTEP "
                          "four-way planning regions (West/Central/East/South).",
            "state_mapping": {s: r for s, r in STATE_TO_REGION.items()},
            "wisconsin": "Split by Local Balancing Authority (entity) then county: "
                         "western WI = North (LRZ 1), eastern/northern WI = Central (LRZ 2).",
            "montana": "Eastern MT sliver (MDU, LRZ 1) assigned to North.",
        },
        "diagnostics": {**adiag, **cdiag, **wi_diag},
        "files": {
            "plants": "miso_capacity_plants.csv",
            "stack": "miso_capacity_stack.csv",
            "stack_by_region": "miso_capacity_stack_by_region.csv",
            "changelog": "miso_capacity_changelog.csv",
            "changelog_by_region": "miso_capacity_changelog_by_region.csv",
            "summary": "summary.json",
            "charts": ["01_stacked_area.png", "02_net_change_forward.png",
                       "03_regions_stacked.png", "04_regional_totals.png"],
        },
    }
    with open(BASE / "summary.json", "w") as f:
        json.dump(summary, f, indent=2)
    print("  wrote plants/stack/changelog CSVs + summary.json")

    make_charts(stack_wide, changelog)
    print("  yearly totals (MISO):")
    for y in range(2025, 2037):
        print(f"    {y}: {tot[y]:,.1f} MW")
    return summary


if __name__ == "__main__":
    main()
