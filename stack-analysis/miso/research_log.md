# MISO capacity stack — v2 research log

Built 2026-11-14. v2 = v1 (EIA-860M only) + 12 named manual adjustments
(26 row-level changes: 10 retimes, 16 new rows), each with an online
source. All sources accessed 2026-11-14. Basis throughout is nameplate MW.

## The adjustments

### A. ADD — Cayuga Energy Complex, IN, Central, Natural Gas, +1,476 MW
2 units: CC1 738 MW Sep 2029, CC2 738 MW May 2030. Not in the EIA
Planned sheet (verified in-file: the only "Cayuga" hits in Planned are NY
Cayuga County solar/wind; the Operating sheet has only the existing Cayuga
coal Units 1–2, 531 MW each, Duke Energy Indiana, Vermillion Co., BA=MISO).
Two 1×1 advanced CC units, ~738 MW winter rating each, at the existing
Cayuga Generating Station; CPCN approved by IURC order Oct 29, 2025
(Cause No. 46193); ~$3.33bn; broke ground May 2026. Grid-connected
utility plant replacing coal — no data-center co-location; testimony
states it addresses "the needs of the MISO region" and cites a MISO
Generator Replacement Request (R1044). The "increase by 470 MW to
1,476 MW" in Duke releases is the Duke-system net after coal retirement;
gross 1,476 MW is the correct stack addition.
Sources: IURC OUCC case page
(https://www.in.gov/oucc/electric/key-cases-by-utility/duke-energy-rates/cayuga-generating-station-cpcn);
Duke/Pinegar testimony, Cause No. 46193
(https://iurc.portal.in.gov/_entity/sharepointdocumentlocation/026a0346-edea-ef11-be20-001dd80b89f5/bb9c6bba-fd52-45ad-8e64-a444aef13c39?file=46193_Duke%20Energy%20Indiana_Direct%20Testimony%20of%20Pinegar_021325.pdf).
Confidence: High.

### B. ADD — Cayuga coal Units 1 & 2 retirement, IN, Central, Coal, −1,062 MW
Unit 1 531 MW Jan 2030; Unit 2 531 MW Jan 2031. EIA has no planned
retirement for them (Operating sheet shows no Planned Retirement Year).
Duke's Nov 2024 IRP preferred portfolio retires them "by the start of
2030 and 2031, respectively," as the CC units replace them (EIA nameplate
531 MW each; winter rating 1,005 MW combined). Flag: Duke's Jun 2025
settlement with Reliable Energy requires a feasibility study on selling
the coal units to a third party for continued operation — retirement is
the plan, not yet a certainty; OUCC testimony says "will retire by 2032."
Source: Global Energy Monitor, https://www.gem.wiki/Cayuga_Generating_Station
(summarises IRP + settlement + Oct 2025 IURC approval).
Confidence: Medium.

### C. ADD — Legend Power Station, TX, South, Natural Gas, +754 MW, Jul 2028
754 MW CCCT, Port Arthur, Jefferson Co. PUCT approved Sep 11, 2025
($1.6bn, with $2.4bn hard cost cap across Legend+Lone Star); broke
ground Apr 2026; in service mid-2028. EIA Planned sheet has it (plant
68053, 754 MW, Jul 2028, status L) but coded BA=ERCO, which is why v1
excluded it. The ERCO code is an error: Entergy Texas operates entirely
on the MISO grid, and the PUCT filing (Docket 56693) states "the final
cost of the transmission network upgrades required for Legend will be
determined by the Midcontinent Independent System Operator (MISO)";
sister Entergy Texas plants in the same file (Orange County, Lone Star)
are coded BA=MISO. Coordinator confirmed the MISO attribution
independently (PUCT filing + Entergy release + Industrial Info).
Sources: Entergy,
https://www.entergy.com/news/entergy-texas-receives-puct-approval-for-two-power-plants-to-support-southeast-texas-growth;
PUCT Docket 56693 filing,
https://interchange.puc.texas.gov/Documents/56693_427_1514330.PDF;
Utility Dive,
https://www.utilitydive.com/news/texas-regulators-approve-2-entergy-gas-plants-with-24b-hard-cap/759981/.
Confidence: High (plant and MISO attribution both confirmed).

### D. ADD — DTE new gas plants, MI, Central, Natural Gas, +2,100 MW
Handy Township (Livingston Co.) 1,400 MW Dec 2031; Milan Township
(Monroe Co.) 700 MW Dec 2032. DTE's 20-year IRP filed with MPSC Sep 24,
2026 proposes two CC plants totalling 2.1 GW ($3.9bn Handy, $2.5bn Milan),
online by end-2031 and end-2032, replacing Monroe coal; carbon capture
to be added by 2035. Grid-connected utility plants (driven partly by
~2.4 GW new load incl. Oracle/Google contracts, but sited separately and
grid-injected — not BTM). MPSC review pending (up to 360 days) — IRP
proposal, not approval.
Sources: DTE,
https://www.dteenergy.com/us/en/newsroom/2026/Powering-the-next-generation--DTE-lays-out-plan-to-deliver-a-cleaner,-reliable-energy-future-for-Michigan-customers.html;
Planet Detroit / Canary Media,
https://planetdetroit.org/2026/11/dte-gas-plants-michigan-clean-energy-law/.
Confidence: Medium.

### E. ADD — Consumers Energy new gas plants (Karn + Thetford), MI, Central, Natural Gas, +1,500 MW
2 units, 750 MW each, Dec 2031 (split and month assumed — see below).
Consumers announced Mar 11, 2026 that its IRP (filed Jun 2026) includes
two new gas plants totalling 1.5 GW, repurposing existing sites at Karn
(Bay Co.) and Thetford Township (Genesee Co.), "fast-starting,
on-demand" grid plants. Per-unit MW split and in-service date were not
published in sources found — "completion around 2031" appears only in
secondary summaries. The 750/750 split and Dec 2031 date are explicit
assumed placeholders. MPSC approval pending.
Source: Consumers / Barchart,
https://www.barchart.com/story/news/694093/consumers-energy-unveils-electric-supply-plan-to-keep-energy-reliable-and-bills-lower.
Confidence: Low-Medium (total/sites verified; split and date assumed).

### F. ADD — Fermi 2 uprate, MI, Central, Nuclear, +177 MW, Jan 2036
Same Sep 2026 DTE IRP: upgrade to existing Fermi 2 nuclear plant adds
177 MW "beginning in 2036" (Jan 2036 placeholder). IRP proposal, not yet
approved.
Source: DTE release (see D).
Confidence: Medium.

### G. Fuel switch — Belle River Units ST1 + ST2, MI, Central, Coal → Natural Gas, 1,395 MW, 2026
Coal retirements retimed Dec 2028 → Dec 2026 (both units); gas additions
of 697.5 MW each booked Dec 2026. DTE's 2022 IRP moved Belle River's coal
exit from 2028 to 2026 and converts both units to gas peaking (Unit 1
Dec 2025, Unit 2 Dec 2026; $135m pre-approved Jul 2023 settlement).
Feb 2026 reporting: Unit 1 converted in 2025, Unit 2 on track for 2026;
EIA-860M Sep 2026 still lists both as coal with Dec 2028 planned
retirement — stale. Unit 1's Dec 2025 conversion is booked in 2026 as it
sits on the anchor boundary and EIA still shows coal. Same treatment as
PJM v2 Miami Fort.
Sources: Utility Dive,
https://www.utilitydive.com/news/dte-energy-resource-plan-irp-solar-coal-michigan-psc/635781/;
Global Energy Monitor, https://www.gem.wiki/Belle_River_Power_Plant.
Confidence: Medium-High on conversion; Medium on exact months.

### H. Fuel switch — AES Petersburg Units 3 + 4, IN, Central, Coal → Natural Gas, 1,341.8 MW, 2026
Coal retirements added Jun 2026 (Unit 3, 670.9 MW) and Dec 2026 (Unit 4,
670.9 MW); gas additions of the same MW/dates. v1 has no Petersburg coal
rows at all — the units sit in the anchor as coal. IURC approved the
coal-to-gas conversion Nov 2024 ($1.1bn; AES: first IOU in Indiana to
stop burning coal). Unit 3 outage Feb 2026, COD Jun 2026; Unit 4 outage
Jun 2026, completion Oct 2026, COD Dec 2026. Note: the PJM log's
"~1,052 MW" figure for this conversion is wrong — EIA nameplate is
2×670.9 MW.
Sources: Indiana Capital Chronicle,
https://indianacapitalchronicle.com/2024/11/06/aes-indiana-wins-approval-for-natural-gas-conversion/;
AES, https://www.aesindiana.com/pike-county.
Confidence: High on conversion; Medium on Unit 4 month (Oct completion
vs Dec COD).

### I. RETIME — J.H. Campbell Units 1, 2, 3, MI, Central, Coal, 1,560.8 MW, Nov 2026 → Feb 2027
265.2 + 378.8 + 916.8 MW. The plant did NOT retire in Nov 2026. DOE
issued Order No. 202-26-51 on Nov 13, 2026, keeping Campbell available
Nov 15, 2026–Feb 12, 2027 (7th consecutive ~90-day FPA §202(c) order;
original planned retirement May 31, 2025). Feb 2027 is the current
order's expiry, not a new retirement date — further renewal is likely,
and the D.C. Circuit vacated the first order on Sep 11, 2026. Per the
standing rule this is an evidence-based retime to the order expiry,
flagged, not a speculative push. Coordinator confirmed the order
independently via DOE's own Nov 14, 2026 press release.
Sources: DOE Order No. 202-26-39 text (prior order in the chain),
https://www.energy.gov/documents/doe-order-no-202-26-39; DOE press
release,
https://www.energy.gov/articles/energy-secretary-keeps-critical-coal-fired-generation-operational-ahead-winter-midwest;
Headwaters Wire,
https://headwaterswire.com/2026/11/14/energy-department-orders-michigan-coal-plant-available-meet-emergency/.
Confidence: Medium-High on Feb 2027 as the current-order end; Low on
ultimate retirement date.

### J. RETIME — Traceview Advanced Power Station, MS, South, Natural Gas, 819.4 MW, Aug 2028 → Dec 2029
477.7 + 341.7 MW. Entergy Mississippi's third CCCT (754 MW nominal) —
air permit issued by MDEQ Oct 14, 2026; Entergy project page:
construction 2026, in-service 2029; POWER Magazine (Oct 2025): Delta
Blues 2028, Traceview 2029, Vicksburg to follow. Dec 2029 is a stack
placeholder (month not published).
Sources: Jackson Wire,
https://www.thejacksonwire.com/article/mdeq-issued-traceview-air-permit-oct-14-ridgeland-gas-plant;
POWER,
https://www.powermag.com/entergy-mississippi-adding-third-gas-fired-power-plant-to-superpower-strategy/.
Confidence: Medium-High.

### K. RETIME — Gerald Andrus Unit 1, MS, South, Natural Gas, 781.4 MW, Jun 2035 → May 2028
Entergy states Gerald Andrus (781 MW, in service 1975) "will be retired
when the new [Delta Blues] plant comes online in 2028"; Delta Blues is
May 2028 in EIA. The 2035 date was the old schedule. This pulls 781.4 MW
of retirement seven years earlier.
Sources: Entergy,
https://www.entergy.com/news/entergy-mississippi-breaks-ground-on-delta-blues-advanced-power-station;
World Energy, https://www.world-energy.org/article/45642.html.
Confidence: Medium-High.

### L. RETIME — Steel River Solar Phase 3 (+ battery), AR, South, Solar 500 MW + Battery 250 MW, Jul 2030 → Dec 2029
Other phases unchanged (P1 Aug 2028, P2 Jul 2029). Cypress Creek/Google
broke ground Jul 14, 2026 on phases 1–2 ($3.5bn financing closed Jun
2026; Google PPA); company states the full three-phase project
(2.45 GWdc solar, 2.9 GWh storage) completes by 2029. EIA's Jul 2030
for phase 3 is a year late vs the developer. Dec 2029 placeholder.
Sources: Reuters,
https://www.reuters.com/legal/litigation/cypress-creek-secures-35-billion-one-largest-us-solar-storage-projects-2026-06-11/;
NACleanEnergy,
https://www.nacleanenergy.com/solar/cypress-creek-and-google-break-ground-on-america-s-largest-solar-project.
Confidence: Medium.

## Checked and confirmed KEEP (no change)
- **Vista Sands Solar, WI, Central, Solar 1,182 MW, Dec 2028, L** — WI PSC
  approved Jan 2025 (1,315.6 MWac gross, 1,182 MWac at POI, +300 MW BESS
  not in v1 as a separate row — see below); construction spring 2026,
  full ops end-2028. EIA MW/date match the POI figure.
  Source: https://apps.psc.wi.gov/ERF/ERFview/viewdoc.aspx?docid=529800
- **Lincoln Land Energy Center, IL, Central, Gas 2×638.4 MW, Jun 2030, P**
  — pre-construction, Pawnee; IEPA permit (2022, extended) expires Jan 1,
  2027; developer reverted EmberClear←Kindle; PPA reported with Eagle
  Rock's Meridian data center (1,000–1,100 MW, Christian Co.) — a grid
  PPA to a separate site, not on-site BTM, so no exclusion. Keep with
  risk flag.
  Source: https://www.illinoistimes.com/news/data-center-development-linked-to-power-plant-construction/
- **Arkansas Cypress Solar, AR, South, Solar 600 MW + Battery 350 MW,
  Jan 2029, P** — Entergy Arkansas, APSC Docket 25-054-U, 600 MWac +
  350 MW BESS at White Bluff substation; construction started Jul 11,
  2026; Google $526m contribution toward the West Memphis data-center
  load; grid-connected (serves all customers per Entergy). EIA date is
  the full-600 MW date (deliveries ramp Feb 2027→Oct 2029).
  Source: https://apps.apsc.arkansas.gov/olsv2/viewdoc/pdfview.asp?document=25-054-U_98_1.pdf
- **Hecate Sunfish (SSLR), MI, Central, Solar 499 MW, Dec 2028, L** —
  Hecate's 1 GW Calhoun Co. project in two ~500 MW phases; phase 1
  (Sunfish Solar 2, 360 MW, Dec 2026, U) is under construction with
  Bechtel/Consumers build-transfer. KEEP.
- **MEC North/South, MI, Central, Gas 500 MW each, Jun 2034, T/L** —
  "MEC" = **Marshall Energy Center** (Marshall, Calhoun Co.), owner
  Development Partners Group LLC, Siemens H-class CC. Pre-construction
  since 2017; city site-plan approval expired; no updates since Jun 2024;
  no firm timeline. **Not** Consumers Energy's new plants (different
  owner/sites). Keep — no termination evidence — with a low-confidence /
  paper-project flag.
