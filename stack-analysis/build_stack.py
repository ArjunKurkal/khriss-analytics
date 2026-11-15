#!/usr/bin/env python3
"""
PJM generation capacity stack, trailing + forward 10 years (2016-2036), PJM level only.

METHOD (as specified by the user)
-------------------------------
* Anchor: PJM State of the Market (Monitoring Analytics / Independent Market
  Monitor) published installed / online generation capacity at Dec 31, 2025
  (2025 Annual SOM, Table 12-1): 202,424.8 MW. That anchor is the base.
* Forward capacity = anchor + EIA-860M changelog, year by year:
  additions (EIA-860M Planned sheet + units already in service in 2026 from
  the Operating sheet) minus retirements (EIA-860M Retired sheet actuals for
  2026 + Operating sheet planned retirements). The EIA totals never replace
  the anchor; the reconciliation between the EIA PJM operating total and the
  SOM anchor is reported in summary.json and the README.
* Trailing 2016-2025: Dec-31 installed capacity by fuel from the annual SOM
  Section 12, Table 12-1 (existing capacity by zone and unit type), parsed
  from the published PDFs with pdftotext. 2018-2025 use the detailed
  unit-type layout; 2016-2017 use older, coarser SOM tables and are split
  into fuels with documented proportional estimates (see
  `som_coarse_split_2016_2017` and README). SOM notes that totals include
  corrections to historical data, so year-to-year wobbles of a few hundred MW
  in a fuel (e.g. nuclear 2016-2018, pumped storage 2020-2021) are SOM
  restatements, not physical changes.
* Capacity definition: SOM "installed capacity" = summer installed capacity
  (ICAP) rating, except solar and wind which are nameplate. EIA-860M
  changelog is in NAMEPLATE MW. Applying nameplate changes to an ICAP
  anchor is an approximation, stated explicitly; it is the standard
  practical approach here because EIA does not publish ICAP, and the
  reconciliation table quantifies the definitional gap (EIA PJM operating
  nameplate 229,105.7 MW vs SOM anchor 202,424.8 MW, +13.2%; on a net-summer
  basis 213,531.5 MW, +5.5%).
* PJM filter for EIA data: Balancing Authority Code == 'PJM'. A state-based
  filter would be badly wrong: 153,211 MW of nameplate in PJM footprint
  states sits in other BAs (MISO, TVA, Duke, LG&E, ...), while only 3.3 MW
  of BA=PJM capacity sits outside the footprint states (one 3.3 MW solar
  unit in MN). Full boundary table in summary.json.
* Fuel buckets (consistent trailing + forward): Coal, Natural Gas, Nuclear,
  Hydro (conventional run-of-river), Pumped Storage, Wind, Solar, Oil,
  Battery Storage, Other. SOM unit types map to buckets as in
  SOM_UNIT_TO_FUEL; EIA rows map by Energy Source Code + Prime Mover as in
  eia_fuel(). Storage is MW only; duration (MWh) is not captured.

RMR OVERRIDE (manual, per user instruction; corrected date Jan 2029)
--------------------------------------------------------------------
All PJM coal retirements scheduled in 2026, 2027 or 2028 are pushed to
Jan 2029, to reflect the president's Reliability Must Run announcements.
Implemented literally: every PJM coal unit on the EIA Operating sheet with
a planned retirement year in {2026, 2027, 2028} gets effective retirement
Jan 2029. Original scheduled date is kept in pjm_capacity_plants.csv
(original_retirement_date, effective_retirement_date, rmr_override=TRUE)
and the changelog/stack use the EFFECTIVE dates. Affected: 5 units,
4,569.0 MW - Kincaid 1 & 2 (IL, 659.5 MW each, orig. Dec 2027) and
Cardinal 3 (OH, 650.0 MW) + Rockport 1 & 2 (IN, 1,300.0 MW each),
orig. Dec 2028. No coal unit was scheduled for retirement in 2026, so the
breakout is 2026: 0 MW / 0 units, 2027: 1,319.0 MW / 2 units,
2028: 3,250.0 MW / 3 units. Because the override date (Jan 2029) is after
all of 2028, this is a pure delay: 4,569.0 MW delayed, 0 MW pulled
forward. (An earlier draft of this instruction said Jan 2028; that was
corrected to Jan 2029 by the user, which removes the pull-forward
consequence a Jan 2028 date would have had for Dec-2028 retirements.)
Already-retired coal units (Retired sheet) are NOT overridden - they
already happened. Note the override is a scenario, not a forecast: RMR
designations are unit-specific and political; treat Jan 2029 as a
placeholder, not a commitment.

SOURCES
--------
* EIA-860M, September 2026 vintage (data as of Sep 30, 2026; released
  Oct 23, 2026; the next release was scheduled Nov 24, 2026, i.e. after
  this build date of Nov 14, 2026):
  https://www.eia.gov/electricity/data/eia860m/
  file: https://www.eia.gov/electricity/data/eia860m/xls/september_generator2026.xlsx
  Sheets: Operating (28,486 rows), Planned (2,360), Retired (7,323).
* PJM State of the Market, Monitoring Analytics (Independent Market Monitor):
  https://www.monitoringanalytics.com/reports/pjm-state-of-the-market
  Annual SOM Section 12 PDFs, 2016-2025:
  https://www.monitoringanalytics.com/reports/pjm_state_of_the_market/{YYYY}/{YYYY}-som-pjm-sec12.pdf
  (2025 annual, created Mar 12, 2026). Cross-check: 2026 Q2 SOM Sec 12,
  https://www.monitoringanalytics.com/reports/PJM_State_of_the_Market/2026/2026q2-som-pjm-sec12.pdf
  (Jun 30, 2026 total 202,384.2 MW).

OUTPUTS (all in this script's directory)
---------------------------------------
* pjm_capacity_stack.csv     - one row per year 2016-2036 x fuel (+ Total), MW
* pjm_capacity_changelog.csv - additions/retirements/net by year x fuel, MW + counts
* pjm_capacity_plants.csv    - unit-level forward changelog (additions + retirements)
* summary.json               - anchor, yearly totals, pipeline, largest units, RMR, reconciliation
* 01_stacked_area.png        - stacked area 2016-2036 by fuel (GW), marker at Nov 2026
* 02_net_change_forward.png  - annual net change by fuel, forward 2026-2036
* 03_add_vs_retire_fuel.png  - cumulative forward additions vs retirements by fuel
* README.md                  - methodology, sources, anchor, mappings, limitations

LIMITATIONS (see README for full list)
--------------------------------------
Planned != built and dates slip (only 8,913 of 26,921 planned MW are under
construction / complete; 11,197 MW have not even begun regulatory
approvals). EIA-860M planned list != PJM interconnection queue (queue
active/under construction/suspended was 41,529 MW at Dec 31, 2025, and
all-cycle active/under construction 45,440 MW at Dec 31, 2025). The
EIA-860M planned horizon effectively ends in 2031 - no additions are
listed for 2032-2036, which is a coverage artifact, not a forecast of
zero builds. Nameplate vs ICAP (see above). Storage MW ignores duration.
No load, energy, or capacity-factor analysis.

Run: python3 build_stack.py  (needs pdftotext on PATH, or pre-downloaded
PDFs/xlsx in ./raw/; downloads are attempted first and existing files reused)
"""

import json
import re
import subprocess
import sys
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd

BASE = Path(__file__).resolve().parent
RAW = BASE / "raw"
RAW.mkdir(exist_ok=True)

EIA_URL = ("https://www.eia.gov/electricity/data/eia860m/xls/"
           "september_generator2026.xlsx")
