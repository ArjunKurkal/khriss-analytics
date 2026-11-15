# PJM capacity stack v2 — research log

Built 2026-11-14. All web sources accessed 2026-11-14 unless a source date is
given. Four parallel research passes (gas builds, retirements, wind/solar,
behind-the-meter/co-located) plus the builder's own cross-checks against the
EIA-860M September 2026 file (`raw/eia860m_sep2026.xlsx`) and the full v1
plant list. Every v2 change is in `manual_adjustments.csv` (33 rows); this log
is the evidence trail, including what was checked and left unchanged and what
could not be verified.

**Method notes that apply to the whole log**

- MW basis is **nameplate**, consistent with the v1 EIA-860M changelog. Where a
  manual addition/retirement concerns a unit that exists in the EIA-860M
  Operating sheet, the EIA nameplate is used and the ICAP/net-summer figure is
  noted alongside. Company-announced figures are used for new builds (they are
  generally nameplate/gross). The one exception is Crane (TMI-1): Constellation's
  ~835 MW company figure is used instead of EIA nameplate 980.8 MW, because the
  stack anchor is ICAP-based and 835 MW sits close to the unit's net summer
  rating (802.8 MW).
- The "≥250 MW" threshold was applied per unit for EIA-listed plants, but
  sub-250 MW units were grouped where they retire/build as one block (the CEJA
  Illinois CT fleets, Forked River, West Lorain).
- Confidence: **High** = primary source (company/PUC/FERC/PJM filing) corroborated
  by a second source or by the EIA file. **Medium** = single primary source, or
  primary source with an unresolved detail (date split, MW basis, pending approval).
  **Low** = early-stage, single secondary source, or a planning assumption rather
  than a filing.

---

## 1. Behind-the-meter / co-located — the Homer City decision

### Homer City Energy Campus, Indiana Co., PA — BTM, grid MW 0, exclude 4,396 MW
- **v2 treatment:** all 14 EIA units (7×360 MW CT + 7×268 MW steam, 2028–29,
  status P) excluded. Confidence: **High** on the classification, **Medium** on
  the exact on-site share.
- Evidence: launch release (Business Wire, 2 Apr 2025) describes "the country's
  largest natural-gas-powered data-center campus"; Kiewit EPC on site since Oct
  2025; vertical construction ("first steel") Apr 2026; >2,000 tradespeople on
  site 20 Oct 2026; PA DEP air plan approval 32-00457A issued 18 Nov 2025 (under
  appeal, Environmental Hearing Board hearing 8–9 Dec 2026); first power Q2 2028,
  completion by 2029. PA DEP permit purpose is 4,678 MWe (seven combined-cycle
  turbines plus ten 25 MW Mitsubishi FT8 peakers — the peakers are not in EIA).
  EQT agreed in principle 15 Jul 2025 to supply up to 665,000 MMBtu/day; no signed
  definitive gas contract found.
- Classification reasoning: ~82% of output earmarked for on-site data centers;
  the plant is marketed as a data-center campus and power is delivered on site.
  Under the user's rule (a 2 GW data center + 2 GW gas plant + 500 MW grid
  connection counts as 0 MW, not 500 MW), a generator that primarily serves
  on-site load has grid MW 0.
- **Flagged alternative (NOT counted):** CEO Corey Hessen's March 2026 split
  (via Axios Pittsburgh, 31 Mar 2026, cited second-hand via Energy News Beat,
  11 Nov 2026) implies ~700–800 MW of deliberate grid export, not merely
  incidental backup; a secondary source (colocationscout.com) independently gives
  ~3,700 MW for data centers and 700–800 MW to the grid. The split "is not locked",
  no tenant is signed (AWS has no definitive agreement as of Aug 2026; county
  planning commission accepted AWS's preliminary land-development plan 14 Oct 2026
  for a 90-day review through 12 Jan 2027). If a surplus-export interpretation is
  adopted, the grid MW to count is **700–800 MW, not 4,396 MW**. No PJM queue /
  GIA / CIR figure for Homer City was found. The Axios article itself (31 Mar 2026)
  could not be fetched directly — cited second-hand.
