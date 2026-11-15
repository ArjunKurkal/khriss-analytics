# ISO-NE capacity stack — v1 (EIA-only)

Replicates the PJM/MISO new-builds-and-retirements (NBR) stack for
ISO New England. Built 2026-11-15. Same conventions: trailing + forward
10-year stack 2016–2036 by fuel (Coal, Natural Gas, Nuclear, Hydro,
Pumped Storage, Wind, Solar, Oil, Battery Storage, Other), nameplate MW
throughout, anchor Dec 31, 2025, forward = anchor + changelog. Region
cut: **Balancing Authority Code = ISNE** in EIA-860M. See
`build_stack.py`; reproduce with `python3 build_stack.py` (it asserts
the trailing reproduction and the anchor + cumulative changelog identity
on every run).

## Headline figures (v1)

| | 2025 anchor | 2036 | Change 2026–2036 |
|---|---|---|---|
| ISO-NE total | 38,238.1 MW | 41,619.4 MW | +3,381.3 MW |

Forward 2026–2036 (EIA-860M only): additions **3,886.3 MW** (78 units),
retirements **505.0 MW** (12 units), net **+3,381.3 MW**.
Additions by fuel: Wind 1,515.0 (Vineyard Wind 1, 800.0, in service
2026 + Revolution Wind, 715.0, Nov 2026); Battery Storage 1,300.5;
Solar 1,067.8; Natural Gas 3.0; all other fuels 0.
Retirements by fuel: Coal 459.2 (all of it Merrimack — see the v2
correction in `README_v2.md`); Natural Gas 41.9; Solar 2.2; Wind 1.7.
Peak build year is 2026 (+1,961.8 MW net: Vineyard, Revolution,
Medway Grid battery 250 MW). After 2031 the EIA pipeline is empty — no
additions at all are in EIA for 2032–2036 — and the stack drifts down
only on small fuel-cell/solar retirements in 2035–2036.

Anchor by fuel (Dec 31, 2025, nameplate): Natural Gas 16,923.5;
Oil 5,970.4; Solar 3,734.3; Nuclear 3,501.9 (Millstone 2,259.9 +
Seabrook 1,242.0); Hydro 1,926.3; Pumped Storage 1,865.0 (Northfield
Mountain 1,168.0 + Bear Swamp 666.0); Wind 1,723.2; Other 1,362.6;
Battery Storage 771.7; Coal 459.2 (Merrimack only).

## Anchor — source and the CELT definitional gap

**The anchor is EIA-derived, stated explicitly — not an ISO-NE
publication.** It is the EIA-860M Operating-sheet snapshot (Sep 30,
2026: 39,295.1 MW nameplate) adjusted to Dec 31, 2025: minus units that
entered service Jan–Sep 2026 (1,078.3 MW, incl. Vineyard Wind 800.0),
plus Retired-sheet units actually retired in 2026 (21.3 MW).

ISO-NE's CELT report (Capacity, Energy, Loads and Transmission) was
used as a cross-check, not as the anchor, because CELT does not publish
a nameplate-by-fuel table comparable to this stack: CELT's generator
list works in Forward Capacity Market terms — summer/winter Seasonal
Claimed Capability and Capacity Network Resource Capability — counts
settlement-only generators separately, treats behind-the-meter solar
as a load modifier in the PV forecast rather than as generation, and
counts ~3,600 MW of demand resources and imports as capacity resources
(which are not generation and are excluded here). ISO-NE's own
overviews describe the region as having "nearly 30,000 MW of
generating capacity" (~29,700 MW, Mar 2025) on that capability basis.

The gap is therefore definitional, and it is large: EIA nameplate
38,238.1 MW vs ~29.7 GW capability — about **8.5 GW**. Decomposition:
(1) nameplate vs summer capability — on a net-summer basis the same
EIA anchor is 35,426.4 MW (wind, solar and oil steam derate heavily);
(2) EIA counts every ≥1 MW unit including small IPP/CHP and
settlement-only generators that CELT lists separately; (3) the EIA
snapshot includes 1,439.7 MW of non-operating nameplate ((OS) out of
service, (SB) standby, (OA)) — e.g., Middletown Units 2/3/4, 767.9 MW,
already marked "not expected to return"; (4) neither figure includes
behind-the-meter solar (next section). Do not mix the two bases.

## Trailing 2016–2025 — reconstructed, estimated

No published nameplate-by-fuel history exists, so the trailing is
**reconstructed from EIA unit-level data**: for year Y, Operating-sheet
units with Operating Year ≤ Y, plus Retired-sheet units with Operating
Year ≤ Y < Retirement Year. Planned Retirement Year is deliberately NOT
used. The reconstruction **reproduces the anchor exactly at 2025**
(asserted). Shape: 2016 37,662.7 → 2019 38,996.8 → 2023 39,125.5 →
2024 37,774.4 → 2025 38,238.1 MW. The named events appear naturally:
Brayton Point coal (1,124.6 MW) retires in 2017 (total falls that year);
Pilgrim nuclear (670.0 MW) in 2019; Bridgeport Harbor coal (400.0 MW)
in 2021; **Mystic's 1,744.4 MW gas retirement drives the 2024 drop**;
Schiller coal (100.0 MW coal + 50.0 MW other) retires in 2025.
Labelled estimated in every output row.

