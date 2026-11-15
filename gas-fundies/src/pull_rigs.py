"""Baker Hughes rotary rig count — weekly, by basin and by state.

Reality of this source (verified Nov 2026): Baker Hughes publishes the
count free as spreadsheets on bakerhughesrigcount.gcs-web.com, but the
site bot-blocks scripted requests (HTTP 403 from datacenter IPs) and the
file URLs are hashed per release, so there is no stable URL to poll.

This puller therefore works in two modes:
  1. Manual drop (reliable): any *.xlsx in
     <data_root>/gas-fundies/raw/rigs/ is parsed. Download the current
     "North America Rotary Rig Count" spreadsheet and drop it there;
     re-running this puller refreshes the curated table.
  2. Direct attempt: the Baker Hughes overview page is fetched and any
     spreadsheet links are followed. If the site blocks the request the
     puller logs it and falls back to mode 1 rather than failing.

Output: curated/rigs_weekly.parquet with columns
  week, geography_type (basin|state|national), geography,
  drill_for (Total|Gas|Oil|Misc), rigs_total

The current workbook (verified 2026-11-15, file dated 11-13-2026) has a
"Naming" sheet set: NAM Summary, NAM Breakdown, and history sheets
NAM Yearly / Quarterly / Monthly / Weekly. The Weekly sheet is a tidy
long table (header row found by its 'US_PublishDate' column, after a
blank preamble) with one row per county x basin x drill-for x
trajectory: Country, County, Basin, GOM, DrillFor, Location,
State/Province, Trajectory, Year, Month, US_PublishDate, Rig Count
Value. The parser aggregates that table for US rows. If a future
workbook drops the tidy sheet, the parser falls back to scanning sheets
for a date column plus known basin/state labels.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pandas as pd
import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "shared"))
from khriss_data.config import project_data   # noqa: E402
from khriss_data.io import write_parquet       # noqa: E402

OVERVIEW = "https://bakerhughesrigcount.gcs-web.com/rig-count-overview/"
BASINS = ["Permian", "Haynesville", "Marcellus", "Utica", "Eagle Ford",
          "Williston", "DJ-Niobrara", "Cana Woodford", "Arkoma Woodford",
          "Ardmore Woodford", "Barnett", "Fayetteville", "Granite Wash",
          "Mississippian", "Bakken"]
STATES = ["Alabama", "Alaska", "Arizona", "Arkansas", "California",
          "Colorado", "Florida", "Illinois", "Indiana", "Kansas",
          "Kentucky", "Louisiana", "Michigan", "Mississippi", "Montana",
          "Nebraska", "Nevada", "New Mexico", "New York", "North Dakota",
          "Ohio", "Oklahoma", "Pennsylvania", "South Dakota", "Tennessee",
          "Texas", "Utah", "Virginia", "West Virginia", "Wyoming"]


def try_direct_download(raw_dir: Path) -> Path | None:
    try:
        r = requests.get(OVERVIEW, timeout=30,
                         headers={"User-Agent": "Mozilla/5.0"})
        if r.status_code != 200:
            print(f"direct download: overview returned {r.status_code} "
                  "(site bot-blocks scripted access); using manual drops")
            return None
        links = sorted(set(re.findall(r'href="([^"]+\.xlsx?[^"]*)"', r.text)))
        for link in links:
            if "north" in link.lower() or "rig" in link.lower():
                url = link if link.startswith("http") else \
                    "https://bakerhughesrigcount.gcs-web.com" + link
                f = requests.get(url, timeout=60,
                                 headers={"User-Agent": "Mozilla/5.0"})
                if f.status_code == 200 and len(f.content) > 10_000:
                    out = raw_dir / "baker_hughes_north_america.xlsx"
                    out.write_bytes(f.content)
                    return out
        print("direct download: no spreadsheet link found on overview page")
        return None
    except Exception as exc:  # network errors are expected here; log, don't die
        print(f"direct download failed ({type(exc).__name__}: {exc}); using manual drops")
        return None


def parse_nam_weekly(path: Path) -> pd.DataFrame:
    """Aggregate the tidy 'NAM Weekly' sheet of the current workbook."""
    raw = pd.read_excel(path, sheet_name="NAM Weekly", header=None,
                        engine="openpyxl")
    header_row = None
    for i in range(min(30, len(raw))):
        vals = [str(v).strip() for v in raw.iloc[i]]
        if "US_PublishDate" in vals and "Rig Count Value" in vals:
            header_row = i
            break
    if header_row is None:
        return pd.DataFrame()
    df = raw.iloc[header_row + 1:].copy()
    df.columns = [str(v).strip() for v in raw.iloc[header_row]]
    df = df[df["Country"].astype(str).str.upper().str.startswith("UNITED")]
    df["week"] = pd.to_datetime(df["US_PublishDate"], errors="coerce").dt.date
    df["rigs"] = pd.to_numeric(df["Rig Count Value"], errors="coerce")
    df = df.dropna(subset=["week", "rigs"])
    if df.empty:
        return pd.DataFrame()
    frames = []
    specs = [("national", None), ("basin", "Basin"), ("state", "State/Province")]
    for geo_type, col in specs:
        keys = ["week"] if col is None else ["week", col]
        tot = df.groupby(keys)["rigs"].sum().reset_index()
        tot["geography"] = "United States" if col is None else tot[col].astype(str).str.title()
        tot["geography_type"] = geo_type
        tot["drill_for"] = "Total"
        frames.append(tot[["week", "geography_type", "geography", "drill_for", "rigs"]])
        for drill_for, sub in df.groupby("DrillFor"):
            g = sub.groupby(keys)["rigs"].sum().reset_index()
            g["geography"] = "United States" if col is None else g[col].astype(str).str.title()
            g["geography_type"] = geo_type
            g["drill_for"] = str(drill_for).strip().title()
            frames.append(g[["week", "geography_type", "geography", "drill_for", "rigs"]])
    out = pd.concat(frames, ignore_index=True)
    return out.rename(columns={"rigs": "rigs_total"})


def parse_workbook(path: Path) -> pd.DataFrame:
    try:
        tidy = parse_nam_weekly(path)
        if not tidy.empty:
            return tidy.sort_values(["geography_type", "geography", "week"])
    except Exception as e:  # fall through to the generic scan
        print(f"NAM Weekly parse failed ({type(e).__name__}: {e}); trying generic scan")
    xls = pd.ExcelFile(path)
    rows = []
    for sheet in xls.sheet_names:
        raw = pd.read_excel(xls, sheet_name=sheet, header=None)
        # find a column that parses as many dates -> the week axis
        date_col, best = None, 0
        for c in raw.columns:
            n = pd.to_datetime(raw[c], errors="coerce").notna().sum()
            if n > best:
                date_col, best = c, n
        if date_col is None or best < 4:
            continue
        weeks = pd.to_datetime(raw[date_col], errors="coerce")
        for _, row in raw.iterrows():
            label = str(row.iloc[0]).strip()
            geo_type = None
            if label in BASINS:
                geo_type = "basin"
            elif label in STATES:
                geo_type = "state"
            elif label.lower() in ("total us", "u.s. total", "total united states"):
                geo_type = "national"
            if geo_type is None:
                continue
            # values sit in the columns after the label; align by position
            vals = pd.to_numeric(row.iloc[1:], errors="coerce")
            wk = weeks.iloc[1:1 + len(vals)]
            for w, v in zip(wk, vals):
                if pd.notna(w) and pd.notna(v):
                    rows.append({"week": w.date(), "geography_type": geo_type,
                                 "geography": label, "drill_for": "Total",
                                 "rigs_total": float(v)})
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    return df.drop_duplicates().sort_values(["geography_type", "geography", "week"])


def main() -> None:
    raw, curated = project_data("gas-fundies")
    rig_dir = raw / "rigs"
    rig_dir.mkdir(parents=True, exist_ok=True)
    downloaded = try_direct_download(rig_dir)
    files = [downloaded] if downloaded else sorted(rig_dir.glob("*.xls*"))
    if not files:
        print("No rig-count workbook available. Download the free North "
              "America Rotary Rig Count spreadsheet from Baker Hughes and "
              f"place it in {rig_dir}, then re-run.")
        raise SystemExit(2)
    frames = [parse_workbook(f) for f in files if f is not None]
    frames = [f for f in frames if not f.empty]
    if not frames:
        print("Workbooks found but parser extracted no rows — the workbook "
              "layout changed; inspect the file before trusting any output.")
        raise SystemExit(1)
    df = pd.concat(frames, ignore_index=True).drop_duplicates(
        subset=["week", "geography_type", "geography", "drill_for"], keep="last")
    write_parquet(df, curated / "rigs_weekly.parquet", "rigs_weekly")
    print(f"rigs: {df['week'].min()} to {df['week'].max()}, "
          f"{df['geography'].nunique()} geographies")


if __name__ == "__main__":
    main()
