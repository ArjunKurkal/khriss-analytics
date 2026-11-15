# DSW capacity stack — v1 (EIA-only)

Replicates the PJM/MISO new-builds-and-retirements (NBR) stack for the
Desert Southwest. Built 2026-11-15. Mirrors the MISO conventions:
trailing + forward 10-year stack 2016–2036 by fuel (Coal, Natural Gas,
Nuclear, Hydro, Pumped Storage, Wind, Solar, Oil, Battery Storage,
Other), nameplate MW throughout, anchor Dec 31, 2025, forward = anchor +
changelog. See `build_stack.py`; reproduce with `python3 build_stack.py`
(it asserts the anchor reproduction and the anchor + cumulative
changelog identity on every run).

## Working definition

**DSW = Desert Southwest = plants in AZ and NM.** This is a working
definition (working assumption), implemented as Plant State ∈ {AZ, NM}.
DSW is not a balancing authority, an ISO, or a NERC subregion with a
published capacity table; the cut is geographic (state), not BA-based.
Every plant physically in Arizona or New Mexico is in scope, whatever
its balancing authority — including plants whose output is exported
(SunZia Wind, coded CISO, whose power flows to CAISO/Arizona) and
eastern-New-Mexico plants in SPP (coded SWPP).

## Headline figures (v1)

| | 2025 anchor | 2036 | Change 2026–2036 |
|---|---|---|---|
| DSW total | 54,315.1 MW | 78,560.7 MW | +24,245.6 MW |
| Arizona | 40,514.0 MW | — | — |
| New Mexico | 13,801.1 MW | — | — |

Forward 2026–2036 (EIA-860M only): additions **28,202.2 MW** (176 units),
retirements **3,956.6 MW** (14 units), net **+24,245.6 MW**.
Additions by fuel: Solar 10,486.0; Battery Storage 9,749.0; Wind 4,340.2;
Natural Gas 3,627.0. Retirements by fuel: Coal 3,307.6 (84% of MW);
Natural Gas 618.9; Oil 27.0; Solar 3.1.
The single largest forward event is already in the 2026 in-service
cohort: SunZia Wind (NM, CISO) 3,650.2 MW, which entered service in
2026 and alone is 39% of the 9,324.7 MW that entered service
Jan–Sep 2026. The stack peaks in 2030 (81,738.5 MW) and declines
thereafter as the Four Corners (2031) and Coronado/Springerville
(2032) coal retirements outweigh the thin post-2030 pipeline — EIA's
Planned sheet for AZ/NM contains nothing after 2030.

Anchor by fuel (Dec 31, 2025, nameplate): Natural Gas 21,041.9;
Solar 9,782.6; Battery Storage 5,985.0; Wind 5,663.5; Coal 4,427.8;
Nuclear 4,209.6; Hydro 2,801.3; Pumped Storage 194.1; Oil 152.3;
Other 57.0. Top-3 fuels are gas, solar, and battery storage — the
anchor is already a solar/storage-heavy system, and Palo Verde alone
(4,209.6 MW) is the entire nuclear fleet.

## BA inventory (anchor, Dec 31, 2025, nameplate MW)

| BA code | MW | Who / what |
|---|---|---|
| SRP | 18,362.6 | Salt River Project (incl. Palo Verde, coded SRP) |
| AZPS | 9,866.8 | Arizona Public Service |
| PNM | 7,538.0 | Public Service Co. of New Mexico |
| WALC | 5,699.2 | WAPA Desert Southwest (AZ portion only; see edge cases) |
| TEPC | 4,499.2 | Tucson Electric Power |
| SWPP | 2,826.2 | SPP — eastern NM (Xcel/SPS and co-ops) |
| CISO | 2,704.2 | CAISO-coded plants in AZ/NM (SunZia is in the 2026 cohort, not the anchor; anchor CISO is mostly solar/storage near the CA border) |
| EPE | 928.7 | El Paso Electric — NM plants only (see edge cases) |
| DEAA | 713.0 | Arlington Valley Energy Facility |
| GRIF | 655.0 | Griffith Energy |
| GRIS | 324.3 | Broadview wind, NM |
| WACM | 197.9 | WAPA Colorado-Missouri — small NM hydro/gas |

The unadjusted Sep 2026 Operating snapshot inventory also includes a
DOPD row (Desert Bloom battery, 150.0 MW, in-service 2026) that drops
out of the anchor with the rest of the 2026 cohort. **NTUA does not
appear as a BA code anywhere in the EIA-860M AZ/NM data** — no
operating, planned, or retired unit in AZ or NM reports BA = NTUA
(the only NTUA-entity plant in the file is Red Mesa Solar, 72.0 MW,
in Utah, coded PACE). Navajo Nation-area plants in scope report under
other BAs: Four Corners (AZPS), Navajo Dam hydro (WACM / Farmington),
Kayenta Solar (WALC). NTUA's own small fleet is simply not in
EIA-860M under its own code — a definitional gap of the state cut as
implemented from this file, stated plainly.

