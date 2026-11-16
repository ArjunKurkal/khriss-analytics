"""AISStream forward collector for Strait of Hormuz transits.

Design (see DESIGN.md):
  * Subscribes to AISStream (wss://stream.aisstream.io/v0/stream) for a
    bounding box around the strait.
  * Keeps ~1 position fix per vessel per minute (downsampled from the raw
    firehose) and writes those fixes to Parquet, partitioned by UTC date.
  * Detects transits with a two-zone method: a vessel definitively seen in
    the Gulf-side zone (lon <= 56.45E) and then in the Oman-side zone
    (lon >= 56.85E), or the reverse, inside the strait latitude band
    (25.7-27.5N), with the two zone fixes at most 12 h apart, counts as one
    crossing. The nominal crossing line is 56.65E; when the track segment
    straddles it, the crossing time is linearly interpolated.
  * Direction: west->east = outbound (leaving the Gulf, eastbound);
    east->west = inbound (entering the Gulf, westbound).
  * Classification uses the AIS static ship-type code only. The code
    supports broad classes (tanker / cargo / passenger / ...). It does NOT
    encode crude vs products vs LNG, and it does NOT separate container
    from bulk within cargo. Crossings therefore record the raw code and
    the broad class, with tanker_subtype left explicitly unknown. Any
    finer split must come from a later registry match (IMO), never from
    the AIS code.
  * Storage is crossings + downsampled fixes, never the raw firehose.
    Only derived counts are for publication (AISStream publishes no data
    licence; raw redistribution is not defensible).
  * Gaps (disconnects, downtime, missing credential) are appended to
    logs/gaps.jsonl and are never backfilled.

Credential: resolved at run time, in order:
  1. AISSTREAM_API_KEY environment variable (manual testing only)
  2. the Muse secure connection `custom.aisstream` via the dynamic
     credential helper, which returns an `hsurr:` surrogate. AISStream
     reads the key inside the WebSocket subscription message, so the
     surrogate is placed in that message's APIKey field; the real key
     never touches this process, the repo, or the logs. The subscription
     payload is never logged.
"""
from __future__ import annotations

import asyncio
import json
import logging
import math
import os
import re
import signal
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
DATA = PROJECT / "data"
LOGS = PROJECT / "logs"
POS_DIR = DATA / "positions"
CROSS_DIR = DATA / "crossings"
VESSEL_DIR = DATA / "vessels"
STATE_PATH = DATA / "state" / "state.json"
STATUS_PATH = LOGS / "status.json"
GAPS_PATH = LOGS / "gaps.jsonl"
LNG_REGISTRY_PQ = DATA / "registry" / "lng_fleet.parquet"
LNG_REGISTRY_CSV = PROJECT / "registry" / "lng_fleet.csv"
LNG_CANDIDATES_PATH = LOGS / "lng_candidates.jsonl"

# LNG loading terminals OUTSIDE the strait subscription box, polled via
# the snapshot API for berth corroboration (see DESIGN.md). A tanker-class
# hull berthed here that is NOT in the LNG registry is logged as a
# registry candidate — never silently classified as LNG.
# The terminal set is NOT hardcoded: it comes from config/geo.json
# (filled in by _load_geo_config below); this is the fallback default.

WS_URL = "wss://stream.aisstream.io/v0/stream"
OW_URL = "wss://ais.openwaters.io/v1/stream"
# Live source selection. Default is Open Waters (see DESIGN.md):
# AISStream's key travels inside the WebSocket subscription message,
# where the Muse credential-swap layer cannot place it (the
# custom.aisstream connection is registered as bearer_header; the swap
# layer acts on HTTP requests, not WS message bodies), and AISStream
# closes subscriptions whose APIKey it does not recognise within
# seconds - verified 2026-11-15 with surrogate, bogus, and no-key
# control trials, against an echo-server control that stayed open.
# Open Waters aggregates AISStream itself plus AISHub as upstream
# sources and accepts anonymous subscriptions, so collection can run
# now. Set HORMUZ_SOURCE=aisstream to use the AISStream path if its
# auth route ever becomes workable.
SOURCE = os.environ.get("HORMUZ_SOURCE", "openwaters")


def proxy_url() -> str | None:
    """Egress proxy for the WebSocket connect, when the runtime sets one.

    The systemd service gets this from /etc/profile.d/hatch-egress.sh
    via run_collector.sh; direct egress from this VM is blocked.
    """
    return (os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy")
            or os.environ.get("ALL_PROXY") or os.environ.get("all_proxy"))
# ---------------------------------------------------------------------------
# Geography: config-driven, NOT Hormuz-hardcoded. config/geo.json carries
# the subscription box, the crossing-zone geometry, and the terminal
# geofences for one chokepoint region. A second strait/terminal set is a
# new config of the same shape (plus a fleet registry) — the enumerable-
# fleet + enumerable-terminal pattern generalizes; see DESIGN.md.
# The values below are the built-in Hormuz defaults, used verbatim when
# the config file is absent, so behaviour never depends on the file.
# ---------------------------------------------------------------------------
_DEFAULT_GEO = {
    "region": "hormuz",
    "subscription_bbox": [[24.8, 54.8], [28.2, 58.8]],
    "crossing": {"band_lat": [25.7, 27.5], "west_lon": 56.45,
                 "east_lon": 56.85, "line_lon": 56.65,
                 "max_zone_gap_s": 43200, "min_cross_interval_s": 1800,
                 "max_speed_kn": 50.0},
    "terminals": [
        {"name": "Ras Laffan", "bbox": [25.83, 51.48, 25.99, 51.64]},
        {"name": "Das Island", "bbox": [25.02, 52.84, 25.09, 52.91]},
    ],
}
GEO = _DEFAULT_GEO
_cr = GEO["crossing"]
BBOX = [GEO["subscription_bbox"]]           # AISStream shape: [[sw, ne]]
OW_BBOX = [GEO["subscription_bbox"][0][0], GEO["subscription_bbox"][0][1],
           GEO["subscription_bbox"][1][0], GEO["subscription_bbox"][1][1]]
