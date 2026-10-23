# VEER — THE COMPLETE CONTEXT DOWNLOAD
> **Everything done with Veer from first commit to this moment, in one file.**
> Written 2026-10-14 for Kaushik (and anyone else) picking up the work at
> `~/argus/veer`; brought up to date on 2026-10-23 for waves 3–4 (Phase I).
> Read this top to bottom and you know the whole system.

---

## 1. Origin — what Veer is and where it came from

**The problem, in reality:** When a protected person (VVIP) moves by road in an
Indian city, traffic along the corridor is stopped 15–45 minutes before the
convoy arrives. Five agencies (traffic police, district admin, SPG/state
security, municipal signals, 108 ambulance dispatch) coordinate by phone and
radio. Commuters freeze. Ambulances sit behind barricades with sirens on —
documented deaths in Kanchipuram (2018), Mumbai (2022), Agartala (2026). The
MHA Blue Book itself says traffic should be *"regulated, not stopped"* — the
policy exists; the tooling to execute it never did.

**The original repo** (`github.com/shubro18202758/VVIP`, cloned Oct 11) was
already unusually deep for a prototype: real PyTorch DSTGAT traffic forecaster
(83K params), Rust/Arrow/NATS ingestion, PostGIS/pgRouting spatial DB seeded
with 40 real Ahmedabad road segments, a custom ReAct orchestrator with 4 agents,
OR-Tools routing, RL signal control. But: it told the operator's story about an
elite movement, its "6×" claim was unmeasured, and it had no citizen-facing
surface. **The pivot:** same engine, but the Very Important Persons are the
**V**oter on the bus, the **V**ictim in the ambulance, and the **V**ulnerable
patient — a social-cause platform for the Hack for Social Cause (HSC) under
VBYLD 2027, theme: Governance & Civic Technology.

## 2. The build arc — phases A to I

### Phase A — Submission foundation (Oct 11)
- Deep review of the original repo → `docs/history/DEEP_REVIEW_VVIP.md`
- Problem statement with named beneficiaries + 5-gap analysis with citations →
  `PROBLEM_STATEMENT_GUJARAT.md`
- LICENSE added (was missing — a disqualifier), judge demo path in README
- **Citizen Advisory Layer**: trilingual (EN/HI/GU) public page showing
  per-stretch freeze windows with clock times, alternates, and an honest
  demo-preview alert signup — wired to the same simulation the operators see
- **Green Corridor driver flow**: one-tap emergency passage request → AI
  evaluates the convoy gap → duty officer approves → live countdown window
  with a "minutes returned to the golden hour" counter

### Phase B — The model stack swap (Oct 12, workflow "Veer industry-grade revamp")
- **Qwen 3.5 9B dropped**; **`pplx-decider-v1-27b`** (Perplexity's open
  Apache-2.0 decision model, BF16 on python/SGLang :8083) adopted as the
  strategic brain; **aditi-ps18-v7h** (the user's own Gemma-4-12B fine-tune,
  Q4_K_M on llama-server :8084) as the tactical agent model; ollama side-load
  kept for debug
- **Embedding spine**: `pplx-embed-v2-late-0.6b` (late-interaction, MIT) +
  bge-m3 dense → migration 004, `/search` = dense ANN recall-100 → MaxSim
  rerank-20, incident memory from simulation runs
- **Two-tier brain**: decider does typed strategic choice (choice/noul/score,
  event-driven checkpoints, ≥5s cadence, token budgets 400/1500/8192,
  p95-based degradation, confidence<0.6 gating); Gemma runs the 4 tactical
  agents with tool-argument drafting; a deterministic heuristic floor completes
  the fallback chain; everything audit-logged into `decisions_log`
- **The GBNF latency fix** (the single most elegant bug of the project): one
  Gemma argument-drafting call ran to its 2,048-token cap at 18.6 tok/s —
  110.6 s, 89.7% of a whole turn — so every scenario 504'd. Fix: a
  `json_schema` envelope compiled to GBNF grammar on llama-server, so Gemma's
  generation stops at the closing brace. Per-turn fell 123.6 s → 30.8 s,
  thresholds untouched. Suite went 0/14 → **14/14, score 100**.
