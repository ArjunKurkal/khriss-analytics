#!/usr/bin/env python3
"""Gas Fundies pipeline orchestrator.

Runs each step in order and reports per-step status. A step that cannot
run (no EIA key, no rig workbook) is SKIPPED with its reason, not a
crash — the dashboard still builds from whatever curated data exists.

Usage:  python run_all.py [--only storage,rigs]
Steps:  eia (monthly + price, needs key) -> storage (keyless)
        -> rigs (needs a Baker Hughes workbook in the raw drop folder)
        -> balance (needs eia + storage) -> dashboard
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE / "src"
STEPS = ["eia", "storage", "rigs", "balance", "dashboard"]
SCRIPTS = {
    "eia": "pull_eia_monthly.py",
    "storage": "pull_storage_weekly.py",
    "rigs": "pull_rigs.py",
    "balance": "build_balance.py",
    "dashboard": "build_dashboard_data.py",
}


def run_step(name: str) -> tuple[str, str]:
    proc = subprocess.run(
        [sys.executable, str(SRC / SCRIPTS[name])],
        capture_output=True, text=True, timeout=3600)
    tail = (proc.stdout + proc.stderr).strip().splitlines()
    summary = tail[-1] if tail else ""
    if proc.returncode == 0:
        return "ok", summary
    # pull_rigs exits 2 when no workbook has been dropped in yet.
    if name == "rigs" and proc.returncode == 2:
        return "skipped", summary
    if name == "eia" and "EIAKeyMissing" in proc.stdout + proc.stderr:
        return "skipped", "no EIA credential available"
    return "FAILED", summary


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", help="comma-separated subset of steps")
    args = ap.parse_args()
    steps = STEPS if not args.only else [s for s in STEPS if s in args.only.split(",")]
    results = {}
    for step in steps:
        if step in ("balance",) and results.get("eia") == "FAILED":
            results[step] = ("skipped", "eia step failed")
            continue
        status, summary = run_step(step)
        results[step] = (status, summary)
        print(f"[{status:>7}] {step}: {summary}")
    failed = [s for s, (st, _) in results.items() if st == "FAILED"]
    raise SystemExit(1 if failed else 0)


if __name__ == "__main__":
    main()
