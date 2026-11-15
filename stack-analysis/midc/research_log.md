# MIDC capacity stack — v2 research log

Built 2026-11-15. v2 = v1 (EIA-860M only) + 2 named manual adjustments
(3 row-level changes: 0 retimes, 3 new rows), each with an online
source. All sources accessed 2026-11-15. Basis throughout is nameplate
MW. Every EIA Planned unit ≥200 MW in the MIDC cut (25 units,
11,250.0 MW) was web-checked; the KEEP list below is the result.

## The adjustments

### A. FUEL SWITCH — TransAlta Centralia Generation Unit 2, WA, Coal → Natural Gas, 729.9 MW
Coal retirement ADDED Dec 2026 (729.9 MW); gas addition ADDED Dec 2028
(729.9 MW). EIA has neither: the Operating sheet (plant 3845, Lewis
County, BPAT) carries Unit 2 as coal, status OP, with **no Planned
Retirement Year**, and the Planned sheet contains no conversion (its
only Centralia row is a separate 200 MW battery project, kept in v1).
The facts: Unit 2 was required to cease coal combustion at the end of
2025 under Washington law and the 2011 TransAlta Memorandum of
Agreement (RCW 80.80.100); it burned its last coal in December 2025
(stopped Dec 19, 2025 per Global Energy Monitor's reporting) and has
produced zero electricity since. DOE then issued successive FPA
§202(c) emergency orders — the fourth running through Dec 12, 2026 —
requiring the unit to remain *available* as a coal plant; TransAlta
does not expect to restart coal generation under them. Booking: the
coal retirement is placed in **Dec 2026**, the current order's expiry
and the anchor boundary — the same treatment MISO v2 gave Belle
River Unit 1 (converted Dec 2025, booked Dec 2026). On Dec 9, 2025
TransAlta signed a 16-year fixed-price tolling agreement with Puget
Sound Energy to convert Unit 2 to natural gas: 700 MW contracted
capacity, ~US$600m capex, target commercial operation **late 2028**,
FID after approvals in early 2027, operation through Dec 31, 2044.
The Jul 31, 2026 SEPA Mitigated Determination of Nonsignificance
(WA Dept. of Ecology / Southwest Clean Air Agency) confirms the
project as filed: Unit 2 "ceased using coal as a fuel source at the
end of December 2025 and will generate electricity from natural gas
after completion," maximum **723 net MW**, fuel via a new 1,500-ft
gas lateral, customer PSE. The gas leg is booked at the EIA nameplate
**729.9 MW** (the stack basis is nameplate; MISO v2 fuel switches at
Belle River and Petersburg kept nameplate MW unchanged across the
switch). Net effect across 2026–2036 is zero; the 2027–2028 gap is
real. This is a utility grid plant built to serve PSE load — not
behind-the-meter.
Sources: TransAlta Form 6-K, Dec 9, 2025,
http://pdf.secdatabase.com/1333/0001171843-25-007842.pdf;
SEPA MDNS, Jul 31, 2026,
https://www.swcleanair.gov/docs/SEPA/Determinations/2026-07-31 TransAlta Generation - Ecology SEPA MDNS Determination.pdf;
Global Energy Monitor, https://www.gem.wiki/Centralia_Power_Plant;
DOE-order reporting,
https://www.ainvest.com/news/centralia-doe-coal-order-noise-gas-conversion-story-2609/.
Confidence: Medium-High (agreement signed and SEPA issued; FID and
WUTC approval still pending).

### B. ADD — Columbia Generating Station extended power uprate, WA, Nuclear, +186.0 MW, Dec 2031
Plant 371, Benton County, BPAT; EIA nameplate 1,200.0 MW (operator
states current output 1,207 MW — the increment is unaffected). The
Bonneville Power Administration approved implementation of the
Extended Power Uprate in May 2025 after 18 months of analysis:
~$700m, **+162 MWe** from the EPU plus **+24 MWe** from energy-
efficiency upgrades in the same outages, **+186 MW total by 2031**,
executed as ~30 modifications staged across the 2027, 2029, and 2031
biennial refuelling outages. Booked as a single addition at
completion, Dec 2031 (the MISO v2 Fermi 2 uprate treatment).
Energy Northwest intends to submit the NRC licence amendment request
in 2028 — i.e., the uprate is approved by the funder/owner but not
yet licensed. The plant's operating licence runs through Dec 2043
(2012 renewal), and Energy Northwest plans to pursue subsequent
licence renewal (+20 years); no retirement appears in any window.
Not in the EIA Planned sheet (verified in-file).
Sources: ANS Nuclear Newswire, Oct 1, 2026,
https://www.ans.org/news/2026-10-01/article-8410/modernizing-for-more-megawatts-columbias-epu-journey/;
POWER Magazine, May 23, 2025,
https://www.powermag.com/only-nuclear-power-plant-in-u-s-northwest-set-to-add-generating-capacity/;
World Nuclear News,
https://world-nuclear-news.org/articles/go-ahead-for-columbia-plant-uprate.
Confidence: Medium-High.

## Checked in detail — NO adjustment

### Colstrip Units 3 & 4, MT, Coal, 2×823.7 = 1,647.4 MW (NWMT) — KEEP operating, no retirement
EIA carries no Planned Retirement Year for either unit (Units 1/2,
358.0 MW each, retired Jan 2020 and appear in the trailing). The
required checks, unit by unit (3 and 4 share one ownership/operator
structure and one answer):
- **Ownership transfer (the headline event):** Puget Sound Energy's
  25% share (~370 MW) and Avista's 15% share both transferred to
  NorthWestern Energy effective **Jan 1, 2026** (Avista agreement
  Jan 2023; PSE Abandonment & Acquisition Agreement Jul 30, 2024;
  NorthWestern Colstrip 370Pu LLC FERC filings for sales from the
  acquired share from Jan 1, 2026). NorthWestern now holds ~55% of
  Units 3/4 (Unit 3: NorthWestern 40% / Talen 30% / PGE 20% /
  PacifiCorp 10%; Unit 4: NorthWestern 70% / PGE 20% / PacifiCorp
  10%). The Washington UTC's Final Order 05 in Docket UE-240729
  (served Dec 19, 2025) holds that the units will be "retired"
  *within the meaning of CETA* when PSE transfers them — i.e.,
  Washington law treats the ownership exit as retirement from
  Washington supply while the physical units keep running for
  Montana. A stack of physical capacity must not book that as a
  retirement.
- **Retirement status:** none announced for the units. NorthWestern
  states it will operate Units 3/4 as baseload **through
  approximately 2042**; Montana DEQ's Final Supplemental EA for the
  Rosebud Mine Amendment 5 (Jan 28, 2026) states "The Colstrip Power
  Plant is projected to operate until 2042 (NorthWestern Energy,
  2026)."
- **Other owners' exits are not retirements:** PGE's 2023 Clean
  Energy Plan / IRP states it will "discontinue usage of and exit its
  20 percent ownership of the Colstrip plant by the end of 2029"
  (Oregon SB 1547 requires Colstrip out of PGE rates by 2035,
  depreciation by 2030); Mar 2023 reporting has PacifiCorp and PGE
  "exiting Colstrip in 2030 rather than 2025." Exiting owners sell or
  abandon shares; the units' capacity does not leave the stack.
- **Emissions-rule status:** the owners litigated the EPA's 2024
  MATS update (compliance, they argued, would make Colstrip
  uneconomic) and the 2024 GHG rules; both rules are under rollback
  pressure from the current administration, and in Jul 2024
  NorthWestern asked the Montana PSC for a Reliability Compliance
  Balancing Account to *fund* MATS compliance and keep operating to
  at least 2042. Montana-specific law (including state restrictions
  enacted around Colstrip decommissioning/ownership, partly struck
  down in Oct 2022 federal court) is part of the plant's unusual
  legal situation, but no rule in force produces a 2026–2036 shutdown
  date. Per the brief: state clean-energy deadlines in WA/OR are
  evidence about *those states' shares*, not about the Montana
  plant's operation.
Conclusion: v1's silence and v2 agree — Colstrip 3/4 remain in the
stack through 2036. Flagged in `summary_v2.json` so a future build
revisits it if NorthWestern's 2042 intent changes.
Sources: WA UTC Final Order 05, Docket UE-240729,
https://apiproxy.utc.wa.gov/cases/GetDocument?docID=585&year=2024&docketNumber=240729;
FERC deficiency response, NorthWestern Colstrip 370Pu LLC (Docket
ER26-129), http://montanapushback.org/pdf/northwestern-response-to-ferc-deficiency-letter.pdf;
Global Energy Monitor, https://www.gem.wiki/Colstrip_Steam_Plant;
Montana DEQ Rosebud AM5 Final Supplemental EA, Jan 2026,
https://deq.mt.gov/files/Land/CoalUranium/Rosebud AM5 Supplemental Environmental Assessment Final.pdf;
PGE 2023 CEP/IRP Appendix E,
http://assets.ctfassets.net/416ywc1laqmd/3K90DGpYCyqQu9RoLagThu/e85d8569e4a1e9f111ad5499504e5aea/2023_CEP-IRP_Appendix_E.pdf;
RMI Colstrip case study, Jan 2025,
https://rmi.org/resources/energy-reinvestments-in-the-intermountain-west-can-save-ratepayers-hundreds-of-millions.
Confidence: High that no 2026–2036 retirement should be booked.

### Behind-the-meter / data-center scan — no exclusion
Oregon and Washington host 5+ GW of proposed data centers along the
Columbia River, so the scan was explicit:
- **VoltaGrid / Vantage, Quincy, WA — the one true BTM plant found.**
  On Jan 27, 2026 Grant County PUD approved a PPA for a **12 MW**
  on-site gas turbine (14 mobile engines, trucked gas) *behind the
  customer's meter* at the Vantage Data Centers campus, a temporary
  bridge until the Wanapum–Mountain View transmission line is
  finished in 2029. Under the standing rule it counts **0 MW** of grid
  addition; it is also below the ≥200 MW check threshold and absent
  from EIA, so no row is created. Logged here so the finding is on
  record either way, as briefed.
- **Sunstone Solar, OR (Amazon)** — Amazon Data Services acquired the
  1,200 MW solar + 1,200 MW battery project out of Pine Gate
  Renewables' Chapter 11 (closed Feb 27, 2026, $83m; EFSC transfer
  approved Jun 26, 2026) to support its eastern-Oregon data centers.
  It is a grid-scale, grid-connected plant with an EFSC site
  certificate — ownership by a data-center company does not make it
  co-located BTM generation. Counted in full (KEEP below).
