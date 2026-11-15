# CAISO capacity stack — v2 research log

Built 2026-11-15. v2 = v1 (EIA-860M only) + 3 named manual adjustments
(4 row-level changes: 2 retimes, 2 new rows), each with an online
source. All sources accessed 2026-11-15. Basis throughout is nameplate MW.

## The adjustments

### A. ADD — Diablo Canyon Unit 1 retirement, CA, Nuclear, −1,159.0 MW, Oct 2029
### B. ADD — Diablo Canyon Unit 2 retirement, CA, Nuclear, −1,164.0 MW, Oct 2030
EIA-860M Sep 2026 shows **no Planned Retirement Year at all** for Diablo
Canyon Units 1/2 (plant 6099, San Luis Obispo Co., PG&E, 1,159.0 +
1,164.0 MW nameplate) — v1 therefore carries California's only nuclear
plant at full capacity through 2036. That is wrong under current state
law. The units were originally NRC-licensed to Nov 2, 2024 (Unit 1) and
Aug 26, 2025 (Unit 2) and were to retire under the 2016 joint proposal.
SB 846 (Dodd, Ch. 239, Statutes of 2022) reversed that, and CPUC
Decision 23-12-036 (Dec 2023) conditionally authorised extended
operations **until October 31, 2029 for Unit 1 and October 31, 2030 for
Unit 2** — a five-year extension only. The CEC's *Diablo Canyon Power
Plant SB 846 Operations Assessment — 2026 Update* (CEC-700-2026-031,
Jul 2026) confirms those dates remain the state-law end of operations.
Complication, flagged not acted on: on Apr 2, 2026 the NRC issued
renewed **federal** licences running to Nov 2044 / Aug 2045, but the CEC
assessment is explicit that the federal renewal "does not alter the
authority of SB 846" — operation past Oct 2029/Oct 2030 requires new
state legislation. A "Diablo Canyon 2045 Coalition" launched Apr 23,
2026 is campaigning for exactly that; no extension bill had been
introduced as of the sources checked. v2 books the retirements at the
current-law dates; the 2044/2045 outcome is a flagged candidate (below).
Sources: CEC SB 846 Operations Assessment 2026 Update,
https://efiling.energy.ca.gov/GetDocument.aspx?tn=271510&DocumentContentId=109055
Confidence: High on the dates as current law; the residual risk is
legislative, not evidentiary.

### C. RETIME — Ormond Beach Units 1 & 2, CA, Natural Gas, 1,612.0 MW, Jan 2027 → Dec 2026
2×806.0 MW (GenOn, Oxnard, Ventura Co.). EIA carries a Jan 2027 planned
retirement. The controlling date is the State Water Board's
Once-Through Cooling Policy **final compliance date of December 31,
2026**: the Board's Aug 15, 2023 amendment extended Alamitos, Huntington
Beach and Ormond Beach to Dec 31, 2026, contingent on participation in
DWR's Electricity Supply Strategic Reliability Reserve Program
(ESSRRP), which all three entered on Jan 1, 2024. The SACCWIS Final
2026 Report (Mar 20, 2026) recommends no further change to the
compliance schedules. In Oct 2026 DWR's deputy director told the CEC
the SRR contracts "will sunset at the end of the year," and Nov 2026
market reporting states plainly that Alamitos, Huntington Beach and
Ormond Beach (~2.9 GW) "retire on Dec. 31, 2026." EIA's Jan 2027 is one
month late; the retime aligns the stack with the compliance date.
Note on MW basis: state documents cite the OTC fleet at ~2,859 MW
(Alamitos Units 3/4/5 1,141.2; Huntington Beach Unit 2 226.8; Ormond
Beach ~1,491) — those are net/dependable figures. EIA nameplate for the
same units is 2,945.0 MW (1,115.0 + 218.0 + 1,612.0). The stack stays on
nameplate throughout; the ~86 MW gap is definitional.
Sources: State Water Board SACCWIS Final 2026 Report,
https://www.waterboards.ca.gov/water_issues/programs/ocean/cwa316/saccwis/docs/2026/26saccwisrptf.pdf;
Enverus, "CAISO and Mid-C 2026 Winter Outlook" (Nov 5, 2026),
https://www.enverus.com/blog/caiso-and-mid-c-winter-outlook-storms-set-the-price/
Confidence: Medium-High. (A state or federal emergency order past
Dec 2026 remains possible — AES's Nov 4, 2026 AQMD filing for Alamitos
says exactly that — but no such order exists as of Nov 15, 2026, and
per the standing rule retirements move only on evidence, not on the
possibility of an order.)

