#!/usr/bin/env python3
"""Build SPP capacity stack v1 — EIA-only, East/West split.

Mirrors the MISO v1 method (~/workspace/miso-capacity-stack/build_stack.py):
trailing + forward 10-year stack 2016-2036 by fuel (Coal, Natural Gas,
Nuclear, Hydro, Pumped Storage, Wind, Solar, Oil, Battery Storage, Other),
nameplate MW throughout, anchor Dec 31 2025, forward = anchor + changelog.

SPP differences from MISO (documented, not hidden):
- Footprint: SPP RTO as it stands NOW, post western expansion
  (effective April 1, 2026). SPP is now two Balancing Authority Areas:
  the East BAA (legacy footprint) and the West BAA. Per SPP's own
  Sep 4, 2026 tariff filing (ER26-3720), the expansion "consolidated
  the Western Area Colorado Missouri (WACM) Balancing Authority and
  the Western Area Upper Great Plains West (WAUW) BA" into the SPP
  West BAA. EIA-860M Sep 2026 still reports the pre-consolidation BA
  codes, so the plant cut is:
    East = Balancing Authority Code == SWPP
    West = Balancing Authority Code in {WACM, WAUW}
           OR a plant-level override (below).
- Plant-level overrides (the analogue of MISO's RockGen override and
  Legend BA correction): two verified transmission-owning RTO
  Expansion Members whose plants EIA files under BAs that did NOT
  consolidate into SPP West, and which would otherwise be missed
  entirely:
    * Platte River Power Authority — Rawhide Energy Station, CO
      (800.4 MW operating; 223.0 MW planned gas), filed under PSCO.
      PRPA is an Expansion Member that initiated the expansion, a
      transmission owner under the SPP Tariff from April 1, 2026
      (FERC ER26-998, new SPP Zone 101).
    * Deseret Generation & Transmission Cooperative — Bonanza, UT
      (512.0 MW) and Solomon (14.9 MW), filed under PACE. Deseret is
      an Expansion Member / transmission owner from April 1, 2026
      (FERC ER26-1137).
  Every other plant under PSCO / PNM / PACE / AZPS / SRP / NWMT etc.
  is EXCLUDED, including Tri-State's own plants filed under PSCO
  (696.1 MW) and PNM (186.0 MW): those BAs did not consolidate into
  SPP, and no SPP source shows those units transferring. The excluded
  882.1 MW is the largest boundary judgement in this build and is
  quantified in summary.json / README.md.
- Markets+ is NOT RTO membership. Arizona Public Service, Salt River
  Project, Tucson Electric and UniSource (and PNM, which chose
  CAISO EDAM) are Markets+ / EDAM participants only; none of their
  plants (AZPS / SRP / TEPC / PNM BAs) is in this stack. The only
  Arizona RTO participant in SPP's Apr 2, 2026 roster is the City of
  Page, which has no EIA-860M generation of its own (its federal
  hydro allocations sit in USBR plants under WALC, also excluded —
  WALC did not consolidate; see README).
- Anchor: no published SPP installed-capacity-by-fuel table on a
  nameplate basis exists for the post-expansion footprint (SPP's
  State of the Market reports the legacy East market; SPP 101 gives
  East/West nameplate totals only, as of mid-2026). Per the MISO
  fallback, the anchor is the EIA-860M Operating-sheet snapshot of
  the cut above, adjusted to Dec 31, 2025 (minus units in service
  Jan-Sep 2026, plus Retired-sheet actual retirements in 2026),
  nameplate MW, all statuses. EIA-derived, stated explicitly.
  Cross-checks against SPP-published figures are in summary.json.
- Trailing 2016-2025: reconstructed from EIA unit-level data on a
  CONSTANT post-expansion footprint. The East trailing is genuine
  history (SWPP existed throughout). The West trailing is pro-forma:
  the West BAA did not exist before April 1, 2026, so 2016-2025 West
  figures show what the plants in today's West footprint summed to
  in each year — they are NOT a record of SPP membership. Labelled
  estimated / pro-forma in every output row.
- No blanket retirement-delay override (PJM's was a PJM-only
  scenario). Plant-specific evidence is handled in v2 only.

Changelog source: EIA-860M September 2026 vintage (data as of
Sep 30, 2026), same file the PJM/MISO stacks used.
Additions: units in service in 2026 (Operating sheet) + Planned sheet.
Retirements: Retired sheet actuals 2026 + Operating sheet planned
retirements 2026-2036. EVERY plants/changelog row carries east_west.

The build asserts: (1) trailing reconstruction reproduces the anchor
exactly at 2025 for Combined, East and West; (2) East + West ==
Combined every year and fuel (stack and changelog); (3) forward
stack == anchor + cumulative changelog.
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
REGIONS = ["East", "West"]  # east_west values; "region" mirrors east_west
FUEL_COLORS = {
    "Coal": "#3b3b3b", "Natural Gas": "#d95f02", "Nuclear": "#7570b3",
    "Hydro": "#1b9e77", "Pumped Storage": "#66a61e", "Wind": "#377eb8",
    "Solar": "#e6ab02", "Oil": "#a6761d", "Battery Storage": "#e7298a",
    "Other": "#999999",
}
REGION_COLORS = {"East": "#377eb8", "West": "#d95f02"}

# ---------------- East/West cut ----------------
EAST_BAS = {"SWPP"}
WEST_BAS = {"WACM", "WAUW"}
# Verified transmission-owning RTO Expansion Members (SPP Apr 2, 2026
# release; FERC RTO Expansion Order, 190 FERC 61,169, Mar 20, 2025)
# whose EIA plants sit under BAs that did not consolidate into SPP
# West. Entity Name strings are EIA's, copied verbatim.
WEST_OVERRIDE_ENTITIES = {
    "Platte River Power Authority",       # Rawhide, CO — filed under PSCO
    "Deseret Generation & Tran Coop",     # Bonanza/Solomon, UT — filed under PACE
}
# Western BAs explicitly NOT in the cut (for diagnostics / README):
# PSCO (Xcel Colorado — not an RTO member), PNM (EDAM), PACE
# (PacifiCorp — EDAM), AZPS / SRP / TEPC (Markets+ only), NWMT
# (NorthWestern Montana — BA did not consolidate), WALC (WAPA Lower
# Colorado — BA did not consolidate).


def east_west_of(row):
    """East/West tag for one EIA plant row, or None if outside SPP."""
    ba = row["Balancing Authority Code"]
    if ba in EAST_BAS:
        return "East"
    if ba in WEST_BAS:
        return "West"
    if str(row.get("Entity Name", "")).strip() in WEST_OVERRIDE_ENTITIES:
        return "West"
    return None


def in_spp(df):
    out = df.copy()
    out["east_west"] = out.apply(east_west_of, axis=1)
    return out[out["east_west"].notna()].copy()


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


def _plant_row(r, typ, status_label, year, month, source):
    """One unit-level changelog row from an EIA-860M record."""
    ew = r["east_west"]
    return {
        "plant_name": r["Plant Name"],
        "plant_id": r["Plant ID"],
        "generator_id": str(r["Generator ID"]),
        "state": r["Plant State"],
        "county": r.get("County", ""),
        "region": ew,
        "east_west": ew,
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
    """Anchor = EIA Operating snapshot of the SPP cut, adjusted to
    Dec 31, 2025 (minus in-service 2026, plus retired actuals 2026).
    Returns (anchor_by_fuel, anchor_by_region_fuel, diag, base, rt26).
    """
    diag = {}
    spp_op = in_spp(op)
    spp_rt = in_spp(rt)
    diag["eia_operating_spp_units"] = int(len(spp_op))
    diag["eia_operating_spp_nameplate_mw"] = round(
        spp_op["Nameplate Capacity (MW)"].sum(), 1)
    diag["eia_operating_spp_netsummer_mw"] = round(
        spp_op["Net Summer Capacity (MW)"].sum(), 1)
    diag["eia_operating_by_ba_mw"] = {
        k: round(v, 1) for k, v in
        spp_op.groupby("Balancing Authority Code")
        ["Nameplate Capacity (MW)"].sum().items()}
    diag["eia_operating_by_eastwest_mw"] = {
        k: round(v, 1) for k, v in
        spp_op.groupby("east_west")["Nameplate Capacity (MW)"].sum().items()}
    ov = spp_op[spp_op["Entity Name"].isin(WEST_OVERRIDE_ENTITIES)
                & ~spp_op["Balancing Authority Code"].isin(WEST_BAS)]
    diag["west_override_operating_mw"] = round(
        ov["Nameplate Capacity (MW)"].sum(), 1)
    diag["west_override_operating_units"] = int(len(ov))
    diag["west_override_by_entity_mw"] = {
        k: round(v, 1) for k, v in
        ov.groupby("Entity Name")["Nameplate Capacity (MW)"].sum().items()}
    op_only = spp_op[spp_op["Status"] == "(OP) Operating"]
    diag["eia_operating_spp_op_only_nameplate_mw"] = round(
        op_only["Nameplate Capacity (MW)"].sum(), 1)
    diag["eia_operating_spp_nonop_nameplate_mw"] = round(
        spp_op[spp_op["Status"] != "(OP) Operating"]
        ["Nameplate Capacity (MW)"].sum(), 1)
    diag["eia_operating_spp_by_fuel_nameplate"] = {
        f: round(v, 1) for f, v in
        spp_op.groupby("fuel")["Nameplate Capacity (MW)"].sum().items()}

    # Boundary diagnostics: western-state capacity under BAs NOT in
    # the cut (what a state-based cut would wrongly include, and what
    # the Markets+ / EDAM / non-consolidated BAs hold).
    west_states = ["WY", "CO", "AZ", "NM", "UT", "MT"]
    in_ws = op[op["Plant State"].isin(west_states)]
    in_ws = in_ws[in_ws.apply(east_west_of, axis=1).isna()]
    diag["excluded_western_states_not_spp_mw"] = round(
        in_ws["Nameplate Capacity (MW)"].sum(), 1)
    diag["excluded_western_states_not_spp_by_ba_mw"] = {
        k: round(v, 1) for k, v in
        in_ws.groupby("Balancing Authority Code")
        ["Nameplate Capacity (MW)"].sum().sort_values(ascending=False)
        .items()}
    # Tri-State plants excluded because their BAs did not consolidate.
    ts = op[op["Entity Name"] == "Tri-State G & T Assn, Inc"]
    ts_out = ts[ts.apply(east_west_of, axis=1).isna()]
    diag["excluded_tristate_nonconsolidated_ba_mw"] = round(
        ts_out["Nameplate Capacity (MW)"].sum(), 1)
    diag["excluded_tristate_nonconsolidated_ba_by_ba_mw"] = {
        k: round(v, 1) for k, v in
        ts_out.groupby("Balancing Authority Code")
        ["Nameplate Capacity (MW)"].sum().items()}
    # Glen Canyon / Hoover (WAPA-CRSP/RMR flagship hydro under WALC).
    walc_usbr = op[(op["Balancing Authority Code"] == "WALC")
                   & (op["Entity Name"] == "U S Bureau of Reclamation")]
    diag["excluded_walc_usbr_hydro_mw"] = round(
        walc_usbr["Nameplate Capacity (MW)"].sum(), 1)

    in_service_2026 = spp_op[pd.to_numeric(
        spp_op["Operating Year"], errors="coerce") == 2026]
    rt26 = spp_rt[pd.to_numeric(
        spp_rt["Retirement Year"], errors="coerce") == 2026].copy()
    diag["anchor_less_in_service_2026_mw"] = round(
        in_service_2026["Nameplate Capacity (MW)"].sum(), 1)
    diag["anchor_less_in_service_2026_units"] = int(len(in_service_2026))
    diag["anchor_less_in_service_2026_by_eastwest"] = {
        k: round(v, 1) for k, v in
        in_service_2026.groupby("east_west")
        ["Nameplate Capacity (MW)"].sum().items()}
    diag["anchor_plus_retired_2026_mw"] = round(
        rt26["Nameplate Capacity (MW)"].sum(), 1)
    diag["anchor_plus_retired_2026_units"] = int(len(rt26))

    base = spp_op[pd.to_numeric(
        spp_op["Operating Year"], errors="coerce") <= 2025].copy()
    anchor_by_fuel = {
        f: round(base[base["fuel"] == f]["Nameplate Capacity (MW)"].sum()
                 + rt26[rt26["fuel"] == f]["Nameplate Capacity (MW)"].sum(), 1)
        for f in FUELS}
    anchor_total = round(sum(anchor_by_fuel.values()), 1)
    anchor_by_region_fuel = {}
    for rg in REGIONS:
        for f in FUELS:
            anchor_by_region_fuel[(rg, f)] = round(
                base[(base["east_west"] == rg) & (base["fuel"] == f)]
                ["Nameplate Capacity (MW)"].sum()
                + rt26[(rt26["east_west"] == rg) & (rt26["fuel"] == f)]
                ["Nameplate Capacity (MW)"].sum(), 1)
    for f in FUELS:
        s = round(sum(anchor_by_region_fuel[(rg, f)] for rg in REGIONS), 1)
        assert abs(s - anchor_by_fuel[f]) < 0.05, (f, s, anchor_by_fuel[f])
    diag["anchor_total_mw"] = anchor_total
    diag["anchor_by_fuel_mw"] = anchor_by_fuel
    diag["anchor_by_region_mw"] = {
        rg: round(sum(anchor_by_region_fuel[(rg, f)] for f in FUELS), 1)
        for rg in REGIONS}
    diag["anchor_by_region_fuel_mw"] = {
        f"{rg}|{f}": anchor_by_region_fuel[(rg, f)]
        for rg in REGIONS for f in FUELS}
    return anchor_by_fuel, anchor_by_region_fuel, diag, base, rt26


# ---------------- Trailing (reconstructed, constant footprint) ----------------
def trailing_reconstructed(op, rt):
    """Dec-31 snapshots 2016-2025 on the constant post-expansion
    footprint: Operating units with Operating Year <= Y, plus Retired
    units with Operating Year <= Y < Retirement Year. Planned
    Retirement Year is NOT used. West pre-2026 is pro-forma (the West
    BAA did not exist). Labelled estimated in the outputs.
    """
    spp_op = in_spp(op)
    spp_rt = in_spp(rt)
    spp_op["_oy"] = pd.to_numeric(spp_op["Operating Year"], errors="coerce")
    spp_rt["_oy"] = pd.to_numeric(spp_rt["Operating Year"], errors="coerce")
    spp_rt["_ry"] = pd.to_numeric(spp_rt["Retirement Year"], errors="coerce")
    assert spp_op["_oy"].notna().all(), "Operating Year missing on Operating"
    assert spp_rt["_oy"].notna().all(), "Operating Year missing on Retired"
    assert spp_rt["_ry"].notna().all(), "Retirement Year missing on Retired"
    rows = []
    for y in range(2016, 2026):
        snap = pd.concat(
            [spp_op[spp_op["_oy"] <= y],
             spp_rt[(spp_rt["_oy"] <= y) & (spp_rt["_ry"] > y)]],
            ignore_index=True)
        r = {"year": y, "period": "trailing",
             "source_note": "EIA-860M reconstructed Dec-31 snapshot on the "
                            "constant post-expansion SPP footprint "
                            "(unit Operating Year / Retirement Year). "
                            "Estimated; West pre-2026 is pro-forma — the "
                            "SPP West BAA did not exist before Apr 1, 2026."}
        for f in FUELS:
            r[f] = round(
                snap[snap["fuel"] == f]["Nameplate Capacity (MW)"].sum(), 1)
        r["Total"] = round(snap["Nameplate Capacity (MW)"].sum(), 1)
        for rg in REGIONS:
            for f in FUELS:
                r[f"{rg} {f}"] = round(
                    snap[(snap["east_west"] == rg) & (snap["fuel"] == f)]
                    ["Nameplate Capacity (MW)"].sum(), 1)
            r[f"{rg} Total"] = round(
                snap[snap["east_west"] == rg]
                ["Nameplate Capacity (MW)"].sum(), 1)
        rows.append(r)
    return pd.DataFrame(rows)


# ---------------- Forward changelog (EIA) ----------------
def eia_changelog(op, pl, rt):
    """Forward changelog from EIA-860M for the SPP cut. No override.

    Additions: in service 2026 (Operating) + Planned sheet units.
    Retirements: Retired actuals 2026 + Operating planned retirements.
    Returns (changelog, changelog_by_region, plants, diag, adds, rets).
    """
    spp_op = in_spp(op)
    spp_pl = in_spp(pl)
    spp_rt = in_spp(rt)
    diag = {}
    diag["eia_planned_spp_units"] = int(len(spp_pl))
    diag["eia_planned_spp_nameplate_mw"] = round(
        spp_pl["Nameplate Capacity (MW)"].sum(), 1)
    diag["eia_planned_spp_by_status_mw"] = {
        k: round(v, 1) for k, v in
        spp_pl.groupby("Status")["Nameplate Capacity (MW)"].sum().items()}
    diag["eia_planned_spp_by_eastwest_mw"] = {
        k: round(v, 1) for k, v in
        spp_pl.groupby("east_west")["Nameplate Capacity (MW)"].sum().items()}
    diag["eia_planned_max_operation_year"] = int(pd.to_numeric(
        spp_pl["Planned Operation Year"], errors="coerce").max())

    adds = []
    in_service_2026 = spp_op[pd.to_numeric(
        spp_op["Operating Year"], errors="coerce") == 2026]
    for _, r in in_service_2026.iterrows():
        adds.append(_plant_row(
            r, "addition", "addition", int(r["Operating Year"]),
            int(pd.to_numeric(r["Operating Month"], errors="coerce") or 1),
            "Operating sheet: in service Jan-Sep 2026"))
    for _, r in spp_pl.iterrows():
        y = pd.to_numeric(r["Planned Operation Year"], errors="coerce")
        m = pd.to_numeric(r["Planned Operation Month"], errors="coerce")
        if pd.isna(y):
            continue
        adds.append(_plant_row(r, "addition", "addition", int(y),
                               int(m) if not pd.isna(m) else 1,
                               "Planned sheet"))
    adds_df = pd.DataFrame(adds)

    rets = []
    rt26 = spp_rt[pd.to_numeric(
        spp_rt["Retirement Year"], errors="coerce") == 2026]
    for _, r in rt26.iterrows():
        rets.append(_plant_row(
            r, "retirement", "retired (actual)", int(r["Retirement Year"]),
            int(pd.to_numeric(r["Retirement Month"], errors="coerce") or 1),
            "Retired sheet: actual Jan-Sep 2026"))
    pr = spp_op[pd.to_numeric(
        spp_op["Planned Retirement Year"], errors="coerce").notna()].copy()
    for _, r in pr.iterrows():
        y = int(pd.to_numeric(r["Planned Retirement Year"], errors="coerce"))
        m = pd.to_numeric(r["Planned Retirement Month"], errors="coerce")
        rets.append(_plant_row(r, "retirement", "planned retirement", y,
                               int(m) if not pd.isna(m) else 1,
                               "Operating sheet: planned retirement"))
    rets_df = pd.DataFrame(rets)

    key = lambda d: set(zip(d["Plant ID"].astype(str),
                            d["Generator ID"].astype(str)))
    diag["overlap_operating2026_vs_planned2026_units"] = len(
        key(in_service_2026) & key(spp_pl[
            spp_pl["Planned Operation Year"] == 2026]))
    diag["overlap_retired2026_vs_plannedret2026_units"] = len(
        key(rt26) & key(spp_op[pd.to_numeric(
            spp_op["Planned Retirement Year"], errors="coerce") == 2026]))

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
        for rg in REGIONS:
            for f in FUELS:
                a = adds_df[(adds_df["effective_year"] == y)
                            & (adds_df["east_west"] == rg)
                            & (adds_df["fuel"] == f)]
                r = rets_df[(rets_df["effective_year"] == y)
                            & (rets_df["east_west"] == rg)
                            & (rets_df["fuel"] == f)]
                clr_rows.append({
                    "year": y, "region": rg, "east_west": rg, "fuel": f,
                    "additions_mw": round(a["mw_nameplate"].sum(), 1),
                    "additions_count": int(len(a)),
                    "retirements_mw": round(r["mw_nameplate"].sum(), 1),
                    "retirements_count": int(len(r)),
                    "net_mw": round(a["mw_nameplate"].sum()
                                    - r["mw_nameplate"].sum(), 1),
                })
    changelog_region = pd.DataFrame(clr_rows)
    # East + West == Combined in the changelog, every year and fuel.
    for y in range(2026, 2037):
        for f in FUELS:
            s = round(changelog_region[
                (changelog_region["year"] == y)
                & (changelog_region["fuel"] == f)]["net_mw"].sum(), 1)
            t = round(float(changelog[
                (changelog["year"] == y) & (changelog["fuel"] == f)]
                ["net_mw"].iloc[0]), 1)
            assert abs(s - t) < 0.05, (y, f, s, t)
    diag["planned_total_mw_2026_2036"] = round(
        adds_df[adds_df["effective_year"].between(2026, 2036)]
        ["mw_nameplate"].sum(), 1)
    diag["retirements_2026_actual_mw"] = round(
        rt26["Nameplate Capacity (MW)"].sum(), 1)
    return changelog, changelog_region, plants, diag, adds_df, rets_df


# ---------------- Build, outputs, charts ----------------
def build_stack(trailing_df, changelog, changelog_region, anchor_by_fuel,
                anchor_by_region_fuel):
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
             "source_note": "EIA-860M Dec-31-2025 anchor (post-expansion "
                            "footprint) + EIA-860M changelog "
                            "(effective dates, nameplate MW)"}
        r.update({f: round(running[f], 1) for f in FUELS})
        r["Total"] = round(sum(running.values()), 1)
        for rg in REGIONS:
            for f in FUELS:
                r[f"{rg} {f}"] = round(running_r[(rg, f)], 1)
            r[f"{rg} Total"] = round(
                sum(running_r[(rg, f)] for f in FUELS), 1)
        rows.append(r)
    stack_wide = pd.concat([trailing_df, pd.DataFrame(rows)],
                           ignore_index=True)
    for _, r in stack_wide.iterrows():
        for f in FUELS + ["Total"]:
            s = round(sum(r[f"{rg} {f}"] for rg in REGIONS), 1)
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
    long_region_rows = []
    for _, r in stack_wide.iterrows():
        for rg in REGIONS:
            for f in FUELS + ["Total"]:
                long_region_rows.append({
                    "year": int(r["year"]), "region": rg, "east_west": rg,
                    "fuel": f, "mw": round(float(r[f"{rg} {f}"]), 1),
                    "period": r["period"],
                    "anchor_year": bool(r["year"] == ANCHOR_YEAR),
                    "source_note": r["source_note"],
                })
    return stack_wide, pd.DataFrame(long_rows), pd.DataFrame(long_region_rows)


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
    ax.text(2025.95, bottom.max() * 0.97,
            "Today (Nov 2026)\nanchor Dec 31, 2025", fontsize=9, va="top")
    ax.set_xlim(2016, 2036)
    ax.set_ylabel("Installed capacity (GW)")
    ax.set_xlabel("Year (Dec 31 position; 2026-2036 = anchor + changelog)")
    ax.set_title(f"SPP generation capacity stack by fuel, 2016-2036 — {version}\n"
                 "EIA-860M Dec-31-2025 anchor, post-expansion footprint "
                 "(East + West), nameplate", fontsize=11)
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
        ax.bar(piv.index, pos, bottom=top, label=f,
               color=FUEL_COLORS[f], width=0.75)
        top += pos
        ax.bar(piv.index, neg, bottom=bottom, color=FUEL_COLORS[f], width=0.75)
        bottom += neg
    ax.axhline(0, color="black", linewidth=0.8)
    pos_tot = float(piv.clip(lower=0).sum(axis=1).max())
    neg_tot = float(piv.clip(upper=0).sum(axis=1).min())
    ax.set_ylim(neg_tot * 1.12 - 0.2, pos_tot * 1.08 + 0.3)
    ax.set_ylabel("Net capacity change (GW / year)")
    ax.set_xlabel("Year")
    ax.set_title(f"SPP annual net capacity change by fuel, forward "
                 f"2026-2036 — {version}\n(EIA-860M additions/retirements, "
                 "nameplate)", fontsize=11)
    ax.legend(ncol=2, fontsize=9, loc="upper right")
    ax.grid(True, alpha=0.3, axis="y")
    fig.tight_layout()
    fig.savefig(BASE / f"02_net_change_forward{suffix}.png", dpi=150)
    plt.close(fig)

    fig, axes = plt.subplots(2, 1, figsize=(12, 10), sharex=True)
    for ax, rg in zip(axes, REGIONS):
        bottom = np.zeros(len(years))
        for f in STACK_ORDER:
            vals = stack_wide[f"{rg} {f}"].values / 1000.0
            ax.fill_between(years, bottom, bottom + vals,
                            label=f, color=FUEL_COLORS[f], alpha=0.9)
            bottom += vals
        ax.axvline(2025.9, color="black", linestyle="--", linewidth=1.2)
        ax.set_ylabel("GW")
        note = " (pro-forma before Apr 2026)" if rg == "West" else ""
        ax.set_title(f"SPP {rg} — capacity stack by fuel, 2016-2036 (GW)"
                     f"{note} — {version}", fontsize=11)
        ax.grid(True, alpha=0.3)
        ax.legend(ncol=5, fontsize=8, loc="upper left")
    axes[-1].set_xlabel("Year (Dec 31 position)")
    fig.tight_layout()
    fig.savefig(BASE / f"03_eastwest_stacked{suffix}.png", dpi=150)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(12, 6))
    for rg in REGIONS:
        ax.plot(years, stack_wide[f"{rg} Total"].values / 1000.0,
                label=rg, color=REGION_COLORS[rg], linewidth=2)
    ax.plot(years, stack_wide["Total"].values / 1000.0,
            label="SPP total", color="black", linewidth=2, linestyle="--")
    ax.axvline(2025.9, color="black", linestyle="--", linewidth=1.2)
    ax.set_ylabel("Installed capacity (GW)")
    ax.set_xlabel("Year (Dec 31 position)")
    ax.set_title(f"SPP capacity by East/West, 2016-2036 — {version}",
                 fontsize=11)
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(BASE / f"04_eastwest_totals{suffix}.png", dpi=150)
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
          f"(EIA-derived, nameplate, post-expansion footprint)")
    print(f"  anchor by East/West: {adiag['anchor_by_region_mw']}")

    trailing_df = trailing_reconstructed(op, rt)
    snap25 = trailing_df[trailing_df["year"] == 2025].iloc[0]
    assert abs(snap25["Total"] - adiag["anchor_total_mw"]) < 0.05
    for f in FUELS:
        assert abs(snap25[f] - anchor_by_fuel[f]) < 0.05, f
    for rg in REGIONS:
        assert abs(snap25[f"{rg} Total"]
                   - adiag["anchor_by_region_mw"][rg]) < 0.05, rg
        for f in FUELS:
            assert abs(snap25[f"{rg} {f}"]
                       - anchor_by_region_fuel[(rg, f)]) < 0.05, (rg, f)
    print("  trailing reconstruction reproduces the anchor at 2025 "
          "(Combined, East, West): OK")

    changelog, changelog_region, plants, cdiag, adds_df, rets_df = \
        eia_changelog(op, pl, rt)
    inw = rets_df[rets_df["effective_year"].between(2026, 2036)]
    print(f"  forward additions 2026-2036: "
          f"{cdiag['planned_total_mw_2026_2036']:,.1f} MW "
          f"({len(adds_df)} units); retirements: "
          f"{inw['mw_nameplate'].sum():,.1f} MW ({len(inw)} units)")

    stack_wide, long_total, long_region = build_stack(
        trailing_df, changelog, changelog_region, anchor_by_fuel,
        anchor_by_region_fuel)
    print("  East + West == Combined (all years/fuels): OK")

    plants.to_csv(BASE / "spp_capacity_plants.csv", index=False)
    long_total.to_csv(BASE / "spp_capacity_stack.csv", index=False)
    long_region.to_csv(BASE / "spp_capacity_stack_by_eastwest.csv",
                       index=False)
    changelog.to_csv(BASE / "spp_capacity_changelog.csv", index=False)
    changelog_region.to_csv(
        BASE / "spp_capacity_changelog_by_eastwest.csv", index=False)

    def agg(df, col):
        return {f: round(float(df[df["fuel"] == f][col].sum()), 1)
                for f in FUELS}
    tot = stack_wide.set_index("year")["Total"].round(1).to_dict()
    summary = {
        "version": "v1",
        "built": "2026-11-15",
        "anchor": {
            "basis": "EIA-860M Operating-sheet snapshot of the "
                     "post-expansion SPP cut (East BA=SWPP; West "
                     "BA=WACM/WAUW plus Platte River and Deseret "
                     "plant-level overrides), adjusted to Dec 31, 2025 "
                     "(minus in-service Jan-Sep 2026, plus retired "
                     "actuals 2026). EIA-derived; no published SPP "
                     "nameplate-by-fuel anchor exists for the "
                     "post-expansion footprint.",
            "total_mw": adiag["anchor_total_mw"],
            "by_fuel_mw": adiag["anchor_by_fuel_mw"],
            "by_region_mw": adiag["anchor_by_region_mw"],
            "by_region_fuel_mw": adiag["anchor_by_region_fuel_mw"],
            "capacity_definition": "Nameplate MW, all statuses (OP/SB/OA/OS).",
            "cross_checks": {
                "spp_101_aug2026_nameplate_east_mw": 110753,
                "spp_101_aug2026_nameplate_west_mw": 10069,
                "spp_101_note": "SPP 101 (Aug 1, 2026): nameplate "
                    "generating capacity East 110,753 MW / West "
                    "10,069 MW, as of Jul-Aug 2026 — i.e. AFTER 2026 "
                    "additions and on SPP's registered-resource basis. "
                    "This build's EIA snapshot (Sep 30, 2026, all "
                    "statuses) is lower in the East and higher in the "
                    "West; see README gap discussion.",
                "spp_som_2025_market_nameplate_mw": "~105,700 (SPP State "
                    "of the Market 2025: wind 35,934 MW nameplate = 34% "
                    "of installed nameplate at end-2025, legacy East "
                    "market only, registered resources)",
                "spp_deliverability_winter2025_registered_mw": 104480.4,
                "spp_deliverability_note": "SPP 2025 Winter "
                    "Deliverability Study, Table 1: max capacity of "
                    "resources registered in the Integrated Marketplace "
                    "as of Mar 1, 2025 (legacy footprint).",
                "eia_operating_sep2026_cut_nameplate_mw":
                    adiag["eia_operating_spp_nameplate_mw"],
                "eia_operating_sep2026_cut_netsummer_mw":
                    adiag["eia_operating_spp_netsummer_mw"],
            },
        },
        "trailing": {
            "basis": "Reconstructed Dec-31 snapshots from EIA unit-level "
                     "data on the constant post-expansion footprint. "
                     "Estimated. West 2016-2025 is pro-forma: the West "
                     "BAA did not exist before Apr 1, 2026.",
            "yearly_totals_mw": {str(int(y)): round(float(v), 1)
                                 for y, v in tot.items() if y <= 2025},
        },
        "forward_2026_2036": {
            "additions_mw": round(float(changelog["additions_mw"].sum()), 1),
            "additions_count": int(changelog["additions_count"].sum()),
            "retirements_mw": round(float(changelog["retirements_mw"].sum()), 1),
            "retirements_count": int(changelog["retirements_count"].sum()),
            "net_mw": round(float(changelog["net_mw"].sum()), 1),
            "additions_by_fuel_mw": agg(changelog, "additions_mw"),
            "retirements_by_fuel_mw": agg(changelog, "retirements_mw"),
            "additions_by_region_mw": {
                rg: round(float(changelog_region[
                    changelog_region["region"] == rg]
                    ["additions_mw"].sum()), 1) for rg in REGIONS},
            "retirements_by_region_mw": {
                rg: round(float(changelog_region[
                    changelog_region["region"] == rg]
                    ["retirements_mw"].sum()), 1) for rg in REGIONS},
            "net_by_region_mw": {
                rg: round(float(changelog_region[
                    changelog_region["region"] == rg]
                    ["net_mw"].sum()), 1) for rg in REGIONS},
        },
        "yearly_totals_mw": {str(int(k)): round(float(v), 1)
                             for k, v in tot.items()},
        "yearly_totals_by_region_mw": {
            rg: {str(int(y)): round(float(
                stack_wide[stack_wide["year"] == y][f"{rg} Total"].iloc[0]), 1)
                for y in range(2016, 2037)} for rg in REGIONS},
        "regions": {
            "definition": "SPP East = legacy RTO footprint, East BAA "
                          "(EIA Balancing Authority Code SWPP). SPP West "
                          "= RTO expansion footprint, West BAA (EIA codes "
                          "WACM + WAUW, the two BAs SPP consolidated into "
                          "the West BAA on Apr 1, 2026) plus plant-level "
                          "overrides for Platte River Power Authority "
                          "(Rawhide, filed under PSCO) and Deseret G&T "
                          "(Bonanza/Solomon, filed under PACE).",
            "expansion_effective": "April 1, 2026 (live, integrated; "
                          "FERC RTO Expansion Order Mar 20, 2025, "
                          "190 FERC 61,169; SPP announcement Apr 2, 2026).",
            "markets_plus_note": "Markets+ is a separate day-ahead "
                          "market service, not RTO membership. APS, SRP, "
                          "TEP, UniSource (Markets+) and PNM (EDAM) "
                          "plants are NOT in this stack.",
        },
        "diagnostics": {**adiag, **cdiag},
        "files": {
            "plants": "spp_capacity_plants.csv",
            "stack": "spp_capacity_stack.csv",
            "stack_by_eastwest": "spp_capacity_stack_by_eastwest.csv",
            "changelog": "spp_capacity_changelog.csv",
            "changelog_by_eastwest": "spp_capacity_changelog_by_eastwest.csv",
            "summary": "summary.json",
            "charts": ["01_stacked_area.png", "02_net_change_forward.png",
                       "03_eastwest_stacked.png", "04_eastwest_totals.png"],
        },
    }
    with open(BASE / "summary.json", "w") as f:
        json.dump(summary, f, indent=2)
    print("  wrote plants/stack/changelog CSVs + summary.json")
    make_charts(stack_wide, changelog)
    print("  yearly totals (SPP Combined):")
    for y in range(2025, 2037):
        print(f"    {y}: {tot[y]:,.1f} MW")
    return summary


if __name__ == "__main__":
    main()
