# MISO capacity stack — v1 (EIA-only, regionalized)

Replicates the PJM new-builds-and-retirements (NBR) stack for MISO, with
regionalization. Built 2026-11-14. Mirrors the PJM conventions:
trailing + forward 10-year stack 2016–2036 by fuel (Coal, Natural Gas,
Nuclear, Hydro, Pumped Storage, Wind, Solar, Oil, Battery Storage,
Other), nameplate MW throughout, anchor Dec 31, 2025, forward = anchor +
changelog. See `build_stack.py`; reproduce with `python3 build_stack.py`
(it asserts the reproduction and the regional-sum identity on every run).

## Headline figures (v1)

| | 2025 anchor | 2036 | Change 2026–2036 |
|---|---|---|---|
| MISO total | 211,974.9 MW | 241,535.8 MW | +29,560.9 MW |
| North | 54,283.9 MW | 55,095.5 MW | +811.6 MW |
| Central | 100,472.4 MW | 111,409.3 MW | +10,936.9 MW |
| South | 57,218.6 MW | 75,031.0 MW | +17,812.4 MW |

Forward 2026–2036 (EIA-860M only): additions **52,546.5 MW** (437 units),
retirements **22,985.6 MW** (107 units), net **+29,560.9 MW**.
Additions by fuel: Solar 23,182.8; Natural Gas 22,103.2; Battery 4,310.2;
Wind 2,836.9; Hydro 89.2; Oil 22.6; Other 1.6; Coal/Nuclear/Pumped 0.
Retirements by fuel: Coal 14,758.5 (64% of MW); Gas 7,742.3; Oil 170.3;
Hydro 150.7; Other 83.8; Wind 80.0; Nuclear/Solar/Battery/Pumped 0.
Peak build years: 2028 (+8,244.2 MW net), 2027 (+7,911.4), 2030 (+5,475.7).
The stack peaks in 2031 (244,595.9 MW) and declines thereafter as coal
retirements (Monroe 2028/2032, Nine Mile Point gas 2031/2033, Gerald
Andrus 2035) outweigh the thin late pipeline — no additions at all are
in EIA for 2035–2036 beyond the 2034 MEC units.

Anchor by fuel (Dec 31, 2025, nameplate): Gas 82,900.6; Coal 46,003.6;
Wind 33,237.1; Solar 20,812.1; Nuclear 13,080.8; Other 5,653.7;
Oil 4,587.9; Hydro 2,478.4; Pumped Storage 2,416.8; Battery 803.9.

Regional character at the anchor: North is wind-heavy (Wind 23,000.8 of
54,283.9; Coal 10,646.0; Gas 11,690.6). Central is the largest region
(Gas 34,935.5; Coal 28,588.1; Solar 13,181.6; Wind 9,907.8; Nuclear
5,688.9; Pumped Storage 2,386.8 — nearly all MISO pumped storage is in
Central). South is gas-heavy (Gas 36,274.5 of 57,218.6; Nuclear 5,520.7;
Coal 6,769.5; Wind only 328.5).

## Anchor — the important caveat

**No exact published MISO ICAP-by-fuel MW table exists.** Potomac
Economics' *2025 State of the Market Report* (June 2026) publishes exact
MW by fuel only in UCAP (Table 1, p. 5 — wind UCAP 8,236 MW, solar 6,228
MW; useless as an installed-capacity anchor) and ICAP only as shares
(Figure 34, p. 73). MISO's Fact Sheet (Jan 2026) gives a 207 GW total
with whole-percent shares, inconsistent with the SOM's own wind/solar
nameplate figures. So, per the task brief's explicit fallback, the anchor
is the **EIA-860M Operating-sheet snapshot, adjusted to Dec 31, 2025**
(minus units in service Jan–Sep 2026: 5,135.1 MW; plus Retired-sheet
actual retirements in 2026: 55.8 MW), nameplate MW, all statuses. It is
**EIA-derived, stated explicitly — not a MISO/IMM publication.**