WEST_LON = _cr["west_lon"]       # at or west of this = definitively Gulf side
EAST_LON = _cr["east_lon"]       # at or east of this = definitively Oman side
LINE_LON = _cr["line_lon"]       # nominal transit line for time interpolation
BAND_LAT = tuple(_cr["band_lat"])  # strait latitude band for zone assignment
MAX_ZONE_GAP_S = _cr["max_zone_gap_s"]        # stale zone fix = not one transit
MIN_CROSS_INTERVAL_S = _cr["min_cross_interval_s"]  # re-cross suppression
MAX_SPEED_KN = _cr["max_speed_kn"]  # faster implied segment = spoof/jump
BERTH_BOXES = {t["name"]: tuple(t["bbox"]) for t in GEO["terminals"]}
DOWNSAMPLE_S = 55         # keep at most one fix per vessel per ~minute
FLUSH_S = 60              # parquet flush cadence
CRED_RETRY_S = 300        # credential re-resolution cadence while waiting

log = logging.getLogger("hormuz-collector")


def _load_geo_config():
    """Overlay config/geo.json onto the built-in defaults, if present."""
    global GEO, BBOX, OW_BBOX, WEST_LON, EAST_LON, LINE_LON, BAND_LAT
    global MAX_ZONE_GAP_S, MIN_CROSS_INTERVAL_S, MAX_SPEED_KN, BERTH_BOXES
    path = PROJECT / "config" / "geo.json"
    try:
        g = json.loads(path.read_text())
    except FileNotFoundError:
        log.info("no config/geo.json — built-in Hormuz defaults in use")
        return
    except Exception as e:
        log.warning("geo config unreadable (%s) — defaults in use", e)
        return
    GEO = {**_DEFAULT_GEO, **g}
    cr = {**_DEFAULT_GEO["crossing"], **(g.get("crossing") or {})}
    GEO["crossing"] = cr
    sb = GEO["subscription_bbox"]
    BBOX = [sb]
    OW_BBOX = [sb[0][0], sb[0][1], sb[1][0], sb[1][1]]
    WEST_LON, EAST_LON, LINE_LON = cr["west_lon"], cr["east_lon"], cr["line_lon"]
    BAND_LAT = tuple(cr["band_lat"])
    MAX_ZONE_GAP_S = cr["max_zone_gap_s"]
    MIN_CROSS_INTERVAL_S = cr["min_cross_interval_s"]
    MAX_SPEED_KN = cr["max_speed_kn"]
    BERTH_BOXES = {t["name"]: tuple(t["bbox"])
                   for t in GEO.get("terminals") or []}
    log.info("geo config loaded: region=%s terminals=%s",
             GEO.get("region"), list(BERTH_BOXES))


_load_geo_config()


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# --------------------------------------------------------------------------
# Classification: AIS ship-type codes (ITU-R M.1371). Broad classes only.
# --------------------------------------------------------------------------

def classify(ship_type: int | None) -> tuple[str, str]:
    """Return (vessel_class, note) for an AIS ship-type code.

    The second digit of cargo (7x) and tanker (8x) codes is a hazardous-
    cargo category (IMDG class A-D / unspecified), NOT a product type:
    it cannot separate crude from products from LNG, and 7x cannot
    separate container from bulk. That uncertainty is stated in the
    returned note rather than hidden behind a guessed subtype.
    """
    if ship_type is None:
        return "unknown", "no static data received for this vessel yet"
    t = int(ship_type)
    if 80 <= t <= 89:
        return "tanker", ("AIS tanker code; crude/products/LNG are NOT "
                          "separable from the AIS code (2nd digit is an "
                          "IMDG hazard category, not a product)")
    if 70 <= t <= 79:
        return "cargo", ("AIS cargo code; container vs bulk vs general "
                         "cargo are NOT separable from the AIS code")
    if 60 <= t <= 69:
        return "passenger", ""
    if t == 30:
        return "fishing", ""
    if t in (31, 32):
        return "towing", ""
    if t == 33:
        return "dredging", ""
    if t == 34:
        return "diving", ""
    if t == 35:
        return "military", ""
    if t == 36:
        return "sailing", ""
    if t == 37:
        return "pleasure", ""
    if 40 <= t <= 49:
        return "high_speed_craft", ""
    if t == 50:
        return "pilot", ""
    if t == 51:
        return "search_and_rescue", ""
    if t == 52:
        return "tug", ""
    if t == 53:
        return "port_tender", ""
    if t == 55:
        return "law_enforcement", ""
    if 20 <= t <= 29:
        return "wing_in_ground", ""
    return "other", f"unmapped AIS ship type code {t}"


# --------------------------------------------------------------------------
# LNG fleet registry: the one tanker subtype that CAN be measured per-ship.
# AIS codes never encode crude/products/LNG, but LNG carriers are a small
# enumerable fleet (~700-800 hulls worldwide) with public registries, and
# an IMO number never changes. The collector joins static data against
# this registry (IMO > MMSI > normalized name); matched crossings are
# recorded as measured LNG transits, by name. Crude vs products gets NO
# such treatment — thousands of hulls, no free bulk registry — the
# modelled monthly split stands for those. Registry built by
# src/build_lng_registry.py (Wikidata + operator rosters, IMO-verified).
# --------------------------------------------------------------------------

def _norm_name(s) -> str:
    return re.sub(r"[^A-Z0-9]", "", (s or "").upper())


