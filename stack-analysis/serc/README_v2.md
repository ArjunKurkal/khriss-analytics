# SERC capacity stack — v2 (EIA + manual corrections)

Built 2026-11-15 from v1 (see `README.md`) by applying 25 named manual
adjustments (81 row-level changes), each with an online source, logged
in `research_log.md` and `manual_adjustments.csv`. Reproduce with
`python3 build_stack_v2.py` (it verifies v1 reproduces, applies the
corrections, and asserts the corrected yearly flow deltas and the
subregional-sum identity on every run). v1 files are untouched.

## Headline figures (v2 vs v1)

| | v1 | v2 | Change |
|---|---|---|---|
| 2036 total | 284,184.5 MW | **318,884.8 MW** | **+34,700.3 MW** |
| Forward additions 2026–2036 | 25,923.4 MW (249 units) | 62,272.2 MW (296 units) | +36,348.8 MW |
| Forward retirements 2026–2036 | 16,582.3 MW (89 units) | 18,230.8 MW (89 units) | +1,648.5 MW |
| Forward net 2026–2036 | +9,341.1 MW | +44,041.4 MW | +34,700.3 MW |
| 2036 SERC-Central | 203,701.3 MW | 217,404.6 MW | +13,703.3 MW |
| 2036 Florida | 80,483.2 MW | 101,480.2 MW | +20,997.0 MW |

Delta by fuel (net): Gas **+15,015.8 MW**; Battery **+10,577.0 MW**;
Solar **+10,355.0 MW**; Nuclear **+251.0 MW**; Coal **−1,498.5 MW**.
In v2's own forward account, **solar leads the net change**
(+23,699.4 MW net: 23,703.6 added, 4.2 retired), ahead of gas
(+21,241.2) and battery (+13,625.0); coal is −14,127.2. The v2 stack
peaks in 2033 at 321,762.4 MW and ends 2036 at 318,884.8 MW.
Year-by-year v2−v1 totals: 2026 +2,197.3; 2027 +6,617.7; 2028
+12,740.7; 2029 +18,632.9; 2030 +26,689.7; 2031 +28,106.7; 2032
+28,866.9; 2033 +34,000.9; 2034 +34,415.1; 2035–2036 +34,700.3.

Why the delta is so much larger than MISO's (+6,340.0): EIA's
Planned sheet for SERC effectively stops at 2030 and misses entire
filed programmes — FPL's battery build (zero FPL battery rows in
EIA), Georgia Power's PSC-certified 9,885 MW portfolio, Duke's
Person County CCs and the certificated Canadys CC — while carrying
TVA coal retirements TVA reversed in Feb 2026. v1 is a snapshot of
what EIA knows; v2 is what the utilities have actually filed.

## What changed (25 adjustments, condensed)

| # | Item | Change | MW | Confidence |
|---|---|---|---|---|
| A | Georgia Power CCs: Bowen 7-8 / Wansley 10-11 / McIntosh 12 | ADD 2029–2030 | +3,692.0 | High |
| B | Georgia Power certified BESS (10 tranches) | ADD 2027–2030 | +3,023.0 | High |
| C | Person County CC1 + CC2 (Roxboro) | ADD 2029/2030 | +2,720.0 | Med-High/Med |
| D | Roxboro coal Units 1 + 4 | ADD retirement 2029 | −1,156.0 | Medium |
| E | Marshall Advanced CTs 2×425 | ADD 2028 | +850.0 | High |
| F | Marshall Units 3 & 4 | Retime 2033→2034 | 1,422.0 | Med-High |
| G | Canadys Joint Resource CC | ADD 2033 | +2,180.0 | High |
| H | Wateree coal 1 & 2 | ADD retirement 2032 | −771.8 | Medium |
| I | Williams coal | ADD retirement 2034 | −659.7 | Medium |
| J | Winyah coal | Retime 2030→2034 | 1,275.8 | Medium |
| K | Victor J. Daniel Jr coal | Retime 2027→2035 | 1,096.6 | Medium |
| L | Cumberland coal | Retime out of window | 2,600.0 | Medium |
| M | Kingston coal | Retime out of window | 1,700.0 | Medium |
| N | Cumberland gas blocks | Retime →2026/2027 | 1,555.6 | Medium |
| O | Kingston BESS | ADD 2027 | +100.0 | Medium |
| P | Gaston Unit 5 | Fuel switch coal→gas 2028 | 952.0 | High |
| Q | Barry Unit 5 | Fuel switch coal→gas 2028 | 788.8 | Medium |
| R | E.W. Brown Unit 12 CC | ADD 2030 | +645.0 | High |
| S | LG&E/KU coal (MC3, MC4, Brown 3) | ADD retirement 2035 | −1,470.2 | Medium |
| T | Duke nuclear uprates (Brunswick/McGuire/Catawba) | ADD 2029/2031 | +251.0 | Med-High |
| U | FPL TYSP solar shortfall (6 tranches) | ADD 2027–2035 | +10,355.0 | Med-High/Med |
| V | FPL TYSP battery (10 tranches) | ADD 2026–2035 | +7,454.0 | Med-High/Med |
| W | FPL TYSP unnamed CTs (4 tranches) | ADD 2032–2035 | +3,276.0 | Low-Medium |
| X | FPL CC uprates | ADD 2027/2028 | +62.0 | Medium |
| Y | GCEC Units 4/5 | ADD retirement 2029 | −150.0 | Medium |