Cross-checks (in `summary.json` under `anchor.cross_checks`):
- SOM-derived ICAP: ~180 GW (Figure 34 ICAP shares scaled to the SOM's
  own wind ~31.5 GW / solar ~18 GW nameplate anchors; a derivation, not
  a published table). EIA nameplate runs ~32 GW higher — expected:
  nameplate exceeds summer ICAP, especially for gas (EIA gas nameplate
  82.9 GW vs SOM ICAP ~71.1 GW) and solar (EIA 20.8 GW vs SOM ~17.8 GW),
  plus standby/out-of-service units in the EIA snapshot (4,672.6 MW
  non-OP, incl. 1,011.1 MW coal out-of-service) and scope differences
  (SOM Figure 34 covers PRA-participating resources; the Fact Sheet
  includes demand response, 9,698 MW per SOM Table 13, and a broader
  footprint). Do not mix the Fact Sheet 207 GW total with SOM shares.
- EIA Operating snapshot Sep 30, 2026 (unadjusted): 217,054.2 MW
  nameplate / 199,983.0 MW net summer; OP-only 212,381.6 / 195,915.6 MW.

## Trailing 2016–2025 — reconstructed, estimated

No published ICAP-by-fuel history exists, so the trailing is
**reconstructed from EIA unit-level data**: for year Y, Operating-sheet
units with Operating Year ≤ Y, plus Retired-sheet units with Operating
Year ≤ Y < Retirement Year. Planned Retirement Year is deliberately NOT
used (it reflects plans as of Sep 2026, not history). The reconstruction
**reproduces the anchor exactly at 2025** (asserted in the build), and
its shape is sane: 2016 193,444.3 → 2025 211,974.9 MW; the 2018 dip
(−2,459.3 MW) matches that year's 5,645.7 MW of retirements; the 2025
jump (+9,782.0 MW) is 10,242.4 MW entering service (Solar 7,224.1, Gas
1,273.9, Wind 1,082.2, Battery 662.2) against only 460.4 MW retired —
the 2025 solar build-out. Labelled estimated in every output row.

## Regionalization

MISO **North / Central / South subregions, LRZ-based**
(resource-adequacy/operations definition). North = LRZ 1+3; Central =
LRZ 2+4+5+6+7; South = LRZ 8+9+10. This is **NOT** the MTEP four-way
planning regions (West/Central/East/South); there is no "North" MTEP
planning region. Sources: MISO / Singularity Energy CarbonFlow Table 5
(LBA→LRZ→subregion); MISO Apr 2026 Long-Term Load Forecast White Paper
(per-LRZ state descriptors); MISO Phase III Clean Power Plan analysis
§4.3; MISO Tariff Attachment VV (LRZ boundary map); Module E-1 §68A.3.1
(two-way North/Central vs South split). Plants are assigned by state,
except Wisconsin, which is split by Local Balancing Authority (entity)
then county: western WI = North (LRZ 1), eastern/northern WI = Central
(LRZ 2). One plant-level override: RockGen Energy Center (3×187 MW gas,
Dane County, owned by Dairyland Power Coop, an LRZ-1 LBA) is assigned
Central — it sits in Alliant (ALTE) service territory around Cambridge,
WI (LRZ 2); LRZ follows the plant's location in the transmission
system, not its owner's LBA. Montana's 6 units (155.6 MW, all
Montana-Dakota Utilities) go to North (eastern MT sliver, LRZ 1).
Wisconsin assignment: entity LRZ-1 1,266.0 MW, entity LRZ-2 15,024.4 MW,
override 561.0 MW, county fallback 2,876.2 MW (396 units, mostly small
hydro/solar/IPP units; the largest fallback plant is Point Beach nuclear,
1,311.0 MW, NextEra, Manitowoc County → Central).
Every regional total is asserted to sum to the MISO total, every year
and fuel, in the build.

## Changelog (EIA-860M Sep 2026, BA=MISO)

