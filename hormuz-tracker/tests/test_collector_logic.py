"""Offline tests for crossing detection and classification.

Run: ~/workspace/hormuz-tracker/.venv/bin/python tests/test_collector_logic.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from collector import (Fix, LngRegistry, VesselTrack, apply_lng,  # noqa: E402
                       classify, handle_openwaters, load_lng_registry,
                       zone_of)

T0 = 1_763_000_000.0  # arbitrary epoch


def track_with(points):
    tr = VesselTrack(mmsi=123456789)
    events = []
    for dt, lat, lon in points:
        ev = tr.add_fix(Fix(ts=T0 + dt, lat=lat, lon=lon))
        if ev:
            events.append(ev)
    return events


def test_zone():
    assert zone_of(26.6, 56.30) == "west"
    assert zone_of(26.6, 57.10) == "east"
    assert zone_of(26.6, 56.65) is None      # buffer
    assert zone_of(25.1, 56.30) is None      # outside latitude band
    assert zone_of(28.0, 56.30) is None


def test_outbound_crossing():
    ev = track_with([
        (0,    26.6, 56.30),   # west
        (3600, 26.6, 56.65),   # buffer
        (7200, 26.6, 57.10),   # east
    ])
    assert len(ev) == 1 and ev[0]["direction"] == "outbound", ev


def test_inbound_crossing():
    ev = track_with([
        (0,    26.6, 57.10),
        (3600, 26.6, 56.30),
    ])
    assert len(ev) == 1 and ev[0]["direction"] == "inbound", ev


def test_buffer_jitter_no_crossing():
    ev = track_with([
        (0,    26.6, 56.50),
        (3600, 26.6, 56.80),
        (7200, 26.6, 56.55),
    ])
    assert ev == [], ev


def test_stale_zone_gap_no_crossing():
    ev = track_with([
        (0,         26.6, 56.30),
        (13 * 3600, 26.6, 57.10),   # 13 h later: too stale
    ])
    assert ev == [], ev


def test_spoof_jump_no_crossing():
    # A single impossible jump west->east in 60 s (~44 nm in a minute)
    # must not generate a crossing.
    ev = track_with([
        (0,   26.6, 56.30),
        (120, 26.6, 57.10),
    ])
    assert ev == [], ev


def test_round_trip_two_crossings():
    ev = track_with([
        (0,     26.6, 56.30),
        (3600,  26.6, 57.10),   # outbound
        (10800, 26.6, 56.30),   # inbound 2 h later
    ])
    assert [e["direction"] for e in ev] == ["outbound", "inbound"], ev


def test_classify():
    assert classify(81)[0] == "tanker"
    assert classify(71)[0] == "cargo"
    assert classify(65)[0] == "passenger"
    assert classify(52)[0] == "tug"
    assert classify(None)[0] == "unknown"
    # The uncertainty must be stated, not hidden.
    assert "NOT" in classify(81)[1] and "LNG" in classify(81)[1]
    assert "NOT" in classify(71)[1]


def _fake_store():
    class FakeStore:
        pass
    s = FakeStore()
    s.counters = {"messages": 0, "positions_kept": 0, "crossings": 0,
                  "anomalies": 0, "frames": 0, "lng_candidates": 0}
    s.last_msg_ts = None
    s.tracks, s.vessels = {}, {}
    s.positions, s.crossings = [], []
    s.lng = load_lng_registry()
    s.candidates = []
    s.lng_candidate = lambda rec: s.candidates.append(rec)
    return s


def test_lng_registry_match_priority():
    reg = LngRegistry([
        {"imo": 9337755, "mmsi": 538003212, "name": "Mozah",
         "capacity_class": "Q-Max", "capacity_m3": 266000, "operator": ""},
        {"imo": 1111111, "mmsi": 222222222, "name": "Other Ship",
         "capacity_class": "conventional", "capacity_m3": None,
         "operator": ""},
    ])
    # IMO wins even when MMSI/name point at a different hull.
    rec, key = reg.match(9337755, 222222222, "Other Ship")
    assert key == "imo" and rec["name"] == "Mozah"
    rec, key = reg.match(None, 538003212, None)
    assert key == "mmsi" and rec["imo"] == 9337755
    rec, key = reg.match(None, None, "  mozah ")
    assert key == "name" and rec["imo"] == 9337755
    rec, key = reg.match(9999999, 999999999, "Not A Ship")
    assert rec is None and key is None
    # Bogus IMO 0 / placeholder must never match.
    rec, _ = reg.match(0, None, None)
    assert rec is None


def test_lng_crossing_end_to_end():
    """Mozah static + west->east fixes = one MEASURED lng_carrier crossing."""
    s = _fake_store()
    assert s.lng is not None and s.lng.size > 250, "real registry required"
    handle_openwaters(s, {
        "type": "event", "time": "2026-11-15T00:00:00Z",
        "mmsi": 538003212, "msg_type": "ShipStaticData",
        "message": {"ShipType": 84, "Name": "MOZAH",
                    "ImoNumber": 9337755, "Destination": "RAS LAFFAN"},
    })
    v = s.vessels[538003212]
    assert v["vessel_class"] == "lng_carrier", v
    assert v["lng_match_key"] == "imo"
    assert v["lng_capacity_class"] == "Q-Max"
    assert s.candidates == []  # matched hulls are not candidates
    for i, lon in enumerate([56.30, 56.50, 56.90, 57.10]):
        handle_openwaters(s, {
            "type": "event",
            "time": f"2026-11-15T0{i}:00:00Z",
            "mmsi": 538003212, "msg_type": "PositionReport",
            "lat": 26.6, "lon": lon, "message": {"Sog": 12.0},
        })
    assert len(s.crossings) == 1, s.crossings
    ev = s.crossings[0]
    assert ev["vessel_class"] == "lng_carrier"
    assert ev["tanker_subtype"] == "lng"
    assert ev["direction"] == "outbound"
    assert "registry match on imo" in ev["class_note"]


def test_name_match_guard_rejects_small_namesake():
    """The AL HAMRA defect (2026-11-15): a 64 m utility vessel sharing
    an LNG carrier's name must NOT be tagged by a name match."""
    from collector import lng_match_for
    s = _fake_store()
    small = {"imo": 9829174, "mmsi": 470525000, "name": "AL HAMRA",
             "length_m": 64, "ship_type_code": 0}
    rec, key = lng_match_for(s, small)
    assert rec is None, (rec, key)
    # Same name on a full-size tanker-coded hull: accepted.
    big = {"imo": None, "mmsi": 470999999, "name": "AL HAMRA",
           "length_m": 290, "ship_type_code": 84}
    rec, key = lng_match_for(s, big)
    assert rec is not None and key == "name"
    # IMO match needs no corroboration.
    exact = {"imo": 9337755, "mmsi": 1, "name": "WHATEVER",
             "length_m": 10, "ship_type_code": 0}
    rec, key = lng_match_for(s, exact)
    assert key == "imo"


