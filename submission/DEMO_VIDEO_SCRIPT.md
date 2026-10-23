# Veer — demo video script (3:00 · nine beats · one continuous live session)

*Screen recording + voiceover (Hindi-English mix). ≥720p, MP4, ≤80 MB.
**One unbroken session on the command deck of the live stack** — a browser
on the GB10 box at `http://127.0.0.1:5273`, **signed in as the duty officer**
(name + PIN; every approval in the video is recorded under that name). `/`
is the Convoy Command cockpit over 3D Ahmedabad, `/ops` the situation wall.
No cuts between beats: the camera may move (cockpit → ops → gods-eye →
citizen → driver → comms), the session never stops. Every beat is a real
flow proven end to end on the real stack — by the judge's journeys
(`VVIP/scripts/journeys.mjs`, J1–J6) and the flagship showcase
(`VVIP/scripts/showcase_run.sh`; artifacts in `VVIP/showcase/`) — nothing in
this video is a mock-up.*
*The honesty line — "sadak asli hai; traffic, camera aur units emulated
hain, aur har screen par likha hai" — is delivered once, in Beat 2, and
never repeated.*

**Pre-roll (not recorded):**
- `bash VVIP/scripts/veer_up.sh --status` → **READY 11/11** (the stack also
  comes back by itself after a reboot).
