# PJM generation capacity stack, 2016-2036 (trailing + forward)

PJM-level only (no regionalization). Built 2026-11-14 by `build_stack.py`
from free public data only.

## What this is

* **Trailing (2016-2025):** Dec-31 installed capacity by fuel, from the PJM
  State of the Market (Monitoring Analytics / Independent Market Monitor),
  Section 12, Table 12-1, parsed from the published PDFs.
* **Anchor (today):** Dec 31, 2025 SOM installed capacity: **202,424.8 MW**
  (38,366.4 MW coal, 89,767.5 MW gas, 33,452.6 MW nuclear).
  This is the base. Nothing replaces it.
* **Forward (2026-2036):** anchor + the EIA-860M changelog, year by year:
  additions (EIA-860M Planned sheet + units already in service in 2026)
  minus retirements (EIA-860M Retired-sheet actuals for 2026 + Operating-sheet
  planned retirements). 2026 stack total: **207,146.8 MW**;
  2036 stack total: **219,875.4 MW**.
* **Cross-check:** 2026 Q2 SOM (Jun 30, 2026) total installed capacity was
  202,384.2 MW vs the Dec-31-2025 anchor 202,424.8 MW
  (-40.6 MW). Coal fell -625.0 MW in H1 2026 in the
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
  https://www.monitoringanalytics.com/reports/pjm_state_of_the_market/{YYYY}/{YYYY}-som-pjm-sec12.pdf
  (2025 annual created Mar 12, 2026). 2026 Q2 Sec. 12:
  https://www.monitoringanalytics.com/reports/PJM_State_of_the_Market/2026/2026q2-som-pjm-sec12.pdf

## Capacity definition

SOM "installed capacity" = summer ICAP rating, except solar and wind which
are nameplate. EIA-860M changelog is in **nameplate MW**. Applying nameplate
changes to an ICAP anchor is an approximation: EIA does not publish ICAP.
Reconciliation (Sep-2026 EIA Operating, BA=PJM, vs Dec-2025 SOM anchor):

| Fuel | SOM anchor (MW) | EIA nameplate (MW) | EIA net summer (MW) |
|---|---:|---:|---:|
| Coal | 38,366.4 | 37,985.1 | 35,518.2 |
| Natural Gas | 89,767.5 | 106,470.6 | 96,746.4 |
| Nuclear | 33,452.6 | 35,447.4 | 33,491.8 |
| Hydro | 2,771.1 | 3,334.2 | 3,284.3 |
| Pumped Storage | 4,792.0 | 5,046.1 | 5,078.5 |
| Wind | 12,512.1 | 12,064.0 | 12,037.6 |
| Solar | 14,887.5 | 19,518.6 | 19,467.7 |
| Oil | 4,059.9 | 5,963.1 | 4,959.2 |
| Battery Storage | 436.6 | 685.9 | 683.6 |
| Other | 1,379.1 | 2,590.7 | 2,264.2 |
| **Total** | **202,424.8** | **229,105.7** | **213,531.5** |

EIA exceeds SOM by +13.2% on nameplate, +5.5% on
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
would be wrong: **153,211.3 MW** of nameplate in PJM footprint
states sits in other BAs (MISO, TVA, Duke, LG&E, ...), while only
**3.3 MW** of BA=PJM capacity sits outside the footprint states
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
**Jan 2029**. Affected: **5 units, 4,569.0 MW** —
2026: 0.0 MW / 0 units; 2027: 1,319.0 MW /
2 units (Kincaid 1 & 2, IL, 659.5 MW each, orig. Dec 2027);
2028: 3,250.0 MW / 3 units (Cardinal 3, OH, 650 MW;
Rockport 1 & 2, IN, 1,300 MW each, orig. Dec 2028). Because Jan 2029 is
after all of 2028 this is a **pure delay: 4,569.0 MW delayed,
0 MW pulled forward**. (An earlier instruction said Jan 2028; that was
corrected to Jan 2029 — a Jan 2028 date would have pulled the Dec-2028
retirements *forward*.) Original dates are preserved in
`pjm_capacity_plants.csv` (`rmr_override`, `original_retirement_date`,
`effective_retirement_date`); the changelog and stack use effective dates.
Already-retired units are not overridden. This is a scenario, not a
forecast — RMR designations are unit-specific.

## Forward pipeline (EIA-860M, BA=PJM, nameplate)

* Total planned additions 2026-2036: **29,818.3 MW** (493 units).
  By fuel: Solar 15,282 MW, Natural Gas 8,150 MW, Wind 5,131 MW, Battery Storage 985 MW, Hydro 267 MW, Other 3 MW
* By year: 2026: 6,286 MW, 2027: 8,338 MW, 2028: 7,658 MW, 2029: 6,403 MW, 2030: 1,119 MW, 2031: 15 MW, 2032: 0 MW, 2033: 0 MW, 2034: 0 MW, 2035: 0 MW, 2036: 0 MW
* By status: only **8,913.0 MW** under construction / construction
  complete; **11,196.6 MW** (status P) have not even begun regulatory
  approvals. Planned ≠ built; dates slip — e.g. Eddystone 3 & 4 (gas steam,
  391 MW each) were listed for Feb 2026 retirement in the Dec-2025 SOM and
  now show Nov 2026 in EIA-860M.
* Largest planned additions: Coastal Virginia Offshore Wind (CVOW) Commercial Project (VA, Wind, 2,640 MW, 2027-01, (U) Under construction, less than or equal to 50 percent complete); Steward Creek Solar Phase 1 (IL, Solar, 1,200 MW, 2029-12, (P) Planned for installation, but regulatory approvals not initiated); Sycamore Riverside Energy, LLC (IN, Natural Gas, 964 MW, 2029-03, (P) Planned for installation, but regulatory approvals not initiated); Illinois Generation LLC (IL, Wind, 616 MW, 2028-04, (T) Regulatory approvals received. Not under construction); Bellflower Solar (VA) (VA, Solar, 600 MW, 2030-01, (P) Planned for installation, but regulatory approvals not initiated)
* Largest planned retirements (effective dates): Rockport (IN, Coal, 1,300 MW, orig 2028-12 -> eff 2029-01); Rockport (IN, Coal, 1,300 MW, orig 2028-12 -> eff 2029-01); TalenEnergy Martins Creek (PA, Natural Gas, 850 MW, orig 2035-06 -> eff 2035-06); TalenEnergy Martins Creek (PA, Natural Gas, 850 MW, orig 2035-06 -> eff 2035-06); Brunner Island (PA, Natural Gas, 848 MW, orig 2035-06 -> eff 2035-06)
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
