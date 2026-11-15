"""DOE cargo-level US LNG exports — the US "truth layer" for LNG trade.

Source: U.S. Department of Energy, Hydrocarbons and Geothermal Energy
Office (HGEO, formerly FECM), "Natural Gas Imports and Exports Monthly"
— file 3, "U.S. LNG Exports and Re-Exports Details (Jan 2016 - ...)",
a cargo-level spreadsheet compiled from the FE-746R reports every
authorization holder must file. Free, no account. The landing page URL
carries the year; the file name carries the through-month, so the page
is scraped on every run and the newest file archived under raw/doe/.

Each spreadsheet row is one authorization holder's share of a sailing;
a physical cargo is (departure date, tanker, point of exit, country).
Export and re-export volumes are kept in separate columns — a cargo
can carry both. ISO-container rows (a few MMcf each) are excluded;
this table is vessel cargoes only. Destination is as reported at
departure: later diversions and re-exports from the destination are
not captured. Lag is ~2 months.

Cross-check: monthly vessel-export totals are compared with the EIA
monthly LNG export series used in the US balance (NG.N9133US2.M).
"""
from __future__ import annotations

import re
import sys
from datetime import date
from pathlib import Path

import pandas as pd
import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "shared"))
from khriss_data.config import project_data  # noqa: E402

LANDING = ("https://www.energy.gov/hgeo/articles/"
           "natural-gas-imports-and-exports-monthly-{year}")
SHEET = "By Vessel and ISO Container"


def find_cargo_file() -> str:
    html = requests.get(LANDING.format(year=date.today().year),
                        headers={"User-Agent": "Mozilla/5.0"},
                        timeout=60).text
    hrefs = re.findall(r'href="([^"]+\.xlsx)"', html)
    hits = [h for h in hrefs
            if "LNG" in h and "Exports%20and%20Re-Exports%20Details" in h]
    if not hits:
        raise RuntimeError("cargo file link not found on DOE landing page")
    url = hits[0]
    return url if url.startswith("http") else "https://www.energy.gov" + url


def parse_cargoes(xlsx_bytes: bytes) -> pd.DataFrame:
    import io
    df = pd.read_excel(io.BytesIO(xlsx_bytes), sheet_name=SHEET,
                       engine="openpyxl")
    df.columns = [str(c).strip() for c in df.columns]
    df = df.rename(columns={
        "Arrival/Departure Date": "date",
        "Tanker": "tanker",
        "Point of Entry or Exit": "point_of_exit",
        "Country": "country",
        "Volume (MMCF)": "volume_mmcf",
        "Activity": "activity",
        "Mode of Transport": "mode",
        "Companies": "authorization_holder",
    })
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df[df["mode"] == "Vessel"].copy()
    df["volume_mmcf"] = pd.to_numeric(df["volume_mmcf"], errors="coerce")
    df = df.dropna(subset=["volume_mmcf"])
    df["volume_bcf"] = df["volume_mmcf"] / 1000.0
    piv = (df.pivot_table(index=["date", "tanker", "point_of_exit", "country"],
                          columns="activity", values="volume_bcf",
                          aggfunc="sum").reset_index())
    piv.columns.name = None
    for col in ("Exports", "Re-Exports"):
        if col not in piv.columns:
            piv[col] = 0.0
    piv = piv.rename(columns={"Exports": "exports_bcf",
                              "Re-Exports": "reexports_bcf"})
    piv["total_bcf"] = piv["exports_bcf"] + piv["reexports_bcf"]
    holders = (df.groupby(["date", "tanker", "point_of_exit", "country"])
               ["authorization_holder"].nunique()
               .rename("n_authorization_holders").reset_index())
    piv = piv.merge(holders, on=["date", "tanker", "point_of_exit", "country"])
    return piv.sort_values("date").reset_index(drop=True)


def main() -> None:
    raw, curated = project_data("gas-fundies")
    url = find_cargo_file()
    fname = url.rsplit("/", 1)[-1]
    dest = raw / "doe" / fname
    if not dest.exists():
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"},
                         timeout=600)
        r.raise_for_status()
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(r.content)
        print(f"DOE cargo file: downloaded {fname} ({len(r.content)/1e3:.0f} KB)")
    else:
        print(f"DOE cargo file: already archived {fname}")
    cargoes = parse_cargoes(dest.read_bytes())
    out = curated / "doe_lng_cargoes.parquet"
    cargoes.to_parquet(out, index=False)
    dated = cargoes.dropna(subset=["date"])
    print(f"DOE cargoes: {len(cargoes)} vessel cargoes "
          f"({int(cargoes['date'].isna().sum())} undated), "
          f"{dated['date'].min().date()} .. {dated['date'].max().date()}")

    # Cross-check against EIA monthly LNG exports as carried in the US
    # balance (NG.N9133US2.M, Bcf/d -> Bcf/month).
    eia_path = curated / "balance_monthly.parquet"
    if eia_path.exists():
        bal = pd.read_parquet(eia_path)
        bal["month"] = pd.to_datetime(bal["month"]).dt.to_period("M")
        bal["eia_bcf"] = bal["exports_lng"] * bal["month"].dt.days_in_month
        eia = bal[["month", "eia_bcf"]]
        doe_m = (dated.assign(month=dated["date"].dt.to_period("M"))
                 .groupby("month")["exports_bcf"].sum().rename("doe_bcf"))
        both = pd.concat([doe_m, eia.set_index("month")["eia_bcf"]],
                         axis=1, join="inner").dropna()
        both["diff_pct"] = 100 * (both["doe_bcf"] - both["eia_bcf"]) / both["eia_bcf"]
        recent = both.tail(6)
        print("DOE vs EIA LNG exports (Bcf/month), last 6 overlapping months:")
        print(recent.round(2).to_string())
        print(f"mean |diff| over {len(both)} months: "
              f"{both['diff_pct'].abs().mean():.2f}%")


if __name__ == "__main__":
    main()
