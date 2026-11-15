# SPP capacity stack — v1 (EIA-only, East/West split)

Replicates the PJM/MISO new-builds-and-retirements (NBR) stack for
SPP, with the East/West split the user required so the series can be
indexed before and after SPP's RTO expansion into the West. Built
2026-11-15. Mirrors the reference conventions: trailing + forward
10-year stack 2016–2036 by fuel (Coal, Natural Gas, Nuclear, Hydro,
Pumped Storage, Wind, Solar, Oil, Battery Storage, Other), nameplate
MW throughout, anchor Dec 31, 2025, forward = anchor + changelog.
See `build_stack.py`; reproduce with `python3 build_stack.py` (it
asserts the anchor reproduction and the East + West = Combined
identity on every run). The full expansion-membership research is
in `research_log.md` Part 1.

## Headline figures (v1)

| | 2025 anchor | 2036 | Change 2026–2036 |
|---|---|---|---|
| SPP total | 116,939.3 MW | 131,128.0 MW | +14,188.7 MW |
| East | 103,225.0 MW | 116,035.3 MW | +12,810.3 MW |
| West | 13,714.3 MW | 15,092.7 MW | +1,378.4 MW |

Forward 2026–2036 (EIA-860M only): additions **23,664.7 MW**
(195 units), retirements **9,476.0 MW** (49 units), net
**+14,188.7 MW**. Additions by fuel: Natural Gas 12,172.0; Solar
7,078.3; Battery 2,822.5; Wind 1,549.6; Oil 42.3. Retirements by
fuel: Coal 6,426.8 (68% of MW); Gas 3,010.2; Oil 37.5; Other 1.5.
By region: East additions 18,997.3 / retirements 6,187.0; West
additions 4,667.4 / retirements 3,289.0. The stack peaks in 2030
(133,756.4 MW) and declines gently thereafter — **the EIA Planned
sheet for this footprint contains no additions after 2030 at all**,
so 2031–2036 is retirements only. That is an artefact of the
EIA pipeline's horizon, not a forecast (SPP's ERAS queue alone drew
13.3 GW of submissions; see `research_log.md`).

Anchor by fuel (Dec 31, 2025, nameplate): Wind 37,382.1; Natural
Gas 39,649.5; Coal 26,697.5; Hydro 4,784.5; Solar 2,321.3; Oil
2,505.2; Nuclear 2,097.3; Battery 560.0; Pumped Storage 467.7;
Other 474.2. Regional character: East is the wind fleet (Wind
35,453.4 of 103,225.0; Gas 37,413.4; Coal 20,279.3; both SPP
nuclear units — Wolf Creek, KS, 1,296.3 MW and Cooper, NE,
801.0 MW — sit in the East). West is coal/hydro-heavy for its size (Coal 6,418.2 of
13,714.3 — Laramie River, Craig, Dry Fork, Comanche (CO), Rawhide,
Bonanza, Nixon; Hydro 1,681.0 — WAPA-marketed federal dams; Wind
only 1,928.7; Solar 963.4).

## The East/West cut — read this first

SPP's RTO expansion into the Western Interconnection went **live
April 1, 2026** (FERC RTO Expansion Order, Mar 20, 2025,
190 FERC ¶ 61,169; SPP announcement Apr 2, 2026). SPP is now one
RTO with two Balancing Authority Areas. Per SPP's own Sep 4, 2026
filing, the West BAA was formed by consolidating the **WACM** and
**WAUW** balancing authorities. EIA-860M Sep 2026 still reports
the pre-consolidation codes, so the tagging rule is:

- **East** ⟺ Balancing Authority Code = **SWPP** (the legacy SPP
  BA = East BAA).
- **West** ⟺ Balancing Authority Code ∈ {**WACM**, **WAUW**}, **or**
  the plant belongs to a verified transmission-owning Expansion
  Member that EIA files under a BA that did not consolidate —
  exactly two such members have plants: **Platte River Power
  Authority** (Rawhide, 800.4 MW operating + 223.0 MW planned,
  filed under PSCO) and **Deseret G&T** (Bonanza + Solomon,
  526.9 MW, filed under PACE). These plant-level overrides are the
  analogue of MISO's RockGen override / Legend BA correction.
- **State never determines the tag; BA does.** Nebraska: SWPP
  Nebraska (12,090.4 MW) is East; 58.8 MW of WACM Nebraska solar/
  wind is West. South Dakota: SWPP (4,304.7 MW, incl. Basin's
  fleet and the Missouri River USACE dams) is East; WACM
  (499.9 MW) is West. Montana: SWPP (168.2 MW) East, WAUW
  (523.0 MW) West, and NWMT (~4,265.1 MW, incl. Colstrip) is not
  SPP at all. Wyoming/Colorado generation outside WACM (PSCO,
  PACE) is excluded except the two overrides.