- **Blacks Creek Solar, ID (Meta)** — output serves Meta's Kuna data
  center *through* Idaho Power's grid under a PPA structure, plus
  general Idaho Power load. Grid plant; counted in full.
- **Williams Northwest Pipeline expansions** (Rockies Columbia
  Connector, Valley Trail) are gas *pipelines* marketed partly on
  future BTM data-center sales; no generation MW exists to book.
  Washington's 2026 CETA amendment now regulates BTM gas sales to
  data centers — relevant context, no stack effect.
- **PSE gas turbines at an undisclosed Washington site** (reported by
  Sightline Institute via Columbia Riverkeeper, Jun 2026): six
  turbines contracted for data-center-driven load; MW and site
  undisclosed — flagged candidate, not added.
- **Grant PUD** is also weighing utility gas plants near Moses
  Lake/Quincy and an interest in an Idaho gas plant (Jan 2026
  workshop, per Riverkeeper) — no MW, site, or approval; not added.
Sources: Columbia Riverkeeper, *Dirty Secrets* report, Jun 1, 2026,
https://www.columbiariverkeeper.org/2026/dirty-secrets-data-centers-drive-demand-for-gas/;
Columbia Insight, Mar 26, 2026,
https://columbiainsight.org/new-gas-pipelines-in-gorge-eastern-washington-could-directly-supply-data-centers/;
Vantage/VoltaGrid account, Jun 3, 2026,
https://www.ecclesiaterra.org/post/twenty-years-of-yes-in-quincy.

