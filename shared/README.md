# shared/ — Khriss Analytics data infrastructure

A deliberately small shared layer. Every project (gas-fundies,
weather-analysis, stack-analysis, and whatever comes next) uses the same:

- `khriss_data/config.py` — one central data lake (`~/workspace/data`,
  override with `KH_DATA_ROOT`), with `raw/` and `curated/` per project.
  Data files live in the lake, never in this repository.
- `khriss_data/io.py` — Parquet read/write plus a run log
  (`<data_root>/_runs.jsonl`) so every published number traces to a run.
- `khriss_data/eia.py` — EIA API v2 client (faceted routes + legacy
  seriesid), key from `EIA_API_KEY` or `~/.config/khriss/eia_api_key`.
  Keys are never committed.

Adding a new source to any project = one puller module in that project
that lands a tidy Parquet table in the lake, plus one entry in the
project's data catalog. Nothing else in the shared layer changes.
