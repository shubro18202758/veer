# Veer — Product Description

Veer is a city-scale, multi-agency operations platform for Ahmedabad, Gujarat. It gives the city's traffic police,
police control room, 108 ambulance service, fire service, Jan Rakshak and municipal teams one shared, live picture
of the city's roads, and helps them run four kinds of work on it: protected movements and green corridors,
stolen-vehicle enforcement support, event intelligence from public sources, and decision support for incidents.
Citizens and 108 drivers get their own plain-language pages. Throughout, the AI proposes and a named human officer
decides.

This document describes the whole product. **Part A** (sections 1–4) is written for everyone: officials, officers,
reviewers and the curious. **Part B** (sections 5–7) is for engineers who clone the repository. Every statement
here is taken from the code or from the committed documentation it names; numbers that come from a model, not a
field measurement, say so.

The repository directory is called `VVIP/` because the platform was born as a protected-movement (VVIP convoy)
planner. Veer has since grown into a general city platform; protected movements are now one use case among many.

---

## Contents

**Part A — The product**

1. [What Veer is](#1-what-veer-is)
2. [Principles](#2-principles)
3. [The interface, surface by surface](#3-the-interface-surface-by-surface)
4. [Capabilities in depth](#4-capabilities-in-depth)

**Part B — Engineering**

5. [Architecture](#5-architecture)
6. [Honest status: what is real, what is emulated, what is left](#6-honest-status)
7. [Getting started](#7-getting-started)
8. [Licence and attributions](#8-licence-and-attributions)
9. [Glossary](#9-glossary)

---

# Part A — The product

## 1. What Veer is

### 1.1 In one paragraph

Veer runs on a single edge server beside a city control room and turns phone-and-radio coordination into one
auditable operating picture. It plans protected movements and other corridor events (processions, marathons,
stadium egress, flood evacuations, work zones) on Ahmedabad's real road network, replaces long blanket road freezes
with short predicted rolling holds, lets a 108 ambulance driver ask for a green corridor in one tap, carries a
stolen-vehicle report from the first FIR to a ranked interception plan without ever fining the theft victim, turns
public news and official alerts into situations about places (never about people), and proposes ranked courses of
action for an incident. Every proposal — from the AI, the rules engine or the decision-support engine — waits for a
named duty officer, and every decision is written to an append-only audit trail under that officer's name.

### 1.2 The problem

When a protected person or a ceremonial movement travels by road today, traffic along the corridor is stopped well
before the convoy arrives, routinely for 15 to 45 minutes at each major junction, although the passage itself
occupies a junction for seconds. Coordination runs by phone, radio and messaging apps across at least five separate
hierarchies — traffic police, district administration, state security, municipal signal teams and 108 dispatch —
none of which share a live picture. Routes are chosen by precedent, closures are timed by rough margins, a 108
ambulance has no channel to ask for passage, and the public learns of a closure at the barricade
([`PROBLEM_STATEMENT_GUJARAT.md`](PROBLEM_STATEMENT_GUJARAT.md)).

The protocol is not the problem. The protected-movement protocol already says traffic is to be *"regulated, not
stopped"*. What has been missing is tooling precise enough to execute that rule: to predict when each stretch must
close, close it only for as long as needed, tell people in advance, and let an ambulance through. The same gap
appears in every event that takes over a corridor for a while — the Rath Yatra, a marathon, a cricket crowd leaving
the stadium, a flood evacuation — and in everyday enforcement, where a stolen car's camera reads, the watchlist and
the pursuit rarely sit on one auditable platform with a human in charge of every penalty.

### 1.3 Who benefits

| Person | Today | With Veer |
|---|---|---|
| **Commuter** (a daily-wage worker on Ashram Road, an office-goer on SG Highway) | Discovers a 15–45 minute freeze at the barricade | Short rolling holds of about 2–3 minutes per junction (modelled — §6.2), and an advance notice in English, Hindi or Gujarati with the alternate road |
| **Emergency patient** in a 108 ambulance | The golden hour can be lost at a barricade | The driver's request reaches the duty officer at once; an approved corridor window opens ahead of the ambulance |
| **108 driver** | No way to ask for passage | One request from a phone-friendly public page, in Gujarati first, with a clear answer and a live countdown |
| **Traffic constable** at the barricade | A phone order given 30 minutes early | Per-segment activation and release times, drafted zone-officer advisories, less public anger absorbed |
| **Duty officer / control room** | Five agencies on phone and radio | One console: what needs a decision now, the real map of the place, what changes if they approve, and their name on the record |
| **Investigating officer** | Recovery of a stolen car depends on luck | Lawful camera reads of the watchlisted vehicle as evidence, an officer-authorised pursuit and ranked interception junctions |
| **Citizen** | No reliable advance information | A public page that says, in plain words and three languages, which roads will hold, when, for how long, and which data is a simulation |
| **City administration** | Disruption is never measured | Every decision, band change and approval recorded; after-action reports per movement |

### 1.4 What Veer is not

- **Not a surveillance system for people.** Cameras read vehicle registration marks only; there is no face, person,
  image or biometric field anywhere in the data model, and no person search.
- **Not autonomous.** No penalty, pursuit, dispatch, signal change or escort route switch happens without a named
  officer's approval. If nobody answers a time-boxed proposal, the current plan holds.
- **Not a replacement for the state's systems.** Veer is built to plug into the state's ICCC, CCTV and ITMS camera
  programmes and to support the police, traffic, 108, fire and Jan Rakshak; every authority stays with them.
- **Not connected to agency radio or computer-aided dispatch today.** A dispatch is an approved, audited request;
  the units shown on the map are emulated (see §6).

---

## 2. Principles

These rules are enforced in the database schema, the server code and the interface — not left to convention.

| Principle | What it means in practice | Where it is enforced |
|---|---|---|
| **Vehicles only** | Cameras read registration marks; camera sites store location and identity only (no frame, image or stream). No face, person or biometric field exists on any path. | Schema (migrations 010–012), the oracle's enforcement and city modules, the interface copy ("Vehicles only: cameras read plates, never people") |
| **Plates masked until a duty officer is named** | Every surface shows a mark like `GJ27EM•••1` with a lock until a named officer is on the console. Exports, share links, saved views and watches are always masked. | The oracle masks every label and feed text it sends; the deck masks every plate it renders; CSV export and saved views mask regardless of officer state |
| **AI proposes, a named officer decides** | The AI, the rules engine and decision support only create PENDING proposals. Approve controls exist only in Decide and in the Analyst workspace and situation wall — never on the map, in the assistant, on object pages or on public pages. | Server refuses an unnamed decision (409 or 422); the assistant's tool rail cannot approve, decide, dispatch or earmark |
| **No answer means the plan holds** | A live-escort proposal (route switch, Plan B, hold, new closures) expires after 90 seconds by default (configurable 15–600 s); the convoy keeps its current approved plan — it neither stops nor switches. | convoy-brain escort workflow (`VVIP_ESCORT_APPROVAL_TIMEOUT_SEC`) |
| **No fine on a theft victim** | Camera reads of a reported-stolen vehicle are evidence only. Approving an e-challan on it is refused (HTTP 409). Only an approved sighting can authorise a pursuit, and one approval authorises one pursuit. | Oracle enforcement rules and pursuit validator (migration 017) |
| **Lawful basis and capped retention** | A watchlist entry needs an enumerated lawful basis (MV Act 1988 s.177/s.183/s.207, BNSS 2023 s.94, or a stolen-vehicle FIR) and a server-computed retention capped at 90 days. | Schema CHECK constraints; read-path reaper |
| **Honest labels** | Every source says what it is: **EMULATED**, **SIMULATED**, **UNVERIFIED-OSINT**, **NEWS-REPORTED**, **OFFICIAL-VERIFIED**. A visual effect is never presented as a sensor feed or a real photo. | Row-level provenance fields, interface tags, the "thermal-style view (visual filter, no thermal sensor)" label |
| **OSINT is about places and situations, never persons** | Names and ages are redacted at parse; news and social URLs are never stored or shown (the outlet's domain and a hash only). | osint-ingress redactor, osint-common ethics checks, oracle ingest guard (`pii_unredacted`) |
| **Strengthen, never undermine, the authorities** | Veer is framed as the control room's tool. The security veto and every operational authority stay human. | Product copy and design rules |

---

## 3. The interface, surface by surface

The interface is the **command deck**, a web application served on port 5273 of the Veer server and opened in a
browser. Operator pages share one dark "night" theme; the two public pages use a light "day" theme. Both are
neutral — black, white and greys, with white (night) or black (day) primary buttons — and colour is kept for meaning
only: orange means a named officer must decide, red a stolen or watchlisted vehicle, green approved or healthy, teal a
protected movement and its route, blue a link or something the assistant wrote or proposed, and a dashed outline
means emulated or unverified. Every surface carries imagery as well as maps: studio shots of each vehicle class and of
the four convoy compositions (Z+, Z, Y, X), key art for every event kind, time-of-day scenes of the Sabarmati
riverfront, credited reference photographs of the city's places (always captioned "Reference photo · not live") and
the marks of the agencies and data sources Veer works with. The design rule is *simple by default, depth on demand*: each screen has one job and one primary button, and every power tool of the
earlier analyst workspace is kept one click deeper under **Analyst**. Nothing was removed; some things moved one
level down.

### 3.1 The shell (every operator page)

- **Left rail**, in the order of the officer's jobs: **Home**, **Map**, **Decide**, **Plan**, **Assistant**,
  **Advisories**, and, separated at the bottom, **Analyst** (visible to every officer). Decide carries the only
  badge: the number of decisions waiting. Every item has an icon and a label.
- **Slim top bar**: the screen title; one search box (the omnibar — `Ctrl K`, `⌘ K` or `/`) for "a place, road,
  event or vehicle mark"; a compact menu holding the language (EN · हिंदी · ગુજરાતી), the exercise-data statement,
  the data status of every feed and the map style; the **alerts bell**; and the **officer pill**.
- **Officer pill**: reads "Name the duty officer · Plates hidden" until an officer is named. With the operator gate
  on, it shows the signed-in officer and holds sign-in and sign-out. The helper text says exactly what naming does:
  *"Naming yourself shows full registration marks on this console and records your name with the decision.
  Attribution, not sign-in."*
- **Alerts bell and chime**: keeps the last 50 alerts with read state per browser. A soft two-note chime (generated
  in the browser, no sound file, no network) is on by default for each new waiting decision and can be muted.
  Decisions already waiting when the page loads never chime, one sync chimes once however many arrive, and an
  emulated or test item chimes only while the console declares it is running on exercise data — so the chime never
  trains officers to react to a rehearsal.
- **Live band**: a 36 px strip under the top bar, shown only while something is live (a movement, a pursuit, a
  decision with a deadline) on pages that do not already show it. Live operations are never hidden.
- **Analyst sub-navigation** on the Analyst pages: Workspace · Situation wall · City map · Assistant, plus the city
  band tag, the Inbox chip, the Data panel, **Policies** (what this console will never do) and More.

### 3.2 Home (`/`, also `/home`)

The first screen answers three questions: what needs me, what is happening, what is coming.

- **Featured decision**: the waiting decision with the soonest deadline, over the real satellite map of its place,
  with tags (for example "Needs you now", "Rules engine", "Emulated"), a one-line reason, two or three key figures
  (time waiting or left, camera reads), and one large **Review now** button. It states the rule underneath: *"It
  keeps waiting until an officer decides. Nothing changes without a named officer."* For a time-boxed escort
  proposal it says that if no one answers, nothing is applied.
- **City pulse**: one sentence for the city band ("The city is steady", "Traffic is building", "The city is under
  strain", "Roads are at a standstill"), the band's age, and four large counts — decisions that need you, live
  operations, reported events (split official / news / unverified), watchlisted vehicles (with "plates hidden until
  an officer is named"). A systems line says, for example, "28 of 28 cameras answering · Traffic simulated on 49
  roads", and turns into a plain warning if a feed stops answering ("Decisions still work").
- **Four rails of map-thumbnail cards**: **Needs your decision** (soonest deadline first), **Live operations**,
  **Reported in the city** ("from news, official alerts and public reports, about places, never people") and
  **Coming up** (next 72 hours, with a link to plan a movement).
- **Footer rules**: "Vehicles only. Plates stay masked until a duty officer is named." · "The assistant proposes. A
  named officer decides every action."

### 3.3 Decide (`/decide`, `/decide/<unit>`)

One decision at a time, soonest deadline first. Three zones: the queue on the left, the **real map of the place**
in the middle, and one decision sheet on the right.

Each sheet follows the same anatomy: what is being decided, why, the key facts, the options (for a decision-support
case, the courses of action as option cards with the recommended one preselected), **"What changes if you approve
/ reject / defer / authorise"**, and one primary button carrying the officer's name. Kinds of decision handled here:

- **Stolen-vehicle sighting** — a masked plate with a lock and a vehicle-class silhouette ("Car · registration mark
  masked … Vehicles only: cameras read plates, never people"); a two-step stepper, **1 Authorise → 2 Open the
  pursuit**; the reads as a timeline (camera, road, speed, time); and the rule: *"Evidence only. No fine is ever
  issued for a stolen vehicle. One approval opens one pursuit."* Buttons: "Dismiss all…" and **Authorise pursuit**.
- **E-challan recommendation** — on a reported-stolen vehicle it can only be rejected: "Its owner is the theft
  victim, so this e-challan can only be rejected."
- **Escort proposal** (time-boxed) — a countdown ring and "If no one answers in time, the current plan is kept and
  nothing is applied."
- **108 corridor request**, **choose a response** (decision support), **pursuit opening** and legacy escort
  approvals follow the same anatomy.

**"Who is deciding?"** sits on every sheet: until an officer is named the buttons are visible but disabled, with the
reason ("Name yourself above to decide"). After deciding, the sheet collapses to its outcome ("Approved · recorded
with your name …"), the queue row turns green, and **Next decision** moves on. A server refusal is shown verbatim
inside the card, never as a passing toast. A side tally shows what was decided on this console (approved, rejected
or dismissed, deferred, expired with the plan kept), with a link to the full record in Analyst.

### 3.4 Object page (`/o/<urn>`)

Every record has a page: corridor event, reported (OSINT) event, vehicle, place, operation (convoy), junction,
camera, dispatch, recommendation and sighting, with a generic layout for any other valid record. Each page has a
hero map of the place (a lightweight map tile, not a 3D viewer), the title and honest tags, key facts, a timeline
and the actions, with depth in tabs: **Overview · Sources** (reports) **· Reads** (vehicles) **· Pursuit** (when one
is open) **· Timeline · Nearby · Record** (every field the analyst inspector shows). A reported event shows "How sure
are we" — a credibility gauge with four plain checks and a verification ladder (Unverified → News-reported →
Official), with the reminder that credibility measures how far sources agree, not whether the report is true. A
vehicle page lists only lawful reads; a read without a lawful basis reads "Withheld: no lawful basis". A read-only
**Ask about it** panel sends a question to the assistant. A link that is not a valid record identifier reads "Not a
record" and fetches nothing.

### 3.5 Map (`/map`)

The God's-eye city canvas, clean by default.

- **Base map**: opens on the natural-colour **photoreal 3D city** (Google Photorealistic 3D Tiles over Cesium World
  Terrain with Bing aerial imagery, through Cesium ion) when the server holds an ion key, labelled *"Photoreal 3D city
  from Google, via Cesium ion · not a live image"*; otherwise the night city map drawn from OpenStreetMap, with the
  reason shown on the 3D control. The choice is remembered per browser.
- **Four group chips** across the top — Live operations · Needs your decision · Reported in the city · Coming up —
  plus **Layers**. An official district weather warning, when one is in force, appears as its own chip.
- **Layers sheet on the left** (collapsible, translucent): base map, Operations (units, dispatches) and City (ANPR
  cameras — "read registration marks only", junctions and signals, traffic flow — "simulated on 49 roads", named
  places, feed checks), with the reminder "Vehicles only. Cameras read registration marks; no images, frames or faces
  are kept."
- **Now panel on the right**: the same objects as the map, grouped the same way, with live countdowns, and a
  **Replay** entry for recorded emulator runs (blocked while a movement is live or a pursuit is open; "Every replayed
  object is emulated. Decisions stay live.").
- **Selection card** for anything picked: key figures, **Review**, **Follow**, **Details** (opens the object in
  Analyst). Selecting an event focuses the map on it and dims the rest ("Show all" returns).
- **Tools**: satellite 3D, **thermal-style view** ("a visual filter, no thermal sensor"), measure, follow, zoom and
  north. A three-line legend (a decision waits · stolen or watchlisted vehicle · protected route) can be hidden.
  **Corridor stats** (signal band, traffic on the corridors, escorts) live in their own panel, closed by default.
- If map tiles stop loading, the roads are still drawn from Veer's own network and the map says so.

### 3.6 Plan a movement (`/plan`)

A four-step flow beside a satellite map: **Where to → Routes → Launch → Live**.

1. **Where to** — From and To with place search; the **protection class** as four cards read from the protocol
   table the planner applies (Z+ 6-lane floor, roads close 3 min ahead; Z 4-lane, 2 min; Y 2-lane, 1 min; X 1-lane
   floor, no advance closure); departure (in 30 min, in 1 hour, at a time); an optional test or rehearsal label ("A labelled
   movement is never shown as a real one"). **Find routes** registers the movement with the planner — "Nothing moves
   until a named officer starts the escort."
2. **Routes** — best first, each card with time, distance, roads held, whether it meets the lane floor or how many
   lane-floor violations it has, and its state: Ready to launch · Needs a waiver · Held by the decider · No route.
   The recommended route is marked; times come from the traffic twin and are labelled "Simulated traffic".
3. **Launch** — a conditional plan needs the officer to accept the listed lane-floor waiver; then "Who is
   launching?" and **Start escort** ("One press sends one request"). A refused or failed launch is shown in the
   brain's own words and never retried on its own.
4. **Live** — "Escort running", the emulated convoy position (labelled), "A decision waits on this escort → Review
   in Decide", Follow on the map, **Stop escort**, and **Clear the movement** (lifts the closures, restores the
   signal programs and closes the corridor event).

### 3.7 Assistant (`/assistant`)

"Ask about the city." A conversation with the two-tier AI that reads live operations, decisions, reported events
and the traffic feed — never people — and **cannot approve, unmask or dispatch**. Answers are short prose with
tappable object chips; a proposal arrives as a card that opens in Decide, never with an approve button. Suggested
questions include "What needs me in the next hour?", "Which events are active right now?", "Where was the stolen
vehicle last read?" and "Which roads are slowest right now?". Model diagnostics become one plain caution (for
example, that a figure is simulated or that a backup model answered); model and trace details are one click away.
Every answer is checked against what the tools actually returned (§4.12).

### 3.8 Advisories (`/comms`)

The communications desk: "One fact, every audience, every language — drafted for an officer to send, never
auto-sent."

- Left: the events eligible for advisories, and **Templates by event kind**.
- Centre: the selected event on a satellite map; the audience switch — **Citizens · SMS / WhatsApp**, **Zone
  officers**, **108 control**, **Municipal**; **Generate advisory** and **Draft all-clear**; and the three drafts side
  by side — **English, हिंदी, ગુજરાતી** — carrying the same facts verbatim, each with a Copy button and a "Facts used"
  disclosure.
- The status is stated once: **"Drafted — not delivered"**, with the reason: no message gateway is deployed, so an
  officer copies and sends the text; nothing is delivered from Veer.
- A side sheet holds the draft log and the dispatch threads.
- Withholding rules: operator-only event kinds (for example a pursuit) and OSINT reports are never drafted for
  citizens, and the rule fails closed.

### 3.9 Analyst (`/analyst` and its family)

Analyst keeps the full-density professional workspace for supervisors and control-room analysts. Its sub-navigation
joins four views:

- **Workspace** (`/analyst`) — the full analyst workspace: a full-bleed God's-eye canvas with Map, Graph
  (link analysis, "search around", find paths), Table (with masked CSV export) and Split views; a bottom dock with a
  brushable Timeline, the Audit table, the AI trace and Replay; a right dock with the Inspector, the Inbox ("Needs
  your decision" by deadline, plus Updates) and the Assistant; the planner and the officer-gated escort HUD ("AI
  PROPOSES … — APPROVE / REJECT · expires in mm:ss"); saved views and watches (stored masked in the browser);
  share links that restore the exact view.
- **Situation wall** (`/ops`) — the 24/7 wall: a situation header (active events, decisions waiting, units
  dispatched, ambulance windows, corridor speed, congested roads, watchlist reads, feed anomalies, over 1 h / 6 h /
  24 h / 7 d); the Decisions panel (needs decision · approved · rejected · expired) holding e-challans, stolen-vehicle
  sightings, dispatch requests and the escort lane; the wall canvas; the city band chart; **City Signal Plans**
  (band → corridor priority and cross-street green, writer state, Apply plan · Restore · Restore all · History); the
  **Active Movement Adaptation** module card; Jan Rakshak dispatch; twin shadow-eval comparison; the interception
  choke plan; the degradation ledger; the event emulator panel; and the **Audit** stream (city or selected event;
  all · officers · machine · system; "Ask why").
- **City map** (`/gods-eye`) — the fullscreen 3D city with City Vitals (open events, decisions waiting, watchlisted
  vehicles, cameras answering, feed anomalies, reported events, traffic feed "Simulated"), eleven layers, sensor
  modes, share links and replay.
- **Assistant** (`/chat`) — the full chat console with its context header, stream and degradation chip.

### 3.10 Public pages: Citizen and 108 driver

Both public pages need no sign-in, load no operator code, run under a strict content-security policy, receive no map
key, and are served only from the deck's own public projection of events — never from an operator feed. The
browser's geolocation, camera and microphone are disabled for the whole site by policy. They use the day theme and
never use the alert red or the decision orange, whose meanings belong to the operator console.

- **Citizen — your road** (`/citizen`): "Corridor alerts · Ahmedabad — Your road, next 2 hours". One plain posture
  sentence ("No corridor holds announced right now."), then hold cards, each topped by a map of the stretch: a
  **solid** line is live; a **dashed** line (and a dashed card) is emulated, fixture or unverified, badged
  **SIMULATED FEED · EMULATED**, never LIVE. Each stretch shows its road name, the approximate hold length and time,
  and the alternate. Also: Today / Later, "Why roads hold", and a subscribe preview that sends nothing. No plate, no
  pursuit and no operator-only event ever appears here. A protected movement's route stays off the public feed until
  it is inside the two-hour horizon.
- **Driver — the window** (`/driver`): Gujarati first. A clock that counts from the moment *this* request was sent
  (it never claims to be the golden hour itself, which began at the incident); four large steps from request to
  "awaiting the duty officer" to "approved by a named officer" to the open window with a live countdown; the driver
  picks the stretch from a list, types the 108 unit number and chooses the urgency (cardiac, accident, stroke, other
  emergency); one **Request a corridor window** button. There is **no approve control, no location collection and no
  registration mark**. Only real corridors are requestable — an emulated event is never offered. With no live
  public event up, a labelled scripted fallback walks the steps and sends nothing.

### 3.11 Languages and accessibility

Every user-visible string of the operator screens ships in English, Hindi and Gujarati, loaded on the route that
needs it; the language follows a cookie shared by all pages. Operational numbers and times stay in Latin digits on
operator pages. The shell starts with a "Skip to main content" link; rails are keyboard-navigable lists; motion
respects the reduced-motion setting; illustrations are original artwork and vehicle-class silhouettes — never a
photo, never a person, never anything that looks like a camera feed.

### 3.12 Keyboard shortcuts

No single key approves, unmasks, dispatches or publishes.

| Keys | Where | Action |
|---|---|---|
| `Ctrl K`, `⌘ K` or `/` | everywhere | Open search (the omnibar) |
| `G` then `H` / `M` / `D` / `P` / `A` / `V` | everywhere | Go to Home / Map / Decide / Plan / Assistant / Advisories |
| `Esc` | everywhere | Close, then clear; never navigates |
| `?` | Analyst pages | Shortcuts sheet |
| `J` / `K` (or arrows) | Decide | Next / previous waiting decision |
| `1`–`4` | Decide | Choose a response option |
| `Enter` | Decide | Focus the primary button (it never presses it) |
| `R` | Decide | Open the reason field (a reject still needs a click) |
| `L` / `F` / `3` | Map | Layers / Follow / 3D city |
| Arrows, `Home`, `End` | Home rails | Move between cards |

### 3.13 Surface map

| Surface | Route | Audience | Sign-in |
|---|---|---|---|
| Home | `/`, `/home` | Duty officer | Operator |
| Decide | `/decide`, `/decide/<unit>` | Duty officer | Operator |
| Object page | `/o/<urn>` | Officer, analyst | Operator |
| Map | `/map` | Officer | Operator |
| Plan a movement | `/plan` | Officer | Operator |
| Assistant | `/assistant` | Officer | Operator |
| Advisories | `/comms` | Communications officer | Operator |
| Analyst · Workspace | `/analyst` | Analyst, supervisor | Operator |
| Analyst · Situation wall | `/ops` | Control room | Operator |
| Analyst · City map | `/gods-eye` | Control room | Operator |
| Analyst · Assistant | `/chat` | Analyst | Operator |
| Citizen advisory | `/citizen` | Public | None |
| 108 green corridor | `/driver` | 108 drivers | None |

Old bookmarks of the former root (`/#v=…`) are handed to `/analyst#…`. Developer galleries under `/design/*` answer
404 in production unless explicitly enabled.

---

## 4. Capabilities in depth

### 4.1 Protected movements and corridor operations

A movement runs in three phases, each AI-assisted and each with its decisions of consequence left to a named
officer.

**Pre-movement planning.**
- The officer picks origin, destination, protection class and departure. The planner asks the strategic AI (the
  decider) three typed questions — route strategy, urgency, disruption tolerance — against a bounded state
  document, then the tactical tier drafts and validates.
- **Routing**: an OR-Tools optimum plus pgRouting k-shortest alternatives (up to five candidates by default), each
  scored on travel time (30 %), traffic disruption (40 %), security compliance (20 %) and route complexity (10 %).
  The adaptive layer may reweight per movement, always within protocol floors and failing closed to these
  baselines. Routing can price the adverse tail of the forecast (P90-robust routing) and ETAs carry bands when the
  forecaster supplies them.
- **Security validation** against the protection class. Routes that violate a lane floor are rejected or marked
  *conditional* with the reason attached. On the current network every Z+ plan is honestly conditional: no route
  meets the Z+ six-lane floor end to end, so launch needs an officer's waiver.
- **Closure (diversion) plans** per segment: activation timing, queue estimates, the detour and its status
  (`found`, `no_path` — a bridge with no way round, `dead_end`, `impractical` — where the plan says to hold or meter
  traffic instead). Detours are computed on the turn graph: one-ways are never driven backwards and a segment closed
  at the same time is never part of a detour.

| Class | Lane floor | Closure type | Advance-closure floor |
|---|---|---|---|
| **Z+** | 6 lanes | Full closure | 180 s |
| **Z** | 4 lanes | Partial closure | 120 s |
| **Y** | 2 lanes | Speed restriction + signal priority | 60 s |
| **X** | 1 lane (any road) | Signal priority only | none |
| **none** (public event, no protectee) | — | Per event kind | none |

**Live escort — predictive rolling holds.**
- Closures activate 60–180 seconds before the convoy reaches each segment, inside the class's protocol floor, and
  release as it passes — instead of a blanket freeze.
- The position loop (adaptive 1–5 s) is pure numeric code with no AI call. No GPS hardware feeds this deployment, so
  an escort walks its approved route on a labelled **emulated GPS**, and stops doing so the moment real fixes arrive.
- The strategic AI is woken only by events: an incident ahead, a congestion-threshold crossing, a situation-band
  change, a phase transition or an operator question — with at least 5 seconds between checkpoints per movement.
- **Escort authority — "officer approves every switch".** Any answer that would change the plan — a hold, **Plan B**
  (the pre-sanitised alternate), an emergency re-route (a deterministic solver call that avoids the hot segments and
  passes the lane floor) and the closures a new route brings — becomes **one open proposal** per escort, computed in
  full (the exact route, closures added and lifted, distance before and after, who proposed it and how confident).
  A proposal raised by a fixed rule because no model answered is labelled "RULE PROPOSES", never AI.
- The officer approves or rejects on Decide, the escort HUD or the situation wall. An approval applies exactly what
  the officer saw; if the convoy has passed the branch point, it is re-proposed rather than improvised. **With no
  answer in 90 seconds (configurable 15–600 s) the proposal expires and the current plan is held.**

**Post-clearance.** Closures deactivate segment by segment; recovery is monitored until congestion returns below
threshold; an after-action report summarises escort duration, segments affected and recovered, recovery time,
diversions lifted, and the counts of alerts and audited decisions.

**Protocol state** (the Advance Security Liaison checklist, compliance rules, transit status, Plan B) is recorded with the
movement by a named officer. No model fills in a threat level (it defaults to "not assessed"); the old model-written
security dossiers and threat assessments were retired and now answer HTTP 410.

### 4.2 One engine, eight corridor event classes

The same engine expresses any planned operation that takes control of part of the road network for a window. One
data model (`events.corridor_events`) carries five independent axes — protection class, crowd class, event kind,
footprint and phases — and the kind selects closure-policy templates, never separate code paths
([`VVIP/docs/USE_CASES.md`](VVIP/docs/USE_CASES.md)).

| # | Event class | Kind | Protection | Crowd | Seeded closure policy |
|---|---|---|---|---|---|
| 0 | Protected-movement base case (Gandhinagar → city core) | `protected_movement` | Z+ | Low | full closure, 180 s |
| 1 | Jagannath Rath Yatra, old city | `procession` | none | Extreme | full closure, 120 s |
| 2 | Kumbh-class mass gathering | `mass_gathering` | none | Extreme | signal hold, 90 s |
| 3 | Sabarmati riverfront marathon | `race` | none | High | full closure, 60 s |
| 4 | Republic Day / Independence Day | `ceremonial` | Z | High | full closure, 150 s |
| 5 | Narendra Modi Stadium egress | `egress_surge` | none | Extreme | signal hold, 60 s |
| 6 | Monsoon flood evacuation | `emergency_evacuation` | none | Medium | signal hold, 60 s |
| 7 | Metro / bullet-train work zone | `work_zone` | none | Low | partial closure, 60 s |
| 8 | Stolen vehicle → camera sweep → pursuit | `crime_incident` + `vehicle_pursuit` | none | Low | none (watchlist, not closure) |

Each is a runnable scenario on the real road network. A flagship composite, "God's Eye Morning", layers the Rath
Yatra, a monsoon burst on the Nehru Bridge approach, a 108 cardiac ambulance and the full stolen-vehicle chain onto
one morning; for the public procession the engine's answer was a signal hold at 45 seconds' advance — regulated,
not stopped.

### 4.3 The road network — Ahmedabad's real roads

- **49 road segments, 34 junctions, about 192 km** (191.76 km measured in the database), one strongly connected
  network with 198 turning movements. Each segment runs along the real road of its name between two real
  intersections — Ashram Road, CG Road, SG Highway, SP Ring Road, the Gandhinagar Highway, Relief Road, Nehru Bridge
  Road, Dr. Ambedkar Road, Sarangpur Road, Indira Bridge, Motera Stadium Road and others — and each junction sits on
  its OpenStreetMap node.
- On it: 11 signal-controlled junctions with signal programs, 28 camera sites (24 ANPR + 4 CCTV, emulated), and 18
  agency stations (police 8, ambulance 4, Jan Rakshak 3, fire 2, traffic 1).
- The network is generated deterministically from committed OpenStreetMap extracts (`scripts/gen_osm_network.py`)
  and re-verified offline with `--verify`: every segment within 15 m of its OSM centreline (worst 7.76 m), ending at
  its junctions, length within 2 % (worst 0.96 %). Migration 020 records the provenance on every row.
- Road geometry © OpenStreetMap contributors, ODbL 1.0.

### 4.4 The traffic picture and forecasting

- **Ingest.** The Rust `signal-ingress` service runs four feed adapters (government traffic, mapping API, fleet GPS,
  crowdsource) over the 49-segment network, runs eight inline plausibility checks per reading (future timestamp,
  stale data, speed jump, phantom reading, speed z-score, congestion outlier, road-class mismatch, spatial mismatch)
  and publishes Arrow batches over NATS. **No live traffic connector is wired yet: every row is synthetic and
  labelled so**, and the interface says "Traffic simulated on 49 roads".
- **Forecasting** (5, 10, 15 and 30 minutes ahead) runs as a ladder: a support gate that keeps any out-of-range
  input away from every model → a third-party zero-shot foundation forecaster (t0-alpha, ONNX INT8, Apache-2.0) →
  Veer's own DSTGAT graph-attention forecaster → a labelled heuristic. **The DSTGAT architecture ships as code only;
  no trained weights are bundled**, so today's forecasts come from t0-alpha or the heuristic rung, reading the
  synthetic feed's own history.
- **Synthetic history is kept apart.** Real hourly aggregates (the only input calibration may read) and the
  synthetic rollup live in separate tables; a fresh install holds zero real rows.

### 4.5 Active Movement Adaptation (AMA)

A deterministic, auditable self-adjusting layer
([`VVIP/docs/ACTIVE_MOVEMENT_ADAPTATION.md`](VVIP/docs/ACTIVE_MOVEMENT_ADAPTATION.md)), in six stages:

1. **Situation** — every active subject is scored from security tier, traffic regime, weather, crowd density and
   anomaly and event flags (score 0–21) into **GREEN (0–4), AMBER (5–9), RED (10–14), BLACK (15–21)**. The score is
   monotone: worsening any single input can never soften the band, and a Z+ movement is never below AMBER.
2. **Hysteresis** — a band change must persist through a dwell window; bands never flicker.
3. **Protocol floors** — advance-closure floors (Z+ 180, Z 120, Y 60 s) apply to every published parameter.
4. **Twin shadow-evaluation** — any deviation from baseline must beat the baseline in a paired digital-twin run, or
   the engine fails closed to baseline.
5. **Audited persistence** — every observation and every published parameter change is logged with its reason.
6. **City signal plans** — the city band (the most severe active subject) drives the gated signal-plan writer.

Emulated traffic lives in its own key space and can never drive a real event's band. A hung tick is abandoned after
30 seconds and the band is marked **stale** (unknown, not "all clear"). The module is shown as a card on the
situation wall, a band chip on the map and the city pulse on Home.

### 4.6 City signal plans and their guards

- A deterministic band → plan table shifts only the green split toward the priority phase — AMBER 6 % (cross-street
  green floor 18 s), RED 12 % (14 s), BLACK 18 % (10 s); GREEN keeps the baseline. Cycle lengths and offsets are
  never changed, and no cross phase drops below its floor.
- The writer is **off by default**, every apply is operator-triggered by a named officer, every plan is
  shadow-evaluated on the twin **before** the write and fails closed, the first write per junction snapshots the
  prior program, and **Restore / Restore all** rebuild it.
- **The twin counts as field-calibrated only with at least 24 distinct field hours of real data and a replay error
  of at most 5 km/h.** A fresh install has none, so every non-baseline plan and every signal write is refused with
  "twin not calibrated: no field observations — simulated feed only". That refusal is the designed posture and is
  shown, not hidden. An apply while the city band is unknown is refused rather than silently treated as GREEN.
- No field signal controller is connected today.

### 4.7 The digital twin

A seeded Monte-Carlo simulation of the road network (a 23-scenario library) used for adaptive shadow-evaluation,
scenario comparison, decision-support wargames and calibration replay. Its outputs are model outputs and are
labelled as such wherever they appear (for example, route times in the planner are marked "Simulated traffic").

### 4.8 The stolen-vehicle enforcement chain

The second mission family rides the same city backbone. Every step is a real API on the running stack:

1. **FIR → lawful-basis earmark.** The plate is put on the watchlist with an enumerated lawful basis
   (`stolen_vehicle_fir`), a reason naming the FIR, and a server-computed retention (hard cap 90 days). Earmark
   create and clear need a named officer.
2. **Camera reads (emulated ANPR).** Reads arrive through the ANPR ingest seam; every row is born
   `source = emulated_anpr`. The `live_anpr` label is reserved for a real vendor adapter behind the `AnprSource` port
   and is refused until one is deliberately enabled. The server, not the emulator, computes the watchlist hit.
3. **Evidence, never a fine.** Deterministic rules (segment speed, signal violation, closed-corridor entry) file
   PENDING rows only — no code path creates an approved row. Because the car is reported stolen, each read instead
   becomes one evidence-only **stolen-vehicle sighting**, with the penal rules it would have fired recorded as
   withheld. Approving any e-challan on that plate is refused: **409 "e-challan withheld — vehicle reported stolen"**.
4. **A named officer approves the sighting** on Decide or the situation wall; the decision is appended to an
   append-only audit tail.
5. **Pursuit.** A separate step opens a pursuit event; it is accepted only with an active earmark and an approved
   sighting of that vehicle. A pursuit based on an e-challan of a stolen car is refused (422), and **one approval
   authorises one pursuit** (a second pursuit from the same approval is refused, 422). The system never opens a
   pursuit on its own.
6. **Interception plan.** pgRouting ranks choke junctions ahead of the latest sighting (driving-distance over the
   live road graph, scored by choke weight and graph cost).
7. **Live trace** on the map, with numbered camera hops and masked plates.
8. **Units to the chokes** through the dispatch channel (§4.9), each dispatch approved by a named officer.

On the map, pins read what they are: `STOLEN · NO FINE` with its state, `WITHHELD · STOLEN` for a pending penal row
of a stolen vehicle, and `SUPERSEDED · STOLEN` for an e-challan approved before the rule existed — kept as audit
history, never a pursuit basis. A single camera read is shown only when its vehicle holds an active earmark or the
read is evidence for a recommendation; anything else is a count-free "not found". A named officer can also look up
any complete registration mark; every such lookup is audited with the masked mark only.

Ordinary e-challan recommendations (for vehicles that are not reported stolen) follow the same rule: PENDING until a
named officer approves or rejects them.

### 4.9 Multi-agency dispatch and the 108 green corridor

- **Dispatch channel.** A closed registry of five agencies — **Jan Rakshak** (first-class), police, traffic, 108
  ambulance and fire. A dispatch moves request → officer approve/defer → en route → on scene → completed, every
  transition one append-only audit row. Closing an event walks its open dispatches to a final state, so no unit is
  left "on scene". There is no agency CAD or radio integration; the unit that moves on the map is an emulated
  projection of the record.
- **108 green corridor.** A driver files a request on `/driver` (anonymous, ambulance-only, rate-limited per
  client). It lands in the duty officer's queue with its event, stretch and waypoint junction and never approves
  itself. When a named officer approves it, the window opens 60–180 seconds before the ambulance reaches the
  junction (the event's advance closure, with its source shown) and the driver's page shows "approved — opens in N
  s", then "open — closes in N s".
- **Golden-hour framing.** Veer counts and reports *minutes returned* to the golden hour; it makes no claim about
  outcomes for patients.

### 4.10 OSINT event intelligence — places and situations, never persons

Off by default (`VEER_OSINT=0`). When enabled, the `osint-ingress` service reads public sources on a schedule and
the oracle fuses them into **situations at places** — a road, a junction, a neighbourhood, a district.

| Connector | Cadence | Source |
|---|---|---|
| `sachet_cap` | 5 min | NDMA SACHET CAP alerts for Gujarat (official) |
| `google_news_rss` | 10 min | Google News RSS search (a pointer layer, never redistributed) |
| `gdelt_events`, `gdelt_doc` | 15 min | GDELT 2.1 event export and DOC 2.0 article list |
| `reddit_rss` | 15 min | the city subreddit's public feed (aggregate social signal only) |
| `amc_scrape`, `gsdma` | hourly | official pages, best effort; a robots.txt disallow disables the connector |
| `common_crawl` | on demand | backfill only |

- **Modes.** `live` fetches from an allow-list of exact hosts over HTTPS (redirects checked hop by hop); `offline`
  (for a venue with no internet) and any failed live fetch parse the newest cached capture and label the signals
  `cached-sample`. Cache retention: 72 hours or 200 MB.
- **Redaction.** Names, ages, contacts and URLs in text are replaced at parse (`[PERSON]`, `[AGE]`, `[CONTACT]`,
  `[URL]`); a Gujarati or Devanagari word that is neither a known place nor an ordinary word is withheld as
  `[WITHHELD]`. There is no named-entity model, so the honest measure is held-out recall on a corpus written blind
  and never tuned on: Latin-script names **0.882**, Indic-script names **1.0**, age markers **0.895**, ordinary words
  kept **0.987**. A cue-less name or an all-caps headline can survive; the oracle's ingest guard refuses any signal
  on which the shared patterns still fire.
- **Never stored:** news and social URLs (only the outlet's domain and a hash), poster blocks, GDELT actor columns,
  court-record portals.
- **Geo-resolution** (`osint-geo`) is offline and deterministic: an ODbL gazetteer of Ahmedabad places with
  transliteration and Gujarati/Hindi spellings, snapped onto the real network. A neighbourhood stays area-level with
  no road anchor; a landmark keeps a road segment only within 900 m. Ambiguous names count only when the text is
  about Ahmedabad.
- **Analysis** (`osint-analysis`): classify (never into a crime-incident or pursuit class), fuse nearby similar
  reports, correlate related classes, score credibility (syndicated copies count as one source; a single social
  source is capped at 0.30; a district alert attached to a street-level report is context, never corroboration),
  attach to a compatible live corridor event, and flag second-order effects (a protected corridor, a convoy, an
  ambulance route, an existing closure nearby). A situation never surfaces from one social post or one community.
- **Labels**: `OFFICIAL-VERIFIED`, `NEWS-REPORTED`, `UNVERIFIED-OSINT`, or `SIMULATED` for the developer-written
  sandbox capture.
- **Human gate.** A surfaced situation becomes a corridor event only when a named officer promotes it.

### 4.11 Decision support

For an event, the decision-support engine proposes a small, distinct set of courses of action built only from
Veer's real actuators:

- **Baseline** — monitor only;
- **Minimal** — a driver and citizen advisory (draft only);
- **Standard** — advisory, a 108 dispatch when the situation calls for one, one responder dispatch and an emergency
  signal-priority hold;
- **Aggressive** — closure, diversion and the dispatches;
- **Information** — one patrol to verify, a situation check by the city's ICCC (no identification) and a short hold.

The options are ranked with AHP weights, a lexical veto and TOPSIS over nine criteria (public-safety risk reduction,
speed of effect, resource cost, public traffic disruption, cascade risk, reversibility, affected population,
protocol compliance, legality), with a sensitivity check; each option is wargamed on the digital twin and a cascade
model, or on a seeded surrogate when those do not answer. Two criteria are labelled for what they are: the
public-safety figure is a **fixed prior by the option's actions, not a simulated outcome**, and speed of effect is a
**nominal time per option kind, not a unit's ETA**. Every actuating action requires an officer; no option can target
a person. An area-level report (no road anchor) can only be met with monitor, advisory or verify.

A named officer approves, rejects or defers (refused with 409 without one), logged append-only. **An approval writes
no field action**: it creates dispatch requests, each then decided on its own. On Decide the options appear as cards
with "Why this one" in plain sentences; the full analysis stays in Analyst.

### 4.12 The AI: two tiers on the edge, grounded in code

All models run locally on the Veer server; no cloud model and no internet connection sit in the decision path.

| Tier | Component | Role |
|---|---|---|
| Strategic | **pplx-decider-v1-27b** (BF16) on the model host | Owns strategy and tool selection, asked typed questions (choice, probability, score); every answer is a distribution with a confidence |
| Tactical | **Gemma 4 12B** (Q4_K_M, shown as `gemma4-12b-veer`) on llama-server | Drafts tool arguments against each tool's schema (one repair round), composes chat answers |
| Numeric | forecaster ladder, ETA, OR-Tools, pgRouting | The deterministic tools the decider chooses among |
| Adaptive | the situation engine (§4.5) | Bands and protocol-floored parameters |
| Memory | **pplx-embed-v2-late-0.6b** + **bge-m3** embeddings | "Similar past situations" retrieval over incidents and scenario runs |

- **Fallback chain:** decider → Gemma → deterministic heuristics; no tier failure stops a convoy. If the decider's
  95th-percentile latency exceeds 3 s, the brain drops to tactical-only mode and alerts the operator; the console
  shows "Both AI tiers", "Tactical only" or "Rules only".
- **Confidence floor 0.45:** a lower-confidence answer becomes a draft plus an operator alert, not an action.
- **Novelty latch:** a confident answer to a situation unlike anything in memory is withheld and audited.
- **Tier-0 cache:** a routine checkpoint that closely matches a recent one is answered without a new 27B call.
- **Grounding validator** (`convoy_brain/grounding.py`): every drafted argument must come from the operator's words,
  the session or an earlier tool result; road names are resolved against the network ("no road segment named X");
  every sentence of an answer is checked against the tool results, and a sentence naming an unreported road,
  figure, time, vehicle position or unit ETA is removed — the answer says so and the operator is alerted. When every
  lookup about a subject comes back empty, the answer is "not in the city picture".
- **The assistant's tools** (29, over MCP) are read-only city lookups, compute calls and six canvas verbs (fly to,
  track, highlight, annotate, sensor, layer). A canvas move is a suggestion the operator applies or dismisses — never
  auto-applied, and the answer is audited. No tool name may approve, decide, earmark, dispatch, withdraw or
  transition.

### 4.13 The audit trail

Every consequential act is recorded with its actor:

- every AI answer and every fallback, with its probability distribution and confidence, in the movement's decision
  log;
- every situation observation and every published adaptive parameter, with the reason it changed;
- every corridor-event status change, creation included, with the named officer;
- every enforcement recommendation's decision (append-only audit tail), every dispatch transition, every
  decision-support decision, every signal-plan write and restore, every full-mark lookup (masked), every canvas
  directive acknowledgement;
- a **degradation ledger** that groups recurring causes of degraded or failed decisions, each tied to a real audit
  row.

The officer's identity is forwarded by the deck from the verified session on every write; the back-end services
accept it only from the deck on the loopback interface. An unattended script's approval carries the script's own
label (for example "Scripted demo officer (showcase script)"), never a person's name. Audit rows are shown in Analyst
(the Audit dock and the situation wall's stream, with "Ask why") and on each object page's Record tab — not on the
operational screens.

### 4.14 Multilingual advisories

The same facts reach four audiences in three languages (§3.8). The citizen and driver pages are trilingual, the
driver page Gujarati first. An advisory draft run on exercise data carries the exercise marker inside the copied
text, so a rehearsal message can never be mistaken for a real one.

### 4.15 The event emulator and the living city

Veer has no live feeds for traffic, cameras, units or GPS in this build, so the **event emulator** supplies
*causes* — never outcomes — through the real services' real APIs: procession schedules, marathon waves, weather
onset, incidents, green-corridor requests, convoy departures, emulated ANPR reads and patrolling unit positions.
The real stack then plans, classifies, escalates and decides on its own.

- **Ten runnable use cases**: the eight corridor classes, the flagship composite and the stolen-vehicle camera
  sweep. Runs are deterministic (same inputs, byte-identical tapes), can be stopped, and can be replayed on the map;
  a tape recorded on a road network that no longer exists is refused rather than re-animated.
- **Labels on every row**: emulated events are badged EMULATED on every surface, including the citizen page;
  synthetic traffic is never labelled real and never published on the live subject; every generated plate carries
  an `EM` series marker.
- **The living city** (off by default): a deterministic day program with two or three overlapping emulated causes,
  two Jan Rakshak beats, cameras reading passing traffic, a 108 green-corridor request about every 25 minutes that
  only a named duty officer can approve, and rare deliberate violators whose reads become PENDING recommendations.
  The bring-up refuses to switch it on unless the public feed labels emulated events.

### 4.16 The God's-eye city in photoreal 3D

- **Two honest modes.** Signed-in operators on a server that holds a Cesium ion key see photoreal 3D Ahmedabad
  (Google Photorealistic 3D Tiles, Cesium World Terrain, Bing aerial imagery). The key is handed only to a valid
  operator session; anonymous visitors and public pages get the keyless OpenStreetMap globe with zero calls to the
  3D providers.
- **Overlays stand on the city**: road flow, event routes (the recommended corridor glowing, alternates dashed),
  pursuit traces and interception fans, dispatch arrows, the convoy, cameras, signal rings, units and anomalies are
  draped on the terrain and the 3D tiles or clamped at street level so no building hides them; every layer reports a
  drape audit, and the recorded live check found every overlay layer with 0 floating entities (2026-10-24).
- **Eleven integrity-validated layers**: corridor events, traffic flow, vehicle traces, enforcement, signal
  network, agency units, dispatch, convoy, cameras, anomalies and photoreal 3D. Every layer fetches from fixed
  same-origin endpoints; an undeployed back end shows an honest "not deployed" chip, never a silent blank.
- **An honest imagery chip** names what is on screen (`PHOTOREAL 3D · GOOGLE`, `OSM · DARK`, `OSM · DARK ·
  FALLBACK` with the reason). Transient 3D-tile failures are retried; a refusal falls back at once. Provider credits
  are always on screen.
- **Thermal-style sensor modes** (white-hot, black-hot) are a visual filter, labelled as such. **Share links**
  restore the exact camera, sensor and layer set. A **City Command** view frames live action obliquely at −42°.
- **Satellite thumbnails** on Home, Decide and object pages draw Bing aerial tiles without a 3D viewer per card,
  under a quota guard (at most 6 tiles per card, 4 in flight, a 192-tile shared cache, 800 requests per tab
  session, and a stand-down on the first 401/403/429), falling back silently to the night map.

### 4.17 The operator gate, attribution and masking

- **Sign-in.** With `VEER_OPERATOR_PIN` set (the intended setting for any deployment reachable from a network), an
  officer signs in with their name and the duty PIN. The session is an HttpOnly, SameSite=Strict cookie signed with
  `VEER_SESSION_SECRET`, valid 12 hours; sign-out revokes it server-side. Failed PINs are throttled (8 per 5 minutes
  per client), comparisons are constant-time, and officer names refuse control and bidirectional characters.
- **Default deny.** Without a session every proxied API call is refused (403), except the public road geometry,
  three liveness probes and the 108 driver's ambulance request.
- **Attribution.** The deck forwards the signed-in officer as the actor of every write and strips any client-supplied
  copy. Services also require a named officer for earmarks, signal applies and restores, and escort start, stop and
  clear (otherwise 422).
- **Gate off.** On a console where the gate is deliberately off (a closed room, development), naming a duty officer
  is attribution only — it unmasks plates and enables decisions on that console. The bring-up's status check reports
  a network-exposed deck without the gate as DEGRADED.
- **Content-security policy** per document: operator pages admit only what the 3D city needs; public pages keep a
  strict policy and never receive the map key.

### 4.18 Privacy and retention

| Data | Rule |
|---|---|
| Camera reads of a vehicle with no active watchlist entry | Kept 30 days, then purged in the read path |
| Camera reads of a watchlisted vehicle | Kept for the longer of 30 days and the entry's retention (cap 90 days) |
| Reads that are evidence for a decided recommendation | Kept with the decision as its evidence and audit |
| Full-mark lookup audit | Who, when, the **masked** mark, found or not; kept 90 days; the raw mark is never stored or logged |
| OSINT cache | 72 hours or 200 MB; directory mode 0700 |
| News and social URLs | Never stored, logged or shown |
| Saved views, watches, CSV exports, share links | Always masked, whatever the officer state |
| Protected-movement identities and destinations | Never logged; the route stays off the public feed until inside the 2-hour horizon |
| Secrets (PIN, session secret, map key) | Only in a mode-600 host environment file, read at run time, never printed or committed |

### 4.19 Offline and degraded operation

- The decision path needs no internet: models, database, routing and the twin all run on the server. Only map
  imagery comes from the internet; when it fails, the canvas draws Veer's own roads and entities and says so.
- OSINT has an `offline` mode that reads cached captures, labelled `cached-sample`.
- Each AI tier degrades to the next and says so; a stale band is shown as unknown; a feed that stops answering is
  named with the time it stopped ("Decisions still work").
- A separate **offline fallback demo** (the legacy React dashboard in `VVIP/frontend/`) runs a clearly labelled
  scripted simulation on any laptop with no back end and no GPU.

### 4.20 Capability summary

| Capability | What it does | Who uses it | Status |
|---|---|---|---|
| Movement planning | Routes, security validation, closure plans | Duty officer | Real engine; traffic inputs simulated |
| Rolling holds & escort | 60–180 s advance closures, proposals, officer approval, timeout → hold | Duty officer, escort | Real engine; convoy GPS emulated |
| Corridor event library | 8 event classes + enforcement on one model | Control room | Real engine; scenarios emulated |
| Road network | 49 segments, 34 junctions on OSM | Everyone | **Real** (OpenStreetMap) |
| Traffic feed | Live congestion per road | Everyone | **Simulated** (synthetic, labelled) |
| Forecasting | T+5/10/15/30 min | Planner, AI | Real third-party model on simulated history; DSTGAT architecture only |
| AMA bands | GREEN/AMBER/RED/BLACK with floors and hysteresis | Control room | Real engine |
| City signal plans | Band-driven green-split plans | Supervisor | Real, gated; refuses to write until the twin is field-calibrated; no field controller connected |
| Stolen-vehicle chain | Earmark → reads → evidence → approval → pursuit → interception | Investigating & duty officer | Real rules and audit; **ANPR reads emulated** |
| E-challan support | Rule-based recommendations, officer decides | Traffic officer | Real rules; reads emulated |
| Dispatch | Five-agency request lifecycle | Duty officer | Real records; **units emulated**, no CAD link |
| 108 green corridor | Driver request → officer approval → timed window | 108 driver, duty officer | Real flow; scripted fallback when no live event |
| OSINT situations | Public sources → redacted place situations | Analyst, duty officer | Real when enabled (live sources); sandbox capture SIMULATED |
| Decision support | Ranked courses of action | Duty officer | Real engine; twin/surrogate outputs modelled |
| Assistant | Grounded answers, proposals as cards | Officers | Real, local models |
| Advisories | EN/HI/GU drafts for four audiences | Communications officer | Real drafts; **not delivered** (no gateway) |
| God's-eye 3D | Shared photoreal city with overlays | Everyone (operators) | Real imagery (not live); overlays real or labelled |
| Audit trail | Append-only records of every decision | Supervisors, auditors | Real |
| Operator gate | PIN sign-in, attribution, masking | Operators | Real |

---

# Part B — Engineering

## 5. Architecture

### 5.1 Topology

```
                     Browser (operator console · /citizen · /driver)
                                     │  HTTP :5273  (the only LAN-facing port)
                   ┌─────────────────▼──────────────────────────────┐
                   │ command-deck  Svelte 5 · CesiumJS · MapLibre    │  operator gate · per-document CSP
                   │               deck.gl · same-origin proxy       │  public projection for public pages
                   └───────┬──────────────────┬──────────────────┬───┘
            /api/v1, /api/traffic      /api/convoy        /api/emulator     (loopback only; the signed-in
                           │                  │                  │           officer forwarded as the actor)
              ┌────────────▼───────┐  ┌───────▼────────┐  ┌──────▼─────────┐
              │ traffic-oracle     │◄─┤ convoy-brain   │  │ event-emulator │  causes only,
              │ FastAPI · ML ·     │  │ decider+Gemma  │  │ every row      │  never outcomes
              │ routing · AMA ·    │  │ grounding · MCP│  │ labelled       │
              │ enforcement · OSINT│  └──┬────┬────┬───┘  └──────┬─────────┘
              │ store · DSS · twin │     │    │    │             │ (real APIs, NATS .emulated)
              └──┬──────┬──────┬───┘     │    │    └─► embedding-service (memory)
                 │      │      │         │    └──────► llama-server (Gemma 4 12B)
                 │      │      │         └───────────► model-host (pplx-decider-v1-27b)
                 │      │      └─► Valkey  (live cache · adaptive params · convoy context)
                 │      └────────► PostGIS + pgRouting + pgvector  (corridor-store, migrations 001–025)
                 └◄─── NATS ◄──── signal-ingress (Rust · Arrow IPC · synthetic feed, labelled)

   osint-ingress (optional, VEER_OSINT=1) ── redacted signals ──► traffic-oracle /api/v1/osint/signals
```

### 5.2 Services (`VVIP/services/`)

| Service | Language / stack | Responsibility |
|---|---|---|
| `command-deck` | TypeScript, SvelteKit 2 + Svelte 5 (runes), adapter-node, CesiumJS 1.146 (vendored), MapLibre GL 5, deck.gl 9 | The interface for every audience; operator PIN gate and session; same-origin loopback proxy; per-document CSP; public projections (`/api/public/*`); map-key handout to signed-in operators only |
| `traffic-oracle` | Python 3.12, FastAPI | Traffic ingest, forecasting ladder, routing (OR-Tools, pgRouting), diversions, the adaptive layer (AMA), the digital twin, city fusion (entities, feed, dossiers, cameras), corridor-event lifecycle and route updates, watchlist and enforcement, dispatch, city signal plans, OSINT situation store, decision support, degradation ledger |
| `convoy-brain` | Python 3.12, FastAPI | Two-tier orchestration (decider → Gemma → heuristics), pre-movement / live-escort / post-clearance workflows, escort proposals and approvals, chat and streaming chat, the grounding validator, the MCP server (29 tools, 4 resources, 3 prompts) |
| `event-emulator` | Python 3.12, FastAPI | Cause-only injection of the use-case library through real APIs; runs ledger, stop, replay; the living city |
| `signal-ingress` | Rust 2024, tokio, Arrow, async-nats | Four traffic feed adapters, inline Tier-1 plausibility checks, Arrow IPC publishing to NATS |
| `corridor-store` | SQL (PostgreSQL 16, PostGIS, pgRouting, pgvector, pg_trgm) | Migrations 001–025, the real-road seed, the OSM importer |
| `embedding-service` | Python | Multi-vector (MaxSim) + dense retrieval for "similar past situations" |
| `model-host` | Python | Serves the strategic decider as typed questions |
| `osint-common` | Python | Shared OSINT types, vocabulary and ethics checks |
| `osint-ingress` | Python | Connectors, scheduler, cache, redaction, posting to the oracle |
| `osint-geo` | Python | Offline gazetteer resolver onto the real network |
| `osint-analysis` | Python | Classification, fusion, correlation, credibility, attachment, second-order effects |

The legacy React dashboard (`VVIP/frontend/`) is the offline fallback demo only, not a service.

### 5.3 Data stores

- **PostGIS** (corridor-store) — schemas `corridor` (road segments, junctions, adjacency and the routing graph view,
  cameras, agency stations, signal programs and their history, the vehicle watchlist, sightings, dispatches, the
  lookup audit), `traffic` (range-partitioned observations, real and synthetic hourly aggregates kept apart, the
  anomaly log, memory documents and embeddings), `convoy` (movements, planned routes, diversions), `events` (corridor
  events, routes with supersession, phases, profiles, status log, enforcement recommendations), `emulator`,
  `adaptive`, `simulation`, `osint` (raw signals already redacted, gazetteer, resolved events, sources) and
  `decision` (courses of action, simulation runs, the append-only decision log). Migrations 001–006 are
  checksum-immutable; 007–025 are idempotent, schema-only and additive (025 deliberately drops a reversible hash).
- **Valkey** — the latest observation per segment (the live plane and the emulated plane in separate key spaces),
  forecasts, corridor summaries, adaptive parameters and the `situation:changed` signal, convoy context with the
  decision log, emulated unit frames.
- **NATS JetStream** — `corridor.traffic.live` (Arrow), `corridor.traffic.anomaly`, `corridor.traffic.emulated`
  (never `.live`), `corridor.units.emulated`.
- **DuckDB** — historical-pattern queries in the oracle.

### 5.4 Model hosts and memory

The model hosts run outside Docker as systemd user units (`veer-decider`, `veer-llama`, `veer-embed`) bound to
loopback, resident for the life of the process, restarted on exit. Target hardware is an NVIDIA GB10-class edge
server with a 121.6 GiB unified-memory pool. The planned budget is about 82 GiB (decider 55, Gemma 9.5, embeddings
5, platform services about 12), leaving about 40 GiB of headroom; the measured resident model stack was 62.73 GiB
(bench of 2026-10-13). The decider is never called per GPS tick, its questions are batched into one forward pass,
and its state documents are capped (1,500 tokens pre-movement, 400 per event, 8,192 hard).

### 5.5 How data flows

1. **Traffic**: signal-ingress publishes labelled synthetic batches on NATS → the oracle decodes them, writes
   observations to PostGIS and the newest row per segment to Valkey, and logs anomaly flags.
2. **Causes**: the event emulator creates corridor events through the lifecycle API, writes situation input
   documents to Valkey with a provenance sidecar, posts emulated ANPR reads to the sightings API, publishes emulated
   unit frames and traffic on their own NATS subjects, and makes one twin call per run.
3. **Adaptation**: the oracle's engine loop (every 5 s) classifies each active subject, applies hysteresis and
   floors, shadow-evaluates deviations on the twin, persists and mirrors parameters to Valkey, and publishes
   `situation:changed` on a band change.
4. **Decisions**: a band change, incident, threshold crossing, phase change or operator question wakes the brain;
   the decider picks a tool, Gemma drafts its arguments, the oracle computes, the grounding validator checks the
   answer, and anything that would change a plan becomes a proposal.
5. **Officers**: the deck polls the oracle and brain through its proxy; an officer's action is sent with the
   verified officer as actor; the service validates it (409/422 refusals are shown verbatim) and writes the audit
   row.
6. **OSINT**: osint-ingress fetches, redacts and posts signals → the oracle resolves, fuses and stores situations →
   an officer promotes one to a corridor event → decision support proposes courses of action → an officer decides →
   dispatch requests wait for their own decisions.
7. **Public**: the deck's server builds a public projection of events and dispatch status; `/citizen` and `/driver`
   read only that.

### 5.6 Network exposure and ports

Every service except the deck binds loopback; the deck is the only LAN-facing service and reaches the others
through its loopback-pinned proxy (which refuses protocol-relative paths, so it cannot become an open relay).
Outbound URLs are fixed configuration constants; no user-supplied URL is ever fetched.

| Component | Default bind |
|---|---|
| command-deck | `0.0.0.0:5273` |
| event-emulator · traffic-oracle · convoy-brain · osint-ingress (optional) | `127.0.0.1:8090` · `:8091` · `:8092` · `:8093` |
| model-host (decider) · llama-server (Gemma) · embedding-service | `127.0.0.1:8083` · `:8084` · `:8085` |
| PostGIS · Valkey · NATS | `127.0.0.1:56434` · `:6380` · `:4223` |

Container images run as non-root users (uids 10001–10006, one per service) with digest-pinned Python and Bun bases
and a frozen lockfile for the deck build.

### 5.7 Repository layout

```
README.md                    the repository front page
PRODUCT.md                   this document
PROBLEM_STATEMENT_GUJARAT.md the problem, beneficiaries and sources
VVIP/
  README.md                  platform overview and quick start
  TECHNICAL_DOCS.md          architecture, APIs, schemas, gates, records (sections 1–18)
  IMPACT_REPORT.md           the deterministic impact model and its assumptions ledger
  docs/USE_CASES.md          the event-class library
  docs/GODS_EYE_INTEGRATION.md  the 3D canvas, emulated/real split, ethics rails
  docs/ACTIVE_MOVEMENT_ADAPTATION.md  the AMA module
  services/                  the services of §5.2
  infra/                     compose files, Dockerfiles, systemd units, Prometheus/Grafana
  scripts/                   bring-up, migrations, network generators, gates, showcase, impact model
  shared/                    protocol parameters, protobuf and Arrow schemas
  models-config/             model-stack configuration (weights are supplied by the operator, never committed)
  tests/adversarial/         the adversarial scenario suite
  frontend/                  the offline fallback demo
```

### 5.8 Bring-up and boot

`VVIP/scripts/veer_up.sh` is the one idempotent bring-up, in a fixed order so no service ever starts against an
older schema: preflight → model units → (with `--build`, the service images; never the database image unless
`--rebuild-postgis`) → PostGIS alone, healthy → migrations → seed (empty store only) and the real-road network step
→ every service → a one-time restart of the services that cache the network if it changed → converge → a readiness
table (11 rows, 12 with OSINT) ending `READY 11/11`. `--status` prints the table read-only; `--install-units` writes
the host environment (mode 600) and enables the systemd units; secrets are entered with `scripts/veer_env.sh --set
KEY -` on standard input, never on a command line. At boot, `veer.target` starts the model units and the bring-up
unit; this was verified by real reboots on 2026-10-23 (`READY 11/11` in 4 min 25 s with no manual command).

### 5.9 Configuration (selected)

| Setting | Default | Effect |
|---|---|---|
| `VEER_OPERATOR_PIN`, `VEER_SESSION_SECRET` | set for a gated deck | The operator gate and session signing |
| `VEER_CESIUM_ION_TOKEN` | optional | Photoreal 3D and satellite imagery for signed-in operators; empty = keyless everywhere |
| `VVIP_REQUIRE_OFFICER` | 1 | Officer actions without a named officer are refused (422) |
| `VVIP_ESCORT_APPROVAL_TIMEOUT_SEC` | 90 (15–600) | How long an escort proposal waits before the plan is held |
| `VVIP_CONFIDENCE_FLOOR` | 0.45 | The decider confidence gate |
| `VVIP_SIGNAL_POLICY_WRITER` | off | The city signal-plan writer (every apply still needs a calibrated twin) |
| `VVIP_ACCEPT_LIVE_ANPR` | unset | `live_anpr` reads are refused until a real vendor adapter exists |
| `VEER_OSINT`, `OSINT_MODE` | 0, `live` | OSINT ingress on/off; `offline` for no-internet venues |
| `EMULATOR_LIVING_CITY` | 0 | The ambient living city |
| `DECIDER_TIER0_DISABLE` | unset | Kill switch for the tier-0 cache |

Model endpoints come from `VVIP/models-config/configs/veer_models.yaml` (overridable by environment); protocol floors
and scoring weights from `VVIP/shared/schemas/protocol_params.json`, generated into both Python services and checked
for drift.

### 5.10 Observability

Prometheus metrics from the model host, llama-server, the brain (per-tier token and latency, per-tool calls and
errors, endpoint latency) and the oracle (inference, pgRouting and pgvector latency, pool gauges, anomaly counts);
23 alert rules in 8 groups (`VVIP/infra/observability/alerts.yml`) and a provisioned Grafana overview dashboard. The readiness table and
the degradation ledger are operator-facing.

### 5.11 Testing and quality gates

Kinds of gate (details in [`VVIP/TECHNICAL_DOCS.md`](VVIP/TECHNICAL_DOCS.md) §13 and §18.6):

- **Per-service unit and integration suites**, each run whole (a test needing an absent database or library skips
  itself and is counted): pytest for every Python service and OSINT package, `cargo test` for signal-ingress.
- **Deck tests**: unit scripts (`*.unit.mjs`) for the shell, Home, Decide, object pages, map and map style, planner,
  advisories, public pages and the root reroute; recorded-payload contract tests; design-token parity (both
  themes, colour discipline, module boundaries); a copy lint over the English interface strings (title length,
  separators, no stray all-caps); route JavaScript size ceilings; `svelte-check`.
- **Hermetic browser smokes**: every GET stubbed and every non-GET and third-party request aborted, over each V3
  screen; SwiftShader canvas and screen cameras that prove key elements and non-blank pixels.
- **Generators with verify modes**: the OSM network, the ingress segment table, display geometry, the OSINT
  gazetteer, protocol parameters.
- **Wave tiers**: the forecaster support hatch, the novelty latch, the foundation forecaster on its real artifact,
  P90-robust routing, the tier-0 cache, the repetition-gate self-test and the degradation ledger.
- **A docs-consistency oracle** that checks documented figures against the tree and the recorded artifacts.
- **Live tiers** (on demand, one operator sign-in, GET-only reads): the deck's gate behaviour, model smoke tests, a
  model-drift panel, an adversarial scenario bench, operator journeys (J1–J7), the flagship showcase, a
  consistency-under-repetition gate, and a leak check of every log for secrets.

Recorded results (dated, from the committed docs):

| What | Result | Date |
|---|---|---|
| pytest tests collected across all suites | 5,119 | 2026-10-26 |
| Last whole-suite runs | traffic-oracle 2,064 passed / 104 skipped; convoy-brain 742 / 1; event-emulator 318 / 13; osint-common 444; osint-ingress 381 / 1; osint-geo 390; osint-analysis 360 | 2026-10-26 |
| signal-ingress `cargo test --locked` | 120 passed | 2026-10-24 (re-run 2026-10-26) |
| Live acceptance on the deployed stack | 19 of 22 steps green first time; the three failures (tier-0 cache keying, two canvas smokes on leftover test data) fixed and re-run green | 2026-10-23/24 |
| Flagship showcase ("God's Eye Morning") | SHOWCASE PASS three times; no fine anywhere in the stolen-vehicle chain | 2026-10-23/24 |
| Operator journeys J1–J6 | 92 / 92 checks | 2026-10-24 |
| Screen camera on the live deck | 40 / 40 (pre-V3 interface) | 2026-10-24 |
| Boot auto-start | READY 11/11 in 4 min 25 s, no manual command | 2026-10-23 |
| Adversarial scenario bench | 19 / 19 scenarios under the 60 s line; decider 455.78 tok/s (p99 1,106.8 ms), Gemma 20.09 tok/s, embeddings 92.7 ms, 62.73 GiB resident | 2026-10-13 |

The live acceptance records predate the V3 interface. The V3 screens are covered by their own unit tests and hermetic
browser smokes (TECHNICAL_DOCS §18.6), with mutation testing recorded per work package; the committed documentation
does not quote a pass count for the merged V3 tree, so none is quoted here.

---

## 6. Honest status

### 6.1 Real, emulated, simulated, modelled

| Real | Emulated or simulated (labelled on every surface) | Modelled (labelled as model output) |
|---|---|---|
| The road network (OpenStreetMap geometry, names, junctions) | The traffic feed — every observation synthetic | Route times and twin outputs |
| Every decision, band change, escalation and refusal the stack makes | ANPR camera reads (`emulated_anpr`) and the 28 camera sites | Decision-support wargames (twin, cascade or seeded surrogate) |
| The audit trail and officer attribution | Agency units and their movement (`emulated_dispatch_projection`, `emulated_patrol`) | The impact figures (§6.2) |
| The local AI models and their answers | Convoy GPS during an escort (`emulated_gps`) | The public-safety criterion (a fixed prior) |
| The rules: 409 no-fine, 422 pursuit basis, one approval one pursuit, timeout → hold | Corridor events opened by the event emulator; the demo stolen vehicle, its plate and FIR | Forecasts (third-party model on simulated history) |
| Public OSINT sources, when enabled (official alerts, news) | The OSINT sandbox capture (`SIMULATED`) | |
| Map imagery (real, but not live) | The living city and every scripted rehearsal | |

The emulator supplies causes only. Every outcome reported anywhere is the real stack responding to those causes.

### 6.2 Modelled impact

From the deterministic impact model (`VVIP/scripts/impact_run.py`, generated 2026-10-23; full report
[`VVIP/IMPACT_REPORT.md`](VVIP/IMPACT_REPORT.md); numbers in `VVIP/scripts/impact_results.json`). **These are model
outputs on the platform's real-road network under a stated, falsifiable assumptions ledger — not field
measurements.**

| Figure (central case unless stated) | Blanket freeze (25 min/junction) | Rolling hold (2.5 min/junction) |
|---|---|---|
| Commuter-minutes per frozen junction | ≈ 33,291 | ≈ 333 |
| Commuter-minutes per movement, whole network frozen (upper-bound framing) | 1,131,888 | 11,319 |
| Vehicles caught in holds per movement | 60,367 | 6,037 |

- **Reduction in junction-freeze commuter delay: 100× central**, 25× conservative (15 → 3 min, fewer arrivals),
  506× optimistic (45 → 2 min). The mechanism is structural: delay grows with the square of the hold length.
- **Per year** (250 movement-days, an assumption): about 4.67 million commuter-hours returned, 2.52 million litres of
  idle fuel and about 6,303 tonnes of CO₂ avoided.
- **108 ambulances** (12 trips per movement-day assumed to cross a corridor; 11 minutes returned per crossing): about
  132 golden-hour minutes per movement-day, about 33,000 per year — **minutes returned to the golden hour, not a
  claim about patient outcomes**.

### 6.3 Known limitations and leftovers

Interface (V3):
- The tablet layout is not built: the rail stays on the left at every width (also below 1280 px), and the tablet
  bottom-sheet "Now" list does not exist.
- The alerts bell is not fed on the Analyst pages (`/analyst`, `/ops`, `/gods-eye`, `/chat`); waiting decisions
  still show there on the rail's Decide badge, the Inbox chip and the live strip.
- The `#evt=`, `#rec=` and `#dsp=` deep-link redirects on `/` are not done (they still work on `/ops`).
- The Analyst Assistant tab (`/chat`) still shows the brain's raw alert codes; the V3 Assistant turns them into one
  plain caution.
- The old navigation bar component is still on disk (pinned by tests), not drawn.
- Route JavaScript is held under ceilings that stop regressions, but the original first-load budget of the redesign
  is not met (TECHNICAL_DOCS §17.7).

Data and integrations:
- No live traffic, ANPR, GPS or agency feed is connected; all are emulated or synthetic and labelled.
- No agency CAD or radio integration and no message gateway: dispatches are approved records, advisories are drafts.
- No field signal controller; the signal writer refuses every write until the twin is field-calibrated (≥ 24 field
  hours, replay error ≤ 5 km/h), which a fresh install cannot be.
- Every Z+ plan on the current network is conditional (no route meets the six-lane floor end to end).
- Ahmedabad only; no multi-city network.
- No usability testing with working control-room operators yet; the design rests on expert review.

Models:
- The DSTGAT forecaster ships as architecture only (no trained weights); the ETA regressor is untrained (its endpoint
  answers with a labelled fallback); the Isolation Forest anomaly detector exists as code but is not wired in.
- Tracked quality gaps on the adversarial bench: tool_validity 0.684 and keyword_coverage 0.561 (both pass the gate;
  the decider often answers after one tool where a scenario expects two).
- OSINT redaction has no named-entity model; recall figures and failure cases are in §4.10. The embedding service
  has no `/embed` route yet, so OSINT fusion uses lexical similarity.

Environment and build:
- One Cesium ion CDN edge refuses TLS from the current host; a session that resolves to it loses aerial imagery
  (honest fallback note) while the 3D tiles retry.
- signal-ingress's Rust base images are not digest-pinned, and the plain x86 Dockerfiles of the oracle and brain
  still run as root (the deployed arm64 images are non-root).

### 6.4 Roadmap

Each item below has a seam already in the code:

- **Real ANPR** behind the `AnprSource` port (`live_anpr` reserved, `VVIP_ACCEPT_LIVE_ANPR`), and registration of the
  state's ICCC / CCTV / ITMS camera inventory (`corridor.cameras.source = registered`).
- **Field traffic data** into the real hourly aggregates → twin calibration → the signal writer and adaptive
  deviations become possible; a field signal-controller adapter.
- **Trained forecasters**: an exported DSTGAT model at the configured path; a trained ETA regressor.
- **Agency integrations** for dispatch and a **message gateway** for advisories, both behind officer approval.
- **Interface**: the tablet layout and bottom sheet, the `/` deep-link redirects, the alerts bell on Analyst pages,
  and plain cautions on `/chat`.
- **OSINT**: Indic-script named-entity redaction; an embedding route for semantic fusion.
- **More cities**: the network generator and gazetteer are data-driven and re-checkable.

---

## 7. Getting started

Setup is documented once, in the repository's own guides; this document does not duplicate it.

- Start with the front page: [`README.md`](README.md).
- Platform overview and quick start: [`VVIP/README.md`](VVIP/README.md) ("Getting Started").
- Full reference — services, APIs, schemas, bring-up, configuration and gates:
  [`VVIP/TECHNICAL_DOCS.md`](VVIP/TECHNICAL_DOCS.md) (bring-up in §11, testing in §13, the V3 interface in §18).
- Event classes and the honesty contract: [`VVIP/docs/USE_CASES.md`](VVIP/docs/USE_CASES.md).
- The 3D canvas and the ethics rails: [`VVIP/docs/GODS_EYE_INTEGRATION.md`](VVIP/docs/GODS_EYE_INTEGRATION.md).
- The adaptation module: [`VVIP/docs/ACTIVE_MOVEMENT_ADAPTATION.md`](VVIP/docs/ACTIVE_MOVEMENT_ADAPTATION.md).

In short: the full stack needs a GB10-class server (121 GiB unified memory) with Docker Compose v2; the model
weights, the duty PIN, the session secret and the optional Cesium ion key are supplied by the operator and never
committed; `bash VVIP/scripts/veer_up.sh` brings everything up and `--status` reports readiness; the console is
then at `http://127.0.0.1:5273`. Without a GPU, `VVIP/frontend` runs the labelled offline fallback demo on any
laptop.

---

## 8. Licence and attributions

- Code: MIT — [`VVIP/LICENSE`](VVIP/LICENSE).
- Road network: © OpenStreetMap contributors, ODbL 1.0 —
  [`VVIP/services/corridor-store/seed/NOTICE.md`](VVIP/services/corridor-store/seed/NOTICE.md).
- 3D city and imagery: Google Photorealistic 3D Tiles, Cesium World Terrain and Bing aerial imagery through Cesium
  ion, credited on screen; the thermal-style shader port and other canvas notices —
  [`VVIP/services/command-deck/src/lib/gods-eye/NOTICE.md`](VVIP/services/command-deck/src/lib/gods-eye/NOTICE.md).
- Foundation forecaster t0-alpha: a third-party model under Apache-2.0, never committed; `VVIP/scripts/fetch_t0.sh`
  fetches it and verifies its sha256 before the oracle image is built.
- OSINT gazetteer: derived from OpenStreetMap, ODbL 1.0.
- Reference photographs of Ahmedabad's places: Wikimedia Commons, each under its own licence (CC0, public domain,
  CC BY or CC BY-SA — not MIT), credited on screen and listed in
  [`VVIP/services/command-deck/static/photos/NOTICE.md`](VVIP/services/command-deck/static/photos/NOTICE.md).
- Agency and data-source marks belong to their owners; Veer is a prototype and is not affiliated with or endorsed by
  them — [`VVIP/services/command-deck/static/logos/NOTICE.md`](VVIP/services/command-deck/static/logos/NOTICE.md).
- Vehicle shots, event key art and the Ahmedabad scenes are original artwork generated by a script in this project.

---

## 9. Glossary

| Term | Meaning |
|---|---|
| **Band** | The situation class of a subject or the whole city: GREEN, AMBER, RED or BLACK |
| **Corridor event** | A planned operation that takes control of part of the road network for a window (a movement, procession, race, evacuation, pursuit …) |
| **Course of action (COA)** | One option proposed by decision support, built from Veer's real actuators |
| **Decider** | The strategic AI model; it answers typed questions and picks tools, never chats |
| **Earmark** | A watchlist entry for a vehicle, with a lawful basis and a retention limit |
| **E-challan** | A penalty recommendation from a deterministic rule; PENDING until an officer decides |
| **Emulated** | Produced by Veer's event emulator to stand in for a feed that is not connected |
| **Grounding validator** | Code that removes any AI sentence or argument not supported by tool results |
| **Interception plan** | Junctions ranked by pgRouting ahead of a stolen vehicle's latest sighting |
| **Plan B** | The pre-sanitised alternate route of a movement, proposed for officer approval |
| **Rolling hold** | A closure activated shortly before a convoy reaches a segment and released as it passes |
| **Shadow-evaluation** | Running a proposed change on the digital twin before it may be applied |
| **Sighting** | One camera read of a watchlisted vehicle; for a stolen vehicle, evidence only |
| **Simulated** | Synthetic data (the traffic feed, the OSINT sandbox) or a model's output |
| **Twin** | The seeded traffic simulation of the city network |
| **URN** | A record identifier such as `event:<id>` or `junction:15`; never a registration mark |