EIA_FILE = RAW / "eia860m_sep2026.xlsx"
EIA_PAGE = "https://www.eia.gov/electricity/data/eia860m/"
EIA_VINTAGE = "September 2026 (data as of Sep 30, 2026; released Oct 23, 2026)"

SOM_URL_TEMPLATE = ("https://www.monitoringanalytics.com/reports/"
                    "pjm_state_of_the_market/{y}/{y}-som-pjm-sec12.pdf")
SOM_Q2_2026_URL = ("https://www.monitoringanalytics.com/reports/"
                   "PJM_State_of_the_Market/2026/2026q2-som-pjm-sec12.pdf")
SOM_PAGE = "https://www.monitoringanalytics.com/reports/pjm-state-of-the-market"

FUELS = ["Coal", "Natural Gas", "Nuclear", "Hydro", "Pumped Storage",
         "Wind", "Solar", "Oil", "Battery Storage", "Other"]

# SOM Table 12-1 unit-type column order, as printed in the PDFs.
SOM_COLS_DETAILED = ["Battery", "Combined Cycle", "CT - Natural Gas",
                     "CT - Oil", "CT - Other", "Fuel Cell",
                     "Hydro - Pumped Storage", "Hydro - Run of River",
                     "Nuclear", "RICE - Natural Gas", "RICE - Oil",
                     "RICE - Other", "Solar", "Solar + Storage",
                     "Solar + Wind", "Steam - Coal", "Steam - Natural Gas",
                     "Steam - Oil", "Steam - Other", "Wind",
                     "Wind + Storage"]
SOM_COLS_2018_19 = [c for c in SOM_COLS_DETAILED
                    if c not in ("Solar + Storage", "Solar + Wind",
                                 "Wind + Storage")]
SOM_COLS_2017 = ["Combined Cycle", "CT", "Coal", "Diesel", "Fuel Cell",
                 "Hydro", "Nuclear", "Solar", "Storage", "Wind", "Other"]
SOM_COLS_2016 = ["Combined Cycle", "CT", "Diesel", "Fuel Cell",
                 "Hydroelectric", "Nuclear", "Solar", "Steam", "Storage",
                 "Wind"]
SOM_COLS_BY_YEAR = {y: SOM_COLS_DETAILED for y in range(2020, 2026)}
SOM_COLS_BY_YEAR.update({2018: SOM_COLS_2018_19, 2019: SOM_COLS_2018_19,
                         2017: SOM_COLS_2017, 2016: SOM_COLS_2016})
# Table number / heading search per year (2016-17 tables are numbered differently)
SOM_TABLE_SEARCH = {2016: "Table 12-10 Existing PJM capacity",
                    2017: "Table 12-11 Existing PJM capacity"}
SOM_TABLE_SEARCH.update({y: "Table 12-1 Existing" for y in range(2018, 2026)})

# SOM detailed unit type -> fuel bucket. 2018 special case (CT-Other is oil
# CTs, reclassified to CT-Oil in 2019) is handled in som_buckets().
SOM_UNIT_TO_FUEL = {
    "Steam - Coal": "Coal",
    "Combined Cycle": "Natural Gas",
    "CT - Natural Gas": "Natural Gas",
    "RICE - Natural Gas": "Natural Gas",
    "Steam - Natural Gas": "Natural Gas",
    "Nuclear": "Nuclear",
    "Hydro - Run of River": "Hydro",
    "Hydro - Pumped Storage": "Pumped Storage",
    "Wind": "Wind",
    "Wind + Storage": "Wind",
    "Solar": "Solar",
    "Solar + Storage": "Solar",
    "Solar + Wind": "Solar",
    "CT - Oil": "Oil",
    "RICE - Oil": "Oil",
    "Steam - Oil": "Oil",
    "Battery": "Battery Storage",
    "CT - Other": "Other",
    "Fuel Cell": "Other",
    "RICE - Other": "Other",
    "Steam - Other": "Other",
}

# RMR override (corrected date): Jan 2029.
RMR_TARGET_YEAR = 2029
RMR_TARGET_MONTH = 1
RMR_YEARS = (2026, 2027, 2028)
ANCHOR_YEAR = 2025
TODAY_LABEL = "Nov 2026"


def download(url, dest):
    dest = Path(dest)
    if dest.exists() and dest.stat().st_size > 100_000:
        print(f"  reuse {dest.name} ({dest.stat().st_size/1e6:.1f} MB)")
        return dest
    print(f"  download {url}")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=120) as r, open(dest, "wb") as f:
        f.write(r.read())
    print(f"  saved {dest.name} ({dest.stat().st_size/1e6:.1f} MB)")
    return dest


def pdftotext(pdf_path, txt_path):
    txt_path = Path(txt_path)
    if txt_path.exists() and txt_path.stat().st_size > 10_000:
        return txt_path
    subprocess.run(["pdftotext", "-layout", str(pdf_path), str(txt_path)],
                   check=True)
    return txt_path


def parse_som_total_row(year):
    """Parse the SOM Section 12 Table 12-1 (or 12-10/12-11) Total row.

    Returns (dict unit_type -> MW, total MW from the table, total MW from
    the report prose). Raises if the table total and prose total disagree.
    """
    pdf = RAW / f"som{year}_sec12.pdf"
    download(SOM_URL_TEMPLATE.format(y=year), pdf)
    txt = pdftotext(pdf, RAW / f"som{year}_sec12.txt")
    lines = txt.read_text(errors="replace").splitlines()
    # Find the existing-capacity table heading (zone table, first match).
    hidx = None
    for i, ln in enumerate(lines):
        if SOM_TABLE_SEARCH[year] in ln:
            hidx = i
            break
    if hidx is None:
        raise RuntimeError(f"SOM {year}: capacity table heading not found")
    # First Total row after the heading.
    vals = None
    for ln in lines[hidx + 1:hidx + 60]:
        s = ln.strip()
        if s.startswith("Total"):
            nums = [float(x.replace(",", ""))
                    for x in re.findall(r"[\d,]+\.\d", s)]
            if len(nums) >= 10:
                vals = nums
                break
    if vals is None:
        raise RuntimeError(f"SOM {year}: Total row not found")
    cols = SOM_COLS_BY_YEAR[year]
    if len(vals) != len(cols) + 1:
        raise RuntimeError(
            f"SOM {year}: Total row has {len(vals)} numbers, expected "
            f"{len(cols) + 1} (cols {cols})")
    total_table = vals[-1]
    unit = dict(zip(cols, vals[:-1]))
    # Prose total as a cross-check. The PDFs are two-column, so pdftotext
    # interleaves the columns; allow intervening text between "PJM" and
    # "had an installed capacity of".
    raw = txt.read_text(errors="replace")
    m = re.search(
        rf"As of December 31,\s+{year},\s+PJM.{{0,150}}?had\s+an\s+installed\s+"
        r"capacity\s+of\s+([\d,]+\.\d)\s+MW", raw, re.DOTALL)
    if not m:
        raise RuntimeError(f"SOM {year}: prose installed-capacity total not found")
    total_prose = float(m.group(1).replace(",", ""))
    if abs(total_table - total_prose) > 0.5:
        raise RuntimeError(
            f"SOM {year}: table total {total_table} != prose total {total_prose}")
    return unit, total_table, total_prose


def som_buckets(year, unit):
    """Map a parsed SOM Table 12-1 Total row to the 10 fuel buckets (MW)."""
    b = {f: 0.0 for f in FUELS}
    for ut, mw in unit.items():
        if year == 2018 and ut == "CT - Other":
            # 2018 SOM put oil-fired CTs in "CT - Other" (3,997.6 MW);
            # in 2019 the same ~3,902 MW appears as "CT - Oil" and
            # CT-Other falls to 49.8 MW. Treat 2018 CT-Other as Oil.
            b["Oil"] += mw
            continue
        b[SOM_UNIT_TO_FUEL[ut]] += mw
    return b


