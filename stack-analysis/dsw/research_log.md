# DSW capacity stack — v2 research log

Built 2026-11-15. v2 = v1 (EIA-860M only) + 9 named manual adjustments
(18 row-level changes: 6 retimes, 12 new rows), each with an online
source. All sources accessed 2026-11-15. Basis throughout is
nameplate MW. Region = DSW (AZ + NM state cut) for every adjustment.

## The adjustments

### A. RETIME — Four Corners Units 4 & 5, NM, Coal, 1,636.2 MW, Dec 2031 → Dec 2038
2 × 818.1 MW. APS announced on Oct 2, 2026 that it will continue
operating Four Corners beyond the previously planned 2031 retirement;
in Sep 2026 APS signed a coal-supply agreement with Navajo
Transitional Energy Co. (NTEC) enabling operation through 2038, and
APS's 2026 IRP (filed with the ACC in early Nov 2026) uses a base case
labelled "FC Extended to 2038" and proposes extending decommissioning
"to no later than 2038," citing reliability, fuel diversity, and
~$1.02bn of modelled customer savings vs a 2031 exit. The plant's
Navajo Nation lease allows operation through 2038. Dec 2038 is
outside the 2026–2036 window, so the retirement leaves the v2
changelog (the plants file carries the v2 date 2038-12).
Caveat: the other owners — PNM, TEP, SRP — still state plans to exit
their shares in 2031 (TEP and PNM confirmed Nov 2026), and APS has
also discussed a possible sale to the Navajo Nation's energy company
or a future gas conversion. EIA reports the full plant at its
location and APS is the operator; the plant-level retime is the
correct stack treatment, but the post-2031 ownership/operation
structure is unsettled.
Sources: Utility Dive, Nov 4, 2026,
https://www.utilitydive.com/news/aps-sales-double-by-2041-proposes-extending-coal-use-to-2038/873648/;
APS Environmental Compliance page (Four Corners),
https://www.aps.com/en/Utility/Regulatory-and-Legal/Environmental-Compliance;
Arizona Republic, Nov 3, 2026,
https://www.azcentral.com/story/money/energy/2026/11/03/aps-wants-coal-plant-open-until-2038-other-owners-want-out/92550752007/.
Confidence: Medium-High (extension announced + coal contract signed +
IRP filed; exact end year is "no later than 2038," not a fixed date).

### B. Fuel switch — Coronado Units CO1 + CO2, AZ, Coal → Natural Gas, 821.8 MW, 2029
Coal retirements retimed Dec 2032 → Dec 2029 (both units); gas
additions of 410.9 MW each booked Dec 2029. SRP's board approved the
coal-to-gas conversion on Jun 24, 2025, expected complete by late
2029, with a ~100-mile gas pipeline to the site (the site currently
has no gas supply). Before the conversion decision, Coronado was
slated for retirement no later than Dec 31, 2032 — the date EIA
still carries. Sierra Club's Jul 2, 2026 ACC comments confirm the
board vote and the 2029 completion.
Sources: Global Energy Monitor,
https://www.gem.wiki/Coronado_Generating_Station; Sierra Club comments
to the ACC, Jul 2, 2026,
https://docket.images.azcc.gov/E000052876.pdf?i=1784141247161.
Confidence: Medium-High on conversion and year; Medium on month
(Dec 2029 placeholder for "late 2029").

### C. Fuel switch — Springerville Units 1 + 2, AZ, Coal → Natural Gas, 849.6 MW, 2030
Coal retirements retimed: Unit 1 Dec 2027 → Dec 2030, Unit 2
Dec 2032 → Dec 2030; gas additions of 424.8 MW each booked Dec 2030.
TEP announced Jul 29, 2025 that it would convert Units 1 and 2 (the
two units TEP owns; TEP operates all four) to gas by 2030, citing
~$170m conversion cost vs >$450m of retrofits needed to keep burning
coal. The ACC approved the CEC amendment for the conversion in
Mar 2026. A ~20-mile pipeline lateral (with the Coronado line) will
supply gas. TEP's 2026 IRP (filed Nov 2, 2026) reaffirms conversion
by ~2030/2031 and a Four Corners exit by 2031.
Sources: ACC staff filing on the Springerville CEC amendment,
Feb 5, 2026, http://docket.images.azcc.gov/E000049241.pdf?i=1771641153246;
Global Energy Monitor,
https://Www.gem.wiki/Springerville_Generating_Station; Arizona
Republic, Nov 3, 2026 (TEP position).
Confidence: Medium-High.

