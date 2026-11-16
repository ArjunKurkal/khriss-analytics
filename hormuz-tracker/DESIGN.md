# Hormuz forward collector — design

Approved by Arjun 2026-11-15 (relayed from main chat). Scope: the
ship-level **forward** collector. (The historical-window decisions were
also closed 2026-11-15 — Option 1 with the modelled monthly split, and
trailing-12-month headline with calendar-2025 baseline — and that build
is complete; see README.md.)

## Source

**As built (2026-11-15): Open Waters AIS, `wss://ais.openwaters.io/v1/stream`,
anonymous tier.** It aggregates AISStream itself plus AISHub as upstream
sources (per its own stats/attribution), so the AISStream feed Arjun
approved is inside it. Subscription: `{"type":"subscribe","bbox":[[24.8,54.8,28.2,58.8]]}`
(their bbox order is [minLat, minLon, maxLat, maxLon]). Anonymous limits
observed in the welcome frame: 2 connections, area cap well above our
box. No key is needed, so nothing about this path touches a credential.

**Why not AISStream direct — a proven blocker, not a preference.**
Arjun's AISStream key was deposited as `custom.aisstream` and its
surrogate resolves. But AISStream reads the key inside the WebSocket
subscription *message body*, and the Muse credential-swap layer acts
on HTTP requests (this connection is registered as `bearer_header`) —
it cannot place a credential inside a WS message body. Control trials
on 2026-11-15: subscriptions carrying the surrogate, a bogus key, and
no subscription at all were all closed by AISStream within seconds,
while an echo-server WebSocket through the same egress proxy stayed
open. Same class of blocker as the ERCOT two-credential finding.
The AISStream code path remains in `src/collector.py`
(`HORMUZ_SOURCE=aisstream`) if the auth route ever becomes workable.
This substitution is flagged to Arjun in the side chat; the rest of the
design (bbox, zones, classification, storage) is source-agnostic.

Both sources are free and forward-looking only: no history, no replay —
every day not collected is permanently lost, which is why collection
started on the workable source immediately. Neither publishes a data
licence that permits raw redistribution; we store crossings and
downsampled fixes locally and publish **derived counts only**.
Per-event source attribution (aishub / aisstream / other) is carried
in the Open Waters frames; crossings do not yet record it — noted as a
known gap for a later revision.

## Subscription

- Bounding box: SW (24.8N, 54.8E) to NE (28.2N, 58.8E) — the strait,
  Bandar Abbas / Qeshm, the Fujairah anchorage approaches, and the
  south-eastern Gulf approach lanes.
- Message types: `PositionReport`, `ShipStaticData`.
- The API key travels inside the subscription message (AISStream's
  protocol). The collector places the Muse secure-connection
  **surrogate** (`hsurr:` token for `custom.aisstream`, resolved at run
  time via `dynamic_credentials`, the EIA/ERCOT pattern) in the
  `APIKey` field. The real key never touches this process, the repo, or
  the logs; the subscription payload is never logged.

## Transit detection

Two-zone method, chosen over a single line because satellite/terrestrial
AIS fixes in the strait are sparse and 2026 Gulf AIS is degraded by
GNSS interference — a line-crossing test on consecutive fixes would
miss transits and hallucinate them from spoofed jumps.

- Latitude band for zone assignment: **25.7–27.5N** (the strait).
- West (Gulf side): **lon ≤ 56.45E**. East (Oman side): **lon ≥ 56.85E**.
  Between them is the strait buffer; fixes there are not definitive.
- A crossing = a vessel definitively zoned on one side and then the
  other, zone fixes ≤ **12 h** apart, with a **30 min** per-vessel
  re-cross suppression after a counted crossing.
- Nominal transit line **56.65E**: when the segment between the two zone
  fixes straddles it, crossing time is linearly interpolated; otherwise
  the first fix in the new zone is the crossing time.
- Direction: west→east = **outbound** (leaving the Gulf, eastbound);
  east→west = **inbound** (entering the Gulf, westbound).
- Spoof guard: a segment implying > **50 kn** breaks the track — the
  fix becomes a fresh anchor and the segment cannot create a crossing.
- Positions are downsampled to at most one kept fix per vessel per
  ~minute (55 s). State (per-vessel zone, last zone fix, vessel
  registry, counters) is persisted every flush so restarts do not
  double-count.

## Classification — and its stated limits

From the AIS static ship-type code only:

- 80–89 → `tanker`; 70–79 → `cargo`; 60–69 → `passenger`; 30 →
  `fishing`; 52 → `tug`; etc. (full map in `src/collector.py`).
- **The code does not encode crude vs products vs LNG.** For tankers
  and cargo ships the second digit is an IMDG hazard category, not a
  product; for cargo it does not separate container from bulk either.
  Crossings store the raw code and the broad class, carry the
  uncertainty in a `class_note` field, and `tanker_subtype` is written
  as null — never inferred. A finer split requires a later IMO-keyed
  registry match, which is future work, not part of this collector.
- Crossings recorded before a vessel's static data arrives get their
  broad class re-joined from the latest registry in
  `src/daily_counts.py`.

## Storage (all under `data/`, Parquet)

- `positions/date=YYYY-MM-DD/part-*.parquet` — downsampled fixes.
- `crossings/date=YYYY-MM-DD/crossing-*.parquet` — one file per crossing.
- `vessels/vessels.parquet` — latest static registry snapshot.
- `state/state.json` — resumable collector state.
- `derived/daily_counts.{csv,json}` — from `src/daily_counts.py`; the
  only publication-shaped output.
