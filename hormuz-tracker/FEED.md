# Hormuz LNG feed — data dictionary

For downstream consumers (first consumer: the Gas Fundies workstream's
global gas S&D). Everything needed to ingest the LNG cargo feed without
reading the collector code. Feed version: schema **1** (2026-11-15).

## What this is

Ship-level LNG carrier transits of the Strait of Hormuz, **measured**
from live AIS by the hormuz-tracker forward collector, where each hull
is identified against a curated IMO-keyed LNG fleet registry
(`registry/lng_fleet.csv`, 301 hulls at first build). There is **no
modelled LNG in this feed** — the historical dashboard's LNG layer is a
separate, labelled estimate and is not part of this feed.

Collection began 2026-11-15. Every day not collected is permanently
lost (live AIS has no replay); gaps are logged in `logs/gaps.jsonl`
and never backfilled.

## Files

| File | Where | Contents |
|---|---|---|
| `lng_crossings.parquet` | lake: `~/workspace/hormuz-tracker/data/feeds/` | one row per measured LNG crossing (canonical) |
| `lng_daily.json` | lake (above) + repo: `hormuz-tracker/feeds/` | daily aggregates |
| `lng_monthly.json` | lake + repo: `hormuz-tracker/feeds/` | monthly aggregates |
| `lng_fleet.csv` | repo: `hormuz-tracker/registry/` | the fleet registry the matches come from |

Regenerate at any time: `.venv/bin/python src/lng_feed.py`
(idempotent; reads the whole crossings lake). Refresh cadence: run
alongside `src/daily_counts.py` (daily), and after any collector change.

## `lng_crossings.parquet` — columns

| Column | Type | Meaning |
|---|---|---|
| `crossing_ts` | float64 | crossing time, epoch seconds (interpolated at the transit line, 56.65°E for Hormuz) |
| `crossing_time` | string | same instant, ISO 8601 UTC (`YYYY-MM-DDTHH:MM:SSZ`) |
| `date` / `month` | string | UTC date / `YYYY-MM` of the crossing |
| `mmsi` | int64 | vessel MMSI at crossing time (can change over a hull's life) |
| `vessel_name` | string | name as broadcast / registry name |
| `imo` | int64 | IMO number — the stable hull key; join on this |
| `capacity_class` | string | `Q-Max` (266,000 m³) / `Q-Flex` (217,000 m³) / `conventional` / `conventional/unknown` |
| `capacity_m3` | int64, nullable | hull **nameplate** LNG capacity — NOT a measured cargo volume |
| `direction` | string | `outbound` = Gulf → Gulf of Oman; `inbound` = reverse |
| `region` | string | chokepoint region id from `config/geo.json` (`hormuz`) |

## JSON aggregates

Both files carry a header block (`feed`, `schema_version`, `region`,
`source`, `semantics`, `generated_at`, `coverage`) — read `semantics`
before using the numbers; it restates the caveats below in machine-
readable form. `coverage` gives `crossings_total`, `first_crossing`,
`last_crossing` (nulls when the feed is empty — a valid state).

Each `rows[]` entry (daily keyed by `date`, monthly by `month`):

| Field | Meaning |
|---|---|
| `transits_total` | measured LNG crossings in the period |
| `outbound` / `inbound` | split by direction |
| `capacity_m3_outbound` / `capacity_m3_inbound` | sum of **nameplate** capacity of the hulls that crossed — "capacity moved", never cargo loaded |
| `by_capacity_class` | counts by class |
| `distinct_vessels` | distinct hulls (IMO, falling back to MMSI) |
| `vessels` | sorted vessel names seen in the period |

## Caveats a consumer must honour

1. **Direction is not load status.** For Qatari/UAE liquefaction the
   outbound leg is the loaded leg in normal trade, but the feed reports
   the observed direction only. Any loaded/ballast inference is the
   consumer's, and should be labelled as such downstream.
2. **Capacity is nameplate.** A Q-Max crossing represents up to
   266,000 m³ of *capacity* (≈5.6 Bcf of gas at the standard ~600:1
   expansion ratio), not a metered cargo. State whatever conversion
   you apply downstream.
3. **AIS-visible only.** Hulls transiting with AIS off are absent;
   during the 2026 closure crisis, dark transits were the majority of
   what little moved. Treat counts as a floor with a variable,
   unmeasurable capture rate.
4. **Registry coverage is a floor.** 301 hulls vs a ~700–800 hull world
   fleet, skewed to notable/Qatar-service hulls (Q-Max complete,
   Q-Flex partial — see DESIGN.md). An LNG hull missing from the
   registry crosses as an unclassified tanker and does not appear here.
   Registry misses surfaced by terminal signals are logged in
   `logs/lng_candidates.jsonl` and folded into registry updates.
5. **Crisis-era baseline warning.** The feed starts during the
   post-closure crisis (traffic ≈5% of normal). Early rates are not a
   normal-times baseline for Qatar loadings.

## Generality

Nothing in the feed contract is Hormuz-specific except `region` and
the transit-line geometry, both of which live in `config/geo.json`.
The same enumerable-fleet + enumerable-terminal pattern (fleet registry
+ terminal geofences + crossing zones, all config) is the intended
design for LNG tracking at other liquefaction/regas regions; a second
region adds a config and a registry, and its crossings land in the
same schema with its own `region` value.