### D. Fuel switch — Springerville Unit 4, AZ, Coal → Natural Gas, 458.1 MW, 2029
NEW coal retirement Dec 2029 + NEW gas addition Dec 2029 (EIA has no
planned retirement for Unit 4 at all). SRP, which owns Unit 4,
presented conversion/replacement/storage options to its Power
Committee on Sep 25, 2025, and its board voted in Nov 2025 to convert
Unit 4 from coal to gas by 2029 (same timeline and pipeline as
Coronado). SRP filed a CEC amendment application for the Unit 4
conversion in 2026; Sierra Club's Jul 2, 2026 comments support ending
Unit 4 coal use by no later than 2029.
Sources: Sierra Club ACC comments, Jul 2, 2026,
https://docket.images.azcc.gov/E000052876.pdf?i=1784141247161;
Global Energy Monitor (Springerville).
Confidence: Medium (board vote reported via ACC filings/secondary
sources; SRP's own release not retrieved).

### E. ADD retirement — Springerville Unit 3, AZ, Coal, −458.1 MW, Dec 2031
NEW coal retirement Dec 2031. Tri-State Generation and Transmission
Association, which owns Unit 3, announced in Dec 2023 that Unit 3
would retire in 2031 and be replaced with ~1,250 MW of renewables.
EIA has no planned retirement for Unit 3. SRP holds a contract for
100 MW of Unit 3 capacity through 2036, which is a contract position,
not plant operation — the owner's retirement announcement governs
the plant-level stack.
Source: Global Energy Monitor (Springerville), summarising the
Tri-State Dec 2023 announcement.
Confidence: Medium.

### F. Fuel switch — Apache Station ST3, AZ, Coal → Natural Gas, 204.0 MW, 2027
NEW coal retirement Dec 2027 + NEW gas addition Dec 2027 (EIA has no
planned retirement for ST3). AEPCO announced in Sep 2024 that it
would stop using coal at Apache by the end of 2027 and transition
the plant entirely to gas (Unit 2 already converted in 2017/2018;
ST3 is the last coal unit). The commitment is tied to AEPCO's USDA
New ERA award (~$485m) with obligations including ~70% emissions
reduction by 2031, which AEPCO states it remains committed to.
FLAG / overhang: in Jun 2026 the DOE allocated $20.8m (plus $32.5m
non-DOE) to modernize the coal turbine, described as extending the
coal unit's lifespan; AEPCO did not respond to press questions on
whether the conversion plan changes. This is the weakest adjustment
in v2 — plant-specific evidence exists for both directions, with the
dated, grant-backed conversion commitment on one side and a 2026
federal coal-modernization grant on the other.
Sources: Global Energy Monitor,
https://www.gem.wiki/Apache_Generating_Station; State Affairs,
Jun 2026 (DOE modernization award).
Confidence: Low-Medium.

### G. ADD — Cholla gas repower, AZ, Natural Gas, +387.0 MW, Dec 2030
NEW gas addition. Cholla's coal units retired in Mar 2025 (Units 1
and 3; Units 2 and 4 retired 2015/2020) and are correctly out of the
v1 anchor. In Jul 2026 APS announced it would convert Units 1 and 3
to natural gas (~380 MW, construction from 2028, in-service 2029),
filing a CEC notice with the ACC on Aug 31, 2026. APS's 2026 IRP
(filed Nov 2026) describes "repowering the Cholla Power Plant as a
387-MW facility by 2030." The IRP figure and year (387.0 MW,
Dec 2030 placeholder) are used as the latest filed plan; the
Jul 2026 announcement's ~380 MW / 2029 is the earlier variant.
Sources: Utility Dive, Nov 4, 2026 (APS 2026 IRP);
ACC news release, Jul 3, 2026,
https://azcc.gov/news/home/2026/07/03/chairman-myers-visits-cholla-power-plant-for-reopening-announcement;
APS CEC notice, Aug 31, 2026,
https://docket.images.azcc.gov/E000054067.pdf?i=1791074149852.
Confidence: Medium.

