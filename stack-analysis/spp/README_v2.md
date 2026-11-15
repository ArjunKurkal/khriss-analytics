# SPP capacity stack — v2 (EIA + manual corrections)

Built 2026-11-15 from v1 (see `README.md`) by applying 5 named
manual adjustments (10 row-level changes), each with an online
source, logged in `research_log.md` Part 2 and
`manual_adjustments.csv`. Reproduce with
`python3 build_stack_v2.py` (it verifies v1 reproduces, applies
the corrections, and asserts the corrected yearly flow deltas and
the East + West = Combined identity on every run). v1 files are
untouched.

## Headline figures (v2 vs v1)

| | v1 | v2 | Change |
|---|---|---|---|
| 2036 total | 131,128.0 MW | **133,216.0 MW** | **+2,088.0 MW** |
| Forward additions 2026–2036 | 23,664.7 MW (195 units) | 25,752.7 MW (197 units) | +2,088.0 MW |
| Forward retirements 2026–2036 | 9,476.0 MW (49 units) | 9,476.0 MW (49 units) | 0 (retimes only) |
| Forward net 2026–2036 | +14,188.7 MW | +16,276.7 MW | +2,088.0 MW |
| 2036 East | 116,035.3 MW | 118,123.3 MW | +2,088.0 MW |
| 2036 West | 15,092.7 MW | 15,092.7 MW | 0 |

The entire v2−v1 delta is **Natural Gas +2,088.0 MW** (the two SPS
plants EIA missed); the three retimes net to zero by 2036 but move
MW between 2028 and 2029. Year-by-year v2−v1 totals: 2028
+1,538.0; 2029–2036 +2,088.0. The v2 stack peaks in 2030 at
135,844.4 MW. **Natural Gas leads the v2 net change by fuel**
(net +11,249.8 MW 2026–2036: additions 14,260.0 − retirements
3,010.2), ahead of Solar (+7,078.3) and Wind (+1,549.6); Coal is
the largest decline (−6,426.8).

## What changed (5 adjustments)

| # | Plant | Change | MW | Confidence |
|---|---|---|---|---|
| A | Gaines County CTG, TX (East, gas) | ADD (Dec 2028) | +1,160.0 | Medium |
| B | Tolk Station CTG, TX (East, gas) | ADD (Apr 2029) | +928.0 | Medium |
| C | Craig (CO) Unit 3, CO (West, coal) | Retime Dec 2029 → Jan 2028 | 534.8 | Medium-High |
| D | Tolk Units 1/2, TX (East, coal) | Retime Dec 2028 → Mar 2029 | 1,135.8 | High |
| E | Rawhide new gas (5 units), CO (West, gas) | Retime Mar 2028 → Dec 2029 | 223.0 | Medium |

Notes and flags:
- **A and B are the ERAS-era SPS self-build plants** from Xcel/
  SPS's NMPRC Case 25-00066-UT, approved by the NMPRC (summer
  2026) and the PUCT (Oct 2026) — and **entirely absent from the
  EIA Planned sheet**. Their MW are the filing's *winter-max*
  figures (1,160 / 928), not EIA nameplates; GEM lists a larger
  1,325 MW Tolk gas unit. Treat the +2,088.0 MW as filing-basis,
  Medium confidence.
- **C** pulls Craig Unit 3's retirement two years earlier, to the
  Tri-State ERP schedule (Units 2 and 3 both retire in 2028) that
  DOE's own rehearing order restates. EIA's Unit 2 date already
  matched and is unchanged.
- **D** is a regulator-approved three-month delay (NMPRC,
  May 2026) — plant-specific evidence, not a blanket delay
  assumption. No other retirement was delayed in v2.
- **Craig Unit 1 was checked and KEPT at Dec 2026**: four
  successive DOE §202(c) orders (202-25-14 → 202-26-49) keep it
  available through Dec 25, 2026 with an orderly ramp-down after,
  which is what EIA's date reflects. A fifth order would move it
  into 2027.
- **No behind-the-meter exclusion was found** in either BAA: the
  large additions are grid-connected utility plants, and SPP's
  data-center load is grid-served. See `research_log.md`.
- Verified KEEPs include Bison (1,518.0 MW EIA nameplate vs
  Basin's 1,470 MW nominal, 2029/2030, under construction),
  Evergy Viola/McNew (KCC-approved), Horizon/Williams Creek
  (480.0 MW nameplate vs CSU's 400 MW site rating; plant
  relocated in 2026 — schedule risk flagged, no revised date
  published), Rawhide coal (Dec 2029), Comanche (CO) Unit 3
  (Dec 2030) and Ray D Nixon (Dec 2029, with a live legislative
  extension attempt flagged).

## Files (v2; v1 files untouched)

- `build_stack_v2.py` — the v2 build.
- `manual_adjustments.csv` — 10 row-level changes with sources,
  confidence, and an `east_west` column (region = East or West).
- `spp_capacity_plants_v2.csv` — unit-level changelog (258 rows:
  v1 256 + 2 new), with `v2_*` columns and `manual_change` flags;
  every row carries `east_west`.
- `spp_capacity_stack_v2.csv` — SPP total stack (year × fuel).
- `spp_capacity_stack_by_eastwest_v2.csv` — per-East/West stack.
- `spp_capacity_changelog_v2.csv` — forward changelog (year × fuel).
- `spp_capacity_changelog_by_eastwest_v2.csv` — changelog by East/West.
- `summary_v2.json` — v1/v2 forward totals, deltas, yearly totals
  for Combined/East/West, largest changes, flagged candidates.
- `research_log.md` — Part 1: expansion membership (SPP sources);
  Part 2: evidence per adjustment, KEEP list, unverified items.
- `01_stacked_area_v2.png`, `02_net_change_forward_v2.png`,
  `03_eastwest_stacked_v2.png`, `04_eastwest_totals_v2.png` — charts.
- `README.md` — v1 documentation (cut rule, anchor caveat and gap
  vs SPP published figures, trailing method, changelog).

## Open items (not in v2)
Tri-State's Craig-site replacement gas (307 MW) + battery
(200 MW) — ERP-approved concept, no pinned in-service date; the
SPP ERAS queue pool (~13,300 MW submitted, not itemised); PSO
Comanche (OK) 1,372.8 MW and AECC Naples 900.0 MW, kept from EIA
at (P) status with approvals unverified; Horizon/Williams Creek
100 MW battery (no EIA row); SPS life-extension requests for
Nichols/Maddox/Plant X units (approval status unclear); the
882.1 MW Tri-State PSCO/PNM boundary sensitivity. See
`research_log.md` and `summary_v2.json`.