class LngRegistry:
    def __init__(self, rows: list[dict]):
        self.by_imo: dict[int, dict] = {}
        self.by_mmsi: dict[int, dict] = {}
        self.by_name: dict[str, dict] = {}
        for r in rows:
            if r.get("imo"):
                self.by_imo.setdefault(int(r["imo"]), r)
            if r.get("mmsi"):
                self.by_mmsi.setdefault(int(r["mmsi"]), r)
            nn = _norm_name(r.get("name"))
            if len(nn) >= 4:
                self.by_name.setdefault(nn, r)
        self.size = len(self.by_imo)

    def match(self, imo, mmsi, name):
        """Return (record, key) with key in imo|mmsi|name, or (None, None)."""
        try:
            imo_i = int(imo) if imo else None
        except (TypeError, ValueError):
            imo_i = None
        if imo_i and imo_i >= 1000000 and imo_i in self.by_imo:
            return self.by_imo[imo_i], "imo"
        try:
            mmsi_i = int(mmsi) if mmsi else None
        except (TypeError, ValueError):
            mmsi_i = None
        if mmsi_i and mmsi_i in self.by_mmsi:
            return self.by_mmsi[mmsi_i], "mmsi"
        nn = _norm_name(name)
        if len(nn) >= 4 and nn in self.by_name:
            return self.by_name[nn], "name"
        return None, None


def load_lng_registry() -> LngRegistry | None:
    """Load the registry if present; absence disables matching, never fatal."""
    try:
        rows = []
        if LNG_REGISTRY_PQ.exists():
            import pyarrow.parquet as pq
            tbl = pq.read_table(LNG_REGISTRY_PQ)
            cols = {c: tbl.column(c).to_pylist() for c in tbl.column_names}
            for i in range(tbl.num_rows):
                rows.append({c: cols[c][i] for c in tbl.column_names})
        elif LNG_REGISTRY_CSV.exists():
            import csv as _csv
            with open(LNG_REGISTRY_CSV) as fh:
                for r in _csv.DictReader(fh):
                    rows.append({
                        "imo": int(r["imo"]) if r["imo"] else None,
                        "mmsi": int(r["mmsi"]) if r["mmsi"] else None,
                        "name": r["name"],
                        "capacity_class": r["capacity_class"],
                        "capacity_m3": int(r["capacity_m3"]) if r["capacity_m3"] else None,
                        "operator": r["operator"],
                    })
        if not rows:
            log.warning("LNG registry empty/missing — LNG matching disabled")
            return None
        reg = LngRegistry(rows)
        log.info("LNG registry loaded: %d hulls (%d IMO, %d MMSI, %d names)",
                 reg.size, len(reg.by_imo), len(reg.by_mmsi), len(reg.by_name))
        return reg
    except Exception as e:
        log.warning("LNG registry load failed (%s) — matching disabled", e)
        return None


def lng_match_for(store: "Store", v: dict):
    """Registry match for a vessel dict, with a corroboration guard on
    NAME matches: a name is not an identifier, and short Gulf names
    collide across fleets (observed 2026-11-15: a 64 m utility vessel
    named AL HAMRA name-matched the ADNOC LNG carrier Al Hamra).
    A name match is accepted only when the vessel's own data does not
    contradict it: length, when known, must be >= 150 m, and the AIS
    ship-type code, when known, must be a tanker code (80-89).
    IMO and MMSI matches are exact identifiers and need no guard."""
    if store.lng is None:
        return None, None
    rec, key = store.lng.match(v.get("imo"), v.get("mmsi"), v.get("name"))
    if rec is None or key != "name":
        return rec, key
    length = v.get("length_m") or v.get("length")
    if length is not None and length < 150:
        return None, None
    code = v.get("ship_type_code") or v.get("type")
    if code and not (80 <= int(code) <= 89):
        return None, None
    return rec, key


def apply_lng(store: "Store", v: dict) -> dict:
    """Tag a vessel-registry entry as an LNG carrier when it matches;
    clear a stale tag when it no longer does (e.g. a name match that
    the corroboration guard now rejects)."""
    if store.lng is None:
        return v
    rec, key = lng_match_for(store, v)
    if rec:
        v["vessel_class"] = "lng_carrier"
        v["lng_match_key"] = key
        v["lng_capacity_class"] = rec.get("capacity_class")
        v["lng_capacity_m3"] = rec.get("capacity_m3")
    elif v.get("lng_match_key"):
        v["vessel_class"] = classify(v.get("ship_type_code"))[0]
        v["lng_match_key"] = None
        v["lng_capacity_class"] = None
        v["lng_capacity_m3"] = None
    return v


def zone_of(lat: float, lon: float) -> str | None:
    """Definitive side of the strait for one fix, or None."""
    if not (BAND_LAT[0] <= lat <= BAND_LAT[1]):
        return None
    if lon <= WEST_LON:
        return "west"
    if lon >= EAST_LON:
        return "east"
    return None  # inside the strait buffer: not definitive


def haversine_nm(lat1, lon1, lat2, lon2) -> float:
    r = 3440.065  # earth radius, nautical miles
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


# --------------------------------------------------------------------------
# Per-vessel track state and crossing detection (pure logic, unit-tested).
# --------------------------------------------------------------------------

@dataclass
class Fix:
    ts: float  # epoch seconds
    lat: float
    lon: float
    sog: float | None = None
    cog: float | None = None


