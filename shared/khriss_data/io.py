"""Parquet IO and run logging for the shared data lake.

Convention: curated datasets are Parquet (CSV only where a human needs to
eyeball a small table). Every write is logged to <data_root>/_runs.jsonl
with row counts and a timestamp, so any number in a dashboard can be
traced back to the run that produced it.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from .config import data_root


def _log(event: dict) -> None:
    event = {"ts": datetime.now(timezone.utc).isoformat(), **event}
    with open(data_root() / "_runs.jsonl", "a") as fh:
        fh.write(json.dumps(event) + "\n")
    print(f"[{event['ts']}] {event.get('action', '')} {event.get('dataset', '')} "
          f"rows={event.get('rows', '')} {event.get('detail', '')}".strip())


def write_parquet(df: pd.DataFrame, path: Path, dataset: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False)
    _log({"action": "write", "dataset": dataset, "rows": len(df), "detail": str(path)})
    return path


def read_parquet(path: Path, dataset: str = "") -> pd.DataFrame:
    df = pd.read_parquet(path)
    _log({"action": "read", "dataset": dataset or path.stem, "rows": len(df),
          "detail": str(path)})
    return df
