# NYISO capacity stack — v2 research log

Built 2026-11-15. v2 = v1 (EIA-860M only) + 3 named manual adjustments
(36 row-level changes, all added retirements), each with an online
source. All sources accessed 2026-11-15. Basis throughout is nameplate MW.

Context: EIA-860M carries almost no NYISO forward retirements — v1
retirements 2026–2036 total just 41.6 MW (22 units, largest Coxsackie
GT1, 21.3 MW gas, Apr 2027), because the state's actual deactivation
pipeline runs through NYISO's generator-deactivation / Short-Term
Assessment of Reliability (STAR) process and the DEC Peaker Rule, not
through EIA planned-retirement fields. The 2026 Gold Book's Table IV-5
deactivation pipeline alone is 1,307 MW of summer capability (vs 48 MW
in the 2025 Gold Book). The three adjustments below are that pipeline's
large, dated items. No blanket retirement-delay override is applied.

## The adjustments

### A. ADD retirement — Danskammer Units 1–4, NY, Natural Gas, −532.0 MW, Jan 2027
Unit 1 72.0 MW, Unit 2 73.5 MW, Unit 3 147.1 MW, Unit 4 239.4 MW
(EIA nameplate; plant ID 2480, Orange County; combined summer
capability 497.3 MW — NYISO process documents cite ~502–572 MW on
capability bases; the stack uses EIA nameplate consistently).
Danskammer (Titanium/Hull Street) noticed deactivation of Units 1–4
effective Aug 1, 2026. The 2026 Q1 STAR (Apr 15, 2026) found the
deactivation would exacerbate a Lower Hudson Valley deficiency, so
Danskammer could not deactivate before Aug 1, 2026 and was required to
remain in service — as an Interim Service Provider from Aug 1, 2026 —
until at least Jan 15, 2027 (the end of its 365-day notice period).
The Q2 STAR (Jul 14/15, 2026) confirmed the retention. The Q3 2026
STAR (Oct 13, 2026) then found the Lower Hudson Valley near-term need
"no longer observed with CHPE having demonstrated its planned
capability," withdrew the Aug 20, 2026 solution solicitation, and
cleared Danskammer 1–4 to "proceed with the deactivation process."
Booked Jan 2027: the earliest date consistent with the Jan 15, 2027
retention floor and the Q3 clearance. The exact deactivation date has
not been published; a later 2027 date is possible, and NYISO's draft
2026 Reliability Needs Assessment still notes Lower Hudson Valley
concerns from 2032 and a possible future RMR — neither changes the
deactivation itself. Units 5–6 (2×2.7 MW oil standby) are not in the
deactivation notice and are not retired here. EIA carries no planned
retirement for any Danskammer unit.
Sources: NYISO, *Short-Term Reliability Process Report: 2026–2030
Generator Deactivation Reliability Needs* (Apr 15, 2026),
https://www.nyiso.com/documents/20142/15930753/2025-Q3-Short-Term-Reliability-Process-Report-Final.pdf;
NYISO 2026 Q2 STAR summary, https://www.luminary-energy.com/articles/nyiso-q2-2026-star/;
NYISO 2026 Q4 STAR study assumptions (Nov 2, 2026, reporting the Q3
findings), https://www.nyiso.com/documents/20142/59547943/03_2026 Q4 STAR Study Assumptions_vFinal.pdf/4aa011a6-9226-6a1d-95c3-6147c5d28e16.
Confidence: High on the retirement happening; Medium on Jan 2027 as
the month (it is a floor, not a published date).

### B. ADD retirement — Gowanus Barges 2 & 3, NY, Natural Gas, −320.0 MW, May 2029
16 simple-cycle turbines, 20.0 MW each: GT21–GT28 (Barge 2) and
GT31–GT38 (Barge 3), plant ID 2494, Kings County (AlphaGen / Astoria
Generating Company). These are DEC Peaker Rule units (6 NYCRR Subpart
227-3, NOx limits for simple-cycle turbines, compliance dates 2023 and
2025). NYISO's 2023 Q2 STAR identified a New York City reliability
need driven by the Peaker Rule; NYISO designated Gowanus 2&3 and
Narrows 1&2 as needed, initially to May 1, 2027, with a possible
further two-year extension. On Apr 15, 2026 the Short-Term Reliability
Process Report extended the designation to **May 1, 2029 — the maximum
extension the Peaker Rule allows** — and on Apr 16, 2026 AlphaGen
withdrew the deactivation notices so the units operate in the market
until then. May 2029 is therefore booked as the retirement date: it is
the regulatory end of the maximum extension, after which the units
cannot comply with Subpart 227-3 as written. Residual risks: a DEC
rule change, or approval of AlphaGen's repowering (see flagged
candidates) altering the site's end state. EIA carries no planned
retirement for these units (one of the 16, GT36, is already flagged
out-of-service in EIA but remains in the anchor under the all-statuses
method).
Sources: NYISO Short-Term Reliability Process Report (Apr 15, 2026),
as above; NYISO Short Term Reliability page,
https://www.nyiso.com/documents/20142/57787467/04_STRP%202026-04%20MC.pdf.
Confidence: Medium-High.

