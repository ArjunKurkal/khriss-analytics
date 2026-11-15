#!/usr/bin/env python3
"""Build SERC capacity stack v1 — EIA-only, by subregion.

Mirrors the MISO v1 method (~/workspace/miso-capacity-stack/build_stack.py),
which mirrors PJM: trailing + forward 10-year stack 2016-2036 by fuel
(Coal, Natural Gas, Nuclear, Hydro, Pumped Storage, Wind, Solar, Oil,
Battery Storage, Other), nameplate MW throughout, anchor Dec 31 2025,
forward = anchor + changelog.

SERC differences from MISO (documented, not hidden):
- Region cut is by Balancing Authority Code, NOT by state. The NERC SERC
  footprint contains PJM and MISO members inside SERC states (Dominion
  Energy Virginia and Duke Energy Indiana/Ohio are PJM; southern Illinois
  and Entergy are MISO) — a state cut would be very wrong. The SERC
  Assessment Area definition itself excludes SERC members that are also
  PJM/MISO members. See BA lists below and README.md for the full
  inclusion/exclusion table with MW.
- Florida is included (peninsular Florida transferred from FRCC to SERC
  as Regional Entity on Jul 1, 2019) but every row is tagged with a
  subregion: "SERC-Central" (non-Florida Southeast BAs) or "Florida"
  (Florida BAs). Stacks/changelogs are produced for the SERC total AND
  by subregion, so totals can be quoted both ways.
- Anchor: NO single published SERC-by-fuel anchor exists (NERC LTRA
  publishes anticipated/prospective capacity on a summer-capability,
  assessment-area basis, not nameplate by fuel). The anchor is therefore
  the EIA-860M Operating-sheet snapshot, adjusted to Dec 31 2025 (minus
  units in service Jan-Sep 2026, plus 2026 retired actuals), nameplate
  MW, all statuses. It is EIA-derived, stated explicitly.
- Trailing 2016-2025: RECONSTRUCTED from EIA unit-level data (Operating
  Year / Retirement Year), labelled estimated. Reproduces the anchor
  exactly at 2025 (asserted), for the total and each subregion.
- No blanket retirement-delay override (PJM's was a PJM-only scenario).
  Plant-specific evidence only, and only in v2.

Changelog source: EIA-860M September 2026 vintage (data as of Sep 30,
2026), same file the PJM/MISO stacks used:
~/workspace/pjm-capacity-stack/raw/eia860m_sep2026.xlsx
Additions: units in service in 2026 (Operating sheet, Operating Year
== 2026) + Planned sheet units in window.
Retirements: Retired sheet actuals with Retirement Year == 2026 +
Operating sheet planned retirements, Planned Retirement Year 2026-2036.

The build asserts: (1) snapshot(2025) == anchor exactly (total, by fuel,
by subregion); (2) subregional stacks sum to the SERC total every year
and fuel; (3) forward stack == anchor + cumulative changelog.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

BASE = Path(__file__).resolve().parent
EIA_FILE = Path("/home/hatch/workspace/pjm-capacity-stack/raw/eia860m_sep2026.xlsx")
ANCHOR_YEAR = 2025
FUELS = ["Coal", "Natural Gas", "Nuclear", "Hydro", "Pumped Storage",
         "Wind", "Solar", "Oil", "Battery Storage", "Other"]
STACK_ORDER = ["Coal", "Natural Gas", "Nuclear", "Hydro", "Pumped Storage",
               "Oil", "Wind", "Solar", "Battery Storage", "Other"]
SUBREGIONS = ["SERC-Central", "Florida"]
FUEL_COLORS = {
    "Coal": "#3b3b3b", "Natural Gas": "#d95f02", "Nuclear": "#7570b3",
    "Hydro": "#1b9e77", "Pumped Storage": "#66a61e", "Wind": "#377eb8",
    "Solar": "#e6ab02", "Oil": "#a6761d", "Battery Storage": "#e7298a",
    "Other": "#999999",
}
SUBREGION_COLORS = {"SERC-Central": "#377eb8", "Florida": "#e6ab02"}

# ---------------- Region cut: Balancing Authority Codes ----------------
# SERC-Central (non-Florida Southeast). EIA BA codes:
#   SOCO Southern Company (incl. Georgia Power, Alabama Power,
#        Mississippi Power, Oglethorpe Power, MEAG, PowerSouth — all
#        report under SOCO; verified in-file)
#   TVA  Tennessee Valley Authority
#   DUK  Duke Energy Carolinas (task brief's "DUKE"; EIA code is DUK)
#   CPLE Duke Energy Progress East; CPLW Duke Energy Progress West
#   SCEG Dominion Energy South Carolina (EIA still uses the legacy
#        South Carolina Electric & Gas code SCEG)
#   SC   South Carolina Public Service Authority (Santee Cooper)
#   LGEE LG&E / Kentucky Utilities
#   AECI Associated Electric Cooperative (MO/AR; small IA/OK slivers
#        under the same BA are included — the BA is the unit of the cut)
#   SEPA Southeastern Power Administration (federal hydro, GA/SC/NC)
#   YAD  Yadkin Division hydro (Eagle Creek Renewable, NC)
CENTRAL_BAS = ["SOCO", "TVA", "DUK", "CPLE", "CPLW", "SCEG", "SC",
               "LGEE", "AECI", "SEPA", "YAD"]
# Florida (ex-FRCC, in SERC since Jul 1, 2019). EIA BA codes:
#   FPL  Florida Power & Light
#   FPC  Duke Energy Florida (legacy Florida Power Corp code; task
#        brief's "DEF")
#   TEC  Tampa Electric
#   FMPP Florida Municipal Power Pool (FMPA + Orlando Utilities
#        Commission/OUC, Kissimmee, Lakeland, Key West, etc.)
#   JEA  Jacksonville Electric Authority
#   SEC  Seminole Electric Cooperative
#   TAL  City of Tallahassee; GVL Gainesville Regional Utilities;
#   HST  City of Homestead
FLORIDA_BAS = ["FPL", "FPC", "TEC", "FMPP", "JEA", "SEC", "TAL", "GVL", "HST"]
BA_TO_SUBREGION = {ba: "SERC-Central" for ba in CENTRAL_BAS}
BA_TO_SUBREGION.update({ba: "Florida" for ba in FLORIDA_BAS})
SERC_BAS = CENTRAL_BAS + FLORIDA_BAS


def subregion_of(row):
    ba = row["Balancing Authority Code"]
    if ba in BA_TO_SUBREGION:
        return BA_TO_SUBREGION[ba]
    raise ValueError(f"BA {ba!r} not in SERC cut (plant {row.get('Plant Name')})")


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


def _plant_row(r, typ, status_label, year, month, source, subregion):
    """One unit-level changelog row from an EIA-860M record."""
    return {
        "plant_name": r["Plant Name"],
        "plant_id": r["Plant ID"],
        "generator_id": str(r["Generator ID"]),
        "state": r["Plant State"],
        "county": r.get("County", ""),
        "subregion": subregion,
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
    (anchor_by_fuel, anchor_by_subregion_fuel, diagnostics, base, rt26).
    """
    diag = {}
    s_op = op[op["Balancing Authority Code"].isin(SERC_BAS)].copy()
    s_rt = rt[rt["Balancing Authority Code"].isin(SERC_BAS)].copy()
    diag["eia_operating_serc_units"] = int(len(s_op))
    diag["eia_operating_serc_nameplate_mw"] = round(
        s_op["Nameplate Capacity (MW)"].sum(), 1)
    diag["eia_operating_serc_netsummer_mw"] = round(
        s_op["Net Summer Capacity (MW)"].sum(), 1)
    op_only = s_op[s_op["Status"] == "(OP) Operating"]
    diag["eia_operating_serc_op_only_nameplate_mw"] = round(
        op_only["Nameplate Capacity (MW)"].sum(), 1)
    diag["eia_operating_serc_nonop_nameplate_mw"] = round(
        s_op[s_op["Status"] != "(OP) Operating"]
        ["Nameplate Capacity (MW)"].sum(), 1)
    diag["eia_operating_serc_by_ba_mw"] = {
        k: round(v, 1) for k, v in
        s_op.groupby("Balancing Authority Code")
        ["Nameplate Capacity (MW)"].sum().items()}
    diag["eia_operating_serc_by_fuel_nameplate"] = {
        f: round(v, 1) for f, v in
        s_op.groupby("fuel")["Nameplate Capacity (MW)"].sum().items()}

    # BA-boundary cross-check: MW in Southeast states under non-SERC BAs.
    se_states = ["VA", "NC", "SC", "GA", "FL", "AL", "TN", "KY", "MS",
                 "AR", "MO", "LA"]
    in_states = op[op["Plant State"].isin(se_states)]
    out_ba = in_states[~in_states["Balancing Authority Code"].isin(SERC_BAS)]
    diag["ba_boundary_in_se_states_not_serc_mw"] = round(
        out_ba["Nameplate Capacity (MW)"].sum(), 1)
    diag["ba_boundary_in_se_states_not_serc_by_ba_mw"] = {
        k: round(v, 1) for k, v in
        out_ba.groupby("Balancing Authority Code")
        ["Nameplate Capacity (MW)"].sum().items()}
    ba_out = s_op[~s_op["Plant State"].isin(se_states)]
    diag["ba_boundary_serc_ba_outside_se_states_mw"] = round(
        ba_out["Nameplate Capacity (MW)"].sum(), 1)
    diag["ba_boundary_serc_ba_outside_se_states"] = {
        k: round(v, 1) for k, v in
        ba_out.groupby("Plant State")["Nameplate Capacity (MW)"].sum().items()}

    # Adjustment to Dec 31, 2025.
    in_service_2026 = s_op[pd.to_numeric(
        s_op["Operating Year"], errors="coerce") == 2026]
    rt26 = s_rt[pd.to_numeric(
        s_rt["Retirement Year"], errors="coerce") == 2026]
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

    base = s_op[pd.to_numeric(
        s_op["Operating Year"], errors="coerce") <= 2025].copy()
    anchor_by_fuel = {
        f: round(base[base["fuel"] == f]["Nameplate Capacity (MW)"].sum()
                 + rt26[rt26["fuel"] == f]["Nameplate Capacity (MW)"].sum(), 1)
        for f in FUELS}
    anchor_total = round(sum(anchor_by_fuel.values()), 1)
    base["subregion"] = base.apply(subregion_of, axis=1)
    rt26 = rt26.copy()
    rt26["subregion"] = rt26.apply(subregion_of, axis=1)
    anchor_by_sub_fuel = {}
    for rg in SUBREGIONS:
        for f in FUELS:
            anchor_by_sub_fuel[(rg, f)] = round(
                base[(base["subregion"] == rg) & (base["fuel"] == f)]
                ["Nameplate Capacity (MW)"].sum()
                + rt26[(rt26["subregion"] == rg) & (rt26["fuel"] == f)]
                ["Nameplate Capacity (MW)"].sum(), 1)
    for f in FUELS:
        s = round(sum(anchor_by_sub_fuel[(rg, f)] for rg in SUBREGIONS), 1)
        assert abs(s - anchor_by_fuel[f]) < 0.05, (f, s, anchor_by_fuel[f])
    diag["anchor_total_mw"] = anchor_total
    diag["anchor_by_fuel_mw"] = anchor_by_fuel
    diag["anchor_by_subregion_mw"] = {
        rg: round(sum(anchor_by_sub_fuel[(rg, f)] for f in FUELS), 1)
        for rg in SUBREGIONS}
    diag["anchor_by_ba_mw"] = {}
    tmp = pd.concat([base, rt26], ignore_index=True)
    for ba in SERC_BAS:
        diag["anchor_by_ba_mw"][ba] = round(
            tmp[tmp["Balancing Authority Code"] == ba]
            ["Nameplate Capacity (MW)"].sum(), 1)
    return anchor_by_fuel, anchor_by_sub_fuel, diag, base, rt26


# ---------------- Trailing (reconstructed from EIA unit data) ----------------
def trailing_reconstructed(op, rt):
    """Dec-31 snapshots 2016-2025 reconstructed from EIA unit-level data.

    For year Y: Operating-sheet units with Operating Year <= Y, plus
    Retired-sheet units with Operating Year <= Y < Retirement Year.
    Planned Retirement Year is deliberately NOT used.
    """
    s_op = op[op["Balancing Authority Code"].isin(SERC_BAS)].copy()
    s_rt = rt[rt["Balancing Authority Code"].isin(SERC_BAS)].copy()
    s_op["subregion"] = s_op.apply(subregion_of, axis=1)
    s_rt["subregion"] = s_rt.apply(subregion_of, axis=1)
    s_op["_oy"] = pd.to_numeric(s_op["Operating Year"], errors="coerce")
    s_rt["_oy"] = pd.to_numeric(s_rt["Operating Year"], errors="coerce")
    s_rt["_ry"] = pd.to_numeric(s_rt["Retirement Year"], errors="coerce")
    assert s_op["_oy"].notna().all(), "Operating Year missing on Operating"
    assert s_rt["_oy"].notna().all(), "Operating Year missing on Retired"
    assert s_rt["_ry"].notna().all(), "Retirement Year missing on Retired"
    rows = []
    for y in range(2016, 2026):
        snap_op = s_op[s_op["_oy"] <= y]
        snap_rt = s_rt[(s_rt["_oy"] <= y) & (s_rt["_ry"] > y)]
        snap = pd.concat([snap_op, snap_rt], ignore_index=True)
        r = {"year": y, "period": "trailing",
             "source_note": "EIA-860M reconstructed Dec-31 snapshot "
                            "(unit Operating Year / Retirement Year). Estimated."}
        for f in FUELS:
            r[f] = round(
                snap[snap["fuel"] == f]["Nameplate Capacity (MW)"].sum(), 1)
        r["Total"] = round(snap["Nameplate Capacity (MW)"].sum(), 1)
        for rg in SUBREGIONS:
            for f in FUELS:
                r[f"{rg} {f}"] = round(
                    snap[(snap["subregion"] == rg) & (snap["fuel"] == f)]
                    ["Nameplate Capacity (MW)"].sum(), 1)
            r[f"{rg} Total"] = round(
                snap[snap["subregion"] == rg]["Nameplate Capacity (MW)"].sum(), 1)
        rows.append(r)
    return pd.DataFrame(rows)


