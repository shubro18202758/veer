#!/usr/bin/env python3
"""Render the HSC deck (Gujarat_Veer_Deck.pptx) from the impact run.

Run:  VVIP/.venvs/deck/bin/python submission/make_deck.py   (the python-pptx venv;
      VVIP/.venvs/ is gitignored — build it with `python3 -m venv VVIP/.venvs/deck &&
      VVIP/.venvs/deck/bin/pip install python-pptx`)
Reads VVIP/scripts/impact_results.json so every number on slide 5 comes from
the same source of truth as IMPACT_REPORT.md, and the slide images from
VVIP/showcase/. VEER_VVIP_ROOT points both at another checkout of VVIP (a
worktree under review); the default is the workspace's VVIP/. Team name:
"Veer" per PROBLEM_STATEMENT_GUJARAT.md §header ("Team: Veer") — rename the
outputs if the team registers a different name.
Convert to PDF and page images afterwards with:
  soffice --headless --convert-to pdf --outdir submission submission/Gujarat_Veer_Deck.pptx
  pdftoppm -png -r 80 submission/Gujarat_Veer_Deck.pdf submission/deck_pages/slide
"""
from __future__ import annotations

import json
import os
from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt

ROOT = Path(__file__).resolve().parent.parent
VVIP = Path(os.environ.get("VEER_VVIP_ROOT") or ROOT / "VVIP")
IMPACT = json.loads((VVIP / "scripts" / "impact_results.json").read_text())
OUT = Path(__file__).resolve().parent / "Gujarat_Veer_Deck.pptx"

NAVY = RGBColor(0x0F, 0x2A, 0x43)
SAFFRON = RGBColor(0xFF, 0x99, 0x33)
GREEN = RGBColor(0x0F, 0x7B, 0x4D)
INK = RGBColor(0x1B, 0x23, 0x30)
GRAY = RGBColor(0x5D, 0x6A, 0x7B)
LIGHT = RGBColor(0xC9, 0xD6, 0xE4)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
FONT = "Liberation Sans"  # metric-compatible with Arial on PowerPoint

W, H = Inches(13.333), Inches(7.5)
FOOTER = "Gujarat · Veer · Hack for Social Cause · VBYLD 2027"


def fmt(n):
    return f"{n:,.0f}"


def millions(n):
    return f"{n/1e6:.2f} million" if n >= 1e6 else fmt(n)


def solid_bg(slide, color):
    slide.background.fill.solid()
    slide.background.fill.fore_color.rgb = color


def rect(slide, x, y, w, h, color):
    from pptx.enum.shapes import MSO_SHAPE
    sh = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, x, y, w, h)
    sh.fill.solid()
    sh.fill.fore_color.rgb = color
    sh.line.fill.background()
    return sh


def textbox(slide, x, y, w, h):
    tb = slide.shapes.add_textbox(x, y, w, h)
    tb.text_frame.word_wrap = True
    return tb.text_frame


def set_par(par, text, size, color, bold=False, italic=False, align=PP_ALIGN.LEFT,
            space_after=6, level=0):
    par.alignment = align
    par.level = level
    par.space_after = Pt(space_after)
    runs = text if isinstance(text, list) else [(text, bold)]
    for t, b in runs:
        r = par.add_run()
        r.text = t
        r.font.size = Pt(size)
        r.font.color.rgb = color
        r.font.bold = b
        r.font.italic = italic
        r.font.name = FONT


def add_footer(slide, idx, dark=False):
    tf = textbox(slide, Inches(0.55), Inches(7.02), Inches(9.0), Inches(0.35))
    set_par(tf.paragraphs[0], FOOTER, 9, LIGHT if dark else GRAY)
    tf2 = textbox(slide, Inches(10.6), Inches(7.02), Inches(2.2), Inches(0.35))
    set_par(tf2.paragraphs[0], f"Slide {idx} / 7", 9, LIGHT if dark else GRAY,
            align=PP_ALIGN.RIGHT)


def title_block(slide, title, kicker=None):
    y = Inches(0.38)
    if kicker:
        tf = textbox(slide, Inches(0.55), y, Inches(12.2), Inches(0.3))
        set_par(tf.paragraphs[0], kicker.upper(), 11, SAFFRON, bold=True)
        y = Inches(0.66)
    tf = textbox(slide, Inches(0.55), y, Inches(12.2), Inches(0.75))
    set_par(tf.paragraphs[0], title, 25, NAVY, bold=True)
    rect(slide, Inches(0.58), y + Inches(0.62), Inches(1.5), Inches(0.045), SAFFRON)


