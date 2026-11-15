"""Minimal EIA API v2 client shared by all projects.

Credential resolution, in order:
  1. the EIA_API_KEY environment variable
  2. ~/.config/khriss/eia_api_key  (a plain text file containing only the key)
  3. the Muse secure connection `custom.eia`, when the Muse dynamic
     credential helper is importable (path in KH_DYNAMIC_CRED_PATH or the
     default skill location). In this mode requests carry a surrogate
     token that the Muse egress layer swaps for the real key; the key
     itself never touches this process.

No key is ever stored in a repository. If no credential is found,
EIAKeyMissing is raised and callers decide whether their dataset has a
keyless fallback (weekly storage does; the API does not).
"""
from __future__ import annotations

import os
import sys
import time
import urllib.parse
from pathlib import Path

import pandas as pd
import requests

BASE = "https://api.eia.gov/v2"
PAGE = 5000  # EIA v2 max rows per JSON response


class EIAKeyMissing(RuntimeError):
    pass


def get_key() -> str | None:
    key = os.environ.get("EIA_API_KEY", "").strip()
    if key:
        return key
    key_file = Path.home() / ".config" / "khriss" / "eia_api_key"
    if key_file.exists():
        key = key_file.read_text().strip()
        if key:
            return key
    return None


def _surrogate_url(url: str) -> str | None:
    """Return url with the Muse secure-connection surrogate appended,
    or None when the dynamic credential helper is unavailable."""
    helper_dir = os.environ.get(
        "KH_DYNAMIC_CRED_PATH",
        "/opt/muse/skills/custom-connector-setup/bin")
    if helper_dir not in sys.path:
        sys.path.insert(0, helper_dir)
    try:
        from dynamic_credentials import url_with_surrogate_query_param
        return url_with_surrogate_query_param(url, "custom.eia",
                                              allowed_hosts=["api.eia.gov"])
    except Exception:
        return None


class EIAClient:
    def __init__(self, key: str | None = None, pause: float = 0.25):
        self.key = key or get_key()
        self.pause = pause
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "khriss-analytics/1.0"})
        if self.key is None and _surrogate_url(f"{BASE}/") is None:
            raise EIAKeyMissing(
                "No EIA credential found. Set EIA_API_KEY, place the key in "
                "~/.config/khriss/eia_api_key, or connect EIA in Muse. "
                "Register free at https://www.eia.gov/opendata/register.php"
            )

    def _get(self, path: str, params: dict) -> dict:
        # EIA's gateway returns intermittent 504s and reads can time out;
        # both are transient (verified 2026-11-15), so retry with backoff.
        # A 404 is NOT retried: it means the series ID is invalid.
        last_exc: Exception | None = None
        for attempt in range(5):
            try:
                if self.key:
                    p = {**params, "api_key": self.key}
                    r = self.session.get(f"{BASE}/{path}", params=p, timeout=120)
                else:
                    url = f"{BASE}/{path}?{urllib.parse.urlencode(params)}"
                    url = _surrogate_url(url)
                    r = self.session.get(url, timeout=120)
                if r.status_code in (429, 500, 502, 503, 504):
                    raise requests.HTTPError(f"{r.status_code} transient", response=r)
                r.raise_for_status()
                return r.json()
            except (requests.HTTPError, requests.ConnectionError,
                    requests.Timeout) as e:
                if isinstance(e, requests.HTTPError) and \
                        getattr(e, "response", None) is not None and \
                        e.response.status_code in (400, 401, 403, 404):
                    raise
                last_exc = e
                time.sleep(5 * (attempt + 1))
        raise last_exc  # type: ignore[misc]

    def route(self, route: str, frequency: str, data_cols: list[str],
              facets: dict[str, list[str]] | None = None,
              start: str | None = None, end: str | None = None,
              sort_col: str = "period") -> pd.DataFrame:
        """Fetch a faceted v2 route, paginating to exhaustion."""
        frames, offset = [], 0
        while True:
            params: dict = {
                "frequency": frequency,
                "offset": offset,
                "length": PAGE,
                "sort[0][column]": sort_col,
                "sort[0][direction]": "asc",
            }
            for i, col in enumerate(data_cols):
                params[f"data[{i}]"] = col
            for facet, values in (facets or {}).items():
                for j, v in enumerate(values):
                    params[f"facets[{facet}][{j}]"] = v
            if start:
                params["start"] = start
            if end:
                params["end"] = end
            payload = self._get(f"{route}/data/", params)
            resp = payload.get("response", {})
            rows = resp.get("data", [])
            if not rows:
                break
            frames.append(pd.DataFrame(rows))
            total = int(resp.get("total", 0))
            offset += len(rows)
            if offset >= total:
                break
            time.sleep(self.pause)
        if not frames:
            return pd.DataFrame()
        return pd.concat(frames, ignore_index=True)

    def series(self, series_id: str, start: str | None = None,
               end: str | None = None) -> pd.DataFrame:
        """Fetch one legacy series through the v2 seriesid endpoint."""
        params: dict = {}
        if start:
            params["start"] = start
        if end:
            params["end"] = end
        payload = self._get(f"seriesid/{series_id}", params)
        rows = payload.get("response", {}).get("data", [])
        return pd.DataFrame(rows)