@dataclass
class VesselTrack:
    mmsi: int
    last_kept: Fix | None = None          # last downsampled fix (anywhere)
    last_zone: str | None = None          # 'west' | 'east' | None
    last_zone_fix: Fix | None = None      # fix that set last_zone
    last_cross_ts: float = 0.0

    def add_fix(self, fix: Fix) -> dict | None:
        """Feed one position fix; return a crossing event or None.

        Applies downsampling, spoof-jump rejection, zone assignment and
        the two-zone crossing rule.
        """
        if self.last_kept is not None:
            dt = fix.ts - self.last_kept.ts
            if dt < DOWNSAMPLE_S:
                return None
            if dt > 0:
                dist = haversine_nm(self.last_kept.lat, self.last_kept.lon,
                                    fix.lat, fix.lon)
                if dist / (dt / 3600.0) > MAX_SPEED_KN:
                    # Spoofed or jumped position: break the track segment.
                    # Keep the fix as a fresh anchor but do not let the
                    # segment generate a crossing.
                    self.last_kept = fix
                    z = zone_of(fix.lat, fix.lon)
                    if z is not None:
                        self.last_zone, self.last_zone_fix = z, fix
                    return None
        self.last_kept = fix

        z = zone_of(fix.lat, fix.lon)
        if z is None or self.last_zone is None or z == self.last_zone:
            if z is not None:
                self.last_zone, self.last_zone_fix = z, fix
            return None

        # Zone changed. Check the transit conditions.
        prev = self.last_zone_fix
        self.last_zone, self.last_zone_fix = z, fix
        if prev is None:
            return None
        if fix.ts - prev.ts > MAX_ZONE_GAP_S:
            return None  # too stale to call one transit
        if fix.ts - self.last_cross_ts < MIN_CROSS_INTERVAL_S:
            return None  # suppression window after a counted crossing

        # Crossing time: interpolate the segment prev->fix at LINE_LON
        # when it straddles the line, else use the new-zone fix time.
        cross_ts = fix.ts
        if (prev.lon - LINE_LON) * (fix.lon - LINE_LON) < 0:
            frac = (LINE_LON - prev.lon) / (fix.lon - prev.lon)
            cross_ts = prev.ts + frac * (fix.ts - prev.ts)
        self.last_cross_ts = fix.ts
        direction = "outbound" if prev_zone_is_west(prev, z) else "inbound"
        return {
            "mmsi": self.mmsi,
            "crossing_ts": cross_ts,
            "direction": direction,  # outbound = Gulf -> Oman (eastbound)
            "from_zone": "west" if direction == "outbound" else "east",
            "to_zone": z,
            "prev_fix_ts": prev.ts,
            "next_fix_ts": fix.ts,
        }


def prev_zone_is_west(prev_fix: Fix, new_zone: str) -> bool:
    return new_zone == "east"


# --------------------------------------------------------------------------
# Credential resolution (surrogate pattern, as in shared/khriss_data/eia.py)
# --------------------------------------------------------------------------

def resolve_api_key() -> str | None:
    """Return the value to place in the subscription APIKey field.

    Prefers the Muse secure connection surrogate (`hsurr:` token from
    dynamic_credentials for `custom.aisstream`); the egress layer swaps
    it for the real key. Falls back to AISSTREAM_API_KEY for manual
    testing. Never logs the returned value.
    """
    env = os.environ.get("AISSTREAM_API_KEY", "").strip()
    if env:
        return env
    helper_dir = os.environ.get(
        "KH_DYNAMIC_CRED_PATH",
        "/opt/muse/skills/custom-connector-setup/bin")
    if helper_dir not in sys.path:
        sys.path.insert(0, helper_dir)
    try:
        from dynamic_credentials import dynamic_credential_entry
        entry = dynamic_credential_entry("custom.aisstream")
        surrogate = str(entry.get("surrogate", "")).strip()
        return surrogate or None
    except Exception:
        return None


# --------------------------------------------------------------------------
# Storage: parquet writers, state, gap log, status
# --------------------------------------------------------------------------

