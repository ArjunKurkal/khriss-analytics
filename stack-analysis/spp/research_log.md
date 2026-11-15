# SPP capacity stack — expansion research + v2 research log

Built 2026-11-15. Part 1 establishes the SPP RTO western expansion
membership from SPP's own published sources (the basis for the
East/West cut). Part 2 is the v2 manual-correction log: v2 = v1
(EIA-860M only) + 5 named manual adjustments (10 row-level changes:
8 retimes, 2 new rows), each with an online source. All sources
accessed 2026-11-15. Basis throughout is nameplate MW.

---

# Part 1 — The RTO western expansion (STEP 0 research)

## What happened, and when

SPP expanded its RTO into the Western Interconnection **effective
April 1, 2026 — live and integrated, not pending**. SPP's own
announcement (Apr 2, 2026): "SPP and member utilities successfully
complete historic western expansion"; expanded RTO operations
"officially began at midnight central time on April 1"; SPP is "now
a 17-state RTO" serving "a 732,000 square-mile region comprising all
or part of 17 states" and 20 million people, "the first regional
transmission organization (RTO) with services spanning two
interconnections."
Source: https://www.spp.org/news-list/spp-and-member-utilities-successfully-complete-historic-western-expansion/

Legal path: FERC accepted SPP's revisions to its Tariff, Bylaws and
Membership Agreement on **March 20, 2025** (RTO Expansion Order,
190 FERC ¶ 61,169, Docket No. ER24-2184); the April 1, 2026 effective
date was accepted Jan 15, 2026 (Docket No. ER24-2184-003); the
individual transmission-owner formula-rate filings were accepted
Mar 31, 2026, effective April 1, 2026 (e.g. Basin Electric
ER26-1169, Platte River ER26-998, Deseret ER26-1137 — all hosted on
spp.org). SPP now operates **two Balancing Authority Areas**: the
East BAA (legacy footprint) and the West BAA. SPP's Sep 4, 2026
tariff filing (ER26-3720, spp.org) states the expansion
"consolidated the Western Area Colorado Missouri (WACM) Balancing
Authority and the Western Area Upper Great Plains West (WAUW) BA,
which were previously managed by WAPA" into the SPP West BAA, and
that West BAA load-responsible entities must meet SPP resource
adequacy requirements from Jan 1, 2027 (per the Apr 7, 2026 order
cited there). The two BAAs are optimised jointly in SPP's Integrated
Marketplace "to the maximum extent practicable using the West DC
Ties" (510 MW of DC ties; RTO Expansion Order).

## The members — entity by entity (SPP sources only)

### A. Transmission-owning Expansion Members (the FERC-defined set)

The RTO Expansion Order (190 FERC ¶ 61,169, fn. cited in every 2026
formula-rate order on spp.org) defines the Expansion Members as
nine transmission-owning members:

| Entity | Home territory | Status Apr 1, 2026 |
|---|---|---|
| Basin Electric Power Cooperative | ND/SD/NE/MT/WY/CO ( HQ Bismarck, ND) | Joined/expanded (prior SPP member on its eastern system); TO, incl. a Miles City (MT) filing |
| Colorado Springs Utilities | Colorado Springs, CO | Joined; TO |
| City of Farmington, New Mexico | Farmington, NM | Joined; TO (listed in the FERC orders; see MEAN note below) |
| Deseret Generation & Transmission Cooperative | Vernal, UT (Bonanza plant) | Joined; TO (ER26-1137) |
| Platte River Power Authority | Fort Collins/Loveland/Longmont/Estes Park, CO | Joined; TO, new SPP Zone 101 (ER26-998) |
| Tri-State Generation and Transmission Association | CO/NM/WY/NE | Joined/expanded (prior member); TO — SPP tariff has a "Tri-State G&T Association-West" rate zone |
| Western Area Power Administration – Colorado River Storage Project (WAPA-CRSP) | CO/UT/AZ/NM federal hydro | Joined; TO |
| Western Area Power Administration – Rocky Mountain Region (WAPA-RMR) | CO/WY/NE | Joined; TO |
| Western Area Power Administration – Upper Great Plains Region (WAPA-UGP) | ND/SD/NE/MT/WY | Joined/expanded; TO |

