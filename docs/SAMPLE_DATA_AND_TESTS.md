<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="../VVIP/services/command-deck/static/brand/veer-lockup.svg">
    <img alt="Veer" src="../VVIP/services/command-deck/static/brand/veer-lockup-day.svg" width="180">
  </picture>
</p>
<p align="center">
  <img alt="sample data and tests" src="https://img.shields.io/badge/document-sample%20data%20and%20tests-2ea44f?style=flat-square"> <img alt="Test cases" src="https://img.shields.io/badge/test%20cases-35-111111?style=flat-square">
</p>

# Veer — sample data and tests

This document lists every dataset the repository ships, says what each one is and where it comes from, and
describes every test suite and gate: what it covers, how to run it, and the latest result the committed
documentation records for it. It ends with about thirty representative test cases taken from the real tests.

Veer is a city operations platform for Ahmedabad: corridor events, protected movements, stolen-vehicle
enforcement support, OSINT event intelligence and decision support. The AI proposes and a named officer
decides. Paths below are relative to the repository root; the platform's code lives under `VVIP/`.

**Provenance words used in this document** (the same words the interface uses):

| Word | Meaning |
|---|---|
| **Real** | Taken from a real public source and committed as it was (for example OpenStreetMap road geometry, the public-domain NDMA SACHET alert sample). |
| **Emulated** | Produced by Veer's event emulator to drive the real stack: camera reads, agency units, corridor events, the demo stolen vehicle. Every row says so (`source: emulated_anpr`, `event-emulator` metadata, an `EM` plate series). |
| **Simulated** | The synthetic traffic feed and anything computed from it; every observation is labelled `data_quality = synthetic`. |
| **Synthetic** | Written by the project for tests (fictional `*.example` publishers, invented names that exist only to prove redaction). |
| **Modelled** | Output of a model run under stated assumptions (the impact model, twin and wargame figures), not a field measurement. |
| **Sandbox** | Read back from a private sandbox stack, never from the live system. |

---

## Contents

