# Khriss Analytics

Private working repo for PJM power-market analysis: winter weather
distributions and the new-builds-and-retirements (NBR) capacity stack.
Built 2026-11-14. Private for now; may be made public later to host
results on GitHub Pages.

## Layout

- `weather-analysis/` — PJM winter temperature work
  - NOAA GHCN-Daily, 7 stations (Chicago O'Hare, Pittsburgh, Columbus,
    Philadelphia, Baltimore/Washington, Washington Reagan, Richmond),
    winters 1995-96 through 2024-25 (30 winters, 18,956 station-days).
  - `fetch_and_analyze.py` — temperature distribution (overall mean
    35.3°F; HDD65 averages 2,682 per station per winter).
  - `forward-cone/` — 14-day forward temperature cone conditioned on
    starting temperature (`forward_cone.py`); cone width saturates at
    ~27-29°F by day 5-7, ~80% mean reversion by day 14.
  - `load-weighted/` — same HDD/cold-snap analysis weighted by PJM zonal
    winter peak load (`load_weighted_hdd_coldsnap.py`; HDD65 2,674/winter).
    Weights: PJM Load Forecast Report, Jan 2026, Table B-2.
  - Raw station files (`USW*.dly`) are the NOAA GHCN-Daily downloads.
- `stack-analysis/` — PJM capacity stack (trailing + forward, 2016-2036)
  - Anchor: PJM State of the Market 2025 Annual, Table 12-1,
    Dec 31 2025, 202,424.8 MW. Forward: anchor + EIA-860M Sep 2026
    changelog (BA=PJM).
  - `build_stack.py` (v1, EIA-only) and `build_stack_v2.py` (v2, with 32
    manual online corrections; net +18,967 MW 2026-2036, 2036 total
    221,391.8 MW). Edit the scripts, not the CSVs — the scripts
    regenerate every v2 output from the v1 files + hardcoded adjustments.
  - Conventions: RMR-style override pushes coal retirements scheduled
    2026-2028 to Jan 2029 (5 units, 4,569 MW). Behind-the-meter rule:
    co-located load+generation counts as 0 MW of grid addition when the
    grid connection is entirely accounted for by the load.
  - Cayuga Energy Complex (1,476 MW) is NOT in this stack: it
    interconnects into MISO, not PJM. It belongs in the MISO stack
    (`stack-analysis/miso/`), where it is a +1,476 MW gas addition
    in v2 (Sep 2029/May 2030), with Cayuga coal retirement −1,062 MW.
- `stack-analysis/miso/` — MISO capacity stack (trailing + forward,
  2016-2036), regionalized North/Central/South by LRZ (North = LRZ 1+3,
  Central = LRZ 2+4+5+6+7, South = LRZ 8+9+10), NOT MTEP planning
  regions. Anchor 211,974.9 MW Dec 31, 2025 (EIA-860M Operating-sheet
  snapshot; no published MISO ICAP-by-fuel table exists). v2 (12 named
  adjustments, 26 row changes): net +35,900.9 MW 2026-2036, 2036 total
  247,875.8 MW (+6,340.0 vs v1; gas +8,566.8, coal −2,403.8,
  nuclear +177.0).

## What is excluded and why

The GitHub connector push is text-only, max 16 MiB per snapshot, so these
local files are not in the repo:

- PNG charts (`*.png` in both folders) — binary. Regenerate by running
  the scripts; the charts are figures of the CSV/JSON outputs.
- `stack-analysis/raw/*.pdf` — State of the Market Section 12 PDFs
  (source for the anchor). The extracted text (`*.txt`) is included.
- `stack-analysis/raw/eia860m_sep2026.xlsx` — EIA-860M source workbook
  (binary). Re-download from EIA to reproduce the changelog.
- `weather-analysis/forward-cone/forward_cone_pairs.csv` (18 MB) —
  exceeds the 16 MiB per-snapshot cap. Derived data; regenerate with
  `forward_cone.py` from the `.dly` files.

## Regenerating derived files

Weather: `python3 weather-analysis/fetch_and_analyze.py`,
`python3 weather-analysis/hdd_coldsnap.py`,
`python3 weather-analysis/forward-cone/forward_cone.py`,
`python3 weather-analysis/load-weighted/load_weighted_hdd_coldsnap.py`.
Stack: `python3 stack-analysis/build_stack.py`,
`python3 stack-analysis/build_stack_v2.py`.
