# Veer — Submission Deck (7 slides)

*Hack for Social Cause · Viksit Bharat Young Leaders Dialogue 2027*
*Team: ________ · State: Gujarat · Themes: Governance & Civic Technology
(primary) · Disaster Mitigation & Large Gatherings (secondary)*
*(Rendered to PPT/PDF ≤10 MB as `submission/Gujarat_Veer_Deck.pptx` / `.pdf`
— team name "Veer" per `PROBLEM_STATEMENT_GUJARAT.md`; rename per
`<State>_<TeamName>_Deck.pdf` if the registered team name differs. Slide-5
numbers are pulled live from `VVIP/scripts/impact_results.json` by
`submission/make_deck.py`. **Interface of record: the SvelteKit
command-deck at `http://127.0.0.1:5273` on the GB10 box, behind the
operator sign-in — `/` the Convoy Command cockpit, `/ops` the situation
wall, `/gods-eye` the city in photorealistic 3D, `/citizen` and `/driver`
public, `/comms`, `/chat` — the canonical surface for every audience; the
legacy React `frontend/` is the offline fallback demo** —
`VVIP/README.md` "The Interface", `VVIP/TECHNICAL_DOCS.md` §2.7 and §16.)*

---

## Slide 1 — When a corridor closes, an Indian city holds its breath

> We built the intelligence that lets it exhale — corridors managed to the
> second, not frozen for half an hour. And not just for convoys: **a
> city-scale platform where VVIP routing is one component among many — on
> Ahmedabad's real roads, with a named, signed-in officer deciding every
> penalty, pursuit and route switch.**

- Today's default: a protected movement freezes entire corridors for
  **15–45 minutes per junction**, coordinated by **phone, radio and WhatsApp
  across five separate hierarchies** (traffic police, district admin,
  SPG/state security, municipal signals, 108 dispatch) — none sharing a live
  picture. The passage itself takes seconds per junction.
- The harm is documented: ambulance held 5–10 min with siren running during a
  Union Home Minister's convoy (Mumbai 2022); a heart-attack death after a
  ~20-minute ambulance hold (Kanchipuram 2018); another ambulance halt for a
  VIP movement this February (Agartala). Commuters — Ahmedabad's own papers
  have run this story since 2009. Even the Gujarat CM's convoy has been
  stuck ~15 minutes in this same city (2022).
- **The protocol is not the villain.** The MHA Blue Book itself says traffic
  is to be *"regulated, not stopped."* The gap is tooling: paper protocol,
  phone-and-radio coordination.
- **And it is one failure mode in many costumes.** The same freeze — a
  corridor whose occupancy nobody can schedule, predict and release — hits
  the Rath Yatra's 14 km old-city loop (148 annual editions), Kumbh-class
  perimeters (240→660 million visits, 2019→2025), the 24,000-runner
  riverfront marathon, Republic Day parade strips, ~130,000-person stadium
  egress at the world's largest cricket ground, monsoon flood evacuations
  (Gujarat 2024: 28+ dead, 24,000+ relocated) and months-long metro work
  zones. **Our answer is a city-scale Corridor OS — the VVIP run is the
  base case, not the boundary** (full library: `VVIP/docs/USE_CASES.md`) —
  and the same backbone carries everyday enforcement: a stolen-vehicle
  FIR traced from watchlist to interception plan, vehicles only, with a
  human in every penalty loop (`VVIP/docs/GODS_EYE_INTEGRATION.md`).

## Slide 2 — The gap, precisely (state problem statement)

Pilot geography: Ahmedabad's **real road network**, traced on
OpenStreetMap — **49 segments, 34 junctions, ~192 km**, every segment on
the real road of its name between real intersections (Ashram Road, SG
Highway, CG Road, SP Ring Road, the Gandhinagar Highway, the old-city
bazaar belt, Motera Stadium Road; © OpenStreetMap contributors, ODbL 1.0 —
`VVIP/scripts/data/osm_network.json`).

