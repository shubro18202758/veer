# Veer — samples

A small, curated set of Veer's data: files copied from this repository (a few of them excerpted), one synthetic
OSINT signal serialised from the test kit, and GET responses read back from a **private sandbox stack**. Use them to
see the shapes Veer works with without running anything, or to compare against a stack of your own.

Nothing here is live data. Every file says what it is:

- **Copied** files are byte-for-byte copies of a file in `VVIP/` (the source path is listed below).
- **Excerpted** files keep the source's structure and cut long lists; an `_excerpt` key says what was cut.
- **Sandbox samples** (`api/`) are wrapped in an envelope: `_sample` (what, where, when, what was trimmed),
  `request`, `status` and `response`. The `response` is the service's body as it was returned, apart from the
  trimming the envelope states. They were captured with GET requests only, on 2026-10-27, from a private sandbox
  stack whose store holds emulated, simulated and synthetic data — never from the live system.

The data words follow the interface: **emulated** (produced by Veer's event emulator: camera reads, units, events,
the demo stolen vehicle), **simulated** (the synthetic traffic feed), **synthetic** (written for tests, fictional
publishers), **modelled** (model output). The plate `GJ27EM9001` that appears in several files is the **emulated
stolen vehicle of the exercise** (demo FIR 4401/2026); every emulated plate carries the `EM` series marker.

For the full description of every dataset and test, see
[`docs/SAMPLE_DATA_AND_TESTS.md`](../docs/SAMPLE_DATA_AND_TESTS.md).

---

## Files

### `road-network/`

| File | Size | What it is | Source |
|---|---|---|---|
| `osm_network.excerpt.json` | 40 KB | **Excerpt** of the road-network evidence file: 5 of the 49 segments (1015 Nehru Bridge Road, 1012 Gandhi Road, 1013 Swami Vivekananda Road, 1001 Ashram Road (South), 1005 Relief Road), their 6 junctions, their signal programs, 4 of the 28 emulated camera sites and 1 of the 18 agency stations. Each segment carries its traced `line` (`[lon, lat]` pairs), OSM way and node ids, names in the OSM data and validation metrics (`hausdorff_m`, `length_m`, `osm_length_m`). The `network` block keeps the whole network's figures (49 segments, 34 junctions, 198 movements, 186 graph edges, 192.04 km). | `VVIP/scripts/data/osm_network.json` (389 KB), written by `VVIP/scripts/gen_osm_network.py` |
| `NOTICE.md` | 4.6 KB | **Copy** of the seed's OpenStreetMap notice. The road geometry is © OpenStreetMap contributors, ODbL 1.0; the notice travels with the excerpt. (Its file paths are relative to `VVIP/services/corridor-store/`.) | `VVIP/services/corridor-store/seed/NOTICE.md` |

### `emulator/`

| File | Size | What it is | Source |
|---|---|---|---|
| `use-case.rath_yatra_monsoon_ambulance.json` | 6.5 KB | **Copy** of one entry of the emulator's use-case library: the flagship composite — the Rath Yatra procession, a monsoon burst and one 108 ambulance — with its route as segment ids, departure, horizon, seed, weather, forced events and closure policy. Emulated: the emulator injects these causes into the real stack; every outcome is the stack's own. | the `rath_yatra_monsoon_ambulance` entry of `VVIP/services/event-emulator/src/event_emulator/use_case_library.json` (10 entries) |

### `osint/`

| File | Size | What it is | Source |
|---|---|---|---|
| `signal.sg-highway-5.json` | 2.0 KB | **Synthetic** OSINT signal, already redacted: a news-aggregator replica from the fictional publisher `news-b.example` reporting a crowd assaulting a driver after the SG Highway crash; the driver's name reads `[PERSON]` and `pii_redactions` is 1. The signal-level fixtures are Python constructors, so this one was serialised from `sg_highway_signals()[4]`; the `_fixture` key says so. `license` and `redistributable` describe the source class the replica imitates, not this text, which the project wrote. | `VVIP/services/osint-common/src/osint_common/testing.py` |
| `situation.robbery.json` | 2.1 KB | **Copy** of a synthetic OSINT situation in the city-entity wire shape: the reported robbery at Odhav Ring Road Circle (junction 11), `NEWS-REPORTED`, credibility 0.60, a second-order flag "On a 108 route", the summary redacted ("Jeweller Mr [PERSON], [AGE], …"), source links withheld ("may name a person"). | `VVIP/services/command-deck/tests/fixtures/osint/robbery.json` |

