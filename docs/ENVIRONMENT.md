<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="../VVIP/services/command-deck/static/brand/veer-lockup.svg">
    <img alt="Veer" src="../VVIP/services/command-deck/static/brand/veer-lockup-day.svg" width="180">
  </picture>
</p>
<p align="center">
  <img alt="environment reference" src="https://img.shields.io/badge/document-environment%20reference-276EF1?style=flat-square"> <img alt="Secrets" src="https://img.shields.io/badge/secrets-never%20committed-FF5C61?style=flat-square">
</p>

# Veer — Environment Variable Reference

Every environment variable the Veer stack reads, where it is read, its default, and what it does. The values here
are read from the code: [`VVIP/scripts/veer_env.sh`](../VVIP/scripts/veer_env.sh),
[`VVIP/scripts/veer_up.sh`](../VVIP/scripts/veer_up.sh), the compose files in
[`VVIP/infra/`](../VVIP/infra/), the systemd units in [`VVIP/infra/systemd/`](../VVIP/infra/systemd/),
[`VVIP/infra/scripts/serve_models.sh`](../VVIP/infra/scripts/serve_models.sh) and each service's settings module
under [`VVIP/services/`](../VVIP/services/). The architecture they configure is described in
[`TECHNICAL_DESIGN.md`](../TECHNICAL_DESIGN.md).

This document never contains a secret value. Placeholders such as `<six-digit PIN>` stand for values you supply.

---

## Contents