class Store:
    def __init__(self):
        import pyarrow as pa  # local import so logic tests need no pyarrow
        self.pa = pa
        self.positions: list[dict] = []
        self.crossings: list[dict] = []
        self.vessels: dict[int, dict] = {}
        self.tracks: dict[int, VesselTrack] = {}
        self.counters = {"messages": 0, "positions_kept": 0,
                         "crossings": 0, "anomalies": 0, "frames": 0,
                         "lng_candidates": 0}
        self.lng = load_lng_registry()
        self._lng_cand_seen: set = set()  # (mmsi, signal, utc-date) dedupe
        self.connected = False
        self.awaiting_credential = True
        self.last_msg_ts: float | None = None
        self.started_ts = time.time()
        self._load_state()

    # -- state persistence (survives restarts; avoids double counting) --
    def _load_state(self):
        try:
            raw = json.loads(STATE_PATH.read_text())
            for mmsi, st in raw.get("tracks", {}).items():
                tr = VesselTrack(mmsi=int(mmsi))
                if st.get("last_zone_fix"):
                    f = st["last_zone_fix"]
                    tr.last_zone_fix = Fix(**f)
                    tr.last_kept = tr.last_zone_fix
                tr.last_zone = st.get("last_zone")
                tr.last_cross_ts = st.get("last_cross_ts", 0.0)
                self.tracks[int(mmsi)] = tr
            self.vessels = {int(k): v for k, v in
                            raw.get("vessels", {}).items()}
            self.counters.update(raw.get("counters", {}))
            last_seen = raw.get("last_msg_ts")
            if last_seen:
                self._gap("downtime_before_start",
                          from_ts=last_seen, to_ts=time.time(),
                          note="gap between previous run's last message "
                               "and this start; never backfilled")
        except FileNotFoundError:
            pass
        except Exception as e:  # corrupt state must not kill the collector
            log.warning("state load failed (%s); starting fresh", e)

    def _save_state(self):
        STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
        tracks = {}
        for mmsi, tr in self.tracks.items():
            f = tr.last_zone_fix
            tracks[str(mmsi)] = {
                "last_zone": tr.last_zone,
                "last_zone_fix": ({"ts": f.ts, "lat": f.lat, "lon": f.lon,
                                   "sog": f.sog, "cog": f.cog} if f else None),
                "last_cross_ts": tr.last_cross_ts,
            }
        payload = {"tracks": tracks,
                   "vessels": {str(k): v for k, v in self.vessels.items()},
                   "counters": self.counters,
                   "last_msg_ts": self.last_msg_ts,
                   "saved_ts": time.time()}
        tmp = STATE_PATH.with_suffix(".tmp")
        tmp.write_text(json.dumps(payload))
        tmp.replace(STATE_PATH)

    # -- LNG registry candidates --------------------------------------
    def lng_candidate(self, rec: dict):
        """Log a tanker that LOOKS like an LNG carrier but is not in the
        registry (berthed at an LNG terminal, or bound for one). These
        are candidates for registry additions — never auto-classified."""
        day = iso(utcnow())[:10]
        dedupe = (rec.get("mmsi"), rec.get("signal"), day)
        if dedupe in self._lng_cand_seen:
            return
        self._lng_cand_seen.add(dedupe)
        LOGS.mkdir(parents=True, exist_ok=True)
        rec = {"logged_at": iso(utcnow()), **rec}
        with LNG_CANDIDATES_PATH.open("a") as fh:
            fh.write(json.dumps(rec) + "\n")
        self.counters["lng_candidates"] += 1
        log.info("LNG CANDIDATE (%s): mmsi=%s name=%s imo=%s len=%s",
                 rec.get("signal"), rec.get("mmsi"), rec.get("name"),
                 rec.get("imo"), rec.get("length_m"))

    # -- gap log ---------------------------------------------------------
    def _gap(self, kind: str, **kw):
        LOGS.mkdir(parents=True, exist_ok=True)
        rec = {"kind": kind, "logged_at": iso(utcnow()), **kw}
        with GAPS_PATH.open("a") as fh:
            fh.write(json.dumps(rec) + "\n")

    # -- parquet flushing -------------------------------------------------
    def flush(self):
        import pyarrow.parquet as pq
        now = utcnow()
        if self.positions:
            rows, self.positions = self.positions, []
            day = now.strftime("%Y-%m-%d")
            d = POS_DIR / f"date={day}"
            d.mkdir(parents=True, exist_ok=True)
            table = self.pa.table({
                "ts": [r["ts"] for r in rows],
                "mmsi": [r["mmsi"] for r in rows],
                "lat": [r["lat"] for r in rows],
                "lon": [r["lon"] for r in rows],
                "sog": [r["sog"] for r in rows],
                "cog": [r["cog"] for r in rows],
                "heading": [r["heading"] for r in rows],
                "nav_status": [r["nav_status"] for r in rows],
            })
            pq.write_table(table, d / f"part-{int(time.time())}.parquet")
        if self.crossings:
            rows, self.crossings = self.crossings, []
            for r in rows:
                day = datetime.fromtimestamp(
                    r["crossing_ts"], timezone.utc).strftime("%Y-%m-%d")
                d = CROSS_DIR / f"date={day}"
                d.mkdir(parents=True, exist_ok=True)
                table = self.pa.table({
                    "crossing_ts": [r["crossing_ts"]],
                    "mmsi": [r["mmsi"]],
                    "direction": [r["direction"]],
                    "from_zone": [r["from_zone"]],
                    "to_zone": [r["to_zone"]],
                    "vessel_name": [r.get("vessel_name")],
                    "imo": [r.get("imo")],
                    "ship_type_code": [r.get("ship_type_code")],
                    "vessel_class": [r.get("vessel_class")],
                    "class_note": [r.get("class_note")],
                    # "lng" ONLY when the fleet-registry match identified
                    # the hull (see class_note); never inferred from AIS.
                    "tanker_subtype": [r.get("tanker_subtype")],
                    "length_m": [r.get("length_m")],
                    "beam_m": [r.get("beam_m")],
                    "destination": [r.get("destination")],
                    "prev_fix_ts": [r["prev_fix_ts"]],
                    "next_fix_ts": [r["next_fix_ts"]],
                })
                pq.write_table(
                    table, d / f"crossing-{r['mmsi']}-{int(r['crossing_ts'])}.parquet")
        if self.vessels:
            VESSEL_DIR.mkdir(parents=True, exist_ok=True)
            vs = list(self.vessels.values())
            table = self.pa.table({
                "mmsi": [v["mmsi"] for v in vs],
                "name": [v.get("name") for v in vs],
                "imo": [v.get("imo") for v in vs],
                "callsign": [v.get("callsign") for v in vs],
                "ship_type_code": [v.get("ship_type_code") for v in vs],
                "vessel_class": [v.get("vessel_class") for v in vs],
                "lng_match_key": [v.get("lng_match_key") for v in vs],
                "lng_capacity_class": [v.get("lng_capacity_class") for v in vs],
                "lng_capacity_m3": [v.get("lng_capacity_m3") for v in vs],
                "length_m": [v.get("length_m") for v in vs],
                "beam_m": [v.get("beam_m") for v in vs],
                "destination": [v.get("destination") for v in vs],
                "updated_ts": [v.get("updated_ts") for v in vs],
            })
            import pyarrow.parquet as pq2
            pq2.write_table(table, VESSEL_DIR / "vessels.parquet")
        self._save_state()
        self._status()

    def _status(self):
        LOGS.mkdir(parents=True, exist_ok=True)
        STATUS_PATH.write_text(json.dumps({
            "updated_at": iso(utcnow()),
            "started_at": iso(datetime.fromtimestamp(
                self.started_ts, timezone.utc)),
            "connected": self.connected,
            "source": SOURCE,
            "awaiting_credential": self.awaiting_credential,
            "last_message_at": (iso(datetime.fromtimestamp(
                self.last_msg_ts, timezone.utc)) if self.last_msg_ts else None),
            "vessels_tracked": len(self.tracks),
            "vessels_known": len(self.vessels),
            "lng_registry_size": self.lng.size if self.lng else 0,
            "lng_vessels_known": sum(
                1 for v in self.vessels.values()
                if v.get("vessel_class") == "lng_carrier"),
            **self.counters,
        }, indent=2))


# --------------------------------------------------------------------------
# Message handling
# --------------------------------------------------------------------------

def _destination_candidate(store: Store, v: dict):
    """Tanker-class hull declaring an LNG terminal as destination but NOT
    in the registry -> candidate for a registry addition (logged only)."""
    if v.get("vessel_class") == "lng_carrier":
        return
    if v.get("vessel_class") not in ("tanker", "unknown", None):
        return
    dest = (v.get("destination") or "").upper()
    term = None
    if "LAFFAN" in dest:
        term = "Ras Laffan"
    elif "DAS" in dest:
        term = "Das Island"
    if term:
        store.lng_candidate({
            "signal": "destination", "terminal": term,
            "mmsi": v.get("mmsi"), "name": v.get("name"),
            "imo": v.get("imo"), "ship_type_code": v.get("ship_type_code"),
            "length_m": v.get("length_m"),
            "destination": v.get("destination"),
        })


