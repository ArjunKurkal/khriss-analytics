# SERC capacity stack — v1 (EIA-only, by subregion)

Replicates the PJM/MISO new-builds-and-retirements (NBR) stack for
SERC — the non-ISO Southeast. Built 2026-11-15. Mirrors the PJM/MISO
conventions: trailing + forward 10-year stack 2016–2036 by fuel (Coal,
Natural Gas, Nuclear, Hydro, Pumped Storage, Wind, Solar, Oil, Battery
Storage, Other), nameplate MW throughout, anchor Dec 31, 2025,
forward = anchor + changelog. See `build_stack.py`; reproduce with
`python3 build_stack.py` (it asserts the anchor reproduction and the
subregional-sum identity on every run).

## Headline figures (v1)

| | 2025 anchor | 2036 | Change 2026–2036 |
|---|---|---|---|
| SERC total | 274,843.4 MW | 284,184.5 MW | +9,341.1 MW |
| SERC-Central | 195,217.3 MW | 203,701.3 MW | +8,484.0 MW |
| Florida | 79,626.1 MW | 80,483.2 MW | +857.1 MW |

Forward 2026–2036 (EIA-860M only): additions **25,923.4 MW** (249
units), retirements **16,582.3 MW** (89 units), net **+9,341.1 MW**.
Additions by fuel: Solar 13,348.6; Natural Gas 9,113.8; Battery
3,048.0; Wind 247.0; Oil 114.0; Hydro 35.0; Other 17.0.
Retirements by fuel: Coal 12,628.7 (76% of MW); Gas 2,888.4; Oil
1,015.4; Other 45.6; Solar 4.2.
The EIA pipeline is front-loaded and thin at the back: additions by
year are 5,009.3 (2026), 11,013.2 (2027), 2,047.3 (2028), 6,734.8
(2029), 341.0 (2030), 0 (2031–2033, 2035–2036) and 777.8 (2034) — EIA's
Planned sheet simply does not carry the Southeast's 2030s pipeline,
which is what v2 corrects. The v1 stack peaks in 2029 (294,554.5 MW).

Anchor by fuel (Dec 31, 2025, nameplate): Natural Gas 143,861.4;
Coal 41,096.7; Nuclear 33,301.4; Solar 27,150.2; Hydro 11,589.4;
Pumped Storage 6,515.4; Oil 4,412.7; Other 4,163.1; Battery 1,793.7;
Wind 959.4. Top-3 fuels are gas, coal, nuclear (52.3% / 15.0% / 12.1%).

