#!/usr/bin/env python3
"""Build PJM capacity stack v2 — manual corrections to v1.

v1 files are NOT touched. Reads pjm_capacity_plants.csv / pjm_capacity_stack.csv /
pjm_capacity_changelog.csv / summary.json, applies the reconciled manual
adjustments (see ADJUSTMENTS + NEW_ROWS below), and writes v2 files alongside.

Basis: nameplate MW throughout, consistent with the v1 EIA-860M changelog.
Manual additions use EIA-860M Operating-sheet nameplate where the unit exists
there, else the company-announced figure (noted per row). Crane is the one
exception: Constellation's ~835 MW company figure is used instead of EIA
nameplate 980.8 MW, because the stack anchor is ICAP-based and 835 MW is
close to the unit's net summer rating (802.8 MW).

Key reconciliation decisions (see research_log.md for full reasoning):
- Homer City: BTM, grid MW 0 — full 4,396 MW excluded per the user's rule
  (primarily serves on-site data-center load). The ~700-800 MW grid-export
  split quoted by the CEO is NOT counted; it is flagged as an alternative.
- Kincaid: KEPT at Jan 2029. The user-directed RMR override (all PJM coal
  retirements scheduled 2026-2028 -> Jan 2029) is the authority; no
  Kincaid-specific RMR filing was found, but the override was instructed
  as a blanket manual scenario, not as a claim about individual filings.
- Keystone/Conemaugh: ADDED retiring Dec 2032 (decree-expiry planning
  assumption; GEM lists planned retirement 2032; no PJM deactivation filed).
- Wolf Summit: v1 actually carries BOTH units (371.5 + 207.4 = 578.9 MW),
  so the correction vs v1 is only +21.1 MW to reach the 600 MW plant total,
  not +228.5 MW.
- AES Petersburg conversion: EXCLUDED — AES Petersburg is MISO, not PJM.
- Cayuga: REMOVED 2026-11-14 per user decision - verified MISO, not PJM
  (Duke IURC testimony Cause No. 46193; MISO queue filings). It had been kept
  on PJM queue entries AH1-740/745 only, never verified as this project.
- Constellation-Google nuclear uprates (890 MW) and Vistra/Meta uprates
  (433 MW): NOT added — PJM share / per-unit split unpublished.
- Sammis-South Canton (1,300 MW, queue-only, no developer): NOT added.
- Shippingport (2.7-3.6 GW, BTM-majority, MW uncertain): NOT added.
"""
import json
from pathlib import Path
import numpy as np
import pandas as pd

BASE = Path(__file__).resolve().parent
FUELS = ["Coal", "Natural Gas", "Nuclear", "Hydro", "Pumped Storage",
         "Wind", "Solar", "Oil", "Battery Storage", "Other"]
STACK_ORDER = ["Coal", "Natural Gas", "Nuclear", "Hydro", "Pumped Storage",
               "Oil", "Wind", "Solar", "Battery Storage", "Other"]
FUEL_COLORS = {
    "Coal": "#3b3b3b", "Natural Gas": "#d95f02", "Nuclear": "#7570b3",
    "Hydro": "#1b9e77", "Pumped Storage": "#66a61e", "Wind": "#377eb8",
    "Solar": "#e6ab02", "Oil": "#a6761d", "Battery Storage": "#e7298a",
    "Other": "#999999",
}
ANCHOR_YEAR = 2025
ACCESSED = "2026-11-14"

