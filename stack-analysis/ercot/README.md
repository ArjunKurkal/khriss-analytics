# ERCOT capacity stack — v1 (EIA-only)

Replicates the PJM/MISO new-builds-and-retirements (NBR) stack for
ERCOT. Built 2026-11-15. Mirrors the PJM/MISO conventions: trailing +
forward 10-year stack 2016–2036 by fuel (Coal, Natural Gas, Nuclear,
Hydro, Pumped Storage, Wind, Solar, Oil, Battery Storage, Other),
nameplate MW throughout, anchor Dec 31, 2025, forward = anchor +
changelog. ERCOT is a single balancing authority, so there is no
regional split. See `build_stack.py`; reproduce with
`python3 build_stack.py` (it asserts the anchor reproduction and the
forward identity on every run).

## Headline figures (v1)

| | 2025 anchor | 2036 | Change 2026–2036 |
|---|---|---|---|
| ERCOT total | 174,266.5 MW | 270,437.2 MW | +96,170.7 MW |

Forward 2026–2036 (EIA-860M only): additions **97,654.2 MW** (631
units), retirements **1,483.5 MW** (7 units), net **+96,170.7 MW**.
Additions by fuel: Solar 39,947.6; Battery 29,444.1; Natural Gas
18,599.5; Wind 5,136.7; Nuclear 4,468.0; Other 38.5; Oil 19.8;
Coal/Hydro/Pumped 0. Retirements by fuel: Gas 905.6; Coal 566.0;
Battery 9.9; Oil 2.0 — ERCOT has almost no announced retirements in
EIA; the forward story is nearly all additions. The pipeline is
front-loaded: EIA carries no planned additions after 2032, so the
stack is flat 2033–2036 by construction, not by forecast.

Anchor by fuel (Dec 31, 2025, nameplate): Gas 68,756.5; Wind 40,247.8;
Solar 30,017.7; Coal 14,329.7; Battery 13,914.3; Nuclear 5,138.6;
Oil 874.1; Hydro 567.5; Other 420.3; Pumped Storage 0.

## Anchor — the important caveat

**The anchor is EIA-derived, stated explicitly — not an ERCOT
publication.** ERCOT publishes its own Capacity, Demand and Reserves
(CDR) report with installed capacity by fuel, but the CDR cannot serve
as a nameplate anchor: it uses **seasonal capacity ratings, not
nameplate**, counts wind/solar/storage at Effective Load Carrying
Capability (ELCC) shares in its reserve accounting, and treats
**switchable units** (3,678 MW, of which 2,184 MW unavailable to ERCOT
in summer 2026), **Private Use Networks** (3,431 MW) and **DC-tie
capacity** specially. The anchor here is the **EIA-860M Operating-sheet
snapshot, adjusted to Dec 31, 2025** (minus units in service Jan–Sep
2026: 10,534.8 MW; plus Retired-sheet actual retirements in 2026:
0.0 MW — the ERCO Retired sheet has no 2026 retirements), nameplate MW,
all statuses.

Cross-checks (in `summary.json` under `anchor.cross_checks`):
- ERCOT CDR, Dec 19, 2025: summer 2026 installed seasonal-rated
  thermal capacity excluding switchable units 65,431 MW; expected
  summer 2026 capacity ~104,850 MW on the CDR basis. The CDR total is
  far below the EIA nameplate anchor (174,266.5 MW) — expected: CDR
  thermal figures are seasonal ratings (EIA gas nameplate alone is
  68,756.5 MW at the anchor), and wind/solar/storage enter the CDR at
  ELCC contributions, not nameplate (EIA anchor nameplate: Wind
  40,247.8 + Solar 30,017.7 + Battery 13,914.3 = 84,179.8 MW).
- ERCOT Fact Sheet, Oct 2026 (operational installed, CDR basis): wind
  41,208 MW, utility solar 41,926 MW, storage 21,537 MW. Solar and
  storage run well above the EIA Operating snapshot because EIA files
  many just-completed units on the Planned sheet (TS status) until
  commercial operation is reported.
- EIA Operating snapshot Sep 30, 2026 (unadjusted): 184,801.3 MW
  nameplate / 175,770.0 MW net summer; OP-only 181,957.5 MW nameplate.
  Non-OP (standby/out-of-service) capacity in the snapshot is
  2,843.8 MW.

## Trailing 2016–2025 — reconstructed, estimated

**Reconstructed from EIA unit-level data**: for year Y, Operating-sheet
units with Operating Year ≤ Y, plus Retired-sheet units with Operating
Year ≤ Y < Retirement Year. Planned Retirement Year is deliberately NOT
used (it reflects plans as of Sep 2026, not history). The reconstruction
**reproduces the anchor exactly at 2025** (asserted in the build).
Shape: 2016 110,403.5 → 2025 174,266.5 MW; the 2018 dip (−1,437.1 MW)
matches that year's coal/gas retirements (4,430.2 MW retired in 2018,
incl. the Deely coal units); growth accelerates after 2020 on solar,
wind and battery additions. Labelled estimated in every output row.

## Region cut — BA = ERCO, not Texas

