# SERC capacity stack — v2 research log

Built 2026-11-15. v2 = v1 (EIA-860M only) + 25 named manual adjustments
(81 row-level changes: 23 retimes, 58 new rows), each with an online
source. All sources accessed 2026-11-15. Basis throughout is nameplate
MW. Cumulative v2−v1 effect at 2036: **+34,700.3 MW** (additions
+36,348.8; retirements +1,648.5; net by fuel: Gas +15,015.8, Solar
+10,355.0, Battery +10,577.0, Nuclear +251.0, Coal −1,498.5). The build
asserts the yearly flow deltas; 2026 was spot-checked by hand
(+2,197.3 = FPL battery tranche 1,419.5 + Cumberland CC block retimed
in 777.8), as was 2027 (+4,420.4, eight named items).

## The adjustments

### A. ADD — Georgia Power certified CCs, GA, SERC-Central, Gas, +3,692 MW
Bowen Units 7-8 1,482 MW Nov 2029; Wansley Units 10-11 1,453 MW
Nov 2029; McIntosh Unit 12 757 MW Nov 2030. Company-owned proposals
from the 2029–2031 All-Source RFP, certified by the Georgia PSC on
Dec 19, 2025 (Dockets 56298/56310; part of the 9,885 MW stipulated
portfolio, ~$16.5bn, ~80% to serve data-center load). None of the
three is in the EIA Planned sheet (verified in-file: no Bowen,
Wansley or McIntosh rows in the v1 plants file). Grid-connected
utility plants — counted in full under the BTM rule.
Sources: Georgia PSC, Newsome testimony Nov 12, 2025
(https://services.psc.ga.gov/api/v1/External/Public/Get/Document/DownloadFile/224506/105769);
Legal 500 summary of the Dec 19, 2025 order.
Confidence: High.

### B. ADD — Georgia Power certified BESS, GA, SERC-Central, Battery, +3,023 MW
Ten tranches with CODs from the same certification: Wadley 260
(Nov 2027, supplemental); South Hall 250, Bowen Phase I 250, Wansley
500, Yates Phase I 320, Yates Phase II 250 (all Nov 2028); Bowen
Phase II 250, Thomson 500 (Nov 2029); Hammond Phase II 193, McIntosh
250 (Nov 2030). None appears in EIA. The remaining certified
portfolio — 2,821 MW of PPAs and 350 MW of solar+BESS COPs — was NOT
added (see candidates).
Source: Georgia PSC testimony Table 1 (see A). Confidence: High.

### C. ADD — Person County Energy Complex (Roxboro CC1/CC2), NC, CPLE, Gas, +2,720 MW
CC1 1,360 MW Dec 2029; CC2 1,360 MW Mar 2030 (targeting Q4 2029/Q1
2030). Duke Energy's replacement build at the Roxboro site; CC1/CC2
certificates approved by the SC PSC Jul 23, 2026 (Order 2026-414);
GEM lists both blocks under construction. Absent from EIA entirely —
the v1 plants file has zero Roxboro rows of any kind.
Sources: Duke 2026 Carolinas Resource Plan, Appendix I
(https://dms.psc.sc.gov/Attachments/Matter/310ce3e8-b895-4bab-aed7-98f59d1f98e6);
Global Energy Monitor, Roxboro Steam Plant.
Confidence: Medium-High (CC1), Medium (CC2).

### D. ADD — Roxboro coal Units 1 & 4 retirements, NC, CPLE, Coal, −1,156.0 MW, Dec 2029
Unit 1 410.8 + Unit 4 745.2 (EIA nameplate), retiring as CC1 enters
service. The 2026 CRP states Duke will *continue to operate Units 2
& 3* after CC2 is built to meet load growth — so no retirement is
booked for them (a change from the 2023 plan, which retired all
four). EIA shows no planned retirement for any Roxboro unit.
Sources: Duke 2026 CRP App. I; GEM Roxboro. Confidence: Medium.

### E. ADD — Marshall Advanced CTs, NC, DUK, Gas, +850 MW, Dec 2028
2 × 425 MW advanced-class CTs at Marshall Steam Station. NCUC CPCN
granted Dec 2, 2024 (Docket E-7, Sub 1297); GEM lists them under
construction for 2028. They enable the Marshall coal Units 1 & 2
retirement already in v1 (Dec 2028). Not in EIA.
Sources: Duke 2026 CRP App. I; GEM Marshall. Confidence: High.

### F. RETIME — Marshall Units 3 & 4, NC, DUK, Dec 2033 → Dec 2034, 1,422 MW
EIA rows: gen 4 coal-coded 711.0 + gen 3 gas-coded 711.0 (EIA splits
the dual-fuel pair by fuel; the pair total is the plant's real MW).
Duke's 2025 Carolinas Resource Plan (filed Oct 2025) delayed Units
3 & 4 to 2034, citing load growth.
Sources: GEM Marshall (summarising the 2025 CRP); Duke 2025 annual
report via GEM. Confidence: Medium-High.

### G. ADD — Canadys Joint Resource, SC, SCEG, Gas, +2,180 MW, Jun 2033
Three 1×1 advanced-class CC blocks at the former Canadys coal site,
Colleton County; DESC / Santee Cooper 50/50 (~$5bn). The SC PSC
granted the CECPCN on Jun 12, 2026 (Order 2026-350) and rejected
reconsideration on Jul 16, 2026; target commercial operation
mid-2033. Booked under SCEG (DESC lineage/site ownership); the
subregion is SERC-Central under either owner. Not in EIA.
Sources: SC PSC Docket 2025-323-E application/hearing notice
(https://dms.psc.sc.gov/Attachments/Matter/6750f890-edec-4728-bde9-233a019937e4);
Synapse/Metz testimony Feb 17, 2026; Order 2026-350 reporting.
Confidence: High.

### H. ADD — Wateree coal retirements, SC, SCEG, Coal, −771.8 MW, Dec 2032
2 × 385.9 MW (EIA nameplate). DESC's 2026 IRP reference plan retires
Wateree Dec 31, 2032 and Williams Dec 31, 2034 (the without-GHG-rules
case; with the rules in force the model wanted both by 2032 and DESC
delayed a year for lack of purchasable capacity). Retirement is
explicitly contingent on replacement capacity (Canadys) being
available; DESC's Dec 29, 2025 ELG notice backstops permanent coal
cessation at Wateree by Dec 31, 2034. EIA has no retirement rows.
Sources: DESC 2026 IRP via EVA study Oct 2026
(https://dms.psc.sc.gov/Attachments/Matter/b0c1ad38-be0c-45a3-9ff9-7db304b41869);
DESC ELG cessation notice. Confidence: Medium.

### I. ADD — Williams coal retirement, SC, SCEG, Coal, −659.7 MW, Dec 2034
Single unit, EIA nameplate 659.7 MW (entity: South Carolina
Generating Co). Same IRP basis as Wateree. Flag: the Oct 2026 EVA
evaluation of DESC's own IRP finds optimized timing keeps Williams
to 2046 in the reference case — the 2034 date is DESC's planning
assumption, adopted here as the utility's stated plan, not an
economic finding. Confidence: Medium.

### J. RETIME — Winyah coal, SC, SC (Santee Cooper), Dec 2030 → Dec 2034, 1,275.8 MW
4 units (330.8 + 315.0 × 3). Santee Cooper's 2025 IRP Update delayed
Winyah's retirement; the SC PSC's order in Docket 2025-18-E records
the delay (the order text reads "delaying the retirement of Winyah
by 2035"), and Santee Cooper's Aug 2026 stakeholder process confirms
an *assumed 2034 retirement date*, ELG-compliant through that date,
with a 2035 date also discussed as avoiding ZLD investment. Dec 2034
booked; the 2034-vs-2035 ambiguity is ±1 year on 1,275.8 MW.
Sources: SC PSC Order, Docket 2025-18-E
(https://dms.psc.sc.gov/Attachments/Matter/77375f6a-4b4d-4c52-869e-d8fc67f9bf02);
Santee Cooper IRP SWG #12 summary (Aug 11, 2026).
Confidence: Medium.

### K. RETIME — Victor J. Daniel Jr coal, MS, SOCO, Dec 2027 → Jan 2035, 1,096.6 MW
2 × 548.3 MW. Southern Company's 2025 IRP cycle extended Daniel —
like Bowen and Scherer — from a 2028 retirement to the mid-2030s,
with gas co-firing by 2030 in the co-fire pathway; data-center load
growth is the stated driver. Jan 2035 is a mid-2030s placeholder.
Sources: Data Center Dynamics; DeSmog analysis of EIA date changes;
DESC 2026 IRP study (Georgia passage). Confidence: Medium.

### L. RETIME OUT — Cumberland coal, TN, TVA, 2,600 MW → Jan 2037 (out of window)
2 × 1,300 MW. In Feb 2026 the TVA Board *reversed* the Cumberland
retirement decision: both coal units will operate past 2028
alongside the new CC, with >$700m of life-extension investment
(CAA notice letter, Jun 25, 2026, quoting the reversal). EIA's
Dec 2028 / Dec 2034 dates are the reversed plan. Booked at Jan 2037
as a "no current retirement date" placeholder, which removes both
units from the 2026–2036 changelog; if TVA sets a date inside the
window, this is the single largest downside correction available
(−2,600 MW).
Sources: Knox News Feb 10, 2026
(https://www.knoxnews.com/story/news/environment/2026/02/10/tennessee-valley-authority-may-keep-coal-at-kingston-cumberland-plant-alongside-battery-natural-gas/88603489007/);
Center for Biological Diversity CAA notice (Jun 2026).
Confidence: Medium (decision is firm; the placeholder year is ours).

### M. RETIME OUT — Kingston coal, TN, TVA, 1,700 MW → Jan 2037 (out of window)
9 units (4 × 175 + 5 × 200; EIA splits them 1,100 MW at 2027 and
600 MW at 2034). TVA's Feb 2026 Supplemental EIS for Kingston
assesses a new proposed alternative: continue operating all nine
coal units *along with* the previously analysed CC + aero CTs and a
100 MW BESS. This is a proposal under study, not a completed
reversal like Cumberland — the original Apr 2024 ROD (retire by end
of 2027) has not been formally replaced. Booked out of window on
the strength of TVA's own stated new proposed alternative; flagged
as the softest of the TVA calls.
Source: TVA Kingston Reservation Operations / SEIS page
(https://www.tva.com/environment/environmental-stewardship/environmental-reviews/nepa-detail/kingston-fossil-plant-retirement).
Confidence: Medium.

### N. RETIME — Cumberland gas CC blocks, TN, TVA, 1,555.6 MW earlier
EIA dates the two 777.8 MW blocks Jan 2029 and Dec 2034. TVA's plan
from its Jan 10, 2023 decision is a 1,450 MW (summer) CC *in
operation by 2026* to replace the first coal unit; Industrial Info
(Nov 2025) reports the Cumberland gas units operational in 2026
with construction under way. Blocks retimed to Dec 2026 and
Dec 2027 (second block's year is a placeholder inside the
construction window).
Sources: TVA release Jan 10, 2023
(https://www.tva.com/news-media/releases/tva-retiring-cumberland-continues-transition-to-clean-energy-future);
Industrial Info. Confidence: Medium.

### O. ADD — Kingston BESS, TN, TVA, Battery, +100 MW, Dec 2027
Part of the approved Kingston replacement package (FEIS Feb 2024 /
ROD Apr 2024) and retained in the Feb 2026 SEIS alternative. The CC
and aero CTs are in v1 from EIA; the BESS is not.
Source: TVA Kingston page (see M). Confidence: Medium.

### P. FUEL SWITCH — E.C. Gaston Unit 5, AL, SOCO, Coal → Gas, 952.0 MW, Dec 2028
Alabama Power confirms, in its Oct 12, 2026 ELG annual progress
report, that work "has commenced and remains ongoing to transition
Gaston Unit 5 to operate solely on natural gas by December 31,
2028" (permanent cessation of coal combustion). EIA nameplate
952.0 MW; EIA carries no conversion/retirement for the unit.
(Units 1–4 already report as gas in EIA; their 2025 ELG transfer to
the generally-applicable pathway has no stack effect.)
Sources: Alabama Power NOPP Annual Progress Report 2026
(https://www.alabamapower.com/content/dam/alabama-power/pdfs-docs/company/compliance---regulation/elg/plant-gaston-nopp-annual-progress-report-2026.pdf);
GEM Gaston. Confidence: High.

### Q. FUEL SWITCH — Plant Barry Unit 5, AL, SOCO, Coal → Gas, 788.8 MW, Dec 2028
Alabama Power's 2025 IRP: "Barry Unit 5 will cease coal combustion
by no later than December 31, 2028" (Unit 4 already converted).
Booked as a conversion on the Gaston pattern (same utility, same
ELG mechanism, same date). Alternative reading — outright
retirement — would make the v2 gas addition 788.8 MW too high and
is flagged here explicitly.
Source: Alabama Power 2025 IRP summary report
(https://external.alabamapower.com/content/dam/alabama-power/pdfs-docs/company/compliance---regulation/2025-irp.pdf).
Confidence: Medium.

### R. ADD — E.W. Brown Unit 12 CC, KY, LGEE, Gas, +645 MW, Dec 2030
645 MW NGCC at the E.W. Brown station; CPCN approved by the
Kentucky PSC in Oct 2025 (Case 2025-00045), in service by 2030.
Not in EIA (the only Brown row in v1 is a 125 MW BESS).
Sources: KY PSC Case 2025-00045 filings; GEM E.W. Brown.
Confidence: High.

### S. ADD — LG&E/KU 2024 IRP coal retirements, KY, LGEE, Coal, −1,470.2 MW, Dec 2035
Mill Creek 3 (462.6) + Mill Creek 4 (543.6) + E.W. Brown 3 (464.0),
all EIA nameplate, all slated for 2035 in LG&E/KU's 2024 IRP. EIA
shows no planned retirement for *any* LG&E/KU coal unit. (Brown 3's
history: the PSC denied its 2027 retirement in Nov 2023; 2035 is
the current plan, paired with Brown 12 above.)
Sources: LG&E/KU 2024 IRP via GEM Mill Creek / E.W. Brown pages.
Confidence: Medium.

### T. ADD — Duke nuclear uprates, NC/SC, DUK/CPLE, Nuclear, +251 MW
The 2026 Carolinas Resource Plan (App. J) plans ~251 MW of uprates
at three stations: Brunswick MUR +26 MW by 2029; McGuire + Catawba
extended uprates +225 MW combined by 2031. Booked as Brunswick 26
(Dec 2029), McGuire 150 + Catawba 75 (Dec 2031) — the 150/75 split
follows POWER Magazine's reporting that the affected units
(McGuire 1 & 2, Catawba 1) gain ~75 MW each; the split is assumed,
the 251 MW total and the 2029/2031 timing are Duke's. SLR status
(no capacity effect): Oconee renewed to 80 years Mar 2025, Robinson
Apr 2026, Brunswick application due late 2026. New nuclear (Lee
1,117 MW LLWR or Belews Creek SMRs) first appears in 2037 in the
IRP — outside the window, flagged only.
Sources: Duke 2026 CRP App. J
(https://dms.psc.sc.gov/Attachments/Matter/d094a68c-4570-4efa-8938-200d468747ef);
POWER Magazine May 13, 2026; NC legislative briefing Feb 2026.
Confidence: Medium-High (total), Medium (split).

### U. ADD — FPL solar shortfall vs TYSP, FL, FPL, Solar, +10,355.0 MW
FPL's Ten Year Site Plan 2026–2035 (filed Apr 2026) plans 12,293 MW
of nameplate solar in 74.5 MW blocks: 894 (2026), 1,192 (2027),
1,788 (2028), 2,384 (2029), 2,980 (2030), 0 (2031–2033), 1,490
(2034), 1,564.5 (2035) — the annual figures tie exactly to the
published total. EIA's Planned sheet captures the pace only
through 2027 (894.0 in 2026 — exact — and 968.5 of 1,192 in 2027)
plus a single 75 MW unit in 2029, then stops. v2 adds the
difference by year: 223.5 / 1,788.0 / 2,309.0 / 2,980.0 / 1,490.0 /
1,564.5. The 2026–2029 programme is covered by FPL's approved
base-rate settlement; FPL states 2030–2035 additions "have an
increased likelihood for change" — hence the confidence step-down.
No TYSP exists beyond 2035, so 2036 gets no tranche (a known
understatement if the pace continues).
Source: FPL TYSP 2026–2035, Table ES-1
(https://floridapsc.com/pscfiles/website-files/PDF/Utilities/Electricgas/TenYearSitePlans/2026/Florida%20Power%20and%20Light%20Company.pdf).
Confidence: Medium-High (≤2029), Medium (2030–2035).

### V. ADD — FPL battery build, FL, FPL, Battery, +7,454.0 MW
TYSP battery additions by year: 1,419.5 / 819.5 / 596 / 596 / 596 /
1,192 / 596 / 596 / 223.5 / 819.5 (2026–2035), tying exactly to the
published 7,454 MW total. EIA's Planned sheet contains **zero** FPL
battery additions — the largest single-fuel gap in v1. The
2026–2029 block (3,431 MW) matches FPL's approved base-rate
settlement (TYSP Ch. III). Same source/confidence pattern as U.

### W. ADD — FPL unnamed CT tranches, FL, FPL, Gas, +3,276 MW (2032–2035)
TYSP fossil additions total 3,948 MW, of which 672 MW is the
Vandolah *acquisition* (excluded — ownership transfer of an existing
plant, not new build) and 3,276 MW is unnamed future CT blocks:
936 (2032), 936 (2033), 936 (2034), 468 (2035) — the "4×0 CT" /
"2×0 CT" placeholder rows of Table ES-1 (sites unidentified; the
reconstruction of ES-1's jumbled columns is verified by the fact
that solar, battery and fossil sub-totals each tie exactly to
their published totals). Included because the TYSP is FPL's filed
plan of record; this is the softest addition in v2.
Source: FPL TYSP Table ES-1 (see U). Confidence: Low-Medium.

### X. ADD — FPL CC uprates, FL, FPL, Gas, +62 MW (43 in 2027, 19 in 2028)
TYSP Table ES-1 "Changes to Existing Generation". Small but
published; booked for completeness. Confidence: Medium.

### Y. ADD — GCEC Units 4/5 retirement, FL, FPL, Gas, −150 MW, Dec 2029
TYSP Table ES-1 subtraction: Gulf Clean Energy Center Units 4
(75 MW) and 5 (75 MW) in 2029. Booked at TYSP MW under FPL;
EIA unit-level match not verified (legacy Gulf Power units).
Confidence: Medium.

## Checked and confirmed KEEP (no change)
- **Plant Bowen / Scherer coal (GA, SOCO)** — no EIA retirement rows
  in the window, and that is now correct: Georgia PSC's Jul 2025 IRP
  order approved keeping ~4,000 MW at Bowen + Scherer through 2038
  (Scherer Unit 3 had been slated for 2028; Bowen for 2035). The
  2038 exit sits outside the window. Co-firing with gas by 2030 does
  not change nameplate. KEEP.
- **Plant Vogtle (GA, SOCO)** — Units 3/4 in service Jul 31, 2023 /
  Apr 29, 2024 (~1,117 MW each); they are in the trailing/anchor,
  not the forward changelog. No further Vogtle expansion is planned.
  KEEP.
- **Kingston gas (TN, TVA) 1,830.6 MW, Dec 2027** — the CC block +
  16 aero CTs from the Apr 2024 ROD; construction ongoing; SEIS
  retains them. EIA MW/date match the ROD package (plus the BESS,
  added as adjustment O). KEEP.
- **Yates gas (GA, SOCO) 1,448.4 MW, 2027** — certified earlier
  (Docket 55378); Units 8–10 under construction in EIA with matching
  dates. KEEP. (The Yates *BESS* phases are adjustment B.)
- **Smarr CC (GA, SOCO) 804.0 MW, 2029** — Oglethorpe Power's Smarr
  CC in EIA with plausible status; no contrary evidence. KEEP.
- **Mill Creek 5 CC (KY, LGEE) 740.0 MW, Jun 2027** — under
  construction (status V); GEM confirms. KEEP.
- **Shawnee (KY, TVA) 1,400 MW coal, 2033; Gallatin (TN, TVA)
  1,255.2 MW coal, 2031** — TVA continues to evaluate retiring the
  balance of its coal fleet by 2035; no plant-specific reversal or
  acceleration found for either. KEEP with a policy-risk note.
- **Crystal River coal (FL, FPC) 1,478.4 MW, Jun 2034** — EIA date;
  no contrary evidence found in this pass. Not individually verified
  beyond the EIA record — noted honestly.
- **Mayo (NC, CPLE) 763.2 MW coal, Jun 2031** — consistent with
  Duke's plan sequence (Mayo + Cliffside 5 by ~2031). KEEP.
- **James H. Miller Jr (AL, SOCO) 2,822 MW coal** — Alabama Power's
  2025 IRP deploys ELG compliance at Miller with no retirement;
  EIA agrees (no planned retirement). KEEP.
- **Pepper Hammock Solar + Storage (GA, SOCO) 2,100 MW solar +
  400 MW battery, 2029, status L** — the largest single v1 addition;
  a Georgia Power RFP-era project at an early stage. No termination
  or confirmation evidence found; kept with a paper-project flag.

## Behind-the-meter scan (explicit)
One large explicitly-BTM gas build exists in the footprint:
**xAI/SpaceX at Southaven, MS** — 41 gas turbines, ~1,200 MW,
permitted by MDEQ in Mar 2026, described in SpaceX's own S-1 as a
"self-built behind-the-meter gigawatt-scale natural gas power
plant" for the Colossus campus (the data center sits across the
state line in Memphis, TN). At Colossus 1 in Memphis, ~198 MW of
permitted turbines remain alongside 150 MW of MLGW/TVA grid supply
(a second 150 MW substation is in progress). A larger fleet of
temporary/mobile turbines (~1.3 GW at peak) is to be removed by
Jul 2027 under an Aug 2026 settlement. None of this is in EIA.
**Treatment under the standing rule: 0 MW of grid addition — no v2
row.** (If a future vintage of EIA picks the Southaven plant up
under SOCO, it should be excluded in v2 on the same basis.)
Everything added in v2 is grid-connected utility capacity counted
in full: the Georgia certified fleet and FPL TYSP build serve
system load (including data-center load delivered through the
grid), and Person County / Marshall / Canadys are conventional
utility plants. Georgia Power's certified PPA portfolio (2,821 MW)
was not added partly for this reason's mirror image — its
counterparties are unspecified and may already sit in EIA as IPP
rows.

## Could not verify / flagged, no adjustment proposed
- **Cross Generating Station (SC, Santee Cooper) 2,451.5 MW coal** —
  no retirement date exists to book: Santee Cooper is running an
  optimal-retirement study in its 2026 comprehensive IRP (the 2023
  IRP's GHG-rule case had Cross ceasing by 2032; the base case did
  not). Largest single unverified retirement exposure in the region.
- **V.C. Summer Units 2 & 3 (SC, SCEG) ~2,234 MW nuclear** — Santee
  Cooper is exploring sale/completion of the abandoned units with
  private partners (also referenced in its IRP stakeholder process).
  No commitment, financing or schedule — not added.
- **Mill Creek Unit 2 (KY, LGEE) 355.5 MW coal** — two-sided:
  retirement was *approved* for 2027 (Case 2022-00402), but in the
  Oct 2025 CPCN case LG&E/KU sought, via stipulation, to extend
  MC2's life until Mill Creek 6 is in service, and filed rate-case
  testimony in Oct 2025 to recover the cost of running past 2027.
  EIA carries no date. No row booked either way.
- **Mill Creek Unit 6 NGCC (KY, LGEE)** — applied for in Case
  2025-00045 alongside Brown 12; Brown 12's Oct 2025 CPCN approval
  is documented, MC6's MW/date/approval were not verified in this
  pass. Not added.
- **Cliffside / James E. Rogers Energy Complex Units 5 & 6 (NC,
  DUK)** — EIA codes both dual-fuel units as *gas* (621.0 + 909.5
  MW), so they sit in the anchor as gas. Duke's 2023 plan pointed
  to Cliffside 5 retiring by 2031 and Unit 6 converting fully to
  gas in 2040 (outside window); the 2026 CRP's Appendix F dates
  were not extracted in this pass. If Unit 5 does retire in-window,
  v2 overstates 2036 by up to 621.0 MW (as gas, not coal).
- **Georgia certified solar+BESS COPs (Laurens County 200 MW,
  Plant Mitchell 150 MW, both Nov 2028)** — certified, but the
  solar/storage split is not published in the testimony table;
  not added rather than guessed.
- **TVA nuclear uprates / SMRs** — TVA's Clinch River SMR programme
  and any Browns Ferry/Watts Bar uprates have no in-window MW/date
  commitment verifiable in this pass. Not added.
- **Duke Energy Florida / TECO / other Florida utility builds**
  beyond FPL's TYSP — DEF's Shady Hills CC (612 MW, 2026) is in v1
  from EIA; no additional large Florida gas build was found that
  EIA misses. Seminole's and FMPA's plans were not separately
  verified — a stated gap, mitigated by their small anchor shares
  (2,825.6 + 4,577.4 MW).

## Candidates NOT proposed (insufficient evidence for MW/date)
Cross (above); V.C. Summer 2&3; Mill Creek 6; Cliffside 5
retirement; Georgia PPA portfolio (2,821 MW, double-count risk);
Duke new nuclear 2037 (outside window by Duke's own IRP);
xAI Southaven BTM (excluded by rule, not by evidence).