def _enrich_crossing(store: Store, event: dict, v: dict, mmsi: int):
    """Fill a crossing event's class fields, with the LNG registry match
    taking precedence over the broad AIS class when it identifies the hull."""
    code = v.get("ship_type_code")
    vclass, note = classify(code)
    subtype = None
    if store.lng is not None:
        rec, key = lng_match_for(store, {**v, "mmsi": mmsi})
        if rec:
            vclass, subtype = "lng_carrier", "lng"
            note = (f"LNG carrier identified by fleet-registry match on "
                    f"{key}: {rec.get('name')} (IMO {rec.get('imo')}, "
                    f"{rec.get('capacity_class')}) — measured per-ship, "
                    f"not modelled")
    event.update({
        "vessel_name": v.get("name"),
        "imo": v.get("imo"),
        "ship_type_code": code,
        "vessel_class": vclass,
        "class_note": note,
        "tanker_subtype": subtype,
        "length_m": v.get("length_m"),
        "beam_m": v.get("beam_m"),
        "destination": v.get("destination"),
    })


def handle_message(store: Store, raw: dict):
    meta = raw.get("MetaData", {})
    mmsi = meta.get("MMSI")
    if not mmsi:
        return
    mtype = raw.get("MessageType")
    msg = raw.get("Message", {})
    store.counters["messages"] += 1
    store.last_msg_ts = time.time()

    if mtype == "ShipStaticData":
        rep = msg.get("ShipStaticData", msg)
        code = rep.get("Type")
        vclass, _ = classify(code)
        dim = rep.get("Dimension", {}) or {}
        length = None
        if dim.get("A") is not None and dim.get("B") is not None:
            length = dim["A"] + dim["B"]
        beam = None
        if dim.get("C") is not None and dim.get("D") is not None:
            beam = dim["C"] + dim["D"]
        entry = {
            "mmsi": int(mmsi),
            "name": (rep.get("Name") or meta.get("ShipName") or "").strip() or None,
            "imo": rep.get("ImoNumber") or None,
            "callsign": rep.get("CallSign") or None,
            "ship_type_code": code,
            "vessel_class": vclass,
            "length_m": length,
            "beam_m": beam,
            "destination": (rep.get("Destination") or "").strip() or None,
            "updated_ts": time.time(),
        }
        store.vessels[int(mmsi)] = apply_lng(store, entry)
        _destination_candidate(store, entry)
        return

    if mtype != "PositionReport":
        return
    rep = msg.get("PositionReport", msg)
    lat, lon = rep.get("Latitude"), rep.get("Longitude")
    if lat is None or lon is None or abs(lat) > 90 or abs(lon) > 180:
        store.counters["anomalies"] += 1
        return
    ts = store.last_msg_ts
    # AISStream MetaData time_utc is the reception time; use it when sane.
    tstr = meta.get("time_utc")
    if tstr:
        try:
            ts = datetime.strptime(
                tstr.strip(), "%Y-%m-%d %H:%M:%S.%f %z").timestamp()
        except Exception:
            try:
                ts = datetime.strptime(
                    tstr.strip(), "%Y-%m-%d %H:%M:%S %z").timestamp()
            except Exception:
                pass
    fix = Fix(ts=ts, lat=float(lat), lon=float(lon),
              sog=rep.get("Sog"), cog=rep.get("Cog"))
    track = store.tracks.setdefault(int(mmsi), VesselTrack(mmsi=int(mmsi)))
    before = track.last_kept
    event = track.add_fix(fix)
    if track.last_kept is fix:  # fix was kept by the downsampler
        store.counters["positions_kept"] += 1
        store.positions.append({
            "ts": fix.ts, "mmsi": int(mmsi), "lat": fix.lat, "lon": fix.lon,
            "sog": fix.sog, "cog": fix.cog,
            "heading": rep.get("TrueHeading"),
            "nav_status": rep.get("NavigationalStatus"),
        })
    if event:
        v = store.vessels.get(int(mmsi), {})
        if not v.get("name"):
            v = {**v, "name": (meta.get("ShipName") or "").strip() or None}
        _enrich_crossing(store, event, v, int(mmsi))
        store.crossings.append(event)
        store.counters["crossings"] += 1
        log.info("CROSSING mmsi=%s dir=%s class=%s at %s",
                 event["mmsi"], event["direction"], event["vessel_class"],
                 iso(datetime.fromtimestamp(event["crossing_ts"],
                                            timezone.utc)))


# --------------------------------------------------------------------------
# Open Waters adapter: normalize its event frames into the same internal
# flow as AISStream messages. Event schema (verified live 2026-11-15):
# {type:"event", time:"...Z", source:"aishub"|"aisstream"|..., mmsi,
#  msg_type:"PositionReport"|"ShipStaticData", lat, lon,
#  message:{decoded AIS fields, AIS-catcher style}}
# --------------------------------------------------------------------------

def _ow_ts(ev: dict) -> float:
    t = ev.get("time")
    if t:
        try:
            return datetime.strptime(
                t.strip(), "%Y-%m-%dT%H:%M:%SZ").replace(
                tzinfo=timezone.utc).timestamp()
        except Exception:
            pass
    return time.time()


