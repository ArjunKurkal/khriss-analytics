# NYISO capacity stack — v2 (EIA + manual corrections)

Built 2026-11-15 from v1 (see `README.md`) by applying 3 named manual
adjustments (36 row-level changes), each with an online source, logged
in `research_log.md` and `manual_adjustments.csv`. Reproduce with
`python3 build_stack_v2.py` (it verifies v1 reproduces, applies the
corrections, and asserts the corrected yearly flow deltas on every
run). v1 files are untouched.

## Headline figures (v2 vs v1)

| | v1 | v2 | Change |
|---|---|---|---|
| 2036 total | 53,605.0 MW | **52,401.0 MW** | **−1,204.0 MW** |
| Forward additions 2026–2036 | 8,013.9 MW (157 units) | 8,013.9 MW (157 units) | 0 |
| Forward retirements 2026–2036 | 41.6 MW (22 units) | 1,245.6 MW (58 units) | +1,204.0 MW |
| Forward net 2026–2036 | +7,972.3 MW | +6,768.3 MW | −1,204.0 MW |

Delta by fuel (net): Natural Gas **−1,204.0 MW**; all other fuels 0.
All three adjustments are gas retirements EIA misses. The v2 stack
peaks in 2031–2034 at 52,401.7 MW and ends 2036 at 52,401.0 MW.
Year-by-year v2−v1 totals: 2026 0; 2027–2028 −532.0; 2029–2036
−1,204.0. Solar leads the v2 net change by fuel (+4,464.9 MW net),
then Wind (+2,697.5) and Battery Storage (+840.3); Natural Gas is the
only fuel with a negative net change (−1,219.8 MW: 5.5 added,
1,225.3 retired).

## What changed (3 adjustments)

| # | Plant | Change | MW | Confidence |
|---|---|---|---|---|
| A | Danskammer Units 1–4, NY | ADD retirement (Jan 2027) | −532.0 | Medium (date is a floor) |
| B | Gowanus Barges 2 & 3, NY | ADD retirement (May 2029) | −320.0 | Medium-High |
| C | Narrows Barges 1 & 2, NY | ADD retirement (May 2029) | −352.0 | Medium-High |

Notes and flags:
- **Danskammer** (A) was noticed for deactivation Aug 1, 2026, was
  required to stay in service (Interim Service Provider) until at
  least Jan 15, 2027 by the Q1/Q2 2026 STARs, and was cleared to
  proceed by the Q3 2026 STAR (Oct 13, 2026) once CHPE demonstrated
  capability. Jan 2027 is the earliest date consistent with that
  record; the exact deactivation date is not yet published.
- **The barges** (B, C) are DEC Peaker Rule units. NYISO's Apr 15,
  2026 Short-Term Reliability Process Report designated them needed
  until **May 1, 2029 — the maximum extension the Peaker Rule
  allows** — and AlphaGen withdrew its deactivation notices to operate
  in the market until then. NYISO's "608 MW" for the four barges is
  summer capability (608.7 MW); nameplate, this stack's basis, is
  672.0 MW.
- **No additions were adjusted.** Every large EIA forward plant that
  was checked — Empire Wind 1 and Sunrise Wind (both survived the
  Apr 2025 and Dec 22, 2025 federal stop-work orders via court
  injunctions and remain on EIA's 2027 dates), Cider Solar, Alle-Catt
  Wind, Excelsior, Mineral Basin and Moonlight Flats (both verified
  as genuine NYISO interconnections from Pennsylvania soil), and the
  largest batteries (NISA 300 MW, NY2 151.5 MW) — matched its online
  evidence at EIA's MW and date. South Fork Wind (130.0 MW EIA
  nameplate; 132 MW publicly) is already operating and in the anchor.
- **Nuclear: no change.** All four upstate units stay; Ginna and Nine
  Mile Point 1 filed subsequent licence renewal to 2049 in 2026. No
  uprate with a published MW/date exists. FitzPatrick's licence
  expires Oct 2034, inside the window — flagged, not retired (see
  open items).
- **Transmission excluded, documented:** Champlain Hudson Power
  Express (1,250 MW, commercial operation May 13, 2026) and Clean
  Path NY (1,300 MW line; Tier 4 contract terminated 2024) are
  transmission, not generation, and are not in the stack. CHPE's
  in-service is nonetheless load-bearing for adjustment A.
- **No BTM exclusion.** The only genuine co-located generation found
  is the existing Greenidge/Vulcan Dresden plant (112.0 MW nameplate,
  NYISO-approved behind-the-meter load up to 64 MW) — an anchor plant,
  not a forward addition, and a grid exporter under a NYISO operating
  agreement, so the standing zero-MW test is not met. No forward
  co-located data-center generation was found; the large new loads
  (e.g. Micron) are grid-served load, not generation.

## Files (v2; v1 files untouched)

- `build_stack_v2.py` — the v2 build.
- `manual_adjustments.csv` — 36 row-level changes with sources and
  confidence.
- `nyiso_capacity_plants_v2.csv` — unit-level changelog (v1 rows plus
  36 added retirements), with `v2_*` columns and `manual_change` flags.
- `nyiso_capacity_stack_v2.csv` — NYISO stack (year × fuel).
- `nyiso_capacity_changelog_v2.csv` — forward changelog (year × fuel).
- `summary_v2.json` — v1/v2 forward totals, deltas, yearly totals,
  largest changes, flagged candidates not added.
- `research_log.md` — evidence, sources, and confidence per
  adjustment; KEEP list; transmission exclusions; BTM finding;
  unverified items; candidates not proposed.
- `01_stacked_area_v2.png`, `02_net_change_forward_v2.png` — charts.
- `README.md` — v1 documentation (anchor caveat and Gold Book
  definitional gap, trailing method, changelog).

## Open items (not in v2)
Gowanus/Narrows repowering (819 MW, conceptual, earliest mid-2031);
NYPA 1 GW advanced nuclear (no site/date); East River ESS 100 MW and
Luyster Creek 126 MW batteries at Astoria (permitted/proposed, absent
from EIA Planned, construction unverified); Pinelawn deactivation
(82 MW, unresolved); Glenwood Landing GT4/GT5 and Port Jefferson
GT2/GT3 retirements (106 MW each, listed only in Q4 STAR assessment
assumptions); Hell Gate 2 (47 MW); FitzPatrick licence expiry
Oct 2034 (883.3 MW); Gowanus Barges 1 & 4 oil turbines (320 MW, all
out-of-service, formal status unclear, kept in the stack). See
`research_log.md` and `summary_v2.json`.