def som_trailing():
    """Trailing Dec-31 installed capacity by fuel, 2016-2025, from SOM.

    2018-2025: detailed Table 12-1 layout, mapped directly.
    2017: coarse Table 12-11 (CC / CT / Coal / Diesel / Fuel Cell / Hydro /
      Nuclear / Solar / Storage / Wind / Other). CT is split gas/oil, Hydro
      pumped/run-of-river, and Other (steam gas/oil/other + RICE) are split
      using the 2018 detailed proportions, computed from the parsed 2018 row.
    2016: coarse Table 12-10 (CC / CT / Diesel / Fuel Cell / Hydroelectric /
      Nuclear / Solar / Steam / Storage / Wind). Steam is split coal/gas/oil/
      other using the 2017 derived steam shares; CT and Hydroelectric use
      the 2018 proportions. Both coarse years are flagged estimated.
    Returns (DataFrame year x fuel, dict of notes by year).
    """
    parsed = {}
    table_totals = {}
    for y in range(2018, 2026):
        unit, tot, _ = parse_som_total_row(y)
        parsed[y] = unit
        table_totals[y] = tot
        print(f"  SOM {y}: Table 12-1 total {tot:,.1f} MW parsed")
    buckets = {y: som_buckets(y, parsed[y]) for y in range(2018, 2026)}

    # 2018 proportions used for the coarse-year splits.
    u18 = parsed[2018]
    ct_gas_share = u18["CT - Natural Gas"] / (
        u18["CT - Natural Gas"] + u18["CT - Other"])  # CT-Other is oil in 2018
    hydro_pumped_share = u18["Hydro - Pumped Storage"] / (
        u18["Hydro - Pumped Storage"] + u18["Hydro - Run of River"])
    other18 = (u18["Steam - Natural Gas"] + u18["Steam - Oil"]
               + u18["Steam - Other"] + u18["RICE - Natural Gas"]
               + u18["RICE - Oil"] + u18["RICE - Other"])
    other_shares = {
        "Natural Gas": u18["Steam - Natural Gas"] / other18,
        "Oil": (u18["Steam - Oil"] + u18["RICE - Oil"]) / other18,
        "Other": (u18["Steam - Other"] + u18["RICE - Other"]
                  + u18["RICE - Natural Gas"]) / other18,
    }

    notes = {}
    # ---- 2017 (coarse) ----
    unit17, tot17, _ = parse_som_total_row(2017)
    table_totals[2017] = tot17
    b17 = {f: 0.0 for f in FUELS}
    b17["Natural Gas"] += unit17["Combined Cycle"]
    b17["Natural Gas"] += unit17["CT"] * ct_gas_share
    b17["Oil"] += unit17["CT"] * (1 - ct_gas_share)
    b17["Coal"] += unit17["Coal"]
    b17["Oil"] += unit17["Diesel"]
    b17["Other"] += unit17["Fuel Cell"]
    b17["Pumped Storage"] += unit17["Hydro"] * hydro_pumped_share
    b17["Hydro"] += unit17["Hydro"] * (1 - hydro_pumped_share)
    b17["Nuclear"] += unit17["Nuclear"]
    b17["Solar"] += unit17["Solar"]
    b17["Battery Storage"] += unit17["Storage"]
    b17["Wind"] += unit17["Wind"]
    for f, s in other_shares.items():
        b17[f] += unit17["Other"] * s
    buckets[2017] = b17
    notes[2017] = ("SOM 2017 Table 12-11 coarse columns; CT split gas/oil, "
                   "Hydro split pumped/run, Other split steam-gas/oil/other "
                   "+RICE using 2018 detailed proportions. Estimated.")
    # ---- 2016 (coarse) ----
    unit16, tot16, _ = parse_som_total_row(2016)
    table_totals[2016] = tot16
    # 2017 steam-fuel shares: coal + the steam parts of the 2017 split.
    steam_gas17 = unit17["Other"] * other_shares["Natural Gas"]
    steam_oil17 = unit17["Other"] * other_shares["Oil"]
    steam_other17 = unit17["Other"] * other_shares["Other"]
    steam_tot17 = unit17["Coal"] + steam_gas17 + steam_oil17 + steam_other17
    steam_shares = {"Coal": unit17["Coal"] / steam_tot17,
                    "Natural Gas": steam_gas17 / steam_tot17,
                    "Oil": steam_oil17 / steam_tot17,
                    "Other": steam_other17 / steam_tot17}
    b16 = {f: 0.0 for f in FUELS}
    b16["Natural Gas"] += unit16["Combined Cycle"]
    b16["Natural Gas"] += unit16["CT"] * ct_gas_share
    b16["Oil"] += unit16["CT"] * (1 - ct_gas_share)
    b16["Oil"] += unit16["Diesel"]
    b16["Other"] += unit16["Fuel Cell"]
    b16["Pumped Storage"] += unit16["Hydroelectric"] * hydro_pumped_share
    b16["Hydro"] += unit16["Hydroelectric"] * (1 - hydro_pumped_share)
    b16["Nuclear"] += unit16["Nuclear"]
    b16["Solar"] += unit16["Solar"]
    b16["Battery Storage"] += unit16["Storage"]
    b16["Wind"] += unit16["Wind"]
    for f, s in steam_shares.items():
        b16[f] += unit16["Steam"] * s
    buckets[2016] = b16
    notes[2016] = ("SOM 2016 Table 12-10 coarse columns; Steam split "
                   "coal/gas/oil/other using 2017 steam shares, CT and "
                   "Hydroelectric split using 2018 proportions. Estimated.")
    for y in range(2018, 2026):
        notes[y] = f"SOM {y} Table 12-1 Total row, detailed unit types."
    # Coherence check: the 2016 split implies a 2016->2017 coal fall of
    # 1,453 MW vs 2,281 MW of SOM-recorded coal retirements in 2016-2017
    # (243.0 + 2,038.0 MW, SOM 2025 Table 12-6). The 828 MW gap is within
    # the estimation error of the coarse-table split plus SOM restatements;
    # it is not forced to match.
    rows = []
    for y in sorted(buckets):
        r = {"year": y, "period": "trailing", "source_note": notes[y]}
        r.update({f: round(buckets[y][f], 1) for f in FUELS})
        # Total is the published SOM Table Total row (exact), not the sum
        # of the rounded buckets (which can differ by 0.1 MW on rounding).
        r["Total"] = round(table_totals[y], 1)
        rows.append(r)
    return pd.DataFrame(rows), buckets, notes


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