The cut is **Balancing Authority Code = ERCO** in EIA-860M. The ERCOT
footprint is **NOT all of Texas**: the Panhandle, El Paso, and parts of
East Texas sit in SPP/MISO/SERC/WECC, so a state-based cut would be
wrong. In the Operating sheet, 23,798.9 MW of Texas capacity sits under
other BAs (SWPP 13,708.0; MISO 7,663.2; EPE 1,927.7; DOPD 500.0) and is
correctly excluded. In the other direction, exactly one ERCO plant sits
outside Texas: **Kiamichi Energy Facility, OK (1,370.0 MW, Pittsburg
Co.)** — checked in v2 and confirmed genuinely ERCOT (transmission
owner Oncor, NERC region TRE); it is a location anomaly, not a BA-code
error. Two genuine BA-code errors were found in the Planned sheet and
are corrected in v2: Legend Power Station (coded ERCO, actually MISO)
and the Fermi Project Matador campus (coded ERCO; actually a
behind-the-meter private grid in SPP territory). See `README_v2.md`.

## Changelog (EIA-860M Sep 2026, BA=ERCO)

Additions = in service Jan–Sep 2026 (115 units, 10,534.8 MW — Battery
5,285.3; Solar 3,762.0; Gas 1,173.1; Wind 304.5; Oil 9.9) + Planned
sheet (516 units, 87,119.4 MW, 2026–2032). Only 28,076.0 MW of the
Planned pipeline is under construction / construction-complete (U
12,396.4 + V 6,765.7 + TS 8,913.9); 59,043.4 MW is not yet under
construction (P 37,477.0 + L 15,670.5 + T 5,895.9) — the forward
pipeline is mostly paper, which is what v2 corrects. Retirements =
actual 2026 (0 units, 0.0 MW) + planned 2026–2036 (7 units, 1,483.5 MW).
No blanket retirement-delay override is applied: the PJM
coal-delay-to-Jan-2029 override was a PJM-only user scenario.
Overlap guards verified at 0 (no unit double-counted between
in-service-2026 and planned-2026, or retired-2026 and
planned-retirement-2026).

GIS cross-check: ERCOT's Generator Interconnection Status report
tracks 1,874 active requests totalling 453,782 MW at Sep 30, 2026
(solar 155,123; battery 162,580; gas ~81,704; wind 49,746 MW) — the
queue is a superset of the EIA pipeline; most queued projects are
never built, and the EIA Planned sheet is the nearer-term, filtered
subset used here.

Largest forward additions (v1, EIA): Project Matador Nuclear, Carson
Co., 4×1,117.0 MW (2031/2032, P — excluded in v2, see below); Project
Matador Gas Plant, Carson Co., 157 units totalling 11,679.3 MW
(2027/2028/2030, P — excluded in v2); Legend Power Station 754.0 MW gas
(2028, L — excluded in v2 as a MISO plant); CPV Basin Ranch Energy
Center 2×722.5 MW gas (2029, U); Cedar Bayou 5 721.0 MW gas (2028, U);
IP Roman Wind 670.5 MW (2028, L); Sandow Lakes Energy Station 2×645.0 MW
gas (2028, P); then a run of 500–645 MW solar and battery projects.
Largest retirements (all of them, v1): O W Sommers Unit 1 gas 446.0 MW
(2027) and Unit 2 446.0 MW (2029); J K Spruce Unit 1 coal 566.0 MW
(2028); Hal C Weaver 13.6 MW (2028); Works 4 oil 2.0 MW (2029); Flower
Valley I battery 9.9 MW (2032). Note: the plants file also lists
retirements beyond 2036 (two 100 MW Hidalgo battery units in 2042) —
outside the changelog window.

## Files

- `build_stack.py` — the build (asserts anchor reproduction, zero
  overlap guards, and the forward identity).
- `ercot_capacity_plants.csv` — unit-level forward changelog (631
  additions + 9 retirements listed; 7 retirements in-window).
- `ercot_capacity_stack.csv` — ERCOT stack, long format (year × fuel).
- `ercot_capacity_changelog.csv` — forward changelog (year × fuel).
- `summary.json` — anchor, cross-checks, trailing, forward totals,
  diagnostics, file list.
- `01_stacked_area.png`, `02_net_change_forward.png` — charts.

## What v1 is not (v2 scope)

EIA-only. Per the standing rule, EIA is fairly good for a snapshot of
what is currently online but NOT reliable for larger gas/power plants
in the forward pipeline — v2 manually corrects the largest forward
plants from online sources (same discipline as PJM/MISO v2: each
adjustment with a source, logged in `research_log.md`). Known v2
items: the Legend BA-code error (754 MW that belongs to MISO); the
Fermi Project Matador campus (16,147.3 MW of gas + nuclear coded ERCO
that is a behind-the-meter private grid in SPP territory); the J K
Spruce Unit 2 coal-to-gas conversion and the Coleto Creek coal-to-gas
repower, neither of which EIA carries at all; Texas Energy Fund
projects EIA omits (e.g. Rayburn Energy Station II); and an explicit
scan for data-center co-located (behind-the-meter) gas. v1 files are
never overwritten by v2.