- **Entergy CCCT fleet — KEEP EIA nameplate MW and dates** (company
  "754 MW" is the ISO/nominal rating; EIA nameplate runs ~780–820 MW per
  unit and is the consistent basis): Delta Blues 818.7 MW May 2028
  (ground broken, 754 MW nominal); Vicksburg 819.4 MW Aug 2028 (Entergy
  social Dec 2025 confirms Aug 2028); Jefferson 820 MW Nov 2029 (754 MW
  nominal, $1.6bn, APSC Docket 25-047-U pending); Waterford 5 820 MW
  Jun 2029 (T; LDEQ air permits Oct 2, 2026); Waterford 6 820 MW Jun 2030
  (P; LPSC certification filed Feb 2026, approval pending); Westlake
  819.4 MW Oct 2030 (P; same filing); Franklin Farms 1&2 1,560.6 MW
  Dec 2028 (L; ground broken, Meta-funded interconnection,
  grid-connected); Richland Parish 1&2 1,560.6 MW Mar 2030, Richland 3/4
  780.3 MW each Oct 2030, Pointe Coupee 1–3 780.3 MW each Oct–Dec 2031
  (all P — these 7 units ARE the 5,278 MW Meta expansion, U-37882,
  hearing Oct 7–9 2026, LPSC vote due Dec 16, 2026; keep, with
  approval-risk flag); Ironwood 467.3 MW Jul 2028 (446 MW simple-cycle
  CT, ground broken Aug 20, 2026); Lone Star 467.3 MW Jul 2028 (453 MW
  CT, PUCT-approved, ground broken Apr 2026); Orange County 1,306 MW
  Oct 2026 (TS; brought online Oct 15, 2026 per Entergy Texas).
