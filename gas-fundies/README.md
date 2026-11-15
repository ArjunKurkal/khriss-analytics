# Gas Fundies

US natural gas supply & demand, built only from free data. The core
identity: **supply − demand = change in inventories**, monthly, in Bcf/d,
with the residual against reported storage published as a balancing item
— never plugged silently.

Dashboard: `dashboard/index.html` (static, GitHub Pages) reads
`dashboard/data.json`, which the pipeline regenerates.

## Balance construction (net view)

- Supply = dry production + pipeline imports + LNG imports
- Demand = reported total consumption + pipeline exports + LNG exports
- Consumption breaks out residential, commercial, industrial, electric
  power (power burn), and other (lease + pipeline + vehicle fuel). The
  gap between the sector sum and EIA's reported total is kept as its own
  line (`consumption_sector_gap`).
- **LNG feedgas is derived, not observed**: feedgas = LNG exports × 1.11
  (liquefaction fuel and losses ≈ 10% of feedgas). It is a memo line in
  the net balance — the gas left the US system as exports — and the
  demand breakout in the dashboard shows it in place of raw LNG exports
  so the components sum to the same total demand.
- Storage reconciliation uses weekly working-gas stocks (month-end to
  month-end) from EIA's keyless weekly files; the five storage regions
  are East, Midwest, South Central (with salt / non-salt), Mountain,
  Pacific.
- Production regions are state aggregates (states are not basin-pure):
  Appalachia = PA/OH/WV, Southwest = TX/NM, Haynesville = LA,
  Midcontinent = OK/KS/AR, Rockies = WY/CO/UT/MT/ND, plus Alaska,
  Federal Offshore Gulf, and Other Lower 48. Basin detail comes from
  Baker Hughes rig counts. Mappings live in `config/regions.json`.
  EIA publishes monthly dry production only for the US total; by state
  it publishes marketed production, so regional dry production is an
  estimate (regional marketed × the month's US dry/marketed ratio).

## Pipeline

```
python run_all.py            # all steps, skipping what cannot run
```

| Step | Script | Source | Needs |
|---|---|---|---|
| eia | `src/pull_eia_monthly.py` | EIA API v2 routes | free EIA API key |
| storage | `src/pull_storage_weekly.py` | ir.eia.gov WNGSR JSON + history XLS | nothing (keyless) |
| rigs | `src/pull_rigs.py` | Baker Hughes workbook dropped in the data lake `raw/rigs/` | manual download (site bot-blocks scripts) |
| balance | `src/build_balance.py` | curated tables | eia + storage |
| dashboard | `src/build_dashboard_data.py` | curated tables | any subset |

Data lands in the central lake (`~/workspace/data/gas-fundies/`,
override with `KH_DATA_ROOT`): `raw/` as pulled, `curated/` as Parquet.
Nothing but code, config, and the small dashboard JSON goes in git.

## EIA key

Free registration: https://www.eia.gov/opendata/register.php
Provide it via `EIA_API_KEY`, `~/.config/khriss/eia_api_key`, or the
Muse secure connection `custom.eia` (see `shared/khriss_data/eia.py`).
Never commit a key.

## Known limits

- EIA monthly data lag ~2 months; the weekly storage file is the
  freshest layer.
- Baker Hughes blocks scripted downloads; the rig puller parses any
  workbook placed in the drop folder and says so when none is there.
- Daily cash/basis prices and forward curves are not free anywhere;
  Henry Hub spot (EIA) is the price layer.
