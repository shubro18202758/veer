# Problem Statement — Gujarat (Ahmedabad–Gandhinagar Corridor)

> Working artifact for the HSC idea submission (feeds deck slides 1–2).
> State: **Gujarat** · Pilot geography: the Ahmedabad–Gandhinagar corridor and
> Ahmedabad's arterial core (Ashram Road, SG Highway, CG Road, Riverfront
> Road, SP Ring Road, Gandhinagar Highway — the exact network seeded in the
> prototype). Team: Veer · Theme: Governance & Civic Technology.

## 1. The problem, stated plainly

When a protected person (VVIP) or a ceremonial movement travels by road in
Gujarat, traffic along the corridor is brought to a complete stop well before
the convoy arrives — routinely 15 to 45 minutes at each major junction. The
passage itself occupies a junction for seconds; the freeze around it consumes
the better part of an hour of a city's traffic capacity. Coordination happens
by phone, radio and WhatsApp across at least five separate hierarchies —
traffic police, district administration, SPG/state security, municipal signal
teams, and 108 ambulance dispatch — none of whom share a live operational
picture. Routes are chosen by precedent rather than by data, closures are
timed by rough margins rather than by prediction, and the public has no way to
learn about a closure before arriving at the barricade.

This is not a Gujarat-specific invention of ours; it is the national operating
default, and Gujarat's capital region experiences it acutely because the
Ahmedabad–Gandhinagar corridor (~25 km, airport ↔ city core ↔ state capital)
hosts a heavy schedule of protected and ceremonial movements: the state's
senior leadership travels it continuously, and recurring global gatherings
(e.g., the Vibrant Gujarat Global Summit, held in Gandhinagar since 2003)
multiply movement days.

## 2. Evidence that the harm is real

**Commuter harm, including in Gujarat specifically:**
- "VIP movement halts city traffic" — Times of India, Ahmedabad (Oct 2009):
  protected-movement duty pulled traffic police off crossroads, disrupting
  flow city-wide. The pattern is two decades old in this exact city.
- The irony cuts both ways: in Ahmedabad (Oct 2022) the Gujarat Chief
  Minister's own convoy was stuck ~15 minutes in a junction breakdown
  (Vibes of India) — even the protected movement suffers from the absence of
  coordinated corridor management.
- The national pattern is harsher still: commuters stranded for hours behind
  VIP halts in 44 °C heat (Uttar Pradesh, viral 2023–24 reports); commuters
  on Pune's J.M. Road — an arterial connecting hospitals and government
  offices — stranded by a VVIP convoy, asking that police "experience the
  disruption first-hand" (Pune Mirror).

**Emergency-care harm — the acute end of the same failure:**
- Mumbai, Sept 2022: an ambulance with siren running was held 5–10 minutes
  while a Union Home Minister's convoy passed (Free Press Journal; the
  bystander video drew national attention).
- Kanchipuram, 2018: a heart-attack victim died after the ambulance was
  stuck ~20 minutes behind a bureaucratic convoy.
- Agartala, Feb 2026: an ambulance halted at Vidurakarta Chowk for a VIP
  movement — the pattern continues into this year.

**Scale of the emergency exposure in Gujarat:** the 108 ambulance service
(GVK EMRI) began in Gujarat with 14 ambulances on 29 Aug 2007 and grew to a
fleet of ~585 in the state; fleet-wide, EMRI ambulances average ~5 emergency
trips each per day across the ~800 million people the service covers. Every
convoy freeze on an arterial is a lottery ticket against one of those trips.

**The protocol itself is not the villain.** The MHA Blue Book — the
classified manual governing protected movements, which our prototype
encodes as working rules (Z+/Z/Y/X tiers, lane and closure requirements,
Advance Security Liaison checklists) — explicitly instructs that traffic be
*"regulated, not stopped"* unless unavoidable, that halts happen away from
junctions, and that arrangements persist only until flow normalises. The gap
is not the policy; it is that no tooling exists to *execute* the policy at
the precision it demands. Paper protocol, phone-and-radio coordination.

## 3. Gap analysis — five specific gaps, each mapped to our module

