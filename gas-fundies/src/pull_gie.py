"""GIE AGSI+ (storage) and ALSI (LNG terminals) daily puller — Europe layer.

Access via the custom.gie connection (see
~/workspace/custom-connectors/custom.gie/CONNECTOR.md): one API key for
both hosts, sent as the x-key header through the dynamic-credentials
surrogate. Rules that matter:
- a browser user agent is mandatory (default Python UA gets a Cloudflare
  403, error 1010, which is NOT a credential failure);
- a bad/missing key returns HTTP 200 with no usable data — validate on
  returned rows, never on status alone;
- all values are strings; "-" means no data -> null, never zero;
- max 30-day window per request, ~60 requests/min shared across hosts;
- data lags ~2 days; values are revised after first publication, so each
  run re-pulls the trailing 10 days.
Licence: GIE attribution is required wherever this data is shown.

Seeds: EU aggregate from 2016-01-01, countries from 2024-01-01; later
runs are incremental. Units as reported: storage in TWh, flows in GWh/d,
LNG inventory in GWh and thousand m3 LNG (dtmi).
"""
from __future__ import annotations

import datetime as dt
import json
import sys
import time
import urllib.request
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "shared"))
sys.path.insert(0, "/opt/muse/skills/custom-connector-setup/bin")
from khriss_data.config import project_data  # noqa: E402
from dynamic_credentials import add_surrogate_to_request, read_json_response  # noqa: E402

BROWSER_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/131.0 Safari/537.36")
HOSTS = {"agsi": "agsi.gie.eu", "alsi": "alsi.gie.eu"}
AGSI_COUNTRIES = ["de", "it", "fr", "nl", "at", "es", "pl", "be", "cz",
                  "hu", "sk", "ro", "bg", "hr", "dk", "ie", "lv", "lt",
                  "pt", "se", "gr"]
ALSI_COUNTRIES = ["es", "fr", "it", "nl", "be", "pl", "pt", "gr", "hr",
                  "lt", "de"]
EU_SEED = dt.date(2016, 1, 1)
COUNTRY_SEED = dt.date(2024, 1, 1)
SLEEP_S = 1.1


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args):
        raise RuntimeError("redirect refused, verify the endpoint")


def fetch(host: str, scope: str, frm: dt.date, to: dt.date) -> list[dict]:
    if scope == "eu":
        q = f"type=eu&from={frm}&to={to}"
    else:
        q = f"country={scope}&from={frm}&to={to}"
    url = f"https://{host}/api?{q}"
    req = urllib.request.Request(url, headers={"User-Agent": BROWSER_UA})
    add_surrogate_to_request(req, "custom.gie", allowed_hosts=[host])
    opener = urllib.request.build_opener(NoRedirect())
    with opener.open(req, timeout=60) as resp:
        payload = read_json_response(resp)
    return payload.get("data") or []


def _num(v) -> float | None:
    if v is None or v == "-" or v == "":
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def parse_agsi(rows: list[dict], scope: str) -> list[dict]:
    out = []
    for r in rows:
        out.append({
            "gas_day": r.get("gasDayStart"),
            "scope": scope,
            "gas_in_storage_twh": _num(r.get("gasInStorage")),
            "full_pct": _num(r.get("full")),
            "injection_gwh": _num(r.get("injection")),
            "withdrawal_gwh": _num(r.get("withdrawal")),
            "working_gas_twh": _num(r.get("workingGasVolume")),
        })
    return out


def parse_alsi(rows: list[dict], scope: str) -> list[dict]:
    out = []
    for r in rows:
        d = r.get("dtmi") or {}
        out.append({
            "gas_day": r.get("gasDayStart"),
            "scope": scope,
            "send_out_gwh": _num(r.get("sendOut")),
            "lng_inventory_gwh": _num(d.get("gwh")),
            "lng_inventory_kcm3": _num(d.get("lng")),
        })
    return out


def pull_series(kind: str, existing: pd.DataFrame | None) -> pd.DataFrame:
    host = HOSTS[kind]
    scopes = ["eu"] + (AGSI_COUNTRIES if kind == "agsi" else ALSI_COUNTRIES)
    today = dt.date.today()
    end = today - dt.timedelta(days=1)
    new_rows: list[dict] = []
    for scope in scopes:
        if existing is not None and not existing[existing["scope"] == scope].empty:
            start = (pd.to_datetime(
                existing[existing["scope"] == scope]["gas_day"]).max().date()
                - dt.timedelta(days=10))
        else:
            start = EU_SEED if scope == "eu" else COUNTRY_SEED
        cur = start
        while cur <= end:
            chunk_end = min(cur + dt.timedelta(days=29), end)
            rows = fetch(host, scope, cur, chunk_end)
            new_rows += (parse_agsi(rows, scope) if kind == "agsi"
                         else parse_alsi(rows, scope))
            time.sleep(SLEEP_S)
            cur = chunk_end + dt.timedelta(days=1)
    new = pd.DataFrame(new_rows)
    if existing is not None and not existing.empty:
        merged = pd.concat([existing, new], ignore_index=True)
    else:
        merged = new
    merged = (merged.dropna(subset=["gas_day"])
              .drop_duplicates(subset=["gas_day", "scope"], keep="last")
              .sort_values(["scope", "gas_day"]).reset_index(drop=True))
    return merged


def main() -> None:
    _, curated = project_data("gas-fundies")
    for kind, fname in [("agsi", "gie_storage_daily.parquet"),
                        ("alsi", "gie_lng_daily.parquet")]:
        path = curated / fname
        existing = pd.read_parquet(path) if path.exists() else None
        df = pull_series(kind, existing)
        df.to_parquet(path, index=False)
        eu = df[df["scope"] == "eu"]
        last = eu.iloc[-1] if not eu.empty else None
        print(f"{kind}: {len(df)} rows, {df['scope'].nunique()} scopes, "
              f"EU through {last['gas_day'] if last is not None else '—'}")


if __name__ == "__main__":
    main()