- Within ~20 minutes of recording — and at least 30 minutes after any
  showcase or `journeys.mjs --live` run (their finished dispatch tiles
  fold into `/ops`'s history only then) — with the team's go-ahead:
  `bash VVIP/scripts/demo_reset.sh --apply --officer '<Duty Officer name>' --cancel-debris`
  — the starting state: stale runs stopped, the old fine-based pursuit
  cancelled through the audited lifecycle, the unapprovable e-challans on
  the stolen plate rejected, the rehearsal debris (TEST-labelled smoke
  and journey events, the showcase's residue, stale sightings) cancelled
  or dismissed through the same audited channels, and a fresh EMULATED
  stolen-vehicle sweep staged whose **sighting waits PENDING for the
  officer**. It never approves anything, and its last check confirms
  `/ops` offers AUTHORISE PURSUIT on that card (one approval authorises
  one pursuit — an approval already spent on a closed pursuit never
  stands in for the officer's).
- Beat 6 films the twin gate's refusal, which needs the city signal-plan
  writer ON: `bash VVIP/scripts/veer_up.sh --demo` (it also switches the
  emulated living city on, and is refused unless the citizen feed labels
  emulated events). With the writer OFF — the default — the same apply is
  refused earlier, `409 writer_disabled`, and the Beat 6 voice-over does
  not fit: film that refusal with a matching line, or skip the beat.
- Rehearse on a private stack with `node VVIP/scripts/journeys.mjs` — J2
  (the stolen vehicle), J3 (the escort), J4 (the 108 corridor) and J5 (chat)
  are the director's cut of beats 4, 5, 8 and the coda.

---

**[0:00–0:15] BEAT 1 — COLD OPEN: the calm.**
Visual: `/ops`, the dark situation wall, still; the signed-in officer's name
in the command bar. The band masthead reads **GREEN — "Normal operations —
city band GREEN."** The decision-audit stream
ticks softly at the bottom. Nobody touches anything.
VO: "Somvar ki subah. Ahmedabad so raha hai. Yeh deck sheher ki saans ki
ek line mein summary hai — aur abhi sab normal hai."

**[0:15–0:35] BEAT 2 — THE YATRA: one fact, two audiences.**
Visual: the Rath Yatra event goes planned→active on the event board. In the
wall canvas the orange corridor spine is draped onto the 3D old city —
Gandhi Road, Sarangpur, Swami Vivekananda Road, the real streets. The band
climbs **GREEN→AMBER** behind its dwell outline (nothing flickers). Select
the event — the **dossier drawer** opens with its trilingual advisory
preview, the **Gujarati** line rendering the same fact for the street.
VO: "148वीं रथ यात्रा शुरू। Band GREEN se AMBER — lekin dheere: dwell
window pura hone se pehle kuch nahi badalta. Operator ko और nagrik ko —
ek hi sach, apni bhasha mein. Sadak asli hai; traffic, camera aur units
emulated hain — aur har screen par likha hai."

**[0:35–0:50] BEAT 3 — THE MONSOON: pressure without panic.**
Visual: the monsoon burst on the Nehru Bridge approach. Input tiles spike;
the band **holds through hysteresis**. The **AMA card** (Active Movement
Adaptation) shows its protocol floors and the twin shadow-eval.
VO: "Monsoon burst. Inputs uchhal rahe hain — par band nahi. Har badlav
apne dwell window se guzarta hai, aur har non-baseline plan pehle twin par
shadow-eval hota hai."

**[0:50–1:20] BEAT 4 — THE STOLEN VEHICLE: evidence, never a fine.**
Visual: an ANPR read of the reported-stolen plate **GJ27EM9001** lands — the
**EMULATED** badge on screen and staying there. The Decision Queue shows a
**PENDING stolen-vehicle sighting** — "e-challan withheld"; on the canvas
its pin reads **STOLEN · NO FINE · PENDING** — the speed reading would have
been an e-challan, but the owner is the theft victim, so the platform
refuses any fine (the e-challan a rehearsal script approved on 2026-10-18
under a cast officer name, before the rule, reads **SUPERSEDED · STOLEN**
and stands dim when it is in frame — audit history, never a pursuit
basis). The
officer reviews the evidence and **approves the sighting, by name** — that
approval authorises the pursuit. The pursuit opens; the interception plan
ranks the choke junctions on the 3D city; a unit is dispatched to choke #1,
the officer approves, and it moves; the live trace draws with its comet
tail.
VO: "Chori ki gaadi. Camera padta hai — EMULATED, saaf likha hua. Gaadi
chori ki hai, toh maalik par challan kabhi nahi — woh khud victim hai.
Sighting sirf saboot hai; insaan approve karta hai — naam ke saath — aur
tabhi pursuit khulta hai. Gaadiyan hi — log kabhi nahi."

**[1:20–1:45] BEAT 5 — THE ESCORT: the AI proposes, the officer decides.**
Visual: on `/`, a protected movement escorted on its approved route. A
congestion spike ahead — the convoy HUD shows **"AI PROPOSES: via … ·
APPROVE / REJECT · expires in 01:30"**. The officer approves; the new spine
replaces the old (the superseded one stays in the history). *(Alternative
take: no answer — the proposal expires and the convoy holds its approved
plan.)*
VO: "Rasta badalna ho toh AI sirf prastav deta hai. Faisla officer ka.
Jawab na mile toh plan wahi rehta hai — AI apne aap kabhi rasta nahi
badalta."

**[1:45–2:00] BEAT 6 — THE HONEST NO: the feature, not the failure.**
Visual: the operator attempts the **RED city signal plan**. The twin gate
**refuses** — `twin_not_calibrated` — HTTP 409 on the City Signal Plans card,
and the deck **holds baseline in full view**; the refusal lands as the
deck's own row in the audit stream (a refused plan writes nothing on the
server — only a committed apply is logged there).
VO: "Operator RED plan lagana chahta hai. System kehta hai — nahi. Twin
abhi field data par calibrated nahi hai, isliye commit fail-closed hai. Yeh
kamzori nahi, design hai — aur woh 'nahi' bhi wall par darj hota hai."

**[2:00–2:15] BEAT 7 — THE SPILLOVER: the volunteer on the ground.**
Visual: Jan Rakshak dispatch to the Swami Vivekananda Road bazaar
spillover — requested → duty-officer **approved** → en_route → **on_scene**,
every transition a row in the audit stream; the unit (EMULATED) moves on the
city canvas.
VO: "Barricade ke peeche bazaar phail raha hai. Ek tap — Jan Rakshak
unit. Approve, raste mein, on-scene: har kadam ek audit row."

**[2:15–2:40] BEAT 8 — THE GOLDEN HOUR: the driver's own window.**
Visual: cut to `/driver` (Daylight theme, Gujarati-first, no sign-in). The
golden-hour counter ticks. Request → **"awaiting duty officer"** → the duty
officer **APPROVES** on `/ops` → **WINDOW OPEN** with the live countdown.
(The evaluating → proposal steps belong to the labelled scripted fallback,
which shows only when no live event is up — not in this live session.)
VO: "Aur wahi jo aaj exist nahi karta — 108 driver ka apna rasta. Ek
request, ek approval, aur window khuli — golden hour ke minute wapas."

**[2:40–3:00] BEAT 9 — THE EASE: the calm you earned.**
Visual: the morning decays and the band steps back to **GREEN** — through
the hysteresis while the event is still live (a step down needs four
consecutive calmer readings, `down_confirm=4`, and its dwell), or, as in
the live showcase run, at once when the event completes and the engine
releases it. The masthead returns to "Normal operations."
End on the audit stream scrolling the whole session — every decision a row,
each under a named officer.
VO: "Sheher wapas saans leta hai — bina flicker. Aaj subah ka har faisla ek
row hai, har row ke peeche ek naam. Yeh hi platform hai — regulated, not
stopped. Team Veer."

End card (2 s): `127.0.0.1:5273/ops` still visible behind · "Operator?
Citizen? 108 driver? — one city, one truth, a human in every decision." ·
Team Veer.

---

## Production checklist

- [ ] Record 1280×720+ (1680×1050 preferred — the wall's three-column grid
      activates ≥1500px). Browser zoom 100%. One continuous session; cuts
      only between screens, never within a flow.
- [ ] Sign in first; pre-open tabs in order: `/`, `/ops`, `/gods-eye`,
      `/citizen`, `/driver`, `/comms` — all on `http://127.0.0.1:5273`. No
      dev server in the video. Give the 3D tiles a minute to stream in
      before recording.
- [ ] `demo_reset.sh --apply --officer '<name>' --cancel-debris` within
      ~20 minutes of recording (the staged sweep's patrol units live only
      while it runs) and ≥ 30 minutes after the last showcase / journeys
      run; it must end with its checks ok and exit 0.
- [ ] Beat 2: the honesty line exactly once. Never again.
- [ ] Beat 4: the EMULATED badge and the STOLEN · NO FINE · PENDING pin
      must be legible when the sighting lands (zoom 150% if needed); the
      approval must be of the SIGHTING — never of an e-challan.
- [ ] Beat 5: hold on the expiry countdown long enough to read it.
- [ ] Beat 6: the writer is ON (pre-roll) so the refusal is the twin's
      `twin_not_calibrated`; do NOT cut away from the 409; hold ≥3 s on the
      refusal.
- [ ] Beat 9: if the step down comes through the hysteresis, hold on the
      dwell counter completing (4/4) before the wipe — the anti-flicker
      proof is the point; if it comes from the event completing, show the
      event leaving the board as the band returns to GREEN.
- [ ] No real person/vehicle data anywhere; the stolen plate, the FIR
      number and the officer names are the scripted cast.
- [ ] Verify the final cut is ≤3:05 and ≥2:55; re-time after any edit.

## Why every beat is filmable as written

| Beat | Flow | Evidence |
|---|---|---|
| 1 | GREEN masthead, audit stream | journeys J1 on the live deck (17/17, city at rest, honest labels); `tests/screens-verify.mjs` ops checks (40/40 on the live deck, 2026-10-24) |
| 2 | event planned→active, dwell outline, Gujarati advisory | the flagship run's `adaptive.situation_log` (AMBER 7 / RED 18 rows; `showcase/showcase_results.json`); journeys J6 (EN/HI/GU, 18/18) |
| 3 | inputs spike, hysteresis hold, AMA shadow-eval | `showcase/ambulance_observe.json` (the band holds AMBER through the 108 window — escalation TAKEOVER, handoff operator); the AMA card's live descriptor |
| 4 | EMULATED read → PENDING stolen-vehicle sighting (e-challan refused, 409) → named approval → pursuit (never on the e-challan, 422) → choke dispatch → the unit moves | journeys J2 on the live deck (23/23, 2026-10-24 00:02 IST); the live flagship run (`showcase/pursuit_chain.json`, 2026-10-24 00:01 IST): 6 reads → `R_STOLEN_SIGHTING` ×6, "e-challan withheld", an e-challan approval on the plate refused 409, the sighting approved by `Scripted demo officer (showcase script)`, ten choke junctions ranked (top: junction 15) and the trace drawn (12 timed positions — the trace's 24 h window held these 6 reads and the 23:51 run's 6) |
| 5 | AI proposal → APPROVE / expiry → plan held | journeys J3 on the live deck (13/13 — no AI proposal arose in its window, so it proved the hold branch: the approved plan held); the APPROVE / REJECT / expiry path: convoy-brain's escort-authority suite (13 tests) and the hermetic ops-wall smoke's escort groups (`VVIP/services/command-deck/tests/ops-wall-smoke.mjs`); `GET /escorts` publishes `officer_approves_every_switch` |
| 6 | RED plan → `twin_not_calibrated` refusal, baseline held | `showcase/signal_policy.json`: 409 `shadow_eval_failed_closed`, 11 junctions, 0 committed; the calibration replay `no_data` (no field observations). The live run's plan was the AMBER band's — every band's plan passes the same shadow-eval gate, so a RED plan meets the same refusal; the refusal is the oracle's last-plan answer and the deck's own audit-stream row (only a committed apply writes `corridor.signal_plan_log`) |
| 7 | Jan Rakshak requested → approved → en_route → on_scene | `showcase/jan_rakshak.json` (JR-EM-01, every transition audited — the script walks them in seconds, so its projected unit had not yet moved); the unit moving on the canvas: journeys J2 on the live deck (117 m in 9 s toward its choke) |
| 8 | driver request → awaiting duty officer → approve → window open | journeys J4 on the live deck (11/11: the live request, the named approval, the driver's own view following to approved · unit bound); `tests/screens-verify.mjs` drives `/driver` to the open window only in its labelled scripted fallback (7/7, the 90-s window — as on 2026-10-24, with no public event up) — in live mode it checks the idle request card and files nothing |
| 9 | the band back to GREEN — by hysteresis (`down_confirm=4`) or by the event's release | `services/traffic-oracle/src/traffic_oracle/adaptive/hysteresis.py` (`down_confirm = 4`, plus the dwell); the live run's `showcase/band_easing.json` holds its one transition row (n=8, AMBER→RED), and the city band was GREEN again once the engine released the completed event (`showcase_results.json` `band_transitions`) |