### C. ADD retirement — Narrows Barges 1 & 2, NY, Natural Gas, −352.0 MW, May 2029
16 simple-cycle turbines, 22.0 MW each: NT11–NT18 (Barge 1) and
NT21–NT28 (Barge 2), plant ID 2499, Kings County. Same determination,
same dates, and same reasoning as B. B + C together are the "608 MW"
in NYISO documents — that figure is the four barges' combined summer
capability (608.7 MW by EIA net summer: Gowanus 2 152.8 + Gowanus 3
146.8 + Narrows 1 158.0 + Narrows 2 151.1); their nameplate total,
the basis of this stack, is 672.0 MW. Two of the 16 Narrows turbines
(NT21, NT27) are already flagged out-of-service in EIA but remain in
the anchor under the all-statuses method.
Sources: as B.
Confidence: Medium-High.

## Checked and confirmed KEEP (no change)

- **Empire Wind 1, Wind 810.0 MW, Sep 2027, status V (EIA).** Equinor,
  54 turbines, delivering into Brooklyn (Zone J). Hit by TWO federal
  stop-work actions: the Apr 2025 Interior order (lifted May 2025,
  ~$200m cost) and the Dec 22, 2025 BOEM lease suspension of five
  projects; a federal judge granted Empire a preliminary injunction on
  Jan 15, 2026 and construction resumed. As of Equinor's Q3 2026
  results (Oct 29–30, 2026) the project is ~80% complete — all 54
  foundations, the offshore substation and cable work done — but
  Jones-Act support-vessel delays pushed turbine installation to early
  2027 and first power to H1 2027. The NYISO queue COD remains
  Sep 1, 2027, matching EIA's Sep 2027. KEEP.
  Sources: https://gcaptain.com/u-s-shipbuilding-delays-push-empire-winds-first-power-into-2027/;
  https://www.catf.us/2026/11/weathering-storm-tracking-federal-actions-against-offshore-wind/;
  https://blog.gridstatus.io/nyiso-empire-wind-update/
- **Sunrise Wind, Wind 924.0 MW, Oct 2027, status U (EIA).** Ørsted,
  ~30 miles east of Montauk, landing on Long Island. Also suspended
  Dec 22, 2025; preliminary injunction Feb 2, 2026 (*Sunrise Wind LLC
  v. Burgum*); construction resumed, onshore works >90% complete,
  turbine installation under way in fall 2026, first power possible
  Q4 2026 with full COD Oct 1, 2027 per the NYISO queue — matching
  EIA. KEEP.
  Sources: https://eelp.law.harvard.edu/?p=5898;
  https://blog.gridstatus.io/nyiso-empire-wind-update/
- **South Fork Wind, Wind 130.0 MW (EIA nameplate), operating since
  2024 — in the anchor.** 12×11 MW turbines, Ørsted/Skyborn, first
  power Dec 2023, fully operational Mar–Jul 2024, delivering to East
  Hampton (Long Island). Public sources cite 132 MW (12×11 MW); EIA
  records 130.0 MW nameplate. The 2 MW is a rating-convention
  difference, not a discrepancy to correct on a nameplate basis. No
  adjustment.
  Source: https://en.wikipedia.org/wiki/South_Fork_Wind_Farm
- **Nuclear — all four upstate units KEEP, no uprate, no retirement.**
  Nine Mile Point 1 (641.8 MW, licence to Aug 2029) and 2 (1,259.3 MW,
  licence to 2046), FitzPatrick (883.3 MW, licence to Oct 2034), Ginna
  (614.0 MW, licence to Sep 2029), all Constellation. There is no
  early-retirement evidence: Constellation filed subsequent licence
  renewal for Nine Mile Point 1 on Mar 25, 2026 and for Ginna on
  Jun 17, 2026, seeking operation to 2049 for both — the opposite of
  retirement risk inside the window. No uprate with a published MW or
  date was found for any New York unit. Two flags, neither booked:
  (i) the state Zero-Emission Credit programme expires Mar 2029, close
  to the Ginna/Nine Mile 1 licence dates — a revenue risk, not a
  retirement notice; (ii) FitzPatrick's licence expires Oct 2034,
  inside the stack window, and its subsequent-renewal application is
  not due until Oct 2029 and has not been filed — no retirement is
  booked, but the unit is carried in `summary_v2.json` as a flagged
  candidate (883.3 MW).
  Sources: https://www.constellationenergy.com/news/2026/08/constellation-reports-second-quarter-2026-results.html;
  https://energyplan.ny.gov/-/media/Project/EnergyPlan/files/Draft-2025-Energy-Plan/Topic-Area-Chapters/Draft-New-York-State-Energy-Plan-02-Nuclear.pdf
- **Mineral Basin Solar Power, Solar 401.6 MW, Dec 2028, status P,
  Clearfield County, PA — KEEP in NYISO.** A Pennsylvania plant in the
  NYISO stack looks like a BA-code error; it is not. Mineral Basin
  (Swift Current Energy, on reclaimed coal-mine land) holds a NYSERDA
  Renewable Energy Standard contract to deliver energy and RECs to the
  New York Control Area, is NYISO Queue Position 1080 (Zone C), and
  interconnects to NYSEG's 345 kV Line 47; NYISO/NYSEG/Min
...[truncated 8187 chars]