# CAISO capacity stack — v1 (EIA-only)

Replicates the PJM/MISO new-builds-and-retirements (NBR) stack for CAISO.
Built 2026-11-15. Mirrors the PJM/MISO conventions: trailing + forward
10-year stack 2016–2036 by fuel (Coal, Natural Gas, Nuclear, Hydro,
Pumped Storage, Wind, Solar, Oil, Battery Storage, Other), nameplate MW
throughout, anchor Dec 31, 2025, forward = anchor + changelog. See
`build_stack.py`; reproduce with `python3 build_stack.py` (it asserts
the trailing reproduction and the anchor + cumulative changelog identity
on every run).

## Headline figures (v1)

| | 2025 anchor | 2036 | Change 2026–2036 |
|---|---|---|---|
| CAISO total | 94,392.9 MW | 123,125.6 MW | +28,732.7 MW |

Forward 2026–2036 (EIA-860M only): additions **31,776.7 MW** (287 units),
retirements **3,044.0 MW** (23 units), net **+28,732.7 MW**.
Additions by fuel: Battery Storage 12,366.0; Solar 10,737.7; Wind 7,545.0;
Pumped Storage 600.0; Other 519.0; Hydro 8.1; Natural Gas 0.9;
Coal/Nuclear/Oil 0. There are effectively **no new gas additions** in the
CAISO forward pipeline — the build is storage, solar and wind.
Retirements by fuel: Natural Gas 2,952.1 (97% of MW — almost all of it
the once-through-cooling fleet, see below); Wind 87.0; Other 2.9; Oil 2.0.
Peak build years: 2026 (+9,290.8 MW net), 2027 (+7,252.9), 2028
(+6,168.1). The stack rises monotonically to 123,125.6 MW in 2033 and is
flat thereafter — EIA has no planned CAISO additions after 2033.