# ---------------------------------------------------------------- adjustments
# Each dict is one row of manual_adjustments.csv. "match" selects v1 plant rows
# to edit in place (plant_name substring + generator_id list, or None for new).
# v1_mw/v1_date are group totals for the matched rows; v2_mw/v2_date the same.
ADJUSTMENTS = [
    dict(plant="Homer City Generating Station", unit="CT1-CT7 + CA1-CA7 (14 units)",
         state="PA", fuel="Natural Gas", v1_mw=4396.0, v1_date="2028-07 to 2029-11",
         v2_mw=0.0, v2_date="-", change_type="BTM-exclude",
         reason="Data-center campus first: ~82% of output earmarked for on-site data centers; "
                "generator primarily serves on-site load, grid connection incidental/backup. "
                "Per user rule grid MW = 0 (a 2 GW plant + 2 GW load + 500 MW connection counts as 0, "
                "not 500 MW). CEO-quoted ~700-800 MW grid-export split is not locked, no tenant signed, "
                "no PJM queue/GIA/CIR figure found — flagged as alternative, not counted.",
         classification="BTM",
         source_url="https://www.businesswire.com/news/home/20250402452555/en/Homer-City-Redevelopment-and-Kiewit-Announce-Countrys-Largest-Natural-Gas-Powered-Data-Center-Campus-to-Support-AI-and-HPC-Demand",
         source_date="2025-04-02", date_accessed=ACCESSED),
    dict(plant="Bellflower Solar (VA)", unit="BELLF", state="VA", fuel="Solar",
         v1_mw=600.0, v1_date="2030-01", v2_mw=0.0, v2_date="-", change_type="remove",
         reason="Developer terminated the project; Brunswick County revoked its conditional use permit "
                "unanimously on 7 Oct 2026.",
         classification="grid-connected",
         source_url="https://cdnsm5-hosted.civiclive.com/UserFiles/Servers/Server_10858796/File/Brunswick%20Brief%202026/Brunswick%20Brief%20-%2010212026.pdf",
         source_date="2026-10-23", date_accessed=ACCESSED),
    dict(plant="Rocky Run Solar", unit="ROCKY", state="VA", fuel="Solar",
         v1_mw=300.0, v1_date="2028-01", v2_mw=290.0, v2_date="2031-12", change_type="retime",
         reason="Dominion now lists up to 290 MW, in service end-2031, construction spring 2027. "
                "-10 MW and ~3-year slip vs EIA.",
         classification="grid-connected",
         source_url="https://www.dominionenergy.com/about/delivering-energy/solar-energy-projects/virginia-solar-projects/rocky-run",
         source_date="2026-11-14", date_accessed=ACCESSED),
    dict(plant="Steward Creek Solar Phase 1", unit="SC1 (Phase 1) + SC2 (Phase 2)",
         state="IL", fuel="Solar", v1_mw=1200.0, v1_date="2029-12",
         v2_mw=1200.0, v2_date="2029-12 (600 MW) + 2030-12 (600 MW)", change_type="retime",
         reason="1,200 MW is the two-phase total, not Phase 1: each phase is 600 MWac, Phase 1 COD 2029, "
                "Phase 2 COD 2030. Total unchanged; 600 MW moves 2029 -> 2030. 600 MW interconnection "
                "agreement with ComEd/PJM executed — grid-connected.",
         classification="grid-connected",
         source_url="https://pv-magazine-usa.com/2026/02/06/terraform-power-acquires-1-5-gw-illinois-solar-project/",
         source_date="2026-02-06", date_accessed=ACCESSED),
    dict(plant="Coastal Virginia Offshore Wind (CVOW) Commercial Project", unit="CVOWC",
         state="VA", fuel="Wind", v1_mw=2640.0, v1_date="2027-01", v2_mw=2640.0,
         v2_date="2027-12", change_type="retime",
         reason="Dominion Q3 2026 (30 Oct 2026): ~85% complete, 44/176 turbines installed, completion "
                "end-2027; first power Mar 2026. ~11-month slip. Stop-work order 22 Dec 2025 lifted by "
                "preliminary injunction 16 Jan 2026 (Judge Jamar Walker, E.D. Va.). MW kept at EIA 2,640 "
                "(176 x 15 MW); Dominion says '2.6 GW', 176 x 14.7 MW = 2,587 MW — ~50 MW ambiguity noted.",
         classification="grid-connected",
         source_url="https://www.oedigital.com/news/544054-dominion-energy-installs-44-turbines-at-virginia-offshore-wind-project",
         source_date="2026-11-02", date_accessed=ACCESSED),
    dict(plant="Sycamore Riverside Energy, LLC", unit="SYRVS", state="IN", fuel="Natural Gas",
         v1_mw=964.0, v1_date="2029-03", v2_mw=918.0, v2_date="2029-03",
         change_type="status-correct",
         reason="Correct MW is 918 MW (4x GE 7F.05, developer/utility/IURC figure), not EIA nameplate 964 MW. "
                "Status wrong: CPCN filed 10 Apr 2026 (IURC Cause No. 46389, decision expected Dec 2026); "
                "gas-pipeline necessity certificate approved 26 Aug 2026 (Cause No. 46407). I&M has a "
                "purchase-and-sale agreement to acquire it. Grid-connected utility peaker, COD 31 Mar 2029.",
         classification="grid-connected",
         source_url="https://www.indianamichiganpower.com/company/news/view?releaseID=11849",
         source_date="2026-04-10", date_accessed=ACCESSED),
    dict(plant="Wolf Summit Energy", unit="HCCT1 + HCCA1", state="WV", fuel="Natural Gas",
         v1_mw=578.9, v1_date="2028-12", v2_mw=600.0, v2_date="2028-12",
         change_type="status-correct",
         reason="v1 carries both EIA units (371.5 + 207.4 = 578.9 MW); the plant is a single 600 MW CCGT "
                "(GE Vernova 7HA.02, $1.2B), so the correction is only +21.1 MW. Status wrong: FID 13 Nov 2025, "
                "groundbreaking 22 Apr 2026, under construction; 100% contracted to ODEC. COD 'as early as "
                "late 2028' (ODEC) — v1 Dec 2028 kept; a 2027 figure in trade press is unconfirmed. "
                "Note: 'Glen Falls Facility' (625 MW) in queue lists is the same plant — do not double-count.",
         classification="grid-connected",
         source_url="https://www.odec.com/wp-content/uploads/Wolf-Summit-Press-Release-Final-7-22-25.pdf",
         source_date="2025-07-22", date_accessed=ACCESSED),
    dict(plant="Trumbull Energy Center", unit="GT11 + GT12 + STG", state="OH", fuel="Natural Gas",
         v1_mw=977.4, v1_date="2026-04", v2_mw=950.0, v2_date="2026-01",
         change_type="status-correct",
         reason="Entered commercial operation Jan 2026 (target COD 31 Jan 2026), not Apr 2026; ~950 MW "
                "(Hanwha; 940-953 MW across sources) vs EIA nameplate 977.4 MW. Same stack year (2026), "
                "so only the MW changes. Grid-connected, PJM ATSI zone.",
         classification="grid-connected",
         source_url="https://www.hanwha.com/newsroom/news/press-releases/hanwha-power-enters-us-market-with-successful-commissioning-of-trumbull-energy-center-combined-cycle-gas-turbine-power-plant.do",
         source_date="2026-06-24", date_accessed=ACCESSED),
    dict(plant="Chesterfield", unit="CERC1-CERC4", state="VA", fuel="Natural Gas",
         v1_mw=1000.0, v1_date="2029-06", v2_mw=944.0, v2_date="2029-06",
         change_type="status-correct",
         reason="Correct MW is 944 MW nominal (4x GE Vernova 7F simple-cycle, dual-fuel gas/oil), not 4x250 MW. "
                "Status wrong: SCC granted CPCN 25 Nov 2025 (Case PUR-2025-00037); DEQ PSD air permit granted "
                "19 Dec 2025; SCC reaffirmed Feb 2026. Now approved / pre-construction, under litigation "
                "(DEQ permit appealed Feb 2026; SCC order appealed to VA Supreme Court 27 May 2026). "
                "COD 1 Jun 2029 kept; litigation risk flagged.",
         classification="grid-connected",
         source_url="https://www.scc.virginia.gov/docketsearch/DOCS/89g501!.PDF",
         source_date="2025-11-25", date_accessed=ACCESSED),
    dict(plant="Illinois Generation LLC (Heritage Prairie Wind)", unit="HPW", state="IL", fuel="Wind",
         v1_mw=616.5, v1_date="2028-04", v2_mw=616.5, v2_date="2028-04",
         change_type="status-correct",
         reason="Status only: construction started Jun 2026 (Pattern/Repsol); EIA status (T) is stale, "
                "should be (U) under construction. MW and Apr 2028 date confirmed. Grid-connected.",
         classification="grid-connected",
         source_url="https://patternenergy.com/projects/heritage-prairie-wind/",
         source_date="2026-11-14", date_accessed=ACCESSED),
    dict(plant="Brandon Shores", unit="1 + 2", state="MD", fuel="Coal",
         v1_mw=1370.2, v1_date="2029-06", v2_mw=1370.2, v2_date="2031-05", change_type="retime",
         reason="FERC accepted amended RMR rate schedules 18 Aug 2026 (ER26-2739-002 / ER26-2740-002), "
                "extending the RMR obligation from 31 May 2029 to 31 May 2031 on PJM's 28 May 2026 request "
                "citing delayed transmission upgrades. Talen's 2 Sep 2026 ELG recertification confirms "
                "operation through 31 May 2031.",
         classification="grid-connected",
         source_url="http://www.pjm.com/-/media/DotCom/planning/gen-retire/deactivation-notices/brandon-shores-and-wagner-letters-as-ferc-amendment.pdf",
         source_date="2026-08-18", date_accessed=ACCESSED),
    dict(plant="Herbert A Wagner", unit="3 + 4", state="MD", fuel="Oil",
         v1_mw=773.7, v1_date="2029-06", v2_mw=773.7, v2_date="2031-05", change_type="retime",
         reason="Same FERC-accepted RMR extension as Brandon Shores (same docket pair, same 28 May 2026 "
                "PJM request): RMR obligation extended to 31 May 2031.",
         classification="grid-connected",
         source_url="http://www.pjm.com/-/media/DotCom/planning/gen-retire/deactivation-notices/brandon-shores-and-wagner-letters-as-ferc-amendment.pdf",
         source_date="2026-08-18", date_accessed=ACCESSED),
    dict(plant="Crane Clean Energy Center (Three Mile Island Unit 1)", unit="1", state="PA",
         fuel="Nuclear", v1_mw=0.0, v1_date="-", v2_mw=835.0, v2_date="2027-07", change_type="add",
         reason="Restart missed by EIA-860M: EIA Operating lists it (OS) out of service, not in Planned. "
                "Constellation 20-yr PPA with Microsoft announced 20 Sep 2024; target accelerated to H2 2027 "
                "(23 Sep 2025; 'on track' 28 Sep 2026). $1.6bn restart; DOE closed $1bn loan 18 Nov 2025; "
                "NRC final EA/FONSI Sep 2026 but restart approval still pending (1 exemption + 3 licence "
                "amendments, to licence expiry 19 Apr 2034). FERC granted waiver 1 Jun 2026 transferring "
                "760 MW of Capacity Interconnection Rights from Eddystone 3-4 to Crane. Grid-connected: "
                "Microsoft buys energy/capacity/attributes under the PPA; no data center at the plant, power "
                "injected into the PJM grid. MW is Constellation's ~835 MW (EIA nameplate 980.8, net summer "
                "802.8; FERC order reportedly says 859 MW). Regulatory-risk flag.",
         classification="grid-connected",
         source_url="https://www.constellationenergy.com/news/2024/09/constellation-to-launch-crane-clean-energy-center-restoring-jobs-and-carbon-free-power-to-the-grid.html",
         source_date="2024-09-20", date_accessed=ACCESSED),
    dict(plant="Cumberland Energy Center", unit="Unit 1 + Unit 2 (2x 2-on-1 CC)", state="VA",
         fuel="Natural Gas", v1_mw=0.0, v1_date="-", v2_mw=3000.0,
         v2_date="2033 (1,500 MW) + 2034 (1,500 MW)", change_type="add",
         reason="Largest single EIA miss. Dominion announced 7 May 2026: two 2-on-1 combined-cycle units, "
                "~3,000 MW, grid-connected utility plant for Dominion customers (PJM). County CUP approved "
                "3-1 in Oct 2026; still needs SCC CPCN (not yet filed Nov 2026) and DEQ air permit. "
                "Construction targeted 2029, operations 2033/2034. 1,500/1,500 split is an assumption "
                "(two units, '2033/2034'); medium confidence.",
         classification="grid-connected",
         source_url="https://www.dominionenergy.com/-/media/content/about/power-stations/cumberland-energy-center/pdfs/cumberland-energy-center-project-fact-sheet.pdf",
         source_date="2026-04-23", date_accessed=ACCESSED),
    dict(plant="Mt. Storm Combined Cycle Station", unit="Unit 1 + Unit 2 (2x 2-on-1 CC)",
         state="WV", fuel="Natural Gas", v1_mw=0.0, v1_date="-", v2_mw=2600.0,
         v2_date="2033 (1,300 MW) + 2034 (1,300 MW)", change_type="add",
         reason="Dominion announced 28 Jul 2026: 2,600 MW CC at the existing Mt. Storm coal site (coal stays "
                "online). Grid-connected; primarily serves Dominion VA customers, excess to PJM. Air-permit "
                "modification filed Jul 2026. 1,300/1,300 split follows trade-press unit dates 2033-34.",
         classification="grid-connected",
         source_url="https://governor.wv.gov/article/governor-morrisey-announces-26-gw-natural-gas-power-plant-grant-county-existing-coal",
         source_date="2026-07-28", date_accessed=ACCESSED),
    dict(plant="CPV Shay Energy Center", unit="3x ~687 MW CC (GE 7HA.03)", state="WV",
         fuel="Natural Gas", v1_mw=0.0, v1_date="-", v2_mw=2100.0, v2_date="2031",
         change_type="add",
         reason="CPV, ~2,100 MW carbon-capture-ready CC, construction 2027, COD 2031. Grid-connected: 9-mile "
                "500 kV line to FirstEnergy Flint Run; WV PSC siting certificate approved Apr 2024; 10-yr EQT "
                "gas-supply deal signed Aug 2026. In PJM queue as 'Flint Run 500 kV'. MW note: WV DEP air "
                "modelling protocol (Dec 2025) says 2,060 MW vs CPV's 2,100 MW — use 2,100 MW announced.",
         classification="grid-connected",
         source_url="https://cpv.com/our-fleet/cpv-shay-energy-center/",
         source_date="2026-11-14", date_accessed=ACCESSED),
    dict(plant="Rockport Energy Center (new CC)", unit="CC", state="IN", fuel="Natural Gas",
         v1_mw=0.0, v1_date="-", v2_mw=1520.0, v2_date="2030-06", change_type="add",
         reason="I&M/AEP new 1,520 MW combined cycle at the existing Rockport coal site (replaces retiring "
                "coal). CPCN filed 20 Jul 2026, decision expected early 2027; construction 2027, operational "
                "summer 2030. Grid-connected utility plant. Not the same as the retiring Rockport coal units.",
         classification="grid-connected",
         source_url="https://www.aep.com/news/stories/view/12100/",
         source_date="2026-07-20", date_accessed=ACCESSED),
    dict(plant="Expedition Generating Station", unit="2 CC trains", state="VA", fuel="Natural Gas",
         v1_mw=0.0, v1_date="-", v2_mw=1540.0, v2_date="2031-12", change_type="add",
         reason="Tenaska, 1,540 MW nominal summer, grid-connected via 1.8-mile 500 kV tie to Cunningham "
                "substation. CPCN filed 15 Jul 2026 (VA SCC Case PUR-2026-00102); earliest construction late "
                "2027; operations late 2031. Land-use approvals received; turbines secured; no offtake yet. "
                "PJM queue AH1-712 + AH1-723 (776 MW each) are the two halves of this one plant — do not "
                "double-count.",
         classification="grid-connected",
         source_url="https://www.scc.virginia.gov/docketsearch/DOCS/8%23g101!.PDF",
         source_date="2026-09-03", date_accessed=ACCESSED),
    dict(plant="Maidsville / Fort Martin (Mon Power & Potomac Edison)", unit="CC", state="WV",
         fuel="Natural Gas", v1_mw=0.0, v1_date="-", v2_mw=1200.0, v2_date="2031-12",
         change_type="add",
         reason="FirstEnergy, 1,200 MW CC, $2.48-2.5B, +70 MW solar. Site work from 2027, online late 2031; "
                "PSC filing Feb 2026, decision due by Mar 2027. Grid-connected utility plant. Demand risk "
                "flag: justified partly by a 1,012 MW data center with no signed power agreement (PSC testimony) "
                "— that is demand risk, not grid-connection risk.",
         classification="grid-connected",
         source_url="https://investors.firstenergycorp.com/investor-materials/news-releases/news-details/2026/Mon-Power-and-Potomac-Edison-Select-Maidsville-West-Virginia-Site-for-New-Natural-Gas-Power-Plant/default.aspx",
         source_date="2026-02-13", date_accessed=ACCESSED),
    dict(plant="Cooper CCGT (East Kentucky Power Cooperative)", unit="CC", state="KY",
         fuel="Natural Gas", v1_mw=0.0, v1_date="-", v2_mw=745.0, v2_date="2030-12",
         change_type="add",
         reason="EKPC, 745 MW CC (KY PSC figure; PJM queue MFO is 786 MW — use 745 MW), $1.37B. KY PSC granted "
                "CPCN 3 Jul 2025. Grid-connected. Separate coal-to-gas co-firing at Cooper Unit 2 / Spurlock "
                "(2029) is a conversion, not new MW — not counted.",
         classification="grid-connected",
         source_url="https://psc.ky.gov/agencies/psc/press/072025/0703_r01.pdf",
         source_date="2025-07-03", date_accessed=ACCESSED),
    dict(plant="Big Sandy (Kentucky Power / AEP, new CC)", unit="CC", state="KY", fuel="Natural Gas",
         v1_mw=0.0, v1_date="-", v2_mw=760.0, v2_date="2031-03", change_type="add",
         reason="Kentucky Power, 760 MW CC, planned in-service 31 Mar 2031; supersedes the earlier 450 MW CT "
                "plan. New CPCN case to be filed (old Case 2026-00103 withdrawn 9 Oct 2026, closed 29 Oct 2026). "
                "Grid-connected utility plant; tied to TeraWulf Muskie data-center agreement (TeraWulf to pay "
                "financing costs). Site assumed Big Sandy, KY per the prior plan — not confirmed in the new "
                "filing. Do not confuse with the existing 300 MW Big Sandy Peaker Plant in Kenova, WV "
                "(ownership change only, not new capacity).",
         classification="grid-connected",
         source_url="https://psc.ky.gov/order_vault/Orders_2026/202600103_10292026.pdf",
         source_date="2026-10-29", date_accessed=ACCESSED),
    dict(plant="Hunterstown uprate (LS Power)", unit="uprate", state="PA", fuel="Natural Gas",
         v1_mw=0.0, v1_date="-", v2_mw=455.0, v2_date="2029-07", change_type="add",
         reason="Uprate, not a new plant: existing 810 MW -> ~1,265 MW (+455 MW). First project accepted under "
                "PJM Expedited Interconnection Track, 8 Oct 2026; in service by 31 Jul 2029. Grid-connected.",
         classification="grid-connected",
         source_url="https://www.UtilityDive.com/news/engie-ls-power-pjm-expedited-interconnection-eit/832613/",
         source_date="2026-10-09", date_accessed=ACCESSED),
    dict(plant="Talen Montour CT", unit="2x ~655 MW CCCT", state="PA", fuel="Natural Gas",
         v1_mw=0.0, v1_date="-", v2_mw=1310.0, v2_date="2031-12", change_type="add",
         reason="Talen, ~1,310 MW new CCCT at the existing Montour site, construction from 2028, COD 2031. "
                "PA DEP plan-approval application submitted Jun 2026; PJM queue request in the Apr 2026 "
                "reformed cycle; grid-connected via the existing Montour interconnection. EARLY-STAGE FLAG: "
                "air permit pending, no CPCN/FID — lowest-confidence addition in v2; include-or-exclude is a "
                "judgement call. Distinct from the Columbia Co. queue entries (AH1-675/688/689) and from the "
                "2023 Montour coal-to-gas conversion.",
         classification="grid-connected",
         source_url="https://www.pa.gov/agencies/dep/dep-regions/northcentral-regional-office/talen-montour-ct-project",
         source_date="2026-06-09", date_accessed=ACCESSED),
    dict(plant="Keystone Generating Station", unit="1 + 2", state="PA", fuel="Coal",
         v1_mw=0.0, v1_date="-", v2_mw=1872.0, v2_date="2032-12", change_type="add",
         reason="ADD retirement, Dec 2032. 2021 plan to cease coal 31 Dec 2028 reversed; PA DEP consent decree "
                "filed 20 Apr 2026 (Indiana County Court of Common Pleas No. 2169-CD-2025) allows operation "
                "through 2032 subject to wastewater upgrades by 2028. GEM lists planned retirement 2032 for "
                "both units. MW is EIA nameplate (2x 936 MW; net ~1,711 MW). FLAG: decree-expiry planning "
                "assumption, NOT a filed PJM deactivation — no deactivation notice has been filed and the "
                "plant could be extended again. If extended, this retirement moves out.",
         classification="grid-connected",
         source_url="https://www.pa.gov/content/dam/copapwp-pagov/en/governor/documents/motion%20to%20enter%20cd-as%20filed.pdf",
         source_date="2026-04-20", date_accessed=ACCESSED),
    dict(plant="Conemaugh Generating Station", unit="1 + 2", state="PA", fuel="Coal",
         v1_mw=0.0, v1_date="-", v2_mw=1951.0, v2_date="2032-12", change_type="add",
         reason="Same owner, history and 20 Apr 2026 consent decree as Keystone; operation through 2032. "
                "GEM lists planned retirement 2032. MW is EIA nameplate (2x 975.5 MW; net ~1,711 MW). "
                "Same decree-expiry flag as Keystone.",
         classification="grid-connected",
         source_url="https://www.pa.gov/content/dam/copapwp-pagov/en/governor/documents/motion%20to%20enter%20cd-as%20filed.pdf",
         source_date="2026-04-20", date_accessed=ACCESSED),
    dict(plant="Powerton Generating Station", unit="5 + 6", state="IL", fuel="Coal",
         v1_mw=0.0, v1_date="-", v2_mw=1785.6, v2_date="2031-05", change_type="add",
         reason="ADD retirement, May 2031. NRG/Midwest Generation filed PJM deactivation notice 30 Jun 2026 "
                "for 1 Jan 2030 under CEJA; PJM requested continued operation through 31 May 2031; notice "
                "withdrawn 2 Jul 2026. MW is EIA nameplate (2x 892.8 MW; ICAP 2x 769 MW = 1,538 MW). FLAG: "
                "31 May 2031 is the end of PJM's requested reliability extension, not a firm retirement date — "
                "PJM will reassess before each delivery year from 2031/32; units could run longer. Conversely "
                "the underlying CEJA deadline is 1 Jan 2030, so 2031 is a 'no earlier than' date.",
         classification="grid-connected",
         source_url="http://www.pjm.com/-/media/DotCom/planning/gen-retire/deactivation-notices/mwg-deactivation-letter.pdf",
         source_date="2026-06-30", date_accessed=ACCESSED),
    dict(plant="Illinois Generating Assets (NRG)", unit="Aurora CT1-10 + Rockford + Univ. Park N/S",
         state="IL", fuel="Natural Gas", v1_mw=0.0, v1_date="-", v2_mw=2649.6,
         v2_date="2031-05", change_type="add",
         reason="ADD retirement, May 2031 (CEJA block). Same 30 Jun 2026 deactivation / 2 Jul 2026 withdrawal "
                "sequence as Powerton; PJM requested operation through 31 May 2031. MW is EIA nameplate: "
                "Aurora 1,086.2 (4x 180.8 + 6x 60.5), Rockford 484.0 (2x 158 + 168), University Park North "
                "726.0 (12x 60.5), University Park South 353.4 (6x 58.9). PJM's letter totals the group at "
                "~2,376 MW ICAP. Same 2031-floor flag as Powerton. Individual units are <250 MW but the "
                "group is 2,650 MW.",
         classification="grid-connected",
         source_url="http://www.pjm.com/-/media/DotCom/planning/gen-retire/deactivation-notices/il-assets-deactivation-letter.pdf",
         source_date="2026-06-30", date_accessed=ACCESSED),
    dict(plant="Fisk Street + Waukegan", unit="Fisk CT31-34 + Waukegan CT31-32", state="IL",
         fuel="Oil", v1_mw=0.0, v1_date="-", v2_mw=372.0, v2_date="2031-05", change_type="add",
         reason="ADD retirement, May 2031 (CEJA block, filed with Powerton in the same 30 Jun 2026 Midwest "
                "Generation notice; same PJM extension to 31 May 2031). MW is EIA nameplate: Fisk Street "
                "260.0 (8x 32.5 MW, DFO), Waukegan 112.0 (4x 28.0 MW, DFO). PJM letter ICAPs: Fisk 170.7 MW, "
                "Waukegan 100.8 MW. Same 2031-floor flag as Powerton.",
         classification="grid-connected",
         source_url="http://www.pjm.com/-/media/DotCom/planning/gen-retire/deactivation-notices/mwg-deactivation-letter.pdf",
         source_date="2026-06-30", date_accessed=ACCESSED),
    dict(plant="Zion Energy Center", unit="CTG1 + CTG2 + CTG3", state="IL", fuel="Natural Gas",
         v1_mw=0.0, v1_date="-", v2_mw=596.7, v2_date="2031-05", change_type="add",
         reason="ADD retirement, May 2031 (CEJA block). Constellation notified PJM 22 Jun 2026 of intent to "
                "deactivate on or before 31 Dec 2029 under CEJA; PJM requested continued operation at least "
                "through 29/31 May 2031; notice withdrawn 2 Jul 2026. MW verified in EIA-860M Operating "
                "sheet: 3x 198.9 MW nameplate (net summer 161/162/155 MW). Same 2031-floor flag as Powerton.",
         classification="grid-connected",
         source_url="http://www.pjm.com/-/media/DotCom/planning/gen-retire/deactivation-notices/zion-ct1-ct2-ct3-withdrawal.pdf",
         source_date="2026-07-02", date_accessed=ACCESSED),
    dict(plant="West Lorain", unit="1A + 1B", state="OH", fuel="Oil",
         v1_mw=0.0, v1_date="-", v2_mw=130.6, v2_date="2030-06", change_type="add",
         reason="ADD retirement, 1 Jun 2030. Owner Vermillion Power (Lotus Infrastructure). Deactivation "
                "notice Jun 2026; PJM response 28 Aug 2026 found no reliability violations; may deactivate "
                "1 Jun 2030. MW is EIA nameplate (2x 65.3 MW, DFO GTs; ICAP 50 + 51 MW). Units 2-6 (gas) "
                "are NOT retiring.",
         classification="grid-connected",
         source_url="https://www.pjm.com/-/media/DotCom/planning/gen-retire/deactivation-notices/west-lorain-pjm-response.pdf",
         source_date="2026-08-28", date_accessed=ACCESSED),
    dict(plant="Forked River", unit="1 + 2", state="NJ", fuel="Natural Gas",
         v1_mw=0.0, v1_date="-", v2_mw=76.8, v2_date="2027-06", change_type="add",
         reason="ADD retirement, 1 Jun 2027. Deactivation notices Feb 2025 (Unit 2: NJ air-permit grounds, "
                "originally effective 1 Jun 2026, rescinded 22 Jul 2025 and replaced with 1 Jun 2027; "
                "Unit 1: NJ carbon rules, 1 Jun 2027). PJM response 30 May 2025 cleared both (no reliability "
                "violations). MW is EIA nameplate (2x 38.4 MW, NG GTs; ICAP 34 + 31 MW).",
         classification="grid-connected",
         source_url="https://www.PJM.com/-/media/DotCom/planning/gen-retire/deactivation-notices/forked-river-unit-1-unit-2-pjm-response.pdf",
         source_date="2025-05-30", date_accessed=ACCESSED),
    dict(plant="Miami Fort", unit="7 + 8", state="OH", fuel="Coal -> Natural Gas",
         v1_mw=1114.8, v1_date="operating coal", v2_mw=1114.8, v2_date="2028",
         change_type="retime",
         reason="Fuel switch, not a net retirement: Vistra announced late 2025 it will convert Miami Fort "
                "7-8 to natural gas (2025 Sustainability Report; proxy 18 Mar 2026: 'intention to convert "
                "our Miami Fort coal plant to a natural gas plant in the coming years'); GEM lists announced "
                "coal-to-gas conversion in 2028. Reverses the Sep 2020 plan to retire by end-2027. Net MW "
                "effect ~zero (coal -1,114.8 / gas +1,114.8 in 2028); MW is EIA nameplate (557.1 + 557.7). "
                "Medium confidence on the 2028 date.",
         classification="grid-connected",
         source_url="https://www.ohiohouse.gov/members/mike-odioso/news/odioso-applauds-plan-to-extend-operations-at-miami-fort-power-plant-140600",
         source_date="2026-11-14", date_accessed=ACCESSED),
]