- Sources: Business Wire 2 Apr 2025,
  https://www.businesswire.com/news/home/20250402452555/en/Homer-City-Redevelopment-and-Kiewit-Announce-Countrys-Largest-Natural-Gas-Powered-Data-Center-Campus-to-Support-AI-and-HPC-Demand ;
  Energy News Beat 11 Nov 2026,
  https://energynewsbeat.com/electrical-generation/kyuden-signs-on-to-run-homer-citys-4-4-gw-gas-plant-first-power-is-aimed-at-2028/ ;
  Business Wire 26 Mar 2026 (1,000 workers),
  https://www.businesswire.com/news/home/20260326477595/en/Homer-City-Redevelopment-Reaches-1000-Workers-on-Construction-Site ;
  Business Wire 12 Nov 2026 (Kyuden O&M; "support the facility's participation in
  PJM… wholesale electricity market"),
  https://www.businesswire.com/news/home/20261112823939/en/Kyuden-Energy-Partners-and-Homer-City-Generation-Ink-Long-Term-Operations-and-Maintenance-Agreement-for-4.4-GW-Homer-City-Energy-Campus

### Crane Clean Energy Center (TMI Unit 1), Dauphin Co., PA — grid-connected, ADD 835 MW, H2 2027
- Confidence: **Medium-High** on grid connection, **Medium** on date (regulatory risk).
- Constellation announced 20 Sep 2024 a 20-year PPA with Microsoft to restart Unit 1;
  target accelerated to 2027 (23 Sep 2025; "on track" for H2 2027 per Constellation via
  World Nuclear News, 28 Sep 2026). $1.6bn restart; DOE closed a $1bn loan 18 Nov 2025.
  NRC draft EA/FONSI 9 Jun 2026, final EA/FONSI Sep 2026; **NRC restart approval itself
  is still pending** (one exemption + three licence amendments, to licence expiry
  19 Apr 2034). FERC granted a waiver 1 Jun 2026 transferring 760 MW of Capacity
  Interconnection Rights from Constellation's Eddystone Units 3–4 to Crane; without it,
  PJM studies put full deliverability at Dec 2030.
- Grid-connected: Microsoft buys the plant's energy, capacity and carbon-free attributes
  under the PPA to match its PJM data-center consumption; there is no data center at the
  plant and no direct/private-wire connection — power is injected into the PJM grid.
- MW: Constellation ~835 MW (837 MW pre-retirement). EIA-860M Operating sheet (checked
  directly): Crane Clean Energy Center Gen 1, BA=PJM, NUC/ST, nameplate 980.8 MW, net
  summer 802.8 MW, status (OS). FERC order reportedly describes Crane as an 859 MW project.
  v2 uses 835 MW (company figure); EIA figures noted here.
- Sources: Constellation 20 Sep 2024 (launch),
  https://www.constellationenergy.com/news/2024/09/constellation-to-launch-crane-clean-energy-center-restoring-jobs-and-carbon-free-power-to-the-grid.html ;
  Constellation 23 Sep 2025; World Nuclear News 28 Sep 2026.

### Susquehanna / Cumulus (AWS), Luzerne Co., PA — no new MW, no change
- Talen sold its 960 MW Cumulus campus next to the ~2.5 GW Susquehanna nuclear plant to
  AWS for $650m (Mar 2024). FERC rejected the amended Interconnection Service Agreement
  1 Nov 2024 (189 FERC ¶ 61,078, ER24-2172), reaffirmed on rehearing Apr 2025. On 11 Jun
  2025 Talen and Amazon restructured to a **front-of-the-meter** arrangement: Susquehanna
  injects into PJM, Talen acts as AWS's licensed retail supplier, 1,920 MW at full contract
  quantity through 2042, ramping 840–1,200 MW by 2029. No new generation — Susquehanna
  already operates and is already in the stack. The 1,920 MW is a contract volume for
  existing output, not new capacity. Confidence: **High**.

### Shippingport Power Station (ex-Bruce Mansfield), Beaver Co., PA — NOT added, flagged
- Frontier Group announced 15 Jul 2025 a $3.2bn conversion of the retired 2,700 MW Bruce
  Mansfield coal plant into a 2,700 MW gas plant plus ~900 MW of new simple-cycle turbines
  (~3.6 GW total), supplying "substantial direct power" to the co-located data center and
  "over 1,000 MW of excess capacity back to PJM"; phasing in from 2027, all operational late
  2028 / early 2029. Jefferies' summary gives the split as 2.7 GW behind-the-meter and
  ~1 GW to the PJM grid. Data Center Frontier (Oct 2026) describes it differently —
  refurbishing three GE steam turbine-generator sets for ~2,550 MW (3×~850 MW). NFG's Q3 2026
  earnings call says it has >400,000 Dth/day contracted to the site "supporting both
  behind-the-meter power generation as well as power generation into the PJM Interconnection".
- v2 treatment: **not added**. Under the user rule the BTM-majority plant would be 0 MW
  anyway, and the total MW is uncertain (3.6 GW vs ~2.55 GW), no EIA-860M planned listing
  was found, and power-plant construction start is not verified (only data-center
  groundbreaking and borough conditional-use approvals Jan/Mar 2026). Same flagged
  alternative as Homer City: ~1,000+ MW surplus export if a surplus reading is adopted.
  Confidence: **Low**.

### Williams Socrates (Meta), New Albany, OH — BTM, not in v1, no change
- Socrates South + North: 400 MW (two 200 MW sites), target in-service Q3/Q4 2026. Ohio
  Power Siting Board authorised Socrates South 9 Jun 2025 (case 25-0185-EL-BLN): it "will
  operate 'behind-the-meter,' to serve the electric load of an adjacent data center and
  **will not be physically connected to the electric power grid**". No EIA listing found.
- Socrates the Younger: 250 MW + 116 MW battery, OPSB approved 26 Jun 2026 (case
  26-0169-EL-BLN); same behind-the-meter language. Note: DCD's Blackstone/Williams coverage
  (Jul 2026) says "will add 340 MW" vs the OPSB-approved 250 MW — 250 MW (the approval)
  is used here. Confidence: **High** (OPSB orders).

### Monarch Compute Campus, Mason Co., WV (AIP / Caterpillar) — BTM, not in v1, no change
- Gas gensets, 2 GW ordered (Caterpillar G3516), deliveries Sep 2026–Aug 2027, "power
  delivery begins in 2026 with 2 GW online in 2027", ultimate target 8 GW. Caterpillar/AIP
  press release Jan 2026: "Designed as a fully self-supplied, behind-the-meter power
  platform… does not require incremental utility transmission or distribution infrastructure
  to serve its load… target of 8 GW of planned generation capacity and an existing West
  Virginia microgrid designation" (WV HB 2014 islanded utility). No EIA listing found.
  Confidence: **High**.

### Other co-located items checked
- **Williams Neo** (682 MW, location/customer undisclosed): cannot confirm PJM — not added.
- **Apollo** (350 MW, Middleton Township, OH): reported only in a low-quality secondary
  source, not verified against OPSB — not added.
- **SB Energy complex, Pike Co., OH**: single-source claim (Marcellus Drilling News via
  Shale Markets) of turbines purchased 27 Aug 2026, "$33 billion, largest gas plant in US
  history". No MW, no COD, uncorroborated — not added.

---

## 2. Large gas builds — verification of the five v1 plants

### Sycamore Riverside Energy Center, Sullivan Co., IN — 964 → 918 MW, status corrected
- 4× GE 7F.05 simple-cycle, dual-fuel (gas/ULSD), developer Invenergy; I&M has a
  purchase-and-sale agreement to acquire it. I&M filed for CPCN 10 Apr 2026 (IURC Cause
  No. 46389), decision expected Dec 2026. Gas-pipeline necessity certificate approved
  26 Aug 2026 (IURC Cause No. 46407). Grid-connected peaker "in support of electric grid
  reliability", adjacent to the retired Breed station. COD 31 Mar 2029 kept. One secondary
  source says 930 MW; 918 MW is the developer/utility/IURC figure. Confidence: **High**.
- Sources: I&M release 10 Apr 2026,
  https://www.indianamichiganpower.com/company/news/view?releaseID=11849 ;
  IURC Order Cause 46407, 26 Aug 2026,
  https://secure.in.gov/iurc/files/ord_46407_082626.pdf ;
  AEP Q2 2026 10-Q.

### Wolf Summit Energy, Harrison Co., WV — v1 total 578.9 → 600 MW (+21.1), status corrected
- **Important correction to the first research pass:** the gas agent initially saw only
  the HCCT1 unit (371.5 MW) and reported +207–253 MW. The full v1 plant list carries
  **both** EIA units (HCCT1 371.5 + HCCA1 207.4 = 578.9 MW), so the true correction is
  only +21.1 MW (applied to HCCA1, 207.4 → 228.5 MW). The plant is a single 600 MW CCGT
  (GE Vernova 7HA.02, $1.2B). FID 13 Nov 2025, groundbreaking 22 Apr 2026, under
  construction; 100% of output contracted to Old Dominion Electric Cooperative (PPA
  22 Jul 2025), APS zone of PJM — grid-connected. COD: ODEC says power delivery "as early
  as late 2028" (v1 Dec 2028 kept); ENR/Blackstone said "by 2027" in Dec 2025 — treat as
  2027–late 2028, unconfirmed which. ENR/Harrison Co. PILOT figure is 625 MW (upper bound).
  "Glen Falls Facility" (625 MW) in queue lists is the same plant — do not double-count.
  Confidence: **High** on MW/status, **Medium** on COD.
- Sources: ODEC PPA release 22 Jul 2025,
  https://www.odec.com/wp-content/uploads/Wolf-Summit-Press-Release-Final-7-22-25.pdf ;
  ENR 2 Dec 2025,
  https://www.enr.com/articles/62093-private-infrastructure-investor-giant-blackstone-funds-12b-west-virginia-gas-power-plant ;
  WV Governor's office Apr 2026,
  https://governor.wv.gov/article/governor-morrisey-breaks-ground-historic-wolf-summit-energy-project-declaring-new-era-west ;
  GEM, https://www.gem.wiki/ESC_Harrison_County_power_station

### Trumbull Energy Center, Lordstown, OH — 977.4 → 950 MW, Apr 2026 → Jan 2026
- Entered commercial operation Jan 2026 (target COD 31 Jan 2026; grand-opening ceremony
  24 Jun 2026). ~950 MW CCGT (Hanwha; 940–953 MW across sources; EIA's own Feb 2026 article
  called it 900 MW), Siemens H-class, owners KOSPO/KIND/Siemens Energy, PJM ATSI zone —
  grid-connected. Same stack year (2026), so only the MW changes (-27.4 MW, applied to the
  STG unit 360 → 332.6 MW). Confidence: **High**.
- Sources: Hanwha 24 Jun 2026,
  https://www.hanwha.com/newsroom/news/press-releases/hanwha-power-enters-us-market-with-successful-commissioning-of-trumbull-energy-center-combined-cycle-gas-turbine-power-plant.do ;
  EIA Today in Energy 20 Feb 2026, https://www.eia.gov/todayinenergy/detail.php?id=67205

### Chesterfield Energy Reliability Center (CERC), Chesterfield Co., VA — 1,000 → 944 MW, status corrected
- 944 MW nominal (4× GE Vernova 7F simple-cycle, dual-fuel gas/oil, up to 10% H₂), COD
  1 Jun 2029, $1.47B. Peaking/reliability purpose — DEQ: operated "during periods of high
  demand, seasonal peaks, and extreme temperature events, as well as when intermittent
  generation… unavailable"; dispatchable by PJM; sited in the footprint of retired
  Chesterfield Unit 6, alongside existing CC Units 7–8. SCC granted CPCN 25 Nov 2025 (Case
  PUR-2025-00037); DEQ PSD air permit granted 19 Dec 2025 (Reg. 50396); SCC reaffirmed Feb
  2026 after a reconsideration petition. **But:** DEQ permit appealed in Richmond Circuit
  Court (SELC, Feb 2026) and SCC order appealed to VA Supreme Court (petition 27 May 2026).
  Status is approved / pre-construction, under litigation — not "approvals pending".
  County conditional-use permit status could not be verified. Confidence: **High** on MW/date,
  **Medium** on litigation outcome.
- Sources: VA SCC Final Order PUR-2025-00037, 25 Nov 2025,
  https://www.scc.virginia.gov/docketsearch/DOCS/89g501!.PDF ;
  VA DEQ PSD permit, approved 19 Dec 2025,
  https://deq.ur.virginia.gov/home/showpublisheddocument/32681/639020172177500000 ;
  Virginia Business 16 Feb 2026,
  http://virginiabusiness.com/scc-approves-dominion-chesterfield-gas-plant-deq-air-permit-appeal/

### Homer City (gas redevelopment) — see §1. Status note: now under construction
- >2,000 tradespeople on site (Nov 2026; 1,000 in Mar 2026), vertical construction from
  Apr 2026, Kiewit EPC since Oct 2025, 7× GE Vernova 7HA.02, ~4.4 GW, first power targeted
  early 2028. Air permit issued 18 Nov 2025, under appeal (filed 18 Dec). Grid/BTM: see §1.

---

## 3. Large gas builds NOT in v1 (all verified absent from the full v1 plant list)

| Plant | MW | Date (v2) | Status / evidence | Confidence |
|---|---|---|---|---|
| Cumberland Energy Center, VA (Dominion) | 3,000 (1,500 + 1,500) | 2033 / 2034 | Announced 7 May 2026; county CUP approved 3–1 Oct 2026; SCC CPCN + DEQ air permit still needed; construction 2029, operations 2033/2034. 1,500/1,500 split is an assumption (two units, "2033/2034"). | Medium |
| Mt. Storm CC, WV (Dominion) | 2,600 (1,300 + 1,300) | 2033 / 2034 | Announced 28 Jul 2026; at existing coal site (coal stays online); air-permit modification filed Jul 2026. Split follows trade-press unit dates 2033–34. | Medium |
| CPV Shay Energy Center, WV | 2,100 | 2031 | 3× ~687 MW CC, GE 7HA.03, carbon-capture-ready; construction 2027; WV PSC siting certificate approved Apr 2024; 10-yr EQT gas deal Aug 2026; 9-mile 500 kV line to FirstEnergy Flint Run. MW note: WV DEP modelling protocol (Dec 2025) says 2,060 MW vs CPV's 2,100 MW. | Medium-High |
| Rockport Energy Center (new CC), IN (I&M/AEP) | 1,520 | Jun 2030 | CPCN filed 20 Jul 2026, decision expected early 2027; construction 2027; at existing Rockport coal site. | Medium-High |
| Expedition Generating Station, VA (Tenaska) | 1,540 | Dec 2031 | 2 CC trains, 1,540 MW nominal summer; CPCN filed 15 Jul 2026 (SCC Case PUR-2026-00102); 1.8-mile 500 kV tie to Cunningham; turbines secured; no offtake yet. PJM queue AH1-712 + AH1-723 are the two halves — not double-counted. | Medium |
| Cayuga Energy Complex, IN (Duke) | 1,476 (738 + 738) | 2029 / 2030 | **REMOVED from v2 on 2026-11-14 — verified MISO, not PJM (Duke IURC testimony Cause No. 46193; MISO queue filings).** Was: 2× ~738 MW winter CC; Unit 1 2029, Unit 2 2030; broke ground 2026; CPCN approved (IURC Cause No. 46193). **Flags:** Duke's "increase by 470 MW to 1,476 MW" is a Duke-system net after coal retirement — the Cayuga coal units are MISO, so for PJM the gross 1,476 MW counts. **BA flag:** Duke Energy Indiana is normally MISO; PJM attribution rests on PJM queue AH1-740/745 — needs confirmation. | Removed |
| Maidsville / Fort Martin, WV (FirstEnergy) | 1,200 | Dec 2031 | $2.48–2.5B, +70 MW solar; PSC filing Feb 2026, decision due by Mar 2027; site work from 2027. Demand risk: justified partly by a 1,012 MW data center with no signed power agreement — demand risk, not grid-connection risk. | Medium |
| Cooper CCGT, KY (EKPC) | 745 | Dec 2030 | KY PSC granted CPCN 3 Jul 2025; $1.37B. Use 745 MW (PSC figure), not 786 MW queue MFO. | Medium-High |
| Big Sandy (new CC), KY (Kentucky Power/AEP) | 760 | Mar 2031 | Supersedes the earlier 450 MW CT plan; new CPCN case to be filed (old Case 2026-00103 withdrawn 9 Oct 2026, closed 29 Oct 2026). Tied to TeraWulf Muskie data-center agreement. Site assumed Big Sandy, KY — not confirmed in the new filing. Not the existing 300 MW Big Sandy Peaker Plant in Kenova, WV (ownership change only). | Medium |
| Hunterstown uprate, PA (LS Power) | +455 | Jul 2029 | Existing 810 MW → ~1,265 MW. First project accepted under PJM Expedited Interconnection Track, 8 Oct 2026; in service by 31 Jul 2029. | Medium-High |
| Talen Montour CT, PA | 1,310 | Dec 2031 | ~1,310 MW (2× ~655 MW CCCT), construction from 2028, COD 2031. PA DEP plan-approval application submitted Jun 2026; PJM queue request Apr 2026; grid-connected via existing Montour interconnection. **Early-stage flag (lowest-confidence addition):** air permit pending, no CPCN/FID. | Low-Medium |

Sources (Table B): Cumberland — Dominion fact sheet Apr 2026,
https://www.dominionenergy.com/-/media/content/about/power-stations/cumberland-energy-center/pdfs/cumberland-energy-center-project-fact-sheet.pdf ;
WHRO 21 Oct 2026, https://www.whro.org/2026-10-21/cumberland-supervisors-approve-dominion-gas-plant-proposal ;
Enerdata 23 Oct 2026. Mt. Storm — WV Governor 28 Jul 2026,
https://governor.wv.gov/article/governor-morrisey-announces-26-gw-natural-gas-power-plant-grant-county-existing-coal ;
Dominion project page. Shay — CPV project page, https://cpv.com/our-fleet/cpv-shay-energy-center/ ;
Connect Clarksburg 17 Aug 2026. Rockport — I&M/AEP release 20 Jul 2026,
https://www.aep.com/news/stories/view/12100/ . Expedition — VA SCC order 3 Sep 2026 (Case
PUR-2026-00102), https://www.scc.virginia.gov/docketsearch/DOCS/8%23g101!.PDF ; Tenaska FAQ
Nov 2026. Cayuga — Duke groundbreaking release,
https://news.duke-energy.com/releases/duke-energy-breaks-ground-on-cayuga-energy-complex-project-in-vermillion-county ;
Duke Q3 2026 earnings; IURC Cause 46193. Maidsville — FirstEnergy release 13 Feb 2026,
https://investors.firstenergycorp.com/investor-materials/news-releases/news-details/2026/Mon-Power-and-Potomac-Edison-Select-Maidsville-West-Virginia-Site-for-New-Natural-Gas-Power-Plant/default.aspx .
Cooper — KY PSC press release 3 Jul 2025, https://psc.ky.gov/agencies/psc/press/072025/0703_r01.pdf .
Big Sandy — KY PSC Order Case 2026-00103, 29 Oct 2026,
https://psc.ky.gov/order_vault/Orders_2026/202600103_10292026.pdf . Hunterstown — Utility Dive
9 Oct 2026, https://www.UtilityDive.com/news/engie-ls-power-pjm-expedited-interconnection-eit/832613/ .
Montour CT — PA DEP,
https://www.pa.gov/agencies/dep/dep-regions/northcentral-regional-office/talen-montour-ct-project ;
Montour Co. letter 9 Jun 2026.