SPP's later Sep 4, 2026 filing (ER26-3720) lists the Expansion
Members with **Municipal Energy Agency of Nebraska (MEAN)** in place
of the City of Farmington: "Basin Electric; Colorado Springs;
Deseret; Municipal Energy Agency of Nebraska (MEAN); Platte River;
Tri-State; WAPA-CRSP; WAPA-RMR; WAPA-UGP". MEAN is a transmission-
dependent member (it owns no transmission), which is why it is
absent from the transmission-owner list in the FERC orders but
present in SPP's resource-adequacy filing and in the Apr 2 roster.
Farmington appears in both the FERC orders and the Apr 2 roster.
Both are treated as RTO members in this build; the distinction has
no plant-level effect (Farmington's 115.8 MW sits in WACM and is in
the West cut either way; MEAN has no generation in the western BAs).

### B. Full Apr 1, 2026 roster (SPP Apr 2, 2026 release, verbatim list)

"Entities joining or expanding their participation in the SPP RTO
on April 1" (* = initiated the expansion; ^ = prior member
expanding): Basin Electric Power Cooperative*^; Central Montana
Electric Power; City of Aztec, New Mexico; City of Farmington, New
Mexico; City of Fountain, Colorado; City of Page, Arizona; City of
Sidney, Nebraska; Colorado Springs Utilities*; Delta-Montrose
Electric Association; Deseret Power Electric Cooperative*;
Guzman Energy^; Kimball Wind; La Plata Electric Association;
Los Alamos County; Municipal Energy Agency of Nebraska*^;
Northwestern Energy^; Platte River Power Authority*; Tenaska Power
Services Co.^; The Energy Authority; Tri-State Generation and
Transmission Association*^; United Power^; WAPA – Upper Great
Plains region*^; WAPA – Colorado River Storage Project region*;
WAPA – Rocky Mountain region*; Warren Air Force Base.

State footprint added (SPP): "resources and customers of numerous
utilities in seven states – Arizona, Colorado, Montana, Nebraska,
New Mexico, Utah, and Wyoming." Arizona's only roster entry is the
**City of Page** (a small municipal; it owns no EIA-860M generation —
its federal hydro allocations are USBR plants filed under WALC).
New Mexico's RTO entries are **Farmington, Aztec and Los Alamos
County** — small municipals/county, not the state's large utilities.

### C. Markets+ is NOT RTO membership — the critical distinction

SPP itself, in the same Apr 2, 2026 release: "SPP is also
developing a **separate** wholesale market called Markets+ that
will enable western utilities **who are not RTO members** to reap
the benefits of a day-ahead market and other services."
Markets+ is a stand-alone tariff under which SPP acts as a market
operator, not as the RTO (FERC Markets+ Funding Agreement order,
ER25-1372, Apr 22, 2025, spp.org); FERC accepted the Markets+
Tariff Jan 16, 2025, and SPP anticipated commencing Markets+
operation in **2027** (Q2/October 2027 in SPP/press reporting).
Markets+ Phase 2 funding participants (FERC order, verbatim):
Arizona Public Service Company (APS); Bonneville Power
Administration; City of Tacoma; Powerex Corp.; Chelan County PUD;
Grant County PUD; Salt River Project; Tucson Electric Power
Company. Arizona's large utilities (APS, SRP, Tucson Electric,
UniSource) announced plans to join **Markets+**, with participation
as early as 2027 — they are **not** SPP RTO members, and none of
their capacity is in this stack. Public Service Company of New
Mexico (PNM) chose CAISO's EDAM, not SPP at all. Xcel Energy's
Public Service Co of Colorado (PSCO) and PacifiCorp (PACE/PACW)
are likewise not RTO members. **Consequence for the build:** of
Arizona + New Mexico's ~40 GW of EIA capacity, only Farmington /
Aztec / Los Alamos-area plants inside the WACM BA (~0.2 GW) are
SPP. A state-based "AZ/NM = SPP West" cut would be wrong by
roughly two orders of magnitude.