## Checked and confirmed KEEP (no change) — EIA Planned ≥200 MW
- **Sunstone Solar, OR, Solar 1,200.0 + Battery 1,200.0 MW, Dec 2027,
  L** — EFSC site certificate Nov 18, 2024 (1,200 MW PV, up to
  7,200 MWh storage); developer Pine Gate Renewables filed Chapter 11
  in Nov 2025; Amazon's Oregon Solar 1, LLC acquired the project
  (closed Feb 27, 2026) and EFSC approved the certificate transfer
  Jun 26, 2026 with **no design changes**; construction must begin by
  Nov 18, 2027. EIA MW matches the certificate; Dec 2027 for the full
  2,400 MW is aggressive (preconstruction compliance covered 1,200 MW
  solar + only 200 MW of battery before the bankruptcy hold) — keep
  with a phasing-risk flag.
  Sources: https://www.oregon.gov/energy/facilities/Facilities%20library/2026-05-20-SSPAMD1-RFA1.pdf;
  https://oregon.gov/energy/facilities/Facilities%20library/2026-06-26-SSPAMD1-Final-Order-on-AMD1.pdf
- **Deschutes Solar and BESS, OR, Solar 1,000.0 + Battery 1,000.0 MW,
  Nov 2029, L** — BrightNight (DECH bn, LLC), Wasco County, 13,626
  acres. As of the Sep 2026 EFSC update the project is still in
  **preliminary Application for Site Certificate completeness
  review** — not approved, no certificate. EIA's L status is
  literally accurate and the Nov 2029 date is a developer target.
  Keep — no termination evidence — with a paper-project flag.
  Source: https://digitalcollections.library.oregon.gov/assets/downloadwiz/1520384
