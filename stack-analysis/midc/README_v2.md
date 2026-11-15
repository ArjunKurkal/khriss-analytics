# MIDC capacity stack — v2 (EIA + manual corrections)

Built 2026-11-15 from v1 (see `README.md`) by applying 2 named manual
adjustments (3 row-level changes), each with an online source, logged
in `research_log.md` and `manual_adjustments.csv`. Reproduce with
`python3 build_stack_v2.py` (it verifies v1 reproduces, applies the
corrections, and asserts the corrected yearly flow deltas on every
run). v1 files are untouched.

## Headline figures (v2 vs v1)

| | v1 | v2 | Change |
|---|---|---|---|
| 2036 total | 78,857.9 MW | **79,043.9 MW** | **+186.0 MW** |
| Forward additions 2026–2036 | 14,100.2 MW (71 units) | 15,016.1 MW (73 units) | +915.9 MW |
| Forward retirements 2026–2036 | 88.0 MW (13 units) | 817.9 MW (14 units) | +729.9 MW |
| Forward net 2026–2036 | +14,012.2 MW | +14,198.2 MW | +186.0 MW |

Delta by fuel (net): **Nuclear +186.0 MW**; Natural Gas +729.9 MW of
additions exactly offset by Coal +729.9 MW of retirements (the
Centralia fuel switch nets to zero across the window); all other fuels
0. **Nuclear leads the v2 net change — it is the only fuel with a
nonzero net delta.** The v2 stack dips below v1 in 2026–2027
(−729.9 MW: Centralia coal is out, its gas conversion is not yet in),
rejoins v1 in 2028, and ends +186.0 MW from 2031. Year-by-year v2−v1
totals: 2026–2027 −729.9; 2028–2030 0; 2031–2036 +186.0.

## What changed (2 adjustments)

| # | Plant | Change | MW | Confidence |
|---|---|---|---|---|
| A | TransAlta Centralia Generation Unit 2, WA | Fuel switch coal→gas: ADD coal retirement Dec 2026; ADD gas Dec 2028 | 729.9 (each leg) | Medium-High |
| B | Columbia Generating Station, WA | ADD extended power uprate, Dec 2031 | +186.0 | Medium-High |

Notes and flags:
- **Centralia (A)** is entirely absent from EIA's forward data: the
  Operating sheet carries Unit 2 as coal with no planned retirement,
  and the Planned sheet has no conversion. The evidence: coal burn
  ceased at end-Dec 2025 under Washington law / the 2011 TransAlta
  agreement; DOE FPA §202(c) emergency orders then held the unit
  "available" as coal (zero generation; latest order through
  Dec 12, 2026), so the coal retirement is booked **Dec 2026** at the
  anchor boundary — the MISO v2 Belle River treatment. The gas leg is
  the Dec 9, 2025 TransAlta–Puget Sound Energy 16-year tolling
  agreement (700 MW contracted; 723 MW maximum net per the Jul 31,
  2026 SEPA determination; ~$600m; target COD late 2028; FID expected
  early 2027 after WUTC approval; runs to end-2044). Booked at the EIA
  nameplate 729.9 MW, as MISO v2 fuel switches kept nameplate
  unchanged. The 2027–2028 gap (coal out, gas not yet in) is real and
  is the region's tightest capacity window in this stack.
- **Columbia uprate (B)**: BPA approved implementation in May 2025
  (~$700m; 162 MW EPU + 24 MW efficiency = 186 MW), staged across the
  2027/2029/2031 refuelling outages and booked at completion
  (Dec 2031). The NRC licence amendment request is not submitted
  until 2028 — approval is pending, hence Medium-High, not High. The
  plant is licensed through 2043; no retirement is in any window.

## Checked, no adjustment (the larger v2 result)