### H. ADD — Desert Sun Power Plant, AZ, Natural Gas, +1,238.0 MW, Dec 2032
NEW gas addition, not in EIA Planned. APS announced the Desert Sun
site (west of Gila Bend, Maricopa Co.) on Oct 30, 2025 as capable of
up to 2,000 MW in two phases — Phase 1 for general customer growth
via competitive procurement (scheduled late 2030), Phase 2 for
extra-large customers under a subscription model (2031–2033) — fed
by Energy Transfer's Transwestern Desert Southwest pipeline
expansion (complete late 2029). APS's 2025 All-Source RFP (revised
Jan 6, 2026) seeks ~1,660 MW at the site in two combined-cycle
blocks; APS's May 2026 Title V permit application describes two
7HA.02 1×1 CC units at 530 MW unfired / 630 MW duct-fired each.
APS's 2026 IRP preferred plan adds "the 1,238 MW Desert Sun
combined-cycle facility in 2032 to serve large-customer subscription
load" — that filed figure and year are used here.
BTM analysis: NOT behind-the-meter. Desert Sun is a utility grid
plant; the subscription model is a cost-allocation/financing
mechanism for Phase 2, not a co-located island — the plant
interconnects to the APS grid and Phase 1 serves general load.
Counted in full under the standing rule.
Distinctness check: Desert Sun is NOT the EIA Planned "Saddleback
Generation Station" (1,250 MW, Dec 2030, status P) — Saddleback is a
separate Copia Power project in Maricopa Co. (Tonopah area). The
similar size is a coincidence of two ~1.25 GW CC projects in the
same county; both are kept.
Sources: Utility Dive, Nov 4, 2026 (IRP figure);
APS newsroom, Oct 30, 2025,
https://newsroom.aps.com/aps-uses-growth-pays-for-growth-model-to-develop-new-natural-gas-plant/;
APS 2025 All-Source RFP (Desert Sun exhibit).
Confidence: Medium (IRP preferred plan, not an approval; MW varies
1,238–2,000 across APS's own documents by phase/basis).

### I. ADD — Project Baccara, AZ, Natural Gas, +744.0 MW, Jun 2028
NEW gas addition, not in EIA Planned. Takanock (developer) / Montera
(data center) propose a 744 MW gas plant ("Project Baccara")
co-located with a two-building data center ("Project Eagle") on
~160 acres in Glendale/Waddell, Maricopa Co. Air-permit applications
were filed with Maricopa County in summer 2026; an ACC Certificate
of Environmental Compatibility was reported issued Feb 4, 2026;
construction was slated to begin in 2026, with the first data center
targeted online early 2028.
BTM analysis (standing rule): NOT excluded. The rule zeroes
co-located generation only when the grid connection is entirely
accounted for by the load. Baccara's own filings state the plant
will sell power to the grid / the local electrical district (which
then sells to the data center), will connect to an APS substation by
2030, and will provide backup to the data center and/or the grid;
the data center itself runs on an interim utility (grid) connection
for its first ~18 months. The generation is therefore independently
grid-connected and counts in full. The counter-consideration is
recorded: Maricopa County Air Quality initially treated plant + data
center as a single emissions source precisely because the plant
"will exist mostly to serve the data center initially," and the
developer is asking the county to treat them separately. If a future
filing shows the plant islanded behind the data center's meter with
no independent grid export, this addition should be zeroed under
the rule. Jun 2028 is a placeholder month (first-data-center timing;
press figures also appear as ~700 MW).
Source: Arizona Republic, Oct 30, 2026,
https://www.azcentral.com/story/news/environment/2026/10/30/how-az-data-center-project-could-alter-air-pollution-rules/92270770007/.
Confidence: Low-Medium.

## Checked and confirmed KEEP (no change)
- **SunZia Wind North + South, NM, Wind 3,650.2 MW, in-service 2026**
  — Pattern Energy placed the full 3,650 MW project (916 turbines)
  in commercial operation on Jun 18, 2026, with its 550-mile HVDC
  line to Arizona; EIA nameplate (2,561.2 + 1,089.0) matches the
  developer/EIA-reported 3,650 MW. It is the largest single item in
  the v1 changelog and it is real. BA = CISO in EIA (output tracked
  by CAISO) — flagged in the README edge cases, kept in the state
  cut. Source: Pattern Energy, Jun 18, 2026 (via trade press).
- **Palo Verde, AZ, Nuclear 4,209.6 MW** — no uprate and no
  retirement in the window. APS filed a Notice of Intent with the
  NRC on Mar 13, 2026 to seek subsequent license renewal (application
  late 2027) extending Unit 1 to 2065, Unit 2 to 2066, Unit 3 to
  2067 — all far outside 2026–2036. APS management stated in Nov 2026
  that most meaningful uprate opportunities at Palo Verde have
  already been completed. An ANL/INL study used a ~100 MW Palo Verde
  uprate as a modelling case; there is no APS uprate proposal, so
  nothing is added (see flagged candidates). Sources: APS newsroom,
  Mar 16, 2026,
  https://newsroom.aps.com/aps-to-seek-license-renewal-for-palo-verde-generating-stations-nuclear-units/;
  Pinnacle West Q3 2026 call.
- **CO Bar Solar and BESS complex, AZ (~2,000 MW in EIA Planned)**
  — Enlight/Clēnera's Q3 2026 results (Nov 3, 2026) state all five
  CO Bar phases are now under construction (1,211 MW solar +
  4,000 MWh storage complex), with first COD Q4 2027 and phases
  through H1 2028. EIA carries the phases as status P (paper) with
  Dec 2027 / May–Aug 2028 dates — the dates are consistent with the
  developer; only the status is stale. Status-only note; no MW/date
  change. **Snowflake A** (EIA: 475 MW solar + 475 MW battery,
  Aug 2027, L): developer states 594 MW solar + 1,900 MWh storage,
  under construction, COD H2 2027 — date consistent; the MW basis
  differs (developer figure appears to be MWdc/gross), so EIA
  nameplate is kept. Source: Enlight Q3 2026 earnings release,
  Nov 3, 2026,
  https://enlightenergy.com/wp-content/uploads/2026/11/3Q26-Earnings-Release-Eng.pdf.
- **Saddleback Generation Station, AZ, Gas 1,250.0 MW, Dec 2030, P**
  — Copia Power project, Maricopa Co.; confirmed distinct from APS
  Desert Sun (see H). Paper project (status P, no approvals
  initiated); kept with a paper-pipeline flag — no termination
  evidence found.
- **NTEC Gas Plant, NM, Gas 1,089.0 MW, Jun 2028, L** — Navajo
  Transitional Energy Co., San Juan Co.; part of NTEC's NavEnergy
  Hub (gas peaking + Four Corners CCS ambitions; NTEC's Sep 2026
  transmission comments describe the hub portfolio). Early-stage
  (status L); kept, flagged. Note the DOE cancelled NTEC's Four
  Corners CCS FEED-study funding in Oct 2025 — that affects the CCS
  retrofit idea, not this EIA gas row.
- **SRP gas expansions in EIA** — Coolidge (6 × 49.5 MW, 2027, U)
  and Red Hawk (8 × 49 MW, 2027, U) CT additions are in v1 and are
  part of the "1,107 MW of CTs/uprates" bucket APS's IRP describes
  for APS's own fleet (SRP's are separate but analogous); no
  adjustment. APS's share of that bucket beyond what EIA already
  carries cannot be separated from EIA's rows, so the bucket is a
  flagged candidate, not an addition (double-count risk).
