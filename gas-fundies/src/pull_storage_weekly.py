"""Weekly natural gas storage — KEYLESS puller.

Sources (both public EIA files, no API key):
  - Snapshot JSON: https://ir.eia.gov/ngs/wngsr.json (latest week, with
    year-ago and 5-year comparison values)
  - History XLS:   https://ir.eia.gov/ngs/ngshistory.xls (weekly history
    by storage region)

Output: curated/storage_weekly.parquet with columns
  week_ending (date), region, working_gas_bcf
Regions: Lower 48 total, East, Midwest, South Central (total, salt,
non-salt), Mountain, Pacific.
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

import pandas as pd
import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "shared"))
from khriss_data.config import project_data          # noqa: E402
from khriss_data.io import write_parquet              # noqa: E402

HISTORY_XLS = "https://ir.eia.gov/ngs/ngshistory.xls"
SNAPSHOT_JSON = "https://ir.eia.gov/ngs/wngsr.json"
UA = {"User-Agent": "khriss-analytics/1.0"}


REGION_MAP = {
    "East Region": "East",
    "Midwest Region": "Midwest",
    "Mountain Region": "Mountain",
    "Pacific Region": "Pacific",
    "South Central Region": "South Central",
    "Salt": "South Central Salt",
    "NonSalt": "South Central Non-Salt",
    "Total Lower 48": "Lower 48",
}


def fetch_history() -> pd.DataFrame:
    """Parse sheet 'html_report_history' of ngshistory.xls.

    Layout verified 2026-11-15: note rows 0-5, header row 6
    (Week ending | Source | East Region | Midwest Region | Mountain
    Region | Pacific Region | South Central Region | Salt | NonSalt |
    Total Lower 48), then one row per week, dates as Excel serials.
    The header row is located by its 'Week ending' label rather than a
    fixed index, in case EIA adds note rows.
    """
    r = requests.get(HISTORY_XLS, headers=UA, timeout=120)
    r.raise_for_status()
    raw = pd.read_excel(io.BytesIO(r.content), sheet_name="html_report_history",
                        header=None, engine="calamine")
    header_row = None
    for i in range(min(15, len(raw))):
        if str(raw.iloc[i, 0]).strip().lower() == "week ending":
            header_row = i
            break
    if header_row is None:
        raise RuntimeError("ngshistory.xls: 'Week ending' header row not found — layout changed")
    cols = [str(c).strip() for c in raw.iloc[header_row]]
    body = raw.iloc[header_row + 1:].copy()
    body.columns = cols
    body["week_ending"] = pd.to_datetime(body["Week ending"], errors="coerce")
    body = body.dropna(subset=["week_ending"])
    frames = []
    for src_col, region in REGION_MAP.items():
        if src_col not in body.columns:
            raise RuntimeError(f"ngshistory.xls: expected column {src_col!r} missing — layout changed")
        s = pd.DataFrame({
            "week_ending": body["week_ending"],
            "region": region,
            "working_gas_bcf": pd.to_numeric(body[src_col], errors="coerce"),
        }).dropna(subset=["working_gas_bcf"])
        frames.append(s)
    out = pd.concat(frames, ignore_index=True)
    out["week_ending"] = out["week_ending"].dt.date
    return out.sort_values(["region", "week_ending"]).reset_index(drop=True)


def main() -> None:
    _, curated = project_data("gas-fundies")
    df = fetch_history()
    write_parquet(df, curated / "storage_weekly.parquet", "storage_weekly")
    import json as _json
    _r = requests.get(SNAPSHOT_JSON, headers=UA, timeout=60)
    snap = _json.loads(_r.content.decode("utf-8-sig"))  # EIA serves a BOM
    print(f"snapshot: week {snap.get('current_week')} released {snap.get('release_date')}")
    print(f"history: {df['week_ending'].min()} to {df['week_ending'].max()}, "
          f"{df['region'].nunique()} region labels")


if __name__ == "__main__":
    main()