- **Colstrip Units 3/4, MT, Coal, 1,647.4 MW — NO retirement added.**
  This is the region's largest single v2 question and the answer is
  that an EIA-style retirement would be wrong. Puget Sound Energy
  (25%) and Avista (15%) **transferred** their shares to NorthWestern
  Energy effective Jan 1, 2026; the Washington UTC's Final Order 05
  (Docket UE-240729) treats the transfer as PSE's "retirement" of
  coal from Washington supply under CETA — an ownership exit, not a
  unit shutdown. NorthWestern (now ~55%, operator) states it will run
  the units to **~2042** (Montana DEQ's Jan 2026 Rosebud Mine
  assessment uses 2042 on NorthWestern's published information).
  Portland General Electric plans to exit its 20% by end-2029 and
  PacifiCorp its 10% around 2030 — further ownership exits, not
  retirements; the units continue under the remaining owners.
  Emissions-rule status cuts both ways and neither way produces a
  date: the 2024 MATS update was litigated by the owners and is under
  rollback pressure from the current EPA, and NorthWestern sought a
  Montana PSC balancing account precisely to fund compliance and keep
  running to 2042. Montana-specific law (state limits on
  decommissioning-related cost recovery and the plant's mine-mouth
  fuel supply) supports continued operation. Plant-specific evidence
  only, per the brief: no retirement in 2026–2036.
- **Every EIA Planned unit ≥200 MW was web-checked and kept** at EIA
  MW/date (25 units, 11,250.0 MW): Sunstone (kept — Amazon acquired
  it out of Pine Gate's Chapter 11 on Feb 27, 2026 and EFSC approved
  the transfer Jun 26, 2026; construction must start by Nov 2027;
  grid-connected, counted in full despite Amazon's data-center
  purpose), Deschutes (kept — still in EFSC completeness review,
  unapproved; paper), Cedar Island, Haymaker (kept — see open items),
  Hop Hill, Blacks Creek (kept — construction began Jul 2026,
  $650m financing closed Mar 2026; Meta/Kuna load is served via an
  Idaho Power PPA through the grid, not BTM), Obsidian (kept — see
  open items), Nolin Hills (EFSC-approved Jul 2023; EIA's 300/300
  wind/solar split vs EFSC's 340/260 noted, EIA kept on the stack's
  nameplate basis), Lower Snake, Royal Slope, Salmonfly, Arco,
  Centralia BESS, Greenwater, Tualatin, Anthelope Hills. Detail in
  `research_log.md`.
- **No BTM exclusion.** The behind-the-meter scan found exactly one
  quantified co-located plant: VoltaGrid's **12 MW** mobile gas plant
  at the Vantage data-center campus in Quincy, WA (Grant PUD approval
  Jan 2026; temporary bridge until a Wanapum transmission upgrade
  lands in 2029). It is below the large-plant threshold, absent from
  EIA, and would count 0 MW under the BTM rule in any case. Utility
  grid plants built to serve data-center load (Centralia conversion
  for PSE, Blacks Creek for Idaho Power/Meta, Sunstone under Amazon
  ownership) are **not** BTM and are counted in full — the MISO v2
  Meta/Entergy conclusion, applied unchanged.
- **Out of scope, confirmed excluded:** North Valmy, NV (567.0 MW,
  NEVP — DSW/WECC-other) and Jim Bridger, WY (2,326.0 MW, PACE —
  SPP/Wyoming). Neither is in the state cut in either version.

## Files (v2; v1 files untouched)

- `build_stack_v2.py` — the v2 build.
- `manual_adjustments.csv` — 3 row-level changes with sources and
  confidence.
- `midc_capacity_plants_v2.csv` — unit-level changelog (90 rows:
  v1 87 + 3 new), with `v2_*` columns and `manual_change` flags.
- `midc_capacity_stack_v2.csv` — MIDC total stack (year × fuel).
- `midc_capacity_changelog_v2.csv` — forward changelog (year × fuel).
- `summary_v2.json` — v1/v2 forward totals, deltas, yearly totals,
  checked-no-adjustment items, flagged candidates not added.
- `research_log.md` — evidence, sources, and confidence per
  adjustment; KEEP list; BTM scan; unverified items.
- `README.md` — v1 documentation (working definition, BA inventory,
  anchor caveat, trailing method, changelog).
- `01_stacked_area_v2.png`, `02_net_change_forward_v2.png` — charts.

## Open items (not in v2)
Cascade Advanced Energy Facility SMR (Energy Northwest / X-energy /
Amazon, Richland WA: initial 320 MW, full build-out 960 MW;
pre-application at the NRC, construction-permit application targeted
end-2026, operations in the 2030s — too early and too undated to
book); Haymaker Hybrid (EIA 630 MW / Oct 2031 kept, but the
Clearway–PSE 25-year PPA describes a 315 MW facility with operations
by 2028 — MW and date conflict unresolved); Obsidian Solar Center
(kept Dec 2028, but EFSC had to extend its construction-start
deadline to Feb 25, 2028 after the original was missed for lack of
interconnection; completion may run to 2031); Badger Mountain Pumped
Storage (500 MW, WA, planning stage); Puget Sound Energy gas turbines
at an undisclosed Washington site for data-center load (reported,
unquantified). See `research_log.md` and `summary_v2.json`.