- **H. Wilson Sundt Generating Station (TEP), AZ** — no coal remains
  at Sundt (its coal-era units retired in 2019; the operating units
  are gas steam + RICE engines, 528.9 MW). There is no Sundt coal
  conversion to book; TEP's conversions are Springerville (C/D).
  EIA carries no Sundt retirement in the window. KEEP.
- **Escalante, NM, Coal 257.0 MW** — retired 2020; appears in the
  trailing reconstruction only, correctly absent from the anchor.
  **San Juan, NM** — fully retired 2022 (Units 2/3 in 2017), trailing
  only; the San Juan Solar I replacement project (200 MW solar +
  100 MW battery, in service 2024) is in the anchor. **Navajo
  Generating Station, AZ, 2,409.3 MW coal** — retired Nov 2019,
  trailing only. **Cholla coal** — retired Mar 2025, out of the
  anchor (verified against APS/ACC reporting; APS kept it shuttered
  despite the Apr 2025 federal executive order naming it); the gas
  repower is adjustment G.
- **PNM forward resources** — PNM's approved/pending 2028 resources
  (Valencia PPA extension 167 MW on an existing plant, Corazon BESS
  150 MW, Sun Lasso BESS 150 MW, Sunbelt solar 100 MW + battery)
  are either already in EIA's Operating/Planned sheets or are PPA
  extensions of existing capacity; no new owned PNM gas plant was
  found in its 2026 IRP materials. No adjustment.
