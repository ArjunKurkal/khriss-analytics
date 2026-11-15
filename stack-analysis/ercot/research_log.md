# ERCOT capacity stack — v2 research log

Built 2026-11-15. v2 = v1 (EIA-860M only) + 6 named manual adjustments
(167 row-level changes: 162 exclusion rows, 5 new rows), each with an
online source. All sources accessed 2026-11-15. Basis throughout is
nameplate MW.

## The adjustments

### A. EXCLUDE — Legend Power Station, TX, Natural Gas, −754 MW, Jul 2028
754 MW CCCT, Port Arthur, Jefferson Co. EIA Planned sheet has it (plant
68053, 754 MW, Jul 2028, status L) coded BA=ERCO, which is why v1
included it. The ERCO code is an error: Entergy Texas operates entirely
on the MISO grid, and the PUCT filing (Docket 56693) states "the final
cost of the transmission network upgrades required for Legend will be
determined by the Midcontinent Independent System Operator (MISO)";
PUCT approved the plant Sep 11, 2025 ($1.6bn); it broke ground Apr
2026 for mid-2028 service. Sister Entergy Texas plants in the same file
(Orange County, Lone Star) are coded BA=MISO. This is the mirror image
of MISO v2 adjustment C, which added Legend to MISO.
Sources: Entergy,
https://www.entergy.com/news/entergy-texas-receives-puct-approval-for-two-power-plants-to-support-southeast-texas-growth;
PUCT Docket 56693 (as documented in the MISO v2 research log).
Confidence: High (plant and MISO attribution both confirmed).

### B. EXCLUDE (BTM) — Project Matador Gas Plant (PMG), TX, Natural Gas, −11,679.3 MW
157 EIA units (plant 69799, entity Fermi America), Carson Co.:
1,287.3 MW in 2027 (23 units), 1,560.0 MW in 2028 (6 units), 8,832.0 MW
in Dec 2030 (128 units), all status P. Fermi America's "Project
Matador" HyperGrid campus near Amarillo is, in the company's own SEC
filing, a "first-of-its-kind behind-the-meter campus" and "the world's
largest private grid," built to power co-located AI data centres on a
privately operated grid "rather than the state's main ERCOT network."
The site sits in the Texas Panhandle — Southwest Power Pool territory
served by Xcel (Southwestern Public Service), not ERCOT — and the
DEPLOY registry records grid operator SPP and "No interconnection
queue position: the campus is built behind the meter, generating its
own power on site." Two independent grounds for exclusion: (1) the
standing BTM rule — co-located generation whose grid connection is
entirely accounted for by the load counts as 0 MW of grid addition;
(2) the EIA BA code (ERCO) is wrong for the location. Company claims
beyond EIA (a 6 GW TCEQ air permit; 11 GW planned, up to 17 GW) are
unquantified and likewise BTM — flagged below, not added anywhere.
Sources: Fermi America Q3 2025 shareholder letter (SEC filing),
https://www.sec.gov/Archives/edgar/data/2071778/000121390025108289/ea026472101ex99-1_fermi.htm;
DEPLOY registry, https://registry.deploy.report/datacenters/fermi-amarillo-texas.
Confidence: High on exclusion; the EIA unit list itself is a paper
filing (all status P) for a campus whose energized capacity was 0 GW
as of Aug 2026 per the registry.

### C. EXCLUDE (BTM) — Project Matador Nuclear, TX, Nuclear, −4,468 MW
4 units × 1,117.0 MW (plant 69798, entity Fermi Nuclear), Carson Co.:
2,234 MW Dec 2031 + 2,234 MW Dec 2032, status P. Four Westinghouse
AP1000 reactors planned for the same HyperGrid campus as B (Hyundai
E&C completed the FEED study Jul 2026; NRC applications under review).
Same BTM + BA grounds as B. Additional flag: Nov 2026 reporting says
Fermi's nuclear chief departed and the reactor timeline slipped; the
firm near-term commitment at the campus is a 600 MW hyperscaler deal
from 2027 anchored on gas and Xcel grid supply, not the reactors.
Sources: Fermi SEC filing (see B); Construction Review Online,
https://constructionreviewonline.com/fermi-america-unveils-plan-for-largest-u-s-energy-and-data-complex/.
Confidence: High on exclusion.

