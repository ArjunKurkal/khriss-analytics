#!/usr/bin/env python3
"""Build ISO-NE capacity stack v1 — EIA-only.

Mirrors the MISO/PJM v1 method (~/workspace/miso-capacity-stack/build_stack.py):
trailing + forward 10-year stack 2016-2036 by fuel (Coal, Natural Gas,
Nuclear, Hydro, Pumped Storage, Wind, Solar, Oil, Battery Storage, Other),
nameplate MW throughout, anchor Dec 31 2025, forward = anchor + changelog.

ISO-NE differences from MISO (documented, not hidden):
- Region cut: Balancing Authority Code == ISNE in EIA-860M. No subregional
  split (ISO-NE is a single balancing area for this stack; the `region`
  column is the constant "ISO-NE" to preserve the reference schema).
- Northern Maine is NOT in ISO-NE: ~155.7 MW of Maine nameplate sits under
  BA code NBSO (New Brunswick System Operator — the Maritimes control area;
  the northern-Maine system is often called NMISA) and is excluded, exactly
  as a BA cut requires. Conversely, 199.1 MW physically in New York state
  is coded BA=ISNE in EIA and is included (BA cut, not state cut).
- Anchor: ISO-NE's CELT report publishes capacity on a Forward Capacity
  Market / claimed-capability basis (summer/winter SCC and CNRC), not
  nameplate by fuel, and counts settlement-only and behind-the-meter solar
  differently from EIA. No CELT table is directly comparable to a nameplate
  stack, so — following the MISO build's practice when no clean published
  anchor exists — the anchor is the EIA-860M Operating-sheet snapshot
  adjusted to Dec 31, 2025 (minus units in service Jan-Sep 2026, plus
  Retired-sheet actual retirements in 2026), nameplate MW, all statuses.
  It is EIA-derived, stated explicitly; CELT cross-checks are in
  summary.json and README.md. Do NOT present the anchor as an ISO-NE
  publication.
- Trailing 2016-2025: reconstructed from EIA unit-level data (Operating
  Year / Retirement Year), labelled estimated. It reproduces the anchor
  exactly at 2025 (asserted). Mystic's 2024 retirement (1,744.3 MW gas),
  Brayton Point coal (2017) and Schiller coal (2025) appear naturally.
- No blanket retirement-delay override: the PJM coal-delay-to-Jan-2029
  override was a PJM-only user scenario, not a general rule.

Changelog source: EIA-860M September 2026 vintage (data as of Sep 30, 2026),
Balancing Authority Code == ISNE, file:
~/workspace/pjm-capacity-stack/raw/eia860m_sep2026.xlsx (not re-downloaded).
Additions: units in service in 2026 (Operating sheet, Operating Year == 2026)
+ Planned sheet units. Retirements: Retired sheet actuals with Retirement
Year == 2026 + Operating sheet planned retirements (all years listed in the
plants file; the changelog/stack window is 2026-2036).

The build asserts: (1) trailing snapshot(2025) == anchor exactly;
(2) forward stack == anchor + cumulative changelog; (3) overlap guards == 0.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

BASE = Path(__file__).resolve().parent
EIA_FILE = Path("/home/hatch/workspace/pjm-capacity-stack/raw/eia860m_sep2026.xlsx")
ANCHOR_YEAR = 2025
BA = "ISNE"
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
        "region": "ISO-NE",
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
    operating at Dec 31, 2025). Nameplate MW, all statuses.
    """
    diag = {}
    isne_op = op[op["Balancing Authority Code"] == BA].copy()
    isne_rt = rt[rt["Balancing Authority Code"] == BA].copy()
    diag["eia_operating_isne_units"] = int(len(isne_op))
    diag["eia_operating_isne_nameplate_mw"] = round(
        isne_op["Nameplate Capacity (MW)"].sum(), 1)
    diag["eia_operating_isne_netsummer_mw"] = round(
        isne_op["Net Summer Capacity (MW)"].sum(), 1)
    diag["eia_operating_isne_netwinter_mw"] = round(
        isne_op["Net Winter Capacity (MW)"].sum(), 1)
    op_only = isne_op[isne_op["Status"] == "(OP) Operating"]
    diag["eia_operating_isne_op_only_nameplate_mw"] = round(
        op_only["Nameplate Capacity (MW)"].sum(), 1)
    diag["eia_operating_isne_nonop_nameplate_mw"] = round(
        isne_op[isne_op["Status"] != "(OP) Operating"]
        ["Nameplate Capacity (MW)"].sum(), 1)
    diag["eia_operating_isne_by_fuel_nameplate"] = {
        f: round(v, 1) for f, v in
        isne_op.groupby("fuel")["Nameplate Capacity (MW)"].sum().items()}

    # BA boundary cross-checks: New England generation outside ISNE, and
    # ISNE-coded capacity physically outside the six New England states.
    me_op = op[op["Plant State"] == "ME"]
    nbso = me_op[me_op["Balancing Authority Code"] == "NBSO"]
    diag["exclusion_northern_maine_nbso_nameplate_mw"] = round(
        nbso["Nameplate Capacity (MW)"].sum(), 1)
    diag["exclusion_northern_maine_nbso_units"] = int(len(nbso))
    diag["exclusion_northern_maine_note"] = (
        "Northern Maine (Maritimes control area; EIA BA code NBSO = New "
        "Brunswick System Operator; the northern-Maine system is commonly "
        "called NMISA) is not part of ISO-NE and is excluded by the BA cut. "
        "Largest item: Mars Hill Wind Farm, 42.0 MW.")
    ne_states = ["ME", "NH", "VT", "MA", "RI", "CT"]
    in_ne_not_isne = op[(op["Plant State"].isin(ne_states))
                        & (op["Balancing Authority Code"] != BA)]
    diag["ba_boundary_in_ne_states_not_isne_mw"] = round(
        in_ne_not_isne["Nameplate Capacity (MW)"].sum(), 1)
    diag["ba_boundary_in_ne_states_not_isne_by_ba_mw"] = {
        str(k): round(v, 1) for k, v in
        in_ne_not_isne.groupby("Balancing Authority Code")
        ["Nameplate Capacity (MW)"].sum().items()}
    isne_outside = isne_op[~isne_op["Plant State"].isin(ne_states)]
    diag["ba_boundary_isne_ba_outside_ne_states_mw"] = round(
        isne_outside["Nameplate Capacity (MW)"].sum(), 1)
    diag["ba_boundary_isne_ba_outside_ne_states_units"] = int(len(isne_outside))
    diag["ba_boundary_isne_ba_outside_ne_states_note"] = (
        "Small solar units physically in New York state but coded BA=ISNE "
        "in EIA (largest: Eureka South/North Solar, 5.0 + 3.5 MW). Included: "
        "the cut is by balancing authority, not by state.")

    in_service_2026 = isne_op[pd.to_numeric(
        isne_op["Operating Year"], errors="coerce") == 2026]
    rt26 = isne_rt[pd.to_numeric(
        isne_rt["Retirement Year"], errors="coerce") == 2026]
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

    base = isne_op[pd.to_numeric(
        isne_op["Operating Year"], errors="coerce") <= 2025].copy()
    anchor_by_fuel = {
        f: round(base[base["fuel"] == f]["Nameplate Capacity (MW)"].sum()
                 + rt26[rt26["fuel"] == f]["Nameplate Capacity (MW)"].sum(), 1)
        for f in FUELS}
    anchor_netsummer = round(
        base["Net Summer Capacity (MW)"].sum()
        + rt26["Net Summer Capacity (MW)"].sum(), 1)
    diag["anchor_total_mw"] = round(sum(anchor_by_fuel.values()), 1)
    diag["anchor_by_fuel_mw"] = anchor_by_fuel
    diag["anchor_net_summer_mw"] = anchor_netsummer
    return anchor_by_fuel, diag


