#!/usr/bin/env python3
"""Build NYISO capacity stack v1 — EIA-only.

Mirrors the MISO v1 method (~/workspace/miso-capacity-stack/build_stack.py),
which mirrors PJM: trailing + forward 10-year stack 2016-2036 by fuel
(Coal, Natural Gas, Nuclear, Hydro, Pumped Storage, Wind, Solar, Oil,
Battery Storage, Other), nameplate MW throughout, anchor Dec 31 2025,
forward = anchor + changelog.

NYISO differences from MISO (documented, not hidden):
- No regionalization: NYISO is a single-state ISO; the stack is NYCA-wide
  (Balancing Authority Code == NYIS). The `region` column in the plants
  file is carried as "NYISO" to keep the MISO file schema.
- Anchor: NYISO's Gold Book (Load & Capacity Data Report) DOES publish
  installed capacity, but on a summer/winter capability (DMNC/CRIS)
  basis, not nameplate, and it counts market-participating resources
  (plus a separate table for non-market load-modifier units). It is
  therefore used as a cross-check only. The anchor is the EIA-860M
  Operating-sheet snapshot, adjusted to Dec 31 2025 (minus units in
  service Jan-Sep 2026, plus 2026 retired actuals), nameplate MW, all
  statuses. It is EIA-derived, stated explicitly — not a NYISO
  publication. See README.md / summary.json for the definitional gap.
- Trailing 2016-2025: no nameplate-by-fuel history is published, so the
  trailing is RECONSTRUCTED from EIA unit-level data (Operating Year and
  Retirement Year), labelled estimated. It is not a NYISO publication.
  Indian Point Unit 2 (retired Apr 2020, 1,299.0 MW nameplate) and
  Unit 3 (retired Apr 2021, 1,012.0 MW) appear naturally in it.
- No RMR-style override: the PJM coal-delay-to-Jan-2029 override was a
  user-directed PJM scenario, not a general rule. NYISO retirements are
  taken at their EIA dates in v1; the large deactivations EIA misses
  (Danskammer, the Gowanus/Narrows barges under the DEC Peaker Rule)
  are corrected on plant-specific evidence in v2 only.

Changelog source: EIA-860M September 2026 vintage (data as of Sep 30,
2026; released Oct 23, 2026), Balancing Authority Code == NYIS, same
file the PJM/MISO stacks used:
~/workspace/pjm-capacity-stack/raw/eia860m_sep2026.xlsx
Additions: units in service in 2026 (Operating sheet, Operating Year
== 2026) + Planned sheet units.
Retirements: Retired sheet actuals with Retirement Year == 2026 +
Operating sheet planned retirements.

The build asserts: (1) snapshot(2025) == anchor exactly (internal
consistency of the trailing reconstruction); (2) forward stack ==
anchor + cumulative changelog; (3) overlap guards are zero.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

BASE = Path(__file__).resolve().parent
EIA_FILE = Path("/home/hatch/workspace/pjm-capacity-stack/raw/eia860m_sep2026.xlsx")
ANCHOR_YEAR = 2025
BA_CODE = "NYIS"
REGION = "NYISO"
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


def _plant_row(r, typ, status_label, year, month, source):
    """One unit-level changelog row from an EIA-860M record."""
    return {
        "plant_name": r["Plant Name"],
        "plant_id": r["Plant ID"],
        "generator_id": str(r["Generator ID"]),
        "state": r["Plant State"],
        "county": r.get("County", ""),
        "region": REGION,
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
    (anchor_by_fuel, diagnostics).
    """
    diag = {}
    ny_op = op[op["Balancing Authority Code"] == BA_CODE].copy()
    ny_rt = rt[rt["Balancing Authority Code"] == BA_CODE].copy()
    diag["eia_operating_nyis_units"] = int(len(ny_op))
    diag["eia_operating_nyis_nameplate_mw"] = round(
        ny_op["Nameplate Capacity (MW)"].sum(), 1)
    diag["eia_operating_nyis_netsummer_mw"] = round(
        ny_op["Net Summer Capacity (MW)"].sum(), 1)
    op_only = ny_op[ny_op["Status"] == "(OP) Operating"]
    diag["eia_operating_nyis_op_only_nameplate_mw"] = round(
        op_only["Nameplate Capacity (MW)"].sum(), 1)
    diag["eia_operating_nyis_op_only_netsummer_mw"] = round(
        op_only["Net Summer Capacity (MW)"].sum(), 1)
    diag["eia_operating_nyis_nonop_nameplate_mw"] = round(
        ny_op[ny_op["Status"] != "(OP) Operating"]
        ["Nameplate Capacity (MW)"].sum(), 1)
    diag["eia_operating_nyis_by_status_mw"] = {
        k: round(v, 1) for k, v in
        ny_op.groupby("Status")["Nameplate Capacity (MW)"].sum().items()}
    diag["eia_operating_nyis_by_fuel_nameplate"] = {
        f: round(v, 1) for f, v in
        ny_op.groupby("fuel")["Nameplate Capacity (MW)"].sum().items()}
    diag["eia_operating_nyis_by_fuel_netsummer"] = {
        f: round(v, 1) for f, v in
        ny_op.groupby("fuel")["Net Summer Capacity (MW)"].sum().items()}

    # BA boundary cross-checks. NYIS includes a small number of plants
    # physically in NJ (Bayonne Energy Center and two small NJ solar
    # units deliver into NYCA); conversely a small amount of NY-state
    # capacity sits under other BAs.
    out_state = ny_op[ny_op["Plant State"] != "NY"]
    diag["ba_boundary_nyis_outside_ny_mw"] = round(
        out_state["Nameplate Capacity (MW)"].sum(), 1)
    diag["ba_boundary_nyis_outside_ny_units"] = int(len(out_state))
    diag["ba_boundary_nyis_outside_ny_by_state_mw"] = {
        k: round(v, 1) for k, v in
        out_state.groupby("Plant State")["Nameplate Capacity (MW)"]
        .sum().items()}
    in_ny = op[op["Plant State"] == "NY"]
    out_ba = in_ny[in_ny["Balancing Authority Code"] != BA_CODE]
    diag["ba_boundary_ny_state_not_nyis_mw"] = round(
        out_ba["Nameplate Capacity (MW)"].sum(), 1)
    diag["ba_boundary_ny_state_not_nyis_units"] = int(len(out_ba))
    diag["ba_boundary_ny_state_not_nyis_by_ba_mw"] = {
        k: round(v, 1) for k, v in
        out_ba.groupby("Balancing Authority Code")
        ["Nameplate Capacity (MW)"].sum().items()}

    # Adjustment to Dec 31, 2025.
    in_service_2026 = ny_op[pd.to_numeric(
        ny_op["Operating Year"], errors="coerce") == 2026]
    rt26 = ny_rt[pd.to_numeric(
        ny_rt["Retirement Year"], errors="coerce") == 2026]
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

    base = ny_op[pd.to_numeric(
        ny_op["Operating Year"], errors="coerce") <= 2025].copy()
    anchor_by_fuel = {
        f: round(base[base["fuel"] == f]["Nameplate Capacity (MW)"].sum()
                 + rt26[rt26["fuel"] == f]["Nameplate Capacity (MW)"].sum(), 1)
        for f in FUELS}
    diag["anchor_total_mw"] = round(sum(anchor_by_fuel.values()), 1)
    diag["anchor_by_fuel_mw"] = anchor_by_fuel
    return anchor_by_fuel, diag