### Gas items checked and NOT counted
- **Sammis – South Canton, OH (1,300 MW, 2030):** queue-only (PJM RRI-selected May 2025,
  Phase 2 facility study done; new 345 kV ring-bus substation). No company announcement,
  developer, or offtake found — **pipeline watch only, not in v2**.
- **PJM queue "MFO" trap:** queue MFO is total plant size, not new MW — Cleanview-style
  lists make existing plants (Greensville 1,756 MW, Hanging Rock 1,364 MW) look like new
  builds; only the uprate is incremental. NJ uprates (Bergen +51, Linden +149/+158 MW) and
  MD Cheltenham +53 MW are below the new-build threshold and were not modelled.
- **CPV Oregon / Bay Shore–Lallendorf, OH (1,475 MW, RRI-selected):** reported withdrawn
  after PJM found ~$1.3B interconnection costs (GridAlpha 5 Oct 2026). Not in v1, so nothing
  to remove; GEM still lists it as pre-construction (stale). **Gordonsville, VA (1,294.6 MW,
  RRI-selected):** reported withdrawn by the same single source; needs PJM queue confirmation.
  If both are truly withdrawn, the RRI new-gas cohort falls from 6,408 MW to ~3,638 MW.
- **Appalachian Power pipeline:** POWER Magazine 13 Nov 2026 — $17B, ~3 GW gas by 2031,
  three plants, **locations not yet announced** — not added.
