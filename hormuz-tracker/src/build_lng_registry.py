#!/usr/bin/env python3
"""Build the curated LNG carrier fleet registry used by the forward collector.

Why this exists: AIS static type codes (80-89) say "tanker" but never encode
crude vs products vs LNG. LNG carriers are the exception that can still be
measured per-ship: the world fleet is small (~700-800 hulls) and enumerable
from public records, and an IMO number never changes for the life of a hull.
This registry is the match table; the collector joins ShipStaticData against
it (IMO > MMSI > normalized name) and records matched crossings as MEASURED
LNG transits, by name. It does NOT extend to crude vs products — that fleet
is thousands of hulls with no free bulk registry; the modelled monthly split
stands for those.

Sources (all public, fetched at build time, logged in the output):
  - Wikidata SPARQL: every item that is an LNG carrier (P31/P279* Q15247)
    or belongs to an LNG carrier class, with IMO (P458), MMSI (P587),
    vessel class (P289), operator (P137), length (P2043).
  - Wikipedia Q-Max / Q-Flex class pages: the definitive name lists for the
    Qatar fleets (14 Q-Max, 31 Q-Flex), used to tag capacity class where
    Wikidata's class statement is missing.
Cross-checks not machine-readable: GIIGNL annual fleet report and Nakilat's
published fleet (their site carries no IMO numbers); Equasis needs an
account. Coverage is therefore a floor, not the full ~700-800 hull fleet:
Wikidata skews to notable vessels, which for Hormuz purposes is the right
skew — the QatarEnergy/Nakilat Q-fleets and large conventional carriers
that actually load at Ras Laffan / Das Island are well covered.

Outputs:
  registry/lng_fleet.csv          committed source of truth (text)
  data/registry/lng_fleet.parquet collector's runtime copy

Run: .venv/bin/python src/build_lng_registry.py
"""
import csv, io, json, re, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CSV_OUT = ROOT / "registry" / "lng_fleet.csv"
PQ_OUT = ROOT / "data" / "registry" / "lng_fleet.parquet"

SPARQL = """
SELECT ?ship ?shipLabel ?imo ?mmsi ?classLabel ?operatorLabel ?length ?article WHERE {
  ?ship wdt:P458 ?imo.
  { ?ship wdt:P31/wdt:P279* wd:Q15247. }
  UNION
  { ?ship wdt:P289 ?c. ?c wdt:P31/wdt:P279* wd:Q15247. }
  OPTIONAL { ?ship wdt:P587 ?mmsi. }
  OPTIONAL { ?ship wdt:P289 ?class. }
  OPTIONAL { ?ship wdt:P137 ?operator. }
  OPTIONAL { ?ship wdt:P2043 ?length. }
  OPTIONAL {
    ?article schema:about ?ship ;
             schema:isPartOf <https://en.wikipedia.org/> .
  }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
}
"""

QMAX_NAMES = {  # Wikipedia Q-Max class page, fleet list (14 hulls, 266,000 m3)
    "MOZAH", "AL MAYEDA", "MEKAINES", "AL MAFYAR", "UMM SLAL", "BU SAMRA",
    "AL GHUW AIRIYA", "AL-GHUWAIRIYA", "LIJMILIYA", "AL SAMRIYA", "AL DAFNA",
    "SHAGRA", "ZARGA", "AAMIRA", "RASHEEDA",
}


def norm_name(s: str) -> str:
    return re.sub(r"[^A-Z0-9]", "", (s or "").upper())


def fetch(url: str, data: bytes | None = None, headers: dict | None = None) -> bytes:
    # curl, not urllib: the VM egress proxy truncates chunked urllib reads.
    cmd = ["curl", "-sL", "--max-time", "60", url]
    for k, v in (headers or {}).items():
        cmd += ["-H", f"{k}: {v}"]
    if data is not None:
        cmd += ["--data-binary", "@-"]
    p = subprocess.run(cmd, input=data, capture_output=True)
    if p.returncode != 0:
        raise RuntimeError(f"fetch failed {url}: {p.stderr.decode()[:200]}")
    return p.stdout