- Real-life simulation twin: seeded multi-replication point-queue corridor
  engine, Poisson events (breakdown/waterlogging/rally/market/signal fault),
  monsoon/fog/TOD/DOW realism, bidirectional DSTGAT forecast coupling,
  deterministic (PYTHONHASHSEED-immune), 14 named scenarios
- Adaptive layer: situation classifier (1,024 combinations exhaustively
  tested), oscillation-immune hysteresis, protocol floors 180/120/60 s,
  fail-closed shadow-eval (any deviation from baseline requires a twin PASS)
- Fleet brought up as one system on arm64 (postgis built from the repo's own
  recipe; host :5432 belongs to another project so compose maps 55434)

### Phase C — Corridor-OS: the event-agnostic generalization (Oct 13)
- Domain model generalized: `movement` → `corridor_event` with typed profiles;
  tier extended with `none` for public events; migrations 007–009
- **8 Indian-context event types** (`VVIP/docs/USE_CASES.md`): VVIP convoy
  (base), Jagannath Rath Yatra (old-city procession), Kumbh-class mass
  gathering, Sabarmati Riverfront marathon, Republic Day parade corridor,
  Narendra Modi Stadium match-night egress (~132k), monsoon-flood evacuation,
  metro/bullet-train work zones
- **Event emulator** (new service): emulates ONLY the causes (schedules,
  processions, weather, incidents, emergency requests) while the REAL stack
  genuinely responds; deterministic, replayable, 79 hermetic tests
- Flagship showcase "God's Eye Morning": Rath Yatra + monsoon + stolen
  vehicle, **32 audited decisions**, all gates green; suite grew to 19/19

### Phase D — The God's Eye city platform (Oct 13, per `docs/history/GODS_EYE_CONTEXT_DOWNLOAD.md`)
The mentor's paradigm shift (verbatim in that file): VVIP is "one of the smaller
parts" — the headline is a city-scale multi-agency platform. Delivered:
- **Watchlist + ANPR** (migration 010): vehicles, earmarks with lawful-basis
  flags + retention limits, sightings, e-challan recommendations with
  append-only audit; the `AnprSource` port (emulated reads, clearly labelled,
  documenting the production path)
- **The pursuit chain, proven end to end**: plate GJ27EM9001 earmarked (FIR
  4401/2026, Kalupur PS) → 4 emulated ANPR reads (93/101/96/113 km/h) →
  e-challan recommendation ("113 km/h in a 40 km/h segment") → a scripted
  approval under a cast officer name (Duty Officer R. Mehta, append-only
  audit — a fine on the stolen car's owner, which C-N later forbade) →
  `vehicle_pursuit`
  event → 9 ranked interception choke junctions (pgRouting drivingDistance) →
  28 timed trace positions on the canvas
- **City signal plans** (migration 011): situation-band-driven band→plan
  table (AMBER 0.06 / RED 0.12 / BLACK 0.18 priority-share), gated by a
  fail-closed shadow-eval writer that correctly REFUSES to commit when the
  twin isn't field-calibrated (seed data can't calibrate it — and the seed
  hourly aggregates its MAE figures of the time came from were later found
  fabricated and deleted; the replay reads `no_data` today) — the refusal
  is demonstrated as designed safety, not a bug
- **Jan Rakshak**: first-class agency actor + dispatch channel + emulated
  units on the canvas
- **God's-eye 3D canvas**: CesiumJS keyless (OSM raster + entities, zero ion
  calls) as the `/ops` centerpiece + cinematic `/gods-eye` route; layer
  registry pattern borrowed from the MIT `gods-eye-view` repo
  (github.com/bilawalsidhu/gods-eye-view); FLIR sensor shader; shareable
  camera URLs; attributed
- **Named Active Movement Adaptation module** (R9): the adaptive layer
  surfaced as an explicit module card + `ACTIVE_MOVEMENT_ADAPTATION.md`
- Ethics guardrails held throughout: **vehicles only, never faces or
  persons; penalties are human-approved recommendations; lawful-basis flags
  + retention limits; nothing anti-government anywhere**