- **Retirements KEEP:** Sherburne County Unit 1 Dec 2026 (765.3 MW) +
  Unit 3 Dec 2030 (938.7 MW) — Xcel plan confirmed; Monroe Units 3/4
  Dec 2028 (1,639.8 MW) + Units 1/2 Dec 2032 (1,639.8 MW) — reaffirmed
  in DTE's Sep 2026 IRP; Baldwin Units 1/2 Dec 2027 (1,259.6 MW) +
  Newton Unit 1 Dec 2027 (617.4 MW) — Vistra WARN May 2026 + ELG filings
  (Newton has some date ambiguity: Sep 2027 per CCR filing vs Dec 2028
  coal cessation — EIA Dec 2027 sits inside the range); Allen S. King
  Dec 31, 2028 (598.4 MW) — Xcel Dec 30, 2025 compliance filing; Sabine
  Units 1/3/4 Oct 2026 (1,304.4 MW gas) — EIA Feb 2026 article, replaced
  by Orange County; Lake Catherine Unit 4 Dec 2027 (552.5 MW) — confirmed
  by Ironwood release; Michigan City Unit 12 May 2028 (540 MW) — 2028
  remains the plan per IURC staff-report comments, extension debated;
  Nine Mile Point Units 5/6 (895.1 MW each, Jun 2031 / Jun 2033) — no
  contrary evidence found.