- **Markets+ ≠ RTO membership.** APS, Salt River Project, Tucson
  Electric and UniSource are Markets+ participants only (a
  separate day-ahead market SPP operates for non-members, from
  2027); PNM chose CAISO EDAM; Xcel Colorado (PSCO) and
  PacifiCorp (PACE) are not RTO members. Their BAs (AZPS 12,810.9
  MW, SRP 19,134.0, TEPC 5,059.2, PNM 7,725.6, PSCO 17,225.8,
  PACE 20,004.0) are **excluded**, except the overrides above.
  Arizona's only RTO participant is the City of Page (no EIA
  generation); New Mexico's are Farmington, Aztec and Los Alamos
  County (their in-BA plants, ~0.2 GW, are in the West cut).
- Largest boundary judgements, both quantified in `summary.json`:
  (1) **Tri-State's plants under PSCO (696.1 MW) and PNM
  (186.0 MW) are excluded** (882.1 MW) — those BAs did not
  consolidate and SPP's tariff creates a "Tri-State-West" zone
  rather than absorbing them; if SPP publishes a unit-level West
  BAA roster showing them in, West's anchor rises by up to
  882.1 MW. (2) **WAPA-CRSP's flagship hydro under WALC is
  excluded** (Glen Canyon 1,312.0 MW; USBR-under-WALC total
  3,765.6 MW) because WALC did not consolidate, even though
  WAPA-CRSP is an Expansion Member and markets that power partly
  to West members. (3) Conversely, non-member plants physically
  inside WACM/WAUW **are** counted West (Xcel's Comanche (CO)
  1,252.8 MW; Black Hills ~813.5 MW; IPPs) — the stack is a
  BA-footprint stack, the same principle that counts non-member
  IPPs inside SWPP as East.

Every plants/changelog row carries `east_west` (and `region`,
which mirrors it), so the whole series can be re-indexed or re-cut
from the CSVs alone.

## Anchor — and the gap vs SPP's published figures

**No published SPP nameplate-by-fuel table exists for the
post-expansion footprint.** SPP's State of the Market covers the
legacy East market on a registered-resource basis; SPP 101 gives
East/West nameplate totals only, as of mid-2026. So, per the
reference fallback, the anchor is the **EIA-860M Operating-sheet
snapshot of the cut above, adjusted to Dec 31, 2025** (minus units
in service Jan–Sep 2026: 2,590.7 MW; plus Retired-sheet actual
retirements in 2026: 34.1 MW), nameplate MW, all statuses. It is
**EIA-derived, stated explicitly — not an SPP publication.**

Cross-checks (in `summary.json` under `anchor.cross_checks`):
- **East 103,225.0** vs SPP State of the Market 2025 registered
  nameplate ≈105,700 MW at end-2025 (derived from its published
  wind figure: 35,934 MW = 34% of installed nameplate; the build's
  East wind is 35,453.4 MW, −480.6). Gap ≈ **−2,474.7 MW (−2.3%)**.
  Vs SPP's 2025 Winter Deliverability Study registered total
  (Mar 1, 2025): 104,480.4 MW — gap −1,255.4 MW, and the by-fuel
  match is close (Gas: build East 37,413.4 vs study 37,483;
  Nuclear: 2,097.3 vs 2,061; Wind: 35,453.4 vs 36,334). The
  residual is the registered-resource vs EIA-all-statuses basis
  and 2025's retirements/additions timing.
- **West 13,714.3** vs SPP 101 (Aug 2026) West nameplate
  **10,069 MW** — EIA runs **+3,645.3 MW (+36%) higher**. Known
  drivers: EIA counts all statuses incl. standby/out-of-service;
  non-member capacity inside the two consolidated BAs (Comanche
  (CO) 1,252.8 MW; Black Hills ~813.5 MW; IPP wind/solar not
  registered as SPP market resources) accounts for ≈2,066 MW of
  the gap; SPP's figure is a registered-resource count as of
  Jul–Aug 2026. The West anchor should be read as "all nameplate
  physically in the West BAA footprint", not as SPP's registered
  total.
- SPP 101's East figure (110,753 MW, Jul 2026) is **not** used as
  a cross-check target for the Dec 2025 anchor: it post-dates the
  anchor by seven months (after 2,434.1 MW of East in-service
  2026 additions in this build) and is on SPP's own basis.
