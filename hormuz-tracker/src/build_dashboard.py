"""Build dashboard/data.json from the Parquet lake + model outputs.

Run after pull_portwatch.py and model_split.py:
    .venv/bin/python src/build_dashboard.py

Window: trailing 12 months ending at the last PortWatch date, with
calendar-2025 as the baseline comparator (audit default, confirmed by
Arjun 2026-11-15 — the last of the three audit decisions to close).
"""
from __future__ import annotations

import json
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

import pyarrow.parquet as pq

PROJECT = Path(__file__).resolve().parent.parent
DASH = PROJECT / "dashboard"


def ma7(vals: list[float]) -> list[float | None]:
    out = []
    for i in range(len(vals)):
        if i < 6:
            out.append(None)
        else:
            out.append(round(sum(vals[i - 6:i + 1]) / 7, 2))
    return out


def main() -> int:
    DASH.mkdir(parents=True, exist_ok=True)
    rows = pq.read_table(
        PROJECT / "data/portwatch/chokepoint_hormuz.parquet").to_pylist()
    rows.sort(key=lambda r: r["date"])
    last = rows[-1]["date"]
    last_d = date.fromisoformat(last)
    start_d = last_d - timedelta(days=364)
    win = [r for r in rows if r["date"] >= start_d.isoformat()]
    y2025 = [r for r in rows if r["date"].startswith("2025")]

    def avg(rs, k):
        return round(sum(r[k] for r in rs) / len(rs), 1)

    classes = ["n_total", "n_tanker", "n_container", "n_dry_bulk",
               "n_general_cargo", "n_roro"]
    daily = {"date": [r["date"] for r in win]}
    for k in classes:
        daily[k] = [r[k] for r in win]
    daily["total_7dma"] = ma7(daily["n_total"])
    daily["tanker_7dma"] = ma7(daily["n_tanker"])
    daily["capacity_tanker"] = [r["capacity_tanker"] for r in win]

    baseline = {k: avg(y2025, k) for k in classes}

    split = pq.read_table(
        PROJECT / "data/model/monthly_split.parquet").to_pylist()
    lng = pq.read_table(
        PROJECT / "data/model/monthly_lng.parquet").to_pylist()

    ports = pq.read_table(
        PROJECT / "data/portwatch/ports.parquet").to_pylist()
    pmonthly: dict[str, dict[str, dict]] = defaultdict(dict)
    for r in ports:
        m = r["date"][:7]
        if m < "2025-11":
            continue
        d = pmonthly[r["portname"]].setdefault(
            m, {"tanker_calls": 0, "export_tanker_t": 0.0})
        d["tanker_calls"] += r["portcalls_tanker"] or 0
        d["export_tanker_t"] += r["export_tanker"] or 0.0
    ports_out = {name: [{"month": m, **vals}
                        for m, vals in sorted(months.items())]
                 for name, months in sorted(pmonthly.items())}

    # Forward collector snapshot (best effort; it runs independently).
    forward = {"note": "Forward ship-level collection started "
                       "2026-11-15 (see methods)."}
    status_path = PROJECT / "logs" / "status.json"
    if status_path.exists():
        s = json.loads(status_path.read_text())
        forward.update({k: s.get(k) for k in
                        ("started_at", "source", "vessels_tracked",
                         "vessels_known", "positions_kept", "crossings",
                         "updated_at")})
    counts_path = PROJECT / "data" / "derived" / "daily_counts.json"
    if counts_path.exists():
        forward["daily_counts"] = json.loads(
            counts_path.read_text()).get("counts", [])

    meta_path = PROJECT / "data" / "portwatch" / "pull_meta.json"
    pull_meta = json.loads(meta_path.read_text()) if meta_path.exists() else {}

    payload = {
        "meta": {
            "portwatch_last_date": last,
            "window_start": win[0]["date"],
            "window_end": last,
            "pulled_at": pull_meta.get("pulled_at"),
            "baseline_year": 2025,
            "closure_date": "2026-02-28",
        },
        "baseline_2025_daily_avg": baseline,
        "daily": daily,
        "monthly_split_modelled": split,
        "monthly_lng_modelled": lng,
        "ports_monthly": ports_out,
        "forward_collector": forward,
    }
    (DASH / "data.json").write_text(json.dumps(payload))
    print(f"data.json written: window {win[0]['date']}..{last}, "
          f"{len(win)} daily rows, {len(split)} split months, "
          f"{len(ports_out)} ports")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
