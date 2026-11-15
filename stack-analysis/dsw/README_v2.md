# DSW capacity stack — v2 (EIA + manual corrections)

Built 2026-11-15 from v1 (see `README.md`) by applying 9 named manual
adjustments (18 row-level changes), each with an online source, logged
in `research_log.md` and `manual_adjustments.csv`. Reproduce with
`python3 build_stack_v2.py` (it verifies v1 reproduces, applies the
corrections, and asserts the corrected yearly flow deltas on every
run). v1 files are untouched.

## Headline figures (v2 vs v1)

| | v1 | v2 | Change |
|---|---|---|---|
| 2036 total | 78,560.7 MW | **83,779.2 MW** | **+5,218.5 MW** |
| Forward additions 2026–2036 | 28,202.2 MW (176 units) | 32,904.7 MW (185 units) | +4,702.5 MW |
| Forward retirements 2026–2036 | 3,956.6 MW (14 units) | 3,440.6 MW (15 units) | −516.0 MW |
| Forward net 2026–2036 | +24,245.6 MW | +29,464.1 MW | +5,218.5 MW |

Delta by fuel (net): Natural Gas **+4,702.5 MW**; Coal **+516.0 MW**
(retirements fall on net — the Four Corners extension removes more
coal retirement than the Springerville 3 / fuel-switch additions
create); all other fuels 0. Natural Gas leads the v2 net change.
The v2 stack peaks in 2032 at 84,074.2 MW and ends 2036 at
83,779.2 MW. Year-by-year v2−v1 totals: 2026 0; 2027 +424.8;
2028 +1,168.8; 2029 +1,168.8; 2030 +1,555.8; 2031 +2,733.9;
2032–2036 +5,218.5.

The story of v2 in one line: EIA's forward picture for DSW — coal
exits on schedule in 2031–2032 and almost nothing is built after
2030 — is stale in both directions. The coal does not exit (Four
Corners extends to 2038; Coronado and three of four Springerville
units convert to gas instead of retiring), and the post-2030 build
is not empty (Desert Sun, Cholla repower, Project Baccara). After
v2, DSW coal falls only from 4,427.8 MW (2025) to 1,636.2 MW (2036) —
and that remainder is Four Corners itself, extended, plus nothing
else: every other coal unit in AZ/NM has a retirement or conversion
date in v2.

## What changed (9 adjustments)

| # | Plant | Change | MW | Confidence |
|---|---|---|---|---|
| A | Four Corners, NM | Retime retirement Dec 2031 → Dec 2038 (out of window) | 1,636.2 | Medium-High |
| B | Coronado, AZ | Fuel switch coal→gas (2029) | 821.8 | Medium-High |
| C | Springerville Units 1/2, AZ | Fuel switch coal→gas (2030) | 849.6 | Medium-High |
| D | Springerville Unit 4, AZ | Fuel switch coal→gas (2029) | 458.1 | Medium |
| E | Springerville Unit 3, AZ | ADD retirement (2031) | −458.1 | Medium |
| F | Apache Station ST3, AZ | Fuel switch coal→gas (2027) | 204.0 | Low-Medium |
| G | Cholla, AZ | ADD gas repower (2030) | +387.0 | Medium |
| H | Desert Sun Power Plant, AZ | ADD gas CC (2032) | +1,238.0 | Medium |
| I | Project Baccara, AZ | ADD gas, co-located data center (2028) | +744.0 | Low-Medium |

Notes and flags:
- **Four Corners (A)** is retimed, not cancelled: APS's own language
  is operation "past 2031" to "no later than 2038," with the end date
  to be set by future IRPs. The other owners (PNM, TEP, SRP) still
  plan 2031 share exits; APS is the operator and EIA reports the
  full plant, so the plant-level date moves. A sale to the Navajo
  Nation's energy company or a gas conversion are also live APS
  talking points — either would keep the MW in the stack in some
  form, but neither is booked.
- **Fuel switches (B, C, D, F)** follow the MISO v2 treatment
  (Belle River / Petersburg): the coal MW leaves as a retirement in
  the conversion year and the same MW returns as a gas addition.
  Net stack effect is zero per switch; the fuel mix and the
  retirement cliff change materially. EIA missed D and F entirely
  (no planned retirement rows) and carried B and C as plain
  retirements at superseded dates.
- **Desert Sun (H)** uses APS's filed 2026 IRP figure (1,238 MW,
  2032). APS's own documents span 1,238–2,000 MW for the site by
  phase and rating basis; the unbooked remainder is a flagged
  candidate, not an addition.
- **Project Baccara (I)** is the BTM test case. It is counted in
  full because its filings describe a grid-selling, APS-interconnected
  plant and a grid-served data center — the standing rule zeroes only
  generation whose grid connection is entirely accounted for by the
  co-located load. The reasoning and the counter-consideration
  (Maricopa County's single-source emissions determination) are in
  `research_log.md`. This is the adjustment most likely to be
  reversed on new evidence.
- **Apache (F)** is the weakest adjustment: AEPCO's dated,
  grant-backed coal-to-gas commitment (end-2027) against a Jun 2026
  DOE coal-modernization grant for the same unit, on which AEPCO has
  not confirmed any change of plan.
- **No BTM exclusion** was applied anywhere in v2: Desert Sun's
  subscription phase and the TSMC direct-pricing contract are grid
  financing arrangements, and Baccara is grid-connected (above).
  Utility grid plants built to serve data-center load are counted,
  per the standing rule.

## Files (v2; v1 files untouched)

- `build_stack_v2.py` — the v2 build.
- `manual_adjustments.csv` — 18 row-level changes with sources and
  confidence.
- `dsw_capacity_plants_v2.csv` — unit-level changelog (205 rows:
  v1 193 + 12 new), with `v2_*` columns and `manual_change` flags.
- `dsw_capacity_stack_v2.csv` — DSW stack (year × fuel).
- `dsw_capacity_changelog_v2.csv` — forward changelog (year × fuel).
- `summary_v2.json` — v1/v2 forward totals, deltas, yearly totals,
  largest changes, flagged candidates not added.
- `research_log.md` — evidence, sources, and confidence per
  adjustment; KEEP list; unverified items; candidates not proposed.
- `01_stacked_area_v2.png`, `02_net_change_forward_v2.png` — charts.
- `README.md` — v1 documentation (working definition, BA inventory,
  edge cases, anchor caveat, trailing method, changelog).

## Open items (not in v2)
APS IRP generic CT/uprate bucket 1,107 MW (double-count risk vs EIA
rows); Desert Sun capacity beyond 1,238 MW (~762 MW, undated); TEP
2026 IRP new gas 300 MW (unnamed, by 2041); Palo Verde uprate
~100 MW (modelling case only, no APS proposal); Four Corners CCS
retrofit (FEED funding cancelled Oct 2025); SpaceX/Tombstone 6 GW
load campus (no generation, unapproved). See `research_log.md` and
`summary_v2.json`.