def handle_openwaters(store: Store, ev: dict):
    if ev.get("type") != "event":
        return
    mmsi = ev.get("mmsi")
    if not mmsi:
        return
    mmsi = int(mmsi)
    msg = ev.get("message", {}) or {}
    store.counters["messages"] += 1
    store.last_msg_ts = time.time()
    mtype = ev.get("msg_type")

    if mtype == "ShipStaticData":
        code = msg.get("ShipType", msg.get("Type"))
        vclass, _ = classify(code)
        dim = msg.get("Dimension", {}) or {}
        length = beam = None
        if dim.get("A") is not None and dim.get("B") is not None:
            length = dim["A"] + dim["B"]
        if dim.get("C") is not None and dim.get("D") is not None:
            beam = dim["C"] + dim["D"]
        if length is None:
            length = ev.get("length") or msg.get("Length")
        if beam is None:
            beam = ev.get("beam") or msg.get("Beam")
        entry = {
            "mmsi": mmsi,
            "name": (msg.get("Name") or ev.get("name") or "").strip() or None,
            "imo": msg.get("ImoNumber") or ev.get("imo") or None,
            "callsign": msg.get("CallSign") or None,
            "ship_type_code": code,
            "vessel_class": vclass,
            "length_m": length,
            "beam_m": beam,
            "destination": (msg.get("Destination")
                            or "").strip() or None,
            "updated_ts": time.time(),
        }
        store.vessels[mmsi] = apply_lng(store, entry)
        _destination_candidate(store, entry)
        return

    if mtype != "PositionReport":
        return
    lat = ev.get("lat", msg.get("Latitude"))
    lon = ev.get("lon", msg.get("Longitude"))
    if lat is None or lon is None or abs(lat) > 90 or abs(lon) > 180:
        store.counters["anomalies"] += 1
        return
    fix = Fix(ts=_ow_ts(ev), lat=float(lat), lon=float(lon),
              sog=msg.get("Sog", ev.get("sog")),
              cog=msg.get("Cog", ev.get("cog")))
    track = store.tracks.setdefault(mmsi, VesselTrack(mmsi=mmsi))
    event = track.add_fix(fix)
    if track.last_kept is fix:
        store.counters["positions_kept"] += 1
        store.positions.append({
            "ts": fix.ts, "mmsi": mmsi, "lat": fix.lat, "lon": fix.lon,
            "sog": fix.sog, "cog": fix.cog,
            "heading": msg.get("TrueHeading"),
            "nav_status": msg.get("NavigationalStatus"),
        })
    if event:
        v = store.vessels.get(mmsi, {})
        _enrich_crossing(store, event, v, mmsi)
        store.crossings.append(event)
        store.counters["crossings"] += 1
        log.info("CROSSING mmsi=%s dir=%s class=%s at %s",
                 event["mmsi"], event["direction"], event["vessel_class"],
                 iso(datetime.fromtimestamp(event["crossing_ts"],
                                            timezone.utc)))


# --------------------------------------------------------------------------
# Main loop: credential wait -> connect -> stream, with backoff + gap log
# --------------------------------------------------------------------------