# ---------------- Trailing (reconstructed from EIA unit data) ----------------
def trailing_reconstructed(op, rt):
    """Dec-31 snapshots 2016-2025 reconstructed from EIA unit-level data.

    For year Y: Operating-sheet units with Operating Year <= Y, plus
    Retired-sheet units with Operating Year <= Y < Retirement Year.
    Planned Retirement Year is deliberately NOT used: it reflects plans
    as of Sep 2026, not history (a slipped plan would wrongly remove a
    unit from earlier snapshots). Labelled estimated in the outputs.
    """
    ny_op = op[op["Balancing Authority Code"] == BA_CODE].copy()
    ny_rt = rt[rt["Balancing Authority Code"] == BA_CODE].copy()
    ny_op["_oy"] = pd.to_numeric(ny_op["Operating Year"], errors="coerce")
    ny_rt["_oy"] = pd.to_numeric(ny_rt["Operating Year"], errors="coerce")
    ny_rt["_ry"] = pd.to_numeric(ny_rt["Retirement Year"], errors="coerce")
    assert ny_op["_oy"].notna().all(), "Operating Year missing on Operating"
    assert ny_rt["_oy"].notna().all(), "Operating Year missing on Retired"
    assert ny_rt["_ry"].notna().all(), "Retirement Year missing on Retired"
    rows = []
    for y in range(2016, 2026):
        snap_op = ny_op[ny_op["_oy"] <= y]
        snap_rt = ny_rt[(ny_rt["_oy"] <= y) & (ny_rt["_ry"] > y)]
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
    """Forward changelog from EIA-860M (BA == NYIS). No override.

    Additions: units in service in 2026 (Operating, Operating Year == 2026)
    + Planned sheet units.
    Retirements: Retired sheet actuals with Retirement Year == 2026 +
    Operating sheet planned retirements.
    Returns (changelog_df, plants_df, diagnostics, adds_df, rets_df).
    """
    ny_op = op[op["Balancing Authority Code"] == BA_CODE].copy()
    ny_pl = pl[pl["Balancing Authority Code"] == BA_CODE].copy()
    ny_rt = rt[rt["Balancing Authority Code"] == BA_CODE].copy()

    diag = {}
    diag["eia_planned_nyis_units"] = int(len(ny_pl))
    diag["eia_planned_nyis_nameplate_mw"] = round(
        ny_pl["Nameplate Capacity (MW)"].sum(), 1)
    diag["eia_planned_nyis_by_status_mw"] = {
        k: round(v, 1) for k, v in
        ny_pl.groupby("Status")["Nameplate Capacity (MW)"].sum().items()}
    diag["eia_planned_nyis_by_status_units"] = {
        k: int(v) for k, v in ny_pl.groupby("Status").size().items()}
    diag["eia_planned_under_construction_mw"] = round(
        ny_pl[ny_pl["Status"].str.contains(
            "Under construction|Construction complete", na=False)]
        ["Nameplate Capacity (MW)"].sum(), 1)
    diag["eia_planned_not_under_construction_mw"] = round(
        diag["eia_planned_nyis_nameplate_mw"]
        - diag["eia_planned_under_construction_mw"], 1)
    diag["eia_planned_max_operation_year"] = int(pd.to_numeric(
        ny_pl["Planned Operation Year"], errors="coerce").max())

    # ---- Additions ----
    adds = []
    in_service_2026 = ny_op[pd.to_numeric(
        ny_op["Operating Year"], errors="coerce") == 2026]
    for _, r in in_service_2026.iterrows():
        adds.append(_plant_row(
            r, "addition", "addition", int(r["Operating Year"]),
            int(pd.to_numeric(r["Operating Month"], errors="coerce") or 1),
            "Operating sheet: in service Jan-Sep 2026"))
    for _, r in ny_pl.iterrows():
        y = pd.to_numeric(r["Planned Operation Year"], errors="coerce")
        m = pd.to_numeric(r["Planned Operation Month"], errors="coerce")
        if pd.isna(y):
            continue
        adds.append(_plant_row(r, "addition", "addition", int(y),
                               int(m) if not pd.isna(m) else 1,
                               "Planned sheet"))
    adds_df = pd.DataFrame(adds)

    # ---- Retirements ----
    rets = []
    rt26 = ny_rt[pd.to_numeric(
        ny_rt["Retirement Year"], errors="coerce") == 2026]
    for _, r in rt26.iterrows():
        rets.append(_plant_row(
            r, "retirement", "retired (actual)",
            int(r["Retirement Year"]),
            int(pd.to_numeric(r["Retirement Month"], errors="coerce") or 1),
            "Retired sheet: actual Jan-Sep 2026"))
    pr = ny_op[pd.to_numeric(
        ny_op["Planned Retirement Year"], errors="coerce").notna()].copy()
    for _, r in pr.iterrows():
        y = int(pd.to_numeric(r["Planned Retirement Year"], errors="coerce"))
        m = pd.to_numeric(r["Planned Retirement Month"], errors="coerce")
        rets.append(_plant_row(r, "retirement", "planned retirement", y,
                               int(m) if not pd.isna(m) else 1,
                               "Operating sheet: planned retirement"))
    rets_df = pd.DataFrame(rets)

    # Overlap guards (would double-count if > 0).
    key = lambda d: set(zip(d["Plant ID"].astype(str),
                            d["Generator ID"].astype(str)))
    diag["overlap_operating2026_vs_planned2026_units"] = len(
        key(in_service_2026) & key(ny_pl[
            ny_pl["Planned Operation Year"] == 2026]))
    diag["overlap_retired2026_vs_plannedret2026_units"] = len(
        key(rt26) & key(ny_op[pd.to_numeric(
            ny_op["Planned Retirement Year"], errors="coerce") == 2026]))
    assert diag["overlap_operating2026_vs_planned2026_units"] == 0
    assert diag["overlap_retired2026_vs_plannedret2026_units"] == 0

    plants = pd.concat([adds_df, rets_df], ignore_index=True)
    plants = plants.sort_values(["effective_year", "type", "fuel",
                                 "plant_name"])

    # ---- Changelog by year x fuel ----
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
    diag["retirements_2026_actual_mw"] = round(
        rt26["Nameplate Capacity (MW)"].sum(), 1)
    return changelog, plants, diag, adds_df, rets_df