1. [How configuration reaches each process](#1-how-configuration-reaches-each-process)
2. [Setting a variable](#2-setting-a-variable)
3. [Reading the tables](#3-reading-the-tables)
4. [Host environment file and bring-up](#4-host-environment-file-and-bring-up)
5. [Operator gate and sessions](#5-operator-gate-and-sessions)
6. [Maps and imagery](#6-maps-and-imagery)
7. [Database and stores](#7-database-and-stores)
8. [AI and model hosts](#8-ai-and-model-hosts)
9. [OSINT](#9-osint)
10. [Emulator and demo](#10-emulator-and-demo)
11. [Ports and binds](#11-ports-and-binds)
12. [Safety switches](#12-safety-switches)
13. [Gate and tool scripts (selected)](#13-gate-and-tool-scripts-selected)
14. [Set but not read, legacy and image-internal](#14-set-but-not-read-legacy-and-image-internal)
15. [A minimal working environment file](#15-a-minimal-working-environment-file)
16. [Checking the configuration](#16-checking-the-configuration)

---

## 1. How configuration reaches each process

```mermaid
flowchart LR
    SH["shell export<br/>explicit values win"] --> LD
    EF["~/.config/veer/veer.env<br/>mode 600, KEY=VALUE lines"] --> LD["scripts/veer_env.sh loader<br/>exports each line not already set"]
    LD --> CI["docker compose interpolation<br/>KEY:-default, pass-through keys"]
    CI --> SV["service containers<br/>a pass-through key left unset is absent,<br/>so the service's own default applies"]
    EF --> UN["systemd --user units<br/>EnvironmentFile"]
    UN --> MH["model hosts<br/>serve_models.sh --foreground"]
    UN --> UP["veer-up.service<br/>veer_up.sh --boot"]
    UP --> LD
```

Four layers, in order of precedence for a container:

1. **Compose files** set most service variables directly (for example the deployed `PORT` of each service and the
   database URLs). Some entries interpolate the environment with a default (`${VVIP_REQUIRE_OFFICER:-1}`).
2. **Pass-through keys** are compose entries with no value (`VVIP_CONFIDENCE_FLOOR:`). They reach the container
   only when set in the bring-up's environment; otherwise they are absent and the service keeps its built-in
   default. An empty string never reaches a parser.
3. **The host environment file** `~/.config/veer/veer.env` supplies the values compose interpolates and the paths
   the model hosts need. `scripts/veer_env.sh` loads it; a variable already exported in the calling shell wins.
4. **Service defaults** in code apply to anything not set above.

Two consequences matter in practice:

- **A boot has no login shell.** At boot, `veer-up.service` and the model units see only `veer.env`. A value you
  exported in a shell but never wrote to `veer.env` disappears after a reboot. `veer_up.sh` warns when your shell
  carries a persisted key that `veer.env` lacks. A deck recreated without the PIN would serve the LAN with the
  operator gate off.
- **The units read a fixed path.** The systemd units always read `%h/.config/veer/veer.env` (never
  `$XDG_CONFIG_HOME`). `VEER_ENV_FILE` changes only what the scripts read.

---

## 2. Setting a variable

Run these from the `VVIP/` directory, as the user that owns the stack (never root).

```bash
# Create ~/.config/veer/veer.env (mode 600) from this host's detected paths.
# --install-units does this too, and links and enables the systemd units.
bash scripts/veer_env.sh --write            # keeps an existing file
bash scripts/veer_env.sh --write --force    # regenerates it, keeping every other line

# A non-secret value:
bash scripts/veer_env.sh --set VEER_OSINT 1

# A secret: the value is read from standard input (typed without echo at a terminal),
# so it never appears in argv, the process list or shell history.
bash scripts/veer_env.sh --set VEER_OPERATOR_PIN -
bash scripts/veer_env.sh --set VEER_SESSION_SECRET -
bash scripts/veer_env.sh --set VEER_CESIUM_ION_TOKEN -
bash scripts/veer_env.sh --set POSTGIS_PASSWORD -

# A generated secret can be piped in, still never on a command line:
openssl rand -hex 32 | bash scripts/veer_env.sh --set VEER_SESSION_SECRET -

# Show the effective non-secret environment and the compose invocation:
bash scripts/veer_env.sh --print
```

Rules the helper enforces:

- A value must be **one unquoted token**: no whitespace, quotes, `$`, backtick or backslash. The loader and systemd's
  `EnvironmentFile=` parser then read it identically. `--set` refuses anything else.
- `--set` replaces the first `KEY=` line (dropping repeats) or appends one, writes through a temporary file and
  keeps mode 600. For keys whose name contains PASSWORD, TOKEN, SECRET or PIN it prints only "KEY set".
- The file is plain `KEY=VALUE` lines; every such line is exported by the loader.

**Applying a change.** Re-run `bash scripts/veer_up.sh`: compose recreates any container whose configuration
changed, in the bring-up's fixed order. A change to a model-host variable needs that unit restarted
(`systemctl --user restart veer-models.target`, or the single unit). A changed deck PIN or session secret takes
effect when the deck container is recreated; rotating `VEER_SESSION_SECRET` ends every open session.

**Never** paste a secret into a command line, a commit, an issue or a chat. Before a release,
`bash scripts/secret_scan.sh` checks the tree, the staged diff and the commits a push would send for the literal
values of the operator PIN, the session secret and the ion token, and for credential patterns.

---

## 3. Reading the tables

| Column | Meaning |
|---|---|
| **Variable** | The exact name. `<CONNECTOR>` marks a family of names. |
| **Read by** | The services or scripts whose code reads it (or the compose interpolation that consumes it). |
| **Default** | The value used when you set nothing. "Deployed" means the value the deployment's compose files or bring-up set; "code" means the service's own fallback. |
| **Required** | **Required**: the stack does not work as designed without it. **Recommended**: works without it, but a deployment should set it. **Set by compose** or **Set by bring-up**: you normally do not set it yourself. **Optional**. |
| **Secret** | ✓ when the value must be treated as a secret (mode-600 file only, `--set KEY -`, never printed). |

Flags documented as "truthy" accept `1`, `true`, `yes` or `on` (any case); flags documented as "exactly `1`"
accept nothing else.

---

## 4. Host environment file and bring-up

Read by `scripts/veer_env.sh` (which every Veer script sources), `scripts/veer_up.sh`,
`infra/scripts/serve_models.sh` and the systemd units.

| Variable | Read by | Default | Required | Secret | What it does |
|---|---|---|---|---|---|
| `VEER_ROOT` | `veer_env.sh`, `veer_up.sh`, `serve_models.sh`, every systemd unit (`ExecStart=${VEER_ROOT}/…`) | the `VVIP/` directory holding the scripts (detected) | **Required** in `veer.env` for boot (written by `--write`) | | Absolute path of the `VVIP/` tree; the units start the scripts from it |
| `VEER_ENV_FILE` | `veer_env.sh`, `deck_session.sh`, `secret_scan.sh`, `demo_reset.sh`, `journeys.mjs` | `$HOME/.config/veer/veer.env` | Optional | | Which host file the scripts load; the systemd units always read `%h/.config/veer/veer.env` |
| `VEER_RUN_DIR` | `veer_env.sh`, `veer_up.sh`, `serve_models.sh` | `$VEER_ROOT/.run-models` | Optional | | Runtime state: the bring-up lock, the network-step stamp and restart marker, pid files |
| `VEER_LOG_DIR` | `serve_models.sh`, gate scripts | `$VEER_RUN_DIR/logs` | Optional | | Model-host and script logs |
| `VEER_VENV_DIR` | `serve_models.sh`, `veer_up.sh` | `$VEER_ROOT/.venvs` | Optional | | Persistent virtual environments (`model-host`, `embedding`, `migrate`) |
| `VEER_MODELS_CONFIG_DIR` | `veer_env.sh`, `serve_models.sh` | `$VEER_ROOT/models-config` | Optional | | Directory of the model-stack configuration |
| `VEER_MODELS_CONFIG` | `serve_models.sh`, model-host, convoy-brain, traffic-oracle (memory budget) | `$VEER_MODELS_CONFIG_DIR/configs/veer_models.yaml` | Optional | | The single model-stack configuration file (endpoints, decider limits, memory budget). Contains no credentials |
| `VEER_COMPOSE_PROJECT` | `veer_env.sh`, `veer_up.sh` | `vvip-argus` | Optional | | Compose project name of the stack |
| `VEER_DEMO` | `veer_up.sh` | `0` | Optional | | `1` = demo mode on every bring-up and reboot: the signal-plan writer on and the living city on (the latter only if the public feed labels emulated events). Set by `veer_up.sh --demo` / `--no-demo` |
| `VEER_OSINT` | `veer_env.sh`, `veer_up.sh` | `0` | Optional | | `1` adds `infra/compose.osint-ingress.yml` to the compose invocation and a 12th readiness component; any other value is off, and a stale OSINT container is removed |
| `VEER_CONVERGE_TIMEOUT` | `veer_up.sh` | `600` (seconds) | Optional | | How long the bring-up waits for every component to be ready (`--timeout` overrides) |
| `VEER_MIGRATE_PY` | `veer_up.sh` | `$VEER_VENV_DIR/migrate/bin/python` | Optional | | Python interpreter used to run `scripts/migrate.py` |
| `POSTGIS_CONTAINER`, `VALKEY_CONTAINER`, `NATS_CONTAINER`, `INGRESS_CONTAINER`, `ORACLE_CONTAINER`, `BRAIN_CONTAINER`, `DECK_CONTAINER`, `EMULATOR_CONTAINER`, `OSINT_CONTAINER` | `veer_env.sh`, `veer_up.sh`, gate scripts; `POSTGIS_CONTAINER` also `migrate.py` | `vvip-argus-postgis`, `vvip-argus-valkey`, … `vvip-argus-osint-ingress` (`migrate.py` alone defaults to `vvip-postgis`) | Optional | | Container names the scripts inspect; the deployed names come from `compose.argus-override.yml` |

---

## 5. Operator gate and sessions

Read by the command-deck (`src/lib/shell/operator-session.server.ts`, `src/routes/api/session/+server.ts`), passed
in by `infra/compose.argus-override.yml`.

| Variable | Read by | Default | Required | Secret | What it does |
|---|---|---|---|---|---|
| `VEER_OPERATOR_PIN` | command-deck; `deck_session.sh` and `deck_session.mjs` (sign-in helpers); `secret_scan.sh` | empty: **gate off** | **Required** for any deck reachable from a network | ✓ | Turns the operator gate on. Officers sign in with their name and this duty PIN; without a session every proxied API call is refused (403). Use `<six-digit PIN>` or longer. With the gate off, `veer_up.sh --status` reports a LAN-exposed deck as DEGRADED |
| `VEER_SESSION_SECRET` | command-deck; `secret_scan.sh` | empty: 32 random bytes per deck process | **Recommended** whenever the gate is on | ✓ | HMAC-SHA256 key that signs the 12-hour `veer_operator` session cookie. Unset, every restart signs everyone out. Rotating it ends every session at once |
| `VEER_SESSION_SECURE` | command-deck | empty (off) | Optional | | `1` sets the cookie's `Secure` flag. Set it **only** when the deck is served over TLS; on plain HTTP a secure cookie never comes back and nobody can sign in |

Behaviour fixed in code (not configurable): failed PINs are throttled at 8 per 5 minutes per client, the PIN check is
constant-time, officer names must be 2–64 printable characters without bidirectional controls, and an anonymous
caller may reach only the road geometry, two liveness probes and the 108 ambulance request (6 per client per 10
minutes).

---

## 6. Maps and imagery

| Variable | Read by | Default | Required | Secret | What it does |
|---|---|---|---|---|---|
| `VEER_CESIUM_ION_TOKEN` | command-deck (`GET /gods-eye/mode`, satellite thumbnails); `secret_scan.sh` | empty: keyless everywhere | Optional | ✓ | Cesium ion access token. When set, **signed-in operators** get photoreal 3D Ahmedabad (Google Photorealistic 3D Tiles), Cesium World Terrain and Bing aerial imagery, and satellite map thumbnails. Anonymous visitors and the public pages always get the keyless OpenStreetMap basemap and never receive the token. Treat it as a secret: it spends your ion quota |

With no token the canvas draws Veer's own roads and entities over OpenStreetMap raster tiles; there is no other map
key.

---

## 7. Database and stores

| Variable | Read by | Default | Required | Secret | What it does |
|---|---|---|---|---|---|
| `POSTGIS_PASSWORD` | compose interpolation (PostGIS `POSTGRES_PASSWORD`, the oracle's and emulator's database URLs), `veer_up.sh` (migrations and seed), `serve_models.sh` (embedding-service URL) | a development placeholder defined in the compose files | **Recommended**: set your own before the first bring-up | ✓ | Password of the `corridor_admin` role on `corridor_db`. The PostgreSQL image applies it only when it initialises an empty data volume, so set it before the first bring-up; changing it later needs the role's password changed in the database too |
| `VVIP_DATABASE_URL` | traffic-oracle, event-emulator, embedding-service, `migrate.py` | Deployed: `postgresql://corridor_admin:${POSTGIS_PASSWORD}@127.0.0.1:56434/corridor_db` (compose). Code: oracle falls back to a local development URL; the emulator has no default and fails closed | Set by compose | ✓ (contains the password) | PostgreSQL connection URL. convoy-brain does not read it (it reports it as ignored if set) |
| `DATABASE_URL` | `migrate.py`, embedding-service | unset | Optional | ✓ | Fallback database URL when `VVIP_DATABASE_URL` is unset |
| `VEER_DATABASE_DSN` | embedding-service | unset | Optional | ✓ | First-choice database URL for the embedding service |
| `EMBEDDING_DATABASE_URL` | `serve_models.sh` (passed to the embedding service as `VVIP_DATABASE_URL`) | built from `POSTGIS_PASSWORD` and `POSTGIS_HOST_PORT` | Optional | ✓ | Overrides the database URL the embedding service gets |
| `VVIP_VALKEY_URL` | traffic-oracle, convoy-brain, event-emulator | Deployed: `redis://127.0.0.1:6380`. Code: `redis://localhost:6379` | Set by compose | | Valkey (Redis protocol) URL |
| `VALKEY_URL` | convoy-brain | unset | Optional | | Fallback Valkey URL when `VVIP_VALKEY_URL` is unset |
| `VVIP_NATS_URL` | traffic-oracle, event-emulator | Deployed: `nats://127.0.0.1:4223`. Code: `nats://localhost:4222` | Set by compose | | NATS URL for the live data plane |
| `NATS_URL` | signal-ingress | Deployed: `nats://nats:4222` (the project network). Code: `nats://localhost:4222` | Set by compose | | NATS URL the Rust ingress publishes to |
| `VVIP_INGEST_ENABLED` | traffic-oracle | `true` | Optional | | `false` keeps the NATS ingest service off (`/health` says so) |
| `VVIP_INGEST_EMULATED` | traffic-oracle | `true` | Optional | | `false` drops the emulator's subjects (`corridor.traffic.emulated`, `corridor.units.emulated`) only |
| `VVIP_INGEST_FLUSH_INTERVAL_SEC` | traffic-oracle | `5.0` | Optional | | Observation buffer flush interval to `traffic.observations` |
| `VVIP_INGEST_FLUSH_ROWS` | traffic-oracle | `2000` | Optional | | Observation buffer flush size |
| `VVIP_OBSERVATION_RETENTION_DAYS` | traffic-oracle | `14` | Optional | | Daily `traffic.observations` partitions older than this are detached and dropped (startup and hourly) |

Fixed in code, not configurable: the role `corridor_admin` and database `corridor_db`; Valkey `maxmemory 512mb` with
`allkeys-lfu`; sighting retention (30 days without an active earmark, earmarks capped at 90 days).

---

## 8. AI and model hosts

### 8.1 Model files and model-host processes

Read by `infra/scripts/serve_models.sh` (run by the `veer-decider`, `veer-llama` and `veer-embed` units) and by the
model services themselves. Weights are supplied by the operator and never committed.

| Variable | Read by | Default | Required | Secret | What it does |
|---|---|---|---|---|---|
| `DECIDER_SNAPSHOT_PATH` | `serve_models.sh`, model-host | `serve_models.sh`: the Hugging Face cache snapshot of `pplx-decider-v1-27b` under `$HOME/.cache/huggingface/hub/`; model-host: `decider.snapshot_path` in `veer_models.yaml` | **Required** (the weights) | | The decider's snapshot **directory** (load it by path; its files are symlinks into the cache's blob store, so never copy the tree). A missing path stops the unit with exit 78 |
| `LLAMA_SERVER_BIN` | `serve_models.sh` | `$HOME/llama.cpp/build/bin/llama-server` | **Required** | | The llama.cpp server binary |
| `GEMMA_GGUF` | `serve_models.sh` | `$HOME/models/q4-stack/v7h-merged-Q4_K_M.gguf` | **Required** | | The Gemma 4 12B Q4_K_M model file |
| `GEMMA_CTX_PER_SLOT` | `serve_models.sh` | `8192` | Optional | | Context tokens per llama slot (total context = slots × this) |
| `GEMMA_PARALLEL_SLOTS` | `serve_models.sh` | `2` | Optional | | Parallel llama slots |
| `BGE_M3_PATH` | embedding-service | `veer_env.sh --write` records `$HOME/models/bge-m3` when it exists; the service's own fallback is a fixed host path | **Required** | | Local `bge-m3` dense encoder directory |
| `LATE_EMBED_MODEL` | embedding-service | `perplexity-ai/pplx-embed-v2-late-0.6b` | Optional | | Late-interaction (multi-vector) encoder |
| `AUX_LATE_EMBED_MODEL` | embedding-service | empty (off) | Optional | | The optional 9B auxiliary embedder slot; off by default (about 15.6 GiB more memory if enabled) |
| `MODEL_HOST_BIND` | model-host | `127.0.0.1` | Optional | | Bind address of the decider host; keep it loopback |
| `MODEL_HOST_LOG_LEVEL` | model-host | `info` | Optional | | Server log level |
| `EMBEDDING_LISTEN_HOST` | embedding-service | `127.0.0.1` | Optional | | Bind address of the embedding service; keep it loopback |
| `EMBEDDING_LISTEN_PORT` | embedding-service | `8085` (`serve_models.sh` passes `EMBEDDING_PORT`) | Optional | | Port of the embedding service |
| `HF_HUB_OFFLINE` | model-host | forced to `1` by `serve_models.sh` and by model-host when the configuration says offline | Set by the unit | | Keeps the model host from reaching the Hugging Face hub |

### 8.2 Model endpoints and AI behaviour

| Variable | Read by | Default | Required | Secret | What it does |
|---|---|---|---|---|---|
| `MODEL_HOST_URL` | convoy-brain, `smoke_models.sh` | Deployed and code: `http://127.0.0.1:8083` | Set by compose | | Decider endpoint. Resolution order: this variable, then `services.model_host` in `veer_models.yaml`, then the default. Must be plain http(s) on loopback or `host.docker.internal` |
| `LLAMA_BASE_URL` | convoy-brain, model-host (readiness only), `smoke_models.sh` | `http://127.0.0.1:8084` | Set by compose | | Gemma (llama-server) endpoint; same rules |
| `EMBEDDING_SERVICE_URL` | convoy-brain, model-host (readiness only), embedding-service client, `smoke_models.sh` | `http://127.0.0.1:8085` | Set by compose | | Embedding-service endpoint; same rules. Compose also passes it to the oracle, which does not read it on this tree |
| `TRAFFIC_ORACLE_URL` | convoy-brain, embedding-service | Deployed: `http://127.0.0.1:8091`. Code: `http://127.0.0.1:8081` | Set by compose | | The oracle endpoint the brain's tools and workflows call; loopback only |
| `VVIP_CONFIDENCE_FLOOR` | convoy-brain | `0.45` | Optional (pass-through) | | Decider confidence gate: a lower-confidence answer becomes a Gemma draft plus an operator alert, not an action. Calibrated on 2026-10-19; do not lower it without new measurements |
| `DECIDER_TIER0_DISABLE` | convoy-brain | unset (cache on) | Optional (pass-through) | | `1` or `true` turns off the tier-0 cache (routine checkpoints answered without a new 27B call); `/health` reports the state |
| `VVIP_MEMORY_RECORD` | convoy-brain | on | Optional | | `0`, `false`, `no` or `off` stops filing served checkpoints into the memory corpus (searches still run). Sandboxes and test brains must set it off so they never write to a shared corpus |
| `VVIP_FOUNDATION_MODEL_PATH` | traffic-oracle | Deployed: set by the oracle image to the baked t0-alpha ONNX artifact. Code: unset (rung dormant) | Set by the image | | The zero-shot foundation forecaster rung of the forecast ladder |
| `VVIP_ONNX_MODEL_PATH` | traffic-oracle | `models/onnx/flow_forecaster.onnx` (absent: the DSTGAT rung stays dormant) | Optional | | Path of an exported DSTGAT forecaster, when one exists |
| `VVIP_FORECAST_SUPPORT_BOUNDS_PATH` | traffic-oracle | the package's committed `support_bounds.json` | Optional | | Support bounds that keep out-of-range inputs away from every model rung |
| `VEER_UNIFIED_BUDGET_MB` | traffic-oracle (`runtime/gpu_arbiter.py`) | unset: `veer_models.yaml`, else `MemTotal` | Optional | | Overrides the unified-memory budget the oracle plans against |
| `OMP_NUM_THREADS`, `MKL_NUM_THREADS`, `OPENBLAS_NUM_THREADS`, `NUMEXPR_NUM_THREADS` | traffic-oracle | `4` each, when unset | Optional | | Math-library thread pools |
| `T0_REVISION` | `scripts/fetch_t0.sh` | a pinned revision | Optional | | Which revision of the third-party t0-alpha artifact is fetched (its sha256 is verified before the oracle image is built) |

---

## 9. OSINT

The OSINT service runs only with `VEER_OSINT=1` ([§4](#4-host-environment-file-and-bring-up)). It reads no secret.
Its tuning settings use the `OSINT_` prefix; the contract variables are read by their exact names.

| Variable | Read by | Default | Required | Secret | What it does |
|---|---|---|---|---|---|
| `OSINT_MODE` | osint-ingress (compose interpolation) | `live` | Optional | | `live` fetches on schedule from the allow-listed hosts; `offline` (a venue with no internet) parses only the newest cached capture of each source, labelled `cached-sample`. Persist it in `veer.env` to survive a reboot |
| `OSINT_ORACLE_URL` | osint-ingress | Deployed: `http://127.0.0.1:8091`. Code: `http://127.0.0.1:9` (the discard port) | Set by compose | | Where redacted signals are posted. Loopback only (`127.0.0.1`, `localhost`, `::1`); anything else is refused. Unset, a run posts nowhere and its batches wait in the outbox |
| `OSINT_CACHE_DIR` | osint-ingress | `/var/cache/osint-ingress` (the `osint_cache` volume) | Set by compose | | Capture cache (72 h or 200 MB) |
| `OSINT_GAZETTEER_PATH` | osint-ingress, osint-common, osint-geo (in the oracle) | the repository's `scripts/data/osint_gazetteer.json`, else the image path | Set by compose | | The place gazetteer. A path that is set but missing is an error, never silently replaced |
| `OSINT_NETWORK_PATH` | osint-geo (ingress and oracle) | the repository's `scripts/data/osm_network.json`, else the image path | Set by compose | | The road network places are snapped onto |
| `OSINT_CADENCE_<CONNECTOR>_SEC` | osint-ingress | `SACHET_CAP` 300, `GOOGLE_NEWS_RSS` 600, `GDELT_EVENTS` 900, `GDELT_DOC` 900, `REDDIT_RSS` 900, `AMC_SCRAPE` 3600, `GSDMA` 3600, `COMMON_CRAWL` 0 | Optional | | Per-connector schedule in seconds; `0` takes a connector off the schedule; 1–59 is raised to 60. Common Crawl is backfill only and never scheduled |
| `OSINT_JITTER` | osint-ingress | `0.1` (0–0.5) | Optional | | ± fraction applied to each cadence |
| `OSINT_PROBE_INTERVAL_SEC` | osint-ingress | `30` (at most 30) | Optional | | Oracle reachability probe interval |
| `OSINT_PROBE_TIMEOUT_SEC` | osint-ingress | `2` (at most 10) | Optional | | Oracle reachability probe timeout |
| `OSINT_RETENTION_HOURS` | osint-ingress | `72` | Optional | | Cache age limit (the newest capture of each connector is always kept) |
| `OSINT_RETENTION_BYTES` | osint-ingress | `209715200` (200 MB) | Optional | | Cache size limit |
| `OSINT_BATCH_SIZE` | osint-ingress | `200` (1–200) | Optional | | Signals per post to the oracle |
| `OSINT_PUBLISH_RETRIES` | osint-ingress | `3` (1–10) | Optional | | Post retries |
| `OSINT_PUBLISH_BACKOFF_SEC` | osint-ingress | `0.5` | Optional | | Retry back-off |
| `OSINT_HTTP_TIMEOUT_SEC` | osint-ingress | `25` | Optional | | Source fetch timeout |
| `PROJ_NETWORK` | osint-ingress and the OSINT libraries (pyproj) | `OFF` (compose and image) | Set by compose | | Keeps pyproj from downloading grids, so the source allow-list stays the only egress |

The egress allow-list itself is code (`osint_ingress/safe_http.py` `ALLOWED_HOSTS`, reported on `GET /health`), not
configuration.

---

## 10. Emulator and demo

Emulated data is labelled on every surface. These variables control what the event emulator and the escort's
emulated GPS do.

| Variable | Read by | Default | Required | Secret | What it does |
|---|---|---|---|---|---|
| `EMULATOR_LIVING_CITY` | event-emulator (compose interpolation, set by `veer_up.sh` from `VEER_DEMO`) | `0` | Optional | | `1` starts the ambient living city at boot: a deterministic day program of emulated causes. Held off unless the deck's public feed labels emulated events |
| `EMULATOR_LIVING_VIOLATORS` | event-emulator | `1` | Optional | | `0` stops the living city's rare deliberate violators (each only a PENDING e-challan recommendation for a named officer) |
| `EMULATOR_CITY_SEED` | event-emulator | `1411` | Optional | | Seed of the living city's deterministic day program |
| `EMULATOR_TRAFFIC_ORACLE_URL` | event-emulator | Deployed: `http://localhost:8091`. Code: `http://localhost:8081` | Set by compose | | The oracle the emulator drives; refused unless loopback or `host.docker.internal` |
| `EMULATOR_DECK_ORIGINS` | event-emulator | Deployed: `http://127.0.0.1:5273,http://localhost:5273`. Code: those plus the dev server on 5173 | Set by compose | | CORS origins, comma-separated `http(s)://host[:port]`; anything else refuses the whole list |
| `VVIP_ESCORT_SIM_GPS` | convoy-brain | Deployed: `1`. Code: off | Set by compose | | No GPS hardware feeds this deployment, so an escort walks its approved route on emulated GPS (`emulated_gps`) and stops the moment real fixes arrive. `0` waits for real fixes and fails after the GPS timeout |
| `VVIP_ESCORT_SIM_SPEED_KMH` | convoy-brain | `80` (clamped 5–120) | Optional (pass-through) | | Cruise speed of the emulated convoy (each segment's limit also caps it) |
| `VVIP_ESCORT_GPS_TIMEOUT_SEC` | convoy-brain | `300` (clamped 10–3600) | Optional (pass-through) | | How long an escort waits for a fix before it fails; a missing fix never completes an escort |
| `INGRESS_CITY_SEED` | signal-ingress | `0xA4D02026` (built in) | Optional (pass-through) | | Seed of the synthetic traffic field |
| `ANOMALY_CONFIG_PATH` | signal-ingress | unset: built-in thresholds | Optional | | A file overriding the Tier-1 anomaly thresholds; an unusable file falls back to the built-ins with a warning |
| `EMULATOR_TEST_PG_DSN` | event-emulator tests | unset (database tests skip) | Optional | ✓ (a database URL) | A scratch database for the emulator's PostgreSQL-backed tests; never the live store |

---

## 11. Ports and binds

The deployed ports are **constants in the compose files**, not interpolated variables. The port variables below
are defaults for scripts and for the deck's proxy; changing one does not move the stack. `veer_up.sh` reads the
ports from the rendered compose configuration and probes exactly those, and warns when a shell export disagrees.

| Variable | Read by | Default | Required | Secret | What it does |
|---|---|---|---|---|---|
| `HOST` (traffic-oracle) | traffic-oracle | Deployed and code: `127.0.0.1` | Set by compose | | Bind address; keep loopback |
| `PORT` (traffic-oracle) | traffic-oracle | Deployed: `8091`. Code: `8081` | Set by compose | | Listen port |
| `HOST` / `PORT` (convoy-brain) | convoy-brain | Deployed: `127.0.0.1` / `8092`. Code: `127.0.0.1` / `8080` | Set by compose | | Bind address and port |
| `HOST` / `PORT` (event-emulator) | event-emulator | `127.0.0.1` / `8090` | Set by compose | | Bind address and port |
| `HOST` / `PORT` (osint-ingress) | osint-ingress | `127.0.0.1` / `8093` | Set by compose | | Bind address and port |
| `HOST` / `PORT` (command-deck) | command-deck (adapter-node) | Deployed: `0.0.0.0` / `5273`. Image: `0.0.0.0` / `5173` | Set by compose | | The deck is the only LAN-facing service |
| `ORACLE_PORT` | command-deck proxy (`/api/v1`, `/api/traffic`, `/gods-eye/feeds`); convoy-brain (oracle URL when `TRAFFIC_ORACLE_URL` is unset); `vite dev`; scripts | `8091` (deck); **no default under `vite dev`** | Set by compose | | Proxy target port on 127.0.0.1. The proxy's host is hard-coded to loopback; only the port is configurable |
| `BRAIN_PORT` | command-deck proxy (`/api/convoy`), `vite dev`, scripts | `8092`; no default under `vite dev` | Set by compose | | Brain port on 127.0.0.1 |
| `EMULATOR_PORT` | command-deck proxy (`/api/emulator`), `vite dev`, scripts | `8090`; no default under `vite dev` | Set by compose | | Emulator port on 127.0.0.1 |
| `DECK_PORT` | `veer_env.sh`, `veer_up.sh`, gate scripts | `5273` | Optional | | Deck port the scripts probe |
| `OSINT_PORT` | `veer_env.sh`, `veer_up.sh` | `8093` | Optional | | OSINT port the scripts probe |
| `MODEL_HOST_PORT` | `serve_models.sh`, model-host, `veer_up.sh` | `8083` | Optional | | Decider port (model-host binds it on loopback) |
| `LLAMA_PORT` | `serve_models.sh`, `veer_up.sh` | `8084` | Optional | | llama-server port (bound on loopback) |
| `EMBEDDING_PORT` | `serve_models.sh`, `veer_up.sh` | `8085` | Optional | | Embedding-service port |
| `POSTGIS_HOST_PORT` | `veer_env.sh`, `veer_up.sh`, `serve_models.sh` | `56434` | Optional | | Loopback port of PostGIS for host processes (migrations, the embedding service) |
| `VALKEY_HOST_PORT`, `NATS_HOST_PORT`, `NATS_MON_PORT` | `veer_env.sh`, `veer_up.sh` | `6380`, `4223`, `8223` | Optional | | Loopback ports of Valkey, NATS and NATS monitoring the scripts probe |

For deck development outside Docker, `vite dev` refuses to start unless `ORACLE_PORT`, `BRAIN_PORT` and
`EMULATOR_PORT` name the backends (there is deliberately no default, so a development deck never reaches the live
stack by accident). The development server binds 127.0.0.1 only, and the proxy's gate, authority pinning and CSP
apply in production builds only.

---

## 12. Safety switches

These change what the platform is allowed to do. Each has a safe default.

| Variable | Read by | Default | Required | Secret | What it does |
|---|---|---|---|---|---|
| `VVIP_REQUIRE_OFFICER` | traffic-oracle (`vehicles/` exactly `1`; `signals/` truthy), convoy-brain (truthy) | Deployed: `1` for both (compose). Code: off when unset | Set by compose | | `1`: earmark create and clear and signal-plan apply and restore (oracle), and escort start, stop and clear (brain), are refused with 422 without a named officer. `0` relaxes both services (an unnamed write is attributed to a system actor). Decisions on recommendations, dispatches, decision support, OSINT promotions and full-mark lookups need a named officer whatever this says |
| `VVIP_ESCORT_APPROVAL_TIMEOUT_SEC` | convoy-brain | `90` (clamped 15–600) | Optional (pass-through) | | How long a live-escort proposal (route switch, Plan B, hold, new closures) waits for a named officer before it expires and **the current plan is held**. It never auto-applies |
| `VVIP_SIGNAL_POLICY_WRITER` | traffic-oracle (truthy) | empty: **off** | Optional | | The city signal-plan writer. `veer_up.sh --demo` sets it to `1`. Even when on, every apply needs a named officer (with `VVIP_REQUIRE_OFFICER=1`), a known or explicitly passed city band, a twin shadow evaluation that passes, and a field-calibrated twin (at least 24 field hours, replay error at most 5 km/h). A fresh install has no field data, so writes are refused |
| `VVIP_ACCEPT_LIVE_ANPR` | traffic-oracle (exactly `1`) | unset: refused | Optional (pass-through) | | `1` accepts sightings labelled `live_anpr`. Reserved for a real vendor adapter behind the `AnprSource` port; leave unset until one exists |
| `VVIP_ADAPTIVE_ROBUST_INPUTS` | traffic-oracle (`adaptive/engine_loop.py`) | unset: follows the robust-routing knob in `shared/schemas/protocol_params.json` (on) | Optional (pass-through) | | `1` or `0` forces the situation engine's robust (length-weighted p90) congestion aggregation on or off |
| `VEER_DESIGN_HARNESS` | command-deck (`/design/*`, exactly `1`) | unset: the developer harness answers 404 | Optional | | `1` serves the `/design/*` harness pages (fixture data) from a production build. Only for private previews and smokes, never on a deployed deck |
| `VEER_DEMO_ALLOW_UNLABELLED` | `veer_up.sh` | unset | Optional | | `1` lets `--demo` start the living city even when the deck's public feed does not declare `emulated_labelling: true`. Leave unset: without the label, emulated events could reach the citizen page looking live |
| `NODE_ENV` | command-deck (`hooks.server.ts`) | unset in the deck image (the CSP header is sent) | Leave unset | | Only the value `development` matters: it skips the content-security-policy header (the dev server injects its own scripts). Never set it on a deployed deck |
| `VVIP_CONFIDENCE_FLOOR`, `DECIDER_TIER0_DISABLE`, `VVIP_MEMORY_RECORD` | convoy-brain | see [§8.2](#82-model-endpoints-and-ai-behaviour) | Optional | | AI gating and memory switches |

---

## 13. Gate and tool scripts (selected)

Variables the acceptance and operator scripts under `VVIP/scripts/` read, beyond the ones above. Each script's
header documents the rest.

| Variable | Read by | Default | Required | Secret | What it does |
|---|---|---|---|---|---|
| `VEER_OPERATOR_PIN_FILE` | `deck_session.sh`, `deck_session.mjs`, `secret_scan.sh` | unset | Optional | ✓ (names a file holding a PIN) | A file holding a sandbox deck's throwaway PIN. A named but unreadable file is an error, never a fall-back to the live PIN in `veer.env` |
| `DECK_URL` | `verify_all.sh`, `demo_reset.sh`, `showcase_run.sh`, `journeys.mjs` | `http://127.0.0.1:${DECK_PORT:-5273}` | Optional | | The deck the script talks to |
| `DECK_COOKIE_JAR` | `deck_session.sh` | a temporary mode-600 jar per session | Optional | ✓ (holds a session) | Where the sign-in helper keeps the session cookie; deleted at sign-out |
| `VERIFY_LIVE_MODELS` | `verify_all.sh` | `1` | Optional | | `0` skips the two live model tiers (for a private rehearsal whose models are the live ones) |
| `VERIFY_EXPECT_GATE` | `verify_all.sh` | `on` | Optional | | Whether the live tier expects the deck's operator gate to be on |
| `VERIFY_PREVIEW_PORT` | `verify_all.sh` | `5199` | Optional | | Port of the private, keyless, gate-off preview the offline deck tiers serve |
| `ORACLE_WRITER_CMD` | `showcase_run.sh`, `repetition_gate.sh` | unset (recreates the deployed oracle) | Optional | | Command that recreates a private stack's oracle when a run switches the signal writer on for its own duration |
| `VEER_PURGE_ACCEPTANCE_OK` | `demo_reset.sh` | unset | Optional | | `yes` allows the reset to purge acceptance-test audit history; without it nothing is deleted |

---

## 14. Set but not read, legacy and image-internal

Listed so that nobody spends time tuning them.

| Variable | Where it appears | Status |
|---|---|---|
| `OLLAMA_BASE_URL` | `veer_models.yaml` (legacy entry) | Not read by any serving path; the brain reports it as ignored if set |
| `VVIP_DATABASE_URL`, `VVIP_NATS_URL` in convoy-brain | brain environment | Not read by the brain (`config.UNUSED_ENV`); reported as ignored if set |
| `EMBEDDING_SERVICE_URL` in traffic-oracle | `compose.yml`, `compose.gb10-override.yml`, `compose.argus-override.yml` | Passed to the oracle, but no oracle code on this tree reads it |
| `VVIP_BATCH_SIZE`, `VVIP_BATCH_TIMEOUT_MS`, `VVIP_ML_THREADS`, `VVIP_ML_INTEROP_THREADS`, `VVIP_MEMORY_GUARD_MB`, `VVIP_ETA_MODEL_PATH`, `VVIP_RL_MAX_EPISODES`, `VVIP_RL_MAX_SIGNALS` | traffic-oracle settings model (`data/config.py`); some set by `compose.prod.yml` | Declared with defaults (100, 100, 4, 2, 3500, …) but not read elsewhere on this tree; the runtime's memory guard uses its own 3,500 MB default |
| `GRAFANA_PASSWORD` ✓ | `infra/compose.prod.yml` only | The older production profile with Prometheus and Grafana; not part of the deployed invocation. If you use that profile, set it (its fallback is a placeholder) |
| `ORT_GLOBAL_THREAD_POOL_SIZE`, `NVIDIA_VISIBLE_DEVICES`, `NVIDIA_DRIVER_CAPABILITIES` | `infra/compose.prod.yml` only | Not part of the deployed invocation |
| `PYTHONPATH`, `PYTHONUNBUFFERED`, `NODE_OPTIONS`, `RUST_LOG` | Dockerfiles | Image-internal; `RUST_LOG=info` sets signal-ingress logging |

---

## 15. A minimal working environment file

A single-server deployment with the operator gate on, imagery keyless and OSINT off. Replace every `<…>`; each real
value must be one token with no spaces or quotes. Paths are examples. Create the file with
`bash scripts/veer_up.sh --install-units` (or `scripts/veer_env.sh --write`), then add the secrets with
`scripts/veer_env.sh --set KEY -` rather than typing them into an editor.

```ini
# ~/.config/veer/veer.env   (mode 600; plain KEY=VALUE lines; never committed)

# repository and runtime state
VEER_ROOT=/home/<user>/veer/VVIP
VEER_RUN_DIR=/home/<user>/veer/VVIP/.run-models
VEER_LOG_DIR=/home/<user>/veer/VVIP/.run-models/logs
VEER_VENV_DIR=/home/<user>/veer/VVIP/.venvs
VEER_MODELS_CONFIG=/home/<user>/veer/VVIP/models-config/configs/veer_models.yaml

# corridor-store on loopback (used by migrations and the embedding service)
POSTGIS_HOST_PORT=56434

# model weights and binaries: host paths supplied by the operator
DECIDER_SNAPSHOT_PATH=<path-to-the-pplx-decider-v1-27b-snapshot-directory>
LLAMA_SERVER_BIN=<path-to-llama-server>
GEMMA_GGUF=<path-to-the-gemma-4-12b-Q4_K_M.gguf>
BGE_M3_PATH=<path-to-the-bge-m3-directory>

# switches
VEER_DEMO=0
VEER_OSINT=0

# secrets: set each with   bash scripts/veer_env.sh --set KEY -
VEER_OPERATOR_PIN=<six-digit PIN>
VEER_SESSION_SECRET=<64 random hex characters>
POSTGIS_PASSWORD=<database password, set before the first bring-up>

# optional
# VEER_CESIUM_ION_TOKEN=<Cesium ion access token>
# OSINT_MODE=offline
```

Everything else takes the deployed default from the compose files: loopback binds, `VVIP_REQUIRE_OFFICER=1`,
`VVIP_ESCORT_SIM_GPS=1`, the signal writer off, the living city off. Then:

```bash
bash scripts/veer_up.sh            # bring-up; READY 11/11 (12/12 with VEER_OSINT=1)
bash scripts/veer_up.sh --status   # read-only readiness, including the security row
```

To enable OSINT later: `bash scripts/veer_env.sh --set VEER_OSINT 1`, then `bash scripts/veer_up.sh`.

---

## 16. Checking the configuration

| Check | Command | What to look for |
|---|---|---|
| Effective non-secret settings and the compose invocation | `bash scripts/veer_env.sh --print` | Paths exist; `osint: on` or `off` as intended. Secrets are not printed |
| Readiness and exposure | `bash scripts/veer_up.sh --status` | Every row READY; the `security` row shows the deck's bind scope and the gate on |
| The gate from the deck's point of view | `curl -s http://127.0.0.1:5273/api/session` | `"gate": true` |
| Imagery mode for an anonymous client | `curl -s http://127.0.0.1:5273/gods-eye/mode` | `"mode": "keyless-osm"` (the token is never sent without a session) |
| Model hosts | `bash scripts/smoke_models.sh` | Decider, Gemma and both embedders answer |
| No secret in the tree or the next push | `bash scripts/secret_scan.sh` | No findings |

If a value you set seems to be ignored, check in this order: is it in `veer.env` (not only in your shell)? Is it a
pass-through key the compose file lists for that service? Did the container get recreated (`veer_up.sh` does this
when its configuration changed)? Is it one of the variables in [§14](#14-set-but-not-read-legacy-and-image-internal)?