- **No BTM exclusion found among the large EIA plants.** The Meta/Entergy
  and Google/Cypress plants are utility grid plants serving data-center
  load through the grid, not on-site co-located generation; Lincoln
  Land's data-center PPA is likewise off-site. The only data-center-
  adjacent gas found that is genuinely BTM-style is outside MISO scope
  or unquantified (see below).
- **In-file cross-checks:** Franklin Farms 1&2 (plant 68214, Dec 2028)
  and Richland Parish 1&2 (plant 69449, Mar 2030) are distinct plants at
  different coordinates (~7 km apart), not a double-count.

## Could not verify / flagged, no adjustment proposed
- **R.M. Schahfer Units 17/18, IN, Coal 847 MW, Dec 2026 (v1)** — planned
  retirement was Dec 31, 2025; DOE orders kept them running (Order
  202-25-12 to Mar 23, 2026; Order 202-26-19 to Jun 21, 2026); NIPSCO's
  Apr 2026 filing says it anticipates further DOE orders. KEEP Dec 2026
  (no evidence-based alternative date) with a high-risk-of-further-delay
  flag.
  Source: https://ecm.idem.in.gov/cs/idcplg?IdcService=GET_FILE&dID=84008768&dDocName=84016912&Rendition=web&allowInterrupt=1&noSaveAs=1
