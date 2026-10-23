<h1 align="center">Veer — Ahmedabad's city-scale corridor & enforcement operating system</h1>

<p align="center">
  <strong>One live, human-supervised operating picture for the city's corridor events — VVIP movements,
  processions, mass gatherings, races, ceremonials, stadium egress, flood evacuations and work zones — and
  for stolen-vehicle pursuits, carried from a report to a ranked interception plan on the same rails.</strong>
</p>

<p align="center">
  <img width="840" alt="The God's-eye city in photorealistic 3D on the live stack (2026-10-24 01:25 IST): the 49-road flow network draped on Google's 3D tiles over the Sabarmati, City Vitals and the fusion rail" src="VVIP/showcase/showcase_gods_eye_city.png" />
</p>

Veer runs on a single edge box (an NVIDIA GB10 with 121 GiB of unified memory) beside the city's command
centre. Six services and three local model hosts fuse the live traffic picture, the road network, the
cameras and every agency's units into one God's-eye canvas; a two-tier AI brain plans and proposes; **a named
officer decides** every penalty, pursuit, dispatch and escort route switch. Everything the system emulates or
simulates says so on screen.

## What is in this repository

| Path | What it is |
|---|---|
| [`VVIP/`](VVIP/) | **The platform** — command-deck (SvelteKit + CesiumJS God's-eye), convoy-brain (the two-tier decider/tactical brain and its MCP tools), traffic-oracle (fusion, routing, enforcement, the digital twin), corridor-store (PostGIS + pgRouting, migrations 001–020, the road network re-anchored on real OpenStreetMap roads), event-emulator, signal-ingress (Rust), embedding service; infra (compose, systemd boot units), the bring-up and acceptance scripts, tests, and the live evidence in [`VVIP/showcase/`](VVIP/showcase/) |
| [`submission/`](submission/) | **The jury package** — the deck (`Gujarat_Veer_Deck.pptx` / `.pdf`, its source `make_deck.py` and `DECK.md`), the demo video script and the annexure template |
| [`PROBLEM_STATEMENT_GUJARAT.md`](PROBLEM_STATEMENT_GUJARAT.md) | The problem statement Veer answers |
| [`VEER_COMPLETE_CONTEXT.md`](VEER_COMPLETE_CONTEXT.md) | The full project context — every phase, decision and component |
| [`KAUSHIK_HANDOFF.md`](KAUSHIK_HANDOFF.md) | The operator handoff — daily commands, the acceptance gates, the pre-judging reset |
| [`docs/history/`](docs/history/) | Dated planning records (the base-repo review, the pivot plan, the mentor's God's-eye directive), kept as history |

**Start here:** [`VVIP/README.md`](VVIP/README.md) (what Veer does, the quick start, the evidence) and
[`VVIP/TECHNICAL_DOCS.md`](VVIP/TECHNICAL_DOCS.md) (architecture, contracts, gates and the live acceptance record).

## Run it

```bash
cd VVIP
bash scripts/veer_up.sh --install-units                 # host env (~/.config/veer/veer.env, mode 600) + systemd units
bash scripts/veer_env.sh --set VEER_OPERATOR_PIN -      # the duty PIN, typed on stdin (never on a command line)
bash scripts/veer_env.sh --set VEER_SESSION_SECRET -    # signs operator sessions
bash scripts/veer_env.sh --set VEER_CESIUM_ION_TOKEN -  # optional: photorealistic 3D for signed-in operators
bash scripts/veer_up.sh                                 # models → compose → migrations → real-road seed → READY 11/11
```

Then open **`http://127.0.0.1:5273`** in a browser on the box and sign in with your name and the duty PIN.
`/` is the Convoy Command cockpit, `/ops` the situation wall, `/gods-eye` the 3D city; `/citizen` and `/driver`
are public. The stack starts itself at boot (`veer.target`).

**Supplied by the operator, never committed:** the model weights for the local model hosts (see
[`VVIP/models-config/`](VVIP/models-config/)), the duty PIN and session secret, and the Cesium ion token —
without a token the God's-eye runs keyless on OpenStreetMap imagery.

**Before judging:** `bash VVIP/scripts/demo_reset.sh --apply --officer '<duty officer>' --cancel-debris`
stages the starting state and stops at PENDING — a signed-in human authorises the stolen-vehicle pursuit on
`/ops`; the script prints the judge checklist.

## Principles the code enforces

- **Vehicles only**, via ANPR plates — never faces or persons.
- **Every penalty is a human decision.** A reported-stolen vehicle's owner is never fined: its reads are
  evidence only, approving a fine on it is refused (409), its pursuit is authorised only by an approved
  sighting, and one approval authorises one pursuit.
- **The AI proposes, a named officer decides** — escort route switches, Plan B, closures and holds included.
- **Plates are masked** unless a named officer is signed in; **emulated and simulated sources are labelled**.
- Veer strengthens the state's ICCC / CCTV programmes — it plugs into them, it does not replace them.

## Licence and attributions

Code: MIT — see [`LICENSE`](LICENSE). Road network: © OpenStreetMap contributors, ODbL 1.0 — see
[`VVIP/services/corridor-store/seed/NOTICE.md`](VVIP/services/corridor-store/seed/NOTICE.md). The 3D city
uses Google Photorealistic 3D Tiles, Cesium World Terrain and Bing imagery through Cesium ion, credited on the
canvas — see [`VVIP/services/command-deck/src/lib/gods-eye/NOTICE.md`](VVIP/services/command-deck/src/lib/gods-eye/NOTICE.md).
