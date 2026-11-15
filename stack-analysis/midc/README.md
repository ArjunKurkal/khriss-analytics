# MIDC capacity stack — v1 (EIA-only)

Replicates the PJM/MISO new-builds-and-retirements (NBR) stack for
MIDC — the Pacific Northwest / Mid-Columbia. Built 2026-11-15. Mirrors
the PJM/MISO conventions: trailing + forward 10-year stack 2016–2036 by
fuel (Coal, Natural Gas, Nuclear, Hydro, Pumped Storage, Wind, Solar,
Oil, Battery Storage, Other), nameplate MW throughout, anchor
Dec 31, 2025, forward = anchor + changelog. See `build_stack.py`;
reproduce with `python3 build_stack.py` (it asserts the anchor
reproduction and the anchor + changelog identity on every run).

## Working definition (read this first)

**Working assumption, stated verbatim from the build brief:** "MIDC =
the Pacific Northwest / Mid-Columbia footprint = plants in WA, OR, ID,
MT that are NOT in CAISO (in practice, exclude any CISO-coded units;
also exclude plants in those states that report to SPP's western
expansion BAs if any appear — flag them rather than silently
including)."

Implemented as: **Plant State ∈ {WA, OR, ID, MT} AND Balancing
Authority Code ≠ CISO.** In the Sep 2026 vintage there are **zero**
CISO-coded units in the four states, so the cut equals the pure state
cut. MIDC is a scheduling/hub designation, not an ISO or a balancing
authority, so a state cut is the only implementable footprint; the BA
inventory below is reported so the cut can be audited.

Edge cases, decided explicitly:

- **(a) Eastern Montana.** The cut includes **all** of Montana per the
  working definition. MT is 7,662.4 MW of the anchor (11.8%). Inside
  it sit two slivers that other stacks in this series also claim: the
  **MISO-coded eastern-MT Montana-Dakota sliver, 155.6 MW** (the MISO
  build assigned it to MISO North), and **SWPP-coded units, 168.2 MW**
  (Culbertson Generation Station 108.2 MW + OREG 1/2, 60.0 MW — SPP
  western-expansion territory). Both are **included here and flagged**,
  per the brief's "flag them rather than silently including": summing
  this stack with the MISO or SPP stacks double-counts 323.8 MW.
- **(b) PacifiCorp East (PACE).** PACE-coded units physically in the
  four states are **included by state and flagged by BA**: 919.7 MW at
  the anchor, mostly southeast-Idaho hydro and wind (Grace, Oneida,
  Soda, Ashton, Gem State), Idaho wind (Goshen, Meadow Creek, Cedar
  Creek), the Pryor Mountain Wind plant in MT (239.8 MW), and the IFP
  Peaking Plant gas units in ID. PACE also carries 359.0 MW of the
  forward pipeline (Arco Wind and Solar, ID).
- **(c) Northern Nevada is NOT in scope.** NV belongs to the Desert
  Southwest / WECC-other builds. North Valmy (NV, 567.0 MW, NEVP) is
  excluded — one line, as briefed. Jim Bridger (WY, PACE) is likewise
  out of scope (SPP/Wyoming); it is not in this cut.

### Balancing Authority inventory (anchor basis, Dec 31, 2025)

| BA | MW | BA | MW |
|---|---|---|---|
| BPAT (Bonneville) | 30,510.7 | GCPD (Grant PUD) | 1,220.0 |
| IPCO (Idaho Power) | 4,871.8 | PACE (PacifiCorp East) ⚑ | 919.7 |
| NWMT (NorthWestern) | 4,260.4 | DOPD (Douglas PUD) | 866.8 |
| PGE (Portland General) | 4,224.5 | TPWR (Tacoma Power) | 724.8 |
| PSEI (Puget Sound Energy) | 3,339.0 | GRID (Gridforce) | 689.4 |
| AVRN (Avangrid Renewables) | 2,848.7 | WAUW (WAPA Upper Missouri) | 523.0 |
| PACW (PacifiCorp West) | 2,709.2 | GWA (Glacier Wind) | 210.0 |
| AVA (Avista) | 2,309.0 | WWA (WAPA Western) | 189.0 |
| SCL (Seattle City Light) | 2,068.1 | SWPP ⚑ | 168.2 |
| CHPD (Chelan PUD) | 2,037.8 | MISO ⚑ | 155.6 |