## Anchor — the important caveat

**No published DSW-by-fuel anchor exists.** There is no DSW market
monitor, no SOM report, and no official AZ+NM capacity-by-fuel table.
So, per the MISO fallback, the anchor is the **EIA-860M
Operating-sheet snapshot, adjusted to Dec 31, 2025** (minus units in
service Jan–Sep 2026: 9,324.7 MW; plus Retired-sheet actual
retirements in 2026: 0.0 MW — there were none in AZ/NM), nameplate MW,
all statuses. It is **EIA-derived, stated explicitly.**

Cross-checks and gaps:
- EIA Operating snapshot Sep 30, 2026 (unadjusted): 63,639.8 MW
  nameplate / OP-only 63,073.1 MW.
- Utility fleet figures (APS, SRP, PNM) are **ownership-share** based
  and are not comparable: e.g. APS reports its ~63% share of Four
  Corners (~970 MW) and its share of Palo Verde, whereas EIA reports
  the **full plant capacity at the plant's location** (Four Corners
  1,636.2 MW; Palo Verde 4,209.6 MW). Palo Verde verified unit by
  unit: 3 units × 1,403.2 MW nameplate (net summer 1,311 / 1,314 /
  1,312 MW), Operating Years 1986 / 1986 / 1988, BA = SRP. The full
  4,209.6 MW sits in the AZ anchor even though APS, SRP, El Paso
  Electric, SCE, PNM, and LADWP share its output — that is the EIA
  convention, noted here so the nuclear figure is not misread as any
  one utility's capacity.
- No EIA state-electric-profile total was pulled for AZ+NM as an
  independent check in this build; the internal consistency check is
  the trailing reconstruction reproducing the anchor exactly
  (asserted).

## Edge cases (decided plant-by-plant, not silently)

- **(a) El Paso Electric (EPE).** EPE is a Desert Southwest utility,
  but a pure state cut splits it. IN scope: EPE's NM plants,
  1,338.7 MW in the Sep 2026 snapshot (928.7 MW at the anchor —
  Rio Grande, Newman-area NM units, Santa Teresa Solar, etc.).
  EXCLUDED: EPE's TX plants, **1,927.7 MW** (28 units), dominated by
  Newman (TX) 1,109.8 MW and Montana Power Station (TX) 527.2 MW,
  plus EPE's TX planned pipeline (602.2 MW, incl. Evlou Solar
  500.0 MW). **Choice: the state cut is kept pure.** EPE-TX is listed
  here as an excluded borderline item with its MW. Rationale: the TX
  units sit in El Paso, interconnect to the Western Interconnection
  through EPE's TX system, and there is no evidence their output is
  predominantly committed to NM load (EPE serves El Paso first);
  stretching the definition to "AZ + NM + El Paso County" would be a
  different region. If a user wants an EPE-inclusive variant, add
  1,927.7 MW to the snapshot (and the TX planned/retired rows) —
  the build does not do it silently.
- **(b) Hoover Dam and WALC (WAPA Desert Southwest).** Hoover Dam is
  split by EIA into two plant records at the state line:
  **Hoover Dam (AZ) 1,039.4 MW — IN scope** (Plant State = AZ, BA =
  WALC) and **Hoover Dam (NV) 1,039.4 MW — OUT of scope** (Plant
  State = NV). The two records are the Arizona and Nevada powerhouse
  halves of the same dam; the state cut takes exactly half the dam.
  Other WALC units: AZ 5,934.2 MW in the snapshot (Glen Canyon Dam
  1,312.0, Davis Dam 254.8, Apache Station, South Point, Sundance,
  etc.) are in; WALC's CA units (127.9 MW, incl. Parker Dam 120.0 MW —
  Parker Dam also straddles the river, coded CA) and NV units
  (1,309.4 MW = Hoover NV) are out. **Southern Nevada is NOT DSW
  under this definition:** NV Energy (NEVP) totals 16,056.9 MW
  nationally (16,038.3 MW in NV in the snapshot grouping) and none of
  it is in scope; NV's CISO/LDWP/WALC capacity is likewise excluded
  except where a plant physically sits in AZ.
- **(c) Navajo Nation / NTUA.** In scope by state (see BA inventory
  note): Four Corners sits on the Navajo Nation in NM and is fully
  in the stack at 1,636.2 MW. No BA = NTUA rows exist in the file.
- **(d) SPP western expansion / CAISO-coded plants.** Flagged, not
  silently treated: AZ/NM plants reporting under **SWPP** (2,942.6 MW
  snapshot; 2,826.2 MW anchor — Hobbs, Cunningham, Maddox, Sagamore
  Wind and other eastern-NM plants in Xcel/SPS territory) are SPP-RTO
  plants that happen to sit in NM; they are IN this geographic stack
  and will also appear in an SPP BA-based stack — do not sum the two
  stacks. Likewise **CISO**-coded plants in AZ/NM (6,654.4 MW
  snapshot, incl. SunZia Wind 3,650.2 MW, whose output is contracted
  to CAISO/Arizona via the SunZia HVDC line) are IN by state and will
  also appear in a CAISO cut. DSW is a geographic lens, not a market
  footprint; overlaps with BA-based regional stacks are expected and
  documented here.