def test_unmatched_tanker_stays_broad_and_candidates():
    s = _fake_store()
    handle_openwaters(s, {
        "type": "event", "time": "2026-11-15T00:00:00Z",
        "mmsi": 999999999, "msg_type": "ShipStaticData",
        "message": {"ShipType": 82, "Name": "MYSTERY TANKER",
                    "ImoNumber": 9999999, "Destination": "RAS LAFFAN"},
    })
    v = s.vessels[999999999]
    assert v["vessel_class"] == "tanker"  # NOT silently upgraded
    assert len(s.candidates) == 1
    assert s.candidates[0]["signal"] == "destination"
    assert s.candidates[0]["terminal"] == "Ras Laffan"


def test_geo_config_matches_legacy_constants():
    import collector as c
    assert c.BAND_LAT == (25.7, 27.5)
    assert (c.WEST_LON, c.EAST_LON, c.LINE_LON) == (56.45, 56.85, 56.65)
    assert c.OW_BBOX == [24.8, 54.8, 28.2, 58.8]
    assert set(c.BERTH_BOXES) == {"Ras Laffan", "Das Island"}


def test_lng_feed_aggregate():
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
    from lng_feed import aggregate
    rows = [
        {"date": "2026-12-01", "month": "2026-12", "direction": "outbound",
         "capacity_class": "Q-Max", "capacity_m3": 266000,
         "imo": 9337755, "mmsi": 1, "vessel_name": "MOZAH"},
        {"date": "2026-12-01", "month": "2026-12", "direction": "inbound",
         "capacity_class": "Q-Max", "capacity_m3": 266000,
         "imo": 9337755, "mmsi": 1, "vessel_name": "MOZAH"},
        {"date": "2026-12-02", "month": "2026-12", "direction": "outbound",
         "capacity_class": "Q-Flex", "capacity_m3": 217000,
         "imo": 9360879, "mmsi": 2, "vessel_name": "AL HUWAILA"},
    ]
    d = aggregate(rows, "date")
    assert d[0]["transits_total"] == 2 and d[0]["outbound"] == 1
    assert d[0]["capacity_m3_outbound"] == 266000
    assert d[1]["by_capacity_class"] == {"Q-Flex": 1}
    m = aggregate(rows, "month")
    assert m[0]["transits_total"] == 3 and m[0]["distinct_vessels"] == 2
    assert aggregate([], "date") == []


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print("ok", fn.__name__)
    print(f"{len(fns)} tests passed")