- **Cedar Island Solar LLC, OR, Solar 800.0 MW, Dec 2031, L** —
  Enlight Renewable Energy, Sherman County; pre-construction; BPA
  point-to-point transmission service executed. GEM lists a stale
  2026 commissioning year from queue data; EIA's Dec 2031 retained.
  Keep with a paper-project flag.
  Source: https://www.gem.wiki/Cedar_Island_Solar
- **Hop Hill Solar Generation and BESS, WA, Solar 500.0 + Battery
  500.0 + Wind 200.0 MW, Sep 2031, L** — BrightNight-affiliated
  (HOHI bn, LLC), Benton County; the WA solar PEIS cumulative-impacts
  chapter lists Hop Hill at 500 MW solar + up to 500 MW storage in
  Planning/Development, interconnecting to BPA at Midway or Wautoma.
  Consistent with EIA. Keep, early-stage flag.
  Source: https://stg.waeprogrammaticeis.wspis.com/documents/Final_EIS/Chapter 4 - Cumulative Impacts.pdf
- **Blacks Creek Solar, ID, Solar 400.0 MW, Jun 2027, U** — rPlus
  Energies' Blacks Creek Energy Center, Ada County (400 MWac /
  520 MWdc); $650m+ debt + tax-equity financing closed Mar 17, 2026;
  **construction began Jul 2026** (rPlus, Jul 21, 2026); delivers to
  Idaho Power's grid, supporting Meta's Kuna data center via PPA and
  general load (grid plant, not BTM). Developer targets operations
  2027–2028; EIA Jun 2027 kept.
  Sources: https://www.rplusenergies.com/rplus-energies-advances-two-major-utility-scale-projects-in-idaho;
  https://www.power-technology.com/news/rplus-energies-secures-650m-blacks-creek/
- **Obsidian Solar Center, OR, Solar 400.0 MW, Dec 2028, L** — EFSC
  site certificate Feb 2022 (400 MW + 50 MW battery; the battery is
  not a separate EIA row). The project **missed its Feb 25, 2025
  construction-start deadline for lack of an interconnection**;
  Amendment 2 (approved Jun 13, 2025) extended the start deadline to
  Feb 25, 2028, with completion up to 3 years after commencement.
  EIA's Dec 2028 is therefore the optimistic edge — keep, with an
  explicit slip-risk flag (see candidates).
  Source: https://www.oregon.gov/energy/facilities/Council%20Meetings/2026-02-13-EFSC-Item-H-Staff-Report-Compliance-Program-Update.pdf