### Phase E — The interface revamp (Oct 13–14, workflow "Veer interface revamp")
The UI had grown by accretion; this made it one product:
- **Design system**: 67 CSS custom properties × command/daylight themes, 16
  primitives (Panel, BandChip, DataTile, DecisionCard, EventDossier,
  BandMasthead…), app shell (CommandBar with global search + band indicator,
  keyboard shortcuts), trilingual i18n throughout
- **`/ops` situation wall**: three columns — band masthead + counters;
  decision queue + dispatch tiles + watchlist console; event board +
  signal-gate card + AMA + audit stream + the embedded God's-eye canvas
- **`/gods-eye` cinematic route** polished; **`/citizen`** rebuilt (daylight
  theme, "Your road, next 2 hours", 11 event cards with hold windows);
  **driver flow driven end-to-end** (idle → golden-hour counter → evaluating →
  proposal → duty-officer approve → 90-second live countdown); **`/comms`**
  trilingual with identical facts in all three languages
- Screenshot-verified on the rebuilt live UI; all gates green; docs survived
  the cold national-finals read (`approved=true`)

### Phase F — The argus clone (Oct 14, this directory)
Cloned to `~/argus/veer` as a **parallel live instance** (project
`vvip-argus`) — every port remapped, zero collisions with the original demo
stack; migrations 11/11 on its own volume + seed; `verify_all.sh` run FROM
THE CLONE: **ALL TIERS PASSED** (422 pytest passes, live models, canvas
smoke); flagship showcase re-run from the clone: **PASS**. Three deliberate
clone-local changes (see §4). Kaushik owns the tree.

### Phase G — The VVIP template restoration (Oct 14, same night)
The original template had been removed during the revamps and the interface
grew redundant layers around its absence. Restored it as the operator's
front door **without adding a redundant layer** (full detail:
`docs/history/TEMPLATE_RESTORATION.md`):
- `/` is now the **Convoy Command cockpit** — the template's map-centric
  layout (full-bleed God's-eye canvas, floating glass rails: left = real
  two-tier-brain planner with RECOMMENDED ribbon + officer-gated escort,
  right = corridor/events/audit), saffron sweep, Outfit display face, mono
  numerals, threat ladder, scanline stats pill, tool dock, AI trace console
  over the REAL decisions_log, honest escort HUD — zero client-side
  simulation
- Template identity added **through the token system** (7 new tokens × both
  themes, parity 74; threat ladder + congestion ramp expressed purely in
  existing token slots) and a new `flow` canvas layer (live congestion
  ramp; neutral when no observations)
- Redundancy DELETED: `(legacy)` routes (command/map/planning/simulation),
  `lib/components` (dead ChatPanel chain + superseded widgets),
  `lib/simulation`, `lib/stores`, `data-service` — their live capabilities
  absorbed by the cockpit and `/ops`
- Bug fixes surfaced by the end-to-end run: argus deck `EMULATOR_PORT`
  8095→8090 (proxy had been 502ing), canvas gate hardened (tiles publish
  from `tileLoadProgressEvent`, bounded poll instead of fixed sleep)
- Re-verified everything: svelte-check 0/0, all design gates,
  **`verify_all.sh` ALL TIERS PASSED again**, argus deck rebuilt and
  screenshot-verified live (all four health dots green)

### Phase H — Waves 1–3: the honesty gates + the Wave redeploy (Oct 17–18)
Three audit waves landed on top of Phase G (detail: `VVIP/TECHNICAL_DOCS.md`
§3/§6.1b/§13). `verify_all.sh` grew into a **14-tier ladder** — frontend
bundle/e2e, gods-eye check/canvas, the pytest suites, submission-consistency,
`wave1-hatches`, `wave2-forecaster`, `wave2-routing`, `wave2-tier0`,
`wave3-repetition`, `wave3-ledger`, models, model-drift (inventory:
`VVIP/scripts/verify_all.sh`).

- **Wave 1 (Oct 17) — abstention hatches.** The **decider novelty latch**
  (`convoy_brain/decider.py`): a checkpoint that is BOTH novel and confident
  is withheld (`tier=novelty_latched` + audit row + operator alert), never
  acted on; the orchestrator falls through to the tactical tier. The
  **forecast support hatch** (`traffic_oracle/predict/support_bounds.py`):
  recorded per-feature support bounds gate EVERY model rung — an
  out-of-support input never reaches a model; it degrades to the heuristic
  with the exact drift math and a labelled reason (bounds fail closed).
  Pinned by `tests/test_novelty_latch.py` / `tests/test_support_hatch.py`
  (pure-python, gate venv).