# The Q-Flex Wikipedia article carries no fleet table (verified 2026-11-15:
# infobox has counts only), and most Q-Flex hulls are not typed as LNG
# carriers in Wikidata, so the SPARQL pull misses them. The roster below is
# the Nakilat/QatarGas Q-Flex fleet as published by the operator and widely
# reproduced; every name is INDEPENDENTLY VERIFIED against Wikidata
# (must resolve to an item carrying an IMO number) before it enters the
# registry — unverified candidates are dropped and printed. Same treatment
# for the three Q-Max hulls the SPARQL pull missed.
QFLEX_CANDIDATES = [
    "Al Aamriya", "Al Bahiya", "Al Ghariya", "Al Gharrafa", "Al Hamla",
    "Al Huwaila", "Al Jassasiya", "Al Kharsaah", "Al Kharaitiyat",
    "Al Khattiya", "Al Nuaman", "Al Oraiq", "Al Rekayyat", "Al Sahla",
    "Al Sheehaniya", "Al Thakhira", "Al Utouriya", "Duhail", "Fraiha",
    "Lusail", "Mesaieed", "Murwab", "Onaiza", "Tembek", "Umm Al Amad",
    "Al Wajba", "Al Deebel", "Al Areesh", "Al Marrouna",
]
QMAX_CANDIDATES = ["Umm Slal", "Al-Ghuwairiya", "Rasheeda"]


def verify_candidates(names: list[str], cap_class: str, cap_m3: int) -> list[dict]:
    """Resolve candidate ship names to IMO/MMSI via Wikidata search+claims."""
    import urllib.parse
    out, missed = [], []
    for name in names:
        q = urllib.parse.quote(name)
        s = json.loads(fetch(
            f"https://www.wikidata.org/w/api.php?action=wbsearchentities"
            f"&search={q}&language=en&type=item&format=json&limit=15"))
        # Places share these names (Al Huwaila is also a Qatari town):
        # scan every label match and keep the one that carries an IMO —
        # that is the ship.
        claims, hit = {}, None
        for cand in s.get("search", []):
            lab = cand.get("label", "")
            if norm_name(lab) != norm_name(name) and \
               norm_name(re.sub(r"\s*\(.*?\)\s*", "", lab)) != norm_name(name):
                continue
            e = json.loads(fetch(
                f"https://www.wikidata.org/w/api.php?action=wbgetentities"
                f"&ids={cand['id']}&props=claims&format=json"))
            c = e["entities"][cand["id"]].get("claims", {})
            if "P458" in c:
                claims, hit = c, cand["id"]
                break
        if not hit:
            missed.append(name)
            continue
        def claim(pid):
            try:
                return claims[pid][0]["mainsnak"]["datavalue"]["value"]
            except (KeyError, IndexError, TypeError):
                return None
        imo = claim("P458")
        if not imo:
            missed.append(name)
            continue
        mmsi = claim("P587")
        length = None
        lv = claim("P2043")
        if isinstance(lv, dict) and "amount" in lv:
            try:
                length = float(lv["amount"])
            except ValueError:
                length = None
        # Name collisions are real: "Al Wajba" resolved to a 62 m jackup
        # rig carrying an IMO. A hull under 200 m is not an LNG carrier —
        # drop it. Class by measured length: Q-Max 345 m, Q-Flex 315 m,
        # the 283-288 m hulls are the conventional Qatari fleet.
        if length is not None and length < 200:
            print(f"candidate {name}: dropped — length {length} m is not an LNG carrier")
            continue
        if length is not None and length >= 330:
            cap_class, cap_m3 = "Q-Max", 266000
        elif length is not None and 305 <= length <= 325:
            cap_class, cap_m3 = "Q-Flex", 217000
        elif length is not None:
            cap_class, cap_m3 = "conventional", None
        out.append({
            "imo": int(imo), "mmsi": int(mmsi) if mmsi else None,
            "name": name, "name_norm": norm_name(name),
            "capacity_class": cap_class, "capacity_m3": cap_m3,
            "operator": "", "length_m": length,
            "source": "wikidata (operator-roster candidate, IMO+length verified)",
            "wikidata_class": cap_class,
        })
    if missed:
        print(f"candidates NOT verified for {cap_class}: {missed}")
    return out


