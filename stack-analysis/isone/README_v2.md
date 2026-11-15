# ISO-NE capacity stack — v2 (EIA + manual corrections)

Built 2026-11-15 from v1 (see `README.md`) by applying 2 named manual
adjustments (3 row-level changes), each with an online source, logged
in `research_log.md` and `manual_adjustments.csv`. Reproduce with
`python3 build_stack_v2.py` (it verifies v1 reproduces, applies the
corrections, and asserts the corrected yearly flow deltas on every
run). v1 files are untouched.

## Headline figures (v2 vs v1)

| | v1 | v2 | Change |
|---|---|---|---|
| 2036 total | 41,619.4 MW | **41,608.4 MW** | **−11.0 MW** |
| Forward additions 2026–2036 | 3,886.3 MW (78 units) | 3,875.3 MW (78 units) | −11.0 MW |
| Forward retirements 2026–2036 | 505.0 MW (12 units) | 505.0 MW (12 units) | 0 |
| Forward net 2026–2036 | +3,381.3 MW | +3,370.3 MW | −11.0 MW |

Delta by fuel (net): Wind **−11.0 MW**; all other fuels 0 (the
Merrimack correction is a retime inside the window). The v2 stack
peaks in 2031 at 41,624.1 MW and ends 2036 at 41,608.4 MW.
Year-by-year v2−v1 totals: 2026 −470.2; 2027 −356.6; 2028–2036 −11.0.
**Wind leads the v2 net change** on both bases: it is the largest
forward net fuel in v2 (+1,504.0 MW of the +3,370.3 MW total) and the
only fuel changed by the manual corrections.

## What changed (2 adjustments)

| # | Plant | Change | MW | Confidence |
|---|---|---|---|---|
| A | Merrimack Units 1/2, NH | Retime Dec 2027 / May 2028 → Sep 2026 (booked) | 459.2 | High |
| B | Revolution Wind, RI | Resize 715.0 → 704.0 MW (Nov 2026 unchanged) | −11.0 | High |

Notes and flags:
- **Merrimack (A) actually closed on Sep 12, 2025** — New England's
  last coal plant, ahead of its 2028 settlement deadline. EIA still
  shows it operating with 2027/2028 retirements. Because v2 never
  restates the EIA anchor, the retirement is booked in Sep 2026, the
  first forward year. Stated plainly: **the EIA anchor overstates true
  Dec-31-2025 capacity by 459.2 MW** (true-basis anchor 37,778.9 MW,
  coal 0.0 MW — New England was already coal-free at the anchor date).
  Timing-only in the window: the 2036 total is unaffected by this item.
- **Revolution Wind (B)** reached full operation Nov 5, 2026 at its
  as-built 704 MW (65 turbines; 400 MW RI + 304 MW CT), after two BOEM
  stop-work orders (Aug 22 and Dec 22, 2025) were both enjoined by
  federal courts. A federal request to remand its 2023 COP approval
  (Oct 9, 2026) remains pending — an overhang, not a cancellation.
- **Vineyard Wind 1 was verified and kept at EIA's 800 MW / 2026**:
  construction completed Mar 13, 2026 and full commercial operation was
  Oct 29, 2026, so the EIA year is right. South Fork Wind (132 MW) is
  a NYISO resource (delivers to Long Island) and is correctly excluded.
- **Millstone and Seabrook: no change.** Seabrook is licensed to 2050.
  Millstone Unit 2's licence expires Jul 2035, inside the window, but
  Dominion intends renewal to 2055; its own retirement-risk warning is
  conditional on failing to win a post-2029 contract, and Connecticut's
  procurement was still pending — flagged below, not booked. The
  proposed NextEra–Dominion combination (announced May 18, 2026)
  proposes no operational changes at either plant.
- **No BTM exclusion was found** among the large forward plants: all
  are grid-connected. The one data-center-adjacent item (a 350 MW load
  study at the retired Merrimack site) is load, not generation.
- **No blanket retirement-delay override** was applied.

## Files (v2; v1 files untouched)

- `build_stack_v2.py` — the v2 build.
- `manual_adjustments.csv` — 3 row-level changes with sources and
  confidence.
- `isone_capacity_plants_v2.csv` — unit-level changelog with `v2_*`
  columns and `manual_change` flags.
- `isone_capacity_stack_v2.csv` — stack (year × fuel).
- `isone_capacity_changelog_v2.csv` — forward changelog (year × fuel).
- `summary_v2.json` — v1/v2 forward totals, deltas, yearly totals,
  largest changes, flagged candidates not added.
- `research_log.md` — evidence, sources, and confidence per adjustment;
  KEEP list; unverified items; candidates not proposed.
- `01_stacked_area_v2.png`, `02_net_change_forward_v2.png` — charts.
- `README.md` — v1 documentation (anchor source and CELT gap, trailing
  method, northern-Maine exclusion, changelog, caveats).

## Open items (not in v2)
Middletown Units 2/3/4, CT (767.9 MW, EIA status already "out of
service, not expected to return"; NEPGA lists closure by mid-2028 but
no owner/ISO filing was found — if it closes, v2 overstates 2028–2036
by 767.9 MW); Millstone Unit 2 licence expiry 2035 (909.9 MW, renewal
intended); Form Energy Lincoln, ME iron-air battery (85 MW, DOE-backed,
construction from 2028, absent from EIA entirely); SouthCoast Wind
(~2,400 MW, COP remanded Nov 2025, developer paused Apr 2026) and New
England Wind 1+2 (contracts unsigned) — the post-Revolution offshore
pipeline is stalled, not scheduled; Merrimack-site solar/battery
redevelopment (~100 MW, unverified). Behind-the-meter solar (~5.9 GW
invisible to EIA) remains a caveat, not a stack item. See
`research_log.md` and `summary_v2.json`.