- `logs/gaps.jsonl` — service starts/stops, connect/disconnect,
  credential-missing periods, and downtime-before-start intervals.
  **Gaps are logged, never backfilled.**
- `logs/status.json`, `logs/collector.log` — health and event log
  (crossings are logged; keys and subscription payloads never are).

## Supervision

Systemd system service `hormuz-collector` (`Restart=always`,
`RestartSec=15`, enabled at boot). The unit source and installer live
in `systemd/` because `/etc` does not survive VM replacement: after a
replacement, run `systemd/install_service.sh` to restore supervision.
The collector itself is restart-safe via `state/state.json`, and the
downtime is recorded in `gaps.jsonl` as `downtime_before_start`.

While the AISStream credential is not resolvable, the service stays up
in a waiting state, re-resolving every 5 minutes and logging
`credential_missing` once per wait episode — collection begins
automatically the moment the key lands, with no restart.

## LNG fleet registry (added 2026-11-15)

Arjun's correction to the audit, accepted on the evidence: AIS type
codes cannot separate tanker subtypes, but **LNG carriers are a small,
enumerable fleet**, so per-ship LNG identification is feasible for the
forward collector via registry matching even though it is not feasible
for crude vs products (thousands of hulls, no free bulk registry — the
modelled monthly split stands for those two).

- **Registry**: `registry/lng_fleet.csv` (committed source of truth),
  built by `src/build_lng_registry.py` into
  `data/registry/lng_fleet.parquet`. Primary key **IMO** (never changes
  for a hull); MMSI and name as secondary keys. **301 hulls** at first
  build: 283 named, 209 with MMSI, Q-Max 14/14, Q-Flex 17 confirmed,
  plus 6 conventional Qatari hulls. Sources: Wikidata (every LNG-typed
  item carrying an IMO), the Wikipedia Q-Max roster, and the
  Nakilat/QatarGas Q-Flex roster — roster names enter ONLY after
  independent verification against a Wikidata IMO record **and** a
  length sanity check (that check caught a false positive: "Al Wajba"
  resolves to a 62 m jackup rig, dropped; the 283–288 m candidates were
  retagged conventional, the 315 m hulls Q-Flex). GIIGNL's fleet report
  and Nakilat's site publish no machine-readable IMO list, and Equasis
  needs an account, so 301 is a floor against the ~700–800 hull world
  fleet — skewed to notable hulls, which for Hormuz is the right skew.
  Known gaps: five Q-Flex names (Al Kharsaah, Al Khattiya, Duhail,
  Fraiha, Mesaieed) have no IMO-bearing public record we could verify.
- **Matching** (collector, at static-data time and again at crossing
  time): IMO > MMSI > normalized name. A matched crossing is recorded
  as `vessel_class=lng_carrier`, `tanker_subtype=lng`, with the match
  key and hull identity in `class_note` — a **measured, named, per-ship
  series**, not a model. Unmatched tankers stay broad-class; nothing is
  inferred.
- **Corroboration / candidate generation** (log-only, never classify):
  (a) a tanker-class hull in the strait feed declaring RAS LAFFAN or
  DAS ISLAND as destination → `logs/lng_candidates.jsonl`;
  (b) berth polling of the Ras Laffan and Das Island terminal boxes via
  the snapshot API every 30 min. **Coverage finding (probed
  2026-11-15): Open Waters' upstreams return zero vessels for the
  entire Qatari coast — snapshot and stream — while the strait box is
  populated.** Berth corroboration is therefore built but currently
  blind; every poll logs its in-box count so the gap stays on record,
  and it starts working if feed coverage appears. Signal (a) and the
  registry match itself carry the load meanwhile.
- **Calibration**: the historical window's LNG layer stays a labelled
  monthly estimate (EIA load-side). Once the forward collector has
  accumulated measured LNG transit rates, those rates calibrate the
  historical estimate's assumptions (loaded exits/day, cargo size) —
  the estimate is never retroactively relabelled as measured.

## General pattern (for other regions)

The LNG machinery is deliberately not Hormuz-specific, because the
same design is the candidate for LNG cargo tracking at other
liquefaction/regas terminals (integration context: the Gas Fundies
global gas S&D, for which this project's LNG output is a feed — see
FEED.md). The pattern has three enumerable parts:

1. **An enumerable fleet**: a curated registry keyed by IMO, built
   from public records with independent verification
   (`src/build_lng_registry.py`). Works for LNG because the fleet is
   ~700–800 hulls; it does not generalize to crude/products tankers.
2. **Enumerable terminals**: geofence boxes per terminal, used for
   berth corroboration and candidate generation.
3. **A crossing geometry**: subscription box, zone lines, and a
   nominal transit line per chokepoint.

Parts 2–3 live in `config/geo.json`, read by the collector at startup
(built-in Hormuz defaults if absent). Part 1 is data, not code. A
second region is therefore a new `geo.json`-shaped config plus a
registry build — and its crossings land in the same feed schema with
their own `region` value. What does NOT generalize: feed coverage
(Open Waters' Qatar-coast gap is a per-region empirical question) and
the direction→loaded-leg inference (a per-region trade fact, kept out
of the feed itself).
