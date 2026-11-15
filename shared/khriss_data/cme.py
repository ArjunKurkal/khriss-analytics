"""CME Group settlements capture for TTF / JKM (Gas Fundies price layer).

Transport reality (verified 2026-11-15): CME blocks this environment's
scripted egress — every cmegroup.com path returns HTTP 403 ("This IP
address is blocked due to suspected web scraping activity") for direct
HTTP clients. The same endpoints load fine in Arjun's Chrome. Capture
therefore runs through the browser: a browser task reads the settlements
pages (or the CmeWS JSON) and returns the full table as CSV text in the
format below; this module parses, validates, and archives it.

The CmeWS JSON endpoint itself is public and keyless:
  https://www.cmegroup.com/CmeWS/mvc/Settlements/Futures/Settlements/{id}/FUT?tradeDate=MM/DD/YYYY
(Henry Hub product id 444 verified by pull, 2026-11-15.) The feed retains
only ~5 business days, so capture is daily or the history is lost.

Expected browser-capture format, one block per product per trade date:

    ## TTF_EUR 2026-11-13
    month,settle,volume,open_interest
    DEC 26,90.952,169,1393
    ...
    TOTAL_VOLUME,312
    TOTAL_OI,10875

"-" or empty numeric fields parse as missing. Validation: parsed volume
and OI sums are cross-checked against the page totals when provided
(volume totals on CME pages are estimates and can differ slightly from
the row sum; OI totals should match closely — mismatches are reported,
never silently accepted).
"""
from __future__ import annotations

import io
import re
from dataclasses import dataclass

import pandas as pd

from .config import project_data

CME_PRODUCTS = {
    "TTF_EUR": {
        "name": "Dutch TTF Natural Gas Calendar Month Futures",
        "globex": "TTF",
        "unit": "EUR/MWh",
        "settlements_url": "https://www.cmegroup.com/markets/energy/natural-gas/dutch-ttf-natural-gas-calendar-month.settlements.html",
        "cmews_product_id": None,  # to pin; page capture does not need it
    },
    "TTF_USD": {
        "name": "Dutch TTF Natural Gas (USD/MMBtu) Futures",
        "globex": "TFU",
        "unit": "USD/MMBtu",
        "settlements_url": "https://www.cmegroup.com/markets/energy/natural-gas/dutch-ttf-natural-gas-usd-mmbtu.settlements.html",
        "cmews_product_id": None,
    },
    "JKM": {
        "name": "LNG Japan/Korea Marker (Platts) Futures",
        "globex": "JKM",
        "unit": "USD/MMBtu",
        "settlements_url": "https://www.cmegroup.com/markets/energy/natural-gas/lng-japan-korea-marker-platts-swap.settlements.html",
        "cmews_product_id": None,
    },
    "HH_FUT": {
        "name": "Henry Hub Natural Gas Futures",
        "globex": "NG",
        "unit": "USD/MMBtu",
        "settlements_url": "https://www.cmegroup.com/markets/energy/natural-gas/henry-hub-natural-gas.settlements.html",
        "cmews_product_id": 444,
    },
}