# ---------------------------------------------------------------- new rows
# (plant_name, generator_id, state, fuel, mw, year, month, type, status, source_sheet)
NEW_ROWS = [
    # Crane restart
    ("Crane Clean Energy Center", "1", "PA", "Nuclear", 835.0, 2027, 7, "addition",
     "Manual addition — restart, NRC approval pending", "Manual v2"),
    # Cumberland 2 units
    ("Cumberland Energy Center", "U1", "VA", "Natural Gas", 1500.0, 2033, 12, "addition",
     "Manual addition — announced, CUP approved, SCC/DEQ pending", "Manual v2"),
    ("Cumberland Energy Center", "U2", "VA", "Natural Gas", 1500.0, 2034, 12, "addition",
     "Manual addition — announced, CUP approved, SCC/DEQ pending", "Manual v2"),
    # Mt Storm 2 units
    ("Mt. Storm Combined Cycle Station", "U1", "WV", "Natural Gas", 1300.0, 2033, 12, "addition",
     "Manual addition — announced, air-permit modification filed Jul 2026", "Manual v2"),
    ("Mt. Storm Combined Cycle Station", "U2", "WV", "Natural Gas", 1300.0, 2034, 12, "addition",
     "Manual addition — announced, air-permit modification filed Jul 2026", "Manual v2"),
    # Shay
    ("CPV Shay Energy Center", "CC", "WV", "Natural Gas", 2100.0, 2031, 12, "addition",
     "Manual addition — PSC siting certificate approved Apr 2024", "Manual v2"),
    # Rockport CC
    ("Rockport Energy Center", "CC", "IN", "Natural Gas", 1520.0, 2030, 6, "addition",
     "Manual addition — CPCN filed Jul 2026", "Manual v2"),
    # Expedition
    ("Expedition Generating Station", "CC", "VA", "Natural Gas", 1540.0, 2031, 12, "addition",
     "Manual addition — CPCN filed Jul 2026", "Manual v2"),
    # Maidsville
    ("Maidsville / Fort Martin", "CC", "WV", "Natural Gas", 1200.0, 2031, 12, "addition",
     "Manual addition — PSC filing Feb 2026, decision due Mar 2027", "Manual v2"),
    # Cooper
    ("Cooper CCGT", "CC", "KY", "Natural Gas", 745.0, 2030, 12, "addition",
     "Manual addition — KY PSC CPCN granted Jul 2025", "Manual v2"),
    # Big Sandy
    ("Big Sandy (new CC)", "CC", "KY", "Natural Gas", 760.0, 2031, 3, "addition",
     "Manual addition — CPCN case to be filed", "Manual v2"),
    # Hunterstown uprate
    ("Hunterstown", "UPRATE", "PA", "Natural Gas", 455.0, 2029, 7, "addition",
     "Manual addition — uprate, PJM Expedited Interconnection Track", "Manual v2"),
    # Montour CT
    ("Talen Montour CT", "CC", "PA", "Natural Gas", 1310.0, 2031, 12, "addition",
     "Manual addition — early-stage, PA DEP plan approval applied Jun 2026", "Manual v2"),
    # Keystone / Conemaugh retirements
    ("Keystone", "1", "PA", "Coal", 936.0, 2032, 12, "retirement",
     "Manual addition — consent-decree expiry planning assumption", "Manual v2"),
    ("Keystone", "2", "PA", "Coal", 936.0, 2032, 12, "retirement",
     "Manual addition — consent-decree expiry planning assumption", "Manual v2"),
    ("Conemaugh", "1", "PA", "Coal", 975.5, 2032, 12, "retirement",
     "Manual addition — consent-decree expiry planning assumption", "Manual v2"),
    ("Conemaugh", "2", "PA", "Coal", 975.5, 2032, 12, "retirement",
     "Manual addition — consent-decree expiry planning assumption", "Manual v2"),
    # Powerton
    ("Powerton", "5", "IL", "Coal", 892.8, 2031, 5, "retirement",
     "Manual addition — CEJA, PJM extension to 31 May 2031", "Manual v2"),
    ("Powerton", "6", "IL", "Coal", 892.8, 2031, 5, "retirement",
     "Manual addition — CEJA, PJM extension to 31 May 2031", "Manual v2"),
    # Illinois Generating Assets (gas CTs)
    ("Aurora", "CTG1-10", "IL", "Natural Gas", 1086.2, 2031, 5, "retirement",
     "Manual addition — CEJA, PJM extension to 31 May 2031", "Manual v2"),
    ("Rockford (NRG)", "CT", "IL", "Natural Gas", 484.0, 2031, 5, "retirement",
     "Manual addition — CEJA, PJM extension to 31 May 2031", "Manual v2"),
    ("University Park North", "CT1-12", "IL", "Natural Gas", 726.0, 2031, 5, "retirement",
     "Manual addition — CEJA, PJM extension to 31 May 2031", "Manual v2"),
    ("University Park South", "CT1-6", "IL", "Natural Gas", 353.4, 2031, 5, "retirement",
     "Manual addition — CEJA, PJM extension to 31 May 2031", "Manual v2"),
    # Fisk / Waukegan (oil)
    ("Fisk Street", "CT31-34", "IL", "Oil", 260.0, 2031, 5, "retirement",
     "Manual addition — CEJA, PJM extension to 31 May 2031", "Manual v2"),
    ("Waukegan", "CT31-32", "IL", "Oil", 112.0, 2031, 5, "retirement",
     "Manual addition — CEJA, PJM extension to 31 May 2031", "Manual v2"),
    # Zion
    ("Zion Energy Center", "CTG1-3", "IL", "Natural Gas", 596.7, 2031, 5, "retirement",
     "Manual addition — CEJA, PJM extension to 31 May 2031", "Manual v2"),
    # West Lorain / Forked River
    ("West Lorain", "1A-1B", "OH", "Oil", 130.6, 2030, 6, "retirement",
     "Manual addition — PJM cleared, deactivates 1 Jun 2030", "Manual v2"),
    ("Forked River", "1", "NJ", "Natural Gas", 38.4, 2027, 6, "retirement",
     "Manual addition — PJM cleared, deactivates 1 Jun 2027", "Manual v2"),
    ("Forked River", "2", "NJ", "Natural Gas", 38.4, 2027, 6, "retirement",
     "Manual addition — PJM cleared, deactivates 1 Jun 2027", "Manual v2"),
    # Miami Fort fuel switch: coal out + gas in, 2028
    ("Miami Fort", "7", "OH", "Coal", 557.1, 2028, 12, "retirement",
     "Manual addition — coal-to-gas conversion, fuel switch", "Manual v2"),
    ("Miami Fort", "8", "OH", "Coal", 557.7, 2028, 12, "retirement",
     "Manual addition — coal-to-gas conversion, fuel switch", "Manual v2"),
    ("Miami Fort", "7", "OH", "Natural Gas", 557.1, 2028, 12, "addition",
     "Manual addition — coal-to-gas conversion, fuel switch", "Manual v2"),
    ("Miami Fort", "8", "OH", "Natural Gas", 557.7, 2028, 12, "addition",
     "Manual addition — coal-to-gas conversion, fuel switch", "Manual v2"),
    # Steward Creek Phase 2 (split from the v1 1,200 MW Phase 1 row)
    ("Steward Creek Solar Phase 2", "SC2", "IL", "Solar", 600.0, 2030, 12, "addition",
     "Manual addition — Phase 2 split out of v1 1,200 MW Phase 1 row", "Manual v2"),
]