### D. Fuel switch — J K Spruce Unit 2, TX, Coal → Natural Gas, 922.5 MW, Dec 2028
Coal retirement and gas addition of 922.5 MW each booked Dec 2028 (net
0). CPS Energy's board-approved plan (Jan 2023) ends coal at Spruce in
2028: Unit 1 (566 MW) retires — already in v1 as a Dec 2028 planned
retirement — and Unit 2 converts to gas. EIA carries no planned
retirement for Unit 2 and no gas addition, so v1 would have left
922.5 MW of coal on the stack indefinitely. CPS's FY2025 financial
statements confirm the Spruce 2 conversion and note the Sommers and
Braunig units are also to retire before the 2030–2032 EPA compliance
deadlines. GEM lists Unit 2 at 878 MW coal / ~922.6 MW as gas; the
stack uses the EIA nameplate 922.5 MW on both sides for consistency.
Sources: CPS Energy FY2025 audited financial statements,
https://www.cpsenergy.com/content/dam/corporate/en/Documents/Finance/FY2025-CPS-Energy-YE-Audited-Financials-FINAL-042925-ada.pdf;
Global Energy Monitor, https://www.gem.wiki/Spruce_Unit_2.
Confidence: Medium-High (conversion is board-approved and in audited
financials; exact month is a Dec 2028 placeholder for "by 2028").

### E. Repower — Coleto Creek, TX, Coal 622.4 MW out / Natural Gas 630 MW in, Dec 2026
Coal retirement 622.4 MW (EIA nameplate, Unit 1, Goliad Co.) and gas
addition 630.0 MW, both Dec 2026 (net +7.6 MW). Vistra announced in
Dec 2020 that Coleto Creek would retire by 2027; it then chose to
repower the site to gas. Vistra's Sep 29, 2025 release: the plant "was
scheduled for retirement in 2027… the company will repower… This will
restore approximately 630 MW of generation to the grid." Vistra's
Power Texas Forward page (Nov 2026) lists the conversion as **under
construction**, "completion expected by the end of 2026"; the Q2 2026
10-Q (per secondary summaries) puts the coal retirement by end-2026.
Williams' Wharton West pipeline expansion entered service Nov 2026
specifically to supply gas for the conversion. EIA carries neither the
coal retirement nor the gas addition. GEM lists the gas configuration
at 600 MW — the 600–630 MW range is noted; 630 MW (Vistra's own
current figure) is booked.
Sources: Vistra,
http://investor.vistracorp.com/2025-09-29-Vistra-Announces-Plans-to-Build-New-Gas-Fueled-Dispatchable-Power-Units-in-the-Permian-Basin;
Power Texas Forward, https://powertexasforward.com/;
Shale Magazine (Williams Wharton West),
https://shalemag.com/texas-gas-pipeline-expansions/.
Confidence: Medium-High on the coal retirement by end-2026; Medium on
the gas MW (600 vs 630) and on gas COD also landing in Dec 2026.

