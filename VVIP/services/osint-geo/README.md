# osint-geo — the offline geo-resolver for Veer's OSINT signals

Turns a `RawOsintSignal` (osint_common, X18) into a `Geocode` snapped to a real `segment_id` or `junction_id` of the
OpenStreetMap network Veer routes on (`corridor.road_segments` 1001-1049, `corridor.junctions` 1-34), with a
calibrated confidence, or an honest `None`. Offline and deterministic: no paid or online geocoder, no network call,
no secret. Places only: nothing here reads, stores or returns a person.

```python
from osint_geo.gazetteer import load, Gazetteer          # .entries .by_id .protect_set (frozenset) .norm() .match()
from osint_geo.resolver import GazetteerResolver, resolve_text
from osint_geo.snap import load_network, snap            # snap(lon, lat) -> (segment_id, junction_id, name, residual_m)
from osint_geo.confidence import score, bucket

geocode = GazetteerResolver().resolve(signal)            # Geocode | None (osint_common.pipeline.GeoResolver)
resolve_text("Paldi char rasta")                         # GET /osint/gazetteer/resolve?q= candidates (C-T)
```

## Data files and path rules

| File | Owner | Rule (first hit wins) |
|---|---|---|
| `scripts/data/osint_gazetteer.json` (X19, ODbL) | this package's generator | argument → `$OSINT_GAZETTEER_PATH` → repo-rooted (walking up from the module) → `/repo/VVIP/scripts/data/` |
| `scripts/data/osm_network.json` (read only) | `scripts/gen_osm_network.py` | argument → `$OSINT_NETWORK_PATH` → repo-rooted → `/repo/VVIP/scripts/data/` |

Both are loaded once per process (cached by path, behind a lock) and are immutable afterwards, so a resolver is safe
to share between threads. An explicit path or variable naming a missing file raises `FileNotFoundError`; an invalid
gazetteer raises `ValueError` (places only: any key outside the X19 field list is refused at load).

## How a signal resolves

1. **Extract** — the title, the text and the connector's `raw_geo_hint.place_names` (the first 8, 200 characters
   each: connectors send one to three short names), read together (the PoC's
   order), normalised (NFKC, lower case, Latin diacritics folded, format characters removed, punctuation → space,
   `NH-147` → `nh147`; Gujarati and Devanagari kept, Gujarati case endings such as `-માં`, `-ે` and `-એ` stripped
   when the stem is a place word). A token-trie longest-match scan finds every non-overlapping surface form; the
   place grammar rewrites generic words (`char rasta` → `cross roads`, `darwaza` → `darwaja`, `cir` → `circle`,
   `ચોકડી` → `cross roads`).