# Edits to existing v1 rows: (plant_name substring, generator_id, new_mw or None,
# new effective (year, month) or None, new status or None, note)
EDITS = [
    # Homer City: exclude all 14 units
    ("Homer City Generating Station", None, None, None, None, "BTM-exclude"),
    # Bellflower: remove
    ("Bellflower Solar (VA)", "BELLF", None, None, None, "remove"),
    # Rocky Run: 300 -> 290 MW, Jan 2028 -> Dec 2031
    ("Rocky Run Solar", "ROCKY", 290.0, (2031, 12), None, "retime+MW"),
    # Steward Creek Phase 1: 1200 -> 600 MW (Phase 2 split into a new row)
    ("Steward Creek Solar Phase 1", "SC1", 600.0, None, None, "split"),
    # CVOW: Jan 2027 -> Dec 2027
    ("Coastal Virginia Offshore Wind (CVOW) Commercial Project", "CVOWC", None, (2027, 12), None, "retime"),
    # Sycamore: 964 -> 918 MW, status P -> CPCN pending
    ("Sycamore Riverside Energy, LLC", "SYRVS", 918.0, None,
     "CPCN pending (IURC Cause No. 46389, filed Apr 2026)", "MW+status"),
    # Wolf Summit: HCCA1 207.4 -> 228.5 MW (plant total 578.9 -> 600), status L -> U
    ("Wolf Summit Energy", "HCCA1", 228.5, None, "(U) Under construction, less than or equal to 50 percent complete", "MW+status"),
    ("Wolf Summit Energy", "HCCT1", None, None, "(U) Under construction, less than or equal to 50 percent complete", "status"),
    # Trumbull: STG 360 -> 332.6 MW (plant total 977.4 -> 950), Apr 2026 -> Jan 2026
    ("Trumbull Energy Center", "STG", 332.6, (2026, 1), None, "MW+date"),
    ("Trumbull Energy Center", "GT11", None, (2026, 1), None, "date"),
    ("Trumbull Energy Center", "GT12", None, (2026, 1), None, "date"),
    # Chesterfield: 4x250 -> 4x236 MW, status L -> approved
    ("Chesterfield", "CERC1", 236.0, None, "Approved — SCC CPCN Nov 2025, DEQ air permit Dec 2025; under litigation", "MW+status"),
    ("Chesterfield", "CERC2", 236.0, None, "Approved — SCC CPCN Nov 2025, DEQ air permit Dec 2025; under litigation", "MW+status"),
    ("Chesterfield", "CERC3", 236.0, None, "Approved — SCC CPCN Nov 2025, DEQ air permit Dec 2025; under litigation", "MW+status"),
    ("Chesterfield", "CERC4", 236.0, None, "Approved — SCC CPCN Nov 2025, DEQ air permit Dec 2025; under litigation", "MW+status"),
    # Illinois Generation: status T -> U
    ("Illinois Generation LLC", "HPW", None, None, "(U) Under construction, less than or equal to 50 percent complete", "status"),
    # Brandon Shores: Jun 2029 -> May 2031
    ("Brandon Shores", "1", None, (2031, 5), None, "retime"),
    ("Brandon Shores", "2", None, (2031, 5), None, "retime"),
    # Wagner: Jun 2029 -> May 2031
    ("Herbert A Wagner", "3", None, (2031, 5), None, "retime"),
    ("Herbert A Wagner", "4", None, (2031, 5), None, "retime"),
]