## Trailing 2016–2025 — reconstructed, estimated

No published history exists, so the trailing is **reconstructed from
EIA unit-level data**: for year Y, Operating-sheet units with
Operating Year ≤ Y, plus Retired-sheet units with Operating Year ≤ Y
< Retirement Year. Planned Retirement Year is deliberately NOT used.
The reconstruction **reproduces the anchor exactly at 2025**
(asserted), and its shape is sane: 2016 41,260.9 → 2019 39,639.5 →
2025 54,315.1 MW. The expected historical events appear naturally:
Navajo Generating Station's closure drops 2,409.3 MW of coal in 2019
(the 2018→2019 total falls despite other additions); Escalante
(257.0 MW coal) retires in 2020; San Juan retires in two steps
(Units 2/3, 924.0 MW coal, 2017; Units 1/4, 924.0 MW, 2022 — note
EIA codes San Juan Units 1/4 with Energy Source RC in the Retired
sheet, so under the reference `eia_fuel()` mapping they reconstruct
as **Other**, not Coal; the MW and the year are right, the fuel label
is EIA's, and it is flagged here rather than silently remapped);
Cholla's last units (425.9 MW coal) retire in 2025 and are correctly
out of the anchor. The 2024→2025 jump (+5,016.0 MW) is the pre-SunZia
solar/storage build-out.

## Changelog (EIA-860M Sep 2026, Plant State ∈ {AZ, NM})

Additions = in service Jan–Sep 2026 (51 units, 9,324.7 MW) + Planned
sheet (125 units, 18,877.5 MW, all dated 2026–2030). Only 7,810.5 MW
of the planned pipeline is under construction / construction-complete
(U/V/TS statuses); 11,067.0 MW is not yet under construction
(L 5,491.0 + P 5,055.0 + T 521.0) — the forward pipeline beyond ~2028
is mostly paper, which is what v2 partially corrects.
Retirements = actual 2026 (0 units, 0.0 MW) + planned 2026–2036
(14 units, 3,956.6 MW). No blanket retirement-delay override (PJM's
was a PJM-only scenario). Overlap guards verified at 0.

Largest forward additions (v1, EIA): SunZia Wind South 2,561.2 MW +
SunZia Wind North 1,089.0 MW (NM, Wind, in-service 2026); Saddleback
Generation Station (Copia Power, Maricopa Co.) 1,250.0 MW gas
(Dec 2030, P); NTEC Gas Plant (San Juan Co., NM) 1,089.0 MW gas
(18 × 60.5 MW, Jun 2028, L); CO Bar Solar and BESS complex
~2,000 MW solar+battery across phases (2027–2028, P); Snowflake A
Solar and BESS 950.0 MW (Aug 2027, L); Maricopa Solar battery
550.0 MW (Dec 2026, U). Largest retirements: Four Corners 2 × 818.1 MW
coal (Dec 2031); Coronado 2 × 410.9 MW coal (Dec 2032);
Springerville Unit 2 424.8 MW coal (Dec 2032) and Unit 1 424.8 MW
(Dec 2027); Cunningham + Rio Grande + Maddox gas (~618.9 MW total,
2027–2034).

## Files

- `build_stack.py` — the build (asserts reproduction + changelog identity).
- `dsw_capacity_plants.csv` — unit-level forward changelog (176 additions
  + 17 retirements listed; 14 retirements fall in 2026–2036).
- `dsw_capacity_stack.csv` — DSW stack, long format (year × fuel).
- `dsw_capacity_changelog.csv` — forward changelog (year × fuel).
- `summary.json` — anchor, BA inventory, edge-case MW, trailing,
  forward totals, diagnostics.
- `01_stacked_area.png`, `02_net_change_forward.png` — charts.

## What v1 is not (v2 scope)

EIA-only. Per the standing rule, EIA is fairly good for a snapshot of
what is currently online but NOT reliable for larger gas/power plants
in the forward pipeline — v2 manually corrects the largest forward
plants from online sources (same discipline as MISO v2: each
adjustment with a source, logged in `research_log.md`). Known v2
items: Four Corners' announced extension past 2031; Coronado and
Springerville coal-to-gas conversions (EIA shows them as plain coal
retirements or not at all); Springerville Unit 3's 2031 retirement
(absent from EIA); Apache ST3's coal-to-gas transition; the Cholla
gas repower and APS's Desert Sun plant (both absent from EIA
Planned); Project Baccara's co-located gas plant (BTM test); and
verification of the big solar/battery projects (CO Bar, Snowflake).
v1 files are never overwritten by v2.