- **Sioux Units 1/2 (MO, 1,099.4 MW, Dec 2028), Columbia Units 1/2 (WI,
  1,112 MW, Dec 2029), Little Gypsy Units 2/3 (LA, 1,002.9 MW, Jun 2029),
  Waterford 1&2 Unit 2 (LA, 445.5 MW, Jun 2028), South Oak Creek Units
  7/8 (WI, 641.6 MW, Dec 2027)** — not individually verified; no
  contrary evidence surfaced.
- **Nine Mile Point** — web search was polluted by the NY nuclear plant
  of the same name; the LA gas units' 2031/2033 dates rest on EIA only.
- **Vista Sands 300 MW BESS** — in the PSC approval but no corresponding
  battery row was found in the v1 plants file (only the 1,182 MW solar
  row); not proposed as an addition because the BESS MW/date split was
  not verified against EIA.
- **Constellation–Google nuclear uprates (~890 MW, announced Oct 2026)**
  — per-unit split unpublished; several Constellation IL units are MISO
  (Quad Cities, Clinton) but the MISO share cannot be determined. Not
  added (same treatment as PJM v2).

## Candidates NOT proposed (insufficient evidence for MW/date)
- **R.S. Nelson Unit 6, LA, Coal ~615 MW, retirement 2028?** — Sierra
  Club (Mar 2024) says the LPSC approved Entergy's plan to retire Big
  Cajun II Unit 3 (2025) and Nelson Unit 6 (2028); no Nelson retirement
  row exists in v1. Needs verification of exact MW/date before adding.