- **Wave 2 (Oct 18) — routine fast path + honest uncertainty.**
  **Decider tier-0 cache**: routine checkpoints (eligible triggers only,
  never operator chat) whose best memory comparable clears the 0.75
  routine similarity floor are answered with ZERO additional `/decide`
  calls (TTL 300 s, 128-entry FIFO, cross-movement isolation); memory
  outage fails OPEN — the decider is called, never degraded;
  `DECIDER_TIER0_DISABLE=1` is the kill switch. Live status (probed this
  session): the argus brain `:8092/health` reports `novelty_latch:
  "armed"` and `tier0_cache: "enabled"` — but the 25 surviving live
  `convoy:context:*` logs (59 `decisions_log` rows) carry no checkpoint
  rows at all, so live engagement is NOT evidenced in the surviving audit
  trail; the behavior is proven by the suite (`check_tier0_gate.sh`, the
  full convoy-brain suite incl. `test_tier0_gate.py`). *(Since evidenced
  live — and first found broken live: on 2026-10-23 the live tier-0 gate
  got no hit on three identical pre-movement plans, because the route
  options were the oracle's per-request ids; with the options labelled by
  their own segments and the pre-movement own-doc filing it re-ran green
  on 2026-10-24 — 1 hit in 3, 1825 ms saved; Phase I.)* **t0-alpha
  foundation rung** (`predict/nn/foundation_adapter.py` + the ONNX INT8
  artifact at `VVIP/models-local/t0/`, sha256-pinned with NOTICE): the
  quantile-contract rung under the hatch — on Oct 18 **dormant in the
  live containerized oracle** (the container then carried no
  `VVIP_FOUNDATION_MODEL_PATH` and no mounts; the real artifact was
  exercised host-side by `check_t0_forecaster.sh` under the wave2 venv).
  Since the 2026-10-19 hosting decision the oracle image bakes the
  artifact in and sets that env (`Dockerfile.traffic-oracle.gb10`), so
  the rung serves the forecasts — `/health` reads
  `forecast_history.foundation_active: true` on a fresh install of the
  wave-4 tree.
  **P90-robust quantile routing** (`optimize/quantile_objective.py`, knob
  `routing.robust_routing` registered in `shared/schemas/protocol_params.json`,
  drift-guarded by `export_protocol_params.py --check`) and **banded ETAs**
  (`eta_band`/`eta_band_reason` from the validated quantile stream, honest
  label whenever it degrades) + the **model-drift panel**
  (`model_drift_panel.sh`: schema-anchored baseline over the four hosted
  model surfaces, never byte comparison).
- **Wave 3 (Oct 18 evening) — the ledger + repetition proofs.** The
  **degradation ledger**: oracle endpoint
  `GET /api/v1/ops/degradation-taxonomy` (`ops/degradation_taxonomy.py`)
  mines convoy-brain's `decisions_log` into a recurring-cause taxonomy
  (Wave-1 latch firings, tier-0 misses, tactical fallbacks, cadence
  refusals, operator alerts, failed turns; every entry carries a
  `sample_ref` to one real row; an empty log yields an honest empty
  taxonomy). The deck's **DegradationLedger panel** polls it every 10 s.
  Live now (probed this session): 25 contexts / 59 rows scanned, two cause
  families — `alert:low_confidence_decision` ×28,
  `alert:decider_unavailable` ×2. The **repetition gate**
  (`repetition_gate.sh`): run "God's Eye Morning" N times from an
  identical restored baseline against the live argus fleet and the
  terminal DB state the showcase's phase-8 assertions are judged over is
  IDENTICAL across rounds — after normalizing exactly the volatility
  classes that are provably not system output (wall clock, the harness's
  per-run sweep seed, gen_random_uuid/BIGSERIAL identity, one in-process
  counter, engine-loop row multiplicity), every normalization justified in
  a printed manifest; anything else that differs FAILS. `--fast` is the
  offline comparator/normalizer/FAIL-path selftest (the ladder tier); the
  full live gate (tens of minutes, restores the DB as found, restarts the
  ARGUS oracle only) is on demand. **`argus_full_smoke.sh`**: full-system
  live smoke of the clone — every service, every shared host model, the
  deck, and one REAL movement plan — with a bounded converge-wait after
  redeploy; it snapshots the ORIGINAL stack's containers and image tags
  read-only before/after and fails on any drift (liveness included).