### `contract/` — a contract fixture pair

| File | Size | What it is | Source |
|---|---|---|---|
| `interception-plan.request.json` | 0.8 KB | The **request** half: the manifest entry that maps `GET /api/v1/events/4508d86d-…/interception-plan?max_cost_sec=600` to its recorded response (status 200, origin `live`), with the manifest's recording time and the command that replays it. | `VVIP/services/command-deck/tests/contract/fixtures/manifest.json` |
| `interception-plan.response.json` | 2.8 KB | The **response** half, a **copy**: the choke-junction ranking for a pursuit of the emulated stolen vehicle, off its latest emulated read (`source: emulated_anpr`), recorded read-only from the deployed oracle on 2026-10-22. | `VVIP/services/command-deck/tests/contract/fixtures/interception_plan.json` |

The pursuit it ranks for is a 2026-10-18 rehearsal (see the note in `api/oracle.events-active.json`).

### `decision-support/`

| File | Size | What it is | Source |
|---|---|---|---|
| `dss_road_accident.json` | 20.6 KB | **Copy** of a synthetic `DecisionSupport` document for the SG Highway road accident: the situation (redacted summary, credibility 0.65, `NEWS-REPORTED`), nine criteria with their AHP weights and honest labels ("fixed prior … not simulated", "nominal time … not a unit ETA"), six courses of action with their scores and wargame figures, the recommendation, provenance and the human gate. State `proposed`. Validated against the frozen C-U contract by `VVIP/services/command-deck/tests/test_dss_fixtures.py`. | `VVIP/services/command-deck/tests/fixtures/dss/dss_road_accident.json` |

### `api/` — sandbox samples (GET only, 2026-10-27)