# ---------------- Build, outputs, charts ----------------
def build_stack(trailing_df, changelog, anchor_by_fuel):
    """Forward stack: anchor (Dec 31, 2025) + cumulative net changelog.

    Returns (stack_wide, stack_long). Asserts the forward stack equals
    anchor + cumulative changelog by construction and checks the 2025
    trailing row equals the anchor.
    """
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


def make_charts(stack_wide, changelog):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    years = stack_wide["year"].values
    # 1. Stacked area, NYISO total, 2016-2036, GW.
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
    ax.set_title("NYISO generation capacity stack by fuel, 2016-2036 — v1\n"
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
    ax.set_title("NYISO annual net capacity change by fuel, forward 2026-2036 — v1\n"
                 "(EIA-860M additions/retirements, nameplate)", fontsize=11)
    ax.legend(ncol=2, fontsize=9, loc="upper right")
    ax.grid(True, alpha=0.3, axis="y")
    fig.tight_layout()
    fig.savefig(BASE / "02_net_change_forward.png", dpi=150)
    plt.close(fig)
    print("  charts written")


def main():
    op = load_eia_sheet("Operating")
    pl = load_eia_sheet("Planned")
    rt = load_eia_sheet("Retired")
    for df in (op, pl, rt):
        df["fuel"] = df.apply(eia_fuel, axis=1)

    anchor_by_fuel, adiag = build_anchor(op, rt)
    print(f"  anchor Dec 31 2025: {adiag['anchor_total_mw']:,.1f} MW "
          f"(EIA-derived, nameplate)")

    trailing_df = trailing_reconstructed(op, rt)
    # Internal consistency: reconstructed 2025 snapshot == anchor exactly.
    snap25 = trailing_df[trailing_df["year"] == 2025].iloc[0]
    assert abs(snap25["Total"] - adiag["anchor_total_mw"]) < 0.05, (
        snap25["Total"], adiag["anchor_total_mw"])
    for f in FUELS:
        assert abs(snap25[f] - anchor_by_fuel[f]) < 0.05, (f, snap25[f])
    print("  trailing reconstruction reproduces the anchor at 2025: OK")
    # Indian Point sanity check: nuclear falls by IP2 in 2020, IP3 in 2021.
    nuc = trailing_df.set_index("year")["Nuclear"].to_dict()
    print(f"  trailing nuclear MW: 2019 {nuc[2019]:,.1f} -> 2020 {nuc[2020]:,.1f} "
          f"(Indian Point 2, -1,299.0) -> 2021 {nuc[2021]:,.1f} "
          f"(Indian Point 3, -1,012.0) -> 2025 {nuc[2025]:,.1f}")
    assert abs((nuc[2019] - nuc[2020]) - 1299.0) < 0.05
    assert abs((nuc[2020] - nuc[2021]) - 1012.0) < 0.05
    print("  Indian Point retirements appear in trailing as expected: OK")

    changelog, plants, cdiag, adds_df, rets_df = eia_changelog(op, pl, rt)
    in_win_ret = rets_df[rets_df["effective_year"].between(2026, 2036)]
    print(f"  forward additions 2026-2036: "
          f"{cdiag['planned_total_mw_2026_2036']:,.1f} MW "
          f"({len(adds_df[adds_df['effective_year'].between(2026, 2036)])} units); "
          f"retirements: {in_win_ret['mw_nameplate'].sum():,.1f} MW "
          f"({len(in_win_ret)} units)")
    print(f"  overlap guards: "
          f"{cdiag['overlap_operating2026_vs_planned2026_units']} / "
          f"{cdiag['overlap_retired2026_vs_plannedret2026_units']} (both must be 0)")

    stack_wide, long_total = build_stack(trailing_df, changelog, anchor_by_fuel)
    # Assertion: forward stack == anchor + cumulative changelog.
    run = dict(anchor_by_fuel)
    for y in range(2026, 2037):
        for f in FUELS:
            run[f] += float(changelog[(changelog["year"] == y)
                                      & (changelog["fuel"] == f)]["net_mw"].iloc[0])
        row = stack_wide[stack_wide["year"] == y].iloc[0]
        for f in FUELS:
            assert abs(row[f] - run[f]) < 0.05, (y, f)
    print("  forward stack == anchor + cumulative changelog: OK")

    # ---- Write outputs (v1 files only; v2 never overwrites these) ----
    plants.to_csv(BASE / "nyiso_capacity_plants.csv", index=False)
    long_total.to_csv(BASE / "nyiso_capacity_stack.csv", index=False)
    changelog.to_csv(BASE / "nyiso_capacity_changelog.csv", index=False)

    def agg(df, col):
        return {f: round(float(df[df["fuel"] == f][col].sum()), 1)
                for f in FUELS}
    fwd_add = agg(changelog, "additions_mw")
    fwd_ret = agg(changelog, "retirements_mw")
    tot = stack_wide.set_index("year")["Total"].round(1).to_dict()
    summary = {
        "version": "v1",
        "built": "2026-11-15",
        "anchor": {
            "basis": "EIA-860M Operating-sheet snapshot adjusted to Dec 31, 2025 "
                     "(minus in-service Jan-Sep 2026, plus retired actuals 2026). "
                     "EIA-derived. NYISO's Gold Book publishes installed capacity "
                     "on a summer/winter capability (DMNC/CRIS) basis, not "
                     "nameplate, so it is a cross-check, not the anchor.",
            "total_mw": adiag["anchor_total_mw"],
            "by_fuel_mw": adiag["anchor_by_fuel_mw"],
            "capacity_definition": "Nameplate MW, all statuses (OP/SB/OA/OS).",
            "cross_checks": {
                "gold_book_2026_existing_net_summer_capability_mw": 37420,
                "gold_book_2026_total_resource_capability_summer_mw": 40866,
                "gold_book_2026_nyca_generating_capability_mw": 36428,
                "gold_book_2026_renewables_summer_capability_mw": {
                    "conventional_hydro": 4211, "land_based_wind": 2578,
                    "offshore_wind": 132, "grid_connected_solar": 571,
                    "other_renewables": 324, "total": 7816},
                "gold_book_note": "NYISO 2026 Load & Capacity Data Report "
                    "(Gold Book, released April 2026): existing net summer "
                    "capability 37,420 MW; Total Resource Capability for "
                    "summer 2026 40,866 MW including imports, SCR and other "
                    "non-generation resources. Gold Book capability (DMNC) "
                    "is tested output, not nameplate: e.g. grid solar counts "
                    "571 MW of summer capability against ~3.0 GW of EIA "
                    "nameplate (most small/community solar is a load "
                    "modifier, not a market generator), and thermal units "
                    "are derated to demonstrated capability. EIA nameplate "
                    "also includes out-of-service/standby units and "
                    "1,622.4 MW of NJ-sited plant under BA NYIS that "
                    "delivers into New York City (Linden Cogen 974.1 MW, "
                    "Bayonne Energy Center 644.0 MW, two small solar units). The "
                    "~8.2 GW gap between the EIA nameplate anchor and Gold "
                    "Book summer capability is definitional, not an error "
                    "in either source. Do not mix the two bases.",
                "eia_operating_sep2026_nameplate_mw": adiag["eia_operating_nyis_nameplate_mw"],
                "eia_operating_sep2026_netsummer_mw": adiag["eia_operating_nyis_netsummer_mw"],
            },
        },
        "trailing": {
            "basis": "Reconstructed Dec-31 snapshots from EIA unit-level data "
                     "(Operating Year / Retirement Year). Estimated; not a NYISO publication.",
            "yearly_totals_mw": {str(int(y)): round(float(v), 1)
                                 for y, v in tot.items() if y <= 2025},
            "indian_point_check": "Nuclear trailing falls 1,299.0 MW in 2020 "
                                  "(Indian Point 2, retired Apr 2020) and "
                                  "1,012.0 MW in 2021 (Indian Point 3, retired "
                                  "Apr 2021), asserted in the build.",
        },
        "forward_2026_2036": {
            "additions_mw": round(float(changelog["additions_mw"].sum()), 1),
            "additions_count": int(changelog["additions_count"].sum()),
            "retirements_mw": round(float(changelog["retirements_mw"].sum()), 1),
            "retirements_count": int(changelog["retirements_count"].sum()),
            "net_mw": round(float(changelog["net_mw"].sum()), 1),
            "additions_by_fuel_mw": fwd_add,
            "retirements_by_fuel_mw": fwd_ret,
        },
        "yearly_totals_mw": {str(int(k)): round(float(v), 1)
                             for k, v in tot.items()},
        "diagnostics": {**adiag, **cdiag},
        "files": {
            "plants": "nyiso_capacity_plants.csv",
            "stack": "nyiso_capacity_stack.csv",
            "changelog": "nyiso_capacity_changelog.csv",
            "summary": "summary.json",
            "charts": ["01_stacked_area.png", "02_net_change_forward.png"],
        },
    }
    with open(BASE / "summary.json", "w") as f:
        json.dump(summary, f, indent=2)
    print("  wrote plants/stack/changelog CSVs + summary.json")

    make_charts(stack_wide, changelog)
    print("  yearly totals (NYISO):")
    for y in range(2025, 2037):
        print(f"    {y}: {tot[y]:,.1f} MW")
    return summary


if __name__ == "__main__":
    main()
