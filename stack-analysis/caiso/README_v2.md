# CAISO capacity stack — v2 (EIA + manual corrections)

Built 2026-11-15 from v1 (see `README.md`) by applying 3 named manual
adjustments (4 row-level changes), each with an online source, logged in
`research_log.md` and `manual_adjustments.csv`. Reproduce with
`python3 build_stack_v2.py` (it verifies v1 reproduces, applies the
corrections, and asserts the corrected yearly flow deltas on every run).
v1 files are untouched.

## Headline figures (v2 vs v1)

| | v1 | v2 | Change |
|---|---|---|---|
| 2036 total | 123,125.6 MW | **120,802.6 MW** | **−2,323.0 MW** |
| Forward additions 2026–2036 | 31,776.7 MW (287 units) | 31,776.7 MW (287 units) | 0 |
| Forward retirements 2026–2036 | 3,044.0 MW (23 units) | 5,367.0 MW (25 units) | +2,323.0 MW |
| Forward net 2026–2036 | +28,732.7 MW | +26,409.7 MW | −2,323.0 MW |

Delta by fuel (net): Nuclear **−2,323.0 MW**; all other fuels 0 (the
Ormond Beach retime moves 1,612.0 MW of gas retirement from 2027 into
2026 and nets to zero by 2036). The v2 stack ends 2036 at 120,802.6 MW.
Year-by-year v2−v1 totals: 2026 −1,612.0; 2027–2028 0; 2029 −1,159.0;
2030–2036 −2,323.0.

## What changed (3 adjustments)

| # | Plant | Change | MW | Confidence |
|---|---|---|---|---|
| A | Diablo Canyon Unit 1, CA | ADD retirement (Oct 2029) | −1,159.0 | High |
| B | Diablo Canyon Unit 2, CA | ADD retirement (Oct 2030) | −1,164.0 | High |
| C | Ormond Beach Units 1/2, CA | Retime Jan 2027 → Dec 2026 | 1,612.0 | Medium-High |

Notes and flags:
- **Diablo Canyon (A/B) is the correction that matters.** EIA-860M
  carries no planned retirement for the plant at all, so v1 silently
  assumed California's only nuclear plant (2,323.0 MW) runs through
  2036. Current state law says otherwise: SB 846 (2022) and CPUC
  Decision 23-12-036 authorise operation only to Oct 31, 2029 (Unit 1)
  and Oct 31, 2030 (Unit 2), confirmed by the CEC's July 2026 SB 846
  Operations Assessment. The NRC's Apr 2026 licence renewal to
  2044/2045 does **not** extend state authorisation; running past
  2029/2030 needs new legislation (a 2045 coalition is campaigning;
  no bill enacted). If that legislation passes, this adjustment
  reverses — it is the stack's largest single policy risk.
- **Ormond Beach (C)** aligns EIA's Jan 2027 with the State Water
  Board's OTC final compliance date, Dec 31, 2026 — the date the DWR
  Strategic Reliability Reserve contracts sunset. Alamitos Units 3/4/5
  and Huntington Beach Unit 2 were already at Dec 2026 in EIA and are
  kept. A post-2026 state/federal emergency order remains possible but
  does not exist as of Nov 15, 2026; per the standing rule, no
  speculative delay is booked.
- **Scattergood is not in this stack** — it is LADWP (BA=LDWP), outside
  the CISO footprint by definition. El Segundo's operating plant is a
  2013 dry-cooled CCGT, not an OTC unit. Both checked, neither adjusted.
- **Largest additions verified KEEP:** Darden Clean Energy Project
  (1,370.8 MW solar + 1,214.8 MW battery, Mar 2028 — CEC-approved Jun
  2025, financed, under construction; EIA nameplate retained over the
  CEC's 1,150 MWac figure), Bellefield 2 (500 + 500 MW, Dec 2026),
  Grace Energy Center (500 + 500 MW, 2027), SunZia Wind (3,650.2 MW,
  in service May 2026).
- **No BTM exclusion:** no co-located data-center generation plant
  meeting the behind-the-meter rule was found in the CAISO footprint;
  data-center load is arriving as grid load and co-location is still a
  CAISO tariff-design proceeding, not an operating fleet.

## Files (v2; v1 files untouched)

- `build_stack_v2.py` — the v2 build.
- `manual_adjustments.csv` — 4 row-level changes with sources and
  confidence.
- `caiso_capacity_plants_v2.csv` — unit-level changelog (316 rows:
  v1 314 + 2 new), with `v2_*` columns and `manual_change` flags.
- `caiso_capacity_stack_v2.csv` — CAISO stack (year × fuel).
- `caiso_capacity_changelog_v2.csv` — forward changelog (year × fuel).
- `summary_v2.json` — v1/v2 forward totals, deltas, yearly totals,
  largest changes, flagged candidates not added.
- `research_log.md` — evidence, sources, and confidence per adjustment;
  KEEP list; unverified items; candidates not proposed.
- `01_stacked_area_v2.png`, `02_net_change_forward_v2.png` — charts.
- `README.md` — v1 documentation (anchor caveat, scope/BAs, trailing
  method, changelog).

## Open items (not in v2)
Diablo Canyon extension to 2044/2045 (2,323.0 MW — needs state
legislation); Eagle Mountain Pumped Storage (1,300 MW — FERC-licensed
but unbuilt, no COD; EIA omits it); Chokecherry and Sierra Madre Wind
timing (3,550.5 MW — external sources suggest ~2 years earlier than
EIA's 2031–2033); SunZia attribution (483.2 MW — CAISO counts only
3,167 MW of the 3,650.2 MW EIA codes to CISO); Whale Rock Pumped
Storage (600 MW at Dec 2027, status P — paper project). See
`research_log.md` and `summary_v2.json`.