- **Nolin Hills, OR, Wind 300.0 + Solar 300.0 MW, Dec 2027, P** —
  EFSC lists the Nolin Hills Wind Power Project as **Approved**
  (Jul 2023), 600 MW in Umatilla County, split 340 MW wind /
  260 MW solar, construction-start deadline Jul 2026. EIA's 300/300
  split differs from EFSC's 340/260; the total (600 MW) agrees. EIA
  kept on the stack's consistent nameplate basis; split difference
  noted, no adjustment.
  Source: https://www.oregon.gov/energy/facilities/Council%20Meetings/2026-02-13-EFSC-Item-H-Staff-Report-Compliance-Program-Update.pdf
- **Lower Snake Solar Generation BESS, WA, Solar 300.0 + Battery
  300.0 MW, Oct 2029, L** — Puget Sound Energy project (per developer
  pipeline listings). No contrary evidence. Keep.
- **Royal Slope, WA, Solar 260.0 + Battery 260.0 MW, Oct 2027, T** —
  approvals received per EIA; no contrary evidence. Keep.
- **Salmonfly Solar and Storage, OR, Solar 247.0 + Battery 247.0 MW,
  Feb 2029, L (PGE)**; **Arco Wind and Solar, ID, Wind 206.0 + 153.0
  MW, 2027–2028, T (PACE)**; **Centralia Battery Energy Storage
  System, WA, Battery 200.0 MW, Dec 2028, L (PSEI)** — at the Centralia
  site but a separate project from the Unit 2 conversion; **Greenwater
  BESS, WA, Battery 200.0 MW, Dec 2026, V**; **Tualatin BESS, OR,
  Battery 200.0 MW, Dec 2027, L (PGE)**; **Anthelope Hills, MT, Solar
  200.0 + Battery 200.0 MW, Dec 2027, L (NWMT)** — no contrary
  evidence found for any of these. Keep.
- **Retirements KEEP:** the entire v1 in-window retirement list is
  13 units / 88.0 MW (largest: Northeast (WA) gas 61.8 MW, Dec 2035;
  Carmen Smith hydro 9.9 MW, 2030). None is large enough to trigger
  the ≥200 MW check; no contrary evidence surfaced. Chehalis gas
  (593.3 MW, Dec 2043) sits beyond the window in both versions.
- **Out of scope, verified absent:** North Valmy, NV (Units 1/2 now
  coded Natural Gas in EIA, 277.2 + 289.8 MW, NEVP) and Jim Bridger,
  WY (2,326.0 MW, PACE) — neither enters the WA/OR/ID/MT cut.

