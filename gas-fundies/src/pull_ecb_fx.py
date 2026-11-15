"""ECB euro reference rates (EUR/USD) for the TTF conversion.

Source: ECB daily + historical reference-rate XML files (free, keyless).
The historical file carries the full series back to 1999, so each run
rewrites the whole table; the daily file is merged on top in case the
historical file lags a day. Rates are ECB reference rates (USD per EUR),
published on TARGET working days only — consumers must as-of join.
"""
from __future__ import annotations

import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pandas as pd
import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "shared"))
from khriss_data.config import project_data  # noqa: E402

NS = {"fx": "http://www.ecb.int/vocabulary/2002-08-01/eurofxref"}
URLS = [
    "https://www.ecb.europa.eu/stats/eurofxref/eurofxref-hist.xml",
    "https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml",
]


def fetch_rates() -> pd.DataFrame:
    rows = {}
    for url in URLS:
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=60)
        r.raise_for_status()
        root = ET.fromstring(r.content)
        for day in root.iter("{%s}Cube" % NS["fx"]):
            t = day.get("time")
            if not t:
                continue
            for c in day:
                if c.get("currency") == "USD":
                    rows[t] = float(c.get("rate"))
    df = pd.DataFrame(sorted(rows.items()), columns=["date", "eur_usd"])
    df["date"] = pd.to_datetime(df["date"])
    return df


def main() -> None:
    _, curated = project_data("gas-fundies")
    df = fetch_rates()
    out = curated / "fx_eurusd_daily.parquet"
    df.to_parquet(out, index=False)
    last = df.iloc[-1]
    print(f"ECB EUR/USD: {len(df)} rates, latest {last['date'].date()} = {last['eur_usd']}")


if __name__ == "__main__":
    main()