⚑ = flagged sliver (see edge cases). Note the EIA code for Idaho Power
is **IPCO** in this vintage (the brief's expected list said "IPC").
BPAT alone is 47.1% of the anchor — the federal Columbia River system
dominates the footprint. Snapshot basis (Sep 30, 2026, unadjusted) the
same inventory totals 65,430.7 MW; PACE is 937.2 MW on that basis.

## Headline figures (v1)

| | 2025 anchor | 2036 | Change 2026–2036 |
|---|---|---|---|
| MIDC total | 64,845.7 MW | 78,857.9 MW | +14,012.2 MW |
| WA | 31,711.8 MW | — | — |
| OR | 19,040.2 MW | — | — |
| MT | 7,662.4 MW (11.8%) | — | — |
| ID | 6,431.3 MW | — | — |

Forward 2026–2036 (EIA-860M only): additions **14,100.2 MW** (71
units), retirements **88.0 MW** (13 units), net **+14,012.2 MW**.
Additions by fuel: Solar 7,182.7; Battery Storage 5,145.0; Wind
1,695.0; Other 50.0; Natural Gas 17.5; Hydro 7.0; Oil 3.0;
Coal/Nuclear/Pumped 0. Retirements by fuel: Natural Gas 66.6; Hydro
15.0; Other 6.4 — **no coal, no nuclear, nothing above 61.8 MW**. That
near-empty retirement schedule is an EIA artifact, not a finding: the
region's two live coal questions (Centralia Unit 2, Colstrip Units
3/4) carry **no EIA planned retirement dates at all** and sit in the
anchor untouched. v2 resolves Centralia from plant-specific evidence
and documents why Colstrip gets no retirement (see `README_v2.md`).
Peak build years: 2027 (+5,780.5 MW net — the Sunstone year), 2029
(+3,553.5), 2031 (+2,630.0). The stack is flat 2032–2034 (no EIA
pipeline beyond 2031) and dips slightly in 2035 (Northeast (WA) gas,
61.8 MW).

Anchor by fuel (Dec 31, 2025, nameplate): **Hydro 35,201.7 (54.3%)**;
Wind 10,846.6; Natural Gas 10,360.1; Coal 2,540.6; Solar 2,445.7;
Nuclear 1,200.0 (Columbia Generating Station, the region's only
nuclear unit); Battery Storage 986.0; Other 853.9; Pumped Storage
314.0; Oil 97.1. **Hydro caution:** nameplate hydro is 54.3% of the
anchor, but Columbia/Snake hydro is largely run-of-river with limited
storage; dependable (firm) hydro capacity is far below nameplate and
varies with water year. Do not read 35.2 GW of nameplate hydro as
35.2 GW of firm capacity — PNUCC/E3 resource-adequacy work accredits
regional hydro at a fraction of nameplate.

## Anchor — the important caveat

**No published MIDC-by-fuel anchor exists.** MIDC (Mid-Columbia) is a
power scheduling hub / trading designation, not an ISO, so there is no
market-monitor capacity table to anchor to — the same situation as
MISO, one step further. The anchor is therefore the **EIA-860M
Operating-sheet snapshot, adjusted to Dec 31, 2025** (minus units in
service Jan–Sep 2026: 593.0 MW; plus Retired-sheet actual retirements
in 2026: 8.0 MW), nameplate MW, all statuses. It is **EIA-derived,
stated explicitly — not a BPA, PNUCC, or NWPCC publication.**

Cross-check (in `summary.json` under `anchor.cross_checks`):
- **PNUCC 2025 Northwest Regional Forecast** (Apr 2025), Figure 3:
  Northwest **utility** generating resources total **~55,000 MW
  nameplate** in 2026 (Power Act footprint). The EIA cut runs ~9.8 GW
  higher. The gap is definitional, in both directions: PNUCC counts
  resources serving Northwest utility load — including Canadian
  Columbia River Treaty entitlement and utility resources physically
  outside the four states — but only utility-owned/contracted
  resources (and only PacifiCorp West plus one-third of NorthWestern
  Energy), while EIA counts **every** generator physically in
  WA/OR/ID/MT, including merchant/IPP capacity contracted out of
  region and 4,278.4 MW of non-operating (OA/OS/SB) nameplate in the
  snapshot. PNUCC's ~30,000 MW of *needed future* nameplate by 2035 is
  a needs assessment, not a project pipeline; the EIA forward pipeline
  here (14.1 GW) is project-specific and not comparable line-to-line.
- EIA Operating snapshot Sep 30, 2026 (unadjusted): 65,430.7 MW
  nameplate; OP-only 61,152.3 MW.

## Trailing 2016–2025 — reconstructed, estimated