async def run(store: Store):
    import websockets

    backoff = 5
    stop = asyncio.Event()

    def _sig(*_):
        stop.set()
    loop = asyncio.get_running_loop()
    for s in (signal.SIGTERM, signal.SIGINT):
        try:
            loop.add_signal_handler(s, _sig)
        except NotImplementedError:
            pass

    store._gap("service_start", pid=os.getpid())

    async def flusher():
        # Independent flush/status cadence, decoupled from message
        # flow. (An earlier build wrapped ws.recv() in
        # asyncio.wait_for; its status appeared to freeze during a
        # quiet-traffic stretch. Root cause was not established -
        # traffic in the box is genuinely sparse at times - but
        # cancelling a pending recv is a known websockets hazard, so
        # the loop now uses async-for + ping/pong liveness instead.)
        while not stop.is_set():
            try:
                await asyncio.wait_for(stop.wait(), timeout=FLUSH_S)
            except asyncio.TimeoutError:
                pass
            store.flush()

    async def registry_seeder():
        # Open Waters' snapshot API carries name/IMO/ship-type for
        # vessels in the box; stream static messages are infrequent,
        # so seed the registry from the snapshot every 30 min. Stream
        # static data, when it arrives, replaces the seeded entry
        # wholesale; the seeder only fills vessels/fields that are
        # missing, never overwrites.
        import urllib.request
        url = ("https://ais.openwaters.io/v1/vessels"
               f"?bbox={OW_BBOX[0]},{OW_BBOX[1]},{OW_BBOX[2]},{OW_BBOX[3]}"
               "&max_age=6h")
        while not stop.is_set():
            try:
                def _fetch():
                    # Via curl: urllib through the egress proxy gets
                    # this endpoint's chunked response truncated at
                    # exactly 32 KiB (observed twice, 2026-11-15);
                    # curl receives it whole.
                    import subprocess
                    out = subprocess.run(
                        ["curl", "-s", "--max-time", "30", url],
                        capture_output=True, timeout=40, check=True)
                    return json.loads(out.stdout)
                data = await asyncio.to_thread(_fetch)
                seeded = 0
                for f in data.get("features", []):
                    p = f.get("properties", {})
                    mmsi = p.get("mmsi")
                    if not mmsi:
                        continue
                    mmsi = int(mmsi)
                    code = p.get("type")
                    vclass, _ = classify(code)
                    entry = {
                        "mmsi": mmsi,
                        "name": (p.get("name") or "").strip() or None,
                        "imo": p.get("imo") or None,
                        "callsign": p.get("callsign") or None,
                        "ship_type_code": code,
                        "vessel_class": vclass,
                        "length_m": p.get("length"),
                        "beam_m": p.get("beam"),
                        "destination": (p.get("destination")
                                        or "").strip() or None,
                        "updated_ts": time.time(),
                    }
                    entry = apply_lng(store, entry)
                    existing = store.vessels.get(mmsi)
                    if existing is None:
                        store.vessels[mmsi] = entry
                        _destination_candidate(store, entry)
                        seeded += 1
                    else:
                        for k, v in entry.items():
                            if existing.get(k) in (None, "") and v:
                                existing[k] = v
                        apply_lng(store, existing)
                if seeded:
                    log.info("registry seeded: +%d vessels (total %d)",
                             seeded, len(store.vessels))
            except Exception as e:
                log.warning("registry seed failed: %s: %s",
                            type(e).__name__, str(e)[:150])
            try:
                await asyncio.wait_for(stop.wait(), timeout=1800)
            except asyncio.TimeoutError:
                pass

    async def berth_poller():
        # Corroboration loop for the LNG registry. Ras Laffan and Das
        # Island sit OUTSIDE the strait subscription box, so poll the
        # snapshot API for those two terminal boxes every 30 min:
        #  - a registry-matched hull berthed there corroborates the
        #    registry (info log only);
        #  - an UNMATCHED tanker-class hull >= 180 m berthed there is a
        #    registry candidate (lng_candidates.jsonl) — logged, never
        #    silently classified as LNG.
        import subprocess

        def _fetch(box):
            lat0, lon0, lat1, lon1 = box
            url = ("https://ais.openwaters.io/v1/vessels"
                   f"?bbox={lat0},{lon0},{lat1},{lon1}&max_age=2h")
            out = subprocess.run(["curl", "-s", "--max-time", "30", url],
                                 capture_output=True, timeout=40, check=True)
            return json.loads(out.stdout)

        while not stop.is_set():
            for term, box in BERTH_BOXES.items():
                try:
                    data = await asyncio.to_thread(_fetch, box)
                    feats = data.get("features", [])
                    # Coverage honesty: Open Waters' upstreams returned
                    # ZERO vessels for the whole Qatari coast on
                    # 2026-11-15 (snapshot and stream probes), while the
                    # strait box is populated — a feed coverage gap, not
                    # an empty port. The count is logged every poll so
                    # the gap stays visible rather than silent; if
                    # coverage appears, corroboration starts working.
                    log.info("berth poll %s: %d vessels in box",
                             term, len(feats))
                    for f in feats:
                        p = f.get("properties", {})
                        mmsi = p.get("mmsi")
                        if not mmsi:
                            continue
                        mmsi = int(mmsi)
                        code = p.get("type")
                        rec = key = None
                        if store.lng is not None:
                            rec, key = lng_match_for(store, {
                                "imo": p.get("imo"), "mmsi": mmsi,
                                "name": (p.get("name") or "").strip() or None,
                                "length_m": p.get("length"),
                                "ship_type_code": code})
                        if rec:
                            log.info("LNG berth corroboration: %s (IMO %s) "
                                     "at %s via %s match",
                                     rec.get("name"), rec.get("imo"),
                                     term, key)
                            continue
                        vclass, _ = classify(code)
                        length = p.get("length")
                        if vclass == "tanker" and \
                                (length is None or length >= 180):
                            store.lng_candidate({
                                "signal": "berth", "terminal": term,
                                "mmsi": mmsi,
                                "name": (p.get("name") or "").strip() or None,
                                "imo": p.get("imo"),
                                "ship_type_code": code,
                                "length_m": length,
                                "sog": p.get("sog"),
                            })
                except Exception as e:
                    log.warning("berth poll %s failed: %s: %s",
                                term, type(e).__name__, str(e)[:150])
            try:
                await asyncio.wait_for(stop.wait(), timeout=1800)
            except asyncio.TimeoutError:
                pass

    flush_task = asyncio.create_task(flusher())
    seed_task = asyncio.create_task(registry_seeder())
    berth_task = asyncio.create_task(berth_poller())
    last_flush = time.time()
    while not stop.is_set():
        if SOURCE == "aisstream":
            key = resolve_api_key()
            if not key:
                if not store.awaiting_credential:
                    store.awaiting_credential = True
                    store._gap("credential_missing",
                               note="custom.aisstream surrogate not "
                                    "resolvable; waiting, retrying "
                                    "periodically")
                store._status()
                try:
                    await asyncio.wait_for(stop.wait(),
                                           timeout=CRED_RETRY_S)
                except asyncio.TimeoutError:
                    pass
                continue
        store.awaiting_credential = False

        disc_from = None
        try:
            if SOURCE == "aisstream":
                ws_cm = websockets.connect(
                    WS_URL, ping_interval=60, ping_timeout=30,
                    max_size=2 ** 22, proxy=proxy_url())
            else:
                ws_cm = websockets.connect(
                    OW_URL, ping_interval=60, ping_timeout=30,
                    max_size=2 ** 22, proxy=proxy_url())
            async with ws_cm as ws:
                if SOURCE == "aisstream":
                    sub = {"APIKey": key,
                           "BoundingBoxes": BBOX,
                           "FilterMessageTypes": ["PositionReport",
                                                  "ShipStaticData"]}
                else:
                    # Open Waters bbox: [minLat, minLon, maxLat, maxLon]
                    sub = {"type": "subscribe", "bbox": [OW_BBOX]}
                await ws.send(json.dumps(sub))  # payload never logged
                store.connected = True
                store._gap("connected", source=SOURCE)
                log.info("connected to %s", SOURCE)
                backoff = 5
                disc_from = time.time()
                async for raw in ws:
                    if stop.is_set():
                        break
                    store.counters["frames"] += 1
                    try:
                        frame = json.loads(raw)
                        if SOURCE == "aisstream":
                            handle_message(store, frame)
                        elif frame.get("type") == "error":
                            log.warning("openwaters error frame: %s",
                                        str(frame)[:200])
                        else:
                            handle_openwaters(store, frame)
                    except Exception as e:
                        log.warning("message handling error: %s", e)
        except asyncio.CancelledError:
            raise
        except Exception as e:
            # Never include the subscription payload or key in errors.
            log.warning("connection error: %s: %s",
                        type(e).__name__, str(e)[:200])
            store._gap("connection_error",
                       error_type=type(e).__name__)
        finally:
            if store.connected and disc_from:
                store._gap("disconnected", from_ts=disc_from,
                           to_ts=time.time(),
                           note="gap in collection; never backfilled")
            store.connected = False
            store.flush()
            last_flush = time.time()
        if stop.is_set():
            break
        try:
            await asyncio.wait_for(stop.wait(), timeout=backoff)
        except asyncio.TimeoutError:
            pass
        backoff = min(backoff * 2, 300)

    flush_task.cancel()
    seed_task.cancel()
    berth_task.cancel()
    store._gap("service_stop")
    store.flush()
    log.info("collector stopped")


def main():
    LOGS.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[logging.FileHandler(LOGS / "collector.log"),
                  logging.StreamHandler(sys.stdout)])
    _load_geo_config()  # re-apply now that logging exists (the
    # import-time call ran before basicConfig, so its line was lost)
    store = Store()
    asyncio.run(run(store))


if __name__ == "__main__":
    main()
