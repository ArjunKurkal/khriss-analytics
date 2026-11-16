# hormuz-tracker

Ship-level tracking of Strait of Hormuz transits for khriss-analytics.
Free/public data only (personal account; no work vendor data).

Two parts:

1. **Historical window** — BUILT 2026-11-15 on Arjun's Option-1 decision.
   IMF PortWatch daily counts (full pull 2019–present in
   `data/portwatch/`), measured tanker aggregate as the primary series,
   plus a clearly-labelled MODELLED monthly crude/products split
   (crude count share 45%, band 34–59%) and modelled monthly LNG
   estimate (EIA-anchored, ±25%; crisis months blank except sourced
   points) — see `src/model_split.py` for the full method and
   assumptions. Dashboard in `dashboard/` (static Plotly, trailing
   12 months with calendar-2025 baseline — audit default, confirmed
   by Arjun 2026-11-15).
   Pipeline: `src/pull_portwatch.py` → `src/model_split.py` →
   `src/build_dashboard.py`. Ras Tanura = port1091, Ras Laffan =
   port1090 in PortWatch Daily_Ports_Data.
2. **Forward collector** — BUILT 2026-11-15. Live AIS, ship-level
   transit detection from collection start onward.
   See `DESIGN.md` for the bounding box, transit-line/zone definitions,
   classification limits, storage layout, and supervision.
   **LNG is measured per-ship** (added 2026-11-15): a curated fleet
   registry (`registry/lng_fleet.csv`, 301 hulls, IMO-keyed, built by
   `src/build_lng_registry.py`) is matched against live static data
   (IMO > MMSI > name); matched crossings are recorded as named LNG
   transits. Crude vs products remains unmeasurable per-ship and stays
   with the modelled split. Registry misses that berth at / declare
   LNG terminals are logged as candidates in
   `logs/lng_candidates.jsonl`, never auto-classified. Forward measured
   LNG rates will calibrate the historical LNG estimate above.

Run / inspect:

```bash
systemctl status hormuz-collector
tail -f ~/workspace/hormuz-tracker/logs/collector.log
cat ~/workspace/hormuz-tracker/logs/status.json
~/workspace/hormuz-tracker/.venv/bin/python ~/workspace/hormuz-tracker/src/daily_counts.py
~/workspace/hormuz-tracker/.venv/bin/python ~/workspace/hormuz-tracker/src/lng_feed.py
~/workspace/hormuz-tracker/.venv/bin/python ~/workspace/hormuz-tracker/tests/test_collector_logic.py
```

The LNG feed (`FEED.md` is the data dictionary) is the consumable
output for the Gas Fundies global gas S&D: per-crossing Parquet in
`data/feeds/`, daily/monthly aggregates as small JSON in `feeds/`.
Geography (subscription box, crossing zones, terminal geofences) is
config, not code: `config/geo.json` — a second strait/terminal set is
a new config plus a fleet registry, not a rewrite.

After a VM replacement: `bash ~/workspace/hormuz-tracker/systemd/install_service.sh`.