No published capacity-by-fuel history exists, so the trailing is
**reconstructed from EIA unit-level data**: for year Y,
Operating-sheet units with Operating Year ≤ Y, plus Retired-sheet
units with Operating Year ≤ Y < Retirement Year. Planned Retirement
Year is deliberately NOT used (it reflects plans as of Sep 2026, not
history). The reconstruction **reproduces the anchor exactly at
2025** (asserted in the build). Shape: 2016 60,858.5 → 2019 61,574.0 →
**2020 60,487.4** → 2025 64,845.7 MW. The 2020 dip is the coal exit,
and it appears naturally as briefed: Boardman (OR, 642.2 MW, Oct 2020)
and Colstrip Units 1/2 (MT, 358.0 MW each, Jan 2020) retire as Coal;
Centralia Unit 1 (WA, 729.9 MW, Dec 2020) also retires that year but
lands in **Other**, because the Retired sheet codes its energy source
"RC" (refined coal), which the reference `eia_fuel()` mapping — copied
exactly — does not classify as coal. True 2020 coal retirements were
2,088.1 MW; the fuel split (not the total) is misstated by that one
unit. Coal in the reconstruction: 3,952.8 (2016) → 2,594.6 (2020) →
2,540.6 (2025). Labelled estimated in every output row.

## Changelog (EIA-860M Sep 2026, state cut)

Additions = in service Jan–Sep 2026 (15 units, 593.0 MW) + Planned
sheet (56 units, 13,507.2 MW, 2026–2031; nothing is planned beyond
2031 in this cut). **Pipeline maturity is the v1 story:** only
1,309.8 MW of the planned pipeline is under construction or
construction-complete (U 888.0 + V 400.0 + TS 21.8); 12,197.4 MW is
not yet under construction (L 9,576.5 + P 1,363.0 + T 1,257.9). The
forward stack is mostly paper, which is what v2 checks plant by
plant. Retirements = actual 2026 (5 units, 8.0 MW, all ≤1.6 MW) +
planned 2026–2036 (8 units, 80.0 MW; largest Northeast (WA) gas
61.8 MW, 2035). Overlap guards verified at 0. The plants file also
lists retirements beyond 2036 (Chehalis gas, 593.3 MW, Dec 2043) —
outside the changelog window, no stack effect. **EIA carries zero
planned gas additions and zero coal retirements for this region** —
both gaps are v2 items, not findings.

Largest forward additions (v1, EIA): Sunstone Solar OR 1,200.0 MW
solar + 1,200.0 MW battery (Dec 2027, L); Deschutes Solar and BESS OR
1,000.0 + 1,000.0 MW (Nov 2029, L); Cedar Island Solar OR 800.0 MW
(Dec 2031, L); Haymaker Hybrid MT wind 630.0 MW (Oct 2031, P); Hop
Hill WA 500.0 solar + 500.0 battery + 200.0 wind (Sep 2031, L);
Blacks Creek Solar ID 400.0 MW (Jun 2027, U); Obsidian Solar Center
OR 400.0 MW (Dec 2028, L); Nolin Hills OR 300.0 wind + 300.0 solar
(Dec 2027, P); Lower Snake WA 300.0 + 300.0 MW (Oct 2029, L); Royal
Slope WA 260.0 + 260.0 MW (Oct 2027, T). Largest retirement in the
entire v1 changelog is 61.8 MW — see the caveat above.

## Files

- `build_stack.py` — the build (asserts reproduction + identities).
- `midc_capacity_plants.csv` — unit-level forward changelog (71
  additions + retirements incl. beyond-2036 rows).
- `midc_capacity_stack.csv` — MIDC total stack, long format (year × fuel).
- `midc_capacity_changelog.csv` — forward changelog (year × fuel).
- `summary.json` — anchor, cross-checks, BA/state inventories,
  trailing, forward totals, diagnostics, file list.
- `01_stacked_area.png`, `02_net_change_forward.png` — charts.
- EIA source (not copied; read in place):
  `~/workspace/pjm-capacity-stack/raw/eia860m_sep2026.xlsx`.

## What v1 is not (v2 scope)

EIA-only. Per the standing rule, EIA is fairly good for a snapshot of
what is currently online but NOT reliable for larger plants in the
forward pipeline — v2 manually checks every forward plant ≥200 MW
from online sources. Known v2 items: Centralia Unit 2 (coal ceased
Dec 2025; coal-to-gas conversion under a Dec 2025 TransAlta–PSE
agreement — entirely absent from EIA); Colstrip Units 3/4 (ownership
transfers and Montana/emissions-rule status vs the absence of any EIA
date); Columbia Generating Station's approved extended power uprate
(absent from EIA Planned); the large OR/WA/ID/MT wind/solar/battery
projects above; any large gas additions tied to data-center load; and
a behind-the-meter scan (Oregon/Washington data-center development is
heavy). Valmy (NV) and Jim Bridger (WY) are out of scope and are not
in either version. v1 files are never overwritten by v2.