| # | What does not exist today | Consequence |
|---|---|---|
| G1 | No shared operational picture across the 5 agencies | 15–45 min blanket holds |
| G2 | No prediction in the loop (fixed advance margins) | Holds far longer than the convoy needs |
| G3 | **No citizen advisory channel** | The commuter discovers the closure at the barricade |
| G4 | **No emergency-passage request channel for 108** | Golden-hour minutes burn; documented deaths |
| G5 | No measurement or accountability | Nothing improves; over-caution every time |

Beneficiaries (named): the daily-wage commuter on Ashram Road; the cardiac
patient in a 108 ambulance (Gujarat: ~585 EMRI ambulances, ~5 emergency trips
each daily); the constable absorbing public anger at the barricade; the duty
officer satisfying Blue Book security with zero tooling — and, through the
use-case library, the pilgrim, the runner, the spectator and the flood
evacuee on the same corridors.

## Slide 3 — The platform: one city-scale OS, the public's protagonist

Same engine the operators run — **but the Very Important Persons are the
Voter on the bus, the Victim in the 108 ambulance, and the Vulnerable
patient for whom ten minutes matter.**

- **One canonical interface for every audience:** the SvelteKit
  command-deck at `:5273` — the **Convoy Command cockpit** at `/`, the
  `/ops` situation wall, the `/gods-eye` cinematic, the public `/citizen`
  and `/driver`, the trilingual `/comms` desk and `/chat`. Operators sign
  in by name; every approval is recorded under it. One design system,
  verified surface-by-surface by a headless camera (40/40 checks). The
  React demo is retained only as the offline fallback.
- **The God's-eye — real 3D Ahmedabad, one picture for every agency:**
  signed-in operators see Google Photorealistic 3D Tiles over Cesium World
  Terrain (chip `PHOTOREAL 3D · GOOGLE`) with the overlays draped on the
  city, none left floating — the simulated congestion feed on the 49 real
  roads, event spines, the pursuit trace and interception fan, vehicle traces, units,
  dispatches, cameras, signals, anomalies — and City Command opens on an
  oblique judge's view of the live action; public pages stay keyless.
  Eleven integrity-validated layers, FLIR-class sensor modes, share links
  (`VVIP/docs/GODS_EYE_INTEGRATION.md`).
- **The officer approves every switch:** during a live escort the AI
  decider only **proposes** a route switch, Plan B, a hold or new
  closures; a named officer approves or rejects each one, and a proposal
  nobody answers in 90 s expires with the **current plan held**. The AI
  never switches a route on its own — the human-veto guarantee.