Additions = in service Jan–Sep 2026 (89 units, 5,135.1 MW) + Planned
sheet (348 units, 47,411.4 MW, 2026–2034; 46,411.4 MW in 2026–2031 plus
two 500 MW MEC gas units in 2034). Only 16,066.4 MW of the planned
pipeline is under construction / construction-complete; 30,345.0 MW is
not yet under construction (P 16,706.6 + L 11,200.0 + T 2,438.4) — the
forward pipeline is mostly paper, which is what v2 corrects.
Retirements = actual 2026 (8 units, 55.8 MW, all tiny) + planned
2026–2036 (99 units, 22,929.8 MW). No RMR-style override: the PJM
coal-delay-to-Jan-2029 override was a user-directed scenario, not a
general rule. Overlap guards verified at 0 (no unit double-counted
between in-service-2026 and planned-2026, or retired-2026 and
planned-retirement-2026).
BA boundary: 318,323.9 MW sits in MISO-footprint states under other BAs
(ERCOT 183,431.3 MW in TX alone, PJM 55,339.2, SPP 35,672.1, TVA
12,069.9) — a state-based cut would be very wrong; BA=MISO is the
right filter. No BA=MISO plant sits outside the 15-state footprint.

Largest forward additions (v1, EIA): Vista Sands Solar WI 1,182.0 MW
(2028, L); Lincoln Land Energy Center IL 2×638.4 MW gas (2030, P);
Arkansas Cypress Solar AR 600.0 MW (2029, P); MEC North/South MI 500 MW
gas each (2034, L/T); Steel River Solar AR 3×500.0 MW (2028–2030, U);
Hecate Sunfish Solar MI 499.0 MW (2028, L); then a run of ~477–478 MW
gas CTs in the South (Jefferson AR, Waterford 5/6 LA, Traceview MS,
Westlake LA, Vicksburg MS, Delta Blues MS, Franklin Farms LA, Pointe
Coupee LA). Largest retirements: Sherburne County MN coal 938.7 MW
(2030) + 765.3 MW (2026); J H Campbell MI coal 916.8 MW (2026); Nine
Mile Point LA gas 895.1 MW each (2031, 2033); Monroe MI coal 4×~820 MW
(2028/2032); Gerald Andrus MS gas 781.4 MW (2035); Belle River MI coal
2×697.5 MW (2028); Baldwin IL coal 634.5 + 625.1 MW (2027); Newton IL
coal 617.4 MW (2027); Allen S King MN coal 598.4 MW (2028).
Note: the plants file also lists retirements beyond 2036 (e.g. Monticello
and Prairie Island nuclear licence expiries in 2050) — they are outside
the changelog window and do not affect the stack.

## Files

- `build_stack.py` — the build (asserts reproduction + regional sums).
- `miso_capacity_plants.csv` — unit-level forward changelog (437 additions
  + 107 retirements in-window; retirements beyond 2036 also listed).
- `miso_capacity_stack.csv` — MISO total stack, long format (year × fuel).
- `miso_capacity_stack_by_region.csv` — per-region stack (year × region × fuel).
- `miso_capacity_changelog.csv` — forward changelog (year × fuel).
- `miso_capacity_changelog_by_region.csv` — changelog by region.
- `summary.json` — anchor, cross-checks, trailing, forward totals,
  diagnostics, file list.
- `01_stacked_area.png`, `02_net_change_forward.png`,
  `03_regions_stacked.png`, `04_regional_totals.png` — charts.
- `raw/eia860m_sep2026.xlsx` — EIA-860M Sep 2026 vintage (same file as
  the PJM stack).
- `eia_explore_miso.txt`, `explore_miso.py` — EIA exploration output/script.

## What v1 is not (v2 scope)

EIA-only. Per the standing rule, EIA is fairly good for a snapshot of
what is currently online but NOT reliable for larger gas/power plants in
the forward pipeline — v2 manually corrects the largest forward plants
from online sources (same discipline as PJM v2: each adjustment with a
source, logged in `research_log.md`). Known v2 items: Cayuga Energy
Complex (Duke Energy Indiana, 2×~738 MW winter CC, Dec 2029/2030,
1,476 MW — removed from PJM v2 because it interconnects into MISO; NOT
in the EIA Planned sheet, so v2 must add it); verification of the big
gas CTs and solar projects above; coal-retirement dates (incl. any
DOE emergency-order / RMR extensions — the SOM notes ~1.6 GW of 2025
coal retirements were blocked by DOE emergency orders); and a scan for
large gas plants EIA misses entirely. v1 files are never overwritten
by v2.