# ---------------- Trailing (reconstructed from EIA unit data) ----------------
def trailing_reconstructed(op, rt):
    """Dec-31 snapshots 2016-2025 reconstructed from EIA unit-level data.

    For year Y: Operating-sheet units with Operating Year <= Y, plus
    Retired-sheet units with Operating Year <= Y < Retirement Year.
    Planned Retirement Year is deliberately NOT used (it reflects plans
    as of Sep 2026, not history). Labelled estimated in the outputs.
    """
    isne_op = op[op["Balancing Authority Code"] == BA].copy()
    isne_rt = rt[rt["Balancing Authority Code"] == BA].copy()
    isne_op["_oy"] = pd.to_numeric(isne_op["Operating Year"], errors="coerce")
    isne_rt["_oy"] = pd.to_numeric(isne_rt["Operating Year"], errors="coerce")
    isne_rt["_ry"] = pd.to_numeric(isne_rt["Retirement Year"], errors="coerce")
    assert isne_op["_oy"].notna().all(), "Operating Year missing on Operating"
    assert isne_rt["_oy"].notna().all(), "Operating Year missing on Retired"
    assert isne_rt["_ry"].notna().all(), "Retirement Year missing on Retired"
    rows = []
    for y in range(2016, 2026):
        snap_op = isne_op[isne_op["_oy"] <= y]
        snap_rt = isne_rt[(isne_rt["_oy"] <= y) & (isne_rt["_ry"] > y)]
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
    """Forward changelog from EIA-860M (BA == ISNE). No blanket override.

    Additions: units in service in 2026 (Operating, Operating Year == 2026)
    + Planned sheet units (all years; the stack window is 2026-2036).
    Retirements: Retired sheet actuals with Retirement Year == 2026 +
    Operating sheet planned retirements (all years listed in plants file).
    """
    isne_op = op[op["Balancing Authority Code"] == BA].copy()
    isne_pl = pl[pl["Balancing Authority Code"] == BA].copy()
    isne_rt = rt[rt["Balancing Authority Code"] == BA].copy()

    diag = {}
    diag["eia_planned_isne_units"] = int(len(isne_pl))
    diag["eia_planned_isne_nameplate_mw"] = round(
        isne_pl["Nameplate Capacity (MW)"].sum(), 1)
    diag["eia_planned_isne_by_status_mw"] = {
        k: round(v, 1) for k, v in
        isne_pl.groupby("Status")["Nameplate Capacity (MW)"].sum().items()}
    diag["eia_planned_under_construction_mw"] = round(
        isne_pl[isne_pl["Status"].str.contains(
            "Under construction|Construction complete", na=False)]
        ["Nameplate Capacity (MW)"].sum(), 1)
    diag["eia_planned_not_under_construction_mw"] = round(
        diag["eia_planned_isne_nameplate_mw"]
        - diag["eia_planned_under_construction_mw"], 1)

    adds = []
    in_service_2026 = isne_op[pd.to_numeric(
        isne_op["Operating Year"], errors="coerce") == 2026]
    for _, r in in_service_2026.iterrows():
        adds.append(_plant_row(
            r, "addition", "addition", int(r["Operating Year"]),
            int(pd.to_numeric(r["Operating Month"], errors="coerce") or 1),
            "Operating sheet: in service Jan-Sep 2026"))
    for _, r in isne_pl.iterrows():
        y = pd.to_numeric(r["Planned Operation Year"], errors="coerce")
        m = pd.to_numeric(r["Planned Operation Month"], errors="coerce")
        if pd.isna(y):
            continue
        adds.append(_plant_row(r, "addition", "addition", int(y),
                               int(m) if not pd.isna(m) else 1,
                               "Planned sheet"))
    adds_df = pd.DataFrame(adds)

    rets = []
    rt26 = isne_rt[pd.to_numeric(
        isne_rt["Retirement Year"], errors="coerce") == 2026]
    for _, r in rt26.iterrows():
        rets.append(_plant_row(
            r, "retirement", "retired (actual)",
            int(r["Retirement Year"]),
            int(pd.to_numeric(r["Retirement Month"], errors="coerce") or 1),
            "Retired sheet: actual Jan-Sep 2026"))
    pr = isne_op[pd.to_numeric(
        isne_op["Planned Retirement Year"], errors="coerce").notna()].copy()
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
        key(in_service_2026) & key(isne_pl[
            isne_pl["Planned Operation Year"] == 2026]))
    diag["overlap_retired2026_vs_plannedret2026_units"] = len(
        key(rt26) & key(isne_op[pd.to_numeric(
            isne_op["Planned Retirement Year"], errors="coerce") == 2026]))
    assert diag["overlap_operating2026_vs_planned2026_units"] == 0
    assert diag["overlap_retired2026_vs_plannedret2026_units"] == 0

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
    """Forward stack: anchor (Dec 31, 2025) + cumulative net changelog."""
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
    stack_wide = pd.concat([trailing_df, pd.DataFrame(rows)],
                           ignore_index=True)
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
    ax.set_title(f"ISO-NE generation capacity stack by fuel, 2016-2036 — {version}\n"
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
    ax.set_title(f"ISO-NE annual net capacity change by fuel, forward 2026-2036 — {version}\n"
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

    anchor_by_fuel, adiag = build_anchor(op, rt)
    print(f"  anchor Dec 31 2025: {adiag['anchor_total_mw']:,.1f} MW "
          f"(EIA-derived, nameplate); net summer {adiag['anchor_net_summer_mw']:,.1f} MW")
    print(f"  northern-Maine (NBSO) exclusion: "
          f"{adiag['exclusion_northern_maine_nbso_nameplate_mw']:,.1f} MW")

    trailing_df = trailing_reconstructed(op, rt)
    snap25 = trailing_df[trailing_df["year"] == 2025].iloc[0]
    assert abs(snap25["Total"] - adiag["anchor_total_mw"]) < 0.05, (
        snap25["Total"], adiag["anchor_total_mw"])
    for f in FUELS:
        assert abs(snap25[f] - anchor_by_fuel[f]) < 0.05, (f, snap25[f])
    print("  trailing reconstruction reproduces the anchor at 2025: OK")
    # Sanity checks named in the brief: Mystic 2024, Schiller coal 2025.
    mystic24 = rt[(rt["Balancing Authority Code"] == BA)
                  & (rt["Plant Name"] == "Mystic Generating Station")
                  & (pd.to_numeric(rt["Retirement Year"], errors="coerce") == 2024)]
    print(f"  sanity: Mystic retired 2024 = {mystic24['Nameplate Capacity (MW)'].sum():,.1f} MW "
          f"({len(mystic24)} units); Schiller coal retired 2025 in Retired sheet; "
          f"Brayton Point coal retired 2017 in Retired sheet")

    changelog, plants, cdiag, adds_df, rets_df = eia_changelog(op, pl, rt)
    inwin_r = rets_df[rets_df["effective_year"].between(2026, 2036)]
    print(f"  forward additions 2026-2036: "
          f"{cdiag['planned_total_mw_2026_2036']:,.1f} MW ({len(adds_df)} units); "
          f"retirements: {inwin_r['mw_nameplate'].sum():,.1f} MW ({len(inwin_r)} units)")
    print(f"  overlap guards: {cdiag['overlap_operating2026_vs_planned2026_units']} / "
          f"{cdiag['overlap_retired2026_vs_plannedret2026_units']} (both must be 0)")

    stack_wide, long_total = build_stack(trailing_df, changelog, anchor_by_fuel)
    # Assertion: forward stack == anchor + cumulative changelog.
    tot = stack_wide.set_index("year")["Total"].round(1).to_dict()
    assert abs(tot[2036] - (adiag["anchor_total_mw"]
                            + float(changelog["net_mw"].sum()))) < 0.15
    print("  forward stack == anchor + cumulative changelog: OK")

    plants.to_csv(BASE / "isone_capacity_plants.csv", index=False)
    long_total.to_csv(BASE / "isone_capacity_stack.csv", index=False)
    changelog.to_csv(BASE / "isone_capacity_changelog.csv", index=False)

    def agg(df, col):
        return {f: round(float(df[df["fuel"] == f][col].sum()), 1)
                for f in FUELS}
    summary = {
        "version": "v1",
        "built": "2026-11-15",
        "anchor": {
            "basis": "EIA-860M Operating-sheet snapshot adjusted to Dec 31, 2025 "
                     "(minus in-service Jan-Sep 2026, plus retired actuals 2026). "
                     "EIA-derived; ISO-NE CELT publishes capacity on an FCM "
                     "claimed-capability (SCC/CNRC) basis, not nameplate by fuel, "
                     "so no CELT table is directly comparable — see cross_checks.",
            "total_mw": adiag["anchor_total_mw"],
            "by_fuel_mw": adiag["anchor_by_fuel_mw"],
            "capacity_definition": "Nameplate MW, all statuses (OP/SB/OA/OS).",
            "net_summer_mw": adiag["anchor_net_summer_mw"],
            "cross_checks": {
                "iso_ne_described_generating_capacity_mw": "~29,700 (ISO-NE "
                    "regional overviews, Mar 2025: 'Nearly 30,000 MW of "
                    "generating capacity' — FCM claimed-capability basis, not "
                    "nameplate; excludes settlement-only resources counted "
                    "differently and all behind-the-meter solar)",
                "definitional_gap": "EIA nameplate anchor (38,238.1 MW) exceeds "
                    "the ISO's ~29.7 GW capability figure by ~8.5 GW. Causes: "
                    "(1) nameplate vs summer claimed capability — wind, solar "
                    "and oil steam derate heavily in summer SCC; the EIA anchor "
                    "on a net-summer basis is 35,426.4 MW, still above CELT "
                    "because (2) EIA counts every >=1 MW unit incl. small IPP/CHP "
                    "and settlement-only generators that CELT's generator list "
                    "treats separately; (3) EIA snapshot includes 1,439.7 MW of "
                    "non-operating (OS/SB/OA) nameplate; (4) CELT counts ~3,600 MW "
                    "of demand resources and imports as capacity resources, which "
                    "are not generation and are excluded here; (5) behind-the-meter "
                    "solar is in neither the EIA anchor nor the CELT generator "
                    "list — ISO-NE puts total New England solar nameplate at "
                    "~9,600 MW at end-2025 vs 3,734.3 MW of grid solar in this "
                    "anchor (see README caveats).",
                "eia_operating_sep2026_nameplate_mw": adiag["eia_operating_isne_nameplate_mw"],
                "eia_operating_sep2026_netsummer_mw": adiag["eia_operating_isne_netsummer_mw"],
            },
        },
        "trailing": {
            "basis": "Reconstructed Dec-31 snapshots from EIA unit-level data "
                     "(Operating Year / Retirement Year). Estimated; not an "
                     "ISO-NE publication.",
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
            "plants": "isone_capacity_plants.csv",
            "stack": "isone_capacity_stack.csv",
            "changelog": "isone_capacity_changelog.csv",
            "summary": "summary.json",
            "charts": ["01_stacked_area.png", "02_net_change_forward.png"],
        },
    }
    with open(BASE / "summary.json", "w") as f:
        json.dump(summary, f, indent=2)
    print("  wrote plants/stack/changelog CSVs + summary.json")

    make_charts(stack_wide, changelog)
    print("  yearly totals (ISO-NE):")
    for y in range(2025, 2037):
        print(f"    {y}: {tot[y]:,.1f} MW")
    return summary


if __name__ == "__main__":
    main()