| File | Request | What it shows |
|---|---|---|
| `oracle.health.json` | `GET /health` (traffic-oracle) | Ingest health: the subjects it consumes (`corridor.traffic.live` from the simulated city feed, the emulated subjects), rows written, cache keys (49). |
| `oracle.spatial-segments.json` | `GET /api/v1/spatial/segments?min_lon=72.55&min_lat=23.0&max_lon=72.62&max_lat=23.05` | Road segments in a bounding box with their GeoJSON line and `geometry_basis: osm` (3 of the 21 returned). |
| `oracle.city-entities.json` | `GET /api/v1/city/entities` | The fused city picture: one entity of each kind (event, vehicle, sighting, camera, junction, recommendation, anomaly; 110 in all). Labels arrive masked (`GJ27EM•••1`); junction signal state is labelled "planned (signal program)", never a live phase. |
| `oracle.events-active.json` | `GET /api/v1/events/active` | The board: one `vehicle_pursuit` in planning — a rehearsal pursuit of 2026-10-18 that the sandbox copy still holds (on the live stack it was cancelled; today such a pursuit can be opened only from an approved `R_STOLEN_SIGHTING`). |
| `oracle.corridor-summary.json` | `GET /api/v1/corridor/summary` | 49 segments, `provenance: emulated`, `quality_mix.real: 0` — every observation is simulated. |
| `oracle.vehicles.json` | `GET /api/v1/vehicles` | The one earmarked vehicle: the emulated stolen car, lawful basis `stolen_vehicle_fir`, its last emulated read. |
| `oracle.osint-events.json` | `GET /api/v1/osint/events` | Three OSINT situations built from the synthetic capture: the district weather alert (`OFFICIAL-VERIFIED`, 0.95), the SG Highway crash and the Odhav robbery (redacted). |
| `oracle.gazetteer-resolve.json` | `GET /api/v1/osint/gazetteer/resolve?q=Lal%20Darwaja` | A place resolved from free text: junction 3, `gazetteer_exact`. |
| `oracle.decision-support.json` | `GET /api/v1/decision-support/7c1076f0-…` | A decision-support record the sandbox generated on 2026-10-25, now `expired` (2 of its courses of action kept). |
| `brain.health.json` | `GET /health` (convoy-brain) | The two model tiers and the decider's gates (novelty latch armed, tier-0 cache enabled). |
| `brain.escorts.json` | `GET /escorts` | No escort running; `authority: officer_approves_every_switch` — the AI proposes, a named officer approves every switch. |
| `emulator.health.json` | `GET /health` (event-emulator) | Probes of store, Valkey, NATS and the twin; the library holds 10 use cases; the living city is off. |
| `emulator.use-cases.json` | `GET /api/v1/emulator/use-cases` | The 10 use cases as the emulator lists them (id, name, class, route, horizon, seed). |
| `emulator.runs.json` | `GET /api/v1/emulator/runs?include_tape=false` | Two recorded runs of the emulated ANPR sweep (a run and its replay) with their delivery counts and the labelled stolen-vehicle precondition (2 of 6; the runner's host name replaced by `(redacted)`). |

On these GET answers the oracle's `props.plate` fields carry the full emulated exercise mark; the deck masks every
mark it draws as `GJ27EM•••1` until a duty officer is named, and its proxy refuses operator reads without a
signed-in officer.

---

## Using the samples

### Read them

```bash
jq '._excerpt' samples/road-network/osm_network.excerpt.json         # what the excerpt keeps
jq '.response.entities[] | {kind, label, source}' samples/api/oracle.city-entities.json
jq '.coa_set[] | {coa_id, label}' samples/decision-support/dss_road_accident.json
jq '.signal | {publisher, title, text, pii_redactions, provenance_label}' samples/osint/signal.sg-highway-5.json
```

Turn the road excerpt into GeoJSON for any map viewer:

```bash
jq '{type: "FeatureCollection", features: [.segments[] | {type: "Feature",
      properties: {segment_id, road_name, road_class, lanes},
      geometry: {type: "LineString", coordinates: .line}}]}' \
   samples/road-network/osm_network.excerpt.json > old-city-roads.geojson
```

### Compare with a local stack

On the server that runs Veer, the services listen on loopback. The ports below are the service registry's
(`VVIP/TECHNICAL_DOCS.md` §1); a private stack may be configured with its own. Send **GET requests only**, and only
to a stack you run.

```bash
ORACLE=http://127.0.0.1:8091     # traffic-oracle
BRAIN=http://127.0.0.1:8092      # convoy-brain
EMU=http://127.0.0.1:8090        # event-emulator

curl -s "$ORACLE/api/v1/spatial/segments?min_lon=72.55&min_lat=23.0&max_lon=72.62&max_lat=23.05" \
  | jq '[.segments[] | {segment_id, road_name, geometry_basis}]'
curl -s "$ORACLE/api/v1/city/entities" | jq '[.entities[].kind] | group_by(.) | map({(.[0]): length}) | add'
curl -s "$ORACLE/api/v1/events/active" | jq '.events[] | {event_kind, status, title}'
curl -s "$ORACLE/api/v1/corridor/summary" | jq '{total_segments, provenance, quality_mix}'
curl -s "$ORACLE/api/v1/osint/events" | jq '.events[] | {label, verification_state, credibility}'
curl -s "$BRAIN/escorts" | jq '{authority, count, pending}'
curl -s "$EMU/api/v1/emulator/use-cases" | jq -r '.[].id'
curl -s "$EMU/api/v1/emulator/runs?include_tape=false" | jq '.runs[] | {run_id, status, use_case: .spec.use_case_id}'
```

Check that your stack answers the same shape as a sample (the keys, not the values):

```bash
diff <(jq -S '.response | keys' samples/api/oracle.corridor-summary.json) \
     <(curl -s "$ORACLE/api/v1/corridor/summary" | jq -S 'keys')
```

From another machine, go through the deck instead: sign in as an operator (the repository's helper is
`VVIP/scripts/deck_session.sh`) and read `/api/v1/…` through the deck's proxy; without a session the deck refuses
operator reads.

### Replay the contract pair

The pair in `contract/` comes from the deck's recorded fixtures. The deck's contract test replays all of them with
no network:

```bash
cd VVIP/services/command-deck
node tests/contract/run.mjs
```

---

## Licences

- `road-network/` and the segment geometry inside `api/oracle.spatial-segments.json`: © OpenStreetMap contributors,
  ODbL 1.0 (see `road-network/NOTICE.md`).
- Everything else here is written by the project or read back from its own sandbox, under the repository's licence
  (`VVIP/LICENSE`).