## Checked and confirmed KEEP (no change)
- **AES Alamitos Units 3/4/5 (310.0 + 310.0 + 495.0 MW, Dec 2026) and
  AES Huntington Beach Unit 2 (218.0 MW, Dec 2026)** — EIA dates already
  equal the OTC final compliance date of Dec 31, 2026 and the ESSRRP
  contract expiry. KEEP. The replacement CCGTs on both sites (Alamitos
  Energy Center 678.0 MW, in service 2020; Huntington Beach Energy
  Project 699.2 MW, in service 2020) are already in the anchor.
- **Scattergood (LADWP)** — an OTC plant repeatedly discussed alongside
  the CAISO fleet, but it sits in the **LDWP balancing authority**, not
  CISO. It is outside this stack's footprint by definition (see
  README.md excluded-BA table) and no adjustment is possible or needed.
- **El Segundo** — the OTC steam units retired in 2015 (already in
  EIA's Retired sheet history). What operates today as El Segundo
  Energy Center LLC (537.4 MW, 2013) is a dry-cooled CCGT, not an OTC
  unit, with no planned retirement. KEEP.
- **Redondo Beach Units 5/6/8** — retired Dec 31, 2023 after their own
  OTC extension; already history in the Retired sheet, correctly absent
  from the anchor. KEEP.
- **Darden Clean Energy Project, CA, Solar 1,370.8 MW + Battery
  1,214.8 MW, Mar 2028, T (EIA)** — verified as the largest
  solar+battery hybrid in the pipeline: Intersect Power / IP Darden I,
  western Fresno Co.; CEC approved Jun 12, 2025 under the AB 205 Opt-In
  Certification program as 1,150 MWac solar + up to 1,150 MW / 4,600 MWh
  battery; $4.95bn financing closed 2026 and construction is under way
  with commercial operation targeted for 2028. EIA's higher solar MW
  (4×342.7) is a DC/nameplate figure vs the CEC's 1,150 MWac — the
  stack's nameplate basis is retained, and the Mar 2028 date is
  consistent with the developer's 2028 target. KEEP (status T in EIA is
  stale — construction has begun — but status does not affect the stack).
  Source: CEC, https://www.energy.ca.gov/news/2025-06/cec-approves-worlds-largest-solar-battery-storage-project-fresno-county-under
- **Bellefield 2 Solar & Energy Storage, CA, 500.0 MW solar + 500.0 MW
  battery, Dec 2026, V** and **Grace Energy Center, CA, 500.0 + 500.0 MW,
  2027, L** — the next-largest hybrids after Darden. No contrary
  evidence on MW or dates found; Bellefield's V status (>50% complete)
  supports its Dec 2026 date. KEEP.
- **SunZia Wind, NM, 3,650.2 MW, in service May 2026 (EIA Operating)** —
  the plant is real and in service; CAISO's 2026 Summer Assessment
  confirms it counts SunZia among CAISO additions. KEEP at full EIA MW
  — but see the attribution flag below.
- **No new gas additions to add.** The EIA Planned sheet for CISO
  contains 0.9 MW of gas in total. Web checks surfaced no large gas
  plant in the CAISO footprint that EIA omits: California procurement
  since 2021 is storage/solar/wind/geothermal, and the state's
  long-duration procurement (up to ~6 GW for 2029–2032 delivery) is
  zero-emitting by order. The forward gas story in CAISO is retirements
  (OTC fleet) and the existing fleet, not additions.