2. **Candidates** — exact aliases; only when none match, `difflib` fuzzy matching (ratio ≥ 0.90, trigram
   prefilter) on the grammar's cue-bound names first ("near Karnavti Club"), then three- and two-word windows:
   multi-word only, never with a locality or newsroom word (`india`, `gujarat`, `news`, …) or only generic words
   in the window. This is the PoC's "India" ↔ "indira" fix, and no bare given name, common word or other town
   ("indira", "gandhi", "income", "helmet", "airport", "dehgam") is an alias at all.
   **Context gate** (`resolver.CONTEXT_FORMS`, each with its reason): some forms name an Ahmedabad place only in a
   text about Ahmedabad. They are common words (`satellite`, `gota`, `bhadra`, `gmdc`, `income tax circle`),
   names many places share (`ring road`, `civil hospital`, `riverfront`, `riverfront road`, `flower park`,
   `iskcon`/`iskcon temple`, `karnavati`, `vaishnodevi`, `gandhi road`, `gandhi ashram` (Wardha's Sevagram,
   Champaran's Bhitiharwa, the khadi stores), `airport road`, `dr ambedkar road`,
   `swami vivekananda road`, `airport circle`, `rto circle`, `maharana pratap circle`, `tapovan circle`,
   `nehru bridge`, `nehru bridge road`), other places of the same name (`lal darwaja`, `jamalpur`, `usmanpura`),
   and every bare route code (`nh47`, `nh147`, `sh41`, `sh71`: a highway runs on through other states), with
   their Latin variants and Gujarati and Hindi spellings. They count only when the signal is placed **in the
   city**: by its metadata (`GazetteerResolver.city_scoped`: r/ahmedabad, AMC or Ahmedabad Police as the source, a
   geo hint naming Ahmedabad or Ahmadabad, `LGD:AHMEDABAD`, an Ahmedabad PIN) or by its text naming the city
   (`resolver.CITY_WORDS`, any script). State-level evidence never opens the gate: SACHET or GSDMA as the source,
   `LGD:GUJARAT`, `GDELT_ADM1:IN09`, a hint naming only Gujarat ("Surat, Gujarat, India"); Surat's ring road is in
   Gujarat too. So "Ring road jam in Surat" is `None` from a national outlet, and state level (no point) from GDELT
   with `IN09` or from SACHET with `LGD:GUJARAT`; "Truck overturns on NH-47 near Indore" is `None`; "Ring road jam"
   on r/ahmedabad and "Waterlogging in Satellite, Ahmedabad" resolve. The gate never changes the source-locality
   term of the confidence. The longer forms ("Karnavati Club", "SP Ring Road", "Asarwa Civil Hospital", "Sabarmati
   Riverfront", "GMDC Ground") are never gated, and an operator's `resolve_text` query is local, so the gate is
   open there. **Another thing of the same name** (`resolver.NOT_A_PLACE_BEFORE`): "Sabarmati river" and
   "Sabarmati Express" (any script) are the river and the train, never the Sabarmati neighbourhood. **The state
   gate** (`resolver.STATE_GATED_FORMS`): a signal with state-level evidence (`GazetteerResolver.state_scoped`:
   SACHET or GSDMA, `LGD:GUJARAT`, `GDELT_ADM1:IN09`, a hint naming Gujarat) and no city-level evidence does not
   read the bare "Sabarmati" (`sabarmati`, `sabarmathi`, Gujarati and Hindi): "Water released from Dharoi dam into
   Sabarmati" from SACHET with `LGD:GUJARAT` stays "Gujarat (state)" with no point, while `LGD:AHMEDABAD`'s
   "Waterlogging in Sabarmati area" and a national outlet with no state evidence keep the neighbourhood.
3. **Disambiguation** — `R = 0.25·in_bbox + 0.15·specificity + 0.20·coherence + 0.10·importance + 0.10·locality
   + 0.10·match` (research A6, the embedding-context term left to OS-4). Every mention is a reading.
4. **Snap** — a junction keeps its `junction_id`, a road its `segment_id`; a landmark attaches to the segment whose
   anchor (`ST_PointOnSurface` of its line, the point the oracle uses for a segment) is nearest, residual =
   geodesic metres to that anchor (with no anchor in reach, to the nearest road line), **only within 900 m**:
   farther it has no road anchor and no snap quality (F-HONEST OSINT-3: Kankaria Lake was carried as Kankaria Road
   at 2.3 km). **A neighbourhood is an area** and never gets a road anchor ("Maninagar" was Kankaria Road at 2 km);
   the pipeline marks its situation `area_level`. A bare area word ("Odhav", "Paldi", in any script) resolves to
   the neighbourhood, never to the junction named after it (OSINT-1; the gazetteer lint refuses such a junction
   form). **For `segment_id` consumers** (OS-4 attach, OS-6 courses of action, promote): a
   landmark's `segment_id` is that network anchor, not always the nearest carriageway. For 12
   of the 41 seed places in reach they differ; Bhadra Fort is on 1013 (whose line is 481 m away) although Relief
   Road 1005 passes 113 m away. The R23 figures (Karnavati Club → 1045 at 190.5 m) are calibrated on the anchor.
   Use the geocode's `lon`/`lat` for a distance, and `snap.Network.line_distance_m(lon, lat, segment_id)` for the
   distance to a road line.
5. **Confidence** — `0.30·match + 0.25·specificity + 0.20·margin + 0.15·snap_quality + 0.10·source_locality`;
   `high` ≥ 0.75, `medium` ≥ 0.5, else `low`. A place named twice ties with itself (margin 0): repetition never
   inflates confidence. Source locality is 1.0 for a city- or state-scoped source (r/ahmedabad, SACHET, AMC,
   Ahmedabad Police, GSDMA), a geo hint naming Ahmedabad or Gujarat, a city or state admin code, or an Ahmedabad PIN
   (the PoC calibration; the context gate reads city-level evidence only).

**Area level (plan R28)**, for an official source or GDELT with no finer toponym: `LGD:AHMEDABAD` (or a GDELT
`ActionGeo_FullName` naming Ahmedabad, including the GNS spelling "Ahmadabad") → the district point,
`area_scope "district"`, confidence 0.40;
`LGD:GUJARAT` / `GDELT_ADM1:IN09` → `area_scope "state"`, **no point**, confidence 0.25; any other code
(`GDELT_ADM1:IN32` is Daman and Diu) → `None`.

## The gazetteer generator

```bash
python scripts/gen_osint_gazetteer.py --check    # gates: exit 1 when the committed file differs from a rebuild
python scripts/gen_osint_gazetteer.py --write    # after a network or seed-table change
python scripts/gen_osint_gazetteer.py --overpass # opt-in review of OSM place nodes the gazetteer lacks (never gates)
```

127 entries with the PoC's ids (34 junctions, 49 roads, 28 neighbourhoods, 16 landmarks), Gujarati and Hindi
aliases from `translit.py`, and a lint that refuses a multi-word phrase without a place-type word (so a person's
name can never become a protected "place"). The schematic pre-OSM junction labels are not aliases, and neither is
a PoC alias that names two places (`SEED_ALIAS_DENY`: "Sardar Patel Stadium" is Motera's old name and
Navrangpura's stadium). The generator runs on the standard library alone (`osint_geo.gazetteer`, `translit` and
`geom`; the segment anchor lives in `geom.py`, which `snap` re-exports), so `--check` needs no numpy, pyproj or
shapely.

## Tests

```bash
cd services/osint-geo && python -m pytest -q -p no:cacheprovider
PYTHONPATH=src:../osint-common/src python tests/poc_parity.py <PoC out/signals.raw.json>   # PoC parity report
```

All fixtures are synthetic (fictional `*.example` publishers, redacted placeholders); the PoC captures are read in
place and never copied. `$OSINT_POC_DIR` names the PoC prototype directory (default: the orchestration checkout on
the GB10 box); the tests that read it skip when it is absent.
