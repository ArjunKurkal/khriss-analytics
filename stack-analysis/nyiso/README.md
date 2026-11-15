# NYISO capacity stack — v1 (EIA-only)

Replicates the PJM/MISO new-builds-and-retirements (NBR) stack for
NYISO. Built 2026-11-15. Mirrors the PJM/MISO conventions: trailing +
forward 10-year stack 2016–2036 by fuel (Coal, Natural Gas, Nuclear,
Hydro, Pumped Storage, Wind, Solar, Oil, Battery Storage, Other),
nameplate MW throughout, anchor Dec 31, 2025, forward = anchor +
changelog. Region cut: Balancing Authority Code = NYIS in EIA-860M
(no sub-regional split — NYISO is a single-state ISO). See
`build_stack.py`; reproduce with `python3 build_stack.py` (it asserts
the trailing reproduction, the Indian Point check, the overlap guards,
and the anchor + cumulative changelog identity on every run).

## Headline figures (v1)

| | 2025 anchor | 2036 | Change 2026–2036 |
|---|---|---|---|
| NYISO total | 45,632.7 MW | 53,605.0 MW | +7,972.3 MW |

Forward 2026–2036 (EIA-860M only): additions **8,013.9 MW** (157 units),
retirements **41.6 MW** (22 units), net **+7,972.3 MW**.
Additions by fuel: Solar 4,464.9; Wind 2,697.5; Battery Storage 842.0;
Natural Gas 5.5; Other 3.0; Oil 1.0; Coal/Nuclear/Hydro/Pumped 0.
Retirements by fuel: Natural Gas 21.3; Other 17.6; Battery 1.7; Oil 1.0.
Peak build years: 2027 (+3,120.5 MW net — Empire Wind 1 and Sunrise
Wind land), 2028 (+2,112.1), 2026 (+1,505.1). The stack is flat after
2031: EIA's pipeline is exhausted by then (the only post-2031 planned
units in the file, two TBE-Montgomery units totalling 21.0 MW, are
dated 2039 and fall outside the window).

Anchor by fuel (Dec 31, 2025, nameplate): Natural Gas 25,892.0;
Hydro 4,681.0; Oil 3,874.4; Nuclear 3,398.4; Solar 2,950.4;
Wind 2,868.1; Pumped Storage 1,240.0; Battery Storage 275.2;
Other 453.2; **Coal 0.0** — New York has had no operating coal since
Somerset retired in 2020 (visible in the trailing).

## Anchor — basis and the Gold Book definitional gap

The anchor is the **EIA-860M Operating-sheet snapshot, adjusted to
Dec 31, 2025** (minus units in service Jan–Sep 2026: 197.1 MW; plus
Retired-sheet actual retirements in 2026: 10.6 MW), nameplate MW, all
statuses. It is **EIA-derived, stated explicitly — not a NYISO
publication.**

NYISO's Gold Book (*Load & Capacity Data Report*) does publish
installed capacity and is the natural cross-check — but it cannot be
the anchor for a nameplate stack, because it reports **summer/winter
capability (DMNC/CRIS ratings)**, not nameplate, and it counts
market-participating resources (with non-market load-modifier units in
a separate table). Cross-checks (in `summary.json` under
`anchor.cross_checks`, from the 2026 Gold Book, released April 2026):

- Existing **net summer capability: 37,420 MW**; NYCA generating
  capability 36,428 MW; **Total Resource Capability for summer 2026:
  40,866 MW** (including imports, Special Case Resources and other
  non-generation resources).
- Renewables summer capability 7,816 MW: conventional hydro 4,211;
  land-based wind 2,578; offshore wind 132; grid-connected solar 571;
  other renewables 324.
- EIA Operating snapshot Sep 30, 2026 (unadjusted): 45,819.2 MW
  nameplate / 42,981.4 MW net summer; OP-only 44,672.6 / ~42,000 MW.

The ~8.2 GW gap between the EIA nameplate anchor (45,632.7 MW) and
Gold Book summer capability (37,420 MW) is **definitional, not an
error in either source**: capability is tested output, derated from
nameplate (thermal units especially); grid solar counts 571 MW of
summer capability against ~3.0 GW of EIA nameplate because most
small/community solar is a load modifier rather than a market
generator and solar's capability value is a fraction of nameplate;
EIA includes out-of-service/standby units (1,146.6 MW non-OP) and
1,622.4 MW of NJ-sited plant under BA NYIS that delivers into New
York City (Linden Cogen 974.1 MW, Bayonne Energy Center 644.0 MW, two
small solar units). Do not mix the two bases.