- **White Bluff coal, AR** — Entergy agreed (2021 settlement) to stop
  burning coal at White Bluff in 2028; its replacement (Jefferson, §2)
  is in v1, but whether White Bluff retires vs converts to gas peaking
  (per Entergy's own testimony) is unresolved. No White Bluff rows in v1.
  Needs verification.
- **Schahfer-site CCGT + data center, IN** — NIPSCO's Apr 2026 NPDES
  addendum mentions a data center (Q2 2027) and a CCGT at/near Schahfer
  (simple-cycle 2029, one CC block 2030, both blocks late 2030/2031); an
  advocacy slide claims a 2,300 MW gas plant for Amazon. MW unverified —
  do not add.

## Coordinator corrections to the v2 research report
1. **Belle River double-count (material).** The researcher's totals
   treated Belle River's coal retirement (−1,395 MW) as a NEW retirement.
   It is a RETIME: v1 already contained it (Dec 2028 → Dec 2026). The
   cumulative coal-retirement delta is therefore Cayuga 1,062 +
   Petersburg 1,341.8 = **2,403.8 MW**, not 3,798.8 MW. Correct net 2036
   effect is **+6,340.0 MW** (Gas +8,566.8; Coal −2,403.8; Nuclear
   +177.0), not +4,945.0 MW. Correct 2028 flow delta is **+548.2 MW**
   (Legend +754, Traceview −819.4, Andrus −781.4, Belle River coal out
   of 2028 +1,395), not −846.8 MW. The build asserts the corrected
   yearly flow deltas; the corrected figures are in summary_v2.json.
2. **Legend MISO attribution (confirmed).** Coordinator verified
   independently: PUCT Docket 56693 filing states MISO determines
   Legend's transmission network upgrades; Entergy's release states its
   customers are connected to the MISO grid; Industrial Info confirms
   Entergy Texas operates on MISO, separate from ERCOT. Confidence
   raised to High.
3. **Campbell DOE order (confirmed).** Coordinator verified
   independently via DOE's own Nov 14, 2026 press release: Order No.
   202-26-51, in effect Nov 15, 2026–Feb 12, 2027. The D.C. Circuit
   vacatur (Sep 11, 2026) of the first order is noted in the adjustment.

## Status-only notes (no MW/date change)
- **Delta Blues** (MS, L in EIA): broke ground Nov 2025 — status should
  be U. **Franklin Farms 1&2** (LA, L): broke ground Dec 1, 2025 —
  status should be U. **Vista Sands** (WI, L): construction was to begin
  spring 2026 per developer — status possibly U now, not verified as of
  Nov 14. Status changes do not affect the stack and were not applied.