_MONTHS = {m: i + 1 for i, m in enumerate(
    ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"])}

_BLOCK_RE = re.compile(r"^##\s+([A-Z_]+)\s+(\d{4}-\d{2}-\d{2})\s*$", re.M)


@dataclass
class CaptureBlock:
    product: str
    trade_date: str
    rows: pd.DataFrame
    total_volume: float | None
    total_oi: float | None


def _num(x: str) -> float | None:
    x = x.strip().replace(",", "")
    if x in ("", "-"):
        return None
    return float(x)


def _contract_date(label: str) -> str:
    mon, yy = label.strip().upper().split()
    return f"20{yy}-{_MONTHS[mon]:02d}-01"


def parse_capture(text: str) -> list[CaptureBlock]:
    """Parse one browser-capture report into validated blocks."""
    blocks: list[CaptureBlock] = []
    parts = _BLOCK_RE.split(text)
    # parts: [prefix, product, date, body, product, date, body, ...]
    for i in range(1, len(parts) - 2, 3):
        product, trade_date, body = parts[i], parts[i + 1], parts[i + 2]
        if product not in CME_PRODUCTS:
            raise ValueError(f"unknown product in capture: {product}")
        rows, total_volume, total_oi = [], None, None
        for line in body.splitlines():
            line = line.strip()
            if not line or line.lower().startswith("month,"):
                continue
            fields = [f.strip() for f in line.split(",")]
            if fields[0] == "TOTAL_VOLUME":
                total_volume = _num(fields[1])
                continue
            if fields[0] == "TOTAL_OI":
                total_oi = _num(fields[1])
                continue
            if len(fields) < 4:
                continue
            rows.append({
                "trade_date": trade_date,
                "product": product,
                "contract_month": fields[0].upper(),
                "contract_date": _contract_date(fields[0]),
                "settle": _num(",".join(fields[1:-2])) if len(fields) > 4 else _num(fields[1]),
                "volume": _num(fields[-2]),
                "open_interest": _num(fields[-1]),
                "unit": CME_PRODUCTS[product]["unit"],
            })
        if not rows:
            raise ValueError(f"no settlement rows parsed for {product} {trade_date}")
        blocks.append(CaptureBlock(product, trade_date,
                                   pd.DataFrame(rows), total_volume, total_oi))
    if not blocks:
        raise ValueError("no capture blocks found in text")
    return blocks


def validate_block(block: CaptureBlock) -> list[str]:
    """Return a list of warnings (empty = clean)."""
    warns = []
    df = block.rows
    if df["settle"].isna().all():
        warns.append(f"{block.product} {block.trade_date}: all settles missing")
    if block.total_oi is not None:
        s = df["open_interest"].sum(min_count=1)
        if pd.notna(s) and abs(s - block.total_oi) > max(1.0, 0.01 * block.total_oi):
            warns.append(f"{block.product} {block.trade_date}: OI row sum {s:.0f} "
                         f"vs page total {block.total_oi:.0f}")
    if block.total_volume is not None:
        s = df["volume"].sum(min_count=1)
        if pd.notna(s) and abs(s - block.total_volume) > max(2.0, 0.05 * block.total_volume):
            warns.append(f"{block.product} {block.trade_date}: volume row sum {s:.0f} "
                         f"vs page total {block.total_volume:.0f} (page totals are estimates)")
    dup = df.duplicated(subset=["contract_month"]).any()
    if dup:
        warns.append(f"{block.product} {block.trade_date}: duplicate contract months")
    return warns


def archive_blocks(blocks: list[CaptureBlock], project: str = "gas-fundies") -> pd.DataFrame:
    """Append blocks to the lake Parquet, deduped on (trade_date, product,
    contract_month) with the newest capture winning."""
    _, curated = project_data(project)
    path = curated / "prices_cme_settlements.parquet"
    new = pd.concat([b.rows for b in blocks], ignore_index=True)
    if path.exists():
        old = pd.read_parquet(path)
        merged = pd.concat([old, new], ignore_index=True)
    else:
        merged = new
    merged = (merged.drop_duplicates(
        subset=["trade_date", "product", "contract_month"], keep="last")
        .sort_values(["trade_date", "product", "contract_date"])
        .reset_index(drop=True))
    merged.to_parquet(path, index=False)
    return merged


def parse_cmews_json(payload: dict, product: str) -> pd.DataFrame:
    """Parse a CmeWS settlements JSON payload (when a route to it exists —
    e.g. a browser-downloaded file) into the archive row schema."""
    trade = payload["tradeDate"]  # MM/DD/YYYY
    trade_date = pd.Timestamp(trade).strftime("%Y-%m-%d")
    rows = []
    for s in payload.get("settlements", []):
        rows.append({
            "trade_date": trade_date,
            "product": product,
            "contract_month": s["month"].upper(),
            "contract_date": _contract_date(s["month"]),
            "settle": _num(str(s.get("settle", "-"))),
            "volume": _num(str(s.get("volume", "-"))),
            "open_interest": _num(str(s.get("openInterest", "-"))),
            "unit": CME_PRODUCTS[product]["unit"],
        })
    return pd.DataFrame(rows)