BA boundary: BA = NYIS is the right filter. Only 199.1 MW of NY-state
capacity sits under another BA (ISO-NE), and the NYIS capacity outside
New York State is the NJ plant above plus two Pennsylvania solar
projects in the *Planned* sheet that interconnect into NYSEG
territory (verified as genuine NYISO projects in v2 — see
`research_log.md`).

## Trailing 2016–2025 — reconstructed, estimated

No nameplate-by-fuel history is published, so the trailing is
**reconstructed from EIA unit-level data**: for year Y, Operating-sheet
units with Operating Year ≤ Y, plus Retired-sheet units with Operating
Year ≤ Y < Retirement Year. Planned Retirement Year is deliberately
NOT used (it reflects plans as of Sep 2026, not history). The
reconstruction **reproduces the anchor exactly at 2025** (asserted in
the build), and its shape is sane: 2016 44,944.1 → 2019 45,780.1 →
2021 44,125.5 → 2025 45,632.7 MW. Sanity check asserted in the build:
nuclear falls exactly 1,299.0 MW in 2020 (Indian Point Unit 2, retired
Apr 2020) and 1,012.0 MW in 2021 (Indian Point Unit 3, retired Apr
2021) — the two largest single-unit retirements in NYISO history
appear naturally, alongside the last coal (Somerset, 655.1 MW, 2020).
Labelled estimated in every output row.

## Changelog (EIA-860M Sep 2026, BA=NYIS)

Additions = in service Jan–Sep 2026 (20 units, 197.1 MW) + Planned
sheet (139 units, 7,837.8 MW, 2026–2039; 7,816.8 MW falls in
2026–2031, plus two 10.5/9 MW TBE-Montgomery units in 2039). Only
3,366.3 MW of the planned pipeline is under construction /
construction-complete (U 1,726.7 + V 1,327.2 + TS 312.4); 4,471.5 MW
is not yet under construction (L 1,610.3 + P 2,361.2 + T 500.0) — the
forward pipeline is majority paper by MW, which is what v2 checks.
Retirements = actual 2026 (9 units, 10.6 MW, all tiny) + planned
2026–2036 (13 units, 31.0 MW). **This is v1's known blind spot**: EIA
carries no planned retirement for any large New York unit, because the
state's deactivation pipeline runs through NYISO's STAR process and
the DEC Peaker Rule. The 2026 Gold Book's deactivation pipeline alone
is 1,307 MW of summer capability. v2 corrects this on plant-specific
evidence; no blanket retirement-delay override is applied (the PJM
coal-delay-to-Jan-2029 override was a PJM-only user scenario).
Overlap guards verified at 0 (no unit double-counted between
in-service-2026 and planned-2026, or retired-2026 and
planned-retirement-2026).

Largest forward additions (v1, EIA): Sunrise Wind 924.0 MW (2027, U);
Empire Wind 1 810.0 MW (2027, V); Cider Solar 557.0 MW nameplate
(500 MWac project, 2026, U); Mineral Basin Solar (PA) 401.6 MW (2028,
P); Alle-Catt Wind 340.0 MW (2026, V); Excelsior Energy Center 280.0 MW
(2026, TS); South Ripley Solar 270.0 MW (2027, L); Mill Point Solar
250.0 MW (2028, P); Moonlight Flats Solar (PA) 250.0 MW (2030, P);
NISA battery 300.0 MW in two units (2028, T). Largest retirement in
v1 is 21.3 MW — see the blind-spot note above.

## Files

- `build_stack.py` — the build (asserts reproduction + identities).
- `nyiso_capacity_plants.csv` — unit-level forward changelog (159
  additions + 29 retirements listed; retirements beyond 2036 and the
  2039 additions are listed but outside the changelog window).
- `nyiso_capacity_stack.csv` — NYISO stack, long format (year × fuel).
- `nyiso_capacity_changelog.csv` — forward changelog (year × fuel).
- `summary.json` — anchor, Gold Book cross-checks, trailing, forward
  totals, diagnostics, file list.
- `01_stacked_area.png`, `02_net_change_forward.png` — charts.

## What v1 is not (v2 scope)

EIA-only. Per the standing rule, EIA is fairly good for a snapshot of
what is currently online but NOT reliable for larger plants in the
forward pipeline — and for NYISO its largest failure is retirements,
not additions. v2 manually checks the largest forward plants from
online sources (same discipline as PJM/MISO v2: each adjustment with a
source, logged in `research_log.md`): the offshore wind projects and
their 2025–2026 federal stop-work orders; downstate peaker
retirements under the DEC NOx peaker rule (Gowanus/Narrows barges,
Danskammer, Astoria); the four upstate nuclear units; the largest
battery projects; a behind-the-meter scan; and the transmission
projects (CHPE, Clean Path NY) that must be documented as excluded,
not counted. v1 files are never overwritten by v2.