## Region cut and the northern-Maine exclusion

BA = ISNE covers the six New England states — **except northern
Maine**, which is in the Maritimes control area (the northern-Maine
system, often called NMISA; EIA codes it **NBSO**, New Brunswick System
Operator) and is not part of ISO-NE. Excluded on the BA cut: 20 units,
**155.7 MW** of Maine nameplate (largest: Mars Hill Wind Farm, 42.0 MW;
Woodland Pulp, ~72 MW). No planned northern-Maine units appear in EIA.
Conversely, 199.1 MW physically in New York state is coded BA=ISNE
(small solar, e.g., Eureka South/North) and is included — the cut is by
balancing authority, not state, exactly as in the MISO build. South
Fork Wind (132 MW, operating, off Rhode Island but delivering to
NYISO) is likewise correctly outside this stack.

## Changelog (EIA-860M Sep 2026, BA=ISNE)

Additions = in service Jan–Sep 2026 (10 units, 1,078.3 MW) + Planned
sheet (68 units, 2,808.0 MW, in-service years 2026–2031 only).
**Pipeline quality:** only 1,253.5 MW of the Planned sheet is under
construction or construction-complete (U/V/TS); **1,554.5 MW is paper**
(L 731.2 + P 645.5 + T 177.8) — including the two largest batteries
(Elevate Middletown 275 MW is status P; Energizar 250 MW is status L).
Retirements = actual 2026 (1 unit, 21.3 MW) + planned 2026–2036
(11 units, 483.7 MW). No blanket retirement-delay override: the PJM
coal-delay override was a PJM-only user scenario. Overlap guards
verified at 0. Largest additions (v1): Vineyard Wind 1 800.0 (2026);
Revolution Wind 715.0 (2026); Elevate Middletown battery 275.0 (2027);
Energizar battery 250.0 (2027); Freedom Pine Solar 250.0 (2029);
Medway Grid battery 250.0 (2026); Broadleaf Solar 200.0 (2028); Taft
battery 200.0 (2027). Largest retirement: Merrimack coal 459.2 MW
(2027/2028 in EIA — corrected in v2).

## Caveats

- **Behind-the-meter solar is largely invisible to EIA-860M.** ISO-NE
  puts total New England solar nameplate at ~9,600 MW at end-2025,
  including >5,100 MW of "behind all meters" PV that reports nothing to
  the ISO; this stack's solar anchor is 3,734.3 MW. The ~5.9 GW gap is
  a known omission of the EIA frame, flagged here and in v2 — it is
  **not** added to the stack.
- **EIA is stale on Merrimack** (still operating, retiring 2027/2028;
  actually closed Sep 2025) — corrected in v2; the v1 anchor and
  trailing inherit the error, which is why v1 coal survives to 2028.
- The anchor counts 5,970.4 MW of mostly elderly oil steam capacity at
  nameplate; much of it runs only in winter emergencies. Nameplate is
  the stack convention, but do not read the oil block as firm energy.
- EIA's forward pipeline for New England is thin and short (nothing
  after 2031) because offshore wind beyond Revolution, most batteries
  and all thermal projects sit in interconnection queues and state
  procurements, not in EIA-860M. v2 checks the large items; the queue
  itself (~38 GW nameplate in Jan 2025, 46% battery / 44% wind / 10%
  solar per ISO-NE) is not a build forecast and is not in the stack.

## Files

- `build_stack.py` — the build (asserts reproduction + changelog identity).
- `isone_capacity_plants.csv` — unit-level changelog (78 additions +
  14 retirements listed; retirements beyond 2036 also listed).
- `isone_capacity_stack.csv` — stack, long format (year × fuel).
- `isone_capacity_changelog.csv` — forward changelog (year × fuel).
- `summary.json` — anchor, CELT cross-checks, trailing, forward totals,
  diagnostics (incl. the northern-Maine exclusion).
- `01_stacked_area.png`, `02_net_change_forward.png` — charts.
- EIA source (not copied, not re-downloaded):
  `~/workspace/pjm-capacity-stack/raw/eia860m_sep2026.xlsx`.

## What v1 is not (v2 scope)

EIA-only. Per the standing rule, EIA is fairly good for a snapshot of
what is currently online but NOT reliable for larger plants in the
forward pipeline — v2 manually corrects the largest forward plants
from online sources (same discipline as MISO v2: each adjustment with
a source, logged in `research_log.md`). Known v2 items: Merrimack's
actual 2025 closure; Revolution Wind's as-built 704 MW; offshore-wind
stop-work orders and court reversals; Millstone/Seabrook status; the
largest battery projects; remaining oil/gas steam retirements
(Canal, Middletown, Boston-area units). v1 files are never overwritten
by v2.