# ---------------- Forward changelog (EIA) ----------------
def eia_changelog(op, pl, rt):
    """Forward changelog from EIA-860M (BA in SERC cut). No override.

    Additions: units in service in 2026 (Operating, Operating Year == 2026)
    + Planned sheet units (all years; window applied in the changelog).
    Retirements: Retired sheet actuals with Retirement Year == 2026 +
    Operating sheet planned retirements (all years listed in plants file).
    """
    s_op = op[op["Balancing Authority Code"].isin(SERC_BAS)].copy()
    s_pl = pl[pl["Balancing Authority Code"].isin(SERC_BAS)].copy()
    s_rt = rt[rt["Balancing Authority Code"].isin(SERC_BAS)].copy()
    s_op["subregion"] = s_op.apply(subregion_of, axis=1)
    s_pl["subregion"] = s_pl.apply(subregion_of, axis=1)
    s_rt["subregion"] = s_rt.apply(subregion_of, axis=1)

    diag = {}
    diag["eia_planned_serc_units"] = int(len(s_pl))
    diag["eia_planned_serc_nameplate_mw"] = round(
        s_pl["Nameplate Capacity (MW)"].sum(), 1)
    diag["eia_planned_serc_by_status_mw"] = {
        k: round(v, 1) for k, v in
        s_pl.groupby("Status")["Nameplate Capacity (MW)"].sum().items()}
    diag["eia_planned_serc_by_ba_mw"] = {
        k: round(v, 1) for k, v in
        s_pl.groupby("Balancing Authority Code")
        ["Nameplate Capacity (MW)"].sum().items()}
    diag["eia_planned_max_operation_year"] = int(pd.to_numeric(
        s_pl["Planned Operation Year"], errors="coerce").max())

    adds = []
    in_service_2026 = s_op[pd.to_numeric(
        s_op["Operating Year"], errors="coerce") == 2026]
    for _, r in in_service_2026.iterrows():
        adds.append(_plant_row(
            r, "addition", "addition", int(r["Operating Year"]),
            int(pd.to_numeric(r["Operating Month"], errors="coerce") or 1),
            "Operating sheet: in service Jan-Sep 2026", r["subregion"]))
    for _, r in s_pl.iterrows():
        y = pd.to_numeric(r["Planned Operation Year"], errors="coerce")
        m = pd.to_numeric(r["Planned Operation Month"], errors="coerce")
        if pd.isna(y):
            continue
        adds.append(_plant_row(r, "addition", "addition", int(y),
                               int(m) if not pd.isna(m) else 1,
                               "Planned sheet", r["subregion"]))
    adds_df = pd.DataFrame(adds)

    rets = []
    rt26 = s_rt[pd.to_numeric(
        s_rt["Retirement Year"], errors="coerce") == 2026]
    for _, r in rt26.iterrows():
        rets.append(_plant_row(
            r, "retirement", "retired (actual)",
            int(r["Retirement Year"]),
            int(pd.to_numeric(r["Retirement Month"], errors="coerce") or 1),
            "Retired sheet: actual Jan-Sep 2026", r["subregion"]))
    pr = s_op[pd.to_numeric(
        s_op["Planned Retirement Year"], errors="coerce").notna()].copy()
    for _, r in pr.iterrows():
        y = int(pd.to_numeric(r["Planned Retirement Year"], errors="coerce"))
        m = pd.to_numeric(r["Planned Retirement Month"], errors="coerce")
        rets.append(_plant_row(r, "retirement", "planned retirement", y,
                               int(m) if not pd.isna(m) else 1,
                               "Operating sheet: planned retirement",
                               r["subregion"]))
    rets_df = pd.DataFrame(rets)

    key = lambda d: set(zip(d["Plant ID"].astype(str),
                            d["Generator ID"].astype(str)))
    diag["overlap_operating2026_vs_planned2026_units"] = len(
        key(in_service_2026) & key(s_pl[
            s_pl["Planned Operation Year"] == 2026]))
    diag["overlap_retired2026_vs_plannedret2026_units"] = len(
        key(rt26) & key(s_op[pd.to_numeric(
            s_op["Planned Retirement Year"], errors="coerce") == 2026]))

    plants = pd.concat([adds_df, rets_df], ignore_index=True)
    plants = plants.sort_values(["effective_year", "type", "fuel",
                                 "plant_name"])

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
    clr_rows = []
    for y in range(2026, 2037):
        for rg in SUBREGIONS:
            for f in FUELS:
                a = adds_df[(adds_df["effective_year"] == y)
                            & (adds_df["subregion"] == rg)
                            & (adds_df["fuel"] == f)]
                r = rets_df[(rets_df["effective_year"] == y)
                            & (rets_df["subregion"] == rg)
                            & (rets_df["fuel"] == f)]
                clr_rows.append({
                    "year": y, "subregion": rg, "fuel": f,
                    "additions_mw": round(a["mw_nameplate"].sum(), 1),
                    "additions_count": int(len(a)),
                    "retirements_mw": round(r["mw_nameplate"].sum(), 1),
                    "retirements_count": int(len(r)),
                    "net_mw": round(a["mw_nameplate"].sum()
                                    - r["mw_nameplate"].sum(), 1),
                })
    changelog_sub = pd.DataFrame(clr_rows)
    diag["planned_total_mw_2026_2036"] = round(
        adds_df[adds_df["effective_year"].between(2026, 2036)]
        ["mw_nameplate"].sum(), 1)
    diag["retirements_2026_actual_mw"] = round(
        rt26["Nameplate Capacity (MW)"].sum(), 1)
    return changelog, changelog_sub, plants, diag, adds_df, rets_df


