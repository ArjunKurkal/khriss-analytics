"""Monthly EIA gas fundamentals — requires a free EIA API key.

Pulls every series in config/eia_series.json through the API v2 seriesid
endpoint and lands two curated tables:

  monthly_state_production.parquet  period, state, marketed_production_mmcf
  monthly_us_balance_inputs.parquet period, component, value_mmcf
      components: dry production (US check total), consumption by sector,
      total consumption, pipeline/LNG imports and exports.

Validation contract: any series that returns no rows is reported by name
at the end of the run and the run exits non-zero. A wrong series ID must
never become a silent zero in the balance.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "shared"))
from khriss_data.config import project_data      # noqa: E402
from khriss_data.eia import EIAClient            # noqa: E402
from khriss_data.io import write_parquet         # noqa: E402

CONFIG = Path(__file__).resolve().parents[1] / "config" / "eia_series.json"


def fetch(client: EIAClient, sid: str, start: str) -> pd.DataFrame:
    """One series, or an empty frame if the call ultimately failed.

    The client already retries transient gateway errors; anything that
    still raises is reported by the caller as a missing series rather
    than crashing the whole pull (a rerun fills the gap).
    """
    try:
        return tidy(client.series(sid, start=start), start)
    except Exception as e:  # noqa: BLE001 - reported, not hidden
        print(f"  fetch failed for {sid}: {type(e).__name__}: {e}")
        return pd.DataFrame()


def tidy(df: pd.DataFrame, start: str) -> pd.DataFrame:
    if df.empty:
        return df
    df = df.copy()
    df["period"] = pd.to_datetime(df["period"])
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df = df[df["period"] >= pd.Timestamp(start)]
    return df[["period", "value"]].dropna().sort_values("period")


def main() -> None:
    cfg = json.loads(CONFIG.read_text())
    start = cfg["start_monthly"]
    client = EIAClient()
    _, curated = project_data("gas-fundies")
    missing: list[str] = []

    # --- state marketed production --------------------------------------
    # EIA publishes monthly dry production only for the US total; by
    # state it publishes marketed production. build_balance.py converts
    # regional marketed to a dry estimate with the US dry/marketed ratio.
    frames = []
    for state, sid in cfg["monthly_volumes_mmcf"]["marketed_production_state"].items():
        df = fetch(client, sid, start)
        if df.empty:
            missing.append(f"marketed_production_state.{state} ({sid})")
            continue
        df["state"] = state
        frames.append(df.rename(columns={"value": "marketed_production_mmcf"}))
    if frames:
        prod = pd.concat(frames, ignore_index=True)
        write_parquet(prod, curated / "monthly_state_production.parquet",
                      "monthly_state_production")

    # --- US balance inputs ----------------------------------------------
    frames = []
    for component, sid in cfg["monthly_volumes_mmcf"].items():
        if component == "marketed_production_state":
            continue
        df = fetch(client, sid, start)
        if df.empty:
            missing.append(f"{component} ({sid})")
            continue
        df["component"] = component
        frames.append(df.rename(columns={"value": "value_mmcf"}))
    if frames:
        bal = pd.concat(frames, ignore_index=True)
        write_parquet(bal, curated / "monthly_us_balance_inputs.parquet",
                      "monthly_us_balance_inputs")

    # --- Henry Hub daily spot -------------------------------------------
    sid = cfg["prices_daily_usd_mmbtu"]["henry_hub_spot"]
    df = fetch(client, sid, cfg["start_daily_price"])
    if df.empty:
        missing.append(f"henry_hub_spot ({sid})")
    else:
        write_parquet(df.rename(columns={"value": "henry_hub_usd_mmbtu"}),
                      curated / "price_henry_hub_daily.parquet", "price_henry_hub_daily")

    if missing:
        print("SERIES WITH NO DATA (fix config/eia_series.json):")
        for m in missing:
            print(f"  - {m}")
        raise SystemExit(1)
    print("All configured EIA series returned data.")


if __name__ == "__main__":
    main()