def main():
    plants = pd.read_csv(BASE / "pjm_capacity_plants.csv")
    stack_v1 = pd.read_csv(BASE / "pjm_capacity_stack.csv")
    chg_v1 = pd.read_csv(BASE / "pjm_capacity_changelog.csv")
    with open(BASE / "summary.json") as f:
        s1 = json.load(f)

    # --- sanity check: v1 stack == anchor + cumulative v1 changelog
    anchor = stack_v1[stack_v1["year"] == ANCHOR_YEAR].set_index("fuel")["mw"].to_dict()
    running = {f: float(anchor[f]) for f in FUELS}
    for y in range(2026, 2037):
        net = chg_v1[chg_v1["year"] == y]
        for f in FUELS:
            running[f] += float(net.loc[net["fuel"] == f, "net_mw"].iloc[0])
        v1row = stack_v1[(stack_v1["year"] == y)]
        for f in FUELS:
            v = float(v1row.loc[v1row["fuel"] == f, "mw"].iloc[0])
            assert abs(v - running[f]) < 0.05, (y, f, v, running[f])
    print("v1 stack reproduces from anchor + v1 changelog: OK")

    # --- plants v2: copy v1, add v2 columns
    p2 = plants.copy()
    p2["v2_mw_nameplate"] = p2["mw_nameplate"]
    p2["v2_effective_date"] = p2["effective_date"]
    p2["v2_status"] = p2["status"]
    p2["v2_type"] = p2["type"]
    p2["manual_change"] = False
    p2["manual_change_note"] = ""

    def find_rows(substr, gen):
        m = p2["plant_name"].str.contains(substr, case=False, na=False, regex=False)
        if gen is not None:
            m = m & (p2["generator_id"].astype(str) == str(gen))
        return p2.index[m]

    # Homer City exclusion + Bellflower removal (whole-plant, by substring)
    for substr, note in [("Homer City Generating Station", "BTM-exclude: data-center campus, grid MW 0 per user rule"),
                         ("Bellflower Solar (VA)", "remove: project terminated, CUP revoked 7 Oct 2026")]:
        idx = find_rows(substr, None)
        assert len(idx) > 0, substr
        p2.loc[idx, "v2_type"] = "excluded"
        p2.loc[idx, "v2_mw_nameplate"] = 0.0
        p2.loc[idx, "manual_change"] = True
        p2.loc[idx, "manual_change_note"] = note
        print(f"  excluded {len(idx)} rows: {substr}")

    for substr, gen, new_mw, new_eff, new_status, note in EDITS:
        if substr in ("Homer City Generating Station", "Bellflower Solar (VA)"):
            continue
        idx = find_rows(substr, gen)
        assert len(idx) == 1, (substr, gen, len(idx))
        i = idx[0]
        if new_mw is not None:
            p2.loc[i, "v2_mw_nameplate"] = new_mw
        if new_eff is not None:
            y, mo = new_eff
            p2.loc[i, "v2_effective_date"] = f"{y:04d}-{mo:02d}"
        if new_status is not None:
            p2.loc[i, "v2_status"] = new_status
        p2.loc[i, "manual_change"] = True
        p2.loc[i, "manual_change_note"] = note

    # New rows
    new_df = pd.DataFrame([{
        "plant_name": pn, "plant_id": np.nan, "generator_id": gid, "state": st,
        "county": "", "balancing_authority": "PJM", "fuel": fu,
        "energy_source_code": "", "prime_mover_code": "", "technology": "",
        "mw_nameplate": mw, "mw_net_summer": np.nan, "type": typ,
        "status": status, "retirement_status": "",
        "source_sheet": src, "original_year": yr, "original_month": mo,
        "original_date": f"{yr:04d}-{mo:02d}", "effective_year": yr,
        "effective_month": mo, "effective_date": f"{yr:04d}-{mo:02d}",
        "rmr_override": False,
        "v2_mw_nameplate": mw, "v2_effective_date": f"{yr:04d}-{mo:02d}",
        "v2_status": status, "v2_type": typ, "manual_change": True,
        "manual_change_note": "manual addition (v2)",
    } for (pn, gid, st, fu, mw, yr, mo, typ, status, src) in NEW_ROWS])
    p2 = pd.concat([p2, new_df], ignore_index=True)
    print(f"  plants v2 rows: {len(p2)} (v1 {len(plants)} + {len(new_df)} new)")

    # --- changelog v2 from plants v2 (effective years 2026-2036, non-excluded)
    act = p2[p2["v2_type"].isin(["addition", "retirement"])].copy()
    act["v2_year"] = act["v2_effective_date"].str.slice(0, 4).astype(int)
    act = act[(act["v2_year"] >= 2026) & (act["v2_year"] <= 2036)]
    rows = []
    for y in range(2026, 2037):
        for f in FUELS:
            sub = act[(act["v2_year"] == y) & (act["fuel"] == f)]
            adds = sub[sub["v2_type"] == "addition"]
            rets = sub[sub["v2_type"] == "retirement"]
            rows.append({
                "year": y, "fuel": f,
                "additions_mw": round(float(adds["v2_mw_nameplate"].sum()), 1),
                "additions_count": int(len(adds)),
                "retirements_mw": round(float(rets["v2_mw_nameplate"].sum()), 1),
                "retirements_count": int(len(rets)),
                "net_mw": round(float(adds["v2_mw_nameplate"].sum() - rets["v2_mw_nameplate"].sum()), 1),
            })
    chg2 = pd.DataFrame(rows)

    # --- stack v2: trailing unchanged, forward = anchor + cumulative v2 changelog
    # (mirrors the v1 CSV layout, including a Total row per year)
    stack_rows = []
    for y in range(2016, 2026):
        for _, r in stack_v1[(stack_v1["year"] == y)].iterrows():
            stack_rows.append({"year": int(r["year"]), "fuel": r["fuel"], "mw": float(r["mw"]),
                               "period": "trailing", "anchor_year": bool(r["anchor_year"]),
                               "source_note": r["source_note"]})
    running = {f: float(anchor[f]) for f in FUELS}
    for y in range(2026, 2037):
        net = chg2[chg2["year"] == y]
        for f in FUELS:
            running[f] += float(net.loc[net["fuel"] == f, "net_mw"].iloc[0])
        for f in FUELS:
            stack_rows.append({
                "year": y, "fuel": f, "mw": round(running[f], 1), "period": "forward",
                "anchor_year": False,
                "source_note": "SOM Dec-31-2025 anchor + v2 changelog (EIA-860M + manual corrections; "
                               "Homer City BTM excluded; RMR coal delay to Jan 2029)",
            })
        stack_rows.append({
            "year": y, "fuel": "Total", "mw": round(sum(running.values()), 1),
            "period": "forward", "anchor_year": False,
            "source_note": "SOM Dec-31-2025 anchor + v2 changelog (EIA-860M + manual corrections; "
                           "Homer City BTM excluded; RMR coal delay to Jan 2029)",
        })
    stack2 = pd.DataFrame(stack_rows)
    # totals check (Total rows only)
    tot2 = stack2[stack2["fuel"] == "Total"].set_index("year")["mw"].round(1).to_dict()
    tot1 = stack_v1[stack_v1["fuel"] == "Total"].set_index("year")["mw"].round(1).to_dict()
    print("  yearly totals v1 -> v2:")
    for y in range(2025, 2037):
        print(f"    {y}: {tot1[y]:,.1f} -> {tot2[y]:,.1f}  ({tot2[y]-tot1[y]:+,.1f})")

    # --- write outputs
    adj = pd.DataFrame(ADJUSTMENTS)[[
        "plant", "unit", "state", "fuel", "v1_mw", "v1_date", "v2_mw", "v2_date",
        "change_type", "reason", "classification", "source_url", "source_date",
        "date_accessed"]]
    adj.to_csv(BASE / "manual_adjustments.csv", index=False)
    p2.to_csv(BASE / "pjm_capacity_plants_v2.csv", index=False)
    stack2.to_csv(BASE / "pjm_capacity_stack_v2.csv", index=False)
    chg2.to_csv(BASE / "pjm_capacity_changelog_v2.csv", index=False)

    def agg(df, col):
        return {f: round(float(df[df["fuel"] == f][col].sum()), 1) for f in FUELS}
    v1_add = agg(chg_v1, "additions_mw"); v2_add = agg(chg2, "additions_mw")
    v1_ret = agg(chg_v1, "retirements_mw"); v2_ret = agg(chg2, "retirements_mw")
    summary = {
        "version": "v2",
        "built": "2026-11-14",
        "anchor_unchanged_mw": 202424.8,
        "anchor_source": s1["anchor"]["source"],
        "v1_forward_2026_2036": {
            "additions_mw": round(float(chg_v1["additions_mw"].sum()), 1),
            "additions_count": int(chg_v1["additions_count"].sum()),
            "retirements_mw": round(float(chg_v1["retirements_mw"].sum()), 1),
            "retirements_count": int(chg_v1["retirements_count"].sum()),
            "net_mw": round(float(chg_v1["net_mw"].sum()), 1),
            "additions_by_fuel_mw": v1_add, "retirements_by_fuel_mw": v1_ret,
        },
        "v2_forward_2026_2036": {
            "additions_mw": round(float(chg2["additions_mw"].sum()), 1),
            "additions_count": int(chg2["additions_count"].sum()),
            "retirements_mw": round(float(chg2["retirements_mw"].sum()), 1),
            "retirements_count": int(chg2["retirements_count"].sum()),
            "net_mw": round(float(chg2["net_mw"].sum()), 1),
            "additions_by_fuel_mw": v2_add, "retirements_by_fuel_mw": v2_ret,
        },
        "delta_v2_minus_v1_mw": {
            "additions": round(float(chg2["additions_mw"].sum() - chg_v1["additions_mw"].sum()), 1),
            "retirements": round(float(chg2["retirements_mw"].sum() - chg_v1["retirements_mw"].sum()), 1),
            "net": round(float(chg2["net_mw"].sum() - chg_v1["net_mw"].sum()), 1),
            "by_fuel_net_mw": {f: round(v2_add[f] - v2_ret[f] - (v1_add[f] - v1_ret[f]), 1) for f in FUELS},
        },
        "yearly_totals_mw": {"v1": {str(k): v for k, v in tot1.items()},
                             "v2": {str(k): v for k, v in tot2.items()}},
        "btm_excluded_mw": 4396.0,
        "btm_excluded": [{"plant": "Homer City Generating Station", "mw": 4396.0,
                          "note": "Full 4,396 MW excluded, grid MW 0 per user rule. "
                                  "Alternative surplus-export reading (~700-800 MW) flagged, not counted."}],
        "manual_adjustments_count": len(ADJUSTMENTS),
        "largest_manual_changes_mw": [
            {"plant": "Homer City Generating Station", "change": "BTM-exclude", "mw": -4396.0},
            {"plant": "Keystone + Conemaugh retirements 2032", "change": "add retirement", "mw": 3823.0},
            {"plant": "Cumberland Energy Center", "change": "add", "mw": 3000.0},
            {"plant": "Illinois Generating Assets (CEJA gas CTs) retirement 2031", "change": "add retirement", "mw": 2649.6},
            {"plant": "Mt. Storm Combined Cycle Station", "change": "add", "mw": 2600.0},
            {"plant": "CPV Shay Energy Center", "change": "add", "mw": 2100.0},
            {"plant": "Powerton 5-6 retirement 2031", "change": "add retirement", "mw": 1785.6},
            {"plant": "Expedition Generating Station", "change": "add", "mw": 1540.0},
            {"plant": "Rockport Energy Center (new CC)", "change": "add", "mw": 1520.0},
            {"plant": "Brandon Shores + Wagner retime 2029->2031", "change": "retime", "mw": 2143.9},
            {"plant": "Talen Montour CT", "change": "add", "mw": 1310.0},
            {"plant": "Maidsville / Fort Martin", "change": "add", "mw": 1200.0},
            {"plant": "Miami Fort fuel switch (coal->gas, 2028)", "change": "retime", "mw": 1114.8},
            {"plant": "Crane Clean Energy Center restart", "change": "add", "mw": 835.0},
            {"plant": "Bellflower Solar", "change": "remove", "mw": -600.0},
        ],
        "not_added_flagged_candidates_mw": {
            "Constellation-Google nuclear uprates (PJM share unknown)": 890.0,
            "Vistra-Meta nuclear uprates (Perry/Davis-Besse/Beaver Valley, per-unit split unpublished)": 433.0,
            "Sammis-South Canton (queue-only, no developer)": 1300.0,
            "Shippingport (2.7-3.6 GW claimed, BTM-majority, MW uncertain)": None,
            "Appalachian Power ~3 GW (locations unannounced)": 3000.0,
            "Homer City surplus-export alternative (if adopted instead of 0)": "700-800",
        },
        "rmr_override_preserved": s1["rmr_override"],
        "files": {
            "manual_adjustments": "manual_adjustments.csv",
            "plants_v2": "pjm_capacity_plants_v2.csv",
            "stack_v2": "pjm_capacity_stack_v2.csv",
            "changelog_v2": "pjm_capacity_changelog_v2.csv",
            "summary_v2": "summary_v2.json",
            "research_log": "research_log.md",
            "readme_v2": "README_v2.md",
            "charts": ["01_stacked_area_v2.png", "02_net_change_forward_v2.png"],
        },
    }
    with open(BASE / "summary_v2.json", "w") as f:
        json.dump(summary, f, indent=2)
    print("  wrote manual_adjustments.csv, pjm_capacity_plants_v2.csv, "
          "pjm_capacity_stack_v2.csv, pjm_capacity_changelog_v2.csv, summary_v2.json")
    return stack2, chg2