- [Part 1 — Sample data](#part-1--sample-data)
  - [1.1 At a glance](#11-at-a-glance)
  - [1.2 The real-road seed (OpenStreetMap network)](#12-the-real-road-seed-openstreetmap-network)
  - [1.3 The event emulator's use-case library and the twin's scenario library](#13-the-event-emulators-use-case-library-and-the-twins-scenario-library)
  - [1.4 The watchlist and the demo fixtures (the emulated stolen vehicle)](#14-the-watchlist-and-the-demo-fixtures-the-emulated-stolen-vehicle)
  - [1.5 OSINT fixtures and the place gazetteer](#15-osint-fixtures-and-the-place-gazetteer)
  - [1.6 Decision-support fixtures](#16-decision-support-fixtures)
  - [1.7 The deck's contract fixtures](#17-the-decks-contract-fixtures)
  - [1.8 The impact model's results](#18-the-impact-models-results)
  - [1.9 The showcase artifacts](#19-the-showcase-artifacts)
  - [1.10 Other committed data](#110-other-committed-data)
  - [1.11 The `samples/` folder](#111-the-samples-folder)
- [Part 2 — Tests](#part-2--tests)
  - [2.1 How the gates fit together](#21-how-the-gates-fit-together)
  - [2.2 Python suites (pytest)](#22-python-suites-pytest)
  - [2.3 Rust suite (signal-ingress)](#23-rust-suite-signal-ingress)
  - [2.4 The command deck](#24-the-command-deck)
  - [2.5 The offline acceptance ladder — `scripts/verify_all.sh`](#25-the-offline-acceptance-ladder--scriptsverify_allsh)
  - [2.6 The live acceptance ladder](#26-the-live-acceptance-ladder)
  - [2.7 The operator journeys — `scripts/journeys.mjs` (J1–J7)](#27-the-operator-journeys--scriptsjourneysmjs-j1j7)
  - [2.8 The flagship showcase — `scripts/showcase_run.sh`](#28-the-flagship-showcase--scriptsshowcase_runsh)
  - [2.9 The repetition gate — `scripts/repetition_gate.sh`](#29-the-repetition-gate--scriptsrepetition_gatesh)
  - [2.10 The docs-consistency oracle — `scripts/submission_consistency_check.mjs`](#210-the-docs-consistency-oracle--scriptssubmission_consistency_checkmjs)
  - [2.11 Running tests safely](#211-running-tests-safely)
- [Part 3 — Representative test cases](#part-3--representative-test-cases)
- [Part 4 — What is not recorded](#part-4--what-is-not-recorded)

---

# Part 1 — Sample data

## 1.1 At a glance

| Dataset | Where (under `VVIP/`) | Format | Size | Provenance | Loaded by |
|---|---|---|---|---|---|
| Road-network seed | `services/corridor-store/seed/*.sql` | SQL | 4 files, ≈ 179 KB | Real (OpenStreetMap, ODbL) + simulated traffic rows | `scripts/veer_up.sh` `seed()` after `scripts/migrate.py` |
| Network evidence and extracts | `scripts/data/osm_network.json`, `osm_network_map.json`, `osm/*.overpass.json.gz` | JSON, gzip JSON | 389 KB, 48 KB, 1.26 MB + 116 KB | Real (OpenStreetMap) | `scripts/gen_osm_network.py` (writes the seed; `--verify` re-checks it) |
| Emulator use-case library | `services/event-emulator/src/event_emulator/use_case_library.json` | JSON array | 10 entries, 23.5 KB | Emulated scenarios on the real network | `event_emulator/library.py` at import |
| Twin scenario library | `scripts/scenario_library.json` | JSON (`veer/scenario-library/1`) | 23 scenarios, 64.7 KB | Generated from the twin's scenarios | `python -m traffic_oracle.simulation export` (writer); tests |
| Demo stolen vehicle and exercise plates | `services/event-emulator/src/event_emulator/{tape,profiles,runner,ambient}.py`, `scripts/showcase_run.sh`, `scripts/demo_reset.sh` | code constants | — | Emulated (exercise data) | the emulator at run time; the scripts |
| OSINT capture (sandbox seed) | `services/osint-ingress/tests/fixtures/capture/` | RSS, Atom, CAP XML, JSON, zipped CSV | 6 data files | 1 real public-domain file, 5 synthetic | `python -m osint_ingress import-poc`; `scripts/osint_smoke.sh --offline` |
| OSINT test fixtures | `services/osint-ingress/tests/fixtures/`, `services/osint-common/`, `services/command-deck/tests/fixtures/osint/`, `services/traffic-oracle/tests/fixtures/osint/` | JSON, XML, HTML, Python | ≈ 76 KB + 25 KB + 11 KB + Python | Synthetic | the test suites |
| OSINT place gazetteer | `scripts/data/osint_gazetteer.json` | JSON `{meta, entries}` | 127 entries, 61 KB | Real (OpenStreetMap names) + reviewed seed table | `osint_geo.gazetteer.load()`; synced into `osint.gazetteer` by the oracle |
| Decision-support fixtures | `services/command-deck/tests/fixtures/dss/`, `services/traffic-oracle/tests/fixtures/dss/`, `services/osint-common/tests/fixtures/` | JSON, Python | 29 KB, 71 KB, 21 KB | Synthetic | the test suites |
| Deck contract fixtures | `services/command-deck/tests/contract/fixtures/` | JSON + `manifest.json` | 29 files, ≈ 105 KB | Recorded read-only (live oracle, sandbox) and contract-shaped | `tests/contract/run.mjs` |
| Deck workspace fixture | `services/command-deck/tests/fixtures/workspace/` | JSON + derivation script | ≈ 160 KB | Emulated capture, marks masked | `tests/workspace.unit.mjs` |
| Impact results | `scripts/impact_results.json` | JSON | 2.1 KB | Modelled | `scripts/impact_run.py` (writer); docs and the docs-consistency oracle |
| Showcase artifacts | `showcase/` | JSON, log, PNG | 23 files (12 JSON, 3 logs, 8 PNG) | Recorded from live runs | written by `scripts/showcase_run.sh` and the hero-shot camera |

## 1.2 The real-road seed (OpenStreetMap network)

**What it is.** Veer's city network: **49 road segments** (ids 1001–1049) and **34 junctions**, every segment
traced along the real road of its name between two real intersections, every junction on its OpenStreetMap node.
The network has 198 turning movements, 186 road-graph edges and is one strongly connected component; the store
measures 191.76 km (the generator's spherical sum reads 192.04 km). Classes: primary 21, trunk 12, secondary 11,
tertiary 5. On it sit 11 signal programs, **28 emulated camera sites** (24 ANPR, 4 CCTV — location and identity
only, no frame or stream) and 18 agency stations. Source: `VVIP/TECHNICAL_DOCS.md` §16.1.

**Files.**

| File | Size | What it carries |
|---|---|---|
| `VVIP/services/corridor-store/seed/sample_corridor.sql` | 57.9 KB | The network rows of a fresh install, plus traffic observations that are all labelled `data_quality = synthetic` ("random numbers, not a feed"). It writes nothing into the real-only `traffic.hourly_aggregates`. |
| `VVIP/services/corridor-store/seed/reanchor_osm_network.sql` | 110.2 KB | The idempotent network step: completes the network on a fresh store, or converts an existing store in place (ids kept) and re-anchors its emulated camera reads onto the real roads. A second apply changes nothing. |
| `VVIP/services/corridor-store/seed/post_seed_derivations.sql` | 9.6 KB | Camera sites, agency stations, junction names (English and Gujarati) and signal programs. |
| `VVIP/services/corridor-store/seed/display_geometry_osm.sql` | 1.4 KB | Clears superseded display lines a store may still carry. |
| `VVIP/services/corridor-store/seed/NOTICE.md` | 4.6 KB | The OpenStreetMap / ODbL 1.0 notice and the list of every derived file. |
| `VVIP/scripts/data/osm/city.overpass.json.gz`, `walled_city.overpass.json.gz` | 1.26 MB, 116 KB | The two Overpass extracts, unmodified (`osm_base` 2026-10-23T08:08:01Z and 08:34:36Z). |
| `VVIP/scripts/data/osm_network_map.json` | 48 KB | The reviewable mapping table: OSM node per junction, road per segment. |
| `VVIP/scripts/data/osm_network.json` | 389 KB | The evidence: traced paths, OSM way and node ids, validation metrics, cameras, stations, signal programs. |

**Provenance.** Real: road geometry © OpenStreetMap contributors, ODbL 1.0. Lanes and speed limits fall back to
seed values where OSM carries none (recorded per segment in the evidence file). Junction type and signal control
are the seed's own, not read from OSM. The camera sites are **emulated** placements on real approaches.

**How it is loaded.** `VVIP/scripts/migrate.py` applies migrations 001–025 (ledgered in
`corridor.schema_migrations`), then `VVIP/scripts/veer_up.sh` `seed()` runs, in order:
`sample_corridor.sql` (only into an empty store) → `reanchor_osm_network.sql` → `post_seed_derivations.sql` →
`display_geometry_osm.sql`. The oracle serves the result with `geometry_basis: osm` (for example
`GET /api/v1/spatial/segments`).

**How it is regenerated and checked.** `python3 VVIP/scripts/gen_osm_network.py --verify` re-measures everything
from the committed extracts with no network access: every segment within 15 m (Hausdorff) of its OSM centreline
(worst measured 7.76 m), ending exactly at its junctions, length within 2 % (worst 0.96 %), one strongly connected
network, outputs byte-identical to a regeneration.

## 1.3 The event emulator's use-case library and the twin's scenario library

Two libraries exist by design (`VVIP/TECHNICAL_DOCS.md` §13, "Adversarial testing").

**Emulator use-case library** — `VVIP/services/event-emulator/src/event_emulator/use_case_library.json`

- **Format:** a JSON array of `{id, scenarioConfig}`; `scenarioConfig` holds the scenario id and name, category,
  protection class, the route as segment ids, departure time, horizon, seed, weather, forced events and the
  closure policy.
- **Size:** 10 entries, 23.5 KB — the eight corridor use cases (`vvip_convoy_base`, `rath_yatra_ahmedabad`,
  `kumbh_scale_gathering`, `riverfront_marathon`, `national_day_parade`, `motera_stadium_egress`,
  `flood_evacuation_corridor`, `metro_work_zone`), the flagship composite `rath_yatra_monsoon_ambulance`
  (procession + monsoon burst + one 108 ambulance) and the emulated `watchlist_anpr_sweep`.
- **Provenance:** emulated scenarios authored by the project; every route is a legal chain on the real network.
  The emulator injects **causes only** (procession schedules, weather onset, camera reads, unit positions, 108
  requests); every decision, band change and refusal is the real stack's own.
- **How it is loaded:** `event_emulator/library.py` reads the file at import and validates its shape (it fails
  closed on a malformed entry); the `event_kind` / `crowd_class` axes come from `event_emulator/profiles.py`. The
  emulator serves it verbatim at `GET /api/v1/emulator/use-cases` and starts a run with
  `POST /api/v1/emulator/runs`. A run's cause tape is a pure function of `(spec, seed, t0)`.

**Twin scenario library** — `VVIP/scripts/scenario_library.json`

- **Format:** `veer/scenario-library/1` — `{format, generator, attribution, n_scenarios, scenarios[], network}`.
- **Size:** 23 scenarios, 64.7 KB, including the eight use cases.
- **Provenance:** generated (`python -m traffic_oracle.simulation export`, from
  `traffic_oracle/simulation/scenarios.py`); its `network` block carries the seed's real-road facts.
- **How it is used:** read by the oracle's simulation tests and cross-checked by `gen_osm_network.py`.

A copy of the flagship entry is in [`samples/emulator/`](../samples/emulator/).

## 1.4 The watchlist and the demo fixtures (the emulated stolen vehicle)

No vehicle is seeded into the store. The watchlist is built at run time through the oracle's own APIs, and every
plate the emulator invents carries the `EM` series marker (`GJ01EM` + four digits), so an emulated plate labels
itself wherever it appears.

| Fixture | Where | What it is |
|---|---|---|
| The demo stolen vehicle **`GJ27EM9001`** | `event_emulator/tape.py` (`_STOLEN_LABEL`) | The plate a stolen-vehicle FIR names in the `watchlist_anpr_sweep` scenario and the flagship showcase. Exercise data, not a real registration. |
| Its FIR, **demo FIR 4401/2026, Kalupur PS** | `event_emulator/profiles.py` (`anpr_stolen_fir_ref`), `scripts/showcase_run.sh` (`FIR_REF`) | The scenario's premise. On emulated entities, feed rows, events and decision-support summaries the oracle prints it as "demo FIR …". |
| The precondition earmark | `event_emulator/runner.py` (`ensure_stolen_earmark`) | Before a sweep's reads, the emulator makes sure the plate holds an active `stolen_vehicle_fir` earmark, created through `POST /api/v1/vehicles/{plate}/earmark` with retention 7 days and the reason "EMULATED scenario precondition …". |
| The operator-exercise plate **`GJ27EM4321`** | `event_emulator/tape.py` (`_EARMARKED_LABEL`) | Never earmarked by the emulator: its reads hit only after a duty officer earmarks it with a lawful basis. |
| Reserved plates | `event_emulator/ambient.py` (`_RESERVED_PLATES`) | The living city never reuses the two demo plates. |
| Demo staging | `scripts/demo_reset.sh` (`DEMO_STOLEN_PLATE`, default `GJ27EM9001`) | Stages a pending `R_STOLEN_SIGHTING` without deciding anything a human must decide. |
| Masked fixture worlds | `services/command-deck/tests/fixtures/workspace/captured.json`, the fixture worlds inside `tests/home-smoke.mjs` and the other hermetic smokes | Deck fixtures; the workspace fixture keeps only masked marks (`GJ27EM•••1`) and replaces every human actor with "Sandbox Officer". |

**Rules the fixtures exercise.** A read of a vehicle under an active `stolen_vehicle_fir` earmark files one
evidence-only `R_STOLEN_SIGHTING`, never an e-challan; approving an e-challan on it answers **409**; a pursuit of it
is authorised only by its approved sighting (otherwise **422**), and one approval authorises one pursuit. Lawful
bases are enumerated (Motor Vehicles Act 1988 s.177 / s.183 / s.207, BNSS 2023 s.94, or a stolen-vehicle FIR);
retention is server-computed and capped at 90 days. Plates are masked as `GJ27EM•••1` on every surface until a
duty officer is named.

## 1.5 OSINT fixtures and the place gazetteer

OSINT in Veer is about **places and situations, never persons**. No fixture names a real person; the real
proof-of-concept captures are never committed.

**The synthetic capture (the sandbox seed)** — `VVIP/services/osint-ingress/tests/fixtures/capture/`
(per-file provenance in its `README.md`):

| File | Provenance | What it is |
|---|---|---|
| `sachet_gujarat_live.xml` | **Real**, public domain | NDMA SACHET CAP RSS for Gujarat, copied verbatim: 10 weather alerts (1 names Ahmedabad district). |
| `gnews_live.xml` | Synthetic | A news RSS replica with fictional publishers `news-a.example`, `news-b.example`; fictional names and ages exist only to be redacted. |
| `reddit_live.rss` | Synthetic | A community Atom replica for the fictional `r/example_city`; every handle is fictional. |
| `gdelt_doc_live.json`, `gdelt_lastupdate_live.txt`, `20261020120000.export.CSV.zip` | Synthetic | GDELT replicas, rebuilt deterministically by `../build_synthetic_gdelt.py` (`--check` compares). |

Its designed outcome: 28 signals parsed, and through the full pipeline **exactly 3 surfaced situations** — the
SG Highway crash near Karnavati Club (segment 1045), the Odhav robbery (junction 11) and the SACHET Ahmedabad
district alert. Single social posts and state-wide nowcasts are held. A synthetic import is labelled `SIMULATED`;
the real SACHET file keeps `OFFICIAL-VERIFIED`.

**Loaded by** `python -m osint_ingress import-poc tests/fixtures/capture <cache_dir>` (it seeds the sandbox) and,
offline, by `VVIP/scripts/osint_smoke.sh --offline`, which runs the pipeline end to end with no network, no oracle
and no database.

**Other OSINT fixtures.**

- `VVIP/services/osint-ingress/tests/fixtures/hostile/` — four hostile XML documents (XXE, billion laughs, an
  external DTD, an Atom external entity) that `defusedxml` must refuse.
- `VVIP/services/osint-ingress/tests/fixtures/pages/` — synthetic municipal and CAP pages for the page connectors.
- `VVIP/services/osint-ingress/tests/fixtures/heldout_names*.json` — three held-out corpora (two written blind) for
  the redaction recall test.
- `VVIP/services/osint-common/src/osint_common/testing.py` — the canonical synthetic **signals** every OSINT
  package imports (`sg_highway_signals()`, `odhav_robbery_signal()`, `social_single_signal()`,
  `sachet_district_signal()`, `sachet_state_signal()`), already redacted to `[PERSON]` / `[AGE]` as a connector
  emits them. They are Python constructors, not JSON files.
- `VVIP/services/command-deck/tests/fixtures/osint/` — five synthetic city-entity replicas (`correlated.json`,
  `district.json`, `robbery.json`, `place.json`, and `poisoned.json`, a negative fixture with a planted
  `author` / `byline` pair).
- `VVIP/services/traffic-oracle/tests/fixtures/osint/` — the oracle's signal fixtures, a deterministic fake
  pipeline and the database harness.

**The place gazetteer** — `VVIP/scripts/data/osint_gazetteer.json`

- **Format:** `{meta, entries}`; each entry `{gaz_id, canonical_name, feature_type, surface_forms[], lon, lat,
  junction_id, segment_id, importance, source, lang_primary}`.
- **Size:** 127 entries, 61 KB — 49 roads, 34 junctions, 28 neighbourhoods, 16 landmarks, with Gujarati and Hindi
  aliases. Places only: the loader refuses any key outside the field list.
- **Provenance:** real road and junction names from OpenStreetMap (ODbL 1.0) plus a reviewed seed table of
  neighbourhoods and landmarks.
- **How it is loaded:** `osint_geo.gazetteer.load()` finds it (argument → `$OSINT_GAZETTEER_PATH` → the repository
  file → the image path); the oracle syncs it into `osint.gazetteer` once per process.
  `python3 VVIP/scripts/gen_osint_gazetteer.py --write` regenerates it; `--check` proves the committed file equals
  a rebuild and that no area word stands as a junction alias.

## 1.6 Decision-support fixtures

| Fixture | Provenance | Used by |
|---|---|---|
| `VVIP/services/command-deck/tests/fixtures/dss/dss_road_accident.json`, `dss_weather_hazard.json` | Synthetic `DecisionSupport` documents (fictional ids) | `tests/dss.unit.mjs` and the DSS card smoke; `tests/test_dss_fixtures.py` validates them against the frozen C-U contract |
| `VVIP/services/osint-common/tests/fixtures/dss_sg_highway.synthetic.json` | Synthetic; equals `osint_common.testing.sg_highway_dss()` | `tests/test_dss_shapes.py` |
| `VVIP/services/traffic-oracle/tests/fixtures/dss/` (`sg_highway_dss_input.json`, `area_subject.json`, `fakedss.py`) | Synthetic | the oracle's decision-support tests |

Every option a decision-support document proposes is labelled for what it is: wargame figures are simulated, the
public-safety criterion is a fixed prior, and an approval only creates dispatch **requests**, each decided on its
own.

## 1.7 The deck's contract fixtures

`VVIP/services/command-deck/tests/contract/fixtures/` holds 29 files (28 payloads and `manifest.json`), about
105 KB. `manifest.json` maps each request (path and query) to its response file and status code, and records each
file's origin:

| Origin | Count | What it means |
|---|---|---|
| `live` | 14 routes | Verbatim GET answers recorded read-only from the deployed oracle on 2026-10-22. |
| `contract` | 3 routes (plus their frozen `*.contract.json` files) | Contract C-C shapes populated from real rows (read-only), frozen so a re-record cannot silently change what an assertion means. |
| `sandbox` | 1 route | `events_history.sandbox.json`, recorded from the private sandbox oracle on 2026-10-24, its marks masked. |
| `osint-sandbox` | 4 routes | `osint_event.entity.json`, `place.entity.json`, `osint.feeditem.json`, `dss.decisionsupport.json`, recorded from the sandbox on 2026-10-25 (fictional publishers). |

**How they are used.** `node tests/contract/run.mjs` (from `VVIP/services/command-deck`) bundles the deck's real
parsers and stores with esbuild and replaces `fetch` with a router over the manifest: no network, and writer POSTs
are answered by an in-process stub so their bodies can be inspected. `--live <base>` runs the same core assertions
against a stack; `--record <base>` re-records the `live` files; both are GET-only and refuse to start without an
explicit base URL. `CONTRACT_FIXTURES=<dir>` points the runner at a scratch copy.

A request/response pair from this folder is in [`samples/contract/`](../samples/contract/).

## 1.8 The impact model's results

`VVIP/scripts/impact_results.json` (2.1 KB, generated 2026-10-23T14:39:29Z) is the output of
`VVIP/scripts/impact_run.py`, a deterministic analytical model of rolling corridor holds against a blanket freeze
on Veer's own network. **These are modelled figures, not field measurements**; every constant is sourced or a
labelled assumption (`VVIP/IMPACT_REPORT.md`).

| Figure (central case) | Blanket freeze (25 min per junction) | Rolling hold (2.5 min per junction) |
|---|---|---|
| Commuter-minutes per frozen junction | ≈ 33,291 | ≈ 333 |
| Commuter-minutes per movement, whole network frozen | 1,131,888 | 11,319 |
| Vehicles caught in holds per movement | 60,367 | 6,037 |

Reduction factors: 100× central, 25× conservative, 506.2× optimistic. Annualised (250 movement-days, an
assumption): about 4.67 million commuter-hours. 108 ambulances: 132 minutes returned per movement-day, 33,000 per
year — minutes returned to the golden hour, not a claim about patient outcomes.

`python3 VVIP/scripts/impact_run.py --offline` regenerates it from the committed `scripts/data/osm_network.json`
(without `--offline` it reads the network from a running oracle). The docs-consistency oracle checks that every
impact figure quoted by the documents chains to this file alone.

## 1.9 The showcase artifacts

`VVIP/showcase/` holds what the flagship showcase run ("God's Eye Morning", §2.8) leaves behind. The committed
JSON and logs are **one run**: the last round of the repetition gate on the deployed stack,
`showcase_results.json` generated **2026-10-23T18:31:51Z** (00:01 IST on 2026-10-24), `passed: true`, no failed
assertion. Every approval in it was made by the script and is recorded as
`Scripted demo officer (showcase script)`.

| File | What it records |
|---|---|
| `showcase_results.json` (12.4 KB) | Every phase's assertions and counts: injections, audit rows, band transitions, the pursuit chain, the stolen-vehicle rule, dispatch, the signal-policy guard, screenshots and their proofs. |
| `injection_flagship.json`, `injection_sweep.json` | The two emulator runs: 761/761 frames (flagship, seed 202506271) and 583/583 frames (ANPR sweep, seed 20261105). |
| `pursuit_chain.json`, `chain_earmark.json` | The stolen-vehicle chain: earmark, emulated reads, evidence-only sightings, the 409 probe, the pursuit, the ranked choke junctions. No fine anywhere. |
| `jan_rakshak.json` | The Jan Rakshak dispatch walked through its audited statuses (emulated projection). |
| `band_easing.json`, `ambulance_observe.json`, `twin_audit.json` | The band transition, the 108 escalation and the twin's 12-replication audit (model output). |
| `signal_policy.json`, `signals_restore.json` | The signal-plan guard: an apply refused **409** `shadow_eval_failed_closed`, zero writes. |
| `shots_manifest.json`, `shots_city.log`, `shots_ops.log`, `shots_rest.log` | The hero-shot camera's checks (non-blank proofs, colour counts, imagery mode). |
| `showcase_gods_eye_city.png`, `showcase_pursuit_trace.png`, `showcase_citizen_advisory.png`, `showcase_ops_wall.png` | The four hero shots, recaptured at 01:25–01:26 IST on 2026-10-24 on the staged demo state (1440 × 900). |
| `showcase_v3_home.png`, `showcase_v3_decide.png`, `showcase_v3_map.png`, `showcase_v3_citizen.png` | Hero shots of the V3 interface from the live stack, committed on 2026-10-27. |

The README screenshots of the V3 interface are a separate set, `VVIP/docs/screenshots/*.jpg` (20 images).

## 1.10 Other committed data

| File | Size | What it is |
|---|---|---|
| `VVIP/scripts/data/route_acceptance_pairs.json` | 4.6 KB | The POI route matrix: 182/182 pairs route on the network (`scripts/poi_route_matrix.py`). |
| `VVIP/shared/schemas/protocol_params.json` | 1.4 KB | The protection-class protocol table (lane floors, advance closures) both services generate code from; `scripts/export_protocol_params.py --check` fails on drift. |
| `VVIP/scripts/bench_results.json`, `bench_adversarial_report*.json` | small | The model bench and the adversarial scenario bench (19/19 on 2026-10-13). |
| `VVIP/scripts/drift_baseline.json` | 14 KB | The model-drift panel's baseline, with a justification per anchor. |
| `VVIP/scripts/data/journeys/reboot_evidence.json` | 2.3 KB | Journey J7's recorded evidence: two real reboots on 2026-10-23, READY 11/11 in 265.3 s and 267.2 s. |

## 1.11 The `samples/` folder

[`samples/`](../samples/) is a small curated set copied from this repository, plus GET responses read back from a
private **sandbox** stack. Each file is at most about 40 KB; large sources are excerpted and say so. See
[`samples/README.md`](../samples/README.md) for every file and for `curl` examples against a local stack.

---

# Part 2 — Tests

## 2.1 How the gates fit together

| Layer | What runs | Touches a stack? |
|---|---|---|
| Unit and integration suites | pytest per Python service and OSINT package; `cargo test` for signal-ingress; the deck's `*.unit.mjs`, contract replay, token and copy gates | No (a few tests skip themselves unless pointed at a scratch database or Valkey) |
| Hermetic browser smokes | the deck's V3 smokes: every same-origin GET answered from a fixture world, every non-GET and every third-party request aborted | A private dev or preview deck only |
| Offline acceptance ladder | `scripts/verify_all.sh` — all of the above in a fixed order, plus generator checks and the docs-consistency oracle | Read-only (GET and read-only SELECT) |
| Live tiers and live gates | `verify_all.sh --live`, the full-system smoke, the operator journeys, the flagship showcase, the repetition gate | Yes — sign in once; some write labelled rows and close them again |

## 2.2 Python suites (pytest)

Every suite runs **whole**: a test that needs torch / ONNX or a database skips itself and the skip is counted; a
suite is never skipped wholesale. The gate discovers every directory under `VVIP/` that holds `test_*.py`.

**How to run.** The offline ladder bootstraps a pure-Python venv at `VVIP/.venvs/gate` and runs each suite the
same way:

```bash
bash VVIP/scripts/verify_all.sh            # bootstraps the gate venv, then runs every tier in order

# one suite by hand, the way the gate runs it (from the suite's tests/ directory):
cd VVIP/services/traffic-oracle/tests
PYTHONPATH=../src ../../../.venvs/gate/bin/python -m pytest . -q
```

The services' `pyproject.toml` files add the sibling OSINT packages to the path where a suite needs them. The deck's
two Python tests document their own command (see `VVIP/services/command-deck/tests/test_dss_fixtures.py`).

**Latest recorded counts** (`VVIP/TECHNICAL_DOCS.md` §13; `VVIP/README.md`):

| Suite | Directory | What it covers | Collected (2026-10-26) | Last whole-suite run (2026-10-26) |
|---|---|---|---|---|
| traffic-oracle | `services/traffic-oracle/tests` (67 files) | routing, forecasting ladder, adaptive layer, enforcement and the stolen-vehicle rule, events and lifecycle, city fusion, signals and their guards, OSINT store and routes, decision support, officer gates | 2168 | 2064 passed / 104 skipped |
| convoy-brain | `services/convoy-brain/tests` (31) | orchestrator, decider gates (novelty latch, tier-0 cache), escort authority, grounding, MCP tool rail, chat directives | 743 | 742 passed / 1 skipped |
| event-emulator | `services/event-emulator/tests` (16) | tape determinism, runs API, replay refusal, watchlist sweep, living city, officer requirement | 331 | 318 passed / 13 skipped |
| corridor-store | `services/corridor-store/tests` (9) | migrations grammar, the OSM network and its evidence, the network step | 146 | not recorded separately |
| corridor-store importer | `services/corridor-store/importer/tests` (1) | the OSM importer | 22 | not recorded separately |
| embedding-service | `services/embedding-service/tests` (7) | the T1 memory service | 113 | not recorded separately |
| osint-common | `services/osint-common/tests` (7) | C-T types, ethics checks, no real names, fixture shapes | 444 | 444 passed |
| osint-ingress | `services/osint-ingress/tests` (13) | connectors, redaction and held-out recall, hostile XML, egress allowlist | 382 | 381 passed / 1 skipped |
| osint-geo | `services/osint-geo/tests` (8) | the gazetteer, resolver, snapping and confidence | 390 | 390 passed |
| osint-analysis | `services/osint-analysis/tests` (12) | classification, correlation, credibility, fusion, ethics rails | 360 | 360 passed |
| command-deck (Python) | `services/command-deck/tests` (2) | the deck proxy guard, the DSS fixtures' contract | 20 | not recorded separately |
| **All** | | | **5119** | |

Each skip is a test whose optional dependency or scratch store (a database, a Valkey) is absent; for example the
emulator's PostgreSQL-backed tests run only when `EMULATOR_TEST_PG_DSN` names a scratch clone. History, kept: the
wave-4 tree collected 2709 tests and ran 2624 passed / 85 skipped (2026-10-24).

## 2.3 Rust suite (signal-ingress)

```bash
cd VVIP/services/signal-ingress
cargo test --locked
```

The verify_all `cargo` tier uses host cargo, else the `rust:alpine` image with cached registry and target volumes.

**Latest recorded result:** **120 passed** — 49 library unit tests plus 7 (`tests/ahmedabad_feed_tests.rs`), 45
(`tests/anomaly_tests.rs`) and 19 (`tests/pipeline_tests.rs`) — re-run on 2026-10-24 in `rust:alpine` on a clean
target and again in the 2026-10-26 deployment audit. A cargo target volume shared with other checkouts can report a
stale build (the 2026-10-23 offline ladder read 118 from one); that is a caveat of the shared volume, not of this
tree. Coverage: the anomaly statistics and flags, the Arrow batcher and IPC round trip, the channel pipeline, and
the Ahmedabad feed meeting the live acceptance bar at off-peak, morning and evening peak and night.

## 2.4 The command deck

All deck tests run from `VVIP/services/command-deck` after `bun install` (the offline ladder installs what it
needs). Unit tests and gates need no browser; smokes drive a headless Chrome through puppeteer.

**svelte-check** — `bun run check` (`svelte-kit sync && svelte-check --tsconfig ./tsconfig.json`). The ladder's
`gods-eye-check` tier runs it and gates the city-canvas files; diagnostics elsewhere are reported, not gated. No
repository-wide count is recorded.

**Design-token gates (contrast proofs)**

- `node tests/design-tokens.mjs` — the v2 token contract that the Analyst pages consume: CSS ↔ TS parity in both
  themes, WCAG AA 4.5:1 for every text ink on canvas and surfaces in both themes, type floors (12 px operator,
  13 px day), a hex sweep, icon and pack contracts, a style lint, and the import boundaries (`R4`).
- `node tests/v3-tokens.unit.mjs` — the V3 tokens (`src/lib/v3/tokens.css` ↔ `tokens.ts`): parity; **every V3 text
  ink ≥ 4.5:1 on every surface (bg, s1–s4) in both themes**, each role's ink on its own veil, and the primary,
  brand and decision fills with their inks (the table is printed); the frozen role values; the type scale; the
  EN / HI / GU packs; no hex literal outside the token files.

**Copy lint** — `node tests/copy-lint.mjs`, over the English strings of every pack: section titles at most 32
characters, at most one " · " in a chrome string, no ALL-CAPS word outside the acronym allowlist (each per-key
exception is printed on every run).

**Contract replay** — `node tests/contract/run.mjs` (see §1.7).

**Unit suites** — `node tests/<name>.unit.mjs`; the ladder runs every `tests/*.unit.mjs` (39 files):

| Group | Files |
|---|---|
| V3 screens | `home`, `decide`, `object-page`, `v3-shell`, `v3-map`, `v3-map-style`, `v3-assistant`, `v3-plan`, `v3-comms`, `v3-public`, `root-flip` |
| V3 identity | `v3-tokens`, `v3-assets` (illustrations labelled, no `<image>` or `<text>`, no orange or red), `v3-media` (artwork, reference photos, marks, budgets, credits) |
| Rails and honesty | `plates`, `mask-superset`, `plate-search`, `omnibar-lookup`, `public-feed`, `comms-osint`, `osint`, `osint-dom`, `no-live-port`, `deck-fixes` |
| Decisions and workspace | `decisions`, `dss`, `corridor`, `workspace`, `views`, `analysis`, `wall`, `assistant` |
| Canvas | `basemap`, `canvas-bus`, `canvas-layers`, `map-v2-fixes`, `thermal-toolbar` |
| Size and load | `route-budget` (per-route JavaScript ceilings from `tests/route-budget.json`), `perf2` |

**Browser smokes** — `node tests/<name>-smoke.mjs <deckUrl>` against a running dev or preview deck of this tree
(25 files). The **hermetic** V3 smokes answer every same-origin GET from a fixture world and abort every non-GET and
every third-party request: `home-smoke`, `decide-smoke`, `object-page-smoke`, `v3-shell-smoke`, `v3-map-smoke`,
`v3-map-style-smoke` (fake token, stubbed imagery), `v3-assistant-smoke`, `v3-plan-smoke`, `v3-comms-smoke`,
`v3-public-smoke`. `ops-wall-smoke` is hermetic as well and carries the "no officer" masking group. The others
need a stack behind the deck: `design-smoke`, `gods-eye-smoke`, `gods-eye-3d-smoke`, `canvas-ux-smoke`,
`city-command-smoke`, `agent-canvas-smoke`, `citizen-smoke`, `dss-card-smoke`, `assistant-smoke`,
`deck-fixes-smoke`, `perf2-prod-smoke`, `root-flip-smoke`, `ops-live-smoke` (the upstreams directly) and
`ops-write-smoke` (the oracle URL, GET-only probes).

**Cameras.** `tests/screens-verify.mjs` photographs `/ops`, `/gods-eye`, `/citizen`, `/driver`, `/comms` and `/chat`
under software WebGL and asserts each surface's key elements and a non-blank picture; `tests/route-coldload.mjs`
measures a cold load per route; `tests/frame-geometry.mjs` measures docks and credit plates;
`tests/integration-agent.mjs` drives the assistant through the deck's proxy.

**Latest recorded results.**

| What | Result | Date |
|---|---|---|
| `screens-verify.mjs` on the live deck | 40/40 checks (the pre-V3 deck) | 2026-10-24 00:21 IST |
| `screens-verify.mjs` in the V3 live run | green; its two developer-harness checks skipped on a production deck, not counted | 2026-10-27 |
| The V3 unit tests and hermetic smokes | no pass count for the merged V3 tree is recorded; the implementers' reports record mutation testing of the new units | 2026-10-27 |
| `verify_all.sh` offline `deck-ui` tier in the V3 live run | **not green**: the assistant smoke's live-strip checks need a pursuit on the board, and after the demo reset none exists until an officer authorises the staged sighting; it also found one long event title clipped at the Analyst assistant dock at 1440 px (cosmetic, recorded) | 2026-10-27 |

## 2.5 The offline acceptance ladder — `scripts/verify_all.sh`

```bash
bash VVIP/scripts/verify_all.sh          # offline: no sign-in, no model call, nothing written to any stack
bash VVIP/scripts/verify_all.sh --live   # the live tiers against DECK_URL (default the live deck) — see §2.11
```

The deck tiers serve the built deck on a **private preview** (port 5199, operator gate off, no keys). The offline
tiers run in order and fail fast:

| Tier | What it runs |
|---|---|
| `scripts-syntax` | `bash -n`, `node --check`, a Python AST parse and a JSON load over the gate and release scripts |
| `gods-eye-check` | svelte-check on the city-canvas files |
| `gods-eye-canvas` | build the deck, then the software-WebGL canvas smoke (`tests/gods-eye-smoke.mjs`) |
| `design-smoke` | `/analyst` is the workspace cockpit, the live URLs answer 200, token parity in both themes |
| `deck-ui` | the hermetic ops-wall smoke (with the "no officer" masking group), contract replay, design tokens, copy lint, every `*.unit.mjs`, the edge-basemap entry, the GET-only ops-write probe, the DSS card, assistant and frame-geometry smokes |
| `pytest-<suite>` | every pytest suite, whole (§2.2) |
| `osint-offline` | `scripts/osint_smoke.sh --offline` over the synthetic capture, then `gen_osint_gazetteer.py --check` |
| `cargo` | `cargo test --locked` (§2.3) |
| `display-geometry` | `scripts/gen_display_geometry.py --verify` — the OSM network re-measured from its committed evidence |
| `ingress-segments` | `scripts/gen_ingress_segments.py --check` — signal-ingress's compiled-in network equals the store's |
| `submission-consistency` | the docs-consistency oracle and its `--selftest` (§2.10) |
| `wave1-hatches` | the forecaster support hatch and the decider novelty latch |
| `wave2-forecaster`, `wave2-routing`, `wave2-tier0` | the foundation forecaster on its real artifact; P90-robust routing and the protocol-params drift guard; the full convoy-brain suite with the tier-0 gate |
| `wave3-repetition` | `repetition_gate.sh --fast` (the offline self-test) |
| `wave3-ledger` | the degradation-ledger taxonomy tests |

`--live` adds: `live` (one operator sign-in through `scripts/deck_session.sh`; the gate must refuse anonymous
operator reads; the imagery key must never reach an anonymous client), `demo-reset` (`scripts/demo_reset.sh`
dry-run), `live-smokes` (`ops-live-smoke.mjs`, then `integration-agent.mjs`), `models` and `model-drift`.

**Latest recorded results:** offline **ALL TIERS PASSED** on the tree as deployed (step 3 of the 2026-10-23 live
acceptance) and `--live` **ALL TIERS PASSED** (step 10, 2026-10-24). In the V3 live run of 2026-10-27,
`verify_all --live` was green and the offline `deck-ui` tier was not (§2.4).

## 2.6 The live acceptance ladder

The live acceptance is a fixed sequence of the repository's own scripts, run in order on the deployed stack with
one log per step. Its steps and results are recorded in `VVIP/TECHNICAL_DOCS.md` §13 ("Live acceptance on the
deployed stack") and §18.8.

| # | Step | Result, 2026-10-23/24 |
|---|---|---|
| 1–2 | `veer_up.sh --status`; API probes | READY 11/11; 49 segments, all `osm`; 34 junctions; 191.76 km; escort authority `officer_approves_every_switch`; 28 MCP tools |
| 3 | `verify_all.sh` (offline) | ALL TIERS PASSED |
| 4 | `argus_full_smoke.sh` (the full-system live smoke) | ALL PASS |
| 5–6 | negative control: signal-ingress stopped for 6 minutes, then restarted | exit 1 with exactly the four data-plane legs failing, everything else green; ALL PASS after the restart |
| 7 | `fleet_smoke.sh` | ALL PASS |
| 8 | `check_tier0_live.sh` | **FAIL**, fixed (the decider's route options keyed on their own segments) and re-run green at 01:21–01:23 |
| 9 | the model-drift panel | 4/4 probes green |
| 10 | `verify_all.sh --live` | ALL TIERS PASSED |
| 11 | `repetition_gate.sh --fast` | PASS |
| 12 | `showcase_run.sh` | SHOWCASE PASS |
| 13 | `repetition_gate.sh 2` | REPETITION GATE PASS |
| 14 | `journeys.mjs --live` | J1–J6 92/92, J7 recorded |
| 15–17 | design, God's-eye and God's-eye 3D smokes | all assertions passed |
| 18 | canvas-ux smoke | **FAIL** (2 assertions), traced to leftover test rows; re-ran green at 00:30 after the demo reset |
| 19 | city-command smoke | **FAIL** (1 assertion), same cause; re-ran green at 00:32 |
| 20 | ops live smoke + the integration agent | all checks passed; 10 passed, 0 failed |
| 21 | `screens-verify.mjs` | 40/40 |
| 22 | leak check over every log | clean — no session secret, imagery token or operator PIN anywhere |

**19 of 22 steps passed first time**; the three failures, their causes and the green re-runs are recorded.

**The V3 live run (2026-10-27)**, gate on, after deploying migrations 021–025 and OSINT (READY 12/12):
green — status; API probes (49/49 OSM segments, escort authority, at least 20 MCP tools); the full-system smoke;
the feed-dark negative and its recovery; fleet; tier-0; the drift panel; `verify_all --live`; repetition (fast);
the journeys J1–J6 (J7 is the manual reboot record); God's-eye and God's-eye 3D; canvas UX; the ops-live and
agent-integration smokes; screens-verify; both leak checks; the four OSINT checks (health, surfaces, officer gates,
the public firewall). **Not green, with the reason:** the flagship showcase (every assertion but one passed; its
pursuit-trace hero shot fell back from the photoreal tiles under load, so the run is not cited — the 2026-10-24
run stays the flagship record); the offline `deck-ui` tier (§2.4); and `city-command` (its anomaly-pick check
found no anomaly pulse on the wall at that moment). Test drifts the ladder exposed were fixed in the tests, never
by loosening a product rule.

## 2.7 The operator journeys — `scripts/journeys.mjs` (J1–J7)

Every journey runs end to end through one deck origin, signed in once as the officer `Journey check (automated)`.
Every row a journey creates is labelled `JOURNEY CHECK (automated)`, every plate it invents carries `EM`, and a
cleanup that always runs closes everything it opened.

```bash
DECK_URL=http://127.0.0.1:<private-deck-port> VEER_OPERATOR_PIN_FILE=<file> node VVIP/scripts/journeys.mjs
node VVIP/scripts/journeys.mjs --only J2,J5 --no-browser   # selected journeys, API-level checks only
```

It refuses the live deck unless `--live` is passed. Exit 0 when J1–J6 pass; 1 when a journey failed or a cleanup
left a row open; 2 on usage or refusal.

| Journey | What it proves |
|---|---|
| J1 | The city at rest, honest labels: every fusion feed answers; cameras, units and sightings say EMULATED; the canvas says SIMULATED FEED exactly when the traffic is synthetic; the roads are the OSM network. |
| J2 | The stolen vehicle: an emulated read → a PENDING `R_STOLEN_SIGHTING` → an e-challan on that plate refused (409) → the named officer approves the sighting → no pursuit from the e-challan (422) → pursuit from the approved sighting → interception plan → dispatch → pursuit closed. |
| J3 | The escort: a Z-class plan, the escort on emulated GPS, an AI proposal approved by the officer — or none, and the approved plan holds — then clear. |
| J4 | The 108 corridor: the anonymous `/driver` request → approval by the named officer on `/ops` → the unit on the canvas and on the driver's view. |
| J5 | Chat: "show me the stolen vehicle on the map" → tool call, prose and a canvas directive → the AI-suggests chip, never auto-applied → Apply → one acknowledgement. |
| J6 | The citizen pages in EN / HI / GU: emulated rows badged SIMULATED FEED · EMULATED, a plan beyond the 2-hour horizon under "Later", no plate, no pursuit. |
| J7 | The reboot checklist (manual), with its recorded evidence in `scripts/data/journeys/reboot_evidence.json`. |

**Latest recorded result:** on the live deck, **J1–J6 PASS — 17/17, 23/23, 13/13, 11/11, 10/10 and 18/18, 92/92
checks** (2026-10-24 00:02–00:06 IST), and J7 recorded (READY 11/11 in 265.3 s and 267.2 s after two real reboots on
2026-10-23). In the V3 live run of 2026-10-27 the journeys J1–J6 were green (no per-journey count is quoted for
that run).

## 2.8 The flagship showcase — `scripts/showcase_run.sh`

```bash
bash VVIP/scripts/showcase_run.sh     # no arguments; drives the running stack through the emulator's HTTP API
```

"God's Eye Morning": the flagship composite `rath_yatra_monsoon_ambulance` (Rath Yatra, a monsoon burst, one 108
ambulance) plus the emulated stolen-vehicle ANPR sweep, injected into the running stack. It asserts fleet and model
health, the injections, the audit trail, the adaptive band response, the green-corridor windows the twin schedules,
the full stolen-vehicle chain (no fine anywhere; the e-challan probe answers 409), the Jan Rakshak dispatch, the
signal-policy guard (fail-closed), the citizen advisory (no pursuit, no plate) and non-blank interface shots. It
switches the signal-policy writer on only for its own run and puts it back afterwards, also on interrupt.

**Latest recorded result:** **SHOWCASE PASS three times** on the deployed stack on the night of 2026-10-23/24 (alone
at 23:51–23:55 IST, then twice under the repetition gate); the committed artifacts are the gate's last round
(`showcase_results.json`, 2026-10-23T18:31:51Z). The 2026-10-27 run is not cited (§2.6).

## 2.9 The repetition gate — `scripts/repetition_gate.sh`

```bash
bash VVIP/scripts/repetition_gate.sh --fast   # offline self-test: comparator, normalizer, FAIL path, restore classifier
bash VVIP/scripts/repetition_gate.sh 2        # the live gate: N >= 2 showcase rounds from an identical baseline (tens of minutes)
```

It proves consistency under repetition: run the showcase N times from a restored baseline, and the terminal database
state the showcase asserts over is identical across rounds after normalising only the volatility classes that are
provably not system output (wall clock, run-scoped ids, generated UUIDs and sequences, one in-process counter,
engine-loop row multiplicity). Every normalisation is printed with its justification; anything else that differs
fails with the differing rows. The restore is ownership-scoped: it deletes only rows its round provably wrote and
fails ("the store was not quiescent") if anyone else's row changed. Run the live gate with `/ops` idle.

**Latest recorded result:** **REPETITION GATE PASS** — two rounds (flagship runs 25 and 27, sweep seed 20261105)
left identical canonical terminal-state projections (65 canonical lines, a 13-class normalisation manifest) from
identical baselines (20 tables, 17,720 rows), 2026-10-23 23:55 → 2026-10-24 00:02 IST. `--fast` passed in the
2026-10-23/24 ladder and in the 2026-10-27 V3 run.

## 2.10 The docs-consistency oracle — `scripts/submission_consistency_check.mjs`

```bash
cd VVIP
node scripts/submission_consistency_check.mjs               # the documents beside the VVIP tree, checked against it
node scripts/submission_consistency_check.mjs --vvip-only   # a checkout of the VVIP tree alone
node scripts/submission_consistency_check.mjs --selftest    # proves each check's failure path
```

The documentation registry as code: about twenty checks, each with a failure path proven by `--selftest` —
referenced paths exist; every bench, showcase, pursuit and pixel figure quoted by the documents equals the artifact
it cites; impact figures chain to `impact_results.json` alone; showcase artifacts are never blended across runs (a
hero shot taken apart from its run is disclosed with its own figure); the pytest counts the docs quote equal the
gate venv's live collection; the gate scripts keep their contracts. It is the `submission-consistency` tier of the
offline ladder; its result is part of that tier's (§2.5). No standalone check count is recorded.

## 2.11 Running tests safely

- Unit suites, the contract replay, the token and copy gates and the generator checks touch nothing.
- Run browser smokes against a **private** dev or preview deck of this tree (`vite dev`, or the preview the ladder
  spawns), never against a deck other people are using.
- `verify_all.sh --live`, `journeys.mjs --live`, `showcase_run.sh`, `repetition_gate.sh` (live) and
  `demo_reset.sh --apply` act on the stack they target. Use a private stack, or a live one only with its owner's
  go-ahead. `journeys.mjs` refuses the live deck without `--live`; `demo_reset.sh` is a dry run by default;
  `contract/run.mjs --live/--record` refuse to start without an explicit base URL and send GETs only.
- Gated tools sign in through one helper (`scripts/deck_session.sh` or `scripts/lib/deck_session.mjs`); the PIN is
  read at run time and never printed.

---

# Part 3 — Representative test cases

Each row is taken from a real test; the last column names the file (and, where useful, the test) that asserts it.
Paths are under `VVIP/services/` unless they start with `VVIP/scripts/`.

| ID | Area | Scenario | Steps | Expected result | Asserted in |
|---|---|---|---|---|---|
| TC-01 | Enforcement | An e-challan on a reported-stolen vehicle | A penal recommendation (`R_SPD_SEGMENT`, `R_SIGNAL_VIOLATION`, `R_CLOSED_CORRIDOR_ENTRY`) on a vehicle under an active `stolen_vehicle_fir` earmark; `POST …/recommendations/{id}/decision` `{decision: approve, officer}` | **409** `{detail: "e-challan withheld — vehicle reported stolen", reason: "stolen_vehicle_fir"}`; nothing written, the row stays pending; rejecting it stays allowed (200) | `traffic-oracle/tests/test_enforcement_stolen.py` — `TestDecision::test_approving_an_e_challan_of_a_stolen_vehicle_is_409`, `test_rejecting_it_stays_allowed` |
| TC-02 | Enforcement | A camera read of a stolen vehicle | Evaluate the rules for a 112 km/h emulated read of `GJ27EM9001` with the stolen context | Exactly one `R_STOLEN_SIGHTING` ("… e-challan withheld, vehicle reported stolen"); the penal rule it would have fired is recorded as withheld; evidence only | `traffic-oracle/tests/test_enforcement_stolen.py` — `test_a_stolen_vehicle_gets_one_sighting_and_no_penal_rule` |
| TC-03 | Enforcement | A pursuit asked for on an e-challan basis | `_validate_pursuit` with an approved penal recommendation of a stolen vehicle, then with its approved sighting | **422** naming `R_STOLEN_SIGHTING` (and never calling it a fine); the approved sighting is accepted | `traffic-oracle/tests/test_enforcement_stolen.py` — `test_an_approved_challan_never_authorises_pursuing_a_stolen_car` |
| TC-04 | Enforcement | One approval, one pursuit | Open a second pursuit from an approval already spent on a closed pursuit | **422** "… already authorised pursuit …"; a fresh approval is accepted | `traffic-oracle/tests/test_enforcement_stolen.py` — `test_one_approval_authorises_one_pursuit` |
| TC-05 | Human authority | An unnamed decision-support decision | `POST /api/v1/decision-support/{id}/decision` with no officer header, for a real, an unknown and a malformed id; then with a header from off loopback | **409** `officer-required` before any lookup (no SQL runs); an off-loopback header names nobody; a malformed body is 422 first | `traffic-oracle/tests/test_dss_decision_gate.py` — `test_officer_required_before_any_lookup` |
| TC-06 | Human authority | Promoting an OSINT situation without an officer | `POST /api/v1/osint/events/{id}/promote` with no header, and with a blank `officer` | **409** `officer-required` for an existing, unknown or malformed id; no lookup happens first | `traffic-oracle/tests/test_promote_gate.py` — `test_officer_required_for_an_existing_and_an_unknown_id` |
| TC-07 | Human authority | A full-mark plate lookup with no officer | `GET /api/v1/vehicles/lookup?plate=…` without the officer header | **409**; nothing is read or written (the officer check precedes every read) | `traffic-oracle/tests/test_vehicle_lookup.py` — `test_no_officer_is_409_and_nothing_is_read_or_written` |
| TC-08 | Human authority | Answering an escort proposal | `POST /movements/{id}/escort/approvals/{approval_id}` with no officer; with the verified header and a different body name; again after the decision; on expired and superseded proposals | No officer → **422** "officer is required"; the header officer decides and the body name is kept as `claimed_officer`; a second answer, an expired or a superseded proposal → **409** | `convoy-brain/tests/test_escort_authority.py` — `TestApprovalsApi::test_answers_and_attribution` |
| TC-09 | Human authority | An escort proposal times out | The decider proposes Plan B; no officer answers within the timeout (15 s in the test) | The proposal expires "no officer response — current plan held"; no route switch, no hold, the convoy keeps moving on its approved route; a late click changes nothing | `convoy-brain/tests/test_escort_authority.py` — `TestTimeout::test_no_answer_expires_and_the_convoy_holds_its_current_plan` |
| TC-10 | Human authority | The timeout setting | `VVIP_ESCORT_APPROVAL_TIMEOUT_SEC` unset, 120, 5, 9999, "soon" | 90 s default; clamped to 15–600 s; an unreadable value falls back to 90 s | `convoy-brain/tests/test_escort_authority.py` — `TestTimeoutSetting::test_default_and_bounds` |
| TC-11 | Watchlist | Lawful basis and retention | Build an earmark with an unknown basis; with a known basis and 90 days; with 91 days | Unknown basis refused; 90 accepted; 91 refused | `traffic-oracle/tests/test_vehicles_watchlist.py` — `TestEarmarkValidation` |
| TC-12 | Signals | A city signal plan when the shadow evaluation fails | `apply_city_plan` with the writer on and a failing shadow evaluation | `applied: false`, reason `shadow_eval_failed_closed`; zero writes | `traffic-oracle/tests/test_signal_city_plans.py` — `test_apply_fail_closed_when_shadow_fails` |
| TC-13 | Honest data | Synthetic history never calibrates anything | Scan the calibration, scheduler and vector-store SQL and the fitting packages | None names `hourly_aggregates_synthetic`; calibration still reads the real table | `traffic-oracle/tests/test_traffic_historical.py` — `TestCalibrationGuard` |
| TC-14 | AI rails | The MCP tool rail cannot act | List every tool name | No name matches `approve|decide|earmark|dispatch_request|withdraw|transition`; 29 tools | `convoy-brain/tests/test_mcp_allowlist.py` — `TestForbiddenVerbs` |
| TC-15 | AI rails | Grounding removes an invented road | Ask for the speed on a road the network does not carry, beside a real segment id | The reading stays under its real road's name; the sentence tying it to the unknown road is removed; the answer says "No road segment named …" and raises `ungrounded_claims_removed` | `convoy-brain/tests/test_grounding_honesty.py` — `TestT1NonExistentRoad::test_the_prose_check_removes_another_roads_figures` |
| TC-16 | OSINT ethics | The redactor removes names and ages | Parse the synthetic capture through every connector | No synthetic name (not even the surname alone) and no age survives; at least 5 `[PERSON]` and 3 `[AGE]`; `pii_redactions` equals the tokens written | `osint-ingress/tests/test_pii_redaction.py` — `test_synthetic_names_and_ages_are_redacted` |
| TC-17 | OSINT ethics | Held-out redaction recall | Redact three corpora, two written blind and never tuned on | Floors met, e.g. on the second blind corpus: latin names ≥ 0.88, Indic names 1.0, ages ≥ 0.89, ordinary words kept ≥ 0.98 | `osint-ingress/tests/test_heldout_recall.py` — `test_heldout_recall_meets_the_floors` |
| TC-18 | OSINT credibility | A single social post | Score one community post, then one with a 0.9 prior | Credibility capped at 0.30 whatever the prior; `UNVERIFIED-OSINT` | `osint-analysis/tests/test_credibility.py` — `test_a_single_social_post_is_capped_at_0_30` |
| TC-19 | OSINT security | Hostile feeds | Parse the four hostile XML fixtures | Each is refused by `defusedxml` (no external entity, no expansion, no remote DTD) | `osint-ingress/tests/test_connectors.py` — `test_defusedxml_refuses_hostile_documents` |
| TC-20 | Public firewall | OSINT never reaches the citizen feed | Project a fake oracle's mix of live, emulated and OSINT rows (one OSINT row of a public kind) | No OSINT row in the projection; emulated rows keep `emulated: true` and the envelope `emulated_labelling: true`; an unreadable row fails closed | `command-deck/tests/public-feed.unit.mjs` |
| TC-21 | Public pages | A public page carries no plate or location | Inspect the driver page's code; load `/citizen` in EN, HI and GU on the live deck | `/driver` makes no geolocation call and has no plate field; no registration mark in the public feed or on `/citizen` in any language | `command-deck/tests/v3-public.unit.mjs` (check 4); `VVIP/scripts/journeys.mjs` J6 |
| TC-22 | Masking | Plates are masked until an officer is named | Feed marks in upper, lower and mixed case, with separators and month-like series, to the mask with and without an officer | Every mark masked (`GJ27EM•••1`) without an officer and shown as sent with one; dates, times, FIR numbers and UUIDs untouched; one rule shared with the workspace mask | `command-deck/tests/plates.unit.mjs` |
| TC-23 | Masking | No raw mark in the rendered Home | Render Home from its fixture world with no officer named | No raw registration mark in `document.body.innerText`; the masked chip shows | `command-deck/tests/home-smoke.mjs` (check 4) |
| TC-24 | Accessibility | Contrast of every V3 text ink | Compute the contrast of each text ink on bg and s1–s4, night and day; each role's ink on its veil; fills with their inks | Every pair ≥ 4.5:1 (the table is printed) | `command-deck/tests/v3-tokens.unit.mjs` |
| TC-25 | Honest imagery | Reference photos are labelled | Read `Cover.svelte` and every photo use | A photo is drawn only by `Cover`, which always prints "Reference photo · not live" and the credit; every photo has author, licence and source | `command-deck/tests/v3-media.unit.mjs` |
| TC-26 | Decide | No single key decides | With no officer: click, Enter, digits, letters; with an officer: Enter; then a triple click on the primary | Without an officer nothing is sent; Enter only focuses the primary button; a triple click sends exactly one POST naming the officer | `command-deck/tests/decide-smoke.mjs` |
| TC-27 | Home | The featured decision | `pickFeatured` over units with different deadlines, with and without a current featured unit | The soonest deadline is featured; it is kept until a new one is at least 15 s sooner; an expired or vanished unit yields | `command-deck/tests/home.unit.mjs` |
| TC-28 | Alerts | The chime rule | `chimeAllowed` for a real and an emulated new decision, chime on and off, exercise data declared or not | A real decision chimes; an emulated one is silent unless the console declares exercise data; nothing chimes when turned off or when nothing is new | `command-deck/tests/home.unit.mjs` |
| TC-29 | Assistant | The assistant cannot approve | Render a turn with a proposal | No Apply or Approve control anywhere; "Open to decide" links to the proposal's home in Decide; the rule "can't approve, dispatch or show full registration marks" is shown | `command-deck/tests/v3-assistant.unit.mjs` |
| TC-30 | Map | The satellite quota guard | Ask for many tiles at once; answer 401 / 403 / 429 | At most 4 requests in flight; an 800-request cap per tab session; a refusal stands satellite down and queued requests are not sent; a card frames at most 6 tiles | `command-deck/tests/v3-map-style.unit.mjs` |
| TC-31 | Navigation | The root reroute | Resolve `/`, `/home`, `/analyst`, `/analyst/` and other paths | `/` and `/home` → Home; `/analyst` and `/analyst/` → the workspace; nothing else moves | `command-deck/tests/root-flip.unit.mjs` |
| TC-32 | Advisories | OSINT events are not drafted for citizens | Draft advisories for an OSINT-sourced event promoted to a public kind | Every citizen and 108 draft in EN, HI and GU is withheld with the verification label; zone and municipal drafts are still written | `command-deck/tests/comms-osint.unit.mjs` |
| TC-33 | Road network | The OSM network re-checks offline | Run the generator's verify on the committed evidence | "OK: every segment on its OSM road", no FAIL; it says what it did not check | `corridor-store/tests/test_osm_network.py` — `TestEvidence::test_offline_verify_passes` |
| TC-34 | Emulator | Tapes are deterministic | Build the same use case twice with the same spec, seed and run id; then with two seeds | Identical bytes; different seeds give different tapes | `event-emulator/tests/test_tape.py` — `TestTapeDeterminism` |
| TC-35 | Emulator | A replay of a tape off today's roads | Record a run, change the network under it, `POST …/runs/{id}/replay` | **422** `route_not_on_current_network` with the offending move; nothing ledgered, nothing re-animated | `event-emulator/tests/test_api.py` — `TestReplayOnTheCurrentNetwork::test_a_route_off_the_current_network_is_refused_422` |

---

# Part 4 — What is not recorded

The committed documentation does not record, and this document therefore does not quote:

- a pass count for the merged V3 deck tests (unit and hermetic smokes) — only that they exist and that mutation
  testing of the new units is recorded in the implementers' reports;
- a repository-wide `svelte-check` count, or a standalone count for the docs-consistency oracle;
- separate last-run counts for the corridor-store, importer, embedding-service and deck Python suites after
  2026-10-26 (they are part of the 5119 collected);
- a per-journey count for the 2026-10-27 V3 live run.