def eia_changelog():
    """Build the forward changelog from EIA-860M (BA == PJM).

    Additions: units in service in 2026 (Operating sheet, Operating
    Year == 2026) + Planned sheet units, Planned Operation Year 2026-2031.
    Retirements: Retired sheet actuals with Retirement Year == 2026 +
    Operating sheet planned retirements, Planned Retirement Year 2026-2036.
    RMR override: coal planned retirements with original year in
    {2026, 2027, 2028} move to effective Jan 2029.
    Returns (changelog_df, plants_df, diagnostics dict).
    """
    op = load_eia_sheet("Operating")
    pl = load_eia_sheet("Planned")
    rt = load_eia_sheet("Retired")
    for df in (op, pl, rt):
        df["fuel"] = df.apply(eia_fuel, axis=1)
    pjm_op = op[op["Balancing Authority Code"] == "PJM"].copy()
    pjm_pl = pl[pl["Balancing Authority Code"] == "PJM"].copy()
    pjm_rt = rt[rt["Balancing Authority Code"] == "PJM"].copy()

    diag = {}
    diag["eia_operating_pjm_units"] = int(len(pjm_op))
    diag["eia_operating_pjm_nameplate_mw"] = round(
        pjm_op["Nameplate Capacity (MW)"].sum(), 1)
    diag["eia_operating_pjm_netsummer_mw"] = round(
        pjm_op["Net Summer Capacity (MW)"].sum(), 1)
    diag["eia_operating_pjm_by_fuel_nameplate"] = {
        f: round(v, 1) for f, v in
        pjm_op.groupby("fuel")["Nameplate Capacity (MW)"].sum().items()}
    diag["eia_operating_pjm_by_fuel_netsummer"] = {
        f: round(v, 1) for f, v in
        pjm_op.groupby("fuel")["Net Summer Capacity (MW)"].sum().items()}
    op_only = pjm_op[pjm_op["Status"] == "(OP) Operating"]
    diag["eia_operating_pjm_op_only_netsummer_mw"] = round(
        op_only["Net Summer Capacity (MW)"].sum(), 1)
    diag["eia_operating_pjm_nonop_nameplate_mw"] = round(
        pjm_op[pjm_op["Status"] != "(OP) Operating"]
        ["Nameplate Capacity (MW)"].sum(), 1)

    # BA boundary cross-check.
    pj_st = ["DE", "IL", "IN", "KY", "MD", "MI", "NJ", "NC", "OH", "PA",
             "TN", "VA", "WV", "DC"]
    in_states = op[op["Plant State"].isin(pj_st)]
    out_ba = in_states[in_states["Balancing Authority Code"] != "PJM"]
    diag["ba_boundary_in_footprint_states_not_pjm_mw"] = round(
        out_ba["Nameplate Capacity (MW)"].sum(), 1)
    diag["ba_boundary_in_footprint_states_not_pjm_units"] = int(len(out_ba))
    diag["ba_boundary_in_footprint_states_not_pjm_by_ba_mw"] = {
        k: round(v, 1) for k, v in
        out_ba.groupby("Balancing Authority Code")
        ["Nameplate Capacity (MW)"].sum().items()}
    ba_out = pjm_op[~pjm_op["Plant State"].isin(pj_st)]
    diag["ba_boundary_pjm_ba_outside_footprint_mw"] = round(
        ba_out["Nameplate Capacity (MW)"].sum(), 1)
    diag["ba_boundary_pjm_ba_outside_footprint_units"] = int(len(ba_out))

    # ---- Additions ----
    adds = []
    in_service_2026 = pjm_op[pd.to_numeric(pjm_op["Operating Year"],
                                           errors="coerce") == 2026]
    for _, r in in_service_2026.iterrows():
        adds.append(_plant_row(r, "addition", "addition",
                               int(r["Operating Year"]),
                               int(pd.to_numeric(r["Operating Month"],
                                                 errors="coerce") or 1),
                               "Operating sheet: in service Jan-Sep 2026"))
    for _, r in pjm_pl.iterrows():
        y = pd.to_numeric(r["Planned Operation Year"], errors="coerce")
        m = pd.to_numeric(r["Planned Operation Month"], errors="coerce")
        if pd.isna(y):
            continue
        adds.append(_plant_row(r, "addition", "addition", int(y),
                               int(m) if not pd.isna(m) else 1,
                               "Planned sheet"))
    adds_df = pd.DataFrame(adds)

    # ---- Retirements (original dates first) ----
    rets = []
    rt26 = pjm_rt[pd.to_numeric(pjm_rt["Retirement Year"],
                                errors="coerce") == 2026]
    for _, r in rt26.iterrows():
        rets.append(_plant_row(
            r, "retirement", "retired (actual)",
            int(r["Retirement Year"]),
            int(pd.to_numeric(r["Retirement Month"], errors="coerce") or 1),
            "Retired sheet: actual Jan-Sep 2026"))
    pr = pjm_op[pd.to_numeric(pjm_op["Planned Retirement Year"],
                              errors="coerce").notna()].copy()
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
        key(in_service_2026) & key(pjm_pl[pjm_pl["Planned Operation Year"] == 2026]))
    diag["overlap_retired2026_vs_plannedret2026_units"] = len(
        key(rt26) & key(pjm_op[pd.to_numeric(
            pjm_op["Planned Retirement Year"], errors="coerce") == 2026]))

    # ---- RMR override (corrected: Jan 2029) ----
    mask = ((rets_df["fuel"] == "Coal")
            & (rets_df["retirement_status"] == "planned retirement")
            & (rets_df["original_year"].isin(RMR_YEARS)))
    affected = rets_df[mask].copy()
    diag["rmr_affected_units"] = int(len(affected))
    diag["rmr_affected_mw"] = round(affected["mw_nameplate"].sum(), 1)
    diag["rmr_affected_by_original_year"] = {
        str(int(y)): {"units": int((affected["original_year"] == y).sum()),
                      "mw": round(affected[affected["original_year"] == y]
                                  ["mw_nameplate"].sum(), 1)}
        for y in RMR_YEARS}
    diag["rmr_delayed_mw"] = diag["rmr_affected_mw"]  # Jan 2029 is after all of 2028
    diag["rmr_pulled_forward_mw"] = 0.0
    diag["rmr_units_detail"] = [
        {"plant": r["plant_name"], "state": r["state"],
         "generator_id": str(r["generator_id"]), "mw": round(r["mw_nameplate"], 1),
         "original": r["original_date"], "effective": "2029-01"}
        for _, r in affected.sort_values(
            ["original_year", "original_month"]).iterrows()]
    rets_df.loc[mask, "effective_year"] = RMR_TARGET_YEAR
    rets_df.loc[mask, "effective_month"] = RMR_TARGET_MONTH
    rets_df.loc[mask, "rmr_override"] = True
    rets_df["effective_date"] = (
        rets_df["effective_year"].astype(int).astype(str) + "-"
        + rets_df["effective_month"].astype(int).astype(str).str.zfill(2))

    plants = pd.concat([adds_df, rets_df], ignore_index=True)
    plants = plants.sort_values(["effective_year", "type", "fuel",
                                 "plant_name"])

    # ---- Changelog by year x fuel (effective dates) ----
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
    diag["planned_by_status_mw"] = {
        k: round(v, 1) for k, v in
        pjm_pl.groupby("Status")["Nameplate Capacity (MW)"].sum().items()}
    diag["planned_under_construction_mw"] = round(
        pjm_pl[pjm_pl["Status"].str.contains(
            "Under construction|Construction complete", na=False)]
        ["Nameplate Capacity (MW)"].sum(), 1)
    diag["planned_not_under_construction_mw"] = round(
        pjm_pl[pjm_pl["Status"].str.contains(
            "Planned for installation|Regulatory approvals", na=False)]
        ["Nameplate Capacity (MW)"].sum(), 1)
    diag["planned_max_operation_year"] = int(pd.to_numeric(
        pjm_pl["Planned Operation Year"], errors="coerce").max())
    diag["retirements_2026_actual_mw"] = round(
        rt26["Nameplate Capacity (MW)"].sum(), 1)
    return changelog, plants, diag, adds_df, rets_df


def _plant_row(r, typ, status_label, year, month, source):
    """One unit-level changelog row from an EIA-860M record."""
    return {
        "plant_name": r["Plant Name"],
        "plant_id": r["Plant ID"],
        "generator_id": str(r["Generator ID"]),
        "state": r["Plant State"],
        "county": r.get("County", ""),
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
        "rmr_override": False,
    }