## Could not verify / flagged, no adjustment proposed
- **Haymaker Hybrid, MT, Wind 630.0 MW, Oct 2031, P (kept)** — the
  one genuine conflict in the KEEP list. Clearway's Jul 23, 2024
  announcement of a 25-year PSE PPA describes "the Haymaker wind
  farm, a **315 MW** facility" in Wheatland/Meagher Counties with
  construction from 2026 and commercial operations **by 2028**.
  EIA/GEM/queue sources describe a **630 MW** project (Haymaker
  Energy Project LLC) for 2028 (GEM) or Oct 2031 (EIA). The 315 MW
  PPA may be a first phase or PSE's contracted share of a 630 MW
  nameplate project, but no source found reconciles the two figures.
  Kept at EIA 630 MW / Oct 2031 on the stack's nameplate basis, with
  the conflict flagged in `summary_v2.json`; a retime to 2028 would
  move 630 MW three years earlier and is NOT booked on conflicting
  secondary evidence (cf. MISO v2's handling of MEC).
  Sources: https://www.wsgr.com/print/v2/content/49028280/Firm-Advises-Clearway-on-25-Year-Power-Purchase-Agreement-with-Puget-Sound-Energy.pdf;
  https://www.gem.wiki/Haymaker_Hybrid_wind_farm
- **Deschutes Solar and BESS (2,000.0 MW, Nov 2029)** — kept, but it
  is the pipeline's largest unapproved project: still in EFSC
  completeness review in Sep 2026, opposed locally, no certificate,
  no announced offtake. Treat its 2029 date as aspirational.
- **Sunstone battery phasing (1,200.0 MW, Dec 2027)** — pre-bankruptcy
  preconstruction covered only 200 MW of the 1,200 MW battery; a
  phased battery build is likely even if the solar date holds.

## Candidates NOT proposed (insufficient evidence for MW/date)
- **Cascade Advanced Energy Facility (SMR), WA, 320 MW initial /
  960 MW full** — Energy Northwest + X-energy + Amazon, adjacent to
  Columbia Generating Station: up to 12 Xe-100 modules × 80 MW.
  Status Nov 2026: NRC **pre-application** only; construction-permit
  application targeted end-2026, permit expected 2028, construction
  from ~2030, operations in the 2030s; Fluor engaged Nov 5, 2026 for
  nuclear-island engineering. No construction permit, no booked COD
  year — flagged at both 320 MW and 960 MW in `summary_v2.json`,
  not added (same treatment as MISO v2's Constellation uprates).
  Sources: https://en.wikipedia.org/wiki/Washington_Xe-100_reactor_site;
  https://www.securities.io/fluor-wins-nuclear-island-services-contract-for-cascade-smr-project/
- **Badger Mountain Pumped Storage, WA, 500 MW** — closed-loop
  project in Douglas County listed as Planning/Development in the WA
  PEIS; no FERC licence or COD found. The anchor's entire pumped-
  storage fleet is 314.0 MW, so this would more than double it —
  flagged, not added.
  Source: https://stg.waeprogrammaticeis.wspis.com/documents/Final_EIS/Chapter 4 - Cumulative Impacts.pdf
- **PSE undisclosed-site gas turbines** — see BTM scan; MW/site
  undisclosed. Not added.
- **Yellow Rosebush Energy Center, OR, 800 MW solar + 800 MW
  storage** (Savion, Wasco/Sherman Counties; EFSC contested case in
  Apr 2026 updates) — **not in the EIA Planned sheet** for this cut
  and still in contested-case proceedings with no certificate or COD;
  noted here as the largest project EIA misses entirely in Oregon.
  Flagged for the next vintage check; not added without a date.
  Source: https://digitalcollections.library.oregon.gov/assets/displaypdf/318865

## Anchor cross-check note (PNUCC)
PNUCC's 2025 Northwest Regional Forecast (Apr 2025) reports Northwest
utility generating resources of ~55,000 MW nameplate (2026, Power Act
footprint, Figure 3) against this build's 64,845.7 MW EIA anchor. The
~9.8 GW gap is definitional (see README.md): PNUCC is a utility
load-and-resource balance (utility resources incl. Canadian Treaty
entitlement and out-of-footprint utility plant; only PacifiCorp West
+ 1/3 of NorthWestern; merchant/IPP capacity excluded), while EIA is
a physical census of the four states (incl. 4,278.4 MW non-OP
nameplate in the snapshot). E3's Apr 2026 regional RA study, built on
PNUCC, works in ELCC/dependable MW (Greater Northwest existing
portfolio ≈46.7 GW ELCC in 2025) — a different basis again, driven
largely by hydro accreditation far below the 35,201.7 MW nameplate
hydro in this anchor. No adjustment follows from any of these; they
bound how the anchor should be quoted.
Sources: https://d588fb10-0cdf-4398-b6a6-77beee46f98e.filesusr.com/ugd/054dfe_9d7ac5503db4492fa204bee4a90d6af6.pdf;
https://www.nwcouncil.org/news/2025/07/24/pnucc-northwest-regional-forecast-update-july-2025/;
https://www.westernenergyboard.org/wp-content/uploads/2026-03-27-Olson-COSR-NWRA.pdf