## How the membership maps to EIA-860M (BA inventory)

EIA-860M Sep 2026 still uses pre-consolidation BA codes. Inventory
of the Operating sheet (nameplate MW):

| BA code | MW | Units | Disposition in this build |
|---|---|---|---|
| SWPP | 105,625.0 | 1,665 | **East** — the legacy SPP BA (East BAA) |
| WACM | 11,415.3 | 268 | **West** — consolidated into the West BAA (SPP ER26-3720) |
| WAUW | 1,128.3 | 46 | **West** — consolidated into the West BAA |
| PSCO | 17,225.8 | 327 | Excluded, EXCEPT Platte River's Rawhide (800.4 MW, override) |
| PACE | 20,004.0 | 334 | Excluded, EXCEPT Deseret's Bonanza + Solomon (526.9 MW, override) |
| PNM | 7,725.6 | 146 | Excluded (EDAM; incl. Tri-State's Pyramid, 186.0 MW — see below) |
| AZPS / SRP / TEPC | 12,810.9 / 19,134.0 / 5,059.2 | — | Excluded (Markets+ only) |
| NWMT | 4,265.1 | 116 | Excluded (BA did not consolidate; NorthWestern's SPP operations are its SD plants, already in SWPP) |
| WALC | 7,371.5 | 90 | Excluded (WAPA Lower Colorado BA did not consolidate; incl. 3,765.6 MW of USBR hydro — Glen Canyon 1,312.0, Hoover AZ/NV 2,078.8, Davis 254.8 — whose output WAPA-CRSP/RMR markets, partly to SPP West members) |
| SPA | 2,748.3 | 78 | Excluded (Southwestern Power Administration federal hydro in AR/MO/OK is not in the SPP BA; SPP membership of some SPA-marketed entities does not move the BA) |

Where the verified members' plants actually sit (Operating sheet):
- **Basin Electric (6,342.6 MW)** splits across the interconnection
  divide exactly as its membership does: SWPP 3,935.9 MW (Antelope
  Valley, Leland Olds, Pioneer, Lonesome Creek in ND; Deer Creek,
  Groton, Prairie Winds in SD; Culbertson in MT) = East, and WACM
  2,406.7 MW (Laramie River 1,863.0 + Dry Fork 483.7 + small WY) =
  West. The BA rule tags each side correctly with no override.
- **Tri-State (2,703.3 MW)**: WACM 1,821.2 MW (Craig 1,427.6, Limon,
  Burlington, Dolores Canyon Solar) = West. PSCO 696.1 MW (J.M.
  Shafer 396.9, Frank Knutson, Axial Basin Solar) and PNM 186.0 MW
  (Pyramid) are **excluded**: those BAs did not consolidate, SPP's
  tariff carves out a "Tri-State-West" zone rather than absorbing
  Tri-State's PSCO/PNM-footprint units, and no SPP source shows
  those units transferring. This 882.1 MW is the build's largest
  boundary judgement; it is quantified in summary.json
  (`excluded_tristate_nonconsolidated_ba_mw`) so the series can be
  re-cut if SPP publishes a unit-level West BAA roster.
- **Colorado Springs Utilities (1,115.2 MW)**: all in WACM = West
  (Front Range 554.3, Ray D Nixon 282.6, South Plant 245.1, hydro).
- **Platte River (800.4 MW operating + 223.0 MW planned)**: Rawhide
  is filed under **PSCO** — without the override, a founding
  transmission-owning member's entire fleet would fall out of the
  stack. Override applied (all PRPA-entity rows → West).
- **Deseret (526.9 MW)**: Bonanza (499.5 coal + 12.5 solar) and
  Solomon (14.9) filed under **PACE**. Override applied.
- **WAPA**: its in-footprint hydro is mostly USBR/USACE-entity
  plants inside WACM (759.9 MW) and WAUW (969.4 MW incl. Yellowtail
  278.2) — captured by the BA rule. WAPA-CRSP's flagship Glen
  Canyon (1,312.0 MW, WALC) is excluded with WALC; flagged above.
- **MEAN**: no generation in the western BAs (its only EIA-entity
  row is a 27.6 MW Kansas plant in SWPP = East). No plant effect.
- **City of Page (AZ), City of Aztec (NM), Warren AFB, Guzman,
  Tenaska, The Energy Authority**: no EIA-860M generation under
  their own entities in the western BAs (marketers / load-only).
- **Inside WACM/WAUW but NOT members**: Xcel's Comanche (CO) units
  2/3 (1,252.8 MW, PSCO entity) and Black Hills Power's fleet
  (~813.5 MW across WACM) are counted West because the stack is a
  BA-footprint stack — the same principle by which non-member IPPs
  inside SWPP are counted East in every NBR stack. Their presence
  is the main reason the EIA West anchor exceeds SPP's published
  West nameplate (see README gap discussion).

**Tagging rule (as built):** East ⟺ BA = SWPP. West ⟺ BA ∈
{WACM, WAUW}, or Entity ∈ {Platte River Power Authority, Deseret
Generation & Tran Coop} under any BA. State never determines the
tag; BA does. Edge cases: **Nebraska** — legacy NE generation is
SWPP = East (12,090.4 MW); the only western-BA Nebraska generation
is 58.8 MW of small solar/wind in WACM (incl. Kimball Wind, an SPP
roster entity) = West; MEAN's expansion changes no Nebraska plant
tags. **South Dakota** — SWPP SD (4,304.7 MW, incl. Basin's fleet)
= East; WACM SD (499.9 MW: Black Hills' Ben French/Lange, IPP wind/
solar) = West; the Missouri River mainstem USACE plants in SD are
filed under SWPP = East. **Montana** — SWPP MT (168.2 MW, incl.
Basin Culbertson) = East; WAUW MT (523.0 MW, USBR Yellowtail etc.)
= West; NWMT MT (Colstrip etc., ~4.3 GW) is not SPP at all.

---

# Part 2 — v2 adjustments

### A. ADD — Gaines County CTG, TX, East, Natural Gas, +1,160.0 MW, Dec 2028
Southwestern Public Service (Xcel) self-build gas CT plant, Gaines
County, TX. In SPS's NMPRC Case 25-00066-UT filing (Table 1, SPS
self-build projects: "Gaines County CTG, Gas Thermal, 1,160 (winter
max), 12/1/2028"). The NMPRC approved SPS's construction programme
in summer 2026 and the PUCT approved the two Texas gas plants with
cost caps in Oct 2026. **Not in the EIA Planned sheet** (verified
in-file: no Gaines rows in the SPP cut). MW basis caveat: the
filing figure is winter max capacity, not an EIA nameplate; it is
used as filed and flagged. Grid-connected utility plant built for
SPP resource adequacy (ERAS-era procurement) — not co-located
behind-the-meter generation.
Sources: SPS Case 25-00066-UT testimony,
https://www.synapse-energy.com/sites/default/files/25-00066%20NMDOJ%20Direct%20Testimony%20Devi%20Glick%2025-105.pdf ;
CleanTechnica (PUCT approval),
https://cleantechnica.com/2026/10/01/texas-puc-greenlights-coal-plant-closure-renewables-construction-saving-millions-of-gallons-of-water-every-year/
Confidence: Medium (approvals and date verified; MW basis is the
filing's winter-max figure).

### B. ADD — Tolk Station CTG, TX, East, Natural Gas, +928.0 MW, Apr 2029
Same SPS case: "Tolk Station CTG, Gas Thermal, 928 (winter max),
4/2/2029", at the Tolk coal site (Lamb County, TX). Not in the EIA
Planned sheet. Flag: Global Energy Monitor lists a 1,325 MW Tolk
gas unit as pre-construction — a different (larger) figure than
the regulatory filing's 928 MW winter max; the filing figure is
used. Same BTM treatment as A (grid plant).
Sources: as A; GEM, https://www.gem.wiki/Tolk_Station
Confidence: Medium.

### C. RETIME — Craig (CO) Unit 3, West, Coal, 534.8 MW, Dec 2029 → Jan 2028
Tri-State's Dec 2023 Electric Resource Plan retires Craig Units 2
and 3 in 2028 — Unit 3 in January 2028, Unit 2 in September 2028 —
reaffirmed by Tri-State in Apr 2025. DOE's Order No. 202-25-14B
(Jun 24, 2026) states the same: "Unit 2 and Unit 3 are slated to
retire in 2028." EIA's Unit 2 date (Sep 2028) already matches and
is kept; its Unit 3 date (Dec 2029) is the stale pre-ERP schedule.
Sources: DOE Order No. 202-25-14B,
https://www.energy.gov/documents/order-addressing-arguments-raised-rehearing-202-25-14b ;
GEM, https://www.gem.wiki/Craig_Station
Confidence: Medium-High.

### D. RETIME — Tolk Units 1/2, East, Coal, 2×567.9 MW, Dec 2028 → Mar 2029
SPS sought a three-month extension of Tolk's retirement (from
Dec 31, 2028 through Mar 31, 2029) in Case 25-00066-UT; the NMPRC
approved the delay to March 2029 in May 2026, and the Oct 2026
PUCT/NMPRC decisions confirm retirement "in early 2029". This is a
plant-specific regulatory approval, not a blanket delay assumption.
Sources: GEM, https://www.gem.wiki/Tolk_Station ; SPS Case
25-00066-UT testimony (see A).
Confidence: High.

### E. RETIME — Rawhide new gas units (G, H, LM3, LM4, LM5), West, Natural Gas, 5×44.6 MW, Mar 2028 → Dec 2029
Platte River's Jul 28, 2026 energy-supply update to its owner
communities schedules "2029: 200 MW aeroderivative turbines;
200+ MW wind; retirement of Rawhide Unit 1" — i.e. the new Rawhide
gas units land in 2029, with the coal retirement, not in EIA's
Mar 2028 (the older IRP schedule; GEM still shows 2028). Dec 2029
is a placeholder month; the year is the published fact. EIA MW
(223.0 total) is kept (PRPA's "200 MW" is its nominal figure).
Source: City of Longmont council communication, Jul 28, 2026,
https://longmont.primegov.com/api/compilemeetingattachmenthistory/historyattachment/?historyId=a5615ea6-b3ae-44cf-9b36-963e0fe79269
Confidence: Medium.

## Checked and confirmed KEEP (no change)
- **Craig Unit 1, West, Coal 446.4 MW, Dec 2026 (v1)** — the unit
  was slated to retire Dec 31, 2025; DOE §202(c) orders kept it
  available all through 2026: Order 202-25-14 (Dec 30, 2025, to
  Mar 30, 2026), 202-26-21 (to Jun 28, 2026), 202-26-31 (to
  Sep 26, 2026), and 202-26-49 (Sep 25, 2026; effective Sep 27 –
  Dec 25, 2026, with "time for an orderly ramp-down after
  Dec. 25"). EIA's Dec 2026 retirement is consistent with the
  current order chain. KEEP Dec 2026, flagged: a fifth order would
  push the retirement into 2027. The orders are addressed to
  Tri-State **and SPP** (West BAA dispatch) — direct confirmation
  that Craig sits in SPP West. Source:
  https://www.energy.gov/documents/doe-order-no-202-26-49
- **Bison Generation Station, ND, East, Gas 1,518.0 MW (2029/2030)**
  — Basin Electric: board approval Jan 2025, ND PSC siting order
  Aug 7, 2025, air permit Dec 29, 2025, $3.926bn, construction
  under way (PCL/Burns & McDonnell); Unit 1 in 2029, Unit 2 in
  2030. Basin's published capacity is 1,470 MW (2×735); EIA's
  1,518.0 (2×496 CT + 2×263 ST) is the nameplate basis and is
  kept. KEEP. Sources: Basin Electric project flyer,
  https://basinelectric.com/_files/pdf/Generation/2026-BGS-Information-Flyer.pdf ;
  ENR, https://www.enr.com/articles/62472-pcl-construction-will-build-4b-natural-gas-plant-in-north-dakota
- **Evergy Viola (765.0 MW, Jan 2029) + McNew (765.0 MW, Jan 2030),
  KS, East, Gas** — the KCC approved settlement agreements in 2025
  for Evergy Kansas Central's two combined-cycle plants (Evergy's
  announced 705 MW nominal each: Sumner County 2029, Reno County
  2030). EIA nameplate 765.0 and dates match. KEEP.
- **Horizon → Williams Creek Generating Station, CO, West, Gas
  480.0 MW (10×48.0), Jul 2028** — Colorado Springs Utilities'
  plant: 10 ProEnergy PE6000-class units; CSU's own figure is
  400 MW (its site-rated/nominal output at ~6,000 ft elevation;
  48 MW is the unit nameplate, so EIA's 480.0 stands on this
  stack's nameplate basis). In Mar 2026 CSU relocated the plant
  from the Horizon Utility Campus to the Lower Williams Creek
  site southeast of Fountain (airport exhaust-plume safety),
  renaming it Williams Creek Generating Station; the move needs
  new air and county approvals — schedule risk to the Jul 2028
  date is real but no revised date is published. KEEP MW/date,
  flagged. Sources: CSU,
  https://www.csu.org/blog/horizon-utility-campus and
  https://www.csu.org/current-projects/horizon-campus
- **Rawhide Unit 1 coal, West, 293.6 MW, Dec 2029** — PRPA's 2024
  IRP retires Rawhide Unit 1 by end-2029; PRPA's board reporting
  (Oct 29, 2026) confirms it "remains on track to retire its
  Rawhide coal-fired plant in 2029" even as the 2030 noncarbon
  date was dropped. KEEP. Source: GEM,
  https://www.gem.wiki/Rawhide_Energy_Station
- **Comanche (CO) Unit 3, West, Coal 856.8 MW, Dec 2030; Unit 2,
  396.0 MW, Dec 2026** — Xcel Colorado's plan retires Comanche 3
  by end-2030 (kept); Unit 2's EIA Dec 2026 sits one year after
  Xcel's original 2025 target — no firmer published date found,
  KEEP with flag. These units are in the stack via the WACM BA
  rule although Xcel is not an RTO member (see Part 1).
- **Ray D Nixon Unit 1, West, Coal 207.0 MW, Dec 2029** — CSU's
  2020 agreement closes Nixon before 2030 (end-2029), matching
  EIA. CSU sought legislation in 2026 (SB26-022) that would allow
  keeping Nixon open past 2029 — a live extension risk, not an
  approved change. KEEP, flagged.
- **Tolk-area SPS renewables in EIA** (Yellow House/Lariat wind,
  Oneida solar in the same SPS filing) — the filing's surplus-
  interconnection wind/solar at Tolk/Harrington (300 + 800 MW wind,
  254 MW solar, 2028–2029) could not be matched one-to-one to EIA
  Planned rows in the time available; no change proposed (see
  unverified items).
- **No BTM exclusion found in either BAA.** The large East gas
  additions (Evergy, Basin Bison, PSO Comanche (OK), AECC Naples,
  OPPD/NPPD units) are grid-connected utility plants; data-center
  load in SPP (e.g. Google Pryor, OK; the proposed 500+ MW
  "Project Catalyst" in Kansas) is served through the grid under
  utility tariffs, not by co-located generation whose grid
  connection is consumed by the load. In the West, no co-located
  data-center gas plant was found among the new members' projects.
  SPP's Jul 20, 2026 FERC informational report on large/co-located
  load (EL26-68) describes load-side proceedings, not BTM
  generation in the EIA cut. Finding stated either way, per the
  standing rule: nothing to exclude in v2.

## Could not verify / flagged, no adjustment proposed
- **Comanche (OK), OK, East, Gas 1,372.8 MW, Sep 2029, status (P)**
  — PSO's planned 2-unit CC is the largest single v1 addition and
  rests on EIA alone at the earliest planning status; no approval
  evidence found. Kept (no termination evidence), high paper risk.
- **Naples Power Plant, TX, East, Gas 900.0 MW, Dec 2028, (P)** —
  Arkansas Electric Cooperative Corp project in Morris County, TX
  (consistent with a ~915 MW Morris County SPP queue entry);
  approval status unverified. Kept, flagged.
- **West paper pipeline**: Rail Tie Wind 504.0 MW (2029, L),
  Dutchman Solar 499.0 + Battery 499.0 (2029, L), Cowboy Solar I
  400.0 + 400.0 battery (2028, P), Cowboy Solar II 365.0 + 200.0
  (2027, T/P) — queue-stage Wyoming projects; EIA is the only
  source; kept with status flags.
- **SPS life extensions** for Nichols Units 1/2, Maddox Unit 1 and
  Plant X Unit 4 were *requested* in Case 25-00066-UT; whether the
  2026 NMPRC/PUCT orders granted them could not be confirmed.
  EIA retirement dates (2027–2034) kept.
- **Jeffrey Energy Center Unit 3 (720.0 MW, Jan 2030), La Cygne
  Unit 1 (873.0 MW, Jan 2032), Lawrence Units 4/5 (517.0 MW,
  Jan 2032)** — Evergy Kansas coal retirements taken at EIA dates;
  not individually verified against Evergy's current IRP.
- **Bonanza (Deseret), West, Coal 499.5 MW** — EIA shows no planned
  retirement; no Deseret retirement announcement found. Kept as
  running through 2036.

## Candidates NOT proposed (insufficient evidence for MW/date)
- **Tri-State Craig-site replacement gas, 307 MW + 200 MW battery**
  — Tri-State's approved ERP puts a 307 MW gas plant and 200 MW of
  battery storage at the Craig Station site to replace Craig's
  capacity, but no in-service date is pinned in the sources found
  (ERP horizon 2028–2030). Not added; flagged in summary_v2.json.
  Source: Colorado Sun via Tri-City Record,
  https://www.tricityrecordnm.com/articles/news/trump-administration-forces-coal-power-plant-in-craig-to-continue-operating/
- **SPP ERAS queue pool, ~13,300 MW** — SPP's Expedited Resource
  Adequacy Study window (Sep–Oct 2025) drew 13.3 GW of submitted
  projects (SPP FERC filing, ER26-156), on top of the regular
  queue. Not itemised to plant/MW/date in public sources; the
  Gaines/Tolk CTGs above are the ERAS-era projects that could be
  verified individually. Not added in aggregate.
- **Horizon/Williams Creek 100 MW battery** — in CSU's campus
  plans (construction from Q2 2026, complete 2028) but no matching
  EIA Planned row was found in the West cut; MW/date split
  unverified against EIA. Not added.