# ---------------- Build, outputs, charts ----------------
def build_stack(trailing_df, changelog, changelog_sub, anchor_by_fuel,
                anchor_by_sub_fuel):
    rows = []
    running = {f: float(anchor_by_fuel[f]) for f in FUELS}
    running_r = {(rg, f): float(anchor_by_sub_fuel[(rg, f)])
                 for rg in SUBREGIONS for f in FUELS}
    for y in range(2026, 2037):
        net = changelog[changelog["year"] == y]
        netr = changelog_sub[changelog_sub["year"] == y]
        for f in FUELS:
            running[f] += float(net.loc[net["fuel"] == f, "net_mw"].iloc[0])
            for rg in SUBREGIONS:
                running_r[(rg, f)] += float(netr.loc[
                    (netr["subregion"] == rg) & (netr["fuel"] == f),
                    "net_mw"].iloc[0])
        r = {"year": y, "period": "forward",
             "source_note": "EIA-860M Dec-31-2025 anchor + EIA-860M changelog "
                            "(effective dates, nameplate MW)"}
        r.update({f: round(running[f], 1) for f in FUELS})
        r["Total"] = round(sum(running.values()), 1)
        for rg in SUBREGIONS:
            for f in FUELS:
                r[f"{rg} {f}"] = round(running_r[(rg, f)], 1)
            r[f"{rg} Total"] = round(
                sum(running_r[(rg, f)] for f in FUELS), 1)
        rows.append(r)
    fwd = pd.DataFrame(rows)
    stack_wide = pd.concat([trailing_df, fwd], ignore_index=True)

    for _, r in stack_wide.iterrows():
        for f in FUELS + ["Total"]:
            s = round(sum(r[f"{rg} {f}"] for rg in SUBREGIONS), 1)
            assert abs(s - r[f]) < 0.1, (r["year"], f, s, r[f])

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
    long_sub_rows = []
    for _, r in stack_wide.iterrows():
        for rg in SUBREGIONS:
            for f in FUELS + ["Total"]:
                long_sub_rows.append({
                    "year": int(r["year"]), "subregion": rg, "fuel": f,
                    "mw": round(float(r[f"{rg} {f}"]), 1),
                    "period": r["period"],
                    "anchor_year": bool(r["year"] == ANCHOR_YEAR),
                    "source_note": r["source_note"],
                })
    long_sub = pd.DataFrame(long_sub_rows)
    return stack_wide, long_total, long_sub


