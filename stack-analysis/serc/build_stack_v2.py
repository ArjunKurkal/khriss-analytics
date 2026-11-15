#!/usr/bin/env python3
"""Build SERC capacity stack v2 — EIA + manual corrections.

Mirrors ~/workspace/miso-capacity-stack/build_stack_v2.py: reads the v1
files, verifies v1 reproduces (anchor + v1 changelog, total and by
subregion), applies manual corrections, rebuilds the changelog and
stack, and writes v2 files alongside (v1 files are never overwritten).

Corrections (25 named adjustments, 81 row-level changes; see
research_log.md for the evidence and per-item confidence):
  A  ADD Georgia Power certified CCs: Bowen 7-8 1,482 MW (Nov 2029),
     Wansley 10-11 1,453 MW (Nov 2029), McIntosh 12 757 MW (Nov 2030)
     — PSC certification Dec 19, 2025, Dockets 56298/56310; none in EIA
  B  ADD Georgia Power certified BESS, 10 tranches, 3,023 MW (2027-2030)
  C  ADD Duke Person County (Roxboro) CC1 1,360 MW (Dec 2029) +
     CC2 1,360 MW (Mar 2030) — not in EIA at all
  D  ADD Roxboro coal Units 1 (410.8) + 4 (745.2) retirements (Dec 2029)
  E  ADD Marshall Advanced CTs 2x425 MW (Dec 2028) — CPCN Dec 2024
  F  RETIME Marshall Units 3/4 Dec 2033 -> Dec 2034 (Duke 2025 CRP)
  G  ADD Canadys Joint Resource CC 2,180 MW (Jun 2033) — CECPCN granted
     Jun 12, 2026 (SC PSC Order 2026-350); DESC/Santee Cooper 50/50
  H  ADD Wateree coal retirements 2x385.9 MW (Dec 2032) — DESC 2026 IRP
  I  ADD Williams coal retirement 659.7 MW (Dec 2034) — DESC 2026 IRP
  J  RETIME Winyah coal Dec 2030 -> Dec 2034 (Santee Cooper 2025 IRP Update)
  K  RETIME Victor J. Daniel Jr coal Dec 2027 -> Jan 2035 (Southern delay)
  L  RETIME Cumberland coal out of window (-> Jan 2037): TVA Board
     Feb 2026 reversed the retirement; $700m life extension
  M  RETIME Kingston coal out of window (-> Jan 2037): TVA Feb 2026 SEIS
     proposes continuing all nine coal units alongside new gas + BESS
  N  RETIME Cumberland gas CC blocks: 2029 -> Dec 2026, 2034 -> Dec 2027
     (TVA: CC operational 2026; EIA's 2029/2034 dates are stale)
  O  ADD Kingston BESS 100 MW (Dec 2027) — TVA Kingston ROD/SEIS
  P  FUEL SWITCH E.C. Gaston Unit 5, coal->gas, 952 MW (Dec 2028)
  Q  FUEL SWITCH Plant Barry Unit 5, coal->gas, 788.8 MW (Dec 2028)
  R  ADD E.W. Brown Unit 12 CC 645 MW (Dec 2030) — KY PSC CPCN Oct 2025
  S  ADD LG&E/KU 2024 IRP coal retirements (Dec 2035): Mill Creek 3
     462.6, Mill Creek 4 543.6, E.W. Brown 3 464.0
  T  ADD Duke nuclear uprates 251 MW: Brunswick 26 (Dec 2029),
     McGuire 150 + Catawba 75 (Dec 2031) — 2026 Carolinas Resource Plan
  U  ADD FPL TYSP solar shortfall vs EIA, 6 tranches, 10,355.0 MW
  V  ADD FPL TYSP battery (none in EIA), 10 tranches, 7,454.0 MW
  W  ADD FPL TYSP unnamed CT tranches 3,276 MW (2032-2035)
  X  ADD FPL CC uprates 43 MW (2027) + 19 MW (2028)
  Y  ADD Gulf Clean Energy Center (GCEC) Units 4/5 retirement 150 MW
     gas (Dec 2029) — FPL TYSP subtraction

Behind-the-meter scan: xAI's Southaven, MS plant (41 turbines, ~1,200 MW,
MDEQ permit Mar 2026) is explicitly behind-the-meter, self-supply for the
Colossus campus; under the standing rule it counts as 0 MW of grid
addition. It is not in EIA and no v2 row is added for it. The Georgia
Power certified fleet and Duke/TVA builds are grid-connected utility
plants serving system load (incl. data-center load through the grid) —
counted in full. See research_log.md.
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
SUBREGIONS = ["SERC-Central", "Florida"]
FUEL_COLORS = {
    "Coal": "#3b3b3b", "Natural Gas": "#d95f02", "Nuclear": "#7570b3",
    "Hydro": "#1b9e77", "Pumped Storage": "#66a61e", "Wind": "#377eb8",
    "Solar": "#e6ab02", "Oil": "#a6761d", "Battery Storage": "#e7298a",
    "Other": "#999999",
}
SUBREGION_COLORS = {"SERC-Central": "#377eb8", "Florida": "#e6ab02"}
ACC = "2026-11-15"  # date accessed

GA_PSC = ("Georgia PSC certification, Dockets 56298/56310 (Dec 19, 2025); "
          "Newsome testimony Nov 12, 2025")
GA_PSC_URL = "https://services.psc.ga.gov/api/v1/External/Public/Get/Document/DownloadFile/224506/105769"
DUKE_CRP_URL = "https://dms.psc.sc.gov/Attachments/Matter/310ce3e8-b895-4bab-aed7-98f59d1f98e6"
FPL_TYSP_URL = "https://floridapsc.com/pscfiles/website-files/PDF/Utilities/Electricgas/TenYearSitePlans/2026/Florida%20Power%20and%20Light%20Company.pdf"

# ---------------- Manual corrections ----------------
# EDITS: (plant_name exact, generator_id, new_mw, new_eff (y, mo),
#         new_status, note, source, source_url, confidence)
EDITS = []
# F. Marshall Units 3/4 retime Dec 2033 -> Dec 2034 (Duke 2025 CRP delayed
# Units 3&4 to 2034; EIA rows: gen 4 = coal 711.0, gen 3 = gas 711.0 —
# EIA splits the dual-fuel pair by fuel).
for _gen, _fu in [("4", "Coal"), ("3", "Natural Gas")]:
    EDITS.append(
        ("Marshall (NC)", _gen, None, (2034, 12), None,
         "Retime Dec 2033 -> Dec 2034: Duke Energy's 2025 Carolinas "
         "Resource Plan (filed Oct 2025) delayed Marshall Units 3 & 4 "
         "retirement to 2034 to help meet load growth. EIA carries the "
         "dual-fuel pair as one coal-coded and one gas-coded generator.",
         "Duke 2025 Carolinas Resource Plan; Global Energy Monitor",
         "https://www.gem.wiki/Marshall_Steam_Station", "Medium-High"))
# J. Winyah retime Dec 2030 -> Dec 2034 (4 coal units).
for _gen, _mw in [("1", 330.8), ("2", 315.0), ("3", 315.0), ("4", 315.0)]:
    EDITS.append(
        ("Winyah", _gen, None, (2034, 12), None,
         "Retime Dec 2030 -> Dec 2034: Santee Cooper's 2025 IRP Update "
         "delayed Winyah's retirement (SC PSC Docket 2025-18-E order); "
         "Aug 2026 stakeholder process confirms an assumed 2034 "
         "retirement date (ELG-compliant through that date).",
         "SC PSC Order, Docket 2025-18-E; Santee Cooper IRP SWG #12 (Aug 2026)",
         "https://dms.psc.sc.gov/Attachments/Matter/77375f6a-4b4d-4c52-869e-d8fc67f9bf02",
         "Medium"))
# K. Daniel retime Dec 2027 -> Jan 2035 (2 coal units, 548.3 MW each).
for _gen in ["1", "2"]:
    EDITS.append(
        ("Victor J Daniel Jr", _gen, None, (2035, 1), None,
         "Retime Dec 2027 -> Jan 2035 (mid-2030s placeholder): Southern "
         "Company's 2025 IRP cycle extended Plant Daniel (Mississippi "
         "Power) from a 2028 retirement to the mid-2030s, with gas "
         "co-firing; data-center load growth cited.",
         "Southern Co 2025 IRP reporting; Data Center Dynamics",
         "https://www.datacenterdynamics.com/en/news/southern-company-to-extend-life-of-three-coal-plants-due-to-data-center-energy-demand/",
         "Medium"))
# L. Cumberland coal retime out of window -> Jan 2037.
for _gen in ["1", "2"]:
    EDITS.append(
        ("Cumberland (TN)", _gen, None, (2037, 1), None,
         "Retime out of window (-> Jan 2037 placeholder = no retirement "
         "date): TVA Board reversed the Cumberland coal retirement "
         "decision in Feb 2026; TVA will invest >$700m in life extension "
         "and operate both coal units past 2028 alongside the new CC. "
         "EIA's 2028/2034 dates are the reversed plan.",
         "TVA Feb 2026 board action; Center for Biological Diversity "
         "CAA notice letter Jun 25, 2026; Knox News Feb 10, 2026",
         "https://www.knoxnews.com/story/news/environment/2026/02/10/tennessee-valley-authority-may-keep-coal-at-kingston-cumberland-plant-alongside-battery-natural-gas/88603489007/",
         "Medium"))
# M. Kingston coal retime out of window -> Jan 2037 (9 units).
for _gen in ["1", "2", "3", "4", "5", "6", "7", "8", "9"]:
    EDITS.append(
        ("Kingston", _gen, None, (2037, 1), None,
         "Retime out of window (-> Jan 2037 placeholder = no retirement "
         "date): TVA's Feb 2026 Supplemental EIS proposes continuing "
         "operation of all nine Kingston coal units alongside the "
         "previously approved gas CC + aero CTs and a 100 MW BESS. "
         "Weaker than Cumberland (a proposal under study, not a final "
         "reversal) — flagged accordingly.",
         "TVA Kingston Reservation Operations / SEIS page (Feb 2026)",
         "https://www.tva.com/environment/environmental-stewardship/environmental-reviews/nepa-detail/kingston-fossil-plant-retirement",
         "Medium"))
# N. Cumberland gas retimes.
EDITS += [
    ("Cumberland (TN)", "CTG2", None, (2026, 12), None,
     "Retime Jan 2029 -> Dec 2026: TVA's 1,450 MW Cumberland CC is built "
     "to be in operation by 2026 (TVA Jan 2023 decision; Industrial Info: "
     "gas units operational in 2026). EIA's 2029/2034 block dates are stale.",
     "TVA release Jan 10, 2023; Industrial Info Nov 2025",
     "https://www.tva.com/news-media/releases/tva-retiring-cumberland-continues-transition-to-clean-energy-future",
     "Medium"),
    ("Cumberland (TN)", "STG2", None, (2026, 12), None,
     "Retime Jan 2029 -> Dec 2026 (see CTG2).",
     "TVA release Jan 10, 2023; Industrial Info Nov 2025",
     "https://www.tva.com/news-media/releases/tva-retiring-cumberland-continues-transition-to-clean-energy-future",
     "Medium"),
    ("Cumberland (TN)", "CTG1", None, (2027, 12), None,
     "Retime Dec 2034 -> Dec 2027: second CC block follows the first "
     "(see CTG2); year is a placeholder within the construction window.",
     "TVA release Jan 10, 2023; Industrial Info Nov 2025",
     "https://www.tva.com/news-media/releases/tva-retiring-cumberland-continues-transition-to-clean-energy-future",
     "Medium"),
    ("Cumberland (TN)", "STG1", None, (2027, 12), None,
     "Retime Dec 2034 -> Dec 2027 (see CTG1).",
     "TVA release Jan 10, 2023; Industrial Info Nov 2025",
     "https://www.tva.com/news-media/releases/tva-retiring-cumberland-continues-transition-to-clean-energy-future",
     "Medium"),
]

# NEW_ROWS: (plant_name, generator_id, plant_id, state, subregion,
#            balancing_authority, fuel, mw, year, month, type, status,
#            source_sheet, note, source, source_url, confidence)
NEW_ROWS = [
    # A. Georgia Power certified CCs (PSC Dec 19, 2025)
    ("Plant Bowen (Units 7-8 CC)", "7-8", None, "GA", "SERC-Central", "SOCO",
     "Natural Gas", 1482.0, 2029, 11, "addition", "manual addition (v2)",
     "Georgia PSC certification, Docket 56298",
     "ADD: Bowen Units 7-8 CC, 1,482 MW, COD Nov 1, 2029. Certified by "
     "the Georgia PSC on Dec 19, 2025 (2029-2031 All-Source RFP). Not in "
     "the EIA Planned sheet. Grid-connected utility plant.",
     GA_PSC, GA_PSC_URL, "High"),
    ("Plant Wansley (Units 10-11 CC)", "10-11", None, "GA", "SERC-Central",
     "SOCO", "Natural Gas", 1453.0, 2029, 11, "addition",
     "manual addition (v2)", "Georgia PSC certification, Docket 56298",
     "ADD: Wansley Units 10-11 CC, 1,453 MW, COD Nov 1, 2029 (see Bowen). "
     "Site is the retired Wansley coal plant, rebuilt as gas.",
     GA_PSC, GA_PSC_URL, "High"),
    ("McIntosh Combined Cycle (Unit 12)", "12", None, "GA", "SERC-Central",
     "SOCO", "Natural Gas", 757.0, 2030, 11, "addition",
     "manual addition (v2)", "Georgia PSC certification, Docket 56298",
     "ADD: McIntosh Unit 12 CC, 757 MW, COD Nov 1, 2030 (see Bowen).",
     GA_PSC, GA_PSC_URL, "High"),
    # C. Duke Person County CCs (Roxboro)
    ("Person County Energy Complex (Roxboro CC1)", "CC1", None, "NC",
     "SERC-Central", "CPLE", "Natural Gas", 1360.0, 2029, 12, "addition",
     "manual addition (v2)", "Duke 2026 Carolinas Resource Plan, App. I",
     "ADD: Person County CC1, 1,360 MW at the Roxboro site, in service "
     "2029, replacing coal Units 1 & 4. Under construction; SC PSC "
     "certificates for CC1/CC2 approved Jul 23, 2026 (Order 2026-414). "
     "Absent from EIA entirely (no Roxboro rows in the v1 plants file).",
     "Duke 2026 Carolinas Resource Plan App. I; Global Energy Monitor",
     DUKE_CRP_URL, "Medium-High"),
    ("Person County Energy Complex (Roxboro CC2)", "CC2", None, "NC",
     "SERC-Central", "CPLE", "Natural Gas", 1360.0, 2030, 3, "addition",
     "manual addition (v2)", "Duke 2026 Carolinas Resource Plan, App. I",
     "ADD: Person County CC2, 1,360 MW, targeting in-service Q4 2029 / "
     "Q1 2030 (Mar 2030 booked). Coal Units 2 & 3 keep operating after "
     "CC2 per the 2026 CRP — no retirement booked for them.",
     "Duke 2026 Carolinas Resource Plan App. I; Global Energy Monitor",
     DUKE_CRP_URL, "Medium"),
    # D. Roxboro coal retirements (EIA nameplate MW)
    ("Roxboro", "1", None, "NC", "SERC-Central", "CPLE", "Coal",
     410.8, 2029, 12, "retirement", "manual addition (v2)",
     "Duke 2026 Carolinas Resource Plan",
     "ADD retirement: Roxboro Unit 1 (EIA nameplate 410.8 MW) retires "
     "when Person County CC1 enters service in 2029. EIA shows no "
     "planned retirement for any Roxboro unit.",
     "Duke 2026 Carolinas Resource Plan; Global Energy Monitor",
     "https://Www.gem.wiki/Roxboro_Steam_Plant", "Medium"),
    ("Roxboro", "4", None, "NC", "SERC-Central", "CPLE", "Coal",
     745.2, 2029, 12, "retirement", "manual addition (v2)",
     "Duke 2026 Carolinas Resource Plan",
     "ADD retirement: Roxboro Unit 4 (EIA nameplate 745.2 MW) retires "
     "with CC1 in 2029 (see Unit 1).",
     "Duke 2026 Carolinas Resource Plan; Global Energy Monitor",
     "https://Www.gem.wiki/Roxboro_Steam_Plant", "Medium"),
    # E. Marshall Advanced CTs
    ("Marshall (NC) (Advanced CTs)", "CT1", None, "NC", "SERC-Central",
     "DUK", "Natural Gas", 425.0, 2028, 12, "addition",
     "manual addition (v2)", "NCUC CPCN, Docket E-7 Sub 1297 (Dec 2, 2024)",
     "ADD: Marshall Advanced Class CT 1 of 2, 425 MW (850 MW total). "
     "CPCN granted Dec 2, 2024; under construction for 2028; allows "
     "Marshall coal Units 1 & 2 to retire (already in v1). Not in EIA.",
     "Duke 2026 Carolinas Resource Plan App. I; Global Energy Monitor",
     DUKE_CRP_URL, "High"),
    ("Marshall (NC) (Advanced CTs)", "CT2", None, "NC", "SERC-Central",
     "DUK", "Natural Gas", 425.0, 2028, 12, "addition",
     "manual addition (v2)", "NCUC CPCN, Docket E-7 Sub 1297 (Dec 2, 2024)",
     "ADD: Marshall Advanced Class CT 2 of 2, 425 MW (see CT1).",
     "Duke 2026 Carolinas Resource Plan App. I; Global Energy Monitor",
     DUKE_CRP_URL, "High"),
    # G. Canadys Joint Resource
    ("Canadys Joint Resource", "CC", None, "SC", "SERC-Central", "SCEG",
     "Natural Gas", 2180.0, 2033, 6, "addition", "manual addition (v2)",
     "SC PSC CECPCN, Docket 2025-323-E (Order 2026-350, Jun 12, 2026)",
     "ADD: Canadys Joint Resource, 2,180 MW (three 1x1 advanced-class "
     "CC blocks), former Canadys coal site, Colleton Co. SC. DESC / "
     "Santee Cooper 50/50. Certificate granted Jun 12, 2026; target "
     "commercial operation mid-2033. Booked under SCEG (DESC is site "
     "owner/operator lineage); SERC-Central either way. Not in EIA.",
     "SC PSC Docket 2025-323-E application and hearing notice; "
     "Order 2026-350 reporting",
     "https://dms.psc.sc.gov/Attachments/Matter/6750f890-edec-4728-bde9-233a019937e4",
     "High"),
    # H. Wateree retirements (EIA nameplate 385.9 x2)
    ("Wateree", "1", None, "SC", "SERC-Central", "SCEG", "Coal",
     385.9, 2032, 12, "retirement", "manual addition (v2)",
     "DESC 2026 IRP (reference plan)",
     "ADD retirement: Wateree Unit 1 (EIA nameplate 385.9 MW), Dec 31, "
     "2032 per DESC's 2026 IRP reference plan (no-GHG-rules case). "
     "Contingent on replacement capacity (Canadys) being available; "
     "DESC's ELG notice backstops coal cessation by Dec 31, 2034.",
     "DESC 2026 IRP; DESC ELG cessation notice (Dec 29, 2025)",
     "https://dms.psc.sc.gov/Attachments/Matter/b0c1ad38-be0c-45a3-9ff9-7db304b41869",
     "Medium"),
    ("Wateree", "2", None, "SC", "SERC-Central", "SCEG", "Coal",
     385.9, 2032, 12, "retirement", "manual addition (v2)",
     "DESC 2026 IRP (reference plan)",
     "ADD retirement: Wateree Unit 2 (see Unit 1).",
     "DESC 2026 IRP; DESC ELG cessation notice (Dec 29, 2025)",
     "https://dms.psc.sc.gov/Attachments/Matter/b0c1ad38-be0c-45a3-9ff9-7db304b41869",
     "Medium"),
    # I. Williams retirement (EIA nameplate 659.7)
    ("Williams", "ST1", None, "SC", "SERC-Central", "SCEG", "Coal",
     659.7, 2034, 12, "retirement", "manual addition (v2)",
     "DESC 2026 IRP (reference plan)",
     "ADD retirement: Williams (EIA nameplate 659.7 MW), Dec 31, 2034 "
     "per DESC's 2026 IRP reference plan. Flag: an Oct 2026 EVA study "
     "of DESC's own IRP finds retaining Williams to 2046 cheaper under "
     "optimized timing — the date is a planning assumption, not a finding.",
     "DESC 2026 IRP; Energy Ventures Analysis study (Oct 2026)",
     "https://dms.psc.sc.gov/Attachments/Matter/b0c1ad38-be0c-45a3-9ff9-7db304b41869",
     "Medium"),
    # O. Kingston BESS
    ("Kingston (BESS)", "BESS", None, "TN", "SERC-Central", "TVA",
     "Battery Storage", 100.0, 2027, 12, "addition",
     "manual addition (v2)", "TVA Kingston ROD (Apr 2024) / SEIS (Feb 2026)",
     "ADD: Kingston 100 MW BESS, part of the approved Kingston "
     "replacement package (CC + aero CTs are in v1; the BESS is not).",
     "TVA Kingston FEIS/ROD; TVA SEIS page",
     "https://www.tva.com/environment/environmental-stewardship/environmental-reviews/nepa-detail/kingston-fossil-plant-retirement",
     "Medium"),
    # P. Gaston Unit 5 fuel switch
    ("E C Gaston", "5", None, "AL", "SERC-Central", "SOCO", "Coal",
     952.0, 2028, 12, "retirement", "manual addition (v2)",
     "Alabama Power ELG NOPP annual progress report (Oct 12, 2026)",
     "ADD coal retirement (fuel switch): Gaston Unit 5 (EIA nameplate "
     "952.0 MW) permanently ceases coal combustion Dec 31, 2028 and "
     "operates solely on gas; conversion work under way. EIA shows no "
     "planned retirement/conversion for the unit.",
     "Alabama Power NOPP Annual Progress Report 2026; Global Energy Monitor",
     "https://www.alabamapower.com/content/dam/alabama-power/pdfs-docs/company/compliance---regulation/elg/plant-gaston-nopp-annual-progress-report-2026.pdf",
     "High"),
    ("E C Gaston (gas conversion)", "5", None, "AL", "SERC-Central", "SOCO",
     "Natural Gas", 952.0, 2028, 12, "addition", "manual addition (v2)",
     "Alabama Power ELG NOPP annual progress report (Oct 12, 2026)",
     "ADD gas (fuel switch): Gaston Unit 5 on gas from Dec 31, 2028 "
     "(see coal row).",
     "Alabama Power NOPP Annual Progress Report 2026; Global Energy Monitor",
     "https://www.alabamapower.com/content/dam/alabama-power/pdfs-docs/company/compliance---regulation/elg/plant-gaston-nopp-annual-progress-report-2026.pdf",
     "High"),
    # Q. Barry Unit 5 fuel switch
    ("Barry", "5", None, "AL", "SERC-Central", "SOCO", "Coal",
     788.8, 2028, 12, "retirement", "manual addition (v2)",
     "Alabama Power 2025 IRP summary report",
     "ADD coal retirement (fuel switch): Barry Unit 5 (EIA nameplate "
     "788.8 MW) ceases coal combustion by Dec 31, 2028 per Alabama "
     "Power's 2025 IRP (Barry Unit 4 already converted to gas). Booked "
     "as a conversion on the Gaston pattern; outright retirement is "
     "the alternative reading — flagged in the log.",
     "Alabama Power 2025 IRP summary report",
     "https://external.alabamapower.com/content/dam/alabama-power/pdfs-docs/company/compliance---regulation/2025-irp.pdf",
     "Medium"),
    ("Barry (gas conversion)", "5", None, "AL", "SERC-Central", "SOCO",
     "Natural Gas", 788.8, 2028, 12, "addition", "manual addition (v2)",
     "Alabama Power 2025 IRP summary report",
     "ADD gas (fuel switch): Barry Unit 5 on gas from Dec 2028 "
     "(see coal row).",
     "Alabama Power 2025 IRP summary report",
     "https://external.alabamapower.com/content/dam/alabama-power/pdfs-docs/company/compliance---regulation/2025-irp.pdf",
     "Medium"),
    # R. Brown Unit 12
    ("E W Brown (Unit 12 CC)", "12", None, "KY", "SERC-Central", "LGEE",
     "Natural Gas", 645.0, 2030, 12, "addition", "manual addition (v2)",
     "KY PSC Case 2025-00045 (CPCN approved Oct 2025)",
     "ADD: E.W. Brown Unit 12, 645 MW NGCC, CPCN approved by the "
     "Kentucky PSC in Oct 2025, in service by 2030. Not in EIA.",
     "KY PSC Case 2025-00045; Global Energy Monitor",
     "https://www.gem.wiki/E_W_Brown_Station", "High"),
    # S. LG&E/KU 2035 coal retirements (EIA nameplate MW)
    ("Mill Creek (KY)", "3", None, "KY", "SERC-Central", "LGEE", "Coal",
     462.6, 2035, 12, "retirement", "manual addition (v2)",
     "LG&E/KU 2024 IRP",
     "ADD retirement: Mill Creek Unit 3 (EIA nameplate 462.6 MW), 2035 "
     "per LG&E/KU's 2024 IRP. EIA shows no planned retirement for any "
     "LG&E/KU coal unit.",
     "LG&E/KU 2024 IRP via Global Energy Monitor",
     "https://www.gem.wiki/Mill_Creek_Station", "Medium"),
    ("Mill Creek (KY)", "4", None, "KY", "SERC-Central", "LGEE", "Coal",
     543.6, 2035, 12, "retirement", "manual addition (v2)",
     "LG&E/KU 2024 IRP",
     "ADD retirement: Mill Creek Unit 4 (EIA nameplate 543.6 MW), 2035 "
     "(see Unit 3).",
     "LG&E/KU 2024 IRP via Global Energy Monitor",
     "https://www.gem.wiki/Mill_Creek_Station", "Medium"),
    ("E W Brown", "3", None, "KY", "SERC-Central", "LGEE", "Coal",
     464.0, 2035, 12, "retirement", "manual addition (v2)",
     "LG&E/KU 2024 IRP",
     "ADD retirement: E.W. Brown Unit 3 (EIA nameplate 464.0 MW), 2035 "
     "per the 2024 IRP (the PSC denied its earlier 2027 retirement in "
     "Nov 2023; 2035 is the current plan).",
     "LG&E/KU 2024 IRP via Global Energy Monitor",
     "https://www.gem.wiki/E_W_Brown_Station", "Medium"),
    # T. Duke nuclear uprates (2026 CRP App. J: +251 MW at three stations)
    ("Brunswick (uprate)", "UPR", None, "NC", "SERC-Central", "CPLE",
     "Nuclear", 26.0, 2029, 12, "addition", "manual addition (v2)",
     "Duke 2026 Carolinas Resource Plan, App. J",
     "ADD (uprate): Brunswick measurement-uncertainty-recapture uprate, "
     "+26 MW by 2029. Part of Duke's +251 MW three-station uprate "
     "program in the 2026 CRP.",
     "Duke 2026 CRP App. J; NC legislative briefing (Feb 2026)",
     DUKE_CRP_URL, "Medium-High"),
    ("McGuire (uprate)", "UPR", None, "NC", "SERC-Central", "DUK",
     "Nuclear", 150.0, 2031, 12, "addition", "manual addition (v2)",
     "Duke 2026 Carolinas Resource Plan, App. J",
     "ADD (uprate): McGuire extended power uprates, +150 MW by 2031 "
     "(2 units x ~75 MW). McGuire+Catawba combined +225 MW is the "
     "published figure; the 150/75 split follows POWER Magazine's "
     "per-unit reporting (McGuire 1&2 + Catawba 1) — split assumed.",
     "Duke 2026 CRP App. J; POWER Magazine (May 2026)",
     "https://www.powermag.com/duke-energys-nuclear-playbook-three-horizons-one-strategy/",
     "Medium"),
    ("Catawba (uprate)", "UPR", None, "SC", "SERC-Central", "DUK",
     "Nuclear", 75.0, 2031, 12, "addition", "manual addition (v2)",
     "Duke 2026 Carolinas Resource Plan, App. J",
     "ADD (uprate): Catawba Unit 1 extended power uprate, +75 MW by "
     "2031 (see McGuire note on the assumed split).",
     "Duke 2026 CRP App. J; POWER Magazine (May 2026)",
     "https://www.powermag.com/duke-energys-nuclear-playbook-three-horizons-one-strategy/",
     "Medium"),
    # Y. GCEC 4/5 retirement (FPL TYSP subtraction)
    ("Gulf Clean Energy Center", "4-5", None, "FL", "Florida", "FPL",
     "Natural Gas", 150.0, 2029, 12, "retirement", "manual addition (v2)",
     "FPL Ten Year Site Plan 2026-2035, Table ES-1",
     "ADD retirement: GCEC Units 4 (75 MW) + 5 (75 MW), 2029 subtraction "
     "in FPL's 2026 TYSP. Booked at TYSP MW; EIA unit-level match not "
     "verified (legacy Gulf Power units).",
     "FPL TYSP 2026-2035, Table ES-1", FPL_TYSP_URL, "Medium"),
    # X. FPL CC uprates (TYSP)
    ("FPL combined-cycle upgrades", "2027", None, "FL", "Florida", "FPL",
     "Natural Gas", 43.0, 2027, 12, "addition", "manual addition (v2)",
     "FPL Ten Year Site Plan 2026-2035, Table ES-1",
     "ADD (uprate): +43 MW of CC upgrades in 2027 per FPL TYSP ES-1.",
     "FPL TYSP 2026-2035, Table ES-1", FPL_TYSP_URL, "Medium"),
    ("FPL combined-cycle upgrades", "2028", None, "FL", "Florida", "FPL",
     "Natural Gas", 19.0, 2028, 12, "addition", "manual addition (v2)",
     "FPL Ten Year Site Plan 2026-2035, Table ES-1",
     "ADD (uprate): +19 MW of CC upgrades in 2028 per FPL TYSP ES-1.",
     "FPL TYSP 2026-2035, Table ES-1", FPL_TYSP_URL, "Medium"),
]
# B. Georgia Power certified BESS tranches (PSC Dec 19, 2025; COD Nov 1).
_BESS = [
    ("Wadley BESS", "WAD", 260.0, 2027, "supplemental resource"),
    ("South Hall BESS", "SH", 250.0, 2028, "2029-2031 All-Source RFP"),
    ("Bowen BESS Phase I", "B1", 250.0, 2028, "2029-2031 All-Source RFP"),
    ("Wansley BESS", "WAN", 500.0, 2028, "2029-2031 All-Source RFP"),
    ("Yates BESS Phase I", "Y1", 320.0, 2028, "2029-2031 All-Source RFP"),
    ("Yates BESS Phase II", "Y2", 250.0, 2028, "2029-2031 All-Source RFP"),
    ("Bowen BESS Phase II", "B2", 250.0, 2029, "2029-2031 All-Source RFP"),
    ("Thomson BESS", "THO", 500.0, 2029, "2029-2031 All-Source RFP"),
    ("Hammond BESS Phase II", "H2", 193.0, 2030, "2029-2031 All-Source RFP"),
    ("McIntosh BESS", "MCI", 250.0, 2030, "2029-2031 All-Source RFP"),
]
for _pn, _gid, _mw, _yr, _prog in _BESS:
    NEW_ROWS.append(
        (_pn, _gid, None, "GA", "SERC-Central", "SOCO", "Battery Storage",
         _mw, _yr, 11, "addition", "manual addition (v2)",
         "Georgia PSC certification, Dockets 56298/56310",
         f"ADD: certified company-owned BESS ({_prog}), COD Nov 1, {_yr}. "
         "Part of the 9,885 MW portfolio certified Dec 19, 2025. None of "
         "the ten tranches appears in the EIA Planned sheet.",
         GA_PSC, GA_PSC_URL, "High"))
# U. FPL TYSP solar shortfall vs EIA (TYSP total 12,293 MW 2026-2035;
# EIA v1 has 894.0 in 2026, 968.5 in 2027, 75.0 in 2029, else 0).
_SOLAR_SHORT = [(2027, 223.5), (2028, 1788.0), (2029, 2309.0),
                (2030, 2980.0), (2034, 1490.0), (2035, 1564.5)]
for _yr, _mw in _SOLAR_SHORT:
    NEW_ROWS.append(
        ("FPL solar build (TYSP tranche)", f"S{_yr}", None, "FL", "Florida",
         "FPL", "Solar", _mw, _yr, 12, "addition", "manual addition (v2)",
         "FPL Ten Year Site Plan 2026-2035, Table ES-1",
         f"ADD: FPL TYSP solar for {_yr} minus the FPL solar already in "
         "v1 from EIA. TYSP plans 12,293 MW of nameplate solar "
         "2026-2035 in 74.5 MW blocks; EIA's Planned sheet captures the "
         "pace only through 2027 and stops. 2026-2029 tranches are "
         "covered by FPL's approved base-rate settlement; 2030+ are "
         "plan figures FPL states are not yet final decisions.",
         "FPL TYSP 2026-2035, Table ES-1; FPL Whitley testimony (2025)",
         FPL_TYSP_URL, "Medium-High" if _yr <= 2029 else "Medium"))
# V. FPL TYSP battery (EIA has zero FPL battery additions).
_BATT = [(2026, 1419.5), (2027, 819.5), (2028, 596.0), (2029, 596.0),
         (2030, 596.0), (2031, 1192.0), (2032, 596.0), (2033, 596.0),
         (2034, 223.5), (2035, 819.5)]
for _yr, _mw in _BATT:
    NEW_ROWS.append(
        ("FPL battery build (TYSP tranche)", f"B{_yr}", None, "FL",
         "Florida", "FPL", "Battery Storage", _mw, _yr, 12, "addition",
         "manual addition (v2)", "FPL Ten Year Site Plan 2026-2035, Table ES-1",
         f"ADD: FPL TYSP battery storage for {_yr} (7,454 MW total "
         "2026-2035). EIA's Planned sheet contains no FPL battery "
         "additions at all. 2026-2029 (3,431 MW) matches FPL's approved "
         "base-rate settlement; 2030-2035 (4,023 MW) is plan-only.",
         "FPL TYSP 2026-2035, Table ES-1", FPL_TYSP_URL,
         "Medium-High" if _yr <= 2029 else "Medium"))
# W. FPL TYSP unnamed CT tranches (fossil total ties: 672 Vandolah
# acquisition excluded + 936+936+936+468 CT = 3,948 MW TYSP fossil).
_CTS = [(2032, 936.0), (2033, 936.0), (2034, 936.0), (2035, 468.0)]
for _yr, _mw in _CTS:
    NEW_ROWS.append(
        ("FPL future CTs (TYSP tranche)", f"CT{_yr}", None, "FL", "Florida",
         "FPL", "Natural Gas", _mw, _yr, 12, "addition",
         "manual addition (v2)", "FPL Ten Year Site Plan 2026-2035, Table ES-1",
         f"ADD: unnamed future CT capacity in FPL's TYSP for {_yr} "
         "('4x0 CT' / '2x0 CT' placeholder blocks; sites not identified, "
         "FPL states later-year additions are not final decisions). The "
         "672 MW Vandolah acquisition in the same table is excluded — "
         "it is an ownership transfer of an existing plant, not new build.",
         "FPL TYSP 2026-2035, Table ES-1", FPL_TYSP_URL, "Low-Medium"))

# Expected yearly FLOW deltas (v2 net changelog - v1 net changelog), MW.
# Filled from the verified build; asserted in main().
EXPECTED_FLOW_DELTA = {
    2026: 2197.3, 2027: 4420.4, 2028: 6123.0, 2029: 5892.2, 2030: 8056.8,
    2031: 1417.0, 2032: 760.2, 2033: 5134.0, 2034: 414.2, 2035: 285.2,
    2036: 0.0,
}  # cumulative +34,700.3 MW; spot-checked by hand (see research_log.md)


def main():
    plants = pd.read_csv(BASE / "serc_capacity_plants.csv")
    stack_v1 = pd.read_csv(BASE / "serc_capacity_stack.csv")
    stackr_v1 = pd.read_csv(BASE / "serc_capacity_stack_by_subregion.csv")
    chg_v1 = pd.read_csv(BASE / "serc_capacity_changelog.csv")
    chgr_v1 = pd.read_csv(BASE / "serc_capacity_changelog_by_subregion.csv")
    with open(BASE / "summary.json") as f:
        s1 = json.load(f)

    # --- sanity check: v1 stack == anchor + cumulative v1 changelog
    anchor = stack_v1[stack_v1["year"] == ANCHOR_YEAR].set_index("fuel")["mw"].to_dict()
    anchor_r = {}
    for rg in SUBREGIONS:
        for fu in FUELS:
            anchor_r[(rg, fu)] = float(stackr_v1[
                (stackr_v1["year"] == ANCHOR_YEAR)
                & (stackr_v1["subregion"] == rg)
                & (stackr_v1["fuel"] == fu)]["mw"].iloc[0])
    running = {fu: float(anchor[fu]) for fu in FUELS}
    running_r = {(rg, fu): float(anchor_r[(rg, fu)])
                 for rg in SUBREGIONS for fu in FUELS}
    for y in range(2026, 2037):
        net = chg_v1[chg_v1["year"] == y]
        netr = chgr_v1[chgr_v1["year"] == y]
        for fu in FUELS:
            running[fu] += float(net.loc[net["fuel"] == fu, "net_mw"].iloc[0])
            for rg in SUBREGIONS:
                running_r[(rg, fu)] += float(netr.loc[
                    (netr["subregion"] == rg) & (netr["fuel"] == fu),
                    "net_mw"].iloc[0])
        v1row = stack_v1[stack_v1["year"] == y]
        for fu in FUELS:
            v = float(v1row.loc[v1row["fuel"] == fu, "mw"].iloc[0])
            assert abs(v - running[fu]) < 0.05, (y, fu, v, running[fu])
    print("v1 stack reproduces from anchor + v1 changelog: OK")

    # --- plants v2
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

    new_df = pd.DataFrame([{
        "plant_name": pn, "plant_id": pid, "generator_id": gid,
        "state": st, "county": "", "subregion": rg,
        "balancing_authority": ba, "fuel": fu,
        "energy_source_code": "", "prime_mover_code": "", "technology": "",
        "mw_nameplate": mw, "mw_net_summer": np.nan, "type": typ,
        "status": status, "retirement_status": "",
        "source_sheet": src, "original_year": yr, "original_month": mo,
        "original_date": f"{yr:04d}-{mo:02d}", "effective_year": yr,
        "effective_month": mo, "effective_date": f"{yr:04d}-{mo:02d}",
        "v2_mw_nameplate": mw, "v2_effective_date": f"{yr:04d}-{mo:02d}",
        "v2_status": status, "v2_type": typ, "manual_change": True,
        "manual_change_note": note,
    } for (pn, gid, pid, st, rg, ba, fu, mw, yr, mo, typ, status, src,
           note, _s, _u, _c) in NEW_ROWS])
    p2 = pd.concat([p2, new_df], ignore_index=True)
    print(f"  plants v2 rows: {len(p2)} (v1 {len(plants)} + {len(new_df)} new)")

    # --- changelog v2
    act = p2[p2["v2_type"].isin(["addition", "retirement"])].copy()
    act["v2_year"] = act["v2_effective_date"].str.slice(0, 4).astype(int)
    act = act[(act["v2_year"] >= 2026) & (act["v2_year"] <= 2036)]
    rows, rows_r = [], []
    for y in range(2026, 2037):
        for fu in FUELS:
            sub = act[(act["v2_year"] == y) & (act["fuel"] == fu)]
            adds = sub[sub["v2_type"] == "addition"]
            rets = sub[sub["v2_type"] == "retirement"]
            rows.append({
                "year": y, "fuel": fu,
                "additions_mw": round(float(adds["v2_mw_nameplate"].sum()), 1),
                "additions_count": int(len(adds)),
                "retirements_mw": round(float(rets["v2_mw_nameplate"].sum()), 1),
                "retirements_count": int(len(rets)),
                "net_mw": round(float(adds["v2_mw_nameplate"].sum()
                                - rets["v2_mw_nameplate"].sum()), 1),
            })
            for rg in SUBREGIONS:
                srg = sub[sub["subregion"] == rg]
                ar = srg[srg["v2_type"] == "addition"]
                rr = srg[srg["v2_type"] == "retirement"]
                rows_r.append({
                    "year": y, "subregion": rg, "fuel": fu,
                    "additions_mw": round(float(ar["v2_mw_nameplate"].sum()), 1),
                    "additions_count": int(len(ar)),
                    "retirements_mw": round(float(rr["v2_mw_nameplate"].sum()), 1),
                    "retirements_count": int(len(rr)),
                    "net_mw": round(float(ar["v2_mw_nameplate"].sum()
                                    - rr["v2_mw_nameplate"].sum()), 1),
                })
    chg2 = pd.DataFrame(rows)
    chg2r = pd.DataFrame(rows_r)

    flow_delta = {y: round(float(chg2[chg2["year"] == y]["net_mw"].sum()
                            - chg_v1[chg_v1["year"] == y]["net_mw"].sum()), 1)
                  for y in range(2026, 2037)}
    print(f"  yearly flow deltas (v2-v1): {flow_delta}")
    print(f"  cumulative flow delta: {sum(flow_delta.values()):+,.1f} MW")
    if EXPECTED_FLOW_DELTA is not None:
        for y in range(2026, 2037):
            assert abs(flow_delta[y] - EXPECTED_FLOW_DELTA[y]) < 0.05, (
                y, flow_delta[y], EXPECTED_FLOW_DELTA[y])
        print("  yearly flow deltas match EXPECTED_FLOW_DELTA: OK")

    # --- stack v2
    stack_rows, stackr_rows = [], []
    for y in range(2016, 2026):
        for _, r in stack_v1[stack_v1["year"] == y].iterrows():
            stack_rows.append({"year": int(r["year"]), "fuel": r["fuel"],
                               "mw": float(r["mw"]), "period": "trailing",
                               "anchor_year": bool(r["anchor_year"]),
                               "source_note": r["source_note"]})
        for _, r in stackr_v1[stackr_v1["year"] == y].iterrows():
            stackr_rows.append({"year": int(r["year"]),
                                "subregion": r["subregion"],
                                "fuel": r["fuel"], "mw": float(r["mw"]),
                                "period": "trailing",
                                "anchor_year": bool(r["anchor_year"]),
                                "source_note": r["source_note"]})
    note2 = ("EIA-860M Dec-31-2025 anchor + v2 changelog (EIA-860M + manual "
             "corrections: Georgia certified CC/BESS, Person County CCs, "
             "Marshall CTs, Canadys, FPL TYSP build, TVA coal reversals, "
             "coal retimes/fuel switches, nuclear uprates)")
    running = {fu: float(anchor[fu]) for fu in FUELS}
    running_r = {(rg, fu): float(anchor_r[(rg, fu)])
                 for rg in SUBREGIONS for fu in FUELS}
    for y in range(2026, 2037):
        net = chg2[chg2["year"] == y]
        netr = chg2r[chg2r["year"] == y]
        for fu in FUELS:
            running[fu] += float(net.loc[net["fuel"] == fu, "net_mw"].iloc[0])
            for rg in SUBREGIONS:
                running_r[(rg, fu)] += float(netr.loc[
                    (netr["subregion"] == rg) & (netr["fuel"] == fu),
                    "net_mw"].iloc[0])
        for fu in FUELS + ["Total"]:
            v = round(sum(running.values()), 1) if fu == "Total" else round(running[fu], 1)
            stack_rows.append({"year": y, "fuel": fu, "mw": v,
                               "period": "forward", "anchor_year": False,
                               "source_note": note2})
        for rg in SUBREGIONS:
            for fu in FUELS + ["Total"]:
                v = round(sum(running_r[(rg, ff)] for ff in FUELS), 1) \
                    if fu == "Total" else round(running_r[(rg, fu)], 1)
                stackr_rows.append({"year": y, "subregion": rg, "fuel": fu,
                                    "mw": v, "period": "forward",
                                    "anchor_year": False, "source_note": note2})
    stack2 = pd.DataFrame(stack_rows)
    stack2r = pd.DataFrame(stackr_rows)
    for y in range(2016, 2037):
        for fu in FUELS + ["Total"]:
            s = round(sum(float(stack2r[
                (stack2r["year"] == y) & (stack2r["subregion"] == rg)
                & (stack2r["fuel"] == fu)]["mw"].iloc[0]) for rg in SUBREGIONS), 1)
            t = float(stack2[(stack2["year"] == y)
                             & (stack2["fuel"] == fu)]["mw"].iloc[0])
            assert abs(s - t) < 0.1, (y, fu, s, t)
    print("  subregional stacks sum to SERC total (all years/fuels): OK")

    tot2 = stack2[stack2["fuel"] == "Total"].set_index("year")["mw"].round(1).to_dict()
    tot1 = stack_v1[stack_v1["fuel"] == "Total"].set_index("year")["mw"].round(1).to_dict()
    print("  yearly totals v1 -> v2:")
    for y in range(2025, 2037):
        print(f"    {y}: {tot1[y]:,.1f} -> {tot2[y]:,.1f}  ({tot2[y]-tot1[y]:+,.1f})")

    # --- manual_adjustments.csv
    adj_rows = []
    for (name, gen, new_mw, new_eff, _ns, note, src, url, conf) in EDITS:
        orig = plants[(plants["plant_name"] == name)
                      & (plants["generator_id"].astype(str) == str(gen))].iloc[0]
        adj_rows.append({
            "plant": name, "unit": str(gen), "state": orig["state"],
            "region": orig["subregion"], "fuel": orig["fuel"],
            "v1_mw": float(orig["mw_nameplate"]),
            "v1_date": orig["effective_date"],
            "v2_mw": float(new_mw) if new_mw is not None
                     else float(orig["mw_nameplate"]),
            "v2_date": f"{new_eff[0]:04d}-{new_eff[1]:02d}" if new_eff
                       else orig["effective_date"],
            "change_type": "retime", "reason": note,
            "classification": "manual correction",
            "source": src, "source_url": url, "confidence": conf,
            "source_date": ACC, "date_accessed": ACC,
        })
    for (pn, gid, _pid, st, rg, _ba, fu, mw, yr, mo, typ, _status, _ss,
         note, s, u, c) in NEW_ROWS:
        if typ == "addition":
            ct = ("add (fuel switch)" if "gas conversion" in pn else "add")
        else:
            ct = ("add retirement (fuel switch)"
                  if pn in ("E C Gaston", "Barry") else "add retirement")
        adj_rows.append({
            "plant": pn, "unit": str(gid), "state": st, "region": rg,
            "fuel": fu, "v1_mw": "", "v1_date": "",
            "v2_mw": float(mw), "v2_date": f"{yr:04d}-{mo:02d}",
            "change_type": ct, "reason": note,
            "classification": "manual correction",
            "source": s, "source_url": u, "confidence": c,
            "source_date": ACC, "date_accessed": ACC,
        })
    adj = pd.DataFrame(adj_rows)
    adj.to_csv(BASE / "manual_adjustments.csv", index=False)
    p2.to_csv(BASE / "serc_capacity_plants_v2.csv", index=False)
    stack2.to_csv(BASE / "serc_capacity_stack_v2.csv", index=False)
    stack2r.to_csv(BASE / "serc_capacity_stack_by_subregion_v2.csv", index=False)
    chg2.to_csv(BASE / "serc_capacity_changelog_v2.csv", index=False)
    chg2r.to_csv(BASE / "serc_capacity_changelog_by_subregion_v2.csv",
                 index=False)

    def agg(df, col):
        return {fu: round(float(df[df["fuel"] == fu][col].sum()), 1)
                for fu in FUELS}
    v1_add = agg(chg_v1, "additions_mw"); v2_add = agg(chg2, "additions_mw")
    v1_ret = agg(chg_v1, "retirements_mw"); v2_ret = agg(chg2, "retirements_mw")
    tot2r = {rg: {str(y): round(float(stack2r[
        (stack2r["year"] == y) & (stack2r["subregion"] == rg)
        & (stack2r["fuel"] == "Total")]["mw"].iloc[0]), 1)
        for y in range(2016, 2037)} for rg in SUBREGIONS}
    summary = {
        "version": "v2",
        "built": "2026-11-15",
        "anchor_unchanged_mw": s1["anchor"]["total_mw"],
        "anchor_by_subregion_mw": s1["anchor"]["by_subregion_mw"],
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
            "by_fuel_net_mw": {fu: round(v2_add[fu] - v2_ret[fu]
                                       - (v1_add[fu] - v1_ret[fu]), 1)
                               for fu in FUELS},
        },
        "yearly_flow_delta_mw": {str(k): v for k, v in flow_delta.items()},
        "yearly_totals_mw": {"v1": {str(k): v for k, v in tot1.items()},
                             "v2": {str(k): v for k, v in tot2.items()}},
        "yearly_totals_by_subregion_mw_v2": tot2r,
        "manual_adjustments_count": len(adj_rows),
        "named_adjustments_count": 25,
        "largest_manual_changes_mw": [
            {"plant": "FPL TYSP solar shortfall tranches", "change": "add", "mw": 10355.0},
            {"plant": "FPL TYSP battery tranches", "change": "add", "mw": 7454.0},
            {"plant": "Georgia Power certified CCs (Bowen/Wansley/McIntosh)", "change": "add", "mw": 3692.0},
            {"plant": "FPL TYSP unnamed CT tranches", "change": "add", "mw": 3276.0},
            {"plant": "Georgia Power certified BESS tranches", "change": "add", "mw": 3023.0},
            {"plant": "Person County CC1+CC2 (Roxboro)", "change": "add", "mw": 2720.0},
            {"plant": "Canadys Joint Resource CC", "change": "add", "mw": 2180.0},
            {"plant": "TVA Kingston coal retime out of window", "change": "retime", "mw": 1700.0},
            {"plant": "TVA Cumberland coal retime out of window", "change": "retime", "mw": 2600.0},
            {"plant": "Winyah retime 2030->2034", "change": "retime", "mw": 1275.8},
            {"plant": "Roxboro coal Units 1+4 retirement", "change": "add retirement", "mw": 1156.0},
            {"plant": "Victor J. Daniel Jr retime 2027->2035", "change": "retime", "mw": 1096.6},
            {"plant": "Gaston Unit 5 fuel switch", "change": "fuel switch", "mw": 952.0},
            {"plant": "Marshall Advanced CTs", "change": "add", "mw": 850.0},
            {"plant": "Barry Unit 5 fuel switch", "change": "fuel switch", "mw": 788.8},
            {"plant": "Wateree coal retirement", "change": "add retirement", "mw": 771.8},
            {"plant": "Williams coal retirement", "change": "add retirement", "mw": 659.7},
            {"plant": "E.W. Brown Unit 12 CC", "change": "add", "mw": 645.0},
            {"plant": "LG&E/KU 2035 coal retirements (MC3/MC4/Brown 3)", "change": "add retirement", "mw": 1470.2},
            {"plant": "Duke nuclear uprates", "change": "add", "mw": 251.0},
        ],
        "not_added_flagged_candidates_mw": {
            "Cross Generating Station coal (Santee Cooper retirement study in 2026 IRP; no date set)": 2451.5,
            "V.C. Summer Units 2&3 completion (Santee Cooper exploring sale/completion; no commitment)": 2234.0,
            "Georgia Power certified PPA portfolio (2,821 MW; counterparties unspecified, likely overlaps EIA IPP rows)": 2821.0,
            "Georgia Power certified solar+BESS COPs (Laurens 200 + Mitchell 150; solar/storage split unpublished)": 350.0,
            "Mill Creek Unit 2 coal (retirement approved for 2027 but LG&E/KU sought life extension to Mill Creek 6 in-service, Case 2025-00045; two-sided)": 355.5,
            "Mill Creek Unit 6 NGCC (in KY PSC Case 2025-00045; MW/date not verified)": None,
            "Cliffside (Rogers) Unit 5 (EIA codes the dual-fuel unit as gas, 621.0 MW; 2023 IRP pointed to retirement by 2031 but the 2026 CRP Appendix F date was not verified)": 621.0,
            "xAI Southaven MS behind-the-meter gas plant (41 turbines, ~1,200 MW permitted Mar 2026; BTM = 0 MW grid under the standing rule; excluded, not a candidate for addition)": 1200.0,
            "FPL Vandolah acquisition (672 MW in TYSP fossil additions; ownership transfer of an existing plant, not new build)": 672.0,
            "Duke new nuclear (Lee LLWR 1,117 MW or Belews Creek SMRs; IRP shows first new nuclear in 2037, outside window)": 1117.0,
        },
        "behind_the_meter_finding": (
            "One large explicitly behind-the-meter gas build found: xAI/"
            "SpaceX Southaven, MS (41 turbines, ~1,200 MW, MDEQ permit "
            "Mar 2026) self-supplying the Memphis Colossus campus, plus "
            "~198 MW of permitted turbines at Colossus 1 in Memphis "
            "alongside 150 MW of MLGW/TVA grid supply. None of it is in "
            "EIA; under the standing rule it is 0 MW of grid addition and "
            "no v2 row is added. All utility builds added in v2 (Georgia "
            "Power certified fleet, Person County, Marshall CTs, Canadys, "
            "FPL TYSP) are grid-connected system resources counted in full."),
        "files": {
            "manual_adjustments": "manual_adjustments.csv",
            "plants_v2": "serc_capacity_plants_v2.csv",
            "stack_v2": "serc_capacity_stack_v2.csv",
            "stack_by_subregion_v2": "serc_capacity_stack_by_subregion_v2.csv",
            "changelog_v2": "serc_capacity_changelog_v2.csv",
            "changelog_by_subregion_v2": "serc_capacity_changelog_by_subregion_v2.csv",
            "summary_v2": "summary_v2.json",
            "research_log": "research_log.md",
            "readme_v2": "README_v2.md",
            "charts": ["01_stacked_area_v2.png", "02_net_change_forward_v2.png",
                       "03_subregions_stacked_v2.png", "04_subregional_totals_v2.png"],
        },
    }
    with open(BASE / "summary_v2.json", "w") as f:
        json.dump(summary, f, indent=2)
    print("  wrote manual_adjustments.csv, plants/changelog/stack v2 CSVs, "
          "summary_v2.json")

    wide = stack2.pivot(index="year", columns="fuel", values="mw").reset_index()
    wide_r = stack2r.pivot_table(index="year", columns=["subregion", "fuel"],
                                 values="mw").reset_index()
    return wide, wide_r, chg2


def make_charts(wide, wide_r, chg2):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    years = wide["year"].values
    fig, ax = plt.subplots(figsize=(12, 6.5))
    bottom = np.zeros(len(years))
    for fu in STACK_ORDER:
        vals = wide[fu].values / 1000.0
        ax.fill_between(years, bottom, bottom + vals,
                        label=fu, color=FUEL_COLORS[fu], alpha=0.9)
        bottom += vals
    ax.axvline(2025.9, color="black", linestyle="--", linewidth=1.5)
    ax.text(2025.95, bottom.max() * 0.97, "Today (Nov 2026)\nanchor Dec 31, 2025",
            fontsize=9, va="top")
    ax.set_xlim(2016, 2036)
    ax.set_ylabel("Installed capacity (GW)")
    ax.set_xlabel("Year (Dec 31 position; 2026-2036 = anchor + v2 changelog)")
    ax.set_title("SERC generation capacity stack by fuel, 2016-2036 — v2\n"
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
    for fu in STACK_ORDER:
        v = piv[fu].values
        pos = np.where(v > 0, v, 0)
        neg = np.where(v < 0, v, 0)
        ax.bar(piv.index, pos, bottom=top, label=fu, color=FUEL_COLORS[fu], width=0.75)
        top += pos
        ax.bar(piv.index, neg, bottom=bottom, color=FUEL_COLORS[fu], width=0.75)
        bottom += neg
    ax.axhline(0, color="black", linewidth=0.8)
    pos_tot = float(piv.clip(lower=0).sum(axis=1).max())
    neg_tot = float(piv.clip(upper=0).sum(axis=1).min())
    ax.set_ylim(neg_tot * 1.12 - 0.2, pos_tot * 1.08 + 0.3)
    ax.set_ylabel("Net capacity change (GW / year)")
    ax.set_xlabel("Year")
    ax.set_title("SERC annual net capacity change by fuel, forward 2026-2036 — v2\n"
                 "(EIA-860M + manual additions/retirements, nameplate)", fontsize=11)
    ax.legend(ncol=2, fontsize=9, loc="upper right")
    ax.grid(True, alpha=0.3, axis="y")
    fig.tight_layout()
    fig.savefig(BASE / "02_net_change_forward_v2.png", dpi=150)
    plt.close(fig)

    fig, axes = plt.subplots(2, 1, figsize=(12, 10), sharex=True)
    for ax, rg in zip(axes, SUBREGIONS):
        bottom = np.zeros(len(years))
        for fu in STACK_ORDER:
            vals = wide_r[(rg, fu)].values / 1000.0
            ax.fill_between(years, bottom, bottom + vals,
                            label=fu, color=FUEL_COLORS[fu], alpha=0.9)
            bottom += vals
        ax.axvline(2025.9, color="black", linestyle="--", linewidth=1.2)
        ax.set_ylabel("GW")
        ax.set_title(f"SERC {rg} — capacity stack by fuel, 2016-2036 (GW) — v2",
                     fontsize=11)
        ax.grid(True, alpha=0.3)
        ax.legend(ncol=5, fontsize=8, loc="upper left")
    axes[-1].set_xlabel("Year (Dec 31 position)")
    fig.tight_layout()
    fig.savefig(BASE / "03_subregions_stacked_v2.png", dpi=150)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(12, 6))
    for rg in SUBREGIONS:
        ax.plot(years, wide_r[(rg, "Total")].values / 1000.0,
                label=rg, color=SUBREGION_COLORS[rg], linewidth=2)
    ax.plot(years, wide["Total"].values / 1000.0,
            label="SERC total", color="black", linewidth=2, linestyle="--")
    ax.axvline(2025.9, color="black", linestyle="--", linewidth=1.2)
    ax.set_ylabel("Installed capacity (GW)")
    ax.set_xlabel("Year (Dec 31 position)")
    ax.set_title("SERC capacity by subregion, 2016-2036 — v2", fontsize=11)
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(BASE / "04_subregional_totals_v2.png", dpi=150)
    plt.close(fig)
    print("  charts written")


if __name__ == "__main__":
    w, wr, c2 = main()
    make_charts(w, wr, c2)
