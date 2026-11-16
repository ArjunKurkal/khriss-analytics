"""JODI Gas backbone for the global gas S&D model.

Source: JODI Gas World Database bulk CSV (free, no account), discovered
through the publisher API listing at
https://api.publisher.jodidata.org/web/files/gas (returns the current
publicationId and file list). Every vintage is archived under
raw/jodi/vintage-<publicationId>/ before parsing, because JODI revises
history; the curated tables carry the vintage id they were built from.

Units: the CSV's M3 view (million cubic metres per month) is canonical.
Bcf/d = Mm3 * 0.0353147 / days_in_month. LNG flows are also kept in
kilotonnes (KTONS view) where reported.

Balance construction (per country-month, JODI questionnaire identity):
    supply  = production + receipts_from_other_sources + total_imports
    demand  = gross_inland_deliveries + total_exports
    implied_stock_change = supply - demand
    balancing_item = implied_stock_change - reported_stock_change
Deliveries use the OBSERVED series where reported, else the CALCULATED
series (flagged in deliveries_basis). The balancing item is published,
never plugged. JODI's own statistical difference (observed - calculated
deliveries) is kept as its own column.

Regions (approved scope, 2026-11-15): North America, Europe,
Asia-Pacific, Middle East, FSU, and Rest of World as the residual
(global minus named regions), so regions always sum to the global total
of reporting countries. Regional rows record how many member countries
actually reported production that month (coverage is uneven; Saudi
Arabia, Turkmenistan and Uzbekistan do not report to JODI Gas at all).
"""
from __future__ import annotations

import io
import json
import sys
import zipfile
from pathlib import Path

import pandas as pd
import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "shared"))
from khriss_data.config import project_data  # noqa: E402

LISTING_URL = "https://api.publisher.jodidata.org/web/files/gas"
DOWNLOAD_URL = "https://www.jodidata.org/jodi-publisher/gas/{pub}/{fname}"
CSV_MEMBER = "STAGING_world_NewFormat.csv"
MM3_TO_BCF = 0.0353147
QA_LNG_BASIS_FACTOR = 1.28  # see exports_lng_phys_bcfd note in parse_vintage

FLOW_MAP = {
    "INDPROD": "production",
    "OSOURCES": "other_sources",
    "TOTIMPSB": "imports_total",
    "IMPLNG": "imports_lng",
    "IMPPIP": "imports_pipe",
    "TOTEXPSB": "exports_total",
    "EXPLNG": "exports_lng",
    "EXPPIP": "exports_pipe",
    "STOCKCH": "stock_change_reported",
    "TOTDEMC": "deliveries_calc",
    "TOTDEMO": "deliveries_obs",
    "STATDIFF": "stat_diff",
    "MAINTOT": "elec_heat",
    "CLOSTLV": "closing_stocks",
}

REGIONS = {
    "North America": ["US", "CA", "MX"],
    "Europe": ["AT", "BE", "BG", "HR", "CZ", "DK", "EE", "FI", "FR", "DE",
               "GR", "HU", "IE", "IT", "LV", "LT", "LU", "MT", "NL", "PL",
               "PT", "RO", "SK", "SI", "ES", "SE", "GB", "NO", "CH", "TR",
               "AL", "MK", "RS", "MD"],
    "Asia-Pacific": ["JP", "KR", "CN", "IN", "TW", "AU", "ID", "MY", "TH",
                     "SG", "BD", "VN", "PH", "MM", "NZ", "PG", "BN", "HK"],
    "Middle East": ["QA", "AE", "OM", "KW", "IQ", "IR", "BH"],
    "FSU": ["RU", "UA", "AZ", "KZ", "BY", "AM", "GE"],
}
BALANCE_FLOWS = ["production", "other_sources", "imports_total",
                 "imports_lng", "imports_pipe", "exports_total",
                 "exports_lng", "exports_pipe", "deliveries",
                 "supply", "demand", "implied_stock_change",
                 "stock_change_reported", "balancing_item"]


def fetch_vintage(raw_root: Path) -> tuple[int, Path]:
    r = requests.get(LISTING_URL, headers={"User-Agent": "Mozilla/5.0"}, timeout=60)
    r.raise_for_status()
    listing = r.json()
    pub = int(listing["publicationId"])
    fname = next(f["filename"] for f in listing["files"]
                 if f.get("format") == "CSV" and not f.get("ignore"))
    vdir = raw_root / f"vintage-{pub}"
    zpath = vdir / fname
    if not zpath.exists():
        vdir.mkdir(parents=True, exist_ok=True)
        (vdir / "listing.json").write_text(json.dumps(listing, indent=1))
        dl = requests.get(DOWNLOAD_URL.format(pub=pub, fname=fname),
                          headers={"User-Agent": "Mozilla/5.0"}, timeout=600)
        dl.raise_for_status()
        zpath.write_bytes(dl.content)
        print(f"JODI vintage {pub}: downloaded {fname} ({len(dl.content)/1e6:.1f} MB)")
    else:
        print(f"JODI vintage {pub}: already archived")
    return pub, zpath


