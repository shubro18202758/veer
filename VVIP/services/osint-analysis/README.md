# osint-analysis

Veer's OSINT analysis library (OS-4): it turns geocoded open-source signals into honest **situations about places,
never persons**. Pure and deterministic: no database, no network except an optional embedder.

```python
from osint_analysis.pipeline import run_pipeline   # (signals, *, resolver, live=None, embedder=None, now=None) -> PipelineResult
from osint_analysis.classify import classify       # classify(signal) -> Classification; never crime_incident
from osint_analysis.embed import HttpEmbedder      # HttpEmbedder(base_url, timeout=3.0); None on any failure
```

The shapes (`RawOsintSignal`, `Geocode`, `Classification`, `ResolvedEvent`, `LiveStateSnapshot`, `PipelineResult`, …)
and the vocabulary (`INCIDENT_CLASSES`, `RELATED_CLASSES`, `RESPONSE_PRIORITY`, …) are `osint_common`'s (X18). The
resolver is injected (`osint_geo.resolver.GazetteerResolver` in production); this package never imports `osint_geo`.

## Stages

| Stage | Module | Rule |
|---|---|---|
| Classify | `classify.py` | The SACHET rule (a CAP alert with a flood word is `urban_flooding`, else `weather_hazard` with the alert's own event as subtype: `rain`, `thunderstorm`, `heat`, … from `cap_event` or the text, else `weather_advisory`, never "storm" for all); the PoC lexicon in order, first row wins, a keyword matching a whole word (itself or a regular inflection: `mobs`, `mobbed`, `crashes`, `robberies`; a noun takes a plural only: `concerts`, never "concerted"), the derived words the PoC's substring test caught (`protesters`, `looters`, `chain snatchers`, `brawlers`, `marchers`, `gas leakage`, `oil spillage`; never "striker", "mobile", "Protestant", "accidental"), a stem list matching any continuation (`waterlog…`, `inundat…`, `flood…` but not "floodlights"), and two context rules (the month "by March" is not a march; a "lightning strike" is not a labour strike); optional zero-shot against one exemplar per class (official and news tiers only); else `general_news`. Every rule reads the text without poster handles. A final check raises on `crime_incident` or `vehicle_pursuit`. |
| Stage 1 | `fusion.py` | Per realm × class: DBSCAN (haversine, 900 m) blocks for points, shared `segment_id` for roads (a neighbourhood blocks by its reference point: it has no segment), state areas only with the same state; a 6 h window for point incidents, 48 h for ongoing situations; inside a block, a link needs co-location, the window, and text similarity (embedder cosine ≥ 0.70, else token Jaccard ≥ 0.20). Links are taken strongest first, and none that would put two point reports more than 1.8 km apart in one cluster, or spread its REPORT times over twice its class window (a dense field of similar reports never chains across the city, an accident hotspot never into one day-long situation; a long validity never stops a 4-day warning from joining its re-issue). A district alert cluster then joins AT MOST ONE point cluster inside its district (the most similar, ties to the earliest), or stays its own: an area never merges two point clusters, and never joins a point cluster made only of social posts. The pair tests run as array operations, and a block no bound can split is clustered as plain connected components: 2 000 reports of one procession within 300 m take about 1 s (12.7 s pair by pair). |
| Stage 2 | `correlate.py` | Related classes co-located at the same level (point representatives within 1 200 m or on one road segment; the same district; the same state) and overlapping in time join into one situation, nearest first, never two clusters of one class (a clash report between two accidents joins one of them); primary class by response priority, ties by member count, then the earliest report. Only pairs a vectorised distance filter lets through are tested (the same result as testing every pair). |
| Credibility | `credibility.py` | Base = strongest prior; +0.15 per extra trust type (official, news, social); +0.05 per extra independent publisher within a type, capped at +0.10; independence by registrable publisher domain, never by URL; a single social source ≤ 0.30; ceiling 0.99. Cross-posts are one source: the posts of one community are one source, and two communities are one when a post of one near-duplicates a post of the other (content-token Jaccard ≥ 0.75 of the titles or of the whole texts, or every token of the shorter, at least 3, in the other; cross-post markers and `r/<community>` mentions removed). Syndicated copies are one source too: the same rule across every news tier, so one wire story carried by N outlets is one independent publisher, not N. `SIMULATED` and `EMULATED` pass through, never upgraded. |
| Attach | `attach.py` | Read-only: an ACTIVE live corridor event (`event:` URN) of a compatible kind (an accident ↔ `road_accident`, a crowd ↔ `mass_gathering`, …) within 900 m or on the situation's road segment, overlapping in time, is corroborated; else `novel`. Never a convoy, a `protected_movement` (that is a second-order effect), a `vehicle_pursuit` or a `crime_incident`. Area-level situations and chatter are always novel, and the pipeline checks surfaced situations only (a held social post is never linked to a live event). |
| Second order | `second_order.py` | `protected_corridor` (an active protected movement's route), `convoy` (a convoy in motion on the route or within 900 m), `ambulance_route` (an active 108 route), `closure` (a segment already closed); notes say "on or near segment N"; surfaced situations only. |

A situation surfaces (`is_event`) only for an incident or operational class, never from a single social post or
from the posts of one social community (one source: they may be one poster), and never when every geocode is
state-level; otherwise it is held with its reason and only counted. An area-level member is never corroboration
of a point-level social report: a district alert or district-level report never joins a point cluster made only
of social posts (it stays its own district situation), and the single-social rules are also applied to a
situation's point-level members, so a SACHET Ahmedabad alert can never lift one waterlogging post into an
"Official, verified" street event. An independent point-level news or official report of the same situation still
surfaces it.
An area member attached to a point situation is context, never verification: credibility, verification state,
cross-type corroboration, independence, source tiers, labels and the time window (which the live attach and the
second-order checks read) come from the point-level members only. A Paldi news report with a district SACHET alert
attached stays `NEWS-REPORTED` 0.60; `OFFICIAL-VERIFIED` needs an official source reporting the point-level
situation itself. The alert stays a member and a source, listed after the point-level sources with the role
`CONTEXT_ROLE` (`"context"` once OS-1's `SourceRole` has it; `"corroborating"` until then).
`fused_event_id = sha1("anchor:" + earliest member signal_id by (published_at, signal_id))` over the situation's
point-level members when it has any: a district alert that joined a point situation never anchors it, so the id
stays with its place when the alert re-attaches elsewhere in a later cycle. A district or state situation is
anchored on its earliest member.

Two kinds of member can never surface and are therefore held as aggregates rather than deduplicated as incidents:
`general_news` chatter (one aggregate per place and time window) and state-level alerts (one per state and class).

## Ethics in code

- No person field anywhere; `ResolvedEvent`, `SourceRef` and the counts are `osint_common` models (`extra="forbid"`).
- A poster handle is never a cue: `classify.strip_handles` removes Reddit's `submitted by /u/<name> [link]
  [comments]` trailer, any other `/u/<name>`, `u/<name>` or `reddit.com/user/<name>`, and the boilerplate inside
  `normalize_text`, the one text view the classifier, the similarity tokens and the embedder read. Two posts by one
  poster are never more alike than the same posts by two posters.
- Labels, summaries and source titles are fitted to their limits and re-checked with `ethics.find_pii` after the
  clip (a cut can leave the "Dr. <name>" of a protected place "Dr. <name> Road"); the same helper drops a stray
  handle trailer and turns any other handle into `[PERSON]`. No text can fail the output model and sink a batch.
- `SourceRef.url` is kept for official sources only (SACHET/NDMA, IMD, SDMA); news and social URLs, whose slugs can
  name a person, are `None` (the source stays verifiable by its `signal_id` and publisher).
- Reported crime comes only from reported text (`reported_crime`, `public_disorder`), never from a camera or image
  path, and never as `crime_incident`.
- `HttpEmbedder` posts only to `/embed` (a read); it never calls `/embed/documents` or `/incidents`, which write to
  the memory store, never follows a redirect and ignores proxy environment variables; one call ends within its
  `deadline` (10 s) however many batches it needs. Today's embedding service has no `/embed` route, so the client
  returns `None` and the pipeline uses lexical similarity.

## Checks

```bash
cd services/osint-analysis
python -m pytest -q -p no:cacheprovider
# PoC parity with the PoC's own geocodes replayed (the real PoC outputs are read in place, never copied; the
# PoC tests find them through $OSINT_POC_DIR or a .veer-orchestration sibling, and skip without them):
PYTHONPATH=src:../osint-common/src python tests/poc_parity.py --signals <PoC out>/signals.raw.json \
  --geo <PoC out>/events.geo.json --live <PoC out>/raw/sandbox_city_entities.json
```

Test fixtures are synthetic (fictional `*.example` publishers, no real names): `tests/analysis_fixtures.py` and
`osint_common.testing`.