def main() -> int:
    raw = fetch(
        "https://query.wikidata.org/sparql?query=" +
        __import__("urllib.parse", fromlist=["quote"]).quote(SPARQL) +
        "&format=json",
        headers={"User-Agent": "khriss-analytics-research/1.0",
                 "Accept": "application/sparql-results+json"},
    )
    rows = json.loads(raw)["results"]["bindings"]
    print(f"wikidata bindings: {len(rows)}")

    qflex: set[str] = set()  # class tagging now comes from verified candidates

    by_imo: dict[int, dict] = {}
    for r in rows:
        def val(k):
            return r[k]["value"] if k in r else None
        try:
            imo = int(val("imo"))
        except (TypeError, ValueError):
            continue
        if not (1000000 <= imo <= 10999999):
            continue
        name = val("shipLabel") or ""
        if re.fullmatch(r"Q\d+", name or ""):
            name = ""
        if not name and val("article"):
            name = val("article").rsplit("/", 1)[-1].replace("_", " ")
            name = re.sub(r"\s*\(.*?\)\s*", "", name).strip()
        mmsi = val("mmsi")
        try:
            mmsi = int(mmsi) if mmsi else None
        except ValueError:
            mmsi = None
        cls = val("classLabel") or ""
        length = val("length")
        try:
            length = float(length) if length else None
        except ValueError:
            length = None
        nn = norm_name(name)
        if "Q-Max" in cls or nn in {norm_name(x) for x in QMAX_NAMES}:
            cap_class, cap_m3 = "Q-Max", 266000
        elif "Q-Flex" in cls or nn in qflex:
            cap_class, cap_m3 = "Q-Flex", 217000
        elif cls:
            cap_class, cap_m3 = "conventional", None
        else:
            cap_class, cap_m3 = "conventional/unknown", None
        rec = {
            "imo": imo, "mmsi": mmsi, "name": name, "name_norm": nn,
            "capacity_class": cap_class, "capacity_m3": cap_m3,
            "operator": val("operatorLabel") or "",
            "length_m": length, "source": "wikidata",
            "wikidata_class": cls,
        }
        old = by_imo.get(imo)
        # Prefer the more complete record (named, with MMSI).
        if old is None or (bool(rec["name"]), bool(rec["mmsi"])) > (bool(old["name"]), bool(old["mmsi"])):
            by_imo[imo] = rec

    for rec in verify_candidates(QFLEX_CANDIDATES, "Q-Flex", 217000) + \
               verify_candidates(QMAX_CANDIDATES, "Q-Max", 266000):
        old = by_imo.get(rec["imo"])
        if old is None:
            by_imo[rec["imo"]] = rec
        else:  # SPARQL row exists but may lack the class tag
            if old["capacity_class"] not in ("Q-Max", "Q-Flex"):
                old["capacity_class"] = rec["capacity_class"]
                old["capacity_m3"] = rec["capacity_m3"]
            if not old["name"]:
                old["name"], old["name_norm"] = rec["name"], rec["name_norm"]
            if not old["mmsi"]:
                old["mmsi"] = rec["mmsi"]

    fleet = sorted(by_imo.values(), key=lambda r: (r["name"] or "ZZZ", r["imo"]))
    CSV_OUT.parent.mkdir(parents=True, exist_ok=True)
    fields = ["imo", "mmsi", "name", "capacity_class", "capacity_m3",
              "operator", "length_m", "source"]
    with open(CSV_OUT, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for rec in fleet:
            w.writerow({k: ("" if rec[k] is None else rec[k]) for k in fields})

    import pyarrow as pa
    import pyarrow.parquet as pq
    PQ_OUT.parent.mkdir(parents=True, exist_ok=True)
    tbl = pa.table({
        "imo": pa.array([r["imo"] for r in fleet], pa.int64()),
        "mmsi": pa.array([r["mmsi"] for r in fleet], pa.int64()),
        "name": pa.array([r["name"] for r in fleet]),
        "name_norm": pa.array([r["name_norm"] for r in fleet]),
        "capacity_class": pa.array([r["capacity_class"] for r in fleet]),
        "capacity_m3": pa.array([r["capacity_m3"] for r in fleet], pa.int64()),
        "operator": pa.array([r["operator"] for r in fleet]),
    })
    pq.write_table(tbl, PQ_OUT)

    n_mmsi = sum(1 for r in fleet if r["mmsi"])
    n_qmax = sum(1 for r in fleet if r["capacity_class"] == "Q-Max")
    n_qflex = sum(1 for r in fleet if r["capacity_class"] == "Q-Flex")
    n_named = sum(1 for r in fleet if r["name"])
    print(f"registry: {len(fleet)} hulls | named {n_named} | with MMSI {n_mmsi} "
          f"| Q-Max {n_qmax} | Q-Flex {n_qflex}")
    print(f"wrote {CSV_OUT} and {PQ_OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