def parse_vintage(zpath: Path, pub: int) -> pd.DataFrame:
    with zipfile.ZipFile(zpath) as z:
        with z.open(CSV_MEMBER) as f:
            df = pd.read_csv(f, low_memory=False)
    df["month"] = pd.to_datetime(df["TIME_PERIOD"])
    m3 = df[df["UNIT_MEASURE"] == "M3"].copy()
    wide = (m3.pivot_table(index=["REF_AREA", "month"], columns="FLOW_BREAKDOWN",
                           values="OBS_VALUE", aggfunc="first")
            .rename(columns=FLOW_MAP).reset_index()
            .rename(columns={"REF_AREA": "country"}))
    kt = df[df["UNIT_MEASURE"] == "KTONS"]
    if not kt.empty:
        ktw = (kt.pivot_table(index=["REF_AREA", "month"], columns="FLOW_BREAKDOWN",
                              values="OBS_VALUE", aggfunc="first")
               .rename(columns={"EXPLNG": "exports_lng_ktons",
                                "IMPLNG": "imports_lng_ktons"})
               .reset_index().rename(columns={"REF_AREA": "country"}))
        keep = [c for c in ["country", "month", "exports_lng_ktons",
                            "imports_lng_ktons"] if c in ktw.columns]
        wide = wide.merge(ktw[keep], on=["country", "month"], how="left")
    for c in FLOW_MAP.values():
        if c not in wide.columns:
            wide[c] = pd.NA
    wide["deliveries"] = wide["deliveries_obs"].fillna(wide["deliveries_calc"])
    wide["deliveries_basis"] = wide["deliveries_obs"].notna().map(
        {True: "observed", False: "calculated"})
    wide["supply"] = wide[["production", "other_sources", "imports_total"]].sum(
        axis=1, min_count=1)
    wide["demand"] = wide[["deliveries", "exports_total"]].sum(axis=1, min_count=1)
    wide["implied_stock_change"] = wide["supply"] - wide["demand"]
    wide["balancing_item"] = wide["implied_stock_change"] - wide["stock_change_reported"]
    days = wide["month"].dt.days_in_month
    for c in BALANCE_FLOWS:
        wide[c + "_bcfd"] = wide[c] * MM3_TO_BCF / days
    # Qatar LNG physical-basis series (HORMUZ-JODI-RECONCILIATION.md,
    # 2026-11-15): Qatar's as-reported EXPLNG in M3 implies 97–105 Mtpa
    # against 77 Mtpa of nameplate capacity in every year 2019–2025 —
    # a stable reporting-basis offset of ~1.28x physical volume. The
    # as-reported series is kept untouched; exports_lng_phys_bcfd puts
    # Qatar on a physical basis and equals the as-reported series for
    # every other country. Use the phys series for any LNG total.
    wide["exports_lng_phys_bcfd"] = wide["exports_lng_bcfd"]
    qa = wide["country"] == "QA"
    wide.loc[qa, "exports_lng_phys_bcfd"] = (
        wide.loc[qa, "exports_lng_bcfd"] / QA_LNG_BASIS_FACTOR)
    wide["closing_stocks_bcf"] = wide["closing_stocks"] * MM3_TO_BCF
    wide["vintage"] = pub
    return wide.sort_values(["country", "month"]).reset_index(drop=True)


def aggregate_regions(country: pd.DataFrame) -> pd.DataFrame:
    rows = []
    all_countries = sorted(country["country"].unique())
    region_of = {c: r for r, cs in REGIONS.items() for c in cs}
    named = set(region_of)
    groups = dict(REGIONS)
    groups["Rest of World"] = [c for c in all_countries if c not in named]
    groups["Global"] = all_countries
    for region, members in groups.items():
        sub = country[country["country"].isin(members)]
        g = sub.groupby("month").agg(
            **{c: (c, "sum") for c in BALANCE_FLOWS},
            countries_reporting=("production", "count"),
            members=("country", "nunique"))
        g = g.reset_index()
        g.insert(0, "region", region)
        days = g["month"].dt.days_in_month
        for c in BALANCE_FLOWS:
            g[c + "_bcfd"] = g[c] * MM3_TO_BCF / days
        rows.append(g)
    return pd.concat(rows, ignore_index=True).sort_values(
        ["region", "month"]).reset_index(drop=True)


def main() -> None:
    raw, curated = project_data("gas-fundies")
    pub, zpath = fetch_vintage(raw / "jodi")
    country = parse_vintage(zpath, pub)
    cpath = curated / "jodi_country_monthly.parquet"
    country.to_parquet(cpath, index=False)
    regions = aggregate_regions(country)
    rpath = curated / "jodi_region_monthly.parquet"
    regions.to_parquet(rpath, index=False)
    latest = country["month"].max()
    print(f"JODI country table: {len(country)} rows, "
          f"{country['country'].nunique()} countries, through {latest.date()}")
    glob = regions[(regions["region"] == "Global")
                   & (regions["month"] == latest)].iloc[0]
    print(f"Global {latest.date()}: production {glob['production_bcfd']:.1f} Bcf/d, "
          f"deliveries {glob['deliveries_bcfd']:.1f}, balancing item "
          f"{glob['balancing_item_bcfd']:.2f} Bcf/d "
          f"({int(glob['countries_reporting'])} reporters)")


if __name__ == "__main__":
    main()
