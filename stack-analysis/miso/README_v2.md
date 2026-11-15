# MISO capacity stack — v2 (EIA + manual corrections)

Built 2026-11-14 from v1 (see `README.md`) by applying 12 named manual
adjustments (26 row-level changes), each with an online source, logged in
`research_log.md` and `manual_adjustments.csv`. Reproduce with
`python3 build_stack_v2.py` (it verifies v1 reproduces, applies the
corrections, and asserts the corrected yearly deltas and the regional-sum
identity on every run). v1 files are untouched.

## Headline figures (v2 vs v1)

| | v1 | v2 | Change |
|---|---|---|---|
| 2036 total | 241,535.8 MW | **247,875.8 MW** | **+6,340.0 MW** |
| Forward additions 2026–2036 | 52,546.5 MW (437 units) | 61,290.3 MW (449 units) | +8,743.8 MW |
| Forward retirements 2026–2036 | 22,985.6 MW (107 units) | 25,389.4 MW (111 units) | +2,403.8 MW |
| Forward net 2026–2036 | +29,560.9 MW | +35,900.9 MW | +6,340.0 MW |
| 2036 North | 55,095.5 MW | 55,095.5 MW | 0 |
| 2036 Central | 111,409.3 MW | 116,995.3 MW | +5,586.0 MW |
| 2036 South | 75,031.0 MW | 75,785.0 MW | +754.0 MW |

Delta by fuel (net): Gas **+8,566.8 MW**; Coal **−2,403.8 MW**; Nuclear
**+177.0 MW**; all other fuels 0. The v2 stack peaks in 2031 at
249,277.5 MW (vs v1 244,595.9 MW) and ends 2036 at 247,875.8 MW.
Year-by-year v2−v1 totals: 2026 +1,560.8; 2027 0; 2028 +548.2; 2029
+2,855.6; 2030 +2,312.6; 2031 +4,681.6; 2032–2034 +5,381.6; 2035
+6,163.0; 2036 +6,340.0.

## What changed (12 adjustments)

| # | Plant | Change | MW | Confidence |
|---|---|---|---|---|
| A | Cayuga Energy Complex CC1/CC2, IN | ADD (Sep 2029 / May 2030) | +1,476.0 | High |
| B | Cayuga coal Units 1/2, IN | ADD retirement (Jan 2030 / Jan 2031) | −1,062.0 | Medium |
| C | Legend Power Station, TX | ADD (Jul 2028; EIA BA code corrected) | +754.0 | High |
| D | DTE Handy + Milan, MI | ADD (Dec 2031 / Dec 2032) | +2,100.0 | Medium |
| E | Consumers Karn + Thetford, MI | ADD (Dec 2031) | +1,500.0 | Low-Medium |
| F | Fermi 2 uprate, MI | ADD (Jan 2036) | +177.0 | Medium |
| G | Belle River, MI | Fuel switch coal→gas (2026) | 0 net (1,395.0) | Medium-High |
| H | AES Petersburg, IN | Fuel switch coal→gas (2026) | 0 net (1,341.8) | High |
| I | J.H. Campbell, MI | Retime Nov 2026 → Feb 2027 | 1,560.8 | Medium-High |
| J | Traceview, MS | Retime Aug 2028 → Dec 2029 | 819.4 | Medium-High |
| K | Gerald Andrus, MS | Retime Jun 2035 → May 2028 | 781.4 | Medium-High |
| L | Steel River Solar Phase 3, AR | Retime Jul 2030 → Dec 2029 | 750.0 | Medium |

Notes and flags:
- **Cayuga** (A) is the plant removed from PJM v2 the same evening —
  it interconnects into MISO, confirmed by IURC Cause No. 46193 (CPCN
  approved Oct 29, 2025) and a MISO Generator Replacement Request. The
  coal retirement (B) carries a real overhang: a Jun 2025 settlement
  requires a feasibility study on selling the coal units to a third
  party for continued operation.
- **D and E are IRP proposals, not approvals** (MPSC review pending).
  E's per-unit 750/750 split and Dec 2031 date are assumed placeholders
  — the verified facts are the 1.5 GW total and the two sites.
- **Campbell** (I) is retimed to the current DOE emergency order's
  expiry (Feb 12, 2027), not to a new retirement date; the D.C. Circuit
  vacated the first order Sep 11, 2026, so further renewal is uncertain
  and the ultimate retirement date is low-confidence.
- **Legend** (C) was excluded from v1 by an EIA BA-code error (ERCO);
  the MISO attribution was confirmed independently by the coordinator
  (PUCT Docket 56693: MISO determines Legend's transmission upgrades).
- **No BTM exclusion** was found among the large EIA plants: the
  Meta/Entergy and Google/Cypress plants are utility grid plants serving
  data-center load through the grid, not on-site co-located generation.

## Coordinator correction (read this before quoting the research report)
The v2 researcher's year-by-year table double-counted Belle River's coal
retirement as a NEW retirement. It is a retime (v1 already had it, Dec
2028 → Dec 2026). The correct net 2036 effect is **+6,340.0 MW**, not
the researcher's +4,945.0 MW, and the correct 2028 flow delta is
**+548.2 MW**, not −846.8 MW. The build asserts the corrected figures.
Details in `research_log.md` and `summary_v2.json`
(`coordinator_arithmetic_note`).

## Files (v2; v1 files untouched)

- `build_stack_v2.py` — the v2 build.
- `manual_adjustments.csv` — 26 row-level changes with sources and
  confidence.
- `miso_capacity_plants_v2.csv` — unit-level changelog (599 rows:
  v1 583 + 16 new), with `v2_*` columns and `manual_change` flags.
- `miso_capacity_stack_v2.csv` — MISO total stack (year × fuel).
- `miso_capacity_stack_by_region_v2.csv` — per-region stack.
- `miso_capacity_changelog_v2.csv` — forward changelog (year × fuel).
- `miso_capacity_changelog_by_region_v2.csv` — changelog by region.
- `summary_v2.json` — v1/v2 forward totals, deltas, yearly totals,
  largest changes, flagged candidates not added.
- `research_log.md` — evidence, sources, and confidence per adjustment;
  KEEP list; unverified items; candidates not proposed.
- `01_stacked_area_v2.png`, `02_net_change_forward_v2.png`,
  `03_regions_stacked_v2.png`, `04_regional_totals_v2.png` — charts.
- `README.md` — v1 documentation (anchor caveat, trailing method,
  regionalization, changelog).

## Open items (not in v2)
Vista Sands 300 MW BESS (MW/date split unverified); Constellation–Google
nuclear uprates (MISO share of ~890 MW unknown); R.S. Nelson Unit 6
retirement (~615 MW, 2028?, unverified); White Bluff coal (retire vs
convert unresolved); Schahfer-site CCGT + data center (2,300 MW claimed,
unverified); Schahfer Units 17/18 (kept Dec 2026, high delay risk under
DOE orders). See `research_log.md` and `summary_v2.json`.
