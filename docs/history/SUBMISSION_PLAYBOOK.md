# Veer — Hack for Social Cause (VBYLD 2027) Submission Playbook

> Staged 11 Oct 2026. The base repo ("Veer") has not been placed in this folder yet —
> this playbook captures everything that does not depend on it, so the deep review and
> idea submission can be produced immediately once the code arrives.

## 1. The competition (verified from mybharat.gov.in)

**Hack for Social Cause (HSC) — Youth Tech Challenge**, under the Viksit Bharat Young
Leaders Dialogue (VBYLD) 2027. Organized by the Department of Youth Affairs / MoYAS with
**IIT Bombay (GISE Hub & SJM School of Management)** as National Knowledge Partner.
Motto: *"Think Global, Hack Local – Technology for Social Transformation."* Aligned with
Viksit Bharat 2047 and UN SDGs.

### Timeline — ⚠ the clock that matters
| Window | Stage |
|---|---|
| **1 Sep – 15 Oct 2026** | **Registration & idea submission (CLOSES IN DAYS)** |
| 16 Oct – 30 Nov 2026 | State-level hackathons (3 winners per State/UT) |
| 1 – 15 Dec 2026 | IIT Bombay screening → 36 national finalists |
| 16 Dec 2026 – 9 Jan 2027 | Virtual mentoring by IIT Bombay |
| 10 – 12 Jan 2027 | National showcase, New Delhi (VBYLD 2027) |

### Eligibility & teams
- Indian citizens, **18–29 years** as of 17 Aug 2026, enrolled in an AICTE/AISHE institution.
- **Up to 3 students** (individuals allowed; interdisciplinary encouraged — a female member
  and a non-tech/social-science member preferred). One team per student. One Team Lead submits.
- 2026 national finalists/winners are ineligible for HSC 2027.

### The 11 themes (indicative; adaptable to local issues)
Rural Development & Livelihoods · Education & Skill Development · Healthcare & Service
Delivery · Governance & Civic Technology · Environment & Sustainability · Digital
Inclusion · AI, GIS & Emerging Technologies · Digital Safety & Cyber Fraud Awareness ·
Elderly Care & Healthy Ageing · Assistive Technology & Accessibility · Disaster
Mitigation (incl. large gatherings such as Kumbh Mela).

### What must be submitted
1. **Deck: 6–7 slides** (PPT/PDF, ≤10 MB) — problem, solution, impact, team, **disclosure
   of AI tool usage**.
2. **Demo video: 3–5 min**, MP4/MOV, ≥720p, ≤80 MB (preferred, not mandatory).
3. **Public GitHub/GitLab repo** — full open-source code under MIT/Apache-2.0/GPL,
   with README, architecture docs, sample data.
4. **Annexure 1** — team details, self-certification, self-attested student IDs.
5. File naming: `<State>_<TeamName>_<Document Name>.pdf`. Resubmission allowed until deadline.

### Evaluation criteria
Relevance · Technical Strength · **Functionality (working prototype)** · Creativity ·
**Social Cause Impact** · Presentation & Teamwork. *Working demos are valued over theory.*

### Prizes
₹75k / ₹50k / ₹25k / ₹15k×2; ₹6k prototype grant for all 36 finalists; certificates,
incubation linkages, media coverage. Teams keep IP; organizers get a non-exclusive
display license.

## 2. Deep-review protocol for the base repo (run this the moment the code lands)

The goal: understand **the problem the repo solves in reality** — not what its README
claims, but what it actually does, for whom, and where it falls short of a social-cause
winner.

1. **Inventory** — tree, languages, frameworks, entry points, tests, CI, license, size/complexity.
2. **Stated intent** — README/docs/issues: what problem does it *claim* to solve, for whom?
3. **Actual behaviour** — trace the main flow through the code; run it if runnable; list
   what genuinely works vs. stub/demo/aspirational.
4. **Reality gap** — who really has this problem in India (evidence: scheme data, census,
   NFHS, news, court/RTI reports)? Is the repo's mechanism plausible for that population —
   connectivity, device, language, literacy, cost, trust?
5. **User fit** — name the concrete beneficiary persona (e.g. "a rural ASHA worker on a
   ₹8k Android phone with intermittent 2G, Hindi/State-language only").
6. **Failure/weakness map** — scalability, offline behaviour, privacy, data sourcing,
   accessibility, cost per user, deployment/maintenance story.
7. **Verdict** — one paragraph: what this repo *is*, in reality, today.

## 3. Enhancement framework: base repo → HSC winner

Map every planned enhancement onto the **judging criteria** and the **theme** it serves;
cut anything that serves neither.

- **Theme lock.** Pick exactly one primary theme (of the 11) + one secondary; every slide
  and feature must ladder up to it. "AI/GIS & Emerging Tech" is a *means*, not a social
  cause — the primary theme should be the social domain.
- **Bharat fit.** Indic-language UI + speech where relevant; offline-first/low-bandwidth;
  Android-first; data-light; works on cheap devices; DPI rails (Aadhaar-adjacent care,
  UPI, ONDC/OCEN/BCSBI only if genuinely load-bearing).
- **Working demo beats theory.** Prefer one end-to-end flow that demonstrably runs over
  five half-built features. Record it honestly for the 3–5 min video.
- **Impact math.** Quantify: affected population (with a citable source), unit cost,
  time saved, coverage target for one district → scale to State → national.
  Judges score *Social Cause Impact* — give them numbers with provenance.
- **Replicability & sustainability.** Who runs it after the hackathon (a society, a
  panchayat, an NGO, a district administration)? Open-source repo already satisfies the
  mandate — keep README + architecture doc + sample data submission-ready.
- **Honesty on AI usage.** The deck must disclose AI tool usage; keep a usage log from day one.

## 4. Submission checklist (final gate before upload)

- [ ] Team ≤3, all eligible, one Team Lead, registered on MyBharat portal
- [ ] Deck 6–7 slides, ≤10 MB, includes AI-usage disclosure, named `<State>_<TeamName>_…pdf`
- [ ] Demo video 3–5 min, ≥720p, ≤80 MB (preferred)
- [ ] Public repo with LICENSE (MIT/Apache-2.0/GPL), README, architecture doc, sample data
- [ ] Annexure 1 with self-certification + self-attested student IDs
- [ ] Submitted before **15 Oct 2026** (resubmission allowed until the deadline)

## 5. Status (updated 11 Oct 2026)

**Base repo placed and deep-reviewed.** The submission builds on
[`VVIP`](https://github.com/shubro18202758/VVIP) (cloned to `./VVIP/`) — an
edge-AI convoy corridor-orchestration platform (DSTGAT traffic forecasting,
Rust/Arrow/NATS ingestion, PostGIS/pgRouting graph, auditable LLM agents).
Deep review: [`DEEP_REVIEW_VVIP.md`](DEEP_REVIEW_VVIP.md). Pivot and runbook:
[`ENHANCEMENT_PLAN.md`](ENHANCEMENT_PLAN.md).

- Theme lock: **Governance & Civic Technology** (primary) · Disaster
  Mitigation & Large Gatherings (secondary).
- Narrative pivot: same engine, protagonist = the commuter and the 108
  ambulance patient, not the protected person.
- P0 hygiene already applied locally: `LICENSE` added (was missing →
  disqualifier), README gains a 3-minute no-backend demo path with a
  simulation-honesty note.
- Remaining open blocker: **human-side facts** — team of ≤3 eligible members
  (18–29, AICTE/AISHE-enrolled) must register on the MyBharat portal and sign
  Annexure 1. Code cannot fix this; confirm before Oct 15.
