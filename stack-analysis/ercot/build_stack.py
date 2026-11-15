#!/usr/bin/env python3
"""Build ERCOT capacity stack v1 — EIA-only.

Mirrors the MISO v1 method (~/workspace/miso-capacity-stack/build_stack.py),
which mirrors PJM: trailing + forward 10-year stack 2016-2036 by fuel
(Coal, Natural Gas, Nuclear, Hydro, Pumped Storage, Wind, Solar, Oil,
Battery Storage, Other), nameplate MW throughout, anchor Dec 31 2025,
forward = anchor + changelog.

ERCOT differences from MISO (documented, not hidden):
- No regionalization: ERCOT is a single balancing authority / single
  region. Plant rows carry region == "ERCOT" to keep the MISO schema.
- Anchor: ERCOT publishes a Capacity, Demand and Reserves (CDR) report,
  but the CDR uses seasonal capacity ratings (not nameplate) and treats
  switchable units, Private Use Networks and DC-tie capacity specially,
  so it is NOT a nameplate-by-fuel anchor. Per the same discipline as
  MISO, the anchor is therefore the EIA-860M Operating-sheet snapshot,
  adjusted to Dec 31 2025 (minus units in service Jan-Sep 2026, plus
  Retired-sheet actual retirements in 2026 — zero for ERCO), nameplate
  MW, all statuses. It is EIA-derived, stated explicitly; the CDR is a
  cross-check only (see summary.json and README.md).
- Trailing 2016-2025: reconstructed from EIA unit-level data
  (Operating Year / Retirement Year), labelled estimated.
- Region cut: Balancing Authority Code == ERCO. The ERCOT footprint is
  NOT all of Texas (the Panhandle, El Paso and parts of East Texas sit
  in SPP/MISO/SERC/WECC), so a state-based cut would be wrong.
- No blanket retirement-delay override: the PJM coal-delay-to-Jan-2029
  override was a PJM-only user scenario, not a general rule.

Changelog source: EIA-860M September 2026 vintage (data as of Sep 30,
2026), Balancing Authority Code == ERCO, same file the PJM/MISO stacks
used: ~/workspace/pjm-capacity-stack/raw/eia860m_sep2026.xlsx
Additions: units in service in 2026 (Operating sheet, Operating Year
== 2026) + Planned sheet units.
Retirements: Retired sheet actuals with Retirement Year == 2026 +
Operating sheet planned retirements, Planned Retirement Year 2026-2036
(the changelog aggregates 2026-2036; later retirements are listed in
the plants file but outside the window).

The build asserts: (1) trailing reconstruction reproduces the anchor
exactly at 2025; (2) forward stack == anchor + cumulative changelog.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

BASE = Path(__file__).resolve().parent
EIA_FILE = Path("/home/hatch/workspace/pjm-capacity-stack/raw/eia860m_sep2026.xlsx")
ANCHOR_YEAR = 2025
BA = "ERCO"
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
        "region": "ERCOT",
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
    operating at Dec 31, 2025; for ERCO there are none). Nameplate MW,
    all statuses. Returns (anchor_by_fuel, diagnostics).
    """
    diag = {}
    erco_op = op[op["Balancing Authority Code"] == BA].copy()
    erco_rt = rt[rt["Balancing Authority Code"] == BA].copy()
    diag["eia_operating_erco_units"] = int(len(erco_op))
    diag["eia_operating_erco_nameplate_mw"] = round(
        erco_op["Nameplate Capacity (MW)"].sum(), 1)
    diag["eia_operating_erco_netsummer_mw"] = round(
        erco_op["Net Summer Capacity (MW)"].sum(), 1)
    op_only = erco_op[erco_op["Status"] == "(OP) Operating"]
    diag["eia_operating_erco_op_only_nameplate_mw"] = round(
        op_only["Nameplate Capacity (MW)"].sum(), 1)
    diag["eia_operating_erco_op_only_netsummer_mw"] = round(
        op_only["Net Summer Capacity (MW)"].sum(), 1)
    diag["eia_operating_erco_nonop_nameplate_mw"] = round(
        erco_op[erco_op["Status"] != "(OP) Operating"]
        ["Nameplate Capacity (MW)"].sum(), 1)
    diag["eia_operating_erco_by_fuel_nameplate"] = {
        f: round(v, 1) for f, v in
        erco_op.groupby("fuel")["Nameplate Capacity (MW)"].sum().items()}
    diag["eia_operating_erco_by_fuel_netsummer"] = {
        f: round(v, 1) for f, v in
        erco_op.groupby("fuel")["Net Summer Capacity (MW)"].sum().items()}

    # BA boundary cross-check: Texas MW under other BAs (must NOT be in
    # ERCOT), and ERCO MW outside Texas (Kiamichi, OK — verified ERCOT).
    tx = op[op["Plant State"] == "TX"]
    tx_other = tx[tx["Balancing Authority Code"] != BA]
    diag["ba_boundary_tx_not_erco_mw"] = round(
        tx_other["Nameplate Capacity (MW)"].sum(), 1)
    diag["ba_boundary_tx_not_erco_units"] = int(len(tx_other))
    diag["ba_boundary_tx_not_erco_by_ba_mw"] = {
        k: round(v, 1) for k, v in
        tx_other.groupby("Balancing Authority Code")
        ["Nameplate Capacity (MW)"].sum().items()}
    ba_out = erco_op[erco_op["Plant State"] != "TX"]
    diag["ba_boundary_erco_outside_tx_mw"] = round(
        ba_out["Nameplate Capacity (MW)"].sum(), 1)
    diag["ba_boundary_erco_outside_tx_units"] = int(len(ba_out))
    diag["ba_boundary_erco_outside_tx_plants"] = sorted(
        ba_out["Plant Name"].unique().tolist())

    # Adjustment to Dec 31, 2025.
    in_service_2026 = erco_op[pd.to_numeric(
        erco_op["Operating Year"], errors="coerce") == 2026]
    rt26 = erco_rt[pd.to_numeric(
        erco_rt["Retirement Year"], errors="coerce") == 2026]
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

    base = erco_op[pd.to_numeric(
        erco_op["Operating Year"], errors="coerce") <= 2025].copy()
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
    as of Sep 2026, not history. Labelled estimated in the outputs.
    """
    erco_op = op[op["Balancing Authority Code"] == BA].copy()
    erco_rt = rt[rt["Balancing Authority Code"] == BA].copy()
    erco_op["_oy"] = pd.to_numeric(erco_op["Operating Year"], errors="coerce")
    erco_rt["_oy"] = pd.to_numeric(erco_rt["Operating Year"], errors="coerce")
    erco_rt["_ry"] = pd.to_numeric(erco_rt["Retirement Year"], errors="coerce")
    assert erco_op["_oy"].notna().all(), "Operating Year missing on Operating"
    assert erco_rt["_oy"].notna().all(), "Operating Year missing on Retired"
    assert erco_rt["_ry"].notna().all(), "Retirement Year missing on Retired"
    rows = []
    for y in range(2016, 2026):
        snap_op = erco_op[erco_op["_oy"] <= y]
        snap_rt = erco_rt[(erco_rt["_oy"] <= y) & (erco_rt["_ry"] > y)]
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
    """Forward changelog from EIA-860M (BA == ERCO). No blanket override.

    Additions: units in service in 2026 (Operating, Operating Year == 2026)
    + Planned sheet units.
    Retirements: Retired sheet actuals with Retirement Year == 2026 +
    Operating sheet planned retirements.
    Returns (changelog_df, plants_df, diagnostics, adds_df, rets_df).
    """
    erco_op = op[op["Balancing Authority Code"] == BA].copy()
    erco_pl = pl[pl["Balancing Authority Code"] == BA].copy()
    erco_rt = rt[rt["Balancing Authority Code"] == BA].copy()

    diag = {}
    diag["eia_planned_erco_units"] = int(len(erco_pl))
    diag["eia_planned_erco_nameplate_mw"] = round(
        erco_pl["Nameplate Capacity (MW)"].sum(), 1)
    diag["eia_planned_erco_by_status_mw"] = {
        k: round(v, 1) for k, v in
        erco_pl.groupby("Status")["Nameplate Capacity (MW)"].sum().items()}
    diag["eia_planned_under_construction_mw"] = round(
        erco_pl[erco_pl["Status"].str.contains(
            "Under construction|Construction complete", na=False)]
        ["Nameplate Capacity (MW)"].sum(), 1)
    diag["eia_planned_max_operation_year"] = int(pd.to_numeric(
        erco_pl["Planned Operation Year"], errors="coerce").max())

    # ---- Additions ----
    adds = []
    in_service_2026 = erco_op[pd.to_numeric(
        erco_op["Operating Year"], errors="coerce") == 2026]
    for _, r in in_service_2026.iterrows():
        adds.append(_plant_row(
            r, "addition", "addition", int(r["Operating Year"]),
            int(pd.to_numeric(r["Operating Month"], errors="coerce") or 1),
            "Operating sheet: in service Jan-Sep 2026"))
    for _, r in erco_pl.iterrows():
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
    rt26 = erco_rt[pd.to_numeric(
        erco_rt["Retirement Year"], errors="coerce") == 2026]
    for _, r in rt26.iterrows():
        rets.append(_plant_row(
            r, "retirement", "retired (actual)",
            int(r["Retirement Year"]),
            int(pd.to_numeric(r["Retirement Month"], errors="coerce") or 1),
            "Retired sheet: actual Jan-Sep 2026"))
    pr = erco_op[pd.to_numeric(
        erco_op["Planned Retirement Year"], errors="coerce").notna()].copy()
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
        key(in_service_2026) & key(erco_pl[
            erco_pl["Planned Operation Year"] == 2026]))
    diag["overlap_retired2026_vs_plannedret2026_units"] = len(
        key(rt26) & key(erco_op[pd.to_numeric(
            erco_op["Planned Retirement Year"], errors="coerce") == 2026]))

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
    anchor + cumulative changelog by construction and checks the
    trailing 2025 row equals the anchor.
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
    # 1. Stacked area, ERCOT total, 2016-2036, GW.
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
    ax.set_title("ERCOT generation capacity stack by fuel, 2016-2036 — v1\n"
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
    ax.set_title("ERCOT annual net capacity change by fuel, forward 2026-2036 — v1\n"
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

    changelog, plants, cdiag, adds_df, rets_df = eia_changelog(op, pl, rt)
    rets_win = rets_df[rets_df["effective_year"].between(2026, 2036)]
    print(f"  forward additions 2026-2036: "
          f"{cdiag['planned_total_mw_2026_2036']:,.1f} MW "
          f"({len(adds_df)} units); retirements: "
          f"{rets_win['mw_nameplate'].sum():,.1f} MW ({len(rets_win)} units)")
    assert cdiag["overlap_operating2026_vs_planned2026_units"] == 0
    assert cdiag["overlap_retired2026_vs_plannedret2026_units"] == 0
    print("  overlap guards are zero: OK")

    stack_wide, long_total = build_stack(trailing_df, changelog, anchor_by_fuel)
    # Forward identity: 2036 total == anchor + cumulative net changelog.
    assert abs(stack_wide[stack_wide["year"] == 2036]["Total"].iloc[0]
               - (adiag["anchor_total_mw"]
                  + changelog["net_mw"].sum())) < 0.15
    print("  forward stack == anchor + cumulative changelog: OK")

    # ---- Write outputs (v1 files only; v2 never overwrites these) ----
    plants.to_csv(BASE / "ercot_capacity_plants.csv", index=False)
    long_total.to_csv(BASE / "ercot_capacity_stack.csv", index=False)
    changelog.to_csv(BASE / "ercot_capacity_changelog.csv", index=False)

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
                     "(minus in-service Jan-Sep 2026, plus retired actuals 2026; "
                     "ERCO retired actuals in 2026 are zero). EIA-derived. ERCOT's "
                     "CDR is a cross-check only: it uses seasonal capacity ratings, "
                     "not nameplate, and treats switchable units, Private Use "
                     "Networks and DC ties specially.",
            "total_mw": adiag["anchor_total_mw"],
            "by_fuel_mw": adiag["anchor_by_fuel_mw"],
            "capacity_definition": "Nameplate MW, all statuses (OP/SB/OA/OS).",
            "cross_checks": {
                "ercot_cdr_dec2025": "ERCOT CDR Dec 19, 2025 (2026-2030): summer "
                    "2026 installed seasonal-rated thermal capacity excl. "
                    "switchable units 65,431 MW; switchable capacity 3,678 MW "
                    "(2,184 MW unavailable to ERCOT in summer 2026); Private Use "
                    "Network capacity 3,431 MW; expected summer 2026 capacity "
                    "~104,850 MW on the CDR basis (thermal seasonal ratings + "
                    "ELCC contributions for wind/solar/storage + PUN + ties). "
                    "Not comparable to the EIA nameplate anchor: CDR counts "
                    "seasonal ratings and ELCC shares, EIA counts nameplate.",
                "ercot_fact_sheet_oct2026": "ERCOT Fact Sheet Oct 2026 "
                    "(operational installed, summer 2026 CDR basis): wind "
                    "41,208 MW, utility solar 41,926 MW, storage 21,537 MW. "
                    "Solar/storage run well above the EIA Operating snapshot "
                    "because EIA files many just-completed units on the "
                    "Planned sheet (TS status) until commercial operation.",
                "ercot_gis_sep2026": "ERCOT Generator Interconnection Status: "
                    "1,874 active requests totalling 453,782 MW at Sep 30, "
                    "2026 (solar 155,123; battery 162,580; gas ~81,704; wind "
                    "49,746 MW). The queue is a superset of the EIA pipeline; "
                    "most queued projects are never built.",
                "eia_operating_sep2026_nameplate_mw": adiag["eia_operating_erco_nameplate_mw"],
                "eia_operating_sep2026_netsummer_mw": adiag["eia_operating_erco_netsummer_mw"],
            },
        },
        "trailing": {
            "basis": "Reconstructed Dec-31 snapshots from EIA unit-level data "
                     "(Operating Year / Retirement Year). Estimated; not an "
                     "ERCOT publication.",
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
        },
        "yearly_totals_mw": {str(int(k)): round(float(v), 1)
                             for k, v in tot.items()},
        "diagnostics": {**adiag, **cdiag},
        "files": {
            "plants": "ercot_capacity_plants.csv",
            "stack": "ercot_capacity_stack.csv",
            "changelog": "ercot_capacity_changelog.csv",
            "summary": "summary.json",
            "charts": ["01_stacked_area.png", "02_net_change_forward.png"],
        },
    }
    with open(BASE / "summary.json", "w") as f:
        json.dump(summary, f, indent=2)
    print("  wrote plants/stack/changelog CSVs + summary.json")

    make_charts(stack_wide, changelog)
    print("  yearly totals (ERCOT):")
    for y in range(2025, 2037):
        print(f"    {y}: {tot[y]:,.1f} MW")
    return summary


if __name__ == "__main__":
    main()