def make_charts(stack_wide, changelog, suffix="", version="v1"):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    years = stack_wide["year"].values
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
    ax.set_xlabel("Year (Dec 31 position; 2026-2036 = anchor + changelog)")
    ax.set_title(f"SERC generation capacity stack by fuel, 2016-2036 — {version}\n"
                 "EIA-860M Dec-31-2025 anchor + changelog (nameplate)",
                 fontsize=11)
    ax.legend(ncol=2, fontsize=9, loc="upper left")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(BASE / f"01_stacked_area{suffix}.png", dpi=150)
    plt.close(fig)

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
    ax.set_title(f"SERC annual net capacity change by fuel, forward 2026-2036 — {version}\n"
                 "(additions/retirements, nameplate)", fontsize=11)
    ax.legend(ncol=2, fontsize=9, loc="upper right")
    ax.grid(True, alpha=0.3, axis="y")
    fig.tight_layout()
    fig.savefig(BASE / f"02_net_change_forward{suffix}.png", dpi=150)
    plt.close(fig)

    fig, axes = plt.subplots(2, 1, figsize=(12, 10), sharex=True)
    for ax, rg in zip(axes, SUBREGIONS):
        bottom = np.zeros(len(years))
        for f in STACK_ORDER:
            vals = stack_wide[f"{rg} {f}"].values / 1000.0
            ax.fill_between(years, bottom, bottom + vals,
                            label=f, color=FUEL_COLORS[f], alpha=0.9)
            bottom += vals
        ax.axvline(2025.9, color="black", linestyle="--", linewidth=1.2)
        ax.set_ylabel("GW")
        ax.set_title(f"SERC {rg} — capacity stack by fuel, 2016-2036 (GW) — {version}",
                     fontsize=11)
        ax.grid(True, alpha=0.3)
        ax.legend(ncol=5, fontsize=8, loc="upper left")
    axes[-1].set_xlabel("Year (Dec 31 position)")
    fig.tight_layout()
    fig.savefig(BASE / f"03_subregions_stacked{suffix}.png", dpi=150)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(12, 6))
    for rg in SUBREGIONS:
        ax.plot(years, stack_wide[f"{rg} Total"].values / 1000.0,
                label=rg, color=SUBREGION_COLORS[rg], linewidth=2)
    ax.plot(years, stack_wide["Total"].values / 1000.0,
            label="SERC total", color="black", linewidth=2, linestyle="--")
    ax.axvline(2025.9, color="black", linestyle="--", linewidth=1.2)
    ax.set_ylabel("Installed capacity (GW)")
    ax.set_xlabel("Year (Dec 31 position)")
    ax.set_title(f"SERC capacity by subregion, 2016-2036 — {version}", fontsize=11)
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(BASE / f"04_subregional_totals{suffix}.png", dpi=150)
    plt.close(fig)
    print("  charts written")


