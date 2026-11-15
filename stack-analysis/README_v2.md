# PJM generation capacity stack v2 — manual corrections (2026-11-14)

v2 = v1 + manual corrections. **v1 files are untouched.** The anchor, the trailing
history (2016–2025) and the RMR override are unchanged. PJM level only, no
regionalization. Built by `build_stack_v2.py` from the v1 CSVs plus the 32
adjustments in `manual_adjustments.csv` (evidence in `research_log.md`).

**Correction 2026-11-14 (evening):** Cayuga Energy Complex (1,476 MW gas)
removed from v2 — verified MISO, not PJM. All figures below are the corrected ones.


## What changed vs v1

| | v1 | v2 | Change |
|---|---:|---:|---:|
| Forward additions 2026–2036 (MW) | 29,818.3 | 41,883.8 | +12,065.5 |
| Forward retirements 2026–2036 (MW) | 12,367.7 | 22,916.8 | +10,549.1 |
| Forward net 2026–2036 (MW) | +17,450.6 | +18,967.0 | +1,516.4 |
| Stack total 2026 (MW) | 207,146.8 | 207,119.4 | −27.4 |
| Stack total 2029 (MW) | 222,607.3 | 220,560.1 | −2,047.2 |
| Stack total 2030 (MW) | 223,240.7 | 223,327.9 | +87.2 |
| Stack total 2036 (MW) | 219,875.4 | 221,391.8 | +1,516.4 |

Net change by fuel (v2 minus v1, MW): Natural Gas +8,517.4, Nuclear +835.0,
Coal −6,723.4, Solar −610.0, Oil −502.6, all other fuels 0. Headline by fuel,
forward 2026–2036 in v2:
gas additions 19,990 MW (v1: 8,150), gas retirements 8,877 MW (v1: 5,554),
gas net +11,113 MW (v1: +2,596); coal retirements 12,663 MW (v1: 5,939);
nuclear additions 835 MW (Crane restart, v1: 0); solar additions 14,673 MW
(v1: 15,283).

The shape of the forward stack changes more than the endpoint does:

- **2029 is no longer the only negative net year, and it is much less negative
  in gross terms but the coal cliff moves:** v1 had 6,713 MW retiring in 2029
  (5,939 MW coal). v2 retires 4,569 MW in 2029 (the RMR-delayed coal only —
  Brandon Shores + Wagner move to 2031) but adds the 2031–2032 retirement
  cliffs below.
- **2031 becomes the biggest retirement year (7,565 MW):** the CEJA Illinois
  block (Powerton coal 1,786 + IL gas CTs 2,650 + Fisk/Waukegan oil 372 + Zion
  gas 597 = 5,404 MW) plus Brandon Shores coal 1,370 + Wagner oil 774. 2031 net
  is −350 MW despite 7,215 MW of additions (Shay, Expedition, Maidsville,
  Big Sandy, Montour CT, Rocky Run).
- **2032 becomes a second coal cliff (−3,827 MW net):** Keystone 1,872 +
  Conemaugh 1,951 MW retire on the consent-decree expiry. v1 had essentially
  nothing in 2032.
- **2033–2034 finally have additions (2,800 MW each year):** Cumberland
  (1,500 MW/yr) + Mt. Storm (1,300 MW/yr). v1 had zero additions after 2031 —
  a coverage artifact that v2 only partly fixes (the EIA planned horizon still
  ends in 2031 for everything else).
- **2028–2029 lose the Homer City gas (4,396 MW):** the 2028 total falls
  2,060 MW vs v1 even though new gas is added elsewhere, because the BTM
  exclusion outweighs it in those years.

## The BTM / co-located rule (as instructed)

- If the generator primarily serves on-site load, is behind-the-meter /
  islanded, or its grid connection is only incidental backup/export, its grid
  MW is **0** — excluded entirely.
- Worked example from the user: a 2 GW data center with a 2 GW gas plant and a
  500 MW grid connection shows as **0 MW, not 500 MW**, because the connection
  is entirely accounted for by load.
- If the full load and the generator are both connected to the grid and
  independent (the generator can export to the grid and the load draws from the
  grid independently), reflect the full capacity of the generator.
- If the case cannot be established after checking, classify **Uncertain**,
  keep the v1 MW, and flag it — never silently exclude it.

**Homer City conclusion:** BTM, **0 MW — the full 4,396 MW is excluded**.
The plant is a data-center campus first (~82% of output earmarked for on-site
data centers, power delivered on site). Flagged alternative, NOT counted: the
CEO-quoted ~700–800 MW grid-export split is not locked, no tenant is signed,
and no PJM queue/GIA/CIR figure was found. If a surplus-export reading is
adopted, count 700–800 MW, not 4,396 MW.

Other co-located findings: Crane (TMI-1) is **grid-connected** — Microsoft buys
the output under a PPA, there is no data center at the plant, power is injected
into the PJM grid — so the 835 MW restart is added. Susquehanna/Cumulus is a
front-of-the-meter contract for **existing** output — no new MW. Socrates
(Meta, OH) and Monarch (WV) are behind-the-meter and not in EIA/v1 — no change.
Shippingport (2.7–3.6 GW claimed) is BTM-majority with uncertain MW and no EIA
listing — not added, flagged.

## Threshold and scope

- Focus on units **≥250 MW** (prioritise ≥500 MW), gas first, then other fuels.
  Sub-250 MW units were grouped where they act as one block (the CEJA Illinois
  CT fleets, Forked River, West Lorain).
