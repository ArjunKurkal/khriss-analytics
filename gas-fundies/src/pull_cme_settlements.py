"""Archive a CME settlements browser capture into the lake.

CME blocks scripted egress from this environment (HTTP 403 domain-wide,
verified 2026-11-15), so capture runs through Arjun's Chrome: a browser
task transcribes the settlements pages into the block format documented
in khriss_data.cme, and this script parses, validates, and archives it.

Usage:
    python pull_cme_settlements.py --capture-file /path/to/capture.md

Exit codes: 0 = archived clean (warnings allowed, printed); 2 = parse or
validation failure severe enough to refuse archiving (no blocks parsed).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "shared"))

from khriss_data.cme import parse_capture, validate_block, archive_blocks  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--capture-file", required=True)
    args = ap.parse_args()

    text = Path(args.capture_file).read_text()
    try:
        blocks = parse_capture(text)
    except ValueError as e:
        print(f"CME capture refused: {e}")
        return 2

    all_warns: list[str] = []
    for b in blocks:
        all_warns += validate_block(b)
    merged = archive_blocks(blocks)

    for b in blocks:
        front = b.rows.sort_values("contract_date").iloc[0]
        print(f"{b.product} {b.trade_date}: {len(b.rows)} months, front "
              f"{front['contract_month']} settle {front['settle']} {front['unit']}")
    for w in all_warns:
        print(f"WARN: {w}")
    print(f"archive rows total: {len(merged)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