def main():
    op = load_eia_sheet("Operating")
    pl = load_eia_sheet("Planned")
    rt = load_eia_sheet("Retired")
    for df in (op, pl, rt):
        df["fuel"] = df.apply(eia_fuel, axis=1)

    anchor_by_fuel, anchor_by_sub_fuel, adiag, _, _ = build_anchor(op, rt)
    print(f"  anchor Dec 31 2025: {adiag['anchor_total_mw']:,.1f} MW "
          f"(EIA-derived, nameplate)")
    print(f"  anchor by subregion: {adiag['anchor_by_subregion_mw']}")
    print(f"  anchor by BA: {adiag['anchor_by_ba_mw']}")

    trailing_df = trailing_reconstructed(op, rt)
    snap25 = trailing_df[trailing_df["year"] == 2025].iloc[0]
    assert abs(snap25["Total"] - adiag["anchor_total_mw"]) < 0.05, (
        snap25["Total"], adiag["anchor_total_mw"])
    for f in FUELS:
        assert abs(snap25[f] - anchor_by_fuel[f]) < 0.05, (f, snap25[f])
    for rg in SUBREGIONS:
        assert abs(snap25[f"{rg} Total"]
                   - adiag["anchor_by_subregion_mw"][rg]) < 0.05, rg
    print("  trailing reconstruction reproduces the anchor at 2025 "
          "(total + fuels + subregions): OK")

    changelog, changelog_sub, plants, cdiag, adds_df, rets_df = \
        eia_changelog(op, pl, rt)
    print(f"  forward additions 2026-2036: "
          f"{cdiag['planned_total_mw_2026_2036']:,.1f} MW "
          f"({len(adds_df)} units listed); retirements in window: "
          f"{rets_df[rets_df['effective_year'].between(2026, 2036)]['mw_nameplate'].sum():,.1f} MW "
          f"({len(rets_df[rets_df['effective_year'].between(2026, 2036)])} units)")

    stack_wide, long_total, long_sub = build_stack(
        trailing_df, changelog, changelog_sub, anchor_by_fuel,
        anchor_by_sub_fuel)
    print("  subregional stacks sum to SERC total (all years/fuels): OK")

    plants.to_csv(BASE / "serc_capacity_plants.csv", index=False)
    long_total.to_csv(BASE / "serc_capacity_stack.csv", index=False)
    long_sub.to_csv(BASE / "serc_capacity_stack_by_subregion.csv", index=False)
    changelog.to_csv(BASE / "serc_capacity_changelog.csv", index=False)
    changelog_sub.to_csv(BASE / "serc_capacity_changelog_by_subregion.csv",
                         index=False)

    def agg(df, col):
        return {f: round(float(df[df["fuel"] == f][col].sum()), 1)
                for f in FUELS}
    fwd_add = agg(changelog, "additions_mw")
    fwd_ret = agg(changelog, "retirements_mw")
    tot = stack_wide.set_index("year")["Total"].round(1).to_dict()
    summary = {
        "version": "v1",
        "built": "2026-11-15",
        "region_cut": {
            "basis": "EIA-860M Balancing Authority Code. SERC footprint "
                     "excluding ISO/RTO members (PJM/MISO plants inside "
                     "SERC states stay out). Florida included (ex-FRCC, "
                     "in SERC since Jul 1, 2019), tagged as subregion "
                     "Florida; all other included BAs are SERC-Central.",
            "central_bas": CENTRAL_BAS,
            "florida_bas": FLORIDA_BAS,
            "ba_code_notes": "Task brief names map to EIA codes: DUKE->DUK "
                             "(Duke Energy Carolinas), DEF->FPC (Duke Energy "
                             "Florida, legacy Florida Power Corp code), "
                             "SCEG is Dominion Energy South Carolina's EIA "
                             "code, OUC sits inside FMPP, FMPA plants sit "
                             "in FMPP and FPC.",
        },
        "anchor": {
            "basis": "EIA-860M Operating-sheet snapshot adjusted to Dec 31, 2025 "
                     "(minus in-service Jan-Sep 2026, plus retired actuals 2026). "
                     "EIA-derived; no single published SERC-by-fuel nameplate "
                     "anchor exists (NERC LTRA publishes assessment-area "
                     "anticipated/prospective capacity on a capability basis).",
            "total_mw": adiag["anchor_total_mw"],
            "by_fuel_mw": adiag["anchor_by_fuel_mw"],
            "by_subregion_mw": adiag["anchor_by_subregion_mw"],
            "by_ba_mw": adiag["anchor_by_ba_mw"],
            "capacity_definition": "Nameplate MW, all statuses (OP/SB/OA/OS).",
            "cross_checks": {
                "note": "NERC LTRA / DOE ITCS figures are peak-load and "
                        "capability-basis, not nameplate: DOE Jul 2025 grid "
                        "report (NERC ITCS data) puts SERC 2024 peak load at "
                        "193,654 MW across SERC-C/SE/FL/E assessment areas. "
                        "Nameplate anchor runs well above peak load, as "
                        "expected (solar nameplate, standby units, reserve).",
                "eia_operating_sep2026_nameplate_mw": adiag["eia_operating_serc_nameplate_mw"],
                "eia_operating_sep2026_netsummer_mw": adiag["eia_operating_serc_netsummer_mw"],
            },
        },
        "trailing": {
            "basis": "Reconstructed Dec-31 snapshots from EIA unit-level data "
                     "(Operating Year / Retirement Year). Estimated; not a "
                     "NERC/SERC publication.",
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
            "additions_by_subregion_mw": {
                rg: round(float(changelog_sub[
                    changelog_sub["subregion"] == rg]["additions_mw"].sum()), 1)
                for rg in SUBREGIONS},
            "retirements_by_subregion_mw": {
                rg: round(float(changelog_sub[
                    changelog_sub["subregion"] == rg]["retirements_mw"].sum()), 1)
                for rg in SUBREGIONS},
            "net_by_subregion_mw": {
                rg: round(float(changelog_sub[
                    changelog_sub["subregion"] == rg]["net_mw"].sum()), 1)
                for rg in SUBREGIONS},
        },
        "yearly_totals_mw": {str(int(k)): round(float(v), 1)
                             for k, v in tot.items()},
        "yearly_totals_by_subregion_mw": {
            rg: {str(int(y)): round(float(
                stack_wide[stack_wide["year"] == y][f"{rg} Total"].iloc[0]), 1)
                for y in range(2016, 2037)} for rg in SUBREGIONS},
        "diagnostics": {**adiag, **cdiag},
        "files": {
            "plants": "serc_capacity_plants.csv",
            "stack": "serc_capacity_stack.csv",
            "stack_by_subregion": "serc_capacity_stack_by_subregion.csv",
            "changelog": "serc_capacity_changelog.csv",
            "changelog_by_subregion": "serc_capacity_changelog_by_subregion.csv",
            "summary": "summary.json",
            "charts": ["01_stacked_area.png", "02_net_change_forward.png",
                       "03_subregions_stacked.png", "04_subregional_totals.png"],
        },
    }
    with open(BASE / "summary.json", "w") as f:
        json.dump(summary, f, indent=2)
    print("  wrote plants/stack/changelog CSVs + summary.json")

    make_charts(stack_wide, changelog)
    print("  yearly totals (SERC):")
    for y in range(2025, 2037):
        print(f"    {y}: {tot[y]:,.1f} MW")
    return summary


if __name__ == "__main__":
    main()
