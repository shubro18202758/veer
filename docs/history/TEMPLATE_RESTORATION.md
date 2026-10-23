# The VVIP Template Restoration — 2026-10-14

> The original VVIP template (`github.com/shubro18202758/VVIP`, `frontend/`)
> was removed from the veer system during the Phase B–E revamps, and the
> interface accreted redundant layers in its place: a frozen `(legacy)`
> route group with its own off-token styling, a second chat implementation,
> dead component chains, a retired React app, two nav systems. This merge
> brings the template's identity back as the operator's front door —
> **on the token system, wired to the real stack, with the redundancy
> deleted**, not added to.

## What "the template identity" means here (and where it now lives)

| Template signature (original React app) | Where it lives now |
|---|---|
| Saffron sweep line (top edge + section headers) | `Panel variant="glass"` top hairline + the cockpit's 2px sweep; animated via `--v-dur-sweep` (reduced-motion calm) |
| Glass panels floating over a full-bleed map | `--v-glass-bg/border/blur` tokens + glass Panel variant; rails float over the Cesium canvas and never resize it |
| Outfit / Inter / JetBrains Mono | `--v-font-display` (Outfit) added to the token contract + root layout font load; mono readouts everywhere (`tabular-nums`) |
| Top status bar (LLM/GPU dots, counters, IST clock) | `StatusStrip` — REAL: decider/gemma dots read live brain health (degradation tier aware), oracle + emulator dots, live event counts, ticking IST clock |
| Live Corridor Stats pill (scanline) | `CorridorStatsPill` — real `/api/v1/corridor/summary` via one shared feed (`corridor.svelte.ts`), flow word + status from the token ramp |
| Convoy planner (POIs, class pills, lifecycle) | `PlannerRail` — REAL `createMovement → planMovement → launchEscort` through the two-tier brain; RECOMMENDED ribbon on the decider's pick; escort gated by the C6 named-officer rule |
| VVIP class coding (Z+ red · Z orange · Y blue · X slate) | The same four API classes as pills, colored purely through token slots (`--v-band-red`, `--v-act`, `--v-data`, `--v-ink-3`) |
| Threat ladder (nominal → critical) | `ThreatLadder` — 5 rungs colored by token slots only; the live rung is the city band mapped onto the ladder |
| AI reasoning trace console | `TraceConsole` — a filter over the REAL `decisions_log` audit ladder (FeedItem contract reused — one audit renderer deck-wide) |
| Convoy Live HUD (gauge, compass, ETA grid) | `ConvoyHud` — honest: gauge = live corridor average (labelled), ETA/distance from the decider's plan, real elapsed since the officer launched |
| Congestion-colored road network | NEW canvas layer `flow` (`layers/traffic-flow.ts`) — 5-stop ramp from tokens; segments without observations render neutral hairlines, never guessed colours |
| Vignette + film grain + dock + coords pill | Cockpit overlays, all token-driven |

**Deliberately NOT restored:** the client-side convoy simulation engine
(the fake telemetry the original ran in the browser). Every number on the
restored cockpit comes from the real stack or is honestly labelled absent.

## The merge rules that kept it non-redundant

1. **Through the token system, never around it.** Seven new keys
   (`--v-font-display`, `--v-glass-bg/border/blur`, `--v-glow-act`,
   `--v-flow-light`, `--v-dur-sweep`) in BOTH themes, mirrored in
   `tokens.ts` (parity gate: 74 vars). The template's threat ladder and
   congestion ramp are expressed **entirely in existing token slots** —
   no second palette exists.
2. **One renderer per concept.** The audit ledger renders through FeedItem
   everywhere; the dossier slide-in reuses `EventDossierDrawer`; the map
   is the one God's-eye canvas (Leaflet is gone with the React app).
3. **Redundancy deleted, not archived:** the whole `(legacy)` route group
   (`/command` `/map` `/planning` `/simulation`), `lib/components`
   (ChatPanel chain incl. ChatMessage/ThoughtChain/ToolCallCard/ChatInput,
   LoadingSkeleton, ConnectionBanner, ConvoyTracker, DiversionTimeline,
   RouteComparator, SegmentInspector, TrafficHeatmap, CorridorMap,
   SimulationViewer), `lib/simulation` (WebGPU engine), `lib/stores`,
   and `lib/api/data-service.ts`. Their live capabilities were absorbed:
   convoy tracking + route planning → the cockpit planner/canvas; the
   event emulator panel stays on `/ops`.
4. **All revamps kept intact:** `/ops` situation wall, `/gods-eye`
   cinematic route, `/citizen` + `/driver` daylight surfaces, `/comms`
   advisory desk, `/chat` console, i18n trilingual, watchlist/ANPR,
   pursuit, signal gate, AMA — untouched and re-verified.

## New topology

```
/          Convoy Command cockpit  (the restored template; operator home)
/ops       Situation wall          (city-scale multi-event command)
/gods-eye  Cinematic canvas
/comms     Advisory desk (trilingual)
/chat      Agent console
/design    Living style sheet
/citizen   /driver                 Public daylight surfaces
```

The `frontend/` React app remains in-tree for what it still uniquely
provides: the offline fallback demo, the `verify_all.sh` e2e tier harness,
and the puppeteer/Chrome provider for the camera scripts. It is not served
by any compose file (the gb10 override replaced that build stanza long ago).

## Bugs found and fixed along the way

- **`EMULATOR_PORT=8095` in `compose.argus-override.yml`** pointed at a
  containerised emulator that never existed — the argus deck's
  `/api/emulator` proxy 502'd (red EMULATOR dot, degraded emulator panel).
  Fixed to the shared host emulator on `:8090`; proxy now 200.
- **Brittle canvas gate:** `gods-eye-smoke` used a fixed 9s sleep for
  SwiftShader tile settle — under tonight's host load it timed out
  (baseline gate failure). The canvas now publishes `tilesLoaded` from
  Cesium's `tileLoadProgressEvent` in real time and the test polls with a
  45s bound, same assertion semantics.

## Verification (all machine-checked, 2026-10-14)

- `svelte-check`: 0 errors, 0 warnings (whole deck)
- `design-tokens`: parity 74×2, hex sweep 16 targets, boundaries — pass
- `design-smoke`: new topology tripwire + all assertions — pass
- `gods-eye-smoke`: canvas non-blank, keyless, `flow` layer live
  (77 entities, 6 layers), `/ops` wall assertions — pass
- `ops-write-smoke`: city-writer safety — pass
- **`verify_all.sh` from the clone: ALL TIERS PASSED** (422 pytest
  passes, live models, e2e, canvas)
- Live argus deck (`:5273`) rebuilt from this tree; cockpit verified by
  probe + screenshot (all four health dots green, real audit rows
  flowing; archived at `screenshots-submission/argus-convoy-command-restored.png`)
