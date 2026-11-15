# ERCOT capacity stack — v2 (EIA + manual corrections)

Built 2026-11-15 from v1 (see `README.md`) by applying 6 named manual
adjustments (167 row-level changes), each with an online source, logged
in `research_log.md` and `manual_adjustments.csv`. Reproduce with
`python3 build_stack_v2.py` (it verifies v1 reproduces, applies the
corrections, and asserts the corrected yearly flow deltas on every
run). v1 files are untouched.

## Headline figures (v2 vs v1)

| | v1 | v2 | Change |
|---|---|---|---|
| 2036 total | 270,437.2 MW | **254,113.5 MW** | **−16,323.7 MW** |
| Forward additions 2026–2036 | 97,654.2 MW (631 units) | 82,875.4 MW (472 units) | −14,778.8 MW |
| Forward retirements 2026–2036 | 1,483.5 MW (7 units) | 3,028.4 MW (9 units) | +1,544.9 MW |
| Forward net 2026–2036 | +96,170.7 MW | +79,847.0 MW | −16,323.7 MW |

Delta by fuel (net): Gas **−10,310.8 MW**; Nuclear **−4,468.0 MW**;
Coal **−1,544.9 MW**; all other fuels 0. The v2 stack ends 2036 at
254,113.5 MW (the pipeline still runs out after 2032 in EIA, so
2033–2036 are flat, as in v1). Year-by-year v2−v1 totals: 2026 +7.6;
2027 −1,279.7; 2028 −3,023.7; 2029 −3,023.7; 2030 −11,855.7; 2031
−14,089.7; 2032–2036 −16,323.7. **Solar leads the v2 net change**
(+39,947.6 MW of additions, no retirements), followed by Battery
Storage (+29,434.2 MW net) and Gas (+7,383.1 MW net).

## What changed (6 adjustments)

| # | Plant | Change | MW | Confidence |
|---|---|---|---|---|
| A | Legend Power Station, TX | EXCLUDE (Jul 2028; EIA BA code corrected) | −754.0 | High |
| B | Project Matador Gas Plant (PMG), TX | EXCLUDE — BTM (2027/2028/2030) | −11,679.3 | High |
| C | Project Matador Nuclear, TX | EXCLUDE — BTM (2031/2032) | −4,468.0 | High |
| D | J K Spruce Unit 2, TX | Fuel switch coal→gas (Dec 2028) | 0 net (922.5) | Medium-High |
| E | Coleto Creek, TX | Repower coal→gas (Dec 2026) | +7.6 net (622.4 out / 630.0 in) | Medium-High / Medium |
| F | Rayburn Energy Station II, TX | ADD (Dec 2028) | +570.0 | Medium |

Notes and flags:
- **Legend (A)** is the mirror image of MISO v2 adjustment C: EIA codes
  the plant ERCO, but Entergy Texas is a MISO utility and PUCT Docket
  56693 states MISO determines Legend's transmission upgrades. It is
  counted in the MISO stack, not here.
- **Matador (B + C)** is the dominant correction: 16,147.3 MW that EIA
  files under ERCO is Fermi America's HyperGrid campus in Carson
  County (Amarillo / Texas Panhandle — SPP territory served by Xcel,
  not ERCOT), designed as a **behind-the-meter private grid** for
  co-located AI data centres with no interconnection queue position.
  Under the standing BTM rule it counts as 0 MW of grid addition; the
  ERCO BA code is also wrong for the location. Both grounds are logged.
- **Spruce (D) and Coleto Creek (E)** are fuel switches EIA misses
  entirely — EIA carries no retirement and no gas addition for either
  unit. Coleto Creek's gas side is booked at Vistra's ~630 MW
  (GEM lists 600 MW; the coal side is the EIA nameplate 622.4 MW).
- **Rayburn II (F)** is a finalized Texas Energy Fund loan project
  (PUCT, Jun 2026) absent from the EIA Planned sheet; the Dec 2028
  month is a placeholder, the year is PUCT's.
- **BTM scan finding (explicit, per the brief):** Texas has extensive
  announced data-center co-located generation. One large BTM campus
  was inside the EIA cut (Matador — excluded). The other confirmed
  BTM build, Crusoe/Stargate Abilene (~360 MW on-site gas, permitted
  for on-site use only), is **not in EIA at all** and is therefore
  correctly absent from both v1 and v2; it is logged as a flagged
  candidate, not added. Sandow Lakes was checked and is **not** BTM:
  it holds an ERCOT interconnection study position (1,291.6 MW) as a
  grid plant; the neighbouring data centres are unconfirmed and, if
  built, separately sited. No other large EIA forward plant was found
  to be co-located BTM.

## Files (v2; v1 files untouched)

- `build_stack_v2.py` — the v2 build.
- `manual_adjustments.csv` — 167 row-level changes with sources and
  confidence (162 exclusion rows are the 157 Matador gas units, 4
  Matador nuclear units and Legend; plus 5 added rows).
- `ercot_capacity_plants_v2.csv` — unit-level changelog (645 rows:
  v1 640 + 5 new), with `v2_*` columns and `manual_change` flags;
  excluded rows carry `v2_type = excluded`.
- `ercot_capacity_stack_v2.csv` — ERCOT stack (year × fuel).
- `ercot_capacity_changelog_v2.csv` — forward changelog (year × fuel).
- `summary_v2.json` — v1/v2 forward totals, deltas, yearly totals,
  largest changes, flagged candidates not added.
- `research_log.md` — evidence, sources, and confidence per adjustment;
  KEEP list; unverified items; candidates not proposed.
- `01_stacked_area_v2.png`, `02_net_change_forward_v2.png` — charts.
- `README.md` — v1 documentation (anchor caveat, trailing method,
  region cut, changelog).

## Open items (not in v2)
WattBridge/Continental 452 MW TxEF loan (Oct 2026, post-vintage);
Anthropic/Caterpillar 1,700 MW BTM generator deal (no plant/date);
Crusoe/Stargate Abilene ~360 MW BTM gas (operating, not in EIA);
Liberty Thermal + Bullock Gas 2,800 MW (ERCOT queue only, 2032);
Vast Sands Power's unverified identity as Vistra's 860 MW Permian
Basin project; Fermi capacity claims beyond EIA (up to 11–17 GW).
See `research_log.md` and `summary_v2.json`.
