# VVIP → HSC Idea Submission — Enhancement Plan & Runbook

> Follows §3 of the Submission Playbook. Base repo reviewed in
> `DEEP_REVIEW_VVIP.md`. Deadline: **idea submission closes 15 Oct 2026**;
> resubmission allowed until the deadline → ship early, improve later.

## ✅ Status (updated 11 Oct 2026 — end of build session)

| Item | State | Evidence |
|---|---|---|
| P0.1 LICENSE | **Done** | `VVIP/LICENSE` (MIT) |
| P0.2 Judge demo path | **Done** | README “Run the Demo in 3 Minutes” + public-surfaces section |
| P0.3 State problem statement | **Done** | `PROBLEM_STATEMENT_GUJARAT.md` (personas, 5-gap analysis, citations) |
| P0.4 Deck | **Done (md → export pending)** | `submission/DECK.md`, 7 slides incl. AI-usage disclosure |
| P0.5 Video | Script done; recording is human work | `submission/DEMO_VIDEO_SCRIPT.md` |
| P1.1 Citizen Advisory Layer | **Done + E2E-verified** | `frontend/src/views/CitizenAdvisory.jsx`, `src/i18n/advisoryStrings.js` (EN/HI/GU) |
| P1.2 Ambulance Green-Corridor mode | **Done + E2E-verified** | `frontend/src/views/GreenCorridor.jsx` (driver flow → proposal → approve → live window) |
| P1.3 Measured impact | **Done, regenerable** | `VVIP/IMPACT_REPORT.md` + `scripts/impact_run.py` (deterministic, honesty contract; conservative 25×) |
| E2E test (repo) | **Done, passing** | `frontend/tests/e2e/` — console → citizen → driver → approved window, no backend |
| Screenshots | **Done** | `screenshots-submission/` (4 shots) |
| Annexure 1 | Template done; signing is human work | `submission/ANNEXURE1_TEMPLATE.md` |

Remaining human-side items: team registration on MyBharat, record the
3–5 min video, export deck to ≤10 MB PDF as
`<State>_<TeamName>_<Document>.pdf`, upload before 15 Oct.

---

## 1. Theme lock

- **Primary theme: Governance & Civic Technology.** The problem is state
  capacity: five agencies coordinating convoy disruption by phone/radio.
- **Secondary theme: Disaster Mitigation & Large Gatherings.** Same corridor
  engine generalizes to yatras, marathons, summits, Kumbh-scale movements.
- "AI, GIS & Emerging Technologies" is our *means*, not our cause.
- SDG alignment: **11** (sustainable cities), **3** (health — golden hour),
  **16** (effective, accountable institutions).

## 2. The pivot: same engine, new protagonist

Today the repo tells an *operator's* story about an *elite* movement. HSC
scores **Social Cause Impact** — so the submission tells the *public's* story
about the *city's* frozen hour.

**Positioning line (deck slide 1):**
> "When a protected convoy passes, an Indian city holds its breath. We built
> the intelligence that lets it exhale — corridors managed to the second, not
> frozen for half an hour."

**Narrative device — invert the acronym:** the platform's real Very Important
Persons are the **V**oter on the bus, the **V**ictim in the 108 ambulance, and
the **V**ulnerable patient for whom ten minutes matter. (Use once, with
restraint; credibility over gimmick.)

**Generalization claim (one engine, three corridors):**
1. Protected-movement corridors (VVIP convoys — original use case)
2. **Emergency green corridors** — on-demand passage for 108 ambulances
3. **Event corridors** — processions, marathons, summits, Kumbh-scale gatherings

## 3. Enhancements, ranked by judging-criteria leverage

### P0 — submission blockers (Day 1)

| # | Item | Why | Effort |
|---|---|---|---|
| P0.1 | Add `LICENSE` (MIT) to repo root | HSC hard requirement; today missing | 5 min |
| P0.2 | Judge path: one README section "Run the demo in 3 minutes" — choose the **React demo UI** (self-simulating, no GPU needed) as the canonical demo; mark `command-deck/` as experimental in its README; fix the `/chat/stream` vs `/chat` drift or route around it in demo mode | *Functionality* is judged fast; must not dead-end | 2–3 h |
| P0.3 | `PROBLEM_STATEMENT_<State>.md`: state-specific problem, named beneficiaries, **gap analysis** with citations (Mumbai Sept-2022 ambulance hold; Kanchipuram 2018 death; Agartala Feb-2026 hold; Smart Cities/MoRTH ITS context). Default state = **Gujarat** (seed data is Ahmedabad); swap if team is elsewhere | Required artifact | 2 h |
| P0.4 | Deck, 6–7 slides, ≤10 MB, incl. **AI-usage disclosure** (AI coding assistants used for prototype development — keep a usage log from now) | Required artifact | 4 h |
| P0.5 | Demo video script + recording, 3–5 min, ≥720p (use the self-driving demo; narrate honestly: "operator console driven by a scripted live-feed simulation") | Preferred-but-weighted | 3 h |

### P1 — score multipliers (Days 2–3)