- **Do not change:** trailing history 2016–2025, the Dec-31-2025 anchor
  (202,424.8 MW), the RMR override (coal retirements scheduled 2026–2028 pushed
  to Jan 2029; 5 units, 4,569 MW). Kincaid is kept at Jan 2029 under that
  instruction even though no Kincaid-specific RMR filing was found — see
  `research_log.md` §4.
- PJM level only; no regionalization.

## Sources and vintages

- Anchor: PJM State of the Market 2025 Annual, Table 12-1, Dec 31, 2025
  (202,424.8 MW) — unchanged from v1.
- Forward base: EIA-860M September 2026 vintage (data as of Sep 30, 2026;
  released Oct 23, 2026), BA = PJM — unchanged from v1.
- Manual corrections: company announcements, PJM deactivation notices and
  continued-operation letters, state PUC filings (IURC, VA SCC, KY PSC, WV PSC,
  PA DEP, OPSB), FERC orders/waivers, DOE §202(c) orders, and reputable trade
  press. Every adjustment names its source with URL and date in
  `manual_adjustments.csv`; the full evidence trail is in `research_log.md`.
  All sources accessed 2026-11-14.
- The EIA-860M file itself (`raw/eia860m_sep2026.xlsx`) was re-checked directly
  to verify nameplate MW and BA for the manual retirement blocks (Keystone,
  Conemaugh, Powerton, Aurora/Rockford/University Park, Fisk, Waukegan, Zion,
  West Lorain, Forked River, Crane) and to confirm that none of the Table B gas
  builds appears in v1 under another name.

## Capacity definition

Same as v1: nameplate MW throughout the changelog, applied to an ICAP anchor.
Manual additions/retirements use EIA nameplate where the unit exists in
EIA-860M, else the company-announced figure. Noted exceptions and ICAP
equivalents are in `research_log.md` §8. The one deliberate exception is Crane
(TMI-1): Constellation's ~835 MW company figure instead of EIA nameplate
980.8 MW (net summer 802.8 MW).

## Files (v2)

- `manual_adjustments.csv` — 33 rows, one per manual change: plant, unit, fuel,
  v1 MW/date, v2 MW/date, change type, reason, classification, source URL/date.
- `pjm_capacity_plants_v2.csv` — 611 rows (v1's 575 + 36 new): v1 columns kept
  plus `v2_mw_nameplate`, `v2_effective_date`, `v2_status`, `v2_type`,
  `manual_change`, `manual_change_note`. Homer City (14 rows) and Bellflower
  (1 row) have `v2_type = excluded` and `v2_mw_nameplate = 0`.
- `pjm_capacity_stack_v2.csv` — year 2016–2036 × fuel (+ Total), same layout as v1.
- `pjm_capacity_changelog_v2.csv` — additions/retirements/net by year × fuel, 2026–2036.
- `summary_v2.json` — v1 vs v2 totals, net change by fuel and year, BTM MW
  excluded, largest manual changes, flagged candidates not added.
- `research_log.md` — per-project findings, sources, what was checked, what was
  not found, confidence for each call, and the reconciliation decisions.
- `build_stack_v2.py` — reproducible build (reads the v1 CSVs, applies the
  adjustments, writes all v2 files and charts).
- `01_stacked_area_v2.png` — v2 stack 2016–2036.
- `02_net_change_forward_v2.png` — v2 forward net change by fuel/year.
- `README_v2.md` — this file.

## Limitations (v2-specific; v1 limitations in README.md still apply)

- Planned ≠ built; dates slip. The largest v2 additions are the least certain:
  Cumberland and Mt. Storm still need SCC/DEQ approvals; Montour CT has no
  CPCN/FID; Expedition and Big Sandy have no offtake/CPCN yet.
- **2031–2032 retirement dates are floors, not firm dates.** The CEJA Illinois
  block is dated to the end of PJM's requested reliability extension
  (31 May 2031); PJM reassesses before each delivery year and the units could
  run longer. Keystone/Conemaugh at Dec 2032 is a consent-decree-expiry planning
  assumption, not a filed deactivation; they could be extended again.
- **The Homer City 0 MW call is the single largest judgement in v2.** If the
  surplus-export reading is adopted instead, add 700–800 MW of gas in 2028–29.
- **Cayuga REMOVED 2026-11-14:** verified MISO, not PJM (Duke IURC testimony
  Cause No. 46193; MISO queue filings). Its 1,476 MW of gas (738 MW in 2029,
  738 MW in 2030) is out of v2; 2029 is now a small negative net year (−297 MW)
  without Cayuga Unit 1.
- **Nuclear uprates (890 MW Constellation–Google + 433 MW Vistra–Meta) are NOT
  in v2** — the PJM share is unpublished. They are the largest known upside.
- **Sammis–South Canton (1,300 MW, queue-only) and Shippingport are NOT in v2.**
- The EIA planned horizon still ends in 2031 for everything except the manual
  additions; 2035–2036 have no additions in v2 either. Do not read that as a
  forecast — it is a coverage limit.
- Small-unit (<250 MW) retirements beyond the CEJA/Forked River/West Lorain
  blocks were not exhaustively swept; the PJM deactivation page lists many
  sub-10 MW landfill-gas/solar/battery items that are immaterial to a ~200 GW stack.
- Nameplate vs ICAP: same approximation as v1, now extended to the manual
  blocks (ICAP equivalents noted in the research log).