def make_charts(stack2, chg2):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    wide = stack2.pivot(index="year", columns="fuel", values="mw").reset_index()
    years = wide["year"].values
    fig, ax = plt.subplots(figsize=(12, 6.5))
    bottom = np.zeros(len(years))
    for f in STACK_ORDER:
        vals = wide[f].values / 1000.0
        ax.fill_between(years, bottom, bottom + vals, label=f, color=FUEL_COLORS[f], alpha=0.9)
        bottom += vals
    ax.axvline(2025.9, color="black", linestyle="--", linewidth=1.5)
    ax.text(2025.95, bottom.max() * 0.97, "Today (Nov 2026)\nanchor Dec 31, 2025",
            fontsize=9, va="top")
    ax.set_xlim(2016, 2036)
    ax.set_ylabel("Installed capacity (GW)")
    ax.set_xlabel("Year (Dec 31 position; 2026-2036 = anchor + v2 changelog)")
    ax.set_title("PJM generation capacity stack by fuel, 2016-2036 — v2\n"
                 "SOM anchor + EIA-860M changelog + manual corrections "
                 "(Homer City BTM excluded)", fontsize=11)
    ax.legend(ncol=2, fontsize=9, loc="upper left")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(BASE / "01_stacked_area_v2.png", dpi=150)
    plt.close(fig)

    fwd = chg2[chg2["year"] >= 2026]
    piv = fwd.pivot(index="year", columns="fuel", values="net_mw") / 1000.0
    piv = piv.reindex(columns=STACK_ORDER).fillna(0.0)
    fig, ax = plt.subplots(figsize=(12, 6))
    bottom = np.zeros(len(piv))
    top = np.zeros(len(piv))
    for f in STACK_ORDER:
        v = piv[f].values
        pos = np.where(v > 0, v, 0)
        neg = np.where(v < 0, v, 0)
        ax.bar(piv.index, pos, bottom=top, label=f, color=FUEL_COLORS[f], width=0.75)
        top += pos
        ax.bar(piv.index, neg, bottom=bottom, color=FUEL_COLORS[f], width=0.75)
        bottom += neg
    ax.axhline(0, color="black", linewidth=0.8)
    pos_tot = float(piv.clip(lower=0).sum(axis=1).max())
    neg_tot = float(piv.clip(upper=0).sum(axis=1).min())
    ax.set_ylim(neg_tot * 1.12 - 0.2, pos_tot * 1.08 + 0.3)
    ax.set_ylabel("Net capacity change (GW / year)")
    ax.set_xlabel("Year")
    ax.set_title("PJM annual net capacity change by fuel, forward 2026-2036 — v2\n"
                 "(EIA-860M + manual additions/retirements, Homer City BTM excluded)",
                 fontsize=11)
    ax.legend(ncol=2, fontsize=9, loc="upper right")
    ax.grid(True, alpha=0.3, axis="y")
    fig.tight_layout()
    fig.savefig(BASE / "02_net_change_forward_v2.png", dpi=150)
    plt.close(fig)
    print("  charts written")


if __name__ == "__main__":
    s2, c2 = main()
    make_charts(s2, c2)