- **No other BTM exclusion found.** The Phoenix-metro data-center
  fleet is otherwise grid-served (APS/SRP interconnection queues);
  APS's TSMC direct-pricing contract (~1.88 GW) and Desert Sun
  Phase 2 subscription are grid arrangements, not co-located
  generation. The two genuine co-location proposals found are
  Project Baccara (adjustment I — counted, with reasoning) and the
  unapproved SpaceX/Tombstone campus (load only, no generation —
  flagged below).

## Could not verify / flagged, no adjustment proposed
- **APS 2026 IRP generic gas bucket: 1,107 MW** of new CTs and
  tolling-unit uprates at existing APS sites, 2026–2030. No
  plant-by-plant split published in the sources retrieved, and EIA
  Planned already carries APS/SRP CT expansions in the same window
  and size class. Adding the bucket would risk double-counting.
  Flagged candidate: 1,107.0 MW.
- **Desert Sun beyond the IRP figure:** site capacity up to
  2,000 MW (APS announcement) / ~1,660 MW (RFP) vs 1,238 MW added.
  The difference (~762 MW vs the announcement) has no firm date.
  Flagged candidate: 762.0 MW.
- **TEP 2026 IRP: 300 MW of new gas generation** (plus 680 MW each of
  solar and storage) by 2041 — no named plant or in-window date.
  Flagged candidate: 300.0 MW.
- **Palo Verde uprate (~100 MW modelling case, ANL/INL Aug 2026)** —
  no APS proposal; APS says uprate opportunities are largely
  exhausted. Flagged candidate: 100.0 MW.
- **Four Corners CCS retrofit** (NTEC NavEnergy Hub) — FEED-study
  DOE award ($6.55m) was cancelled in Oct 2025; no MW/date for any
  capacity change (it is a life-extension/emissions project, and
  adjustment A already extends the plant). No MW proposed.
- **SpaceX / Tombstone Resources 6 GW AI campus, Cochise Co., AZ**
  (filed Oct 30, 2026; county hearing Dec 9, 2026) — a ~6 GW load
  proposal next to Apache Station with no generation of its own in
  the application. Load is not capacity; nothing to add. Noted
  because, if approved, it would transform the DSW load picture
  behind every IRP in this log.
- **La Osa / Vermaland (Eloy, AZ, ~3 GW data-center proposal)** —
  energy plan "opens with a gas plant" but no MW, tenant, or date
  verified. Not proposed.
- **APS/SRP/TEP new-nuclear exploration** — the three utilities
  jointly sought DOE funding in 2025 to evaluate new nuclear sites
  in Arizona. No MW, site, or date. Not proposed.

## Status-only notes (no MW/date change)
- CO Bar phases: EIA status P, actually under construction (all
  five phases, per Enlight Q3 2026). Snowflake A: EIA status L,
  actually under construction. SunZia: EIA Operating-sheet 2026
  in-service rows match the Jun 18, 2026 commercial-operation date.
  Status changes do not affect the stack and were not applied.