Notes and flags:
- **Florida drives 60% of the delta** (+20,997.0 of +34,700.3 MW),
  entirely from FPL's Ten Year Site Plan: EIA captured FPL's solar
  pace only through 2027 and none of its 7,454 MW battery build.
  TYSP annual solar/battery/fossil sub-totals each tie exactly to
  FPL's published totals (12,293 / 7,454 / 3,948 MW). The 2030–2035
  tranches and the unnamed CT blocks (W) are plan figures FPL itself
  flags as not-yet-final — they are the softest part of v2.
- **TVA reversed itself in Feb 2026.** Cumberland's retirement was
  formally reversed (board action, >$700m life extension) and
  Kingston's is under a Supplemental EIS proposing to run all nine
  coal units alongside the new gas. Both are retimed out of the
  window (Jan 2037 placeholder = no current date). Together they
  remove 4,300 MW of v1 coal retirements; if TVA re-dates either
  inside the window, that is v2's largest downside exposure.
- **No blanket delay was applied.** Bowen/Scherer needed none (their
  2038 exit, approved Jul 2025, is already outside the window and
  absent from EIA); Daniel, Winyah and Marshall 3&4 were retimed on
  plant-specific filings only.
- **Behind-the-meter:** the scan found exactly one large BTM build —
  xAI's ~1,200 MW permitted gas plant at Southaven, MS, self-supply
  for the Memphis Colossus campus. It is not in EIA and, under the
  standing rule (grid connection accounted for by the load → 0 MW),
  no row is added. All v2 additions are grid-connected utility
  capacity counted in full, including the data-center-driven Georgia
  certified fleet (system resources, procured by the utility).
- **Retirement count is unchanged (89) by coincidence of offsetting
  flows:** +11 new retirement rows (Roxboro, Wateree, Williams,
  Gaston/Barry coal legs, LG&E/KU, GCEC) against −11 rows retimed
  out of the window (Kingston 9, Cumberland 2).

## Files (v2; v1 files untouched)

- `build_stack_v2.py` — the v2 build.
- `manual_adjustments.csv` — 81 row-level changes with sources and
  confidence (column `region` carries the subregion, per the brief).
- `serc_capacity_plants_v2.csv` — unit-level changelog (408 rows:
  v1 350 + 58 new), with `v2_*` columns and `manual_change` flags.
- `serc_capacity_stack_v2.csv` — SERC total stack (year × fuel).
- `serc_capacity_stack_by_subregion_v2.csv` — per-subregion stack.
- `serc_capacity_changelog_v2.csv` — forward changelog (year × fuel).
- `serc_capacity_changelog_by_subregion_v2.csv` — changelog by subregion.
- `summary_v2.json` — v1/v2 forward totals, deltas, yearly totals,
  largest changes, flagged candidates not added, BTM finding.
- `research_log.md` — evidence, sources, and confidence per
  adjustment; KEEP list; unverified items; candidates not proposed.
- `01_stacked_area_v2.png`, `02_net_change_forward_v2.png`,
  `03_subregions_stacked_v2.png`, `04_subregional_totals_v2.png` — charts.
- `README.md` — v1 documentation (BA inclusion/exclusion table with
  MW, anchor caveat and definitional gap, trailing method).

## Open items (not in v2)
Cross coal retirement (2,451.5 MW, date under study in Santee
Cooper's 2026 IRP); V.C. Summer 2&3 completion (~2,234 MW, no
commitment); Mill Creek Unit 2 (355.5 MW, approved 2027 retirement
vs life-extension stipulation — two-sided); Mill Creek Unit 6 CC
(MW/date unverified); Cliffside Unit 5 (621.0 MW coded as gas in
EIA; possible in-window retirement not verified); Georgia certified
PPAs (2,821 MW, double-count risk) and solar+BESS COPs (350 MW,
split unpublished); FPL post-2035 pace (no TYSP beyond 2035, so
2036 gets no FPL tranche). See `research_log.md` and
`summary_v2.json`.