# ---------------- Build, outputs, charts ----------------
FUEL_COLORS = {
    "Coal": "#3b3b3b", "Natural Gas": "#d95f02", "Nuclear": "#7570b3",
    "Hydro": "#1b9e77", "Pumped Storage": "#66a61e", "Wind": "#377eb8",
    "Solar": "#e6ab02", "Oil": "#a6761d", "Battery Storage": "#e7298a",
    "Other": "#999999",
}
STACK_ORDER = ["Coal", "Natural Gas", "Nuclear", "Hydro", "Pumped Storage",
               "Oil", "Wind", "Solar", "Battery Storage", "Other"]


def build_stack(trailing_df, changelog):
    """Forward stack: anchor (Dec 31, 2025) + cumulative net changelog."""
    anchor = trailing_df[trailing_df["year"] == ANCHOR_YEAR].iloc[0]
    rows = []
    running = {f: float(anchor[f]) for f in FUELS}
    for y in range(2026, 2037):
        net = changelog[changelog["year"] == y]
        for f in FUELS:
            running[f] += float(
                net.loc[net["fuel"] == f, "net_mw"].iloc[0])
        r = {"year": y, "period": "forward",
             "source_note": "SOM Dec-31-2025 anchor + EIA-860M changelog "
                            "(effective dates, RMR override applied)"}
        r.update({f: round(running[f], 1) for f in FUELS})
        r["Total"] = round(sum(running.values()), 1)
        rows.append(r)
    fwd = pd.DataFrame(rows)
    stack_wide = pd.concat(
        [trailing_df[["year", "period", "source_note"] + FUELS + ["Total"]],
         fwd], ignore_index=True)
    return stack_wide


def to_long_stack(stack_wide):
    rows = []
    for _, r in stack_wide.iterrows():
        for f in FUELS + ["Total"]:
            rows.append({
                "year": int(r["year"]), "fuel": f,
                "mw": round(float(r[f]), 1),
                "period": r["period"],
                "anchor_year": bool(r["year"] == ANCHOR_YEAR),
                "source_note": r["source_note"],
            })
    return pd.DataFrame(rows)


def parse_som_q2_2026():
    """Cross-check: 2026 Q2 SOM (Jun 30, 2026) Table 12-1, same 22-col layout."""
    pdf = RAW / "som2026q2_sec12.pdf"
    download(SOM_Q2_2026_URL, pdf)
    txt = pdftotext(pdf, RAW / "som2026q2_sec12.txt")
    lines = txt.read_text(errors="replace").splitlines()
    hidx = next(i for i, ln in enumerate(lines)
                if "Table 12-1 Existing capacity" in ln)
    vals = None
    for ln in lines[hidx + 1:hidx + 60]:
        s = ln.strip()
        if s.startswith("Total"):
            nums = [float(x.replace(",", ""))
                    for x in re.findall(r"[\d,]+\.\d", s)]
            if len(nums) == len(SOM_COLS_DETAILED) + 1:
                vals = nums
                break
    if vals is None:
        return None
    unit = dict(zip(SOM_COLS_DETAILED, vals[:-1]))
    return {"total_mw": vals[-1], "buckets": som_buckets(2026, unit),
            "unit_types": unit}


def make_charts(stack_wide, changelog):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    years = stack_wide["year"].values
    # 1. Stacked area, 2016-2036, GW.
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
    ax.set_xlabel("Year (Dec 31 position; 2026-2036 = anchor + EIA changelog)")
    ax.set_title("PJM generation capacity stack by fuel, 2016-2036\n"
                 "Trailing: PJM State of the Market; Forward: SOM anchor + "
                 "EIA-860M changelog (RMR coal delay to Jan 2029)")
    ax.legend(ncol=2, fontsize=9, loc="upper left")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(BASE / "01_stacked_area.png", dpi=150)
    plt.close(fig)

    # 2. Annual net change by fuel, forward 2026-2036 (stacked bars, GW).
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
    ax.set_ylabel("Net capacity change (GW / year)")
    ax.set_xlabel("Year")
    ax.set_title("PJM annual net capacity change by fuel, forward 2026-2036\n"
                 "(EIA-860M additions minus retirements, effective dates)")
    ax.legend(ncol=2, fontsize=9, loc="upper right")
    ax.grid(True, alpha=0.3, axis="y")
    fig.tight_layout()
    fig.savefig(BASE / "02_net_change_forward.png", dpi=150)
    plt.close(fig)

    # 3. Cumulative forward additions vs retirements by fuel (GW).
    cum = changelog.groupby("fuel")[["additions_mw",
                                     "retirements_mw"]].sum() / 1000.0
    cum = cum.reindex(STACK_ORDER).fillna(0.0)
    fig, ax = plt.subplots(figsize=(11, 6))
    x = np.arange(len(cum))
    w = 0.38
    ax.bar(x - w / 2, cum["additions_mw"], w, label="Additions 2026-2036",
           color="#1b9e77")
    ax.bar(x + w / 2, cum["retirements_mw"], w, label="Retirements 2026-2036",
           color="#d95f02")
    ax.set_xticks(x)
    ax.set_xticklabels(cum.index, rotation=30, ha="right")
    ax.set_ylabel("Cumulative MW 2026-2036 (GW)")
    ax.set_title("PJM forward additions vs retirements by fuel, cumulative "
                 "2026-2036\n(EIA-860M, effective dates; coal retirements "
                 "delayed to Jan 2029 by RMR override)")
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3, axis="y")
    fig.tight_layout()
    fig.savefig(BASE / "03_add_vs_retire_fuel.png", dpi=150)
    plt.close(fig)
    print("  charts written")


