# ISO-NE capacity stack — v2 research log

Built 2026-11-15. v2 = v1 (EIA-860M only) + 2 named manual adjustments
(3 row-level changes), each with an online source. All sources accessed
2026-11-15. Basis throughout is nameplate MW. No blanket
retirement-delay override was applied; retirements moved only on
plant-specific evidence. The standing behind-the-meter rule was applied
to every large forward plant (see "BTM check" below).

## The adjustments

### A. RETIME — Merrimack Units 1 & 2, NH, Coal, 459.2 MW, EIA Dec 2027 / May 2028 → Sep 2026 (booked)
113.6 + 345.6 MW. Merrimack Station (Bow, NH) — New England's last
coal-fired plant — **ceased operations on September 12, 2025**, ahead of
the June 2028 deadline in its March 2024 settlement with the EPA,
Conservation Law Foundation and Sierra Club. Schiller Station's coal
units (Portsmouth, NH) also closed in 2025; New England is coal-free.
EIA-860M Sep 2026 is stale here: it still lists Merrimack Unit 1 as
(OP) Operating with a Dec 2027 planned retirement and Unit 2 as (OS)
with a May 2028 planned retirement.
Treatment: v2 never restates the EIA anchor (the MISO/PJM build
convention), so the retirement is booked in **Sep 2026**, the first
forward year, with the actual Sep 2025 cessation stated wherever the
figure is used. Consequence, stated plainly: **the EIA anchor overstates
true Dec-31-2025 capacity by 459.2 MW** (true-basis anchor 37,778.9 MW,
coal 0.0 MW). The retime is timing-only inside the 2026–2036 window, so
it does not change the 2036 total.
Sources: WAMC / Northeast Public Radio, "The last coal power in New
England," Nov 19, 2025
(https://www.wamc.org/show/earth-wise/2025-11-19/the-last-coal-power-in-new-england);
Global Energy Monitor, Merrimack Station
(https://www.gem.wiki/Merrimack_Station); CLF, "Coal-Free New England"
(https://www.clf.org/making-an-impact/coal-free-2020/).
Confidence: High on the closure and its date; the Sep-2026 booking is a
stated convention, not a claim about when the plant closed.

### B. RESIZE — Revolution Wind, RI, Wind, 715.0 → 704.0 MW (date unchanged, Nov 2026)
EIA's Planned sheet carries Revolution Wind at 715 MW, status (V),
Nov 2026. The project is 65 Siemens Gamesa turbines totalling **704 MW**
(400 MW to Rhode Island, 304 MW to Connecticut), and Ørsted confirmed
**full operation on November 5, 2026** — the year in EIA is right, the
MW is 11.0 high. History, because it decided whether the 2026 date
could be trusted: BOEM stop-work order Aug 22, 2025 (~80% complete) →
preliminary injunction Sep 22, 2025 (Judge Lamberth; the order was
later described in court as the "height of arbitrary and capricious")
→ second BOEM suspension Dec 22, 2025 (one of five projects suspended
that day) → second injunction Jan 12, 2026 → first power Mar 14, 2026 →
final (65th) turbine installed Sep 18, 2026 → full operation Nov 5,
2026. Still open: on Oct 9, 2026 the Justice/Interior departments asked
the court to remand the project's 2023 construction-and-operations-plan
approval for reconsideration; that request was pending at the time of
writing. It is noted as a legal overhang, not treated as a cancellation
— the farm is built and selling power under contract.
Sources: Providence Journal, Nov 5, 2026
(https://www.providencejournal.com/story/news/local/rhode-island/2026/11/05/revolution-wind-targeted-by-trump-is-now-complete-and-selling-power-to-utilities/92615688007/);
Nature World News, Nov 10, 2026
(https://www.natureworldnews.com/articles/73784/20261110/revolution-wind-reaches-full-operation-off-rhode-island-after-two-stop-work-orders-new-england.htm);
CT AG filing on the second stop-work order
(https://portal.ct.gov/-/media/ag/press_releases/2026/revolution-wind-pi.pdf).
Confidence: High.

## Checked and confirmed KEEP (no change)

- **Vineyard Wind 1, MA, Wind 800 MW, in service Apr 2026 (EIA Operating
  sheet)** — KEEP. First power Jan 2, 2024; construction completed
  Mar 13, 2026 (final blade on the 62nd turbine); **full commercial
  operation Oct 29, 2026**, so EIA's 2026 in-service year is correct on
  the stack's annual basis. The Dec 22, 2025 BOEM 90-day suspension hit
  this project too (95% complete); a preliminary injunction in Jan 2026
  allowed work to resume. Project literature variously says 800 / 804 /
  806 MW (62 × 13 MW); the stack keeps EIA's 800.0 MW for consistency.
  Sources: WBUR, Nov 6, 2026
  (https://www.wbur.org/news/2026/11/06/vineyard-wind-fully-running-offshore-wind-massachusetts,
  via search-result reporting); Baird Maritime, Nov 10, 2026
  (https://www.bairdmaritime.com/offshore/renewables/offshore-wind/vineyard-wind-1-commercial-operations).
- **South Fork Wind, 132 MW — correctly NOT in the stack.** Operating
  since Mar 2024, but it delivers to Long Island (East Hampton, NY) and
  EIA codes it BA=NYIS (130.0 MW in-file). It is a NYISO resource that
  happens to sit off Rhode Island. Excluding it is the BA cut working as
  intended; it is also listed in summary_v2.json's flagged candidates so
  it is not mistaken for an omission.
- **Block Island Wind Farm, RI, Wind 30 MW** — in the anchor (operating
  2016, BA=ISNE). KEEP.
- **Millstone Units 2 & 3, CT, Nuclear 909.9 + 1,350.0 MW (EIA
  nameplate)** — KEEP, no retirement or uprate in the window. Unit 2's
  licence expires Jul 31, 2035 and Unit 3's on Nov 25, 2045. Dominion
  intends to seek subsequent renewals (Unit 2 to 2055, Unit 3 to 2065)
  but warned Connecticut regulators in Mar 2026 that without a long-term
  contract past the current PPA's Oct 2029 expiry, the Unit 2 renewal
  decision "becomes materially more challenging, increasing the risk of
  a Unit 2 license expiration and retirement." Connecticut's zero-carbon
  procurement decision was still pending in late 2026. Separately,
  NextEra and Dominion announced a combination on May 18, 2026
  (shareholders approved Sep 3, 2026; regulatory approvals pending; the
  NRC licence-transfer application proposes **no physical or operational
  changes**). Neither item is an announced retirement — see flagged
  candidates. Sources: Utility Dive, Aug 3, 2026
  (https://www.utilitydive.com/news/dominion-offshore-wind-project-cost-rises-nearly-300m/826845/);
  Hartford Business Journal via Titan Energy blog, May 14, 2026
  (https://blog.titanenergyne.com/millstone-reactor-could-retire-without-new-long-term-contract).
- **Seabrook, NH, Nuclear 1,242.0 MW** — KEEP. Licence renewed Mar 12,
  2019 to Mar 15, 2050; no retirement, licence or uprate news in
  2025–2026 (the live regulatory item is NRC special oversight of
  alkali-silica concrete degradation, a monitoring matter, not a
  retirement signal). The proposed NextEra–Dominion combination would
  put Seabrook and Millstone under one parent; no operational change is
  proposed.
- **Largest EIA Planned batteries — KEEP EIA MW/dates, with status
  flags.** Elevate Middletown, CT, 275 MW, Dec 2027, status (P) —
  paper: approvals not initiated. Energizar BESS, MA, 250 MW, Dec 2027,
  status (L) — approvals pending. Taft BESS, MA, 200 MW, Apr 2027,
  status (V) — under construction >50%, the firmest of the three. Salt
  Cod BESS, MA, 168 MW, Dec 2028, status (L). No contrary evidence
  (cancellation, resize, new date) was found for any of them; the stack
  keeps EIA and the README reports the status mix (only 1,253.5 MW of
  the 2,808.0 MW Planned sheet is under construction or
  construction-complete).
- **Maine batteries already operating — in the anchor, KEEP.** Cross
  Town Energy Storage, Gorham, ME, 175 MW (operating 2025) and
  Cranberry Point, MA, 150 MW (operating 2025) are the region's largest
  operating batteries after Medway Grid (250 MW, in service Mar 2026,
  a v1 2026 addition). All present in EIA with sensible dates.
- **Canal Units 1 & 2, MA, Oil 585.0 + 580.0 MW (plus Canal 3 gas,
  330 MW)** — KEEP; **no retirement announcement found.** Owner JERA
  Americas' Sep 2026 update to the Town of Sandwich presents Units 1–2
  (online 1968/1976) as winter grid-support units that "rarely run
  unless the system is in crisis," and JERA is developing a battery
  project on the site — a site addition, not a unit retirement. EIA has
  no planned retirement for them. Source: Town of Sandwich staff-meeting
  minutes, Sep 10, 2026
  (https://www.sandwichmass.org/AgendaCenter/ViewFile/Agenda/_09102026-4410).
- **William F Wyman Unit 4, ME, Oil 632.4 MW; New Haven Steam, CT, Oil
  460.0 MW; Montville Unit 6, CT, Oil 414.9 MW; Newington, NH, Oil
  414.0 MW** — no retirement announcements found; EIA shows no planned
  retirements. KEEP. (These elderly oil steam units are the stack's
  largest single retirement-risk block — 5,970.4 MW of oil sits in the
  anchor — but risk is not evidence, and no dates were invented.)
- **Schiller, NH** — EIA's Retired sheet already records the coal units
  (2 × 50 MW coal + 50 MW other) as retired in 2025, matching the
  reported 2025 closure; the trailing reconstruction handles them with
  no adjustment. The remaining Schiller GT1 (21.2 MW oil peaker) stays.
- **Mystic, MA** — the 2024 retirement (6 gas units, 1,744.4 MW) is in
  EIA's Retired sheet and appears naturally in the trailing
  reconstruction (2024 total falls 1,351.1 MW). No adjustment.

## BTM check (standing rule)
Every forward addition ≥200 MW was checked for co-located load:
Vineyard Wind 1, Revolution Wind, Elevate Middletown, Energizar, Taft,
Freedom Pine Solar, Broadleaf Solar and Medway Grid are all
grid-connected projects selling into the ISO-NE grid — none is
generation co-located with load behind a single grid connection, so
**no 0-MW exclusion applies and nothing was removed**. The only
data-center-adjacent item found in the region is at the retired
Merrimack site: an April 2026 Eversource viability study for a **350 MW
load** connection requested by the site owner. That is load, not
generation, and it is not in the stack. Separately: behind-the-meter
rooftop/distributed solar is largely invisible to EIA-860M — ISO-NE
puts total New England solar nameplate at ~9,600 MW at end-2025
(including >5,100 MW of "behind all meters" PV that provides the ISO no
data at all), versus 3,734.3 MW of solar in this stack's anchor. Per
the brief, that gap is flagged as a caveat in README.md and **not**
added to the stack.

## Could not verify / flagged, no adjustment proposed
(Also in summary_v2.json as `not_added_flagged_candidates_mw`.)
- **Middletown Units 2/3/4, CT, 767.9 MW (113.6 gas + 239.4 gas +
  414.9 oil)** — EIA status is already (OS) "out of service and NOT
  expected to return," yet EIA carries no planned retirement, so v1
  holds them in the stack through 2036. NEPGA's president (Jun 13,
  2025 presentation) lists "Middletown Power (Middletown, CT) — 750 MW —
  Oil — Closure by mid-2028," and secondary coverage repeats that
  Schiller, Merrimack and Middletown close "between this year and
  mid-2028." No owner announcement or ISO-NE deactivation filing was
  found, so — as with MISO v2's R.S. Nelson — this is flagged, not
  booked. If it closes mid-2028, v2 overstates 2028–2036 by 767.9 MW.
  Source: http://www.raabassociates.org/Articles/Dolan%20Presentation%206-13-2025.pdf
- **Millstone Unit 2, CT, Nuclear 909.9 MW** — licence expiry Jul 2035
  falls inside the window. Dominion intends renewal to 2055 but has
  itself flagged retirement risk without a post-2029 contract (see
  KEEP entry). Not booked: an intended renewal plus a pending state
  procurement is not a retirement announcement.
- **Form Energy Lincoln, ME, Battery 85 MW / 8,500 MWh** — iron-air
  long-duration storage at the former Lincoln mill, ~$147M DOE grant
  (Power Up New England). **Not in EIA-860M at all** — a clean example
  of EIA missing a large project. Construction is slated to start in
  2028; no in-service date is published, so no row was added. Flagged
  at 85.0 MW.
- **SouthCoast Wind, offshore MA, ~2,400 MW** — COP approved Jan 17,
  2025; DOI moved to remand/vacate it in Sep 2025 and the D.C. court
  granted the remand on Nov 4, 2025; the developer (Ocean Winds / EDP)
  paused the project in Apr 2026; its 2023 contracts were cancelled and
  the 2024 re-bid produced no signed contract as of Oct 2026. Not in
  EIA-860M. Not added — no contract, no permit in hand, no date.
- **New England Wind 1 + 2, offshore MA (Avangrid)** — DOI has likewise
  sought remand of the COP approvals; state contracts unsigned. Not in
  EIA-860M; combined potential (~2,600 MW class) unverified at unit
  level. Not added.
- **Merrimack site redevelopment, NH** — Granite Shore announced in
  Oct 2025 that the site will become a "renewable energy park" (~100 MW
  of solar plus battery storage, per settlement coverage). MW split and
  dates unverified; not added. The 350 MW data-center study at the same
  site is a load item (see BTM check).
- **Sunrise Wind, 924 MW** — under construction off Long Island and in
  EIA's Planned sheet, but coded BA=NYIS and delivering to NYISO. It is
  listed here only so its absence from an ISO-NE stack is not mistaken
  for an EIA omission.

## Status-only notes (no MW/date change)
- Revolution Wind's EIA status (V) understates reality — it is fully
  operational (Nov 5, 2026). Vineyard Wind 1's EIA in-service month
  (Apr 2026) precedes its full-commercial-operation date (Oct 29,
  2026); both fall in 2026, so the annual stack is unaffected.
- The Dec 22, 2025 five-project federal lease suspension (Empire,
  Revolution, Sunrise, Vineyard, Coastal Virginia) was enjoined for all
  five projects by Apr 2026; none of the New England projects lost its
  2026 in-service year because of it. The underlying permit litigation
  (including the Oct 2026 remand request for Revolution) remains open.