- EIA Operating snapshot of the cut, Sep 30, 2026 (unadjusted):
  119,495.9 MW nameplate (SWPP 105,625.0; WACM 11,415.3; WAUW
  1,128.3; overrides 1,327.3).

## Trailing 2016–2025 — reconstructed, estimated; West is pro-forma

Reconstructed from EIA unit-level data on the **constant
post-expansion footprint**: for year Y, Operating units with
Operating Year ≤ Y, plus Retired units with Operating Year ≤ Y <
Retirement Year (Planned Retirement Year deliberately not used).
It **reproduces the anchor exactly at 2025** for Combined, East
and West (asserted in the build). Combined: 2016 97,063.6 →
2025 116,939.3 MW (East 85,274.3 → 103,225.0; West 11,789.3 →
13,714.3). **The East trailing is genuine history** (SWPP existed
throughout). **The West trailing is pro-forma**: the West BAA did
not exist before April 1, 2026, so 2016–2025 West figures show
what today's West-footprint plants summed to in each year — they
are not a record of SPP membership, and the pre-2026 West series
should only be used as a footprint-constant comparison base.
Labelled as such in every output row.

## Changelog (EIA-860M Sep 2026, cut as above)

Additions = in service Jan–Sep 2026 (34 units, 2,590.7 MW) +
Planned sheet (161 units, 21,074.0 MW, all dated 2026–2030; only
part is under construction — the pipeline is mostly paper, which
is what v2 checks). Retirements = actual 2026 (5 units, 34.1 MW) +
planned 2026–2036 (44 units). Overlap guards verified at 0.

Largest forward additions (v1, EIA, by plant): Comanche (OK) gas
CC 1,372.8 MW (2029, status P — earliest planning stage); Naples
Power Plant TX 900.0 (2028, P); Cass County NE gas 792.0 (2029);
Evergy McNew KS 765.0 (2030) and Viola KS 765.0 (2029); Basin
Bison Generation Station ND 759.0 + 759.0 (2029/2030); Swan Solar
MO 650.0 (2028, U); GREC OK gas 594.0 (in service 2026); West:
Rail Tie Wind WY 504.0 (2029, L), Dutchman Solar WY 499.0 + 499.0
battery (2029, L), Horizon (Colorado Springs) 480.0 (2028, P),
Cowboy Solar I/II WY ~1,365 combined (2027–2028).
Largest retirements: La Cygne KS coal 873.0 (2032); Comanche (CO)
Unit 3 coal 856.8 (2030); Jeffrey Energy Center Unit 3 720.0
(2030); Tolk TX coal 2×567.9 (2028); Craig (CO) coal — Unit 1
446.4 (2026), Unit 2 446.4 (2028), Unit 3 534.8 (2029 in v1;
retimed in v2); Lawrence Energy Center 517.0 (2032); Comanche
(CO) Unit 2 396.0 (2026); Rawhide coal 293.6 (2029); Ray D Nixon
coal 207.0 (2029). West retirements are dominated by Colorado
coal (Craig + Comanche (CO) + Rawhide + Nixon = 2,880.0 MW of the
West's 3,289.0 MW).

## Files

- `build_stack.py` — the build (asserts reproduction + East/West sums).
- `spp_capacity_plants.csv` — unit-level changelog (195 additions +
  61 retirements incl. beyond-2036 rows), every row with `east_west`.
- `spp_capacity_stack.csv` — SPP total stack, long format (year × fuel).
- `spp_capacity_stack_by_eastwest.csv` — per-East/West stack.
- `spp_capacity_changelog.csv` — forward changelog (year × fuel).
- `spp_capacity_changelog_by_eastwest.csv` — changelog by East/West.
- `summary.json` — anchor, cross-checks, trailing, forward totals,
  boundary diagnostics, file list.
- `01_stacked_area.png`, `02_net_change_forward.png`,
  `03_eastwest_stacked.png`, `04_eastwest_totals.png` — charts.
- `raw/eia860m_sep2026.xlsx` — EIA-860M Sep 2026 vintage (same file
  as the PJM/MISO stacks).
- `research_log.md` — Part 1: the expansion-membership research.

## What v1 is not (v2 scope)

EIA-only. EIA is fairly good for a snapshot of what is currently
online but NOT reliable for larger plants in the forward pipeline:
v2 (see `README_v2.md`) manually verifies the large forward plants
and finds two SPS gas plants EIA misses entirely (Gaines County
CTG, Tolk Station CTG), retimes Craig Unit 3, Tolk and the Rawhide
gas units on regulatory evidence, and confirms the Craig Unit 1
DOE-order position. v1 files are never overwritten by v2.