### F. ADD — Rayburn Energy Station II, TX, Natural Gas, +570 MW, Dec 2028
570 MW gas plant for Rayburn Country Electric Cooperative (Grayson
Co., Sherman area), financed by a finalized Texas Energy Fund
In-ERCOT loan of $411m announced Jun 4, 2026, operations 2028. The
PUCT TxEF page (updated Nov 14, 2026) lists it among the nine
finalized In-ERCOT loan agreements totalling 5,446 MW. Verified
absent from the EIA Planned sheet (no Rayburn addition; the existing
Rayburn Energy Station, 803.2 MW, is in Operating). Of the nine TxEF
loans, this was the only large one with no EIA counterpart: Kerrville
Rock Island 122 MW is in EIA (6×20.3 MW, Sep 2027, L); NRG TH Wharton
456 MW and Calpine/Constellation Pin Oak Creek 460 MW entered service
in 2026 (Pin Oak Creek GT5/GT6, 222 MW each, are in the Operating
sheet's 2026 in-service set); NRG Cedar Bayou 5 (721 MW) and CPV Basin
Ranch (1,350 MW nominal) are in EIA Planned; NRG Greens Bayou 6
(455 MW nominal) is in EIA at 447 MW. Dec 2028 month is a placeholder;
the year is PUCT's.
Source: PUCT Texas Energy Fund,
https://www.puc.texas.gov/industry/electric/business/texas-energy-fund/.
Confidence: Medium (finalized state loan; no EIA filing yet; exact
unit configuration unpublished).

## Checked and confirmed KEEP (no change)
- **Kiamichi Energy Facility, OK, Gas 1,370.0 MW (anchor)** — the only
  ERCO plant outside Texas. Checked as a suspected BA error; it is
  not one: EIA-derived directories list BA = ERCO, transmission owner
  Oncor Electric Delivery (TX), NERC region TRE. The plant sits in
  Oklahoma but interconnects south into ERCOT. KEEP.
  Source: https://www.gridinfo.com/plant/kiamichi-energy-facility/55501
- **CPV Basin Ranch Energy Center, TX, Gas 2×722.5 MW, Feb 2029, U** —
  construction began Nov 2025 after a $1.1bn TxEF loan; COD 2029.
  Company figure 1,350 MW is the nominal rating; EIA nameplate
  1,445 MW is the consistent stack basis (same treatment as the
  Entergy fleet in MISO v2). KEEP.
  Source: https://www.powermag.com/new-gas-fired-plants-bring-needed-generation-flexibility-to-the-power-sector/
- **Cedar Bayou 5, TX, Gas 721.0 MW, Aug 2028, U** — NRG 8-K (Oct 1,
  2025) confirms the ~721 MW CC, TxEF financing, and a Dec 1, 2028
  commercial-operation deadline; NRG targets mid-2028. KEEP.
  Source: https://gov.texas.gov/news/post/governor-abbott-announces-texas-energy-fund-loan-to-721-mw-natural-gas-facility-in-southeast-texas
- **Greens Bayou 6, TX, Gas 447.0 MW, May 2028, U** — NRG's TxEF
  portfolio lists 455 MW nameplate / mid-2028 COD, "on track." The
  8 MW difference is definitional. KEEP at EIA figures.
- **Sandow Lakes Energy Station, TX, Gas 2×645 MW, Oct/Dec 2028, P** —
  1,200 MW net CC (EIA 1,290 MW nameplate), Macquarie $450m equipment
  financing closed Oct 2025. Checked explicitly for BTM: the plant
  holds an ERCOT interconnection study position at 1,291.6 MW as a
  grid resource, so generation and any neighbouring load are
  independently grid-connected — count in full under the BTM rule.
  Reporting of data centres "next door" (SoftBank land purchase,
  unconfirmed buildings) does not make the plant itself BTM. KEEP
  with a paper-project flag (status P, no construction start found).
  Source: https://admin.inframation.io/proposals?source_id=us.iso.ercot.gen_queue&lifecycle_state=announced%2Cfiled%2Cstudied%2Cpermitted%2Ccontracted%2Cunder_construction%2Cwithdrawn%2Ccancelled%2Cbuilt%2Cunknown%2Cpostponed
- **O W Sommers Units 1/2, TX, Gas 446 MW each, Mar 2027 / Mar 2029
  retirements (v1)** — CPS's 2021 Flexible Path showed 2026/2028 and
  its FY2025 financials commit to retirement before the 2030–2032 EPA
  deadlines; the EIA dates sit inside the announced range. KEEP.
- **Coal fleet otherwise KEEP:** no announced retirement/conversion
  evidence found for W A Parish (2,736.8 MW coal), Martin Lake
  (2,379.6), Limestone (1,849.8), Oak Grove (1,795.4), Fayette
  (1,690.0), Sandy Creek (1,008.0) or San Miguel (410.0) within
  2026–2036. Vistra's announced ~4,578 MW of coal retirements are
  Coleto Creek (ERCOT, adjusted above) and Miami Fort (PJM).
- **IP Roman / IP Meitner wind + solar (Deaf Smith/Roberts/Gray Cos.,
  ~2,170 MW, 2028, L)** — Panhandle-county projects coded ERCO.
  Checked: unlike Matador they are ordinary grid projects in the
  ERCOT interconnection process (the Panhandle hosts both SPP and
  ERCOT-served pockets; no BTM or private-grid evidence). KEEP, with
  a note that county alone does not settle BA for Panhandle projects.

## Could not verify / flagged, no adjustment proposed
- **Vast Sands Power, TX, Gas 2×440 MW, May 2027, U (in v1/v2)** —
  Ward Co., entity Permian Power I LLC. Vistra's FID'd Permian Basin
  expansion is 860 MW at its Permian Basin Power Plant with a Jun
  2026 TxEF loan and 2028 operations; MW (880 vs 860), county and
  timing are close but the project-LLC identity could not be
  confirmed as Vistra's. KEEP at EIA MW/date with the flag.
- **TH Wharton additions (NRG, 456 MW, TxEF)** — NRG reports the unit
  fully operational May 2026; no TH Wharton unit appears in the EIA
  Operating sheet's 2026 in-service set under that name in the checks
  run (Pin Oak Creek's 2026 units were found). If it is genuinely
  missing from EIA it is a ≤456 MW understatement of 2026 additions;
  unresolved in this pass, flagged rather than added on a name match
  that could not be made.
- **Fermi Matador gas units dated 2027 (1,287.3 MW)** — excluded with
  the rest of the campus; note Fermi's own 2026 target was ~1.1 GW of
  first power, so the campus will likely file real capacity in SPP/BTM
  form in later vintages. It remains 0 MW of ERCOT grid capacity
  either way.

## Candidates NOT proposed (insufficient evidence for MW/date)
- **WattBridge / Continental Resources West Texas gas, 452 MW** —
  TxEF loan announced Oct 7, 2026, after the EIA vintage closed;
  plant name and in-service date not yet published. 452.0 MW flagged.
- **Anthropic / Caterpillar BTM generators, 1,700 MW** — Nov 2026
  reporting of a $3.4bn equipment takeover for behind-the-meter
  on-site microgrids; no single plant, site or date. BTM in any case —
  would be excluded under the rule even if filed. 1,700.0 MW flagged.
- **Crusoe / Stargate Abilene on-site gas, ~360 MW** — ten simple-cycle
  turbines, partially energized since Sep 2025, "permitted for
  onsite/data-center use only; behind-the-meter while ERCOT
  interconnection is built." Not in EIA; BTM, so correctly absent
  from the stack. 360.0 MW flagged.
  Source: https://registry.deploy.report/datacenters/stargate-abilene
- **Liberty Thermal Energy Center + Bullock Gas, Hill Co., 1,400 MW
  each** — data-centre-linked CC projects visible only in the ERCOT
  queue (studied, online Jul 2032). Queue-only; no EIA filing, no
  financing evidence. 2,800.0 MW flagged.
- **Schahfer-style paper solar/battery bulk of the pipeline** — 59 GW
  of the EIA Planned sheet is not under construction; no attempt was
  made to verify individual sub-300 MW solar/wind/battery projects.

## Status-only notes (no MW/date change)
- **CPV Basin Ranch** (U in EIA): construction formally began Nov 20,
  2025 — consistent with U. **Pin Oak Creek** TxEF units reached full
  commercial operations spring 2026 per Modo Energy — consistent with
  their presence in the Operating sheet.