| # | Item | Criterion hit | Effort |
|---|---|---|---|
| P1.1 | **Citizen Advisory Layer** (new thin service + public page): "Corridor Alerts" — planned/active closures as a lightweight multilingual web widget (EN/HI/GU) + WhatsApp/SMS alert opt-in (stub transport with clearly-labeled mock, offline fallback). One screen: *map of the corridor, "this stretch freezes in ~12 min for ~3 min, here is your alternate"* | **Social Cause Impact** (W1) — gives the beneficiary a face and a touchpoint | 1 day |
| P1.2 | **Ambulance Green-Corridor mode**: promote the existing emergency-request bell to a first-class flow — a simple mobile-view "108 driver" page (request passage → AI evaluates convoy gap → corridor window opens → duty-officer approve/defer), plus a minutes-saved counter | **Social Cause Impact + Functionality** (W2); the emotional core of the video | 1 day |
| P1.3 | **Measured impact run**: execute `evaluate/scenario_sim.py` + adversarial runner against the Ahmedabad seed; publish `IMPACT_REPORT.md` — baseline (manual 25-min blanket stop) vs platform (rolling 2–3-min closures): commuter-minutes saved, queue length, ambulance delay, fuel/CO₂ delta | **Technical Strength + credibility** (W4); replaces the unverified "6×" | 0.5–1 day |

### P2 — if runway allows (Days 3–4)

- **Event-corridor preset** (procession/marathon config + one narrative slide → secondary theme lock).
- Hindi/Gujarati strings on operator surfaces; accessibility labels.
- "Who runs it" section: pilot via a Smart City SPV / city traffic police; BOM = one edge laptop; data partnerships (city ITS feeds, 108/EMRI dispatch).
- Privacy principle slide: VVIP identity/destination never logged; decisions carry chain-of-thought audit trails → *accountable institutions* (SDG 16) framing.

## 4. Impact math skeleton (fill from the P1.3 run + citations)

- **Population:** commuters on the pilot corridor's arterials at peak hour
  (from seed network capacity); 108 ambulance trips/day crossing the corridor
  (state EMRI figures — to verify for chosen state).
- **Unit math (illustrative until measured):** one Z+ movement, 12 km, N
  junctions: baseline freeze = 25 min × junctions × vehicles/min arrival;
  platform = rolling 2–3 min × junctions. Output: commuter-minutes per
  movement; × movements/year (RTI-able figure for the state) → annual hours
  returned to the city.
- **Health:** golden-hour literature for cardiac/trauma survival vs 10–20 min
  ambulance delay — cite conservatively, never claim lives saved outright;
  claim *minutes returned to the golden hour*.

## 5. Rubric → evidence mapping (for the deck's benefit)

| Criterion | Evidence we will show |
|---|---|
| Relevance | State PS + cited incidents; Smart Cities/MoRTH ITS alignment |
| Technical Strength | 5-service edge architecture; DSTGAT; PostGIS/pgRouting; auditable agents; adversarial suite |
| Functionality | 3-min one-command demo; ambulance flow end-to-end |
| Creativity | Inversion of the problem (secure the movement *and* free the city); corridor OS generalization |
| Social Cause Impact | Citizen advisory layer; ambulance mode; **measured** commuter-minutes & ambulance-minutes |
| Presentation & Teamwork | Deck discipline; honest AI-usage disclosure; division of labour slide |

## 6. Runway (11 → 15 Oct)

- **Day 1 (Oct 11–12):** P0.1–P0.3 complete; start P1.1; team eligibility
  confirmed and registered on MyBharat portal (blocker — see risks).
- **Day 2 (Oct 12–13):** P1.2 + P1.3; draft deck.
- **Day 3 (Oct 13–14):** P0.4 deck final; P0.5 video record + edit; README
  polish; push public repo.
- **Day 4 (Oct 14–15):** Buffer. **Submit early on Oct 14**; resubmit improved
  build on Oct 15 if needed. Annexure-1 package signed and scanned.

## 7. Risk register

| Risk | Mitigation |
|---|---|
| Team eligibility (18–29, AICTE/AISHE-enrolled, ≤3) | **Confirm human-side facts immediately** — no code fixes this |
| Heavy stack fails on judges' machines | Demo video is the primary functional evidence; repo carries the one-command lite demo |
| Overclaiming ("6×") | Measured IMPACT_REPORT or softened language; never state unverified multiples |
| Simulated-data honesty | Video + deck disclose simulation explicitly; AI-usage disclosure included |
| Two-frontend confusion | Canonical demo path documented; other marked experimental |
| Security sensitivity | Keep the repo's data-minimization posture; no real movement data, no real identities |

## 8. Immediate next actions (this session's queue)

1. P0.1 LICENSE + P0.2 judge-path README (quick, unblocks repo).
2. P1.1 Citizen Advisory Layer scaffold (public alerts page + alert feed
   consumed from the same ConvoyContext simulation so the demo stays one
   story).
3. P1.2 Ambulance driver page wired to the existing approve/defer flow.
4. P1.3 Impact run harness script (`scripts/impact_run.py`) producing
   IMPACT_REPORT.md from seed + scenario sim.