- **No BTM exclusion found.** Scan for data-center co-located
  generation in the CAISO footprint found no plant whose grid
  connection is entirely accounted for by co-located load. California
  data-center load growth is real (CEC forecasts +1.8 GW in the CAISO
  BAA by 2030) but is being served as grid load; co-location /
  behind-the-meter generation for large loads is still a *tariff
  design* question in CAISO's stakeholder process (prompted by FERC's
  Jun 18, 2026 show-cause order on large loads), not an operating
  fleet. Nothing to exclude under the standing behind-the-meter rule.

## Could not verify / flagged, no adjustment proposed
- **Chokecherry and Sierra Madre Wind, WY, 3,550.5 MW (EIA: Dec 2031 /
  Dec 2031 / Dec 2032 / Dec 2033, status U)** — Global Energy Monitor's
  phase table suggests materially earlier dates (Phase 1A 844.2 MW in
  2029; 2A 1,303.2 MW in 2030; 2B 553.5 MW in 2031), and the associated
  TransWest Express HVDC line is now expected to energise in late 2029
  (developer) — the wind cannot deliver to CAISO before the line.
  Sources conflict (some CAISO-side commentary still cites ~2027 for
  the line) and the GEM phase mapping to EIA's four generator IDs is
  incomplete. EIA dates kept; the whole 3,550.5 MW is flagged as
  timing-risk — plausibly ~2 years early, which would move it from
  2031–2033 into 2029–2031 without changing the 2036 total.
  Source: https://www.gem.wiki/Chokecherry_And_Sierra_Madre_Wind_Energy_Project
- **SunZia Wind attribution, 483.2 MW** — EIA codes the full 3,650.2 MW
  to BA=CISO. CAISO's 2026 Summer Assessment counts "CAISO's share
  (3,167 MW) of SunZia Wind project (3,650.2 MW total nameplate)" —
  implying 483.2 MW is contracted/attributed elsewhere. Kept at the
  EIA BA figure for consistency with the stack's definitional rule
  (BA filter), flagged here as the largest single attribution risk in
  the forward changelog.
  Source: CAISO 2026 Summer Loads and Resources Assessment.
- **Whale Rock Pumped Storage, CA, 600.0 MW, Dec 2027, status P** —
  in EIA's Planned sheet with regulatory approvals *not initiated*.
  A 600 MW pumped-storage project cannot plausibly reach service in
  Dec 2027 from that status. Kept (no verified alternative date or
  cancellation), flagged as a paper project inside the v1/v2 pipeline.

## Candidates NOT proposed (insufficient evidence for MW/date)
- **Diablo Canyon operation to 2044/2045, 2,323.0 MW** — physically
  licensed by the NRC (Apr 2026) but not authorised under state law.
  Requires new legislation; a campaign coalition exists, no bill
  enacted. If enacted, the v2 retirements in 2029/2030 would reverse.
  Not added as a scenario — v2 follows current law.
- **Eagle Mountain Pumped Storage, CA, 1,300 MW** — the large project
  EIA omits entirely (not in the Planned sheet). FERC-licensed
  (P-13123, Eagle Crest Energy, Riverside Co., former Kaiser iron
  mine), but: CAISO interconnection queue entries withdrawn, the mine
  land was sold in Apr 2023 to Ecology Mountain Holdings, and FERC has
  stayed the construction deadlines (commence by Jun 19, 2028; complete
  by Jun 19, 2031) with no financing, no offtake and no construction
  start. No credible in-window COD exists. NOT added; recorded here so
  the omission is a decision, not an oversight.
  Source: https://www.gem.wiki/Eagle_Mountain_Pumped_hydroelectric_plant

## Status-only notes (no MW/date change)
- **Darden (T in EIA)** — construction began in 2026 per the developer
  and CEC site reporting; status should be U. **Alamitos/Huntington/
  Ormond OTC units** have operated as emergency-only ESSRRP resources
  since Jan 1, 2024 — they are in the anchor at nameplate like
  everything else in this stack; on an NQC basis CAISO already excludes
  them, which is part of the anchor cross-check gap documented in
  README.md.
