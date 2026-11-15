#!/usr/bin/env python3
"""Build DSW capacity stack v1 — EIA-only.

Mirrors the MISO v1 method (~/workspace/miso-capacity-stack/build_stack.py),
which mirrors PJM: trailing + forward 10-year stack 2016-2036 by fuel
(Coal, Natural Gas, Nuclear, Hydro, Pumped Storage, Wind, Solar, Oil,
Battery Storage, Other), nameplate MW throughout, anchor Dec 31 2025,
forward = anchor + changelog.

REGION CUT — WORKING DEFINITION (working assumption, stated verbatim):
DSW = Desert Southwest = plants in AZ and NM. Implemented as
Plant State in {AZ, NM}. There is no single DSW balancing authority;
the cut is geographic (state), not BA-based. Every BA code found in
AZ/NM is inventoried in summary.json / README.md.

DSW differences from MISO (documented, not hidden):
- Anchor: NO published DSW-by-fuel anchor exists. Per the MISO
  fallback, the anchor is the EIA-860M Operating-sheet snapshot,
  adjusted to Dec 31 2025 (minus units in service Jan-Sep 2026, plus
  Retired-sheet actual retirements in 2026 — zero in DSW), nameplate
  MW, all statuses. It is EIA-derived, stated explicitly.
- Trailing 2016-2025: RECONSTRUCTED from EIA unit-level data
  (Operating Year / Retirement Year), labelled estimated.
- No subregions: DSW is a single region (region column = "DSW").
- No RMR-style override.

Changelog source: EIA-860M September 2026 vintage (data as of
Sep 30, 2026), Plant State in {AZ, NM}, same file the PJM/MISO stacks
used: ~/workspace/pjm-capacity-stack/raw/eia860m_sep2026.xlsx
Additions: units in service in 2026 (Operating sheet, Operating Year
== 2026) + Planned sheet units.
Retirements: Retired sheet actuals with Retirement Year == 2026 +
Operating sheet planned retirements.

The build asserts: (1) snapshot(2025) == anchor exactly;
(2) forward stack == anchor + cumulative changelog.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

BASE = Path(__file__).resolve().parent
EIA_FILE = Path("/home/hatch/workspace/pjm-capacity-stack/raw/eia860m_sep2026.xlsx")
ANCHOR_YEAR = 2025
DSW_STATES = ["AZ", "NM"]
REGION = "DSW"
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


def is_dsw(df):
    return df["Plant State"].isin(DSW_STATES)


# ---------------- Anchor (EIA-derived, Dec 31 2025) ----------------
def build_anchor(op, rt):
    diag = {}
    d_op = op[is_dsw(op)].copy()
    d_rt = rt[is_dsw(rt)].copy()
    diag["eia_operating_dsw_units"] = int(len(d_op))
    diag["eia_operating_dsw_nameplate_mw"] = round(
        d_op["Nameplate Capacity (MW)"].sum(), 1)
    diag["eia_operating_dsw_netsummer_mw"] = round(
        d_op["Net Summer Capacity (MW)"].sum(), 1)
    op_only = d_op[d_op["Status"] == "(OP) Operating"]
    diag["eia_operating_dsw_op_only_nameplate_mw"] = round(
        op_only["Nameplate Capacity (MW)"].sum(), 1)
    diag["eia_operating_dsw_nonop_nameplate_mw"] = round(
        d_op[d_op["Status"] != "(OP) Operating"]
        ["Nameplate Capacity (MW)"].sum(), 1)
    diag["ba_inventory_operating_snapshot_mw"] = {
        k: round(v, 1) for k, v in
        d_op.groupby("Balancing Authority Code")
        ["Nameplate Capacity (MW)"].sum().sort_values(ascending=False).items()}
    diag["ba_inventory_operating_snapshot_units"] = {
        k: int(v) for k, v in
        d_op.groupby("Balancing Authority Code").size().items()}

    in_service_2026 = d_op[pd.to_numeric(
        d_op["Operating Year"], errors="coerce") == 2026]
    rt26 = d_rt[pd.to_numeric(
        d_rt["Retirement Year"], errors="coerce") == 2026]
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

    base = d_op[pd.to_numeric(
        d_op["Operating Year"], errors="coerce") <= 2025].copy()
    anchor_by_fuel = {
        f: round(base[base["fuel"] == f]["Nameplate Capacity (MW)"].sum()
                 + rt26[rt26["fuel"] == f]["Nameplate Capacity (MW)"].sum(), 1)
        for f in FUELS}
    anchor_total = round(sum(anchor_by_fuel.values()), 1)
    diag["anchor_total_mw"] = anchor_total
    diag["anchor_by_fuel_mw"] = anchor_by_fuel
    diag["anchor_by_state_mw"] = {
        s: round(base[base["Plant State"] == s]
                 ["Nameplate Capacity (MW)"].sum()
                 + rt26[rt26["Plant State"] == s]
                 ["Nameplate Capacity (MW)"].sum(), 1)
        for s in DSW_STATES}
    diag["anchor_by_ba_mw"] = {
        k: round(v, 1) for k, v in
        base.groupby("Balancing Authority Code")
        ["Nameplate Capacity (MW)"].sum().sort_values(ascending=False).items()}

    # Edge cases (documented in README.md)
    epe_op = op[op["Balancing Authority Code"] == "EPE"]
    diag["edge_epe_tx_operating_mw"] = round(
        epe_op[epe_op["Plant State"] == "TX"]
        ["Nameplate Capacity (MW)"].sum(), 1)
    diag["edge_epe_tx_operating_units"] = int(
        len(epe_op[epe_op["Plant State"] == "TX"]))
    diag["edge_epe_nm_operating_mw"] = round(
        epe_op[epe_op["Plant State"] == "NM"]
        ["Nameplate Capacity (MW)"].sum(), 1)
    walc_op = op[op["Balancing Authority Code"] == "WALC"]
    diag["edge_walc_by_state_operating_mw"] = {
        k: round(v, 1) for k, v in
        walc_op.groupby("Plant State")["Nameplate Capacity (MW)"]
        .sum().items()}
    hoover_nv = walc_op[walc_op["Plant Name"] == "Hoover Dam (NV)"]
    hoover_az = walc_op[walc_op["Plant Name"] == "Hoover Dam (AZ)"]
    diag["edge_hoover_nv_mw"] = round(
        hoover_nv["Nameplate Capacity (MW)"].sum(), 1)
    diag["edge_hoover_az_mw"] = round(
        hoover_az["Nameplate Capacity (MW)"].sum(), 1)
    nevp = op[op["Balancing Authority Code"] == "NEVP"]
    diag["edge_nevp_total_operating_mw"] = round(
        nevp["Nameplate Capacity (MW)"].sum(), 1)
    pv = d_op[d_op["Plant Name"] == "Palo Verde"]
    diag["palo_verde_units"] = [
        {"generator_id": str(r["Generator ID"]),
         "mw_nameplate": round(float(r["Nameplate Capacity (MW)"]), 1),
         "mw_net_summer": round(float(r["Net Summer Capacity (MW)"]), 1),
         "operating_year": int(r["Operating Year"])}
        for _, r in pv.iterrows()]
    diag["palo_verde_total_mw"] = round(
        pv["Nameplate Capacity (MW)"].sum(), 1)
    return anchor_by_fuel, diag, base, rt26


# ---------------- Trailing (reconstructed from EIA unit data) ----------------
def trailing_reconstructed(op, rt):
    d_op = op[is_dsw(op)].copy()
    d_rt = rt[is_dsw(rt)].copy()
    d_op["_oy"] = pd.to_numeric(d_op["Operating Year"], errors="coerce")
    d_rt["_oy"] = pd.to_numeric(d_rt["Operating Year"], errors="coerce")
    d_rt["_ry"] = pd.to_numeric(d_rt["Retirement Year"], errors="coerce")
    assert d_op["_oy"].notna().all(), "Operating Year missing on Operating"
    assert d_rt["_oy"].notna().all(), "Operating Year missing on Retired"
    assert d_rt["_ry"].notna().all(), "Retirement Year missing on Retired"
    rows = []
    for y in range(2016, 2026):
        snap_op = d_op[d_op["_oy"] <= y]
        snap_rt = d_rt[(d_rt["_oy"] <= y) & (d_rt["_ry"] > y)]
        snap = pd.concat([snap_op, snap_rt], ignore_index=True)
        r = {"year": y, "period": "trailing",
             "source_note": "EIA-860M reconstructed Dec-31 snapshot "
                            "(unit Operating Year / Retirement Year). Estimated."}
        for f in FUELS:
            r[f] = round(
                snap[snap["fuel"] == f]["Nameplate Capacity (MW)"].sum(), 1)
        r["Total"] = round(snap["Nameplate Capacity (MW)"].sum(), 1)
        rows.append(r)
    return pd.DataFrame(rows)


# ---------------- Forward changelog (EIA) ----------------
def eia_changelog(op, pl, rt):
    d_op = op[is_dsw(op)].copy()
    d_pl = pl[is_dsw(pl)].copy()
    d_rt = rt[is_dsw(rt)].copy()
    diag = {}
    diag["eia_planned_dsw_units"] = int(len(d_pl))
    diag["eia_planned_dsw_nameplate_mw"] = round(
        d_pl["Nameplate Capacity (MW)"].sum(), 1)
    diag["eia_planned_dsw_by_status_mw"] = {
        k: round(v, 1) for k, v in
        d_pl.groupby("Status")["Nameplate Capacity (MW)"].sum().items()}
    diag["eia_planned_under_construction_mw"] = round(
        d_pl[d_pl["Status"].str.contains(
            "Under construction|Construction complete", na=False)]
        ["Nameplate Capacity (MW)"].sum(), 1)
    diag["eia_planned_max_operation_year"] = int(pd.to_numeric(
        d_pl["Planned Operation Year"], errors="coerce").max())

    adds = []
    in_service_2026 = d_op[pd.to_numeric(
        d_op["Operating Year"], errors="coerce") == 2026]
    for _, r in in_service_2026.iterrows():
        adds.append(_plant_row(
            r, "addition", "addition", int(r["Operating Year"]),
            int(pd.to_numeric(r["Operating Month"], errors="coerce") or 1),
            "Operating sheet: in service Jan-Sep 2026", REGION))
    for _, r in d_pl.iterrows():
        y = pd.to_numeric(r["Planned Operation Year"], errors="coerce")
        m = pd.to_numeric(r["Planned Operation Month"], errors="coerce")
        if pd.isna(y):
            continue
        adds.append(_plant_row(r, "addition", "addition", int(y),
                               int(m) if not pd.isna(m) else 1,
                               "Planned sheet", REGION))
    adds_df = pd.DataFrame(adds)

    rets = []
    rt26 = d_rt[pd.to_numeric(
        d_rt["Retirement Year"], errors="coerce") == 2026]
    for _, r in rt26.iterrows():
        rets.append(_plant_row(
            r, "retirement", "retired (actual)",
            int(r["Retirement Year"]),
            int(pd.to_numeric(r["Retirement Month"], errors="coerce") or 1),
            "Retired sheet: actual Jan-Sep 2026", REGION))
    pr = d_op[pd.to_numeric(
        d_op["Planned Retirement Year"], errors="coerce").notna()].copy()
    for _, r in pr.iterrows():
        y = int(pd.to_numeric(r["Planned Retirement Year"], errors="coerce"))
        m = pd.to_numeric(r["Planned Retirement Month"], errors="coerce")
        rets.append(_plant_row(r, "retirement", "planned retirement", y,
                               int(m) if not pd.isna(m) else 1,
                               "Operating sheet: planned retirement",
                               REGION))
    rets_df = pd.DataFrame(rets)

    key = lambda d: set(zip(d["Plant ID"].astype(str),
                            d["Generator ID"].astype(str)))
    diag["overlap_operating2026_vs_planned2026_units"] = len(
        key(in_service_2026) & key(d_pl[
            d_pl["Planned Operation Year"] == 2026]))
    diag["overlap_retired2026_vs_plannedret2026_units"] = len(
        key(rt26) & key(d_op[pd.to_numeric(
            d_op["Planned Retirement Year"], errors="coerce") == 2026]))

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
    diag["planned_total_mw_2026_2036"] = round(
        adds_df[adds_df["effective_year"].between(2026, 2036)]
        ["mw_nameplate"].sum(), 1)
    return changelog, plants, diag, adds_df, rets_df


# ---------------- Build, outputs, charts ----------------
def build_stack(trailing_df, changelog, anchor_by_fuel):
    rows = []
    running = {f: float(anchor_by_fuel[f]) for f in FUELS}
    for y in range(2026, 2037):
        net = changelog[changelog["year"] == y]
        for f in FUELS:
            running[f] += float(net.loc[net["fuel"] == f, "net_mw"].iloc[0])
        r = {"year": y, "period": "forward",
             "source_note": "EIA-860M Dec-31-2025 anchor + EIA-860M changelog "
                            "(effective dates, nameplate MW)"}
        r.update({f: round(running[f], 1) for f in FUELS})
        r["Total"] = round(sum(running.values()), 1)
        rows.append(r)
    fwd = pd.DataFrame(rows)
    stack_wide = pd.concat([trailing_df, fwd], ignore_index=True)
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
    return stack_wide, pd.DataFrame(long_rows)


def make_charts(stack_wide, changelog, suffix=""):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    years = stack_wide["year"].values
    ver = "v2" if suffix else "v1"
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
    ax.set_title(f"DSW (AZ+NM) generation capacity stack by fuel, 2016-2036 — {ver}\n"
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
    bottom = np.zeros(len(piv)); top = np.zeros(len(piv))
    for f in STACK_ORDER:
        v = piv[f].values
        pos = np.where(v > 0, v, 0); neg = np.where(v < 0, v, 0)
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
    ax.set_title(f"DSW annual net capacity change by fuel, forward 2026-2036 — {ver}\n"
                 "(additions/retirements, nameplate)", fontsize=11)
    ax.legend(ncol=2, fontsize=9, loc="upper right")
    ax.grid(True, alpha=0.3, axis="y")
    fig.tight_layout()
    fig.savefig(BASE / f"02_net_change_forward{suffix}.png", dpi=150)
    plt.close(fig)
    print("  charts written")


def main():
    op = load_eia_sheet("Operating")
    pl = load_eia_sheet("Planned")
    rt = load_eia_sheet("Retired")
    for df in (op, pl, rt):
        df["fuel"] = df.apply(eia_fuel, axis=1)

    anchor_by_fuel, adiag, _, _ = build_anchor(op, rt)
    print(f"  anchor Dec 31 2025: {adiag['anchor_total_mw']:,.1f} MW "
          f"(EIA-derived, nameplate)")
    print(f"  anchor by state: {adiag['anchor_by_state_mw']}")
    print(f"  anchor by BA: {adiag['anchor_by_ba_mw']}")

    trailing_df = trailing_reconstructed(op, rt)
    snap25 = trailing_df[trailing_df["year"] == 2025].iloc[0]
    assert abs(snap25["Total"] - adiag["anchor_total_mw"]) < 0.05, (
        snap25["Total"], adiag["anchor_total_mw"])
    for f in FUELS:
        assert abs(snap25[f] - anchor_by_fuel[f]) < 0.05, (f, snap25[f])
    print("  trailing reconstruction reproduces the anchor at 2025: OK")

    changelog, plants, cdiag, adds_df, rets_df = eia_changelog(op, pl, rt)
    fwd_rets = rets_df[rets_df["effective_year"].between(2026, 2036)]
    print(f"  forward additions 2026-2036: "
          f"{cdiag['planned_total_mw_2026_2036']:,.1f} MW "
          f"({len(adds_df)} units); retirements: "
          f"{fwd_rets['mw_nameplate'].sum():,.1f} MW ({len(fwd_rets)} units)")
    assert cdiag["overlap_operating2026_vs_planned2026_units"] == 0
    assert cdiag["overlap_retired2026_vs_plannedret2026_units"] == 0
    print("  overlap guards: 0 / 0 OK")

    stack_wide, long_total = build_stack(trailing_df, changelog, anchor_by_fuel)
    # Assertion: anchor + cumulative changelog == yearly totals.
    tot_check = adiag["anchor_total_mw"] + changelog["net_mw"].sum()
    assert abs(tot_check - float(stack_wide[stack_wide["year"] == 2036]["Total"].iloc[0])) < 0.05
    print("  anchor + cumulative changelog = 2036 total: OK")

    plants.to_csv(BASE / "dsw_capacity_plants.csv", index=False)
    long_total.to_csv(BASE / "dsw_capacity_stack.csv", index=False)
    changelog.to_csv(BASE / "dsw_capacity_changelog.csv", index=False)

    def agg(df, col):
        return {f: round(float(df[df["fuel"] == f][col].sum()), 1)
                for f in FUELS}
    tot = stack_wide.set_index("year")["Total"].round(1).to_dict()
    summary = {
        "version": "v1",
        "built": "2026-11-15",
        "region_definition": "DSW = Desert Southwest = plants in AZ and NM. "
                             "Working definition (working assumption): Plant State in {AZ, NM}. "
                             "Geographic state cut, not a balancing-authority cut.",
        "anchor": {
            "basis": "EIA-860M Operating-sheet snapshot adjusted to Dec 31, 2025 "
                     "(minus in-service Jan-Sep 2026, plus retired actuals 2026 = 0.0 MW). "
                     "EIA-derived; no published DSW-by-fuel anchor exists.",
            "total_mw": adiag["anchor_total_mw"],
            "by_fuel_mw": adiag["anchor_by_fuel_mw"],
            "by_state_mw": adiag["anchor_by_state_mw"],
            "by_ba_mw": adiag["anchor_by_ba_mw"],
            "capacity_definition": "Nameplate MW, all statuses (OP/SB/OA/OS).",
            "cross_checks": {
                "eia_operating_sep2026_nameplate_mw": adiag["eia_operating_dsw_nameplate_mw"],
                "eia_operating_sep2026_netsummer_mw": adiag["eia_operating_dsw_netsummer_mw"],
                "palo_verde_mw": adiag["palo_verde_total_mw"],
                "note": "No published DSW-by-fuel table exists to cross-check against; "
                        "APS/SRP/PNM fleet figures are ownership-share based and not "
                        "comparable to EIA full-plant-at-location nameplate.",
            },
        },
        "trailing": {
            "basis": "Reconstructed Dec-31 snapshots from EIA unit-level data "
                     "(Operating Year / Retirement Year). Estimated; not a published series.",
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
        },
        "yearly_totals_mw": {str(int(k)): round(float(v), 1)
                             for k, v in tot.items()},
        "diagnostics": {**adiag, **cdiag},
        "files": {
            "plants": "dsw_capacity_plants.csv",
            "stack": "dsw_capacity_stack.csv",
            "changelog": "dsw_capacity_changelog.csv",
            "summary": "summary.json",
            "charts": ["01_stacked_area.png", "02_net_change_forward.png"],
        },
    }
    with open(BASE / "summary.json", "w") as f:
        json.dump(summary, f, indent=2)
    print("  wrote plants/stack/changelog CSVs + summary.json")
    make_charts(stack_wide, changelog)
    print("  yearly totals (DSW):")
    for y in range(2025, 2037):
        print(f"    {y}: {tot[y]:,.1f} MW")
    return summary


if __name__ == "__main__":
    main()
