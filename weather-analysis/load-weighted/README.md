# PJM winter HDD / cold-snap analysis — load-weighted (zonal peak load)

Same cleaned data and same definitions as the equal-weighted version
(`../hdd_coldsnap.py`, NOAA GHCN-Daily, 7 stations, winters 1996–2025,
Dec–Jan–Feb; HDD = max(0, base − Tavg) per station-day; cold snaps =
consecutive-day runs with Tavg < 20 °F / < 32 °F), but every cross-station
average is weighted by PJM zonal peak load instead of 1/7 each. No
equal-weighted file was modified; all outputs live in this directory.

## Weights — zonal winter peak load

Source: **PJM Load Forecast Report, January 2026** (posted Jan 14, 2026),
Table B-2 "Winter Peak Load (MW) and Growth Rates for Each PJM Zone and
Geographic Region (2025/26 – 2045/46)", column **25/26** — the
weather-normalised (WN) forecast winter peak, non-coincident, unrestricted.

- Tables workbook:
  https://www.pjm.com/-/media/DotCom/planning/res-adeq/load-forecast/2026-load-report-tables.xlsx
- Report PDF:
  https://www.pjm.com/-/media/DotCom/library/reports-notices/load-forecast/2026-load-report.ashx

Winter peak (not summer) was used, per the brief. The 25/26 column is a
weather-normal forecast — chosen over the metered 24/25 actuals because
winter 2024/25 was an extreme-weather winter (PJM metered RTO peak
143,319 MW vs 137,670 MW weather-normal forecast), so the actuals would
bake one winter's weather into the weights. Sensitivity below shows the
choice barely matters.

| Station | PJM zone | Winter peak 25/26 (MW) | Weight |
|---|---|---:|---:|
| Richmond Intl, VA | DOM (Dominion) | 24,779 | 0.2985 |
| Columbus, OH | AEP | 23,423 | 0.2821 |
| Chicago O'Hare, IL | COMED | 15,011 | 0.1808 |
| Philadelphia Intl, PA | PECO | 6,619 | 0.0797 |
| Baltimore/Washington Intl, MD | BGE | 5,855 | 0.0705 |
| Washington Reagan, DC | PEPCO | 5,353 | 0.0645 |
| Pittsburgh Intl, PA | DLCO (Duquesne Light) | 1,982 | 0.0239 |
| **Total, 7 zones** | | **83,022** | **1.0000** |

**Coverage:** the 7 zones are **58.3% of the sum of all 21 PJM zones'
non-coincident 2025/26 winter peaks** (142,390 MW). The weights are
relative shares among these 7 zones only, not of PJM — the other 14 zones
(AE, APS, ATSI, DAYTON, DEOK, DPL, EKPC, JCPL, METED, PENLC, PL, PS,
RECO, UGI, OVEC) are unrepresented. The 7-zone sum is 60.3% of the
coincident RTO forecast peak (137,670 MW), but that is not apples-to-apples:
zonal peaks are non-coincident, so the sum of zonal peaks exceeds the
coincident RTO peak.

## Headline results (load-weighted vs equal-weighted)

| Metric | Equal-weighted | Load-weighted | Change |
|---|---:|---:|---:|
| Winter mean Tavg | 35.3 °F | 35.38 °F | +0.1 °F |
| HDD65 / winter | 2,682 | **2,674** | −8 (−0.3%) |
| HDD60 / winter | 2,234 | 2,227 | −7 (−0.3%) |
| HDD65 / day | 29.72 | 29.63 | −0.09 |
| Coldest winter | 2003 (3,114) | 2003 (3,076) | same winter, −38 |
| Warmest winter | 2023 (2,274) | 2023 (2,271) | same winter, −4 |
| HDD65 decadal: 1996–2005 / 2006–2015 / 2016–2025 | 2,730 / 2,802 / 2,515 | 2,721 / 2,788 / 2,514 | −9 / −14 / −1 |
| Sub-20 °F events / winter | 3.23 | 3.29 | +1.8% |
| Sub-20 °F mean longest run | 3.19 days | 3.36 days | +5.3% |
| Sub-20 °F days/yr in ≥3-day runs | 4.95 | 5.47 | **+10.5%** |
| Sub-20 °F days/yr in ≥5-day runs | 2.59 | 2.90 | **+12.0%** |
| Sub-32 °F events / winter | 8.24 | 8.05 | −2.2% |
| Sub-32 °F mean longest run | 10.87 days | 11.19 days | +3.0% |
| Sub-32 °F days/yr in ≥3-day runs | 25.56 | 25.82 | +1.0% |
| Longest single-station sub-20 run | 15 days (Chicago, 2007) | 15 days (Chicago, 2007) | unchanged |
| Longest pooled sub-20 run | 12 days (2018) | 9 days (2018) | −3 days |
| Longest pooled sub-32 run | 23 days (2007) | 23 days (2004) | same length, different winter |