def bullets(slide, items, x=Inches(0.55), y=Inches(1.6), w=Inches(12.2), h=Inches(5.2)):
    tf = textbox(slide, x, y, w, h)
    first = True
    for item in items:
        level, size, color, runs = item
        par = tf.paragraphs[0] if first else tf.add_paragraph()
        first = False
        set_par(par, runs, size, color, level=level, space_after=7)
    return tf


def b1(text_runs): return (0, 14, INK, text_runs)
def b2(text_runs): return (1, 12.5, GRAY, text_runs)
def b1_light(text_runs): return (0, 14, LIGHT, text_runs)
def b1s(text_runs): return (0, 12, INK, text_runs)  # compact, image-column slides


def build():
    prs = Presentation()
    prs.slide_width, prs.slide_height = W, H
    blank = prs.slide_layouts[6]

    c = IMPACT["scenarios"]["central"]
    cons = IMPACT["scenarios"]["conservative"]
    opt = IMPACT["scenarios"]["optimistic"]
    ann = IMPACT["annualization"]
    amb = IMPACT["ambulance"]
    net = IMPACT["network"]
    pj = IMPACT.get("per_junction_central") or {}
    fuel_l = (c["idle_liters_baseline"] - c["idle_liters_platform"]) * IMPACT_A
    co2_t = fuel_l * 2.5 / 1000

    # ── Slide 1 — the hook (dark) ─────────────────────────────────────
    s = prs.slides.add_slide(blank)
    solid_bg(s, NAVY)
    rect(s, Inches(0), Inches(0), Inches(0.18), H, SAFFRON)
    tf = textbox(s, Inches(0.75), Inches(0.9), Inches(11.9), Inches(1.9))
    set_par(tf.paragraphs[0],
            "When a corridor closes, an Indian city holds its breath.",
            30, WHITE, bold=True)
    tf = textbox(s, Inches(0.75), Inches(2.35), Inches(11.9), Inches(0.8))
    set_par(tf.paragraphs[0],
            "We built the intelligence that lets it exhale — corridors managed "
            "to the second, not frozen for half an hour. A city-scale platform on "
            "Ahmedabad's real roads, where VVIP routing is one component among many "
            "and a named officer decides every penalty, pursuit and route switch.",
            16, SAFFRON, italic=True)
    bullets(s, [
        b1_light("Today's default: a protected movement freezes corridors 15–45 minutes at every "
                 "junction, coordinated by phone, radio and WhatsApp across five separate agencies."),
        b1_light("The passage itself takes seconds per junction. The MHA Blue Book says traffic "
                 "must be “regulated, not stopped” — the gap is tooling, not policy. Documented "
                 "harm: ambulance held 5–10 min with siren running (Mumbai 2022); a death after a "
                 "~20-min hold (Kanchipuram 2018); another halt this February (Agartala 2026)."),
        b1_light("One failure mode, many costumes: the same freeze hits the Rath Yatra's 14 km "
                 "old-city loop (148 annual editions), Kumbh-class perimeters (240→660 million "
                 "visits, 2019→2025), a 24,000-runner marathon, Republic Day parade strips, "
                 "~130,000-person stadium egress, monsoon flood evacuation and metro work zones."),
        b1_light("Our answer is a city-scale Corridor OS — the VVIP run is the base case, not the "
                 "boundary (full library: VVIP/docs/USE_CASES.md) — and the same backbone carries "
                 "everyday enforcement: a stolen-vehicle FIR traced from watchlist to interception "
                 "plan, vehicles only, with a human in every penalty loop "
                 "(VVIP/docs/GODS_EYE_INTEGRATION.md)."),
    ], x=Inches(0.75), y=Inches(3.3), w=Inches(11.9), h=Inches(3.4))
    add_footer(s, 1, dark=True)

    # ── Slide 2 — the gap ─────────────────────────────────────────────
    s = prs.slides.add_slide(blank)
    title_block(s, "The gap, precisely — Gujarat (Ahmedabad–Gandhinagar)",
                "Problem statement")
    bullets(s, [
        b1([("Pilot geography: ", True), (f"Ahmedabad's real road network, traced on OpenStreetMap — "
            f"{net['segments']} segments, {net['junctions']} junctions, ~{net['total_km']:.0f} km: "
            "Ashram Road, SG Highway, CG Road, SP Ring Road, the Gandhinagar Highway, the old-city "
            "bazaar belt (© OpenStreetMap contributors, ODbL 1.0).", False)]),
        b2("G1  No shared operational picture across the 5 agencies  →  15–45-minute blanket holds"),
        b2("G2  No prediction in the loop (fixed advance margins)  →  holds far longer than the convoy needs"),
        b2("G3  No citizen advisory channel  →  the commuter discovers the closure at the barricade"),
        b2("G4  No emergency-passage channel for 108  →  golden-hour minutes burn; documented deaths"),
        b2("G5  No measurement or accountability  →  nothing improves; over-caution every time"),
        b1([("Beneficiaries, named: ", True), ("the commuter on Ashram Road; the cardiac patient in a "
            "108 ambulance (Gujarat: ~585 EMRI ambulances, ~5 emergency trips each daily); the "
            "constable at the barricade; the duty officer with zero tooling — and, through the "
            "use-case library, the pilgrim, the runner, the spectator and the flood evacuee.", False)]),
    ])
    add_footer(s, 2)

    # ── Slide 3 — the platform ────────────────────────────────────────
    s = prs.slides.add_slide(blank)
    title_block(s, "The platform — a city-scale OS, the public's protagonist",
                "Solution")
    bullets(s, [
        b1s([("Our Very Important Persons: ", True), ("the Voter on the bus, the Victim in the "
            "108 ambulance, and the Vulnerable patient for whom ten minutes matter.", False)]),
        b1s([("One interface, simple by default, deep on demand — 127.0.0.1:5273: ", True),
            ("Home (what needs you now), Map, Decide (one decision at a time, \u201cwhat changes "
            "if you approve\u201d), Plan, Assistant and Advisories on one rail; the full analyst "
            "workspace, situation wall and 3D city under Analyst; public /citizen + /driver in "
            "EN/HI/GU. Real place photos, agency marks and artwork; every approval carries a "
            "named officer.", False)]),
        b1s([("The God's-eye — real 3D Ahmedabad: ", True), ("signed-in operators see Google "
            "Photorealistic 3D Tiles with the overlays draped on the city, none floating — the "
            "simulated congestion feed on the real roads, spines, the pursuit fan, units, cameras; "
            "public pages stay keyless. Eleven integrity-validated layers.", False)]),
        b1s([("The officer approves every switch: ", True), ("during a live escort the AI only "
            "proposes a re-route, Plan B, a hold or closures; a named officer approves each — "
            "no answer in 90 s and the current plan holds. The AI never switches a route on its "
            "own.", False)]),
        b1s([("Enforcement on the same rails: ", True), ("FIR → lawful-basis earmark → emulated "
            "ANPR reads → evidence-only sighting, never a fine on a stolen car's owner (409) → "
            "a named officer approves → pursuit (one approval, one pursuit) → pgRouting "
            "interception plan. Vehicles only — no faces, no persons; plates masked unless an "
            "officer is signed in.", False)]),
        b1s([("Predictive rolling holds, two-tier AI, AMA: ", True), ("closures 60–180 s ahead, "
            "~2–3-minute holds instead of 25-minute freezes; a 27B decider + Gemma 4 12B at the "
            "edge, every answer logged with its confidence; plans fail closed to protocol "
            "floors. In the flagship the engine chose signal hold at 45 s — “regulated, not "
            "stopped.”", False)]),
    ], x=Inches(0.55), y=Inches(1.5), w=Inches(8.55), h=Inches(5.35))
    # The interface, live (V3, 2026-10-27): Home — the one decision that needs
    # an officer now over the real map of its place — and the public citizen
    # page (keyless, EN/HI/GU). 1440x900 → w3.95/h2.47.
    v3 = VVIP / "showcase"
    if (v3 / "showcase_v3_home.png").exists() and (v3 / "showcase_v3_citizen.png").exists():
        s.shapes.add_picture(str(v3 / "showcase_v3_home.png"),
                             Inches(9.25), Inches(1.55), width=Inches(3.95))
        s.shapes.add_picture(str(v3 / "showcase_v3_citizen.png"),
                             Inches(9.25), Inches(4.12), width=Inches(3.95))
        tf = textbox(s, Inches(9.1), Inches(6.66), Inches(4.25), Inches(0.4))
        set_par(tf.paragraphs[0],
                "Live stack, 2026-10-27 — Home · the public citizen page",
                8, GRAY, italic=True, align=PP_ALIGN.CENTER)
    add_footer(s, 3)

    # ── Slide 4 — working now (with screenshots) ───────────────────────
    s = prs.slides.add_slide(blank)
    title_block(s, "Working now — one honest interface, live stack, measured",
                "Functionality")
    bullets(s, [
        b1s([("Live on the box: ", True),
            ("scripts/veer_up.sh brings the stack up and it starts itself at boot — real reboots "
            "came back READY in 4 min 25 s, no manual command. The V3 interface went live on "
            "2026-10-27 (READY 12/12 with OSINT on, migrations 001–025, operator gate on): / is "
            "Home, Decide holds one decision at a time, Analyst keeps the workspace and the "
            "situation wall.", False)]),
        b1s([("Deployed, then accepted live (2026-10-23/24): ", True),
            ("19 of 22 acceptance steps passed first time; the tier-0 cache miss was fixed (route "
            "options named by their own segments, answers filed per movement), redeployed and "
            "re-run green — 1 hit in 3, 1825 ms saved; two canvas smokes' failed checks re-ran "
            "green once the reset cleared acceptance debris; the judge's journeys passed 92/92.",
            False)]),
        b1s([("Flagship “God's Eye Morning” (SHOWCASE PASS three times that night; artifacts "
              "2026-10-24 00:01 IST): ", True),
            ("Rath Yatra + monsoon + one 108 ambulance + a stolen-vehicle report, injected "
            "through the emulator into the live stack: 31 audited decisions; a 12-replication twin "
            "of the scenario's 4 scripted green-corridor windows (ambulance delay 231.92 s, model "
            "output); 6 emulated ANPR reads at 95–115 km/h → R_STOLEN_SIGHTING ×6, evidence only — "
            "e-challan withheld, an e-challan approval on the plate refused (409) → the sighting "
            "approved under the honest label “Scripted demo officer (showcase script)” (in the "
            "judged demo, a signed-in human) → 10 choke junctions ranked by pgRouting (top: "
            "junction 15, unsignalised, score 0.008683) + a live 12-position trace (its 24 h window "
            "also holds an earlier run's reads); the signal guard refused the uncalibrated commit "
            "(409 — no field observations).", False)]),
        b1s([("Emulated/real split, plainly: ", True), ("the roads are real; the traffic feed, "
            "ANPR reads, camera sites and units are emulated or simulated and labelled so on "
            "every surface; every decision is the real stack's, every approval carries the "
            "officer's name — a signed-in human in the judged demo.", False)]),
        b1s([("Measured: ", True), ("5123 pytest tests collected on the deployed tree (5012 pass, "
            "92 skip themselves) + 120 cargo tests; migrations 001–025. Bench: decider 455.78 tok/s (p99 1106.8 ms), Gemma 20.09 tok/s, "
            "embeddings 92.7 ms, 62.73 GiB resident; adversarial suite 19/19 (score 100; avg "
            "29.19 s / max 57.38 s). Kept visible: tool coverage 0.684 / keyword coverage 0.561; "
            "one same-day 69.99 s scenario; DSTGAT ships as architecture only.", False)]),
    ], x=Inches(0.55), y=Inches(1.5), w=Inches(8.55), h=Inches(5.35))
    # The interface, live (V3, 2026-10-27): Decide on the stolen-vehicle
    # sighting (EMULATED reads, plate masked until an officer is named) and
    # the Map on Google's photoreal 3D city. Both 1440x900 → w3.95/h2.47.
    v3 = VVIP / "showcase"
    if (v3 / "showcase_v3_decide.png").exists() and (v3 / "showcase_v3_map.png").exists():
        s.shapes.add_picture(str(v3 / "showcase_v3_decide.png"),
                             Inches(9.25), Inches(1.55), width=Inches(3.95))
        s.shapes.add_picture(str(v3 / "showcase_v3_map.png"),
                             Inches(9.25), Inches(4.12), width=Inches(3.95))
        tf = textbox(s, Inches(9.1), Inches(6.66), Inches(4.25), Inches(0.4))
        set_par(tf.paragraphs[0],
                "Live stack, 2026-10-27 — Decide · the Map on the 3D city",
                8, GRAY, italic=True, align=PP_ALIGN.CENTER)
    add_footer(s, 4)

    # ── Slide 5 — impact (numbers from the run) ───────────────────────
    s = prs.slides.add_slide(blank)
    title_block(s, "Impact for Viksit Bharat 2047 — from the impact run",
                "Social cause impact")
    per_jn = (f" (per frozen junction ≈ {fmt(pj['commuter_minutes_baseline'])} → "
              f"≈ {fmt(pj['commuter_minutes_platform'])})" if pj else "")
    bullets(s, [
        b1([("Per movement (central case, modelled on the real-road network): ", True),
            (f"commuter delay drops from {fmt(c['commuter_minutes_baseline'])} to "
             f"{fmt(c['commuter_minutes_platform'])} commuter-minutes when all "
             f"{net['junctions']} junctions of the {net['segments']}-segment network are frozen "
             f"— an upper-bound framing{per_jn}; vehicles caught in holds fall from "
             f"{fmt(c['vehicles_delayed_baseline'])} to {fmt(c['vehicles_delayed_platform'])}.", False)]),
        b1([("Reduction in junction-freeze commuter delay: ", True),
            (f"{fmt(cons['reduction_factor'])}× (conservative) — {fmt(c['reduction_factor'])}× "
             f"(central) — {fmt(opt['reduction_factor'])}× (optimistic), independent of the "
             "junction count: delay scales with hold duration squared.", False)]),
        b1([("Per year ", True),
            (f"(250 movement-days, RTI-able): {millions(ann['commuter_hours_returned_per_year_central'])} "
             f"commuter-hours returned; {millions(fuel_l)} litres of idle fuel and "
             f"{fmt(co2_t)} tonnes of CO₂ avoided.", False)]),
        b1([("Emergency patients: ", True),
            (f"≈ {fmt(amb['minutes_returned_per_year'])} golden-hour minutes/year returned "
             f"({fmt(amb['trips_crossing_per_movement_day'])} intersecting trips/day × 11 min). "
             "We claim minutes returned, never “lives saved”.", False)]),
        b1([("Accountability (SDG 16): ", True), ("every AI decision logged with distribution + "
            "confidence; every penalty a recommendation until a named officer approves it, with an "
            "append-only audit trail; every escort route switch an officer's call; vehicles-only enforcement "
            "with lawful basis and capped retention — no person-tracking, no fine on a stolen "
            "car's owner. SDG 11 · 3 · 16 · 13.", False)]),
        b1([("One engine, eight corridor classes + the enforcement family: ", True), ("protected "
            "movements · the 148-edition Rath Yatra · Kumbh-class gatherings · marathons · the "
            "national ceremonial days · ~132,000-seat stadium egress · monsoon flood evacuation · "
            "metro work zones — plus the stolen-vehicle chain, each a runnable scenario on the "
            "real roads (VVIP/docs/USE_CASES.md).", False)]),
    ])
    add_footer(s, 5)

    # ── Slide 6 — team & sustainability ───────────────────────────────
    s = prs.slides.add_slide(blank)
    title_block(s, "Team, adoption, sustainability", "Presentation & teamwork")
    bullets(s, [
        b1([("Team (≤3): ", True), ("<Name 1 — platform / ML> · <Name 2 — civic layer / outreach> · "
            "<Name 3 — operations / impact> — <institution>, <AISHE IDs>", False)]),
        b1([("Adoption: ", True), ("a Smart City SPV / city traffic police pilot on one corridor; "
            "bill of materials = one GB10-class edge box; it plugs into the state's ICCC / CCTV / "
            "ITMS cameras and 108/EMRI dispatch rather than replacing them.", False)]),
        b1([("Open source (MIT): ", True), ("any state can fork. Roadmap: T+1 month — register the "
            "city's ICCC / CCTV cameras and land the first live ANPR adapter · T+3 — pilot design "
            "with one city + 108 dispatch; real field traffic to calibrate the twin; lift the two "
            "open suite quality gaps (tool coverage 0.684, keyword coverage 0.561); first trained "
            "DSTGAT weights · T+6 — two more languages; event-corridor preset for a real gathering "
            "(Rath Yatra / match night) with the city.", False)]),
        b1([("Costs: ", True), ("the intelligence runs at the edge; marginal cost per movement ≈ "
            "zero; alerts ride existing SMS/WhatsApp rails.", False)]),
        b1([("Privacy principle: ", True), ("VVIP identity/destination never logged; decisions carry "
            "audit trails; enforcement is vehicles-only with lawful basis, capped retention and "
            "human-approved decisions.", False)]),
    ])
    add_footer(s, 6)

    # ── Slide 7 — AI disclosure & references ──────────────────────────
    s = prs.slides.add_slide(blank)
    title_block(s, "Disclosure of AI-tool usage & references", "Mandatory disclosure")
    bullets(s, [
        b1([("AI tool usage: ", True), ("the base prototype and our enhancements were developed "
            "with the help of AI coding assistants — including agent sessions that built the model "
            "stack, the citizen advisory and 108 driver surfaces, the event emulator, the God's-eye "
            "canvas and its 3D draping, the real-road network generator, the command-deck "
            "interface, the enforcement/watchlist chain, escort authority, the impact harness and "
            "documentation.", False)]),
        b1("Detection/decision tools are deterministic, team-reviewed code (optimizer, classifier, "
           "simulator, enforcement rules); the forecaster's live rung is a third-party zero-shot "
           "model with fixed weights (t0-alpha, Apache-2.0); the two-tier reasoning layer is "
           "logged answer-by-answer with probability and confidence; no AI output acts unreviewed — "
           "the AI proposes, a named officer decides every penalty, pursuit, dispatch and escort "
           "route switch."),
        b1("The interface of record is the backend-wired command-deck at :5273 behind the "
           "operator sign-in (screenshots taken on it live, 2026-10-27: operator views, the "
           "public page keyless; reference photos are credited and labelled not live); "
           "the legacy React demo is the clearly-labelled offline fallback; the showcase injects "
           "emulator-generated causes into the real stack (reads labelled emulated_anpr, units "
           "labelled emulated). Every statistic comes from cited sources, the falsifiable "
           "assumptions ledger of IMPACT_REPORT.md, or the in-repo "
           "artifacts (scripts/bench_results.json, showcase/showcase_results.json, "
           "showcase/pursuit_chain.json, services/command-deck/tests/artifacts/screens/) — model "
           "outputs are labelled as modelled. Road geometry © OpenStreetMap contributors, ODbL 1.0."),
        b2("References: MHA Blue Book protocol summary · Free Press Journal (Mumbai ambulance hold, "
           "Sept 2022) · Kanchipuram 2018 · Agartala Feb 2026 · Times of India Ahmedabad (2009; "
           "riverfront-run diversions May 2024) · Vibes of India (2022 CM convoy) · GVK EMRI "
           "Gujarat fleet figures · NDTV + utsav.gov.in (148th Rath Yatra) · Wikipedia/UP govt "
           "(Kumbh 2019→2025) · ahmedabadmarathon.com / Olympics.com / ThePrint (2024 marathon) · "
           "Gujarat CMO (76th Republic Day) · Wikipedia + Ayen News (Motera / IPL 2026 final) · "
           "India Today (T20 WC 2026 final) · BBC / ReliefWeb (Gujarat floods 2024) · PIB + Indian "
           "Express (Metro Phase 2, Kankaria closure) · OpenStreetMap · MoRTH ITS / Smart Cities / "
           "Gati Shakti · MyBharat HSC 2027 brief."),
        b2("Full citation lists: PROBLEM_STATEMENT_GUJARAT.md §6 and VVIP/docs/USE_CASES.md "
           "(Sources). The demo runs live on the GB10 box; emulated sources are labelled on every "
           "screen."),
    ])
    add_footer(s, 7)

    prs.save(OUT)
    print(f"wrote {OUT}")
    print(f"network {net['segments']} segments / {net['junctions']} junctions; central: "
          f"{fmt(c['commuter_minutes_baseline'])} -> {fmt(c['commuter_minutes_platform'])} "
          f"commuter-min/movement; annual hours {fmt(ann['commuter_hours_returned_per_year_central'])}; "
          f"fuel {fmt(fuel_l)} L/yr; CO2 {fmt(co2_t)} t/yr; ambulance {fmt(amb['minutes_returned_per_year'])} min/yr")


# movements per year for annual fuel/CO2 — same constant as the report
IMPACT_A = 250

if __name__ == "__main__":
    build()