| # | Gap (what does not exist today) | Consequence | Our module that closes it |
|---|---|---|---|
| G1 | **No shared operational picture** across traffic police, district admin, security, municipal signals, 108 dispatch | 15–45 min blanket holds; mis-timed closures; radio chaos | Unified command console — all agencies on one live map (existing) |
| G2 | **No prediction in the loop** — closure timing set by fixed advance margins, not by traffic forecasting | Holds far longer than the convoy needs; cascading jams | DSTGAT forecaster (T+5/10/15/30) driving rolling 60–180 s closures (existing) |
| G3 | **No citizen advisory channel** — the commuter discovers the closure at the barricade | Kilometre-long queues feeding into frozen junctions; wage loss; rage at constables | **Citizen Advisory Layer (new)** — free multilingual corridor alerts: which stretch freezes, when, for how long, and the alternate |
| G4 | **No emergency-passage request channel** — a 108 driver has no way to request corridor access; the only "protocol" is a siren and luck | Golden-hour minutes burned at barricades; documented deaths | **Ambulance Green-Corridor mode (new)** — driver-side request → AI-evaluated corridor window → duty-officer approval |
| G5 | **No measurement or accountability** — disruption is never quantified; no after-action data reaches planners or the public | Nothing improves; the same over-caution every time | Post-clearance after-action reports + published impact metrics (existing + impact harness) |

## 4. Target beneficiaries (named, per HSC format)

| Persona | Who, concretely | What changes for them |
|---|---|---|
| **The stranded commuter** | Daily-wage worker on Ashram Road losing paid hours; office-goer on SG Highway; student on a BRTS-adjacent arterial | Freezes shrink from ~25 min to ~2–3 min rolling holds; advance alerts let them route around the corridor entirely |
| **The emergency patient** | Cardiac/trauma/stroke case in a 108 ambulance whose golden hour intersects a movement window | Corridor windows open on request; minutes returned to the golden hour |
| **The 108 ambulance driver** | EMRI crew member, ~5 emergency trips/day, currently powerless at a barricade | A one-tap passage request with a yes/no/hold answer in seconds |
| **The traffic constable** | Officer at the barricade executing a phone order given 30 minutes early | Precise per-segment activation/deactivation times instead of blanket orders; less public anger absorbed |
| **The duty officer / control room** | Traffic DCP or district cell running 5-agency coordination by phone and WhatsApp | One console, AI-scored routes with auditable reasoning, ambulance requests triaged |
| **The city administration** | Municipal corporation / Smart City SPV answering for congestion and grievances | Measured disruption per movement; after-action data; a path to protocol-compliant operations |

Primary social-cause face for the submission: **the commuter and the
emergency patient**. Adopters: **traffic police and district administration**.

## 5. Why now, and why this team's approach

- **Policy tailwind:** the system aligns with MoRTH ITS initiatives, Smart
  Cities Mission and PM Gati Shakti — and, decisively, with the Blue Book's
  own text. We are not asking anyone to break protocol; we are building the
  tool that finally *satisfies* it.
- **Technical feasibility is demonstrated, not promised:** the prototype
  already runs neural forecasting, graph routing, auditable agents and the
  command console on a single edge laptop — the form factor of a motorcade
  command vehicle. The two new citizen-facing surfaces (G3, G4) are thin
  layers over the same engine.
- **Honest scope:** security veto authority stays human (SPG/state police).
  The platform is decision support with a full audit trail — the only posture
  that can be adopted in the real world.

## 6. Sources

1. Times of India (Ahmedabad), Oct 2009 — "VIP movement halts city traffic".
2. Vibes of India, Oct 2022 — Gujarat CM's convoy stuck ~15 min in Ahmedabad.
3. Pune Mirror — "VVIP convoy holds up traffic on J.M. Road, commuters fume".
4. Free Press Journal, Sept 2022 — ambulance held 5–10 min during Union Home
   Minister's convoy, Mumbai (bystander video).
5. Kanchipuram, 2018 — heart-attack death after ~20 min ambulance hold behind
   a convoy (national press coverage).
6. Tripura press, Feb 2026 — ambulance halted for VIP movement, Agartala.
7. GVK EMRI / 108 Gujarat — service began 29 Aug 2007 with 14 ambulances,
   grew to ~585 in Gujarat; fleet-wide ~5 trips/ambulance/day; ~800 million
   people served (EMRI public materials, Stanford evaluation, PubMed).
8. MHA Blue Book protocol summary (as encoded in the prototype's security
   tiers and ASL checklists) — "traffic is regulated, not stopped".