README_TEMPLATE = """# PJM generation capacity stack, 2016-2036 (trailing + forward)

PJM-level only (no regionalization). Built {build_date} by `build_stack.py`
from free public data only.

## What this is

* **Trailing (2016-2025):** Dec-31 installed capacity by fuel, from the PJM
  State of the Market (Monitoring Analytics / Independent Market Monitor),
  Section 12, Table 12-1, parsed from the published PDFs.
* **Anchor (today):** Dec 31, 2025 SOM installed capacity: **{anchor_total:,.1f} MW**
  ({anchor_coal:,.1f} MW coal, {anchor_gas:,.1f} MW gas, {anchor_nuc:,.1f} MW nuclear).
  This is the base. Nothing replaces it.
* **Forward (2026-2036):** anchor + the EIA-860M changelog, year by year:
  additions (EIA-860M Planned sheet + units already in service in 2026)
  minus retirements (EIA-860M Retired-sheet actuals for 2026 + Operating-sheet
  planned retirements). 2026 stack total: **{total_2026:,.1f} MW**;
  2036 stack total: **{total_2036:,.1f} MW**.
* **Cross-check:** 2026 Q2 SOM (Jun 30, 2026) total installed capacity was
  {q2_total:,.1f} MW vs the Dec-31-2025 anchor {anchor_total:,.1f} MW
  ({q2_delta:+,.1f} MW). Coal fell {q2_coal_delta:+,.1f} MW in H1 2026 in the
  SOM with no PJM coal retirement on the EIA Retired sheet in that period —
  flagged as an unexplained SOM restatement/reclassification, not modelled.

## Sources (with vintages)

* EIA-860M, **September 2026** vintage (data as of Sep 30, 2026; released
  Oct 23, 2026; next release scheduled Nov 24, 2026):
  https://www.eia.gov/electricity/data/eia860m/
  file: https://www.eia.gov/electricity/data/eia860m/xls/september_generator2026.xlsx
* PJM State of the Market, Monitoring Analytics:
  https://www.monitoringanalytics.com/reports/pjm-state-of-the-market
  Annual SOM Sec. 12 PDFs 2016-2025:
  https://www.monitoringanalytics.com/reports/pjm_state_of_the_market/{{YYYY}}/{{YYYY}}-som-pjm-sec12.pdf
  (2025 annual created Mar 12, 2026). 2026 Q2 Sec. 12:
  https://www.monitoringanalytics.com/reports/PJM_State_of_the_Market/2026/2026q2-som-pjm-sec12.pdf

## Capacity definition

SOM "installed capacity" = summer ICAP rating, except solar and wind which
are nameplate. EIA-860M changelog is in **nameplate MW**. Applying nameplate
changes to an ICAP anchor is an approximation: EIA does not publish ICAP.
Reconciliation (Sep-2026 EIA Operating, BA=PJM, vs Dec-2025 SOM anchor):

| Fuel | SOM anchor (MW) | EIA nameplate (MW) | EIA net summer (MW) |
|---|---:|---:|---:|
{recon_rows}
| **Total** | **{anchor_total:,.1f}** | **{eia_np:,.1f}** | **{eia_ns:,.1f}** |

EIA exceeds SOM by {eia_gap_pct:+.1f}% on nameplate, {eia_gap_ns_pct:+.1f}% on
net summer. Drivers: nameplate-vs-summer rating (nuclear: EIA nameplate
35,447 MW vs net summer 33,492 MW, i.e. the SOM 33,453 MW — the gap is
almost entirely definitional); gas nameplate counts every CT/steam component
of combined-cycle plants at nameplate while SOM CC is an ICAP rating;
EIA includes standby/out-of-service units (3,681 MW nameplate) and units
that entered service Jan-Sep 2026 (2,897 MW); solar is the largest
unexplained gap (EIA 19,519 MW vs SOM 14,888 MW, +4,631 MW — only ~1,424 MW
is 2026 in-service additions; the rest is BA/scope and small-unit coverage
differences, reported honestly rather than forced to match).

## PJM filter (EIA)

Balancing Authority Code == `PJM` (4,080 operating units). A state filter
would be wrong: **{ba_not_pjm_mw:,.1f} MW** of nameplate in PJM footprint
states sits in other BAs (MISO, TVA, Duke, LG&E, ...), while only
**{ba_out_mw:,.1f} MW** of BA=PJM capacity sits outside the footprint states
(one 3.3 MW solar unit in MN). Ambiguous plants: essentially none on the
BA boundary — the BA code is the plant's actual balancing authority; the
residual ambiguity is that PJM covers only *parts* of IL, IN, KY, MI, NC
and TN, which is exactly why the BA filter, not the state filter, is used.

## Fuel mapping

* SOM unit types → buckets: Steam-Coal → Coal; Combined Cycle + CT-Natural
  Gas + RICE-Natural Gas + Steam-Natural Gas → Natural Gas; Nuclear →
  Nuclear; Hydro-Run of River → Hydro; Hydro-Pumped Storage → Pumped
  Storage; Wind (+ Wind+Storage) → Wind; Solar (+ Solar+Storage, Solar+Wind)
  → Solar; CT-Oil + RICE-Oil + Steam-Oil → Oil; Battery → Battery Storage;
  CT-Other + Fuel Cell + RICE-Other + Steam-Other → Other.
* EIA rows → buckets by Energy Source Code + Prime Mover: coal = ANT/BIT/
  LIG/SUB/WC; gas = NG; nuclear = NUC; solar = SUN; wind = WND; hydro =
  WAT with prime mover HY; pumped storage = prime mover PS; battery =
  prime mover BA/FW (energy source MWH); oil = DFO/RFO/JF/KER/PC; else Other.
* Definitional breaks (documented, not smoothed away): 2018 SOM put
  oil-fired CTs in "CT-Other" (3,997.6 MW) and reclassified them to
  "CT-Oil" in 2019 — the 2018 CT-Other is mapped to Oil here. Nuclear
  wobbles 2016-2018 (34,872 → 33,732 → 34,258 MW) and pumped storage
  2020-2021 (5,052 → 4,792 MW) are SOM restatements. 2016-2017 SOM tables
  are coarser and were split into fuels with documented proportional
  estimates (see `som_trailing()` in build_stack.py); those two years are
  flagged `estimated` in the stack CSV's source_note.
* SOM prose vs table: the 2025 SOM text says combined cycle 57,047.4 MW;
  Table 12-1 says 57,047.7 MW. The table value is used.

## RMR override (manual scenario, corrected date Jan 2029)

All PJM coal retirements scheduled in 2026, 2027 or 2028 are pushed to
**Jan 2029**. Affected: **{rmr_units} units, {rmr_mw:,.1f} MW** —
2026: {rmr_2026_mw:,.1f} MW / {rmr_2026_n} units; 2027: {rmr_2027_mw:,.1f} MW /
{rmr_2027_n} units (Kincaid 1 & 2, IL, 659.5 MW each, orig. Dec 2027);
2028: {rmr_2028_mw:,.1f} MW / {rmr_2028_n} units (Cardinal 3, OH, 650 MW;
Rockport 1 & 2, IN, 1,300 MW each, orig. Dec 2028). Because Jan 2029 is
after all of 2028 this is a **pure delay: {rmr_mw:,.1f} MW delayed,
0 MW pulled forward**. (An earlier instruction said Jan 2028; that was
corrected to Jan 2029 — a Jan 2028 date would have pulled the Dec-2028
retirements *forward*.) Original dates are preserved in
`pjm_capacity_plants.csv` (`rmr_override`, `original_retirement_date`,
`effective_retirement_date`); the changelog and stack use effective dates.
Already-retired units are not overridden. This is a scenario, not a
forecast — RMR designations are unit-specific.

## Forward pipeline (EIA-860M, BA=PJM, nameplate)

* Total planned additions 2026-2036: **{planned_total:,.1f} MW** ({planned_n} units).
  By fuel: {planned_by_fuel}
* By year: {planned_by_year}
* By status: only **{uc_mw:,.1f} MW** under construction / construction
  complete; **{p_mw:,.1f} MW** (status P) have not even begun regulatory
  approvals. Planned ≠ built; dates slip — e.g. Eddystone 3 & 4 (gas steam,
  391 MW each) were listed for Feb 2026 retirement in the Dec-2025 SOM and
  now show Nov 2026 in EIA-860M.
* Largest planned additions: {largest_adds}
* Largest planned retirements (effective dates): {largest_rets}
* The EIA-860M planned horizon effectively ends in 2031 (latest planned
  operation year in the file); **no additions are listed for 2032-2036**.
  That is a coverage artifact, not a forecast of zero builds. The PJM
  interconnection queue is much larger: 41,529 MW active/under
  construction/suspended at Dec 31, 2025 (SOM Table 12-26) — the EIA
  planned list is a subset of projects that have reached EIA reporting.

## Limitations

* Planned ≠ built; date slippage is the norm, not the exception.
* EIA-860M planned list ≠ PJM interconnection queue (see above).
* BA boundary vs PJM footprint (see filter section); small residual
  ambiguity where PJM covers only part of a state.
* Nameplate vs ICAP vs summer capability (see capacity definition);
  forward changes are nameplate applied to an ICAP anchor.
* Storage is MW only — duration (MWh) and ELCC derates are not captured;
  solar/wind MW overstate their capacity contribution (ELCC).
* No load, energy (MWh), or capacity-factor analysis; this is a capacity
  (MW) stack only.
* Trailing 2016-2017 fuel splits are proportional estimates (flagged).
* Retirements beyond 2036 in the EIA file (~57 MW, small solar/battery)
  are outside the window and excluded.

## Files

* `build_stack.py` — reproducible build (downloads, parses, builds, charts)
* `pjm_capacity_stack.csv` — year × fuel, MW, trailing/forward, anchor flag
* `pjm_capacity_changelog.csv` — additions / retirements / net by year × fuel
* `pjm_capacity_plants.csv` — unit-level forward changelog
* `summary.json` — anchor, totals, pipeline, largest units, RMR, reconciliation
* `01_stacked_area.png`, `02_net_change_forward.png`, `03_add_vs_retire_fuel.png`
* `raw/` — downloaded source files (EIA xlsx, SOM Sec-12 PDFs 2016-2025, 2026 Q2)
"""