- **The `-argus` image split** (Wave redeploy,
  `infra/compose.argus-override.yml`): the clone's tree code has diverged,
  so traffic-oracle / convoy-brain / command-deck now BUILD their own
  `vvip-argus-*:latest` images from this tree — the shared
  `vvip-*:latest` tags are never written by this project; conversely
  postgis + signal-ingress were then byte-identical infra and REUSED the
  shared images with their inherited build stanzas stripped (`build:
  !reset null`) so a project-wide build could never retag them either.
  (Since the original fleet's retirement those two are argus-owned
  `-argus` images too — `VVIP/TECHNICAL_DOCS.md` §13 "Image ownership".)
- **Submission regeneration** (Oct 18 evening): the
  **submission-consistency oracle**
  (`VVIP/scripts/submission_consistency_check.mjs`, the docs-vs-tree/
  vs-artifacts registry incl. a `--selftest` of its own failure paths) is
  itself a `verify_all.sh` tier, and the deck/PPTX/PDF were regenerated
  against the live artifacts (`submission/`, `submission/make_deck.py`).

### Phase I — the work-package waves (WP-01…WP-22) and wave 4: real roads, human authority, 3D (Oct 19–23)
The argus stack became THE system (the original `vvip` fleet was retired
on 2026-10-19), and waves 3–4 closed the distance between the demo and the
city (detail: `VVIP/TECHNICAL_DOCS.md` §16, `VVIP/docs/`):