- **RRI non-selected new-gas entries not counted** (no plant name/developer found): Columbia
  Co., PA 2,175 MW (AH1-675) and 2× 1,450 MW (AH1-688/689), all 2030; Nottingham, Harrison
  Co., OH 650 MW (AH1-724), 2030; Susquehanna-Mountain, Luzerne Co., PA 637.8 MW (AH1-733),
  2031; Shenandoah, VA 333.8 MW (AH1-743), 2029; Marshall Co., WV 455 MW (AH1-753,
  in-service date listed as 2019 — stale).
- **Fuel conversions — not net new gas capacity:** AES Petersburg Units 3 & 4 (~1,052 MW
  coal→gas, 2026) — **excluded: AES Petersburg is MISO, not PJM** (verified in the EIA-860M
  Operating sheet; the gas agent's inclusion was an error). Talen Montour Units 1 & 2 —
  coal→gas conversion completed 2023, already in the operating fleet. EKPC Cooper Unit 2 /
  Spurlock co-firing (2029) — conversion of existing coal units, not new MW.

---

## 4. Retirements EIA may have missed

### Keystone + Conemaugh, PA — coal, ADD retiring Dec 2032 (1,872 + 1,951 MW nameplate)
- Owner Keystone-Conemaugh Projects announced Sep 2021 it would cease burning coal by
  31 Dec 2028 (federal wastewater/ELG limits). At end-2025 the company reversed course
  citing data-center demand; PA DEP filed a proposed consent decree 20 Apr 2026 (Indiana
  County Court of Common Pleas, No. 2169-CD-2025) allowing operation **through 2032**
  subject to wastewater-treatment upgrades by 2028. GEM lists planned retirement 2032 for
  both units. No PJM deactivation notice has been filed for either plant.
- **Reconciliation note:** an earlier working note in this project said "no v2 retirement
  to add — the decree is an extension, not a 2032 retirement announcement; they stay in the
  stack through 2036". v2 **overrides** that note: a consent decree that permits operation
  *through 2032* is a dated endpoint, and GEM treats 2032 as the planned retirement. The
  v2 treatment is therefore a **decree-expiry planning assumption, flagged as such** — if
  the plants are extended again, this retirement moves out. MW is EIA nameplate (Keystone
  2×936 MW; Conemaugh 2×975.5 MW; net ~1,711 MW each). Confidence: **Medium**.
- Sources: PA DEP consent-decree motion, filed 20 Apr 2026,
  https://www.pa.gov/content/dam/copapwp-pagov/en/governor/documents/motion%20to%20enter%20cd-as%20filed.pdf ;
  Allegheny Front, 22 Apr 2026, https://www.alleghenyfront.org/josh-shapiro-coal-fired-power-plants-data-centers-keystone-conemaugh/ ;
  GEM, https://www.gem.wiki/Keystone_Generating_Station and
  https://www.gem.wiki/Conemaugh_Generating_Station

### Powerton Units 5–6, IL — coal, ADD retiring May 2031 (1,785.6 MW nameplate)
- 2×892.8 MW nameplate (ICAP 2×769 MW). NRG announced Feb 2024 retirement by 31 Dec 2028
  (ELG); Illinois EPA then allowed operation to 31 Dec 2029. Midwest Generation filed a
  formal PJM deactivation notice 30 Jun 2026 for 1 Jan 2030 under CEJA; PJM requested
  continued operation through 31 May 2031; notice withdrawn 2 Jul 2026. NRG's Q3 2026 10-Q
  confirms PJM requested Powerton operate until at least 31 May 2031. **Flag:** 31 May 2031
  is the end of PJM's requested reliability extension, not a firm date — PJM will reassess
  before each delivery year from 2031/32; units could run longer. Conversely the CEJA
  deadline is 1 Jan 2030, so 2031 is a "no earlier than" date. Confidence: **Medium-High**.
- Sources: PJM deactivation letter, 30 Jun 2026,
  http://www.pjm.com/-/media/DotCom/planning/gen-retire/deactivation-notices/mwg-deactivation-letter.pdf
  (verified by direct fetch 2026-11-14: Powerton 5–6 at 769 MW ICAP each; Fisk CT31–34 at
  49.1/50.8/47.9/22.9 MW; Waukegan CT31–32 at 52.5/48.3 MW); PJM continued-operation letter,
  2 Jul 2026.

### Illinois Generating Assets (NRG), IL — gas CTs, ADD retiring May 2031 (2,649.6 MW nameplate)
- Aurora CT1–10 (1,086.2 MW nameplate: 4×180.8 + 6×60.5), Rockford (484.0 MW: 2×158 +
  168), University Park North (726.0 MW: 12×60.5), University Park South (353.4 MW: 6×58.9).
  Same CEJA sequence as Powerton (deactivation 30 Jun 2026 for 1 Jan 2030; PJM requested
  operation through 31 May 2031; withdrawn 2 Jul 2026). PJM's letter totals the group at
  ~2,376 MW ICAP. Same 2031-floor flag. Individual units are <250 MW but the group is
  2,650 MW. Confidence: **Medium-High**.
- Sources: PJM deactivation letter, 30 Jun 2026,
  http://www.pjm.com/-/media/DotCom/planning/gen-retire/deactivation-notices/il-assets-deactivation-letter.pdf ;
  ICC IRP workshop slides, 24 Sep 2026 (PJM requested ~5.7 GW of CEJA units stay online
  through 2031).

### Fisk CT31–34 + Waukegan CT31–32, IL — oil CTs, ADD retiring May 2031 (372.0 MW nameplate)
- EIA nameplate: Fisk Street 260.0 MW (8×32.5 MW, DFO), Waukegan 112.0 MW (4×28.0 MW, DFO).
  PJM letter ICAPs: Fisk 170.7 MW, Waukegan 100.8 MW. Same CEJA sequence and 2031-floor flag
  as Powerton. Confidence: **Medium-High**.

### Zion Energy Center CTG1–3, IL — gas CTs, ADD retiring May 2031 (596.7 MW nameplate)
- Constellation notified PJM 22 Jun 2026 of intent to deactivate on or before 31 Dec 2029
  under CEJA; PJM requested continued operation at least through 29/31 May 2031; notice
  withdrawn 2 Jul 2026. MW verified in the EIA-860M Operating sheet: 3×198.9 MW nameplate
  (net summer 161/162/155 MW). Same 2031-floor flag. Confidence: **Medium-High**.
- Source: Constellation withdrawal letter, 2 Jul 2026,
  http://www.pjm.com/-/media/DotCom/planning/gen-retire/deactivation-notices/zion-ct1-ct2-ct3-withdrawal.pdf

### West Lorain Units 1A & 1B, OH — oil, ADD retiring Jun 2030 (130.6 MW nameplate)
- Owner Vermillion Power (Lotus Infrastructure). Deactivation notice Jun 2026 (PJM log date
  19 Jun 2026); PJM response 28 Aug 2026 found no reliability violations; may deactivate
  1 Jun 2030. EIA nameplate 2×65.3 MW (DFO GTs; ICAP 50 + 51 MW). Units 2–6 (gas) are NOT
  retiring. Confidence: **High**.
- Sources: PJM response, 28 Aug 2026,
  https://www.pjm.com/-/media/DotCom/planning/gen-retire/deactivation-notices/west-lorain-pjm-response.pdf ;
  PJM TEAC deactivation update, 8 Sep 2026.

### Forked River Units 1 & 2, NJ — gas, ADD retiring Jun 2027 (76.8 MW nameplate)
- Unit 2: 31 MW ICAP, notice 24 Feb 2025 effective 1 Jun 2026 (NJ air-permit grounds);
  rescinded 22 Jul 2025, replaced with a new notice effective 1 Jun 2027. Unit 1: 34 MW
  ICAP, notice 24 Feb 2025 effective 1 Jun 2027 (NJ carbon rules). PJM response 30 May 2025
  cleared both. EIA nameplate 2×38.4 MW (NG GTs). Confidence: **High**.

### Brandon Shores (coal, 1,370.2 MW) + Wagner (oil, 773.7 MW) — retime Jun 2029 → May 2031
- FERC accepted amended RMR rate schedules 18 Aug 2026 (Docket Nos. ER26-2739-002 /
  ER26-2740-002), extending the RMR obligation from 31 May 2029 to 31 May 2031, on PJM's
  28 May 2026 formal request citing delayed transmission upgrades. Talen's 2 Sep 2026 ELG
  recertification confirms operation through 31 May 2031. Confidence: **High**.
- Source: FERC order via PJM, 18 Aug 2026,
  http://www.pjm.com/-/media/DotCom/planning/gen-retire/deactivation-notices/brandon-shores-and-wagner-letters-as-ferc-amendment.pdf

### Kincaid Units 1 & 2, IL — coal — KEPT at Jan 2029 (no change in v2)
- Vistra filed PJM deactivation notice 22 Jul 2025: both units, 556 MW ICAP each, effective
  30 Nov 2027 (EPA Coal Combustion Residuals Rule). PJM responded 25 Nov 2025: no reliability
  violations; units may deactivate 30 Nov 2027. Vistra's Dec 2025 ELG progress report and
  Nov 2025 CCR update confirm boiler cessation by 30 Nov 2027. WARN notices show layoffs
  Jan 2028. Kincaid filed a FERC petition 9 Mar 2026 (ER26-1686) for a must-offer-exception
  deadline waiver — consistent with retirement proceeding, not an RMR. **No evidence of a
  Kincaid-specific RMR agreement was found.**
- **Why v2 keeps Jan 2029 anyway:** the RMR override was a direct user instruction — "all
  coal plant retirements scheduled between this year and end of year 2028 are to be pushed to
  Jan 2029" as a manual scenario to account for the president's RMR announcements. It was
  applied as a blanket rule, not as a claim about individual filings. The retirements agent
  recommended reverting Kincaid to Nov 2027; the builder declined because the user's
  instruction is the authority for the override. **If the user revisits the override,
  Kincaid moves to 30 Nov 2027 (-14 months) and 2029 coal retirements fall by 1,319 MW.**
  One watch item: EPA's Nov 2025 proposal would extend the CCR pond-closure deadline for 11
  plants including Kincaid from Oct 2028 to Oct 2031 — a proposal only, not a decision.
- Sources: Vistra deactivation letter, 22 Jul 2025,
  https://www.pjm.com/-/media/DotCom/planning/gen-retire/deactivation-notices/kincaid-deactivation-letter.pdf ;
  PJM response, 25 Nov 2025,
  https://www.pjm.com/-/media/DotCom/planning/gen-retire/deactivation-notices/kincaid-pjm-response.pdf

### Rockport Units 1 & 2 — no change (immaterial)
- AEP/I&M deactivation notice 28 Mar 2025: both units retire by 31 Dec 2028. v1's Jan 2029
  (RMR override) is effectively the same date. Watch item: Indiana's attorney general filed
  a motion in Jul 2026 to intervene in the consent-decree proceedings seeking to keep Rockport
  Unit 1 "available as long as it is needed" — no outcome found as of Nov 2026.

### Cardinal Unit 3 — no change
- PJM TEAC 3 Nov 2026: 620 MW ICAP (650 MW nameplate), notified 22 Jul 2026, requested
  deactivation 1 Jan 2029, reliability analysis in progress. Buckeye Power has said since
  Aug 2022 it plans to shut Unit 3 by end of 2028. Units 1–2 are NOT retiring (DOE awarded
  $34M in Feb 2026 for Units 1–2 upgrades; all three units got a MATS exemption to 9 Jul 2029).

### Eddystone Units 3–4 — no change, flag likely extension
- Originally scheduled to retire 31 May 2025. DOE has issued six successive FPA §202(c)
  emergency orders keeping them available, most recently 21 Aug 2026 (Order No. 202-26-40)
  through 20 Nov 2026 — matching v1's Nov 2026 date. That order states the units "shall not
  be considered a capacity resource" and that emergency conditions "are also likely to
  continue in subsequent years". No further renewal order was announced as of 14 Nov 2026.
  v2 keeps Nov 2026 and flags a likely further extension (watch for the next 90-day renewal);
  it does not retime on speculation.

### Martins Creek / Brunner Island (gas, Jun 2035) — no change
- No contrary filing found; not independently re-verified beyond noting no contrary filing
  appeared on PJM's deactivation page (last updated 20 Oct 2026).

### Miami Fort Units 7–8, OH — fuel switch coal → gas, 1,114.8 MW, 2028 (net zero)
- The Sep 2020 Vistra plan to retire by end-2027 has been **reversed**. Vistra announced in
  late 2025 it will convert Miami Fort to natural gas (2025 Sustainability Report; proxy
  statement 18 Mar 2026: "intention to convert our Miami Fort coal plant to a natural gas
  plant in the coming years"); Ohio House release confirms Vistra will "continue operating
  the Miami Fort Power Plant beyond 2027 and convert the plant to a modern, natural gas-fueled
  operation". GEM lists announced coal→gas conversion in 2028. Net capacity effect ≈ zero;
  v2 books coal −1,114.8 MW / gas +1,114.8 MW in 2028 (EIA nameplate 557.1 + 557.7 MW).
  Confidence: **Medium** (date 2028 is GEM's; Vistra's language is "in the coming years").
- Sources: Vistra 2025 Sustainability Report; Vistra proxy, 18 Mar 2026,
  https://www.sec.gov/Archives/edgar/data/1692819/000162828026019029/vistra-20260318.htm ;
  Ohio House, https://www.ohiohouse.gov/members/mike-odioso/news/odioso-applauds-plan-to-extend-operations-at-miami-fort-power-plant-140600

### Prime suspects cleared — NO retirement announced
- **W.H. Sammis, OH (coal, ~2,233 MW):** already retired — Units 1–4 retired 31 May 2020;
  Units 5–7 closed 3 May 2023. Site sold to ETEM; demolition/remediation to complete H1 2027.
- **Montour, PA (~1,758 MW):** converted, not retired. Talen committed Nov 2020 to stop
  burning coal by end-2025 and convert to gas; conversion completed Aug 2023; EIA-860M lists
  gas as the fuel. (The separate Talen Montour CT new-build is in §3.)
- **Gavin Power Plant, OH (coal, ~2,600 MW, 2×1,300):** no firm retirement date. InsideClimate
  News (Oct 2024) reported Gavin was "poised" to close or convert by 2031; the buyer told FERC
  it has **no timetable** for closing or switching fuel. Do not add.
- **Clifty Creek, IN (coal, 1,303 MW, 6×217.3):** no scheduled retirement; still operating as
  of Apr 2026. OVEC intercompany power agreement runs to 2040; I&M's 2024 IRP lists Clifty
  Creek only as a 2039/40 planning assumption — outside the horizon anyway.
- **Kyger Creek, OH (coal, 1,086 MW, 5 units):** same OVEC position as Clifty Creek; agreement
  to 2040; still operating as of Apr 2026. One low-quality profile claimed "expected to retire
  by 2025–2026" — contradicted by April 2026 reporting; disregarded.
- **Homer City coal (1,888 MW):** retired 1 Jul 2023 (past, not forward).
- **East Bend, KY (coal, 600 MW net / 669 MW gross):** Duke Energy Kentucky 2024 IRP: convert
  to diesel co-firing in 2030, estimated retirement 31 Dec 2038 — beyond 2036.
- **Nuclear:** no PJM nuclear retirement announced in 2024–2026. Perry, Davis-Besse and Beaver
  Valley (previously slated for retirement) were acquired by Vistra (2023–2024); Perry's licence
  was renewed 7 Jul 2025 to 7 Nov 2046; Vistra signed 20-year Meta PPAs 9 Jan 2026 covering
  2,609 MW including **433 MW of uprates** across the three plants — see §6 (candidate, not added).

### PJM deactivation list — what was checked
- PJM's official Generator Deactivation Notices page (last updated 20 Oct 2026),
  http://www.pjm.com/planning/service-requests/gen-deactivations/generator-deactivation-notices ,
  was reviewed in full. Entries since Jan 2025: real forward retirements are covered above
  (Cardinal 3, West Lorain, Forked River, Rockport, Kincaid, Brandon Shores/Wagner updates,
  Eddystone DOE orders, Illinois CEJA + Midwest Generation notices, Zion). Withdrawn /
  reactivated / transferred — not retirements: Elwood (Units 8–9 retired 1 Jun 2025, already
  in v1's 2026 actuals; Units 5–7 sold to Dairyland Power Cooperative 6 Mar 2026, deactivation
  withdrawn 6 May 2026, now exporting to MISO with a 2045 retirement per ICC slides; Units 1–4/8–9
  sold to Hull Street Energy — **net PJM effect is partial and could not be cleanly resolved
  from PJM letters alone; not modelled, flagged**); Morgantown CT3–6 (oil CTs; notices Dec 2023,
  partial rescissions May–Dec 2024, reactivations through Sep 2025; site sold to TeraWulf, FERC
  approved 29 Jul 2026, oil units ~216 MW still operating); Sayreville CT (reactivated); Indian
  River CT10, Lawnside 14 BT, Perryman 6, Kenilworth (withdrawals/rescissions); Fisk/Waukegan CTs
  (Feb 2025 notices withdrawn, superseded by the Jun 2026 CEJA notices above); Rocky Road CT33
  (revision). Non-generation/trivial: Mantua Creek (battery deactivation, Oct 2026, no MW stated);
  landfill-gas, solar, battery or small units generally <10 MW each — on the PJM page if an
  exhaustive sweep is wanted, immaterial to a ~200 GW stack.

---

## 5. Wind / solar — verification of the 14 large v1 projects

### Removed / corrected
- **Bellflower Solar, VA — REMOVE, −600 MW solar.** Developer terminated it; Brunswick
  County revoked its CUP unanimously 7 Oct 2026. Source: Brunswick County *Brunswick Brief*,
  23 Oct 2026 (meeting 21 Oct 2026),
  https://cdnsm5-hosted.civiclive.com/UserFiles/Servers/Server_10858796/File/Brunswick%20Brief%202026/Brunswick%20Brief%20-%2010212026.pdf
- **Rocky Run Solar, VA — 300 MW / Jan 2028 is wrong.** Dominion now says up to 290 MW, in
  service end-2031, construction spring 2027. −10 MW, +~3 years. Source: Dominion project page,
  https://www.dominionenergy.com/about/delivering-energy/solar-energy-projects/virginia-solar-projects/rocky-run
- **Steward Creek Solar, IL — 1,200 MW is the two-phase total, not Phase 1.** Each phase is
  600 MWac: Phase 1 COD 2029, Phase 2 COD 2030. Total unchanged; 600 MW moves 2029 → 2030.
  Sources: PV Magazine USA, 6 Feb 2026,
  https://pv-magazine-usa.com/2026/02/06/terraform-power-acquires-1-5-gw-illinois-solar-project/ ;
  Lee County Phase 2 permit application,
  http://www.leecountyil.com/DocumentCenter/View/4527/Steward-Creek-Solar-Project-Narrative_Phase-2 .
  A 600 MW interconnection agreement with ComEd/PJM is executed — grid-connected, not BTM.
- **CVOW, VA — Jan 2027 is wrong.** Dominion Q3 2026 (30 Oct 2026): ~85% complete, 44/176
  turbines installed, completion end-2027; first power delivered Mar 2026. ~11-month slip;
  status now >50% complete, not EIA "U ≤50%". Stop-work: BOEM issued a stop-work order to all
  five US offshore wind projects under construction, including CVOW, on 22 Dec 2025; on
  16 Jan 2026 Judge Jamar Walker (E.D. Va.) issued a preliminary injunction allowing CVOW
  construction to proceed. MW caveat: Dominion says "2.6 GW" and "176 × 14-MW turbines";
  Wikipedia lists 176 × 14.7 MW (= 2,587 MW); EIA figure 2,640 MW (176 × 15 MW) — keep 2,640 MW
  as the EIA figure but note the ~50 MW ambiguity. Sources: Offshore Engineer / Dominion Q3
  2026, published 2 Nov 2026,
  https://www.oedigital.com/news/544054-dominion-energy-installs-44-turbines-at-virginia-offshore-wind-project ;
  Legal 500, 6 Feb 2026,
  https://www.legal500.com/intelligence/united-states/energy-and-natural-resources/updated-court-lifts-stop-work-orders-for-three-paused-offshore-wind-projects
- **Illinois Generation LLC = Heritage Prairie Wind (Pattern/Repsol, 616.5 MW).** Construction
  started June 2026 — v1 status T is stale, should be U. Date Apr 2028 confirmed. Sources:
  Pattern Energy project page, https://patternenergy.com/projects/heritage-prairie-wind/ ;
  Livingston County Board resolution, May 2026.

### Verified unchanged (one line each)
- **Panther Grove 2** (472.5 MW, Dec 2027, U) — verified unchanged.
- **Panther Grove 1** (423 MW, Dec 2026, TS) — 22 turbines installed by Feb 2026; developer
  says construction continues through 2026, COD late 2026. Date/MW right; TS status not
  corroborated (likely still U/V at Sep 2026) — **left as-is in v2** (no change booked on a
  status inference alone).
- **Starfire Mountain Solar** (410 MW, Sep 2029, L) — Phase 1 ~210 MW + Phase 2 ~200 MW; KY
  Siting Board approved Phase 1 on 1 Aug 2025; construction not yet commenced as of 31 Jul 2026 letter.
- **Firefly Solar PA** (401.6 MWac, Dec 2027, L) — original 200 MW project cancelled Dec 2024,
  revised ~400 MW project in Lawrence County.
- **Harvey Solar** (350 MW, Aug 2028, T) — Ohio Supreme Court affirmed OPSB certificate 30 Apr
  2025; Leeward acquired it, announced 24 Mar 2026, construction fall 2026, operations late 2028.
- **Mammoth Solar South / Central I / Central II** (300 MW each, Oct–Nov 2026) — construction of
  all three phases completed, marked 7 Oct 2026, commercial operation imminent/Q4 2026.
- **Yellow Wood Solar** (300 MW, Dec 2027, U) — full construction began Oct 2026; Meta PPA;
  Invenergy states power is delivered to the local grid while Meta receives clean energy
  credits — **grid-connected, NOT BTM**.
- **Heritage Prairie Solar** (300 MW, Sep 2028, T) — verified unchanged.
- **Firelands Wind** (297 MW, May 2027, U) — Ohio Supreme Court affirmed OPSB certificate
  27 Jul 2023; Enverus PJM New Build Report, 16 Jul 2026, lists COD 30 Apr 2027.
- **No wind/solar project among the 14 was found to be behind-the-meter.** Grid-connection
  evidence found for CVOW, Steward Creek, Heritage Prairie Wind & Solar, Panther Grove 1 & 2,
  Firefly, Yellow Wood, Mammoth, Starfire, Harvey Solar, Firelands Wind.
- Net quantified change to the listed wind/solar projects: **−610 MW of solar** (Bellflower
  −600, Rocky Run −10); no MW change to the listed wind.

---

## 6. Nuclear uprates — candidates NOT added

- **Constellation–Google, announced 6 Oct 2026:** 20-year PPA with Google enabling >$4.3bn
  investment across 11 Constellation nuclear units in Illinois, Pennsylvania and New Jersey
  to add **~890 MW of incremental generation capacity to the PJM grid, first uprate expected
  in 2028**, all online before end-2032; plus a separate 15-year supply agreement for 2,700 MW
  of existing output (not new capacity — do not count the 2,700 MW). Conditional DOE loan
  commitment up to $5bn signed Oct 2026. NRC applications had not yet been filed as of Oct 2026
  (first planned Q4 2026) and the per-unit MW split was not published. **Not added: the 11 units
  span IL, PA and NJ and not all are in PJM — several Constellation Illinois units are in MISO
  (e.g. Quad Cities, Clinton) — so the full 890 MW cannot be attributed to PJM without the
  per-unit split.** Source: Constellation Q3 2026 results, 9 Nov 2026,
  https://www.constellationenergy.com/news/2026/11/constellation-reports-third-quarter-2026-results.html
- **Vistra–Meta, 9 Jan 2026:** 20-year PPAs covering 2,609 MW including **433 MW of uprates**
  across Perry, Davis-Besse and Beaver Valley (all PJM). No per-unit MW split or dates published
  in the sources retrieved — **candidate, not added**.

---

## 7. What was checked and could not be verified

- Homer City PJM interconnection / CIR MW (no PJM queue, GIA or CIR figure found; the 700–800 MW
  grid figure is a CEO statement via Axios, not a PJM filing, and "the split is not locked");
  Homer City tenant (AWS has no definitive agreement, Aug 2026).
- Shippingport total MW and power-plant construction status (3.6 GW vs ~2.55 GW); Socrates North
  in-service status; Socrates the Younger 250 vs 340 MW (OPSB approval used).
- Chesterfield county conditional-use permit status; Wolf Summit exact COD (2027 vs late 2028).
- Cayuga BA attribution — RESOLVED 2026-11-14: verified MISO (Duke IURC testimony Cause No. 46193; MISO queue filings); removed from v2.
- Cumberland 1,500/1,500 and Mt. Storm 1,300/1,300 unit splits (assumptions from "2033/2034"
  language); Cumberland SCC CPCN not yet filed as of Nov 2026.
- Gordonsville withdrawal (single newsletter source); Bay Shore withdrawal (two secondary sources,
  GEM contradicts).
- Sammis–South Canton developer, offtake, and whether it serves a data center.
- Big Sandy 760 MW site (assumed Big Sandy, KY) and whether any of it is BTM for TeraWulf.
- Elwood's final PJM MW disposition (partial sale to Dairyland/MISO + Hull Street).
- Whether any additional coal unit retired in 2026 outside PJM's notice page.
- MD, NJ, DE, NC, IL were not systematically swept for ≥250 MW gas builds beyond the RRI list
  (which shows no new-gas RRI selections there except NJ uprates, all below threshold).
- The Constellation–Google 890 MW and Vistra–Meta 433 MW nuclear uprate per-unit splits.
- Zion CT exact online/retirement mechanics beyond the PJM letters (MW verified in EIA file).

---

## 8. Reconciliation decisions made by the builder (not by any single agent)

1. **Homer City = 0 MW, not 700–800 MW.** The BTM agent's primary call (0 MW under the user
   rule) was adopted over the gas agent's "Uncertain" label, because the evidence (data-center
   campus first, ~82% on-site, no signed tenant, no PJM interconnection figure) fits the user's
   worked example. The 700–800 MW surplus-export alternative is recorded in
   `manual_adjustments.csv` and `summary_v2.json` so it can be switched on if the user prefers
   that reading (+700–800 MW to the 2036 total).