- **Multi-agency and event-agnostic by construction:** a generalized event
  model (`events.corridor_events`) expresses any corridor operation on five
  axes — protection class (Z+/Z/Y/X/**none** — *none* = a public event with
  no protectee), crowd class, event kind (protected movement, procession,
  mass gathering, race, ceremonial, egress surge, emergency evacuation,
  work zone — **plus the enforcement family's `crime_incident` and
  `vehicle_pursuit`**), footprint, phases. The kind selects **closure
  templates, never code paths**.
- **The enforcement family, on the same rails:** stolen-vehicle FIR →
  lawful-basis earmark (retention capped) → emulated ANPR camera reads →
  **evidence-only sighting — never a fine on the owner, who is the
  victim** (an e-challan approval on that plate is refused, 409) → a named
  officer approves the sighting → operator-initiated pursuit (one
  approval, one pursuit; an e-challan is never its basis — 422) →
  pgRouting interception plan → a unit to the choke, approved by a human. Vehicles
  only, via ANPR plates — no faces, no persons; plates masked unless an
  officer is signed in; Jan Rakshak, police, traffic, 108 and fire dispatch
  through the same human-approved, audited channel.
- **Predictive rolling holds:** closures trigger **60–180 s** before the
  corridor user reaches a junction and release as it passes — **~2–3-minute
  holds instead of 25-minute freezes**, exactly what the Blue Book asks for.
  For public events the same machinery chooses the gentler policy — in the
  flagship run the engine's own answer for a procession + monsoon +
  ambulance was **signal hold at 45 s: "regulated, not stopped."**
- **A two-tier AI command mind, at the edge:** a 27B strategic *decider*
  owns strategy and tool selection; a Gemma 4 12B *tactical* tier drafts
  tool arguments and writes the operator-facing narrative (dossiers,
  advisories, chat), a deterministic floor beneath both; checkpoints fire
  only on real events, every decider answer logged with its probability
  distribution and confidence. **Active
  Movement Adaptation (AMA)** keeps every published plan inside protocol
  floors and a twin shadow-evaluation — **failing closed**. Runs on one
  GB10-class edge box.
- **Citizen Advisory + 108 Green Corridor:** free multilingual corridor
  alerts (English/हिंदी/ગુજરાતી) — which stretch, when, for how long, the
  alternate; and the driver's one-tap request → it waits in the duty
  officer's queue → a named officer approves on `/ops` → a window with
  countdown and a golden-hour counter on the driver's own page.

## Slide 4 — Working now (demo, honestly)

- **One interface, live on the box:** `bash scripts/veer_up.sh` brings the
  whole stack up — and it **starts itself at boot**: real reboots on
  2026-10-23 came back to **READY 11/11 in 4 min 25 s** with no manual
  command. Open `http://127.0.0.1:5273`, sign in by name: `/` is **the
  Convoy Command cockpit** (served directly), `/ops` the situation wall
  (band masthead, Corridor Operations Board, Pursuit & Watchlist, the
  Decision Queue with its escort lane, Jan Rakshak Dispatch, City Signal
  Plans, the AMA card, the Decision-Audit Stream, the God's-eye canvas).
  Per-surface acceptance is a camera, not a claim:
  `services/command-deck/tests/screens-verify.mjs` — **40/40 checks green**
  on the live deck (2026-10-24; artifacts at `tests/artifacts/screens/`).
  The legacy React `frontend/` remains the **offline fallback** (scripted
  simulation, no GPU, no backends; it ships with an 11-check e2e journey).
- **Deployed, then accepted on the live stack (night of 2026-10-23/24
  IST):** the release went live at 23:33 (`veer_up.sh --build`, READY
  11/11, the real-road network `osm 49/49 · 34 junctions`, migrations
  001–020) and its 22-step acceptance ladder ran there — **19 passed
  first time**. The 3 that failed are on the record with their fixes:
  the live tier-0 gate found no cache hit on three identical plans (the
  decider's route options were the oracle's per-request ids — now labels
  derived from each route's own segments, and a pre-movement answer is
  also filed under the movement's own decision doc; redeployed at 01:20
  and **re-run green: 1 hit in 3, 1825 ms saved**), and two canvas smokes
  tripped over acceptance debris and the stale pre-rule pursuit — their
  failed checks **re-ran green** once the pre-judging reset cleared them.
  The judge's journeys passed **92/92**
  on the live deck, and the final reset (01:23) verified the judged
  state: one PENDING stolen-vehicle sighting, AUTHORISE PURSUIT offered,
  no debris on `/ops`.
- **The flagship showcase — "God's Eye Morning"** (`scripts/showcase_run.sh`
  on the deployed live stack: **exit 0, SHOWCASE PASS** three times that
  night — once alone, then twice under the repetition gate, whose two
  rounds left **identical** canonical end states; the artifacts on disk
  are the gate's last round, one run: `showcase/showcase_results.json`
  **2026-10-23T18:31Z** (00:01 IST) + `showcase/pursuit_chain.json`):
  Rath Yatra + monsoon burst + one 108 ambulance **+ a stolen-vehicle
  report (FIR 4401/2026, Kalupur PS)** injected through the event emulator
  into the running fleet (761/761 + 583/583 frames delivered), and the
  real engine answers everything at once: **31 audited decisions this
  run** (25 situation + 6 parameter), 1 band transition (AMBER → RED; the
  city band back to GREEN once the event ended), the 108 escalation
  (TAKEOVER → operator handoff); a 12-replication twin of the morning —
  its audited schedule carries the scenario's **4 green-corridor windows**
  (scripted 108 crossings: causes, not engine grants) — puts the
  ambulance delay at **231.92 s** (model output);
  plate GJ27EM9001 **earmarked** (lawful basis `stolen_vehicle_fir`,
  30-day retention) → **6 emulated ANPR reads** (EM-CAM-01..04, EM-J01B
  and EM-J05 at 95–115 km/h, every row `source=emulated_anpr`) →
  **`R_STOLEN_SIGHTING` ×6 — evidence only, the e-challan withheld** (0
  penal recommendations; the penal rules that would have fired,
  `R_SPD_SEGMENT` ×6 and `R_SIGNAL_VIOLATION` ×2, recorded as withheld),
  and an e-challan approval on the plate **refused, 409** → the newest
  sighting approved by `Scripted demo officer (showcase script)` — the
  pursuit's only basis → **10 choke junctions ranked** by pgRouting off
  the latest sighting (top: junction 15, unsignalised, score 0.008683) +
  a **live 12-position trace** on the God's-eye canvas (the trace's 24 h
  window: these 6 reads and the 23:51 run's 6); the scripted
  pursuit was closed when the run ended (its approval spent — one
  approval, one pursuit); a Jan Rakshak unit (JR-EM-01) dispatched and
  approved end to end; the city signal-policy guard **refused** the
  uncalibrated commit for 11 junctions (409 `shadow_eval_failed_closed` —
  the twin's calibration replay is `no_data`: **no field observations**,
  so nothing can calibrate it), the refusal reported in the oracle's
  last-plan answer (`showcase/signal_policy.json`), nothing written. No
  fine anywhere in the stolen-vehicle chain.
- **The emulated/real split, stated plainly:** the roads are real; the
  traffic feed, the ANPR reads, the camera sites and the agency units are
  emulated or simulated and **labelled so on every surface** (every ANPR
  row born `emulated_anpr`; `live_anpr` is reserved for a real vendor feed —
  the state's ICCC / CCTV cameras — behind a frozen port). The emulator
  injects *causes only* (the twin's green-corridor windows are such
  causes — the scenario's scripted crossings); every decision, band
  transition and escalation is the real stack's, and every
  pending→approved transition carries the
  name of the officer who made it — a signed-in human in the judged demo;
  a script's unattended approval says so (`Scripted demo officer
  (showcase script)`).
- **Screenshots — the hero shots recaptured 2026-10-24 01:25–01:26 IST on
  the live stack in its clean, staged judging state** (after the
  pre-judging reset; 1440×900, pixel-proven non-blank; the three operator
  views on `PHOTOREAL 3D · GOOGLE`, the public page keyless):
  `VVIP/showcase/showcase_gods_eye_city.png` — the 3D city at rest, the
  49 real roads draped on the tiles in the simulated feed's colours
  (`FLOW 49 · SIM`), **110 entities** (10,515-colour PNG proof,
  `shots_city.log`) · `VVIP/showcase/showcase_pursuit_trace.png` — the
  camera on the stolen vehicle's trace centroid (EMULATED reads), the
  trace as it stood at capture (a 13-point trace, `shots_manifest.json`;
  10,031-colour proof), its pins reading `STOLEN · NO FINE · APPROVED`
  and — on the e-challan a rehearsal script approved on 2026-10-18 under a
  cast officer name, before the stolen-vehicle rule —
  `SUPERSEDED · STOLEN` · `VVIP/showcase/showcase_citizen_advisory.png` —
  the public Daylight advisory (the deck's public projection, the same
  page every visitor gets): no pursuit, no plate, **0 event cards** (the one live
  event, the staged sweep, is operator-only; 2,060-colour proof,
  `shots_rest.log`) · `VVIP/showcase/showcase_ops_wall.png` — the `/ops`
  wall: band GREEN, 1 pending decision, 2 Decision Queue cards (the
  stolen-vehicle card with AUTHORISE PURSUIT and its pursuit card, no
  basis yet; 7,268-colour proof, `shots_ops.log`). On the city and
  pursuit shots the fusion rail's newest human-decision rows are the
  01:23 reset's, under its honest label
  `Scripted demo officer (demo reset)`.
- **Measured-model impact** (`IMPACT_REPORT.md`, deterministically
  regenerated on the real-road network): junction-freeze commuter delay
  falls **25×–506× (central 100×)** under the stated assumptions ledger —
  structural (delay ∝ hold²), so even the conservative bound clears the
  original unmeasured "6×" we no longer lead with.
- **Under the hood — built, with tests; only measured numbers quoted:**
  **2709 pytest** tests collected on the deployed tree (incl. the
  emulator's 328, the traffic-oracle's 1500 and convoy-brain's 635 after
  the tier-0 fix; every suite run whole: 2624 pass, 85 skip themselves
  when an optional dependency or a scratch store (a database, a Valkey) is absent) and the
  Rust ingress's 120 cargo tests; the generalized
  events schema and the enforcement tables (migrations 007–011) extended
  by 012–020 — the real-road network is migration 020 — **migrations
  001–020** on a fresh install. The two-tier
  brain (27B decider + Gemma 4 12B + dual embedders) resident on a 121 GiB
  GB10 edge box; bench (`scripts/bench_results.json` +
  `bench_adversarial_report.json`, **2026-10-13T13:24Z**): decider
  **455.78 tok/s, p99 1106.8 ms**; Gemma 20.09 tok/s; embeddings 92.7 ms;
  62.73 GiB resident; adversarial decision suite **19/19 passed (score
  100)**, avg 29.19 s / max 57.38 s per scenario. Kept visible: open
  quality gaps tool coverage **0.684** and keyword coverage **0.561** (pass
  the gate, tracked; keyword coverage moves run to run), and a same-day
  bench run with one 69.99 s scenario that still passed (the 60 s line is
  scored, not a hard gate; that report was overwritten — documented
  history). Implemented, awaiting trained weights — the DSTGAT neural
  forecaster ships as PyTorch architecture only. Simulation-labelled, never
  faked.

### Demo storyboard (the judged live demo, in order)

1. **Open `http://127.0.0.1:5273` on the box and sign in** as the duty
   officer → `/` is **the Convoy Command cockpit** over 3D Ahmedabad; step
   into **`/ops`** — band masthead live, the event board, the
   Decision-Audit Stream scrolling.
2. **`/gods-eye`** fullscreen — the photorealistic 3D city with the live
   congestion network draped on the real roads; flip sensor modes; paste a
   share link to restore the exact view.
3. **The stolen vehicle, on screen:** an EMULATED ANPR read of plate
   GJ27EM9001 lands; the Decision Queue shows an **evidence-only
   stolen-vehicle sighting** PENDING — its e-challan WITHHELD (the owner is
   the victim); the officer approves the sighting by name — one approval,
   one pursuit — opens the pursuit, and the interception plan ranks the
   choke junctions; a unit is dispatched to choke #1 and approved — it
   moves on the canvas.
4. **The escort:** plan a protected movement on `/`; during the escort the
   AI **proposes** a re-route ("AI PROPOSES … — APPROVE / REJECT · expires
   in mm:ss"); the officer approves it — or lets it expire and the convoy
   holds its plan.
5. **The public answers:** `/citizen` (Daylight) — the same morning in
   plain language, emulated events badged SIMULATED FEED · EMULATED (with
   a public event live — e.g. the emulated living city of `veer_up.sh
   --demo`; the staged sweep alone is operator-only, so the page then
   reads "no holds"); then
   **`/driver`** — request → "awaiting duty officer" → the officer approves
   on `/ops` → the open window with the live countdown and the golden-hour
   counter.
6. **`/comms`** — the same facts in English, हिंदी and ગુજરાતી, side by
   side; **`/chat`** — "show me the stolen vehicle on the map": the answer
   comes with a suggestion chip the officer applies.
7. **Close on the wall:** every decision of the session is a row in the
   audit stream, each under a named officer.
8. *(Offline coda, if asked)* the legacy React fallback demo runs the
   scripted simulation with no backends — clearly labelled as the
   fallback, not the interface of record.

## Slide 5 — Impact for Viksit Bharat 2047 (from the impact run + the use-case library)

- **Per movement (central case, modelled on the real-road network):**
  commuter delay drops from ~1,132,000 to ~11,300 commuter-minutes when
  all 34 junctions of the 49-segment network are frozen (an upper-bound
  framing; per frozen junction ≈ 33,291 → ≈ 333); vehicles caught in holds
  fall from ~60,367 to ~6,037.
- **Reduction in junction-freeze commuter delay: 25×–506× (central 100×)** —
  the ratio does not depend on the junction count; delay scales with hold
  duration squared.
- **Per year** (250 movement-days — RTI-able constant): 4.67 million
  commuter-hours returned; 2.52 million litres of idle fuel and ~6,303
  tonnes of CO₂ avoided (modelled).
- **Health:** ~33,000 golden-hour minutes/year returned (12 intersecting
  trips/day × 11 min) — minutes returned to the golden hour, never "lives
  saved"; exactly what the documented holds (5–20 min) and the model support.
- **One engine, eight corridor classes + the enforcement family — the
  national calendar argument** (`VVIP/docs/USE_CASES.md`, each with
  documented reality and a runnable scenario on the real roads):
  protected movements (the base case) · the 148-edition Rath Yatra ·
  Kumbh-class mass gatherings (240→660 M visits) · World Athletics-calendar
  marathons · the two national ceremonial days · ~132,000-seat stadium
  egress · monsoon flood evacuation (the Gujarat 2024 class — the Disaster
  Mitigation lock) · published metro/bullet-train work zones — plus the
  stolen-vehicle watchlist-to-interception chain on the same backbone.
- **Accountability (SDG 16):** after-action data per event reaches planners
  for the first time; every AI decision logged with distribution +
  confidence; every penalty a recommendation until a named officer
  approves it, with an append-only audit trail; every escort route
  switch an officer's call;
  **vehicles-only enforcement with lawful basis and capped retention** — no
  person-tracking, no fine on a stolen car's owner; protectee
  identities/destinations never logged.
- SDG 11 (sustainable cities) · SDG 3 (golden hour) · SDG 16 (accountable
  institutions) · SDG 13 (flood-response resilience).

## Slide 6 — Team, adoption, sustainability

- **Team (≤3):** [Name 1 — platform/ML] · [Name 2 — civic layer/outreach] ·
  [Name 3 — operations/impact], [institution].
- **Who runs it after the hackathon:** a Smart City SPV / city traffic
  police pilot on one corridor; BOM is one GB10-class edge box (the browser
  demo runs on any laptop); it plugs into the state's ICCC / CCTV / ITMS
  camera inventory and 108/EMRI dispatch rather than replacing them. Open
  source (MIT) — any state can fork.
- **Roadmap:** T+1 mo: register the city's ICCC / CCTV cameras as camera
  sites and land the first live ANPR adapter against a real vendor feed ·
  T+3: pilot design with one city + 108 dispatch; real field traffic to
  calibrate the twin (≥ 24 field hours); lift the two open suite quality
  gaps (tool coverage 0.684, keyword coverage 0.561); first trained DSTGAT
  weights · T+6: two more languages; event-corridor preset for a real
  gathering (Rath Yatra / match night) with the city.
- **Costs:** the intelligence runs at the edge; marginal cost per movement
  ≈ zero; alerts ride existing SMS/WhatsApp rails.

## Slide 7 — Disclosure of AI-tool usage & references

- **AI usage disclosure (mandatory):** the base prototype and our
  enhancements were developed with the help of AI coding assistants
  (including agent sessions used to build the model stack, the
  citizen/ambulance surfaces, the event emulator, the God's-eye canvas and
  its 3D draping, the real-road network generator, the command-deck
  interface — the `/ops` situation wall and the Daylight public surfaces —
  the enforcement/watchlist chain, escort authority, the impact harness and
  documentation). The decision *tools* are deterministic, team-reviewed
  code (optimizer, classifier, simulator, enforcement rules), and the
  forecaster's live rung is a third-party zero-shot model run with fixed
  weights (t0-alpha, Apache-2.0 — our own DSTGAT awaits training);
  the two-tier reasoning layer (27B decider + Gemma 12B) is logged
  answer-by-answer with probability and confidence, and no AI output acts
  unreviewed in the decision path — the security veto is human by design,
  and so is every penalty, every pursuit, every dispatch and every escort
  route switch: the AI proposes, a named officer decides. The interface of
  record is the backend-wired command-deck at `:5273` behind the operator
  sign-in; the screenshots on these slides were taken on it against the
  running live stack (recaptured 2026-10-24 in the staged judging state —
  the operator views in photorealistic 3D, the public page keyless); the
  legacy React demo runs a clearly-labelled scripted
  simulation as the **offline fallback**; the flagship showcase injects
  emulator-generated *causes* into the real stack (camera reads labelled
  `emulated_anpr` at the row level, unit positions labelled emulated
  projections); every statistic on these slides comes from the cited
  sources, the falsifiable assumptions ledger of `IMPACT_REPORT.md`, or
  the in-repo measurement artifacts (`scripts/bench_results.json`,
  `showcase/showcase_results.json`, `showcase/pursuit_chain.json`,
  `services/command-deck/tests/artifacts/screens/`) — model outputs are
  labelled as modelled, always. Road geometry © OpenStreetMap
  contributors, ODbL 1.0.
- **References:** MHA Blue Book protocol summary; Free Press Journal (Mumbai
  ambulance hold, Sept 2022); Kanchipuram 2018 case; Agartala Feb 2026;
  Times of India Ahmedabad (2009; riverfront-run diversions May 2024);
  Vibes of India (2022 CM convoy); GVK EMRI Gujarat fleet/trip figures;
  NDTV (26 Jun 2025) & utsav.gov.in (148th Rath Yatra); Gujarat Samachar
  (Jul 2026, 35-drone monitoring); Wikipedia/UP government (Kumbh
  attendance 2019→2025); ahmedabadmarathon.com, Olympics.com, ThePrint
  (2024 marathon); Gujarat CMO (76th Republic Day, Jan 2025); Wikipedia +
  Ayen News (Motera capacity / IPL 2026 final); India Today (8 Mar 2026, T20
  WC final deployment); BBC/NDTV/ReliefWeb (Gujarat floods, Aug 2024);
  PIB + Indian Express (metro Phase 2 approvals, Kankaria Road closure);
  OpenStreetMap (the road network); MoRTH ITS / Smart Cities Mission / PM
  Gati Shakti; MyBharat HSC 2027 brief. Full lists:
  `PROBLEM_STATEMENT_GUJARAT.md` §6 and `VVIP/docs/USE_CASES.md` (Sources).
  In-repo technical references: `VVIP/TECHNICAL_DOCS.md`,
  `VVIP/docs/GODS_EYE_INTEGRATION.md`,
  `VVIP/docs/ACTIVE_MOVEMENT_ADAPTATION.md`.
