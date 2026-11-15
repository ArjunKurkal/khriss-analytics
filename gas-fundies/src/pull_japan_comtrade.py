"""Japan LNG imports by origin — Asia layer (customs data via UN Comtrade).

Japan's Ministry of Finance trade statistics, republished by UN
Comtrade, pulled through Comtrade's keyless public preview API
(comtradeapi.un.org/public/v1/preview). Reporter Japan (392), imports
(flow M), HS 271111 (liquefied natural gas), monthly, all partners.
One call per month returns every partner plus the world total
(partnerCode 0). Quantities are net weight (kg -> tonnes) and CIF
value (USD).

The preview API is throttled (~1 call / 6 s) and capped per call, which
suits this use: a monthly seed from 2022 is ~50 calls. Comtrade lags
the MOF release by some weeks on top of MOF's own ~3-week lag.

Known gap, recorded 2026-11-15: METI's weekly LNG stocks at major
power utilities (published Wednesdays since Jan 2021) have no
machine-readable feed — the METI LNG survey itself was discontinued
in April 2022 and the weekly figure appears only in Japanese press
announcements. It is NOT in this layer; Japan's monthly totals are
covered by the JODI backbone until a harvest route is built.
"""
from __future__ import annotations

import sys
import time
from datetime import date

import pandas as pd
import requests

from pathlib import Path  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "shared"))
from khriss_data.config import project_data  # noqa: E402

API = "https://comtradeapi.un.org/public/v1/preview/C/M/HS"
SEED_START = (2022, 1)
SLEEP_S = 6.5
# The preview API returns partner codes but no descriptions.
PARTNER_NAMES = {
    0: "World", 12: "Algeria", 24: "Angola", 36: "Australia",
    96: "Brunei", 120: "Cameroon", 124: "Canada", 156: "China",
    178: "Congo", 226: "Equatorial Guinea", 818: "Egypt",
    360: "Indonesia", 410: "South Korea", 458: "Malaysia",
    508: "Mozambique", 566: "Nigeria", 512: "Oman",
    598: "Papua New Guinea", 604: "Peru", 634: "Qatar", 643: "Russia",
    702: "Singapore", 780: "Trinidad and Tobago", 792: "Turkey",
    784: "United Arab Emirates", 842: "United States",
}


def fetch_month(year: int, month: int) -> list[dict]:
    params = {"reporterCode": 392, "period": f"{year}{month:02d}",
              "flowCode": "M", "cmdCode": "271111"}
    r = requests.get(API, params=params, headers={"User-Agent": "Mozilla/5.0"},
                     timeout=60)
    if r.status_code == 429:
        raise RuntimeError("comtrade preview rate limit hit (429) — stop")
    if r.status_code != 200:
        return []
    return r.json().get("data") or []


def main() -> None:
    _, curated = project_data("gas-fundies")
    path = curated / "japan_lng_imports_monthly.parquet"
    existing = pd.read_parquet(path) if path.exists() else None
    if existing is not None and not existing.empty:
        last = pd.to_datetime(existing["month"]).max()
        start = (last.year, last.month)
        # re-pull the last two months (revisions + late postings)
        months = []
        y, m = start
        for _ in range(3):
            months.append((y, m))
            m += 1
            if m == 13:
                y, m = y + 1, 1
    else:
        months = []
        y, m = SEED_START
        today = date.today()
        while (y, m) <= (today.year, today.month):
            months.append((y, m))
            m += 1
            if m == 13:
                y, m = y + 1, 1

    rows = []
    for y, m in months:
        data = fetch_month(y, m)
        for row in data:
            code = row.get("partnerCode")
            rows.append({
                "month": pd.Timestamp(y, m, 1),
                "partner_code": code,
                "partner": PARTNER_NAMES.get(
                    code, row.get("partnerDesc") or f"code {code}"),
                "net_wgt_tonnes": (row.get("netWgt") or 0) / 1000.0,
                "value_usd": row.get("primaryValue"),
            })
        if data:
            print(f"  {y}-{m:02d}: {len(data)} partners")
        time.sleep(SLEEP_S)
    new = pd.DataFrame(rows)
    if new.empty:
        print("Japan Comtrade: no rows returned")
        return
    if existing is not None and not existing.empty:
        merged = pd.concat([existing, new], ignore_index=True)
    else:
        merged = new
    merged = (merged.drop_duplicates(subset=["month", "partner_code"],
                                     keep="last")
              .sort_values(["month", "partner_code"]).reset_index(drop=True))
    merged.to_parquet(path, index=False)
    world = merged[merged["partner_code"] == 0]
    last = world.iloc[-1]
    print(f"Japan LNG imports: {len(merged)} rows through "
          f"{last['month'].date()}; latest world total "
          f"{last['net_wgt_tonnes']/1e6:.2f} Mt")


if __name__ == "__main__":
    main()