2. **Kincaid kept at Jan 2029** despite no Kincaid-specific RMR filing, because the override was
   a direct user instruction applied as a blanket scenario (see §4).
3. **Keystone/Conemaugh added at Dec 2032** (decree-expiry planning assumption), overriding an
   earlier working note that said not to add them (see §4).
4. **Wolf Summit correction is +21.1 MW, not +228.5 MW**, because v1 carries both EIA units
   (578.9 MW total). The gas agent's larger figure came from seeing only one unit.
5. **AES Petersburg excluded** — it is MISO, not PJM (verified in the EIA file). The gas agent
   had listed it as a fuel conversion.
6. **Nameplate basis throughout** for manual additions/retirements, with ICAP figures noted
   alongside (CEJA block: 2,649.6 MW nameplate vs 2,376 MW ICAP for the IL gas assets;
   Powerton 1,785.6 vs 1,538; Fisk/Waukegan 372.0 vs 271.5; Zion 596.7 vs ~478 net summer;
   West Lorain 130.6 vs 101; Forked River 76.8 vs 65; Keystone 1,872 vs 1,711 net;
   Conemaugh 1,951 vs 1,711 net). Crane is the deliberate exception (835 MW company figure).
7. **Cayuga REMOVED 2026-11-14** — verified MISO, not PJM. (It had been kept as PJM with a BA flag on the queue evidence; the verification reversed that.)
8. **Talen Montour CT (1,310 MW) included** despite early stage, because it has a PA DEP
   application and a PJM queue request comparable to other included projects (e.g. Big Sandy,
   whose CPCN is not yet filed either). It is the lowest-confidence addition and is flagged as such.
9. **Sammis–South Canton, Shippingport, the nuclear uprates and Appalachian Power's
   unlocated ~3 GW were NOT added** — see the relevant sections for why.