Anchor by fuel (Dec 31, 2025, nameplate): Natural Gas 32,259.1; Solar
24,959.4; Battery Storage 15,777.3; Hydro 6,740.3; Wind 6,343.8; Other
3,410.6 (of which geothermal ~2.2 GW, in the EIA snapshot); Nuclear
2,323.0 (Diablo Canyon, the state's only nuclear plant); Pumped Storage
2,077.6; Oil 439.3; Coal 62.5 (a single small unit — CAISO is effectively
coal-free).

## Anchor — the important caveat

**The anchor is EIA-derived, stated explicitly — not a CAISO
publication.** It is the **EIA-860M Operating-sheet snapshot, adjusted
to Dec 31, 2025** (minus units in service Jan–Sep 2026: 6,348.3 MW, of
which SunZia Wind in New Mexico is 3,650.2 MW; plus Retired-sheet actual
retirements in 2026: 0.0 MW — no CISO unit actually retired in Jan–Sep
2026), nameplate MW, all statuses.

CAISO publishes installed-capacity figures on a **Net Qualifying
Capacity (NQC) / resource-adequacy basis, which is NOT nameplate**:
wind and solar are heavily derated to their expected peak-hour
contribution, and non-RA resources — including the Strategic
Reliability Reserve once-through-cooling units — are excluded. Those
published figures are used here as cross-checks only:

- CAISO *2026 Summer Loads and Resources Assessment*: total modelled
  capacity **84,153 MW as of Sep 2026** (existing RA-eligible resources
  from the Feb 12, 2026 NQC list plus expected additions). That runs
  ~10.2 GW below the EIA nameplate anchor of 94,392.9 MW — a
  definitional gap, not an error in either figure: NQC derating of
  ~25 GW of solar and ~6.3 GW of wind, exclusion of ~1.8 GW of
  non-operating-status units in the EIA snapshot (OA/OS/SB), exclusion
  of the SRR emergency-only OTC fleet, and scope differences (the EIA
  cut includes out-of-state CISO resources in AZ/NV at nameplate).
  Do not mix the two bases.
- EIA Operating snapshot Sep 30, 2026 (unadjusted): 100,741.2 MW
  nameplate / net summer lower; OP-only 98,910.1 MW nameplate.

## Trailing 2016–2025 — reconstructed, estimated

No published nameplate-by-fuel history exists, so the trailing is
**reconstructed from EIA unit-level data**: for year Y, Operating-sheet
units with Operating Year ≤ Y, plus Retired-sheet units with Operating
Year ≤ Y < Retirement Year. Planned Retirement Year is deliberately NOT
used (it reflects plans as of Sep 2026, not history). The reconstruction
**reproduces the anchor exactly at 2025** (asserted in the build). Shape:
2016 68,748.8 → 2019 66,884.5 (the OTC/gas retirement trough: San Onofre
aftermath, Encina, El Segundo and other coastal retirements) → 2025
94,392.9 MW, with the steep 2020–2025 climb driven by solar and the
battery build-out (battery goes from negligible in 2019 to 15,777.3 MW
at the anchor). Labelled estimated in every output row.

## Region cut — BA = CISO, not the state of California

**California is NOT all CAISO.** The BA filter (Balancing Authority Code
= CISO) defines the footprint. California generating capacity under
other BAs, excluded from this stack (EIA Operating snapshot, CA-state
plants, nameplate MW):

| Excluded BA | Who | MW |
|---|---|---|
| LDWP | Los Angeles Dept. of Water & Power (incl. Scattergood, Haynes, Harbor steam plants) | 8,639.9 |
| BANC | Balancing Authority of Northern California — SMUD and Modesto Irrigation District | 5,719.2 |
| IID | Imperial Irrigation District | 2,324.0 |
| TIDC | Turlock Irrigation District | 807.5 |
| WALC | Western Area Power Admin., Lower Colorado | 127.9 |
| PACW | PacifiCorp West (far northern California) | 31.2 |
| NEVP | NV Energy (slivers on the CA border) | 18.6 |
| **Total excluded CA-state capacity** | | **17,668.3** |

Conversely, the CISO footprint reaches outside California, correctly:
AZ 3,004.2 MW (Agua Caliente/Mesquite solar, Desert Star gas), NV
1,756.4 MW (Copper Mountain/Silver State solar, geothermal), NM
3,650.2 MW (SunZia Wind, in service May 2026 — in the forward changelog,
not the anchor). One data error rides along with the BA filter and is
kept for consistency: a 2.0 MW unit in Plainville, **Connecticut**
("AmericoldCA") coded BA=CISO. Immaterial; flagged here so it is not a
surprise in the plants file.

## Changelog (EIA-860M Sep 2026, BA=CISO)

Additions = in service Jan–Sep 2026 (79 units, 6,348.3 MW — SunZia Wind
3,650.2 MW of it) + Planned sheet (208 units, 25,428.4 MW, 2026–2033).
Of the planned pipeline, only **11,985.1 MW is under construction or
construction-complete** (U 5,167.2 + V 4,458.6 + TS 2,359.3);
**13,443.3 MW is not yet under construction** (T 3,991.5 + L 3,263.5 +
P 6,188.3) — over half the forward pipeline is paper, which is what v2
spot-checks at the large end.
Retirements = actual 2026 (0 units, 0.0 MW) + planned 2026–2036
(23 units, 3,044.0 MW). No blanket retirement-delay override: the PJM
coal-delay-to-Jan-2029 override was a user-directed scenario, not a
general rule. Overlap guards verified at 0 (no unit double-counted
between in-service-2026 and planned-2026, or retired-2026 and
planned-retirement-2026).

Largest forward additions (v1, EIA): SunZia Wind NM 3,650.2 MW (2026,
in service — two units, 2,561.2 + 1,089.0); Chokecherry and Sierra Madre
Wind WY 3,550.5 MW in four units (Dec 2031–Dec 2033, U — Wyoming wind
delivered to CAISO via TransWest Express); Darden I–IV Solar CA
4×342.7 MW solar + 4×303.7 MW battery (Mar 2028, T — the Darden Clean
Energy Project, see research log); Bellefield 2 Solar & Storage CA
500.0 MW solar + 500.0 MW battery (Dec 2026, V); Grace Energy Center CA
500.0 MW solar + 500.0 MW battery (2027, L); Pelicans Jaw Hybrid Solar
CA 440.0 MW (2027, TS). Largest retirements: Ormond Beach Units 1/2
806.0 MW each (Jan 2027 in EIA — retimed in v2); AES Alamitos Units
3/4/5, 310.0 + 310.0 + 495.0 MW (Dec 2026); AES Huntington Beach Unit 2,
218.0 MW (Dec 2026); Solano Wind 87.0 MW (2031).
Note: **EIA shows no planned retirement at all for Diablo Canyon
nuclear (2,323.0 MW)** — that is the single largest known error in v1
and is corrected in v2 (SB 846 authorises operation only to Oct
2029/Oct 2030). The plants file also lists a handful of small planned
retirements beyond 2036 — outside the changelog window.

## Files

- `build_stack.py` — the build (asserts trailing reproduction + the
  anchor + cumulative changelog identity).
- `caiso_capacity_plants.csv` — unit-level forward changelog (287
  additions + all listed retirements; retirements beyond 2036 also listed).
- `caiso_capacity_stack.csv` — CAISO stack, long format (year × fuel).
- `caiso_capacity_changelog.csv` — forward changelog (year × fuel).
- `summary.json` — anchor, cross-checks, trailing, forward totals,
  diagnostics, file list.
- `01_stacked_area.png`, `02_net_change_forward.png` — charts.

## What v1 is not (v2 scope)

EIA-only. Per the standing rule, EIA is fairly good for a snapshot of
what is currently online but NOT reliable for larger gas/power plants in
the forward pipeline — v2 manually checks the largest forward plants
from online sources (each adjustment with a source, logged in
`research_log.md`). Known v2 items: Diablo Canyon (EIA retirement dates
vs the SB 846 extension to 2029/2030 — in fact EIA has no retirement at
all); the once-through-cooling gas plants whose retirements California
repeatedly delayed via the State Water Board / Strategic Reliability
Reserve (Alamitos, Huntington Beach, Ormond Beach — Scattergood and
El Segundo checked and found outside scope, see research log); the
largest battery and solar+battery hybrid additions (Darden, Bellefield,
Grace); Chokecherry/SunZia out-of-state wind attribution and timing;
and a scan for large projects EIA omits entirely (Eagle Mountain pumped
storage) and for behind-the-meter data-center generation. v1 files are
never overwritten by v2.