- **The package waves (WP-01…WP-19)** — the city-fusion spine (one city picture:
  `/api/v1/city/*`, cameras, the event audit, the fusion rail and City
  Vitals), the honest live data plane (real ingestion, the emulator's
  traffic in its own key space so it can never drive a real event's band),
  the chat brain grounded in the city with canvas directives the operator
  applies (and `/mcp`), the God's-eye reconstruction (eleven layers), the
  stolen-vehicle rule (a reported-stolen car's reads are evidence-only
  `R_STOLEN_SIGHTING`; an e-challan approval on it answers 409 — the owner
  is the victim), route updates that supersede but never delete spines,
  the synthetic traffic history kept apart from the real baseline, and
  provenance on every surface. Migrations 012–019.
- **One-command bring-up + boot (WP-08)** — `scripts/veer_up.sh` (READY
  11/11 table) and the systemd `--user` units under `veer.target`; real
  reboots on 2026-10-23 came back to READY 11/11 in 4 min 25 s and 4 min
  27 s with no manual command. **The operator PIN gate** is on: the deck
  is the only LAN-facing service, operators sign in by name, and the
  signed-in officer is the recorded actor of every write
  (`x-veer-officer`, trusted on loopback only).
- **WP-20 — the road network on real OpenStreetMap roads** (user decision
  "Rebuild on real roads"): the 49 segments re-drawn along the real roads
  of their names between real intersections, 34 junctions on their OSM
  nodes, one strongly connected network of ≈192 km (191.76 km measured
  in the store), generated
  deterministically from committed Overpass extracts and re-provable
  offline (`gen_osm_network.py --verify`: worst Hausdorff 7.76 m, worst
  length deviation 0.96 %); real names (1013 Swami Vivekananda Road, 1031
  Kasturba Gandhi Road, 1010 SH71 (Bhat–Motera Road) …); migration 020;
  © OpenStreetMap contributors, ODbL 1.0. Everything downstream (routing,
  the twin, cameras, the ingress feed, emulator tapes, the God's-eye) was
  regenerated from it.
- **WP-21 — escort authority, "officer approves every switch"** (user
  decision): during a live escort the decider only PROPOSES a route
  switch, Plan B, a hold or new closures; a named officer approves or
  rejects each one on the convoy HUD or the `/ops` Decision Queue; with no
  answer in 90 s (configurable 15–600) the proposal expires and the convoy
  holds its current approved plan. The decider never switches a route on
  its own — the human-veto guarantee.
- **WP-22 — the God's-eye in true 3D** (merged and verified on a keyed,
  signed-in preview of the integrated tree): signed-in operators see
  Google Photorealistic 3D Tiles over Cesium World Terrain with Bing
  imagery — the chip reads `PHOTOREAL 3D · GOOGLE` and `imageryMode`
  `ion-photoreal`; the ion token stays server-side and reaches only a
  signed-in session, with 0 CSP violations. The overlays are draped on the
  3D city — every overlay layer audits 0 floating, the e-challan pins and
  the pursuit included, and the selection halo, the AI's agent notes and
  the REPLAY stand on the ground; City Command opens on a judge-grade
  oblique (the live action at −42°, the camera 2.3–2.7 km up), with the
  Google / Cesium ion / OSM credits legible above its fusion rail. Public
  pages stay keyless.
- **After the merge — the integrated tree's fixes**: the pursuit basis
  of a reported-stolen vehicle is only its approved `R_STOLEN_SIGHTING`
  (an e-challan basis → 422), and **one officer approval authorises one
  pursuit** (reuse → 422; every recommendation row carries its `pursuit`,
  and `/ops` and `demo_reset.sh` skip a spent approval, so the showcase's
  scripted approval never pre-empts the human's); the emulator's positions
  sit on the road line (`ST_LineInterpolatePoint`), its wire rows are
  labelled synthetic (data_quality 2; 1 only as the outlier marker, never
  0), its movements end at their route's ends, and a replay whose recorded
  route is no longer a legal path — a run recorded before the conversion —
  is refused (422 `route_not_on_current_network`); the network step also
  re-anchors the EMULATED reads (and their copies in the run tapes) and
  the use-case profiles, applies whenever the store is off the generated
  network and restarts the oracle, emulator and deck once; event markers
  sit on their route.
- **WP-15 — truthful gates, docs and submission**: one sign-in helper for
  every gated tool, the offline/live gate ladder, the judge's journeys
  J1–J7 (92 checks over J1–J6), `demo_reset.sh` (stops at PENDING — a
  human approves live; `--cancel-debris` clears the rehearsal debris
  through the audited lifecycle), the repetition gate's ownership-scoped
  restore (only the rounds' own rows; anyone else's activity fails the
  gate, untouched), the docs and this deck re-proved from code and a
  fresh-install stack.
- **The live pass (Oct 23–24)** — wave 4 deployed to the live stack
  (2026-10-23 23:33 IST, `veer_up.sh --build`, READY 11/11, migration 020
  applied) and accepted there in 22 steps: 19 green first time; the three
  that failed were fixed and re-ran green — the live tier-0 gate (the
  pre-movement route options were the oracle's per-request ids, so the
  cache could never hit; now labelled by each route's own segments, plus
  the pre-movement own-doc filing — redeployed 01:20, re-run: 1 hit in 3,
  1825 ms saved) and two canvas smokes that tripped over acceptance debris
  and the stale pre-rule pursuit (green after the pre-judging reset). The
  flagship showcase passed three times on the live stack (once alone,
  twice under the repetition gate, whose rounds were identical): the
  stolen plate's 6 reads became 6 evidence-only `R_STOLEN_SIGHTING`, an
  e-challan approval on it was refused 409, the sighting approved under
  the label `Scripted demo officer (showcase script)` authorised the
  pursuit, 10 choke junctions ranked, no fine anywhere. The journeys went
  92/92 on the live deck, the final reset left the judged state verified
  (one PENDING sighting, AUTHORISE PURSUIT offered, no debris), and the
  hero shots were recaptured on it (the operator views in photoreal 3D);
  on the canvas an
  e-challan approved before the stolen-vehicle rule now reads
  `SUPERSEDED · STOLEN`.

## 3. The architecture, as it stands

```
HOST MODELS (systemd --user units under veer-models.target, loopback-only):
  :8083 pplx-decider-v1-27b (strategic brain, typed questions)   veer-decider.service
  :8084 aditi-ps18-v7h Gemma-4-12B Q4_K_M (llama-server, tactical) veer-llama.service
  :8085 embedding-service (pplx-late + bge-m3)                    veer-embed.service

FLEET (docker compose project vvip-argus, every image built here as -argus):
  postgis :56434 (migrations 001-020, the 49-segment OSM road network)
  valkey :6380   nats :4223/8223   signal-ingress (Rust, edge-synthetic, Arrow→NATS)
  traffic-oracle :8091 (ML + optimization + adaptive + twin + city fusion + enforcement)
  convoy-brain   :8092 (decider → Gemma → heuristics; live escort: the AI proposes,
                        the officer approves every switch)
  event-emulator :8090 (causes only, every row labelled EMULATED)
  command-deck   0.0.0.0:5273 (SvelteKit, the operator PIN gate: / /ops /gods-eye
                        /citizen /driver /comms /chat; 3D for signed-in operators)

BOOT: veer.target = veer-models.target + veer-up.service (scripts/veer_up.sh --boot)
```

The emulated/real split: the emulator, the ANPR generator and the ingress
feeds produce ONLY causes, all labelled; every decision, adaptation,
recommendation and corridor action is the real stack working, audit-logged
— and every approval carries the officer's name: a signed-in human in the
judged demo, while a script's unattended approval says it is the script's
(`Scripted demo officer (showcase script)`; the 2026-10-18 showcase used
the cast name "Duty Officer R. Mehta").

## 4. The argus stack is the system

The clone that started as a parallel instance on 2026-10-14 became the
live system when the original `vvip` fleet was retired (2026-10-19). Its
identity lives in `infra/compose.argus-override.yml` (ports, container
names, the `-argus` images, loopback binds), `scripts/veer_env.sh` (the one
host environment, `~/.config/veer/veer.env`), `scripts/veer_up.sh` and
`infra/systemd/`. The deck's proxy defaults to this stack's ports
(`ORACLE_PORT` 8091, `BRAIN_PORT` 8092, `EMULATOR_PORT` 8090). The only
thing still shared with the retired tree is the model-weights directory
(`VVIP/models` → `~/Desktop/Veer/VVIP/models`).

## 5. Verification state (wave 4)

Measured for the wave-4 documentation pass on a fresh install of the
release tree (migrations 001–020 + the bring-up's seed order) and from code
(the commands are named in `VVIP/TECHNICAL_DOCS.md` §13 and §16):

- **The network**: 49 segments, 34 junctions (34/34 on OSM nodes), 198
  movements, 186 road-graph edges, one strongly connected component,
  191.76 km (PostGIS spheroid length; ≈192 km); `gen_osm_network.py --verify` exit 0 (worst Hausdorff 7.76 m,
  worst length deviation 0.96 %); 11 signal programs, 28 emulated camera
  sites, 18 agency stations; every segment served as `geometry_basis: osm`.
- **Tests**: 2709 pytest tests collected by the gate venv on the deployed
  tree (convoy-brain 635, corridor-store importer 22 + store 107,
  embedding-service 113, event-emulator 328, traffic-oracle 1500,
  command-deck 4); signal-ingress `cargo test` 120 passed (recounted
  2026-10-24, after the tier-0 fix).
- **Boot**: real reboots on 2026-10-23 → READY 11/11 in 4 min 25 s and
  4 min 27 s, no manual command (`journalctl --user -u veer-up.service`).
- **Release gates — run live on the deployed stack (2026-10-23 23:33 →
  2026-10-24 01:26 IST)**: `veer_up.sh --status` READY 11/11;
  `verify_all.sh` offline and `--live` ALL TIERS PASSED;
  `argus_full_smoke.sh` ALL PASS, its negative control failing exactly
  the four data-plane legs; `fleet_smoke.sh` ALL PASS; the drift panel
  4/4; the flagship showcase SHOWCASE PASS ×3 and the repetition gate's
  two rounds identical; the journeys 92/92; the design, gods-eye and 3D
  smokes green; the screens camera 40/40; no secret in any log. The
  tier-0 gate and the canvas-ux / city-command smokes failed first and
  re-ran green after their fixes (`VVIP/TECHNICAL_DOCS.md` §13 has the
  steps, causes and times). The showcase artifacts on disk are the live
  run of 2026-10-24 00:01 IST; the hero shots were recaptured on the
  staged state at 01:25.
- History, kept: the 2026-10-14 clone ran `verify_all.sh` ALL TIERS PASSED
  (422 pytest passes then) and the flagship showcase PASS; the 2026-10-18
  waves drove the then-ladder green again (1138 pytest collected then).

## 6. What was NOT covered (the honest boundary)

- Real camera feeds and real ANPR hardware — reads are emulated by design
  behind the `AnprSource` port; the camera sites are emulated, built to
  register the state's ICCC / CCTV / ITMS inventory
- Real Jan Rakshak / police / 108 units and real convoy GPS — emulated,
  clearly labelled
- Field traffic data — the roads are real (OpenStreetMap), but every
  traffic observation is synthetic; the twin's calibration needs ≥ 24 real
  field hours and a replay MAE ≤ 5 km/h, so the signal writer and every
  non-baseline adaptive plan fail closed, honestly
- Multi-city networks — Ahmedabad only
- Usability testing with real operators — the design is expert-judged

## 7. Key files (where to look for what)

| File | What it is |
|---|---|
| `KAUSHIK_HANDOFF.md` | Daily commands, ports, gates, shared-vs-owned boundary |
| `docs/history/GODS_EYE_CONTEXT_DOWNLOAD.md` | The mentor's directive + R1–R10 requirements |
| `PROBLEM_STATEMENT_GUJARAT.md` | The problem, beneficiaries, gap analysis, citations |
| `VVIP/docs/USE_CASES.md` | The 8 event types with Indian context |
| `VVIP/docs/GODS_EYE_INTEGRATION.md` | Canvas architecture + ethics guardrails |
| `VVIP/docs/ACTIVE_MOVEMENT_ADAPTATION.md` | The R9 module |
| `VVIP/TECHNICAL_DOCS.md` | Full service/API/schema reference |
| `submission/DECK.md` + `make_deck.py` | The submission deck (regenerable PPTX/PDF) |
| `VVIP/scripts/verify_all.sh` | The acceptance ladder (offline by default; `--live` signs in once) |
| `VVIP/scripts/showcase_run.sh` | The flagship demo |
| `VVIP/scripts/bench_stack.sh` | Throughput + scenario-suite benchmarks |
| `VVIP/scripts/argus_full_smoke.sh` | Full-system live smoke of the clone + original-stack guard |
| `VVIP/scripts/repetition_gate.sh` | Consistency-under-repetition gate (`--fast` selftest / full live) |
| `VVIP/scripts/submission_consistency_check.mjs` | Submission-consistency oracle (deck/docs vs tree vs artifacts) |
| `VVIP/scripts/veer_up.sh` · `VVIP/infra/systemd/` | The one-command bring-up and boot auto-start |
| `VVIP/scripts/gen_osm_network.py` · `VVIP/scripts/data/osm_network.json` | The real-road network and its evidence |
| `VVIP/scripts/journeys.mjs` · `VVIP/scripts/demo_reset.sh` | The judge's journeys; pre-judging hygiene that stops at PENDING |

## 8. Where we are (the clock)

The idea submission (closed 15 Oct 2026) is behind us; Veer is entered for
the **national round** — judges clone the repo and watch a live,
human-in-the-loop demo on this GB10 box at `http://127.0.0.1:5273`, a
signed-in officer approving live on `/ops`. The release-day sequence ran
on the deployed stack on 2026-10-23/24, each write with the team's
go-ahead: the live smokes → the showcase → the repetition gate →
`scripts/journeys.mjs --live` → `scripts/demo_reset.sh --apply --officer
'<name>' --cancel-debris` (run unattended as `Scripted demo officer (demo
reset)`); then the tier-0 fix's redeploy and gate re-run, a final reset at
01:23 and the hero screenshots recaptured on that staged state at 01:25;
the deck was re-rendered from the live artifacts (`submission/`). What is
left before judging: re-stage with `demo_reset.sh --apply --officer
'<name>' --cancel-debris` within ~20 minutes of it (the staging sweep
staged at 01:23 IST on 2026-10-24 runs only until 02:08) and fill in the
team's names.

**One rule to hold above all: nothing anti-government, anywhere. The system
strengthens government capability** — vehicles only (never faces or
persons), every penalty human-approved, no fine on a stolen car's owner,
every escort route switch an officer's call.
