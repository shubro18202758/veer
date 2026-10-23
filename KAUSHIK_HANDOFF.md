# Veer @ Argus — the operator's handbook for this box

> `~/argus/veer/VVIP` is **THE live system** (compose project `vvip-argus`).
> The original demo stack at `~/Desktop/Veer` (project `vvip`) was retired on
> 2026-10-19; only its model-weights directory is still used (see "Shared vs
> yours"). Owner `kaushik`, group `devteam` (sandy is in devteam); both are in
> `docker`.
>
> Updated 2026-10-23 for wave 4 (see `VEER_COMPLETE_CONTEXT.md` §Phase I): the
> road network on real OpenStreetMap roads, escort authority (the officer
> approves every switch), the God's-eye in 3D, the operator PIN gate, boot
> auto-start, migrations 001–020 and the new gate ladder — and on
> 2026-10-24 for the live deploy and its acceptance ("The live stack now",
> below).

## What this is

The full Veer city platform — the event-agnostic Corridor-OS, the
pplx-decider brain (:8083) over the aditi Gemma-4-12B tactical model (:8084),
pplx-late + bge-m3 embeddings (:8085), the God's-eye CesiumJS city
(photorealistic 3D for signed-in operators), watchlist / ANPR / evidence-only
stolen-vehicle sightings / human-approved e-challans, Jan Rakshak and the
other agencies' dispatch, city signal plans — on Ahmedabad's real road network
(49 segments, 34 junctions, ~192 km, traced on OpenStreetMap).

## The live stack now (2026-10-24)

- **Deployed** 2026-10-23 23:33 IST (`COMPOSE_PARALLEL_LIMIT=2 bash
  scripts/veer_up.sh --build --timeout 900` → READY 11/11; migration 020
  applied, the real-road network step applied, `network osm 49/49 · 34
  junctions · 20 migrations ledgered`) and **redeployed** 01:20 IST on
  2026-10-24 with the tier-0 fix (pre-movement route options labelled by
  their own segments, a pre-movement answer also filed under the
  movement's own decision doc) and the canvas's `SUPERSEDED · STOLEN` pin
  — READY 11/11, no migration to apply. The deck UI smokes, the journeys
  and the screens camera ran on the 23:33 build; after the 01:20 rebuild
  the tier-0 gate re-ran and the hero shots were taken.
- **Rollback, if ever needed:** the pre-deploy store dump
  `VVIP/.run-models/backups/corridor_db_pre_wave3c_deploy_20261023T233236.dump`,
  the seed stamps `VVIP/.run-models/backups/seed_stamps_pre_wave3c_20261023T233236/`
  and the image tag `:pre-wave3c` on every `vvip-argus-*` image (+ nats,
  valkey). Ask before using any of it.
- **Accepted live:** the 22-step acceptance ladder — 19 green first time;
  the tier-0 gate (fixed, redeployed, re-run green: 1 hit in 3 identical
  plans, 1825 ms saved) and two canvas smokes (their failed checks green
  once the reset cleared the acceptance debris) re-ran green; the
  flagship showcase PASS
  three times, the repetition gate's two rounds identical, the journeys
  92/92, the screens camera 40/40, no secret in any log. Detail:
  `VVIP/TECHNICAL_DOCS.md` §13.
- **Staged for judging:** the final `demo_reset.sh --apply` (01:23 IST)
  passed every check — one stolen-vehicle card for GJ27EM9001 with its
  PENDING sighting (1 at 01:24; the staging sweep keeps adding EMULATED
  reads while it runs, so the card's count grows),
  0 pending penal rows, the old pursuit `4508d86d` cancelled, `/ops`
  offering AUTHORISE PURSUIT, no debris visible. Its staging sweep (run
  30) ends by itself at 02:08 IST, so re-stage within ~20 minutes of the
  next judging (`--apply` again, or `--restage`). The hero screenshots in
  `VVIP/showcase/` were recaptured on that staged state (01:25 IST).

## Ports (all loopback except the deck)

| Service | Where | Port |
|---|---|---|
| command-deck (the UI, operator PIN gate) | container `vvip-argus-command-deck` | **0.0.0.0:5273** — open `http://127.0.0.1:5273` on the box |
| traffic-oracle | `vvip-argus-traffic-oracle` | 127.0.0.1:8091 |
| convoy-brain | `vvip-argus-convoy-brain` | 127.0.0.1:8092 |
| event-emulator | `vvip-argus-event-emulator` | 127.0.0.1:8090 |
| postgis | `vvip-argus-postgis` | 127.0.0.1:56434 (migrations 001–020) |
| valkey | `vvip-argus-valkey` | 127.0.0.1:6380 |
| nats | `vvip-argus-nats` | 127.0.0.1:4223 (monitoring :8223) |
| signal-ingress | `vvip-argus-signal-ingress` | — (publishes to NATS) |
| decider · Gemma · embeddings | systemd `--user` units `veer-decider` · `veer-llama` · `veer-embed` | 127.0.0.1:8083 · :8084 · :8085 |

Every port, container and compose argument comes from
`scripts/veer_env.sh` + `infra/compose.argus-override.yml`; every script takes
them from env with these defaults, so the same script runs against a private
sandbox and against this stack.

## Daily commands (from `~/argus/veer/VVIP`)

```bash
# bring-up / status (idempotent; never as root)
bash scripts/veer_up.sh                 # model units → compose up → migrate → seed → READY 11/11
bash scripts/veer_up.sh --status        # read-only readiness table (11 rows + network/security/modes/boot)
bash scripts/veer_up.sh --build         # rebuild the -argus images after tree changes
bash scripts/veer_up.sh --demo          # + signal-plan writer + living city (refused unless the
                                        #   citizen feed labels emulated events); --no-demo to undo
bash scripts/veer_up.sh --install-units # once: veer.env + systemd units + enable veer.target

# secrets live in ~/.config/veer/veer.env (mode 600) — set them on stdin, never in argv
bash scripts/veer_env.sh --set VEER_OPERATOR_PIN -
bash scripts/veer_env.sh --set VEER_SESSION_SECRET -
bash scripts/veer_env.sh --set VEER_CESIUM_ION_TOKEN -

# by hand (what veer_up.sh runs)
docker compose -p vvip-argus -f infra/compose.yml \
  -f infra/compose.gb10-override.yml -f infra/compose.argus-override.yml up -d
POSTGIS_CONTAINER=vvip-argus-postgis \
VVIP_DATABASE_URL=postgresql://corridor_admin:<POSTGIS_PASSWORD>@127.0.0.1:56434/corridor_db \
  .venvs/migrate/bin/python scripts/migrate.py

# before judging: data hygiene (dry-run = GET-only; --apply needs the team's go-ahead
# and the name of the officer running it — the unattended live rehearsals of 2026-10-24
# ran as 'Scripted demo officer (demo reset)'; it stops at PENDING — a signed-in
# human approves on /ops)
bash scripts/demo_reset.sh
bash scripts/demo_reset.sh --apply --officer '<Duty Officer name>' --cancel-debris
bash scripts/demo_reset.sh --apply --officer '<name>' --restage   # force a fresh sweep
```

**Release-day order on the live stack** (each write with the team's
go-ahead): the live smokes → `showcase_run.sh` → `repetition_gate.sh`
(nobody working on `/ops` while it runs — foreign activity fails it,
untouched) → `node scripts/journeys.mjs --live`
→ `demo_reset.sh --apply --officer '<name>' --cancel-debris`, the reset
**at least 30 minutes after the showcase and the journeys** (their
finished dispatch tiles fold into `/ops`'s history only after 30 min —
until then the verification FAILs and prints the fold time; re-running
`--apply` after it is a no-op) and **within ~20 minutes of judging**.

`demo_reset.sh --apply` (signed in as that officer, so every write carries
the name): stops stale emulator runs; cancels the old fine-based pursuit
`4508d86d…` through the audited lifecycle; has the officer reject the
pending penal recommendations on the stolen plate (unapprovable: "e-challan
withheld — vehicle reported stolen"); with `--cancel-debris`, cancels the
live TEST-labelled smoke/journey events and the showcase's residue through
the audited lifecycle, clears leftover journey exercise plates and
dismisses the stolen plate's stale EMULATED sightings; stages
`watchlist_anpr_sweep` (it ensures the FIR earmark first) and waits for a
PENDING `R_STOLEN_SIGHTING` and its JR-EM units; then verifies, with the
deck's own rules, that `/ops` offers AUTHORISE PURSUIT on the
stolen-vehicle card and a pursuit card with no basis until that human
approval — never an e-challan; prints the judge checklist; never approves
anything. One officer approval authorises ONE pursuit (the oracle answers
422 on reuse, and `/ops` skips an approval spent on a closed pursuit — so
the showcase's scripted approval no longer pre-empts the judged one); an
approved sighting that is not yet spent (no closed pursuit behind it)
cannot be withdrawn and would pre-empt it, so the verification FAILs and
names it.
The EMULATED sweep runs 45 min (the JR-EM patrol units exist only while a
run publishes them); a second `--apply` is a no-op while it is fresh.
Audit rows are never deleted; without `--cancel-debris` debris is left as
is and the verification lists what is still visible; `--purge-acceptance`
only lists rows unless `VEER_PURGE_ACCEPTANCE_OK=yes`. Exit 0 done · 1 a
step or check failed · 2 usage / preflight refusal · 3 purge listed but
not confirmed. Logs:
`$VEER_LOG_DIR/demo_reset-*`. In the judged demo the officer authorises
the pursuit from the stolen-vehicle SIGHTING on `/ops` — never from an old
e-challan.

**Deploys.** The images bake the source: changed service code reaches the
stack only through `bash scripts/veer_up.sh --build`. A bring-up that
applies the road-network step (whenever the store is not on the generated
network — a restored pre-conversion backup included, whatever the run-dir
stamp says) restarts the oracle, the emulator and the deck once by itself
and WARNs about any open event whose route is no longer a legal path; no
manual restart or stamp removal is needed. The postgis row of `--status`
reads `network osm 49/49 · 34 junctions` on the generated network. Runs
recorded before the conversion are history: the emulator refuses to
replay a run whose recorded route is no longer a legal path (422
`route_not_on_current_network` — start a new run of the use case; on a
converted copy of this store every pre-conversion run was refused), and
for the God's-eye REPLAY pick a run recorded after the deploy (e.g. the
sweep `demo_reset.sh` stages) — an old run's reads were moved onto the
real roads, its patrol-unit frames were not.

**Boot.** `veer.target` (enabled by `--install-units`) starts
`veer-models.target` (the three model units) and `veer-up.service`
(`veer_up.sh --boot`). Proof: `journalctl --user -u veer-up.service` — the
real reboots of 2026-10-23 reached `READY 11/11` in 4 min 25 s and 4 min 27 s
with no manual command.

**Signing in from scripts.** Every gated tool signs in through ONE helper:
`. scripts/deck_session.sh; deck_signin <deck_url> "<who> (automated check)"`
(bash) or `scripts/lib/deck_session.mjs` (node). The PIN is read at run time
from `VEER_OPERATOR_PIN`, the file named by `VEER_OPERATOR_PIN_FILE`, or
veer.env — never printed. One attempt per run: the deck throttles 8 failed
PINs per 5 minutes.

## The gates

```bash
bash scripts/verify_all.sh          # OFFLINE ladder (no sign-in, no model call, no writes):
                                    #   scripts-syntax, gods-eye-check, gods-eye-canvas,
                                    #   design-smoke, deck-ui, every pytest suite (whole), cargo,
                                    #   display-geometry, ingress-segments, submission-consistency,
                                    #   wave1-hatches, wave2-{forecaster,routing,tier0},
                                    #   wave3-{repetition,ledger}
bash scripts/verify_all.sh --live   # live (one sign-in; GET-only reads through the deck),
                                    #   demo-reset (the dry-run), live-smokes (ops-live-smoke +
                                    #   integration-agent), then the models + model-drift tiers
node scripts/journeys.mjs           # the judge's journeys J1–J6 (+ the J7 reboot checklist),
                                    #   signed in once as 'Journey check (automated)'; every row it
                                    #   makes is labelled JOURNEY CHECK and closed again; refuses
                                    #   :5273 unless --live (go-ahead); --no-browser = API-level;
                                    #   92 checks (J1–J6: 17/23/13/11/10/18 — 92/92 on the live
                                    #   deck, 2026-10-24); exit 1 = a journey
                                    #   failed or a cleanup left a row open, 130/143 = interrupted
                                    #   (rows closed first); artifacts in $VEER_LOG_DIR/journeys-<stamp>/
bash scripts/argus_full_smoke.sh    # full-system live smoke: every service + models, the 49 osm
                                    #   segments, traffic:latest freshness, publisher AND consumer,
                                    #   a real Z plan + its diversions (titled ARGUS SMOKE TEST), the
                                    #   city picture, MCP (no writer tool), chat -> canvas directive
bash scripts/showcase_run.sh        # the flagship "God's Eye Morning" (writes: live only with
                                    #   the go-ahead; it stops at PENDING where a gate allows)
bash scripts/repetition_gate.sh --fast   # offline selftest; the full live gate is on demand (its
                                    #   restore deletes only the rounds' own rows; anyone else's
                                    #   activity fails the gate, untouched — run it with /ops idle)
node scripts/submission_consistency_check.mjs   # docs/deck vs tree vs artifacts (+ --selftest)
python3 scripts/gen_osm_network.py --verify     # the real-road network re-proved offline
python3 scripts/impact_run.py                   # IMPACT_REPORT.md from the running stack
```

Test inventory on the deployed tree (gate-venv collection, recounted
2026-10-24 after the tier-0 fix): 2709 pytest tests — convoy-brain 635,
corridor-store importer 22 + store 107, embedding-service 113,
event-emulator 328, traffic-oracle 1500, command-deck 4 — and
signal-ingress `cargo test` 120 (run it on a clean target directory: a
cargo target volume shared with another checkout can report that
checkout's stale build — the live ladder's offline run read 118 that way).

## Shared vs yours — read before deleting things

- `VVIP/models` is a **symlink** to `~/Desktop/Veer/VVIP/models` — the model
  weights (the 27B decider, Gemma-12B, the embedders). The host model units
  serve from it. Do NOT delete or reorganize through the symlink. Model
  configuration lives in this tree: `VVIP/models-config/` (`veer_models.yaml`,
  `MEMORY_BUDGET.md`, the launchers); experiments go in `VVIP/models-local/`
  (the Wave-2 t0-alpha artifact lives at `models-local/t0/`).
- The model hosts are the systemd `--user` units `veer-decider` /
  `veer-llama` / `veer-embed` — `systemctl --user status veer-models.target`.
  Their logs and pids are this tree's `.run-models/`; their Python venvs
  come from `VEER_VENV_DIR` in veer.env, which on this box still points at
  the retired tree's `models/.venvs` (the running decider is
  `…/Desktop/Veer/VVIP/models/.venvs/model-host/bin/python`) —
  `scripts/veer_env.sh` warns and names the rebuild under `VVIP/.venvs`
  (`VEER_VENV_DIR=$VEER_ROOT/.venvs infra/scripts/serve_models.sh build`).
- `~/.config/veer/veer.env` holds the operator PIN, the session secret and
  the Cesium ion token: mode 600, never commit, never paste.

## Things that are emulated (say so when asked)

ANPR camera reads (`emulated_anpr`), the 28 camera sites, agency units
(`emulated_dispatch_projection` / `emulated_patrol`), the escort convoy's GPS
(`emulated_gps` — no GPS hardware feeds this deployment) and the traffic feed
(`data_quality: synthetic`) — every surface labels them EMULATED or SIMULATED
FEED. The roads are real (OpenStreetMap); the decisions are the real stack's
or a named human officer's — a script's unattended approval is labelled
`Scripted demo officer (showcase script)` (the pre-judging reset's own
writes: `Scripted demo officer (demo reset)`; the 2026-10-18 showcase's
"Duty Officer R. Mehta" was such a cast name; the e-challan it approved on
the stolen plate stays as superseded audit history — its canvas pin reads
`SUPERSEDED · STOLEN` — and is never a pursuit basis).