def main():
    print("== PJM capacity stack build ==")
    print("Step 1: SOM trailing 2016-2025")
    trailing_df, buckets, notes = som_trailing()
    print("Step 2: EIA-860M changelog (download if needed)")
    download(EIA_URL, EIA_FILE)
    changelog, plants, diag, adds_df, rets_df = eia_changelog()
    print("Step 3: forward stack from anchor")
    stack_wide = build_stack(trailing_df, changelog)
    stack_long = to_long_stack(stack_wide)

    anchor = trailing_df[trailing_df["year"] == ANCHOR_YEAR].iloc[0]
    anchor_by_fuel = {f: round(float(anchor[f]), 1) for f in FUELS}
    q2 = parse_som_q2_2026()
    q2_buckets = q2["buckets"] if q2 else {}
    q2_total = q2["total_mw"] if q2 else None

    # Outputs.
    stack_long.to_csv(BASE / "pjm_capacity_stack.csv", index=False)
    changelog.to_csv(BASE / "pjm_capacity_changelog.csv", index=False)
    plant_cols = ["plant_name", "plant_id", "generator_id", "state", "county",
                  "balancing_authority", "fuel", "energy_source_code",
                  "prime_mover_code", "technology", "mw_nameplate",
                  "mw_net_summer", "type", "status", "retirement_status",
                  "source_sheet", "original_year", "original_month",
                  "original_date", "effective_year", "effective_month",
                  "effective_date", "rmr_override"]
    plants[plant_cols].to_csv(BASE / "pjm_capacity_plants.csv", index=False)
    print(f"  stack rows: {len(stack_long)}, changelog rows: {len(changelog)}, "
          f"plant rows: {len(plants)}")

    # Summary.
    fwd = changelog[changelog["year"] >= 2026]
    by_fuel_add = fwd.groupby("fuel")["additions_mw"].sum().round(1).to_dict()
    by_fuel_ret = fwd.groupby("fuel")["retirements_mw"].sum().round(1).to_dict()
    by_year_add = fwd.groupby("year")["additions_mw"].sum().round(1).to_dict()
    by_year_ret = fwd.groupby("year")["retirements_mw"].sum().round(1).to_dict()
    adds_f = adds_df[adds_df["effective_year"].between(2026, 2036)]
    rets_f = rets_df[rets_df["effective_year"].between(2026, 2036)]
    largest_adds = [
        {"plant": r["plant_name"], "state": r["state"],
         "generator_id": str(r["generator_id"]), "fuel": r["fuel"],
         "mw_nameplate": round(r["mw_nameplate"], 1),
         "effective_date": r["effective_date"], "status": r["status"]}
        for _, r in adds_f.sort_values("mw_nameplate", ascending=False)
        .head(10).iterrows()]
    largest_rets = [
        {"plant": r["plant_name"], "state": r["state"],
         "generator_id": str(r["generator_id"]), "fuel": r["fuel"],
         "mw_nameplate": round(r["mw_nameplate"], 1),
         "original_date": r["original_date"],
         "effective_date": r["effective_date"],
         "rmr_override": bool(r["rmr_override"])}
        for _, r in rets_f.sort_values("mw_nameplate", ascending=False)
        .head(10).iterrows()]
    yearly_totals = {int(r["year"]): round(float(r["Total"]), 1)
                     for _, r in stack_wide.iterrows()}
    # Implied "today" (Sep 30, 2026 data) position: anchor + 2026 YTD actuals.
    ytd_add = adds_df[(adds_df["source_sheet"].str.startswith("Operating"))
                      & (adds_df["effective_year"] == 2026)]["mw_nameplate"].sum()
    ytd_ret = rets_df[rets_df["retirement_status"] == "retired (actual)"][
        "mw_nameplate"].sum()
    summary = {
        "anchor": {
            "source": "PJM State of the Market 2025 Annual, Table 12-1 "
                      "(Monitoring Analytics)",
            "vintage": "Dec 31, 2025 (report created Mar 12, 2026)",
            "definition": "Installed capacity: summer ICAP rating, except "
                          "solar and wind at nameplate",
            "total_mw": round(float(anchor["Total"]), 1),
            "by_fuel_mw": anchor_by_fuel,
        },
        "eia_860m": {
            "source": EIA_PAGE,
            "file_url": EIA_URL,
            "vintage": EIA_VINTAGE,
            "ba_filter": "Balancing Authority Code == PJM",
        },
        "reconciliation_eia_operating_pjm_vs_som_anchor": {
            "eia_nameplate_mw": diag["eia_operating_pjm_nameplate_mw"],
            "eia_netsummer_mw": diag["eia_operating_pjm_netsummer_mw"],
            "eia_op_only_netsummer_mw":
                diag["eia_operating_pjm_op_only_netsummer_mw"],
            "som_anchor_mw": round(float(anchor["Total"]), 1),
            "gap_nameplate_mw": round(
                diag["eia_operating_pjm_nameplate_mw"]
                - float(anchor["Total"]), 1),
            "gap_netsummer_mw": round(
                diag["eia_operating_pjm_netsummer_mw"]
                - float(anchor["Total"]), 1),
            "by_fuel_nameplate_mw": diag["eia_operating_pjm_by_fuel_nameplate"],
            "by_fuel_netsummer_mw": diag["eia_operating_pjm_by_fuel_netsummer"],
            "som_anchor_by_fuel_mw": anchor_by_fuel,
        },
        "ba_boundary": {
            "in_footprint_states_not_pjm_mw":
                diag["ba_boundary_in_footprint_states_not_pjm_mw"],
            "in_footprint_states_not_pjm_units":
                diag["ba_boundary_in_footprint_states_not_pjm_units"],
            "in_footprint_states_not_pjm_by_ba_mw":
                diag["ba_boundary_in_footprint_states_not_pjm_by_ba_mw"],
            "pjm_ba_outside_footprint_mw":
                diag["ba_boundary_pjm_ba_outside_footprint_mw"],
            "pjm_ba_outside_footprint_units":
                diag["ba_boundary_pjm_ba_outside_footprint_units"],
        },
        "som_2026q2_crosscheck": {
            "source": "2026 Q2 SOM Sec 12, Table 12-1 (Jun 30, 2026)",
            "total_mw": q2_total,
            "by_fuel_mw": {f: round(v, 1) for f, v in q2_buckets.items()},
            "delta_vs_dec2025_anchor_mw": (
                round(q2_total - float(anchor["Total"]), 1)
                if q2_total else None),
        },
        "implied_today_position_memo": {
            "note": "Anchor + 2026 year-to-date actuals in EIA-860M Sep 2026 "
                    "(in-service additions minus actual retirements). Memo only; "
                    "the stack's 2026 point is the full-year position.",
            "additions_ytd_mw": round(float(ytd_add), 1),
            "retirements_ytd_mw": round(float(ytd_ret), 1),
            "implied_mw": round(float(anchor["Total"]) + float(ytd_add)
                                - float(ytd_ret), 1),
        },
        "yearly_totals_mw": yearly_totals,
        "trailing_change_2016_to_2025_mw": {
            f: round(float(trailing_df[trailing_df["year"] == 2025].iloc[0][f])
                     - float(trailing_df[trailing_df["year"] == 2016].iloc[0][f]), 1)
            for f in FUELS},
        "forward_pipeline_2026_2036": {
            "additions_total_mw": round(
                fwd["additions_mw"].sum(), 1),
            "additions_count": int(fwd["additions_count"].sum()),
            "retirements_total_mw": round(
                fwd["retirements_mw"].sum(), 1),
            "retirements_count": int(fwd["retirements_count"].sum()),
            "net_mw": round(fwd["net_mw"].sum(), 1),
            "additions_by_fuel_mw": {k: round(float(v), 1)
                                     for k, v in by_fuel_add.items()},
            "retirements_by_fuel_mw": {k: round(float(v), 1)
                                       for k, v in by_fuel_ret.items()},
            "additions_by_year_mw": {str(k): round(float(v), 1)
                                     for k, v in by_year_add.items()},
            "retirements_by_year_mw": {str(k): round(float(v), 1)
                                       for k, v in by_year_ret.items()},
            "by_status_mw": diag["planned_by_status_mw"],
            "under_construction_mw": diag["planned_under_construction_mw"],
            "not_under_construction_mw":
                diag["planned_not_under_construction_mw"],
            "latest_planned_operation_year": diag["planned_max_operation_year"],
        },
        "largest_planned_additions": largest_adds,
        "largest_planned_retirements_effective": largest_rets,
        "rmr_override": {
            "rule": "PJM coal retirements scheduled 2026-2028 pushed to "
                    "Jan 2029 (corrected from Jan 2028)",
            "affected_units": diag["rmr_affected_units"],
            "affected_mw": diag["rmr_affected_mw"],
            "by_original_year": diag["rmr_affected_by_original_year"],
            "delayed_mw": diag["rmr_delayed_mw"],
            "pulled_forward_mw": diag["rmr_pulled_forward_mw"],
            "units": diag["rmr_units_detail"],
        },
        "overlap_guards": {
            "operating2026_vs_planned2026_units":
                diag["overlap_operating2026_vs_planned2026_units"],
            "retired2026_vs_plannedret2026_units":
                diag["overlap_retired2026_vs_plannedret2026_units"],
        },
        "files": {
            "stack_csv": "pjm_capacity_stack.csv",
            "changelog_csv": "pjm_capacity_changelog.csv",
            "plants_csv": "pjm_capacity_plants.csv",
            "summary_json": "summary.json",
            "charts": ["01_stacked_area.png", "02_net_change_forward.png",
                       "03_add_vs_retire_fuel.png"],
        },
    }
    with open(BASE / "summary.json", "w") as f:
        json.dump(summary, f, indent=2)

    # README.
    recon_rows = "\n".join(
        f"| {fu} | {anchor_by_fuel[fu]:,.1f} | "
        f"{diag['eia_operating_pjm_by_fuel_nameplate'].get(fu, 0):,.1f} | "
        f"{diag['eia_operating_pjm_by_fuel_netsummer'].get(fu, 0):,.1f} |"
        for fu in FUELS)
    planned_by_fuel = ", ".join(
        f"{k} {v:,.0f} MW" for k, v in
        sorted(by_fuel_add.items(), key=lambda x: -x[1]) if v > 0)
    planned_by_year = ", ".join(
        f"{k}: {v:,.0f} MW" for k, v in sorted(by_year_add.items()))
    largest_adds_s = "; ".join(
        f"{a['plant']} ({a['state']}, {a['fuel']}, {a['mw_nameplate']:,.0f} MW, "
        f"{a['effective_date']}, {a['status']})" for a in largest_adds[:5])
    largest_rets_s = "; ".join(
        f"{a['plant']} ({a['state']}, {a['fuel']}, {a['mw_nameplate']:,.0f} MW, "
        f"orig {a['original_date']} -> eff {a['effective_date']})"
        for a in largest_rets[:5])
    import datetime
    readme = README_TEMPLATE.format(
        build_date=datetime.date.today().isoformat(),
        anchor_total=float(anchor["Total"]),
        anchor_coal=anchor_by_fuel["Coal"],
        anchor_gas=anchor_by_fuel["Natural Gas"],
        anchor_nuc=anchor_by_fuel["Nuclear"],
        total_2026=yearly_totals[2026],
        total_2036=yearly_totals[2036],
        q2_total=q2_total or 0,
        q2_delta=(q2_total - float(anchor["Total"])) if q2_total else 0,
        q2_coal_delta=(q2_buckets.get("Coal", 0) - anchor_by_fuel["Coal"]
                       if q2_buckets else 0),
        recon_rows=recon_rows,
        eia_np=diag["eia_operating_pjm_nameplate_mw"],
        eia_ns=diag["eia_operating_pjm_netsummer_mw"],
        eia_gap_pct=100 * (diag["eia_operating_pjm_nameplate_mw"]
                           - float(anchor["Total"])) / float(anchor["Total"]),
        eia_gap_ns_pct=100 * (diag["eia_operating_pjm_netsummer_mw"]
                              - float(anchor["Total"])) / float(anchor["Total"]),
        ba_not_pjm_mw=diag["ba_boundary_in_footprint_states_not_pjm_mw"],
        ba_out_mw=diag["ba_boundary_pjm_ba_outside_footprint_mw"],
        rmr_units=diag["rmr_affected_units"],
        rmr_mw=diag["rmr_affected_mw"],
        rmr_2026_mw=diag["rmr_affected_by_original_year"]["2026"]["mw"],
        rmr_2026_n=diag["rmr_affected_by_original_year"]["2026"]["units"],
        rmr_2027_mw=diag["rmr_affected_by_original_year"]["2027"]["mw"],
        rmr_2027_n=diag["rmr_affected_by_original_year"]["2027"]["units"],
        rmr_2028_mw=diag["rmr_affected_by_original_year"]["2028"]["mw"],
        rmr_2028_n=diag["rmr_affected_by_original_year"]["2028"]["units"],
        planned_total=round(fwd["additions_mw"].sum(), 1),
        planned_n=int(fwd["additions_count"].sum()),
        planned_by_fuel=planned_by_fuel,
        planned_by_year=planned_by_year,
        uc_mw=diag["planned_under_construction_mw"],
        p_mw=diag["planned_by_status_mw"].get(
            "(P) Planned for installation, but regulatory approvals not initiated", 0),
        largest_adds=largest_adds_s,
        largest_rets=largest_rets_s,
    )
    (BASE / "README.md").write_text(readme)

    print("Step 4: charts")
    make_charts(stack_wide, changelog)
    print("Done.")
    print(f"Anchor Dec 31 2025: {float(anchor['Total']):,.1f} MW")
    print(f"Stack 2026: {yearly_totals[2026]:,.1f} MW; 2036: "
          f"{yearly_totals[2036]:,.1f} MW")
    print(f"Forward adds 2026-36: {fwd['additions_mw'].sum():,.1f} MW; "
          f"rets: {fwd['retirements_mw'].sum():,.1f} MW")
    print(f"RMR: {diag['rmr_affected_units']} units, "
          f"{diag['rmr_affected_mw']:,.1f} MW -> Jan 2029")


if __name__ == "__main__":
    main()