Monthly HDD65 per winter month: Jan 998.5 (EQ 1,001.2), Dec 855.6 (EQ 855.7),
Feb 819.8 (EQ 825.0).

**Why HDD barely moves but cold snaps move more:** the big weights sit on
both ends — warm Richmond (DOM, 0.298, only 2,165 HDD65/winter) and
mid-cold Columbus (AEP, 0.282, 2,908) — which roughly cancel in the HDD
total, while cold Pittsburgh (2,988 HDD) is nearly zero-weighted (0.024).
For cold snaps the cancellation fails: Chicago (7.2 sub-20 events/winter,
mean longest run 7.4 days, 15.5 days/yr in ≥3-day runs) is upweighted
0.143 → 0.181 and Columbus (4.5 events, 4.6-day mean longest) is
upweighted to 0.282, which more than offsets Pittsburgh's downweighting.
Richmond contributes almost no sub-20 cold at all (0.8 events/winter),
so its 0.298 weight mostly dilutes the average rather than adding cold.

**The recent-decade story is unchanged:** HDD65 falls ~10% in 2016–2025
vs 2006–2015 under either weighting (LW −9.8%, EQ −10.3%).

## Sensitivity — weight vintage barely matters

Headline mean HDD65/winter under three defensible weight sets:

| Weight set | HDD65 / winter |
|---|---:|
| Primary: B-2 forecast 25/26 (weather-normal) | 2,674.3 |
| Metered 24/25 actuals (extreme winter) | 2,674.0 |
| Table F-3 weather-normalised 24/25 loads | 2,680.3 |

Range is 6 HDD (0.2%). The weights are stable because the zonal shares
hardly change between vintages (largest shift: DOM 0.298 → 0.288).

## Limitations and mapping uncertainty

- **DOM / Richmond is the biggest caveat.** Dominion is the largest weight
  (0.298) and Richmond is the warmest station (2,165 HDD65), but most of
  DOM's load — and its growth, including Northern Virginia data centers —
  sits in colder Northern Virginia, not Richmond. Attaching the whole DOM
  weight to Richmond likely biases the load-weighted HDD and cold-snap
  figures low. A Northern Virginia station (e.g. Dulles) would be the fix
  if DOM is to be represented properly.
- **AEP is geographically broad** (Ohio, West Virginia, Virginia, Kentucky,
  Tennessee, Indiana, Michigan); Columbus is central but the zone spans
  several climate bands. Same direction of error as DOM, smaller.
- **Pittsburgh is effectively dropped** (weight 0.024 vs 0.143 equal): the
  Duquesne zone is small, so the second-coldest station barely counts.
  That is correct for a load weight, but it means the result is insensitive
  to western-Pennsylvania cold.
- **Non-coincident zonal peaks.** PJM publishes winter peaks by zone as
  non-coincident (each zone's own peak hour); a coincident-peak weighting
  would shift shares slightly toward zones that peak with the RTO. No
  winter coincident-peak table is published in the forecast tables (Table
  B-10 is summer only), so this could not be computed from the same source.
- **Single-vintage weights for a 30-year record.** The 2025/26 shares are
  applied to all winters 1996–2025. Zonal shares drifted over that period
  (notably DOM's data-center growth is recent); a time-varying weight
  would be more accurate but is not available in one table.
- **Winter peak ≠ winter energy.** Peak-load weights proxy for load
  exposure; an energy-weighted (GWh) version would weight zones slightly
  differently. Table E-1 (annual net energy by zone) would be the source
  if that variant is wanted.
- All temperature-side limitations of the equal-weighted version carry
  over unchanged (equal station coverage is 100%, TAVG definition,
  no homogenisation).

## Files

- `load_weighted_hdd_coldsnap.py` — the analysis script (reproduce with
  `python3 load_weighted_hdd_coldsnap.py` from this directory)
- `load_weighted_hdd_coldsnap_summary.json` — headline numbers + weights
  + equal-weighted comparison + sensitivity
- `load_weighted_hdd_yearly.csv` — per-winter HDD65/HDD60/mean Tavg,
  load-weighted and equal-weighted side by side
- `load_weighted_coldsnap_by_station_winter.csv` — per-station, per-winter
  cold-snap runs (same per-station values as the equal-weighted file;
  weights do not change per-station runs)
- `load_weighted_coldsnap_yearly.csv` — per-winter load-weighted and
  equal-weighted cold-snap aggregates + load-weighted pooled runs
- `01_hdd_by_winter_lw_vs_eq.png` — HDD65 by winter, LW vs EQ
- `02_coldsnap_lw_vs_eq.png` — sub-20 °F cold snaps, LW vs EQ
- `03_weights_and_station_hdd.png` — weights vs equal weight; per-station
  HDD65 and its contribution to the load-weighted total