Subregional character at the anchor: SERC-Central holds all of the
coal fleet's core (TVA, Southern, Duke Carolinas), all pumped storage
of consequence, and 195.2 GW across 11 BAs. Florida (79.6 GW, 9 BAs)
is gas-and-solar: FPL alone is 42,039.1 MW of it, with no coal except
Duke Energy Florida's Crystal River units and FPL's 215 MW summer
share of Scherer Unit 3 in Georgia (booked under SOCO — see the BA
table; subregion follows the BA, not the plant's state).

## Region cut — Balancing Authority Codes (the headline caveat)

The cut is built from EIA-860M **Balancing Authority Codes, not
states** — the same lesson as MISO's BA-boundary discussion. The NERC
SERC footprint contains ISO/RTO members inside Southeast states, and
NERC's own SERC Assessment Area definition *excludes* SERC members
that are also PJM or MISO members. In the twelve Southeast states
(VA/NC/SC/GA/FL/AL/TN/KY/MS/AR/MO/LA), **116,560.7 MW of operating
nameplate sits under non-SERC BAs** (MISO 61,671.5 — incl. all of
Entergy; PJM 41,138.2 — incl. Dominion Energy Virginia and Duke
Energy Kentucky; SWPP 12,115.5; SPA 1,635.5). A state-based cut would
wrongly sweep all of that in. Conversely, only 1,255.5 MW of the
included BAs sits outside those twelve states (AECI in OK/IA) — the
BA is the unit of the cut, so it stays in.

### Included BAs (anchor MW, Dec 31, 2025)

**SERC-Central (195,217.3 MW):**

| BA | What it is | Anchor MW |
|---|---|---|
| SOCO | Southern Company — Georgia Power, Alabama Power, Mississippi Power, plus Oglethorpe Power, MEAG and PowerSouth, which all report under SOCO in EIA (verified in-file; there are no separate OPC/MEAG BA codes) | 70,584.4 |
| TVA | Tennessee Valley Authority | 44,023.2 |
| DUK | Duke Energy Carolinas (the brief's "DUKE"; EIA code is DUK) | 30,990.7 |
| CPLE | Duke Energy Progress East | 17,643.0 |
| SCEG | Dominion Energy South Carolina (EIA retains the legacy SC Electric & Gas code; no successor code exists in the file) | 8,134.7 |
| LGEE | LG&E / Kentucky Utilities | 9,073.8 |
| AECI | Associated Electric Cooperative (MO/AR; IA/OK slivers ride along with the BA) | 6,705.6 |
| SC | Santee Cooper (SC Public Service Authority) | 5,978.5 |
| SEPA | Southeastern Power Administration (federal hydro, GA/SC/NC) | 1,826.6 |
| YAD | Yadkin Division hydro (Eagle Creek Renewable, NC) | 215.2 |
| CPLW | Duke Energy Progress West (small; mostly batteries/solar) | 41.6 |

**Florida (79,626.1 MW)** — peninsular Florida transferred from FRCC
to SERC as Regional Entity on Jul 1, 2019 (FERC Docket RR19-4), so
Florida is *in* SERC; it is tagged separately so totals can be quoted
both ways:

| BA | What it is | Anchor MW |
|---|---|---|
| FPL | Florida Power & Light (incl. ex-Gulf Power NW Florida) | 42,039.1 |
| FPC | Duke Energy Florida (the brief's "DEF"; EIA retains the legacy Florida Power Corp code) | 16,480.5 |
| TEC | Tampa Electric | 8,684.5 |
| FMPP | Florida Municipal Power Pool — FMPA, Orlando Utilities Commission (the brief's "OUC"), Kissimmee, Lakeland, Key West et al. | 4,577.4 |
| JEA | Jacksonville Electric Authority | 3,214.5 |
| SEC | Seminole Electric Cooperative | 2,825.6 |
| TAL | City of Tallahassee | 1,023.8 |
| GVL | Gainesville Regional Utilities | 745.0 |
| HST | City of Homestead | 35.7 |

Notes on the brief's starting list, verified against the file:
- **No NCEM (NC Electric Membership) BA code exists** in EIA-860M, and
  no other NC muni/co-op BA code exists; NC municipal/co-op generation
  reports under DUK/CPLE/CPLW. Georgia co-op/OPC and MEAG plants
  report under SOCO (Oglethorpe 6,472.2 MW and MEAG 594.1 MW of
  Operating nameplate, inside SOCO's total).
- Florida Municipal Power Agency plants also appear inside FPC
  (250.1 MW Operating) — they are in the Florida subregion either way.
- SOCO's 309.6 MW in Florida (legacy Gulf Power panhandle units not
  yet moved to FPL) is tagged SERC-Central because the subregion
  follows the BA. This is the one place the BA rule and a geographic
  rule visibly differ; it is 0.1% of the anchor.

### Excluded BAs and borderline calls

- **PJM and MISO codes — excluded even inside SERC states.** Largest
  cases: Dominion Energy Virginia (PJM, in VA); Duke Energy Indiana /
  Ohio / Kentucky (PJM/MISO, in IN/OH/KY); Entergy (MISO — Arkansas,
  Louisiana, Mississippi, Texas; Entergy is a MISO member, so its
  Southeast plants belong to the MISO stack); southern Illinois (MISO).
- **EKPC (East Kentucky Power Cooperative) — excluded.** EKPC joined
  PJM on Jun 1, 2013 and is no longer reported in SERC's assessment
  areas; its 3,494.6 MW of Operating nameplate is coded BA=PJM in EIA.
- **Plum Point (AR, 720 MW) — excluded.** Coded BA=MISO in EIA
  (NRG/Plum Point Energy Associates); an Arkansas border plant that
  belongs to the MISO stack despite AECI's part-ownership interest.
- **SPA (Southwestern Power Administration) — excluded.** 2,748.3 MW
  Operating nameplate nationally (1,635.5 MW of it in AR/MO: federal
  hydro plus IPPs). SPA markets into the SPP footprint and is not on
  the SERC assessment-area BA list; including it would also sweep in
  its Oklahoma SPP-area plants. This is the closest exclusion call;
  it is 0.6% of the anchor if reversed.
- **SWPP / ERCO in AR/MO/LA/TX — excluded** (west-side RTOs).
- **NSB (New Smyrna Beach, FL)** has no Operating or Planned units in
  this vintage (17.6 MW in the Retired sheet only) — no effect.

## Anchor — the important caveat

**No single published SERC-by-fuel nameplate anchor exists.** NERC's
Long-Term Reliability Assessment publishes SERC assessment-area
(SERC-Central / Southeast / East / Florida Peninsula) figures as
anticipated/prospective *capability* against peak load, not nameplate
by fuel, and its assessment areas do not map one-to-one onto this BA
cut (NERC's areas split the Carolinas differently and report on a
summer-capability basis). So, as with MISO, the anchor is the
**EIA-860M Operating-sheet snapshot, adjusted to Dec 31, 2025**
(minus units in service Jan–Sep 2026: 3,190.5 MW, 49 units; plus
Retired-sheet actual retirements in 2026: 9.8 MW, 4 units), nameplate
MW, all statuses. It is **EIA-derived, stated explicitly — not a
NERC/SERC publication.**

Definitional gap, stated plainly: the DOE's Jul 2025 grid-reliability
report (built on NERC ITCS data) puts SERC's 2024 *peak load* at
193,654 MW across its four assessment areas. The EIA nameplate anchor
(274,843.4 MW) runs ~81 GW above that peak — expected, and not an
error: nameplate counts solar at full DC/AC rating (27.2 GW), standby
and out-of-service units, and the reserve margin itself. The EIA
snapshot's own net-summer figure for the same fleet is 255,855.7 MW.
Do not mix the nameplate anchor with NERC capability or peak figures.

## Trailing 2016–2025 — reconstructed, estimated

No published by-fuel history exists, so the trailing is
**reconstructed from EIA unit-level data**: for year Y, Operating-sheet
units with Operating Year ≤ Y, plus Retired-sheet units with Operating
Year ≤ Y < Retirement Year. Planned Retirement Year is deliberately
NOT used. The reconstruction **reproduces the anchor exactly at 2025**
— total, by fuel, and by subregion (asserted in the build). Shape:
2016 254,550.7 → 2025 274,843.4 MW; the 2023–2024 steps (+6,428.2,
+4,855.2) carry Plant Vogtle Units 3 (Jul 2023) and 4 (Apr 2024),
~1,117 MW each, inside SOCO. Labelled estimated in every output row.

## Changelog (EIA-860M Sep 2026, BA in the SERC cut)

Additions = in service Jan–Sep 2026 (49 units, 3,190.5 MW) + Planned
sheet (200 units, 22,732.9 MW). Only ~6,154 MW of the planned pipeline
is under construction or construction-complete — and, uniquely for
this region, the Planned sheet stops almost entirely at 2030.
Retirements = actual 2026 (4 units, 9.8 MW) + planned 2026–2036
(85 units). No blanket retirement-delay override: PJM's
coal-delay scenario was PJM-only. Overlap guards verified at 0.

Largest forward additions (v1, EIA): Pepper Hammock Solar + Storage
GA 2,100.0 MW solar (2029, L, plus 400 MW battery); Kingston TN gas
1,830.6 (2027 — the CC + 16 aero CTs replacing Kingston coal);
Cumberland TN gas 1,555.6 (paired blocks EIA dates 2029/2034 — stale,
see v2); Yates GA gas 1,448.4 (2027); Smarr CC GA 804.0 (2029);
Mill Creek (KY) gas 740.0 (2027); Shady Hills CC FL 612.0 (2026).
Largest retirements: Cumberland coal 2,600.0 (2028/2034 — reversed by
TVA in Feb 2026, see v2); Kingston coal 1,700.0 (2027/2034 — under
reversal study, see v2); Crystal River FL coal 1,478.4 (2034);
Shawnee KY coal 1,400.0 (2033); Winyah SC coal 1,275.8 (2030 —
delayed to 2034, see v2); Gallatin TN coal 1,255.2 (2031);
Victor J. Daniel Jr MS coal 1,096.6 (2027 — delayed to mid-2030s,
see v2); Marshall NC 2,119.0 across coal/gas-coded dual-fuel rows
(2028/2033).
Note: EIA splits several dual-fuel units into paired coal-coded and
gas-coded generator rows of equal MW (Marshall is the large case;
Belews Creek's two units, 2,491.2 MW, are coded gas outright). The
totals are right; the fuel split at those plants follows EIA's coding.

## Files

- `build_stack.py` — the build (asserts reproduction + subregional sums).
- `serc_capacity_plants.csv` — unit-level forward changelog (249
  additions + retirements in and beyond the window).
- `serc_capacity_stack.csv` — SERC total stack, long format (year × fuel).
- `serc_capacity_stack_by_subregion.csv` — per-subregion stack.
- `serc_capacity_changelog.csv` — forward changelog (year × fuel).
- `serc_capacity_changelog_by_subregion.csv` — changelog by subregion.
- `summary.json` — anchor, cross-checks, trailing, forward totals,
  BA diagnostics, file list.
- `01_stacked_area.png`, `02_net_change_forward.png`,
  `03_subregions_stacked.png`, `04_subregional_totals.png` — charts.
- `raw/eia860m_sep2026.xlsx` — EIA-860M Sep 2026 vintage (same file as
  the PJM/MISO stacks).

## What v1 is not (v2 scope)

EIA-only. Per the standing rule, EIA is fairly good for a snapshot of
what is currently online but NOT reliable for larger gas/power plants
in the forward pipeline — and in SERC it is unusually weak forward:
the Planned sheet contains *nothing* for Duke Energy's Person County
or Marshall gas builds, Georgia Power's PSC-certified 9,885 MW
portfolio, the certificated 2,180 MW Canadys CC, or FPL's battery
build, and it carries TVA coal retirements that TVA reversed in
Feb 2026. v2 corrects the largest items from online sources, each
with a source, logged in `research_log.md`. v1 files are never
overwritten by v2.
