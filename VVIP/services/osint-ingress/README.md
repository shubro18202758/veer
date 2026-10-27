# osint-ingress (:8093)

Turns open sources into canonical, already-redacted `RawOsintSignal` records (`osint_common.types`, contract
X18) and posts them to the oracle's loopback machine-ingest route `POST /api/v1/osint/signals` (contract C-T).
Events are about places and situations, never persons.

## Run

```bash
PYTHONPATH=src:../osint-common/src:../osint-geo/src:../osint-analysis/src python -m osint_ingress serve
python -m osint_ingress once [--offline] [--cache-dir D] [--oracle URL] [--dry-run] [--report out.json] [--backfill] [--only a,b]
python -m osint_ingress import-poc <capture_dir> <cache_dir>
```

Exit codes: 0 ok, 2 usage (a non-loopback oracle URL or an unknown `--only` connector included; caught before
anything is built or probed), 3 pipeline libraries missing (`--dry-run`).
`once` probes the oracle first; when it is unreachable nothing is posted, the batches stay in the cache outbox,
the report says `publish: "skipped: oracle unreachable"` and the exit code is 0. `--dry-run` runs
`osint_analysis.pipeline.run_pipeline` with the `osint_geo` resolver in-process and prints `MACHINE_RESULT={...}`.

Environment: `OSINT_ORACLE_URL` (loopback only; unset: `http://127.0.0.1:9`, the discard port), `HOST` (`127.0.0.1`), `PORT` (`8093`),
`OSINT_CACHE_DIR` (`/var/cache/osint-ingress`), `OSINT_MODE` (`live` | `offline`), `OSINT_GAZETTEER_PATH`,
`OSINT_CADENCE_<CONNECTOR>_SEC` (0 takes a connector off the schedule; values under 60 s are raised to 60 s).
The service reads no secret and writes nothing but its cache. `OSINT_ORACLE_URL` has no usable default: unset, it is
the discard port `:9`, so a run that names no oracle posts nowhere (its batches wait in the outbox) and never
reaches the live oracle by accident. The deployment names its oracle explicitly; a harness names a sandbox oracle.

## Routes

- `GET /health`: `{status, mode, version, oracle{host, reachable, last_post_at, last_post_status},
  connectors{<name>{enabled, cadence_sec, last_run_at, last_ok_at, fetch_mode, signals, error, cache_age_sec}},
  last_cycle{at, signals, accepted, rejected, geotagged, surfaced, pii_redactions}, egress_allowlist}`.
  `oracle.reachable` comes only from a `GET {oracle}/health` probe (start-up, then every 30 s). A connector its
  source disables ("robots.txt disallows") shows `enabled: false` with that `error`, and its cache is not served.
- `POST /cycle` (loopback callers only): one cycle now; returns the `last_cycle` object.

## Connectors and schedule

| source | cadence | endpoint |
|---|---|---|
| `sachet_cap` | 5 min | NDMA SACHET CAP RSS for Gujarat, plus the CAP 1.2 detail of new alerts |
| `google_news_rss` | 10 min | Google News RSS search (pointer layer, never redistributed) |
| `gdelt_events` | 15 min | GDELT 2.1 `lastupdate.txt` and only the export zip it names |
| `gdelt_doc` | 15 min | GDELT DOC 2.0 ArtList (≥ 5 s between requests; a 429 serves the cache) |
| `reddit_rss` | 15 min | r/ahmedabad Atom feed (aggregate social signal only; the committed synthetic capture uses the fictional `r/example_city`) |
| `amc_scrape`, `gsdma` | hourly | official pages, best effort; a robots.txt disallow disables the connector |
| `ahmedabad_police_scrape` | off | disabled: the listed host serves unrelated content and is not allow-listed |
| `common_crawl` | never | backfill only (`once --backfill`) |

Each connector separates `fetch()` (raw bytes into the cache) from `parse()` (cache to signals). Offline mode, and
a failed live fetch, parse the newest cache entry and label the signals `cached-sample`, with `fetched_at` set to
the capture time. Retention: 72 h or 200 MB, whichever comes first; the newest entry of each connector is kept.
The cache root is created `0700` (files `0600`). A CAP `<expires>` days ahead is kept as `valid_until` (up to
31 days ahead); a publication time more than a day ahead is treated as unknown.

## Ethics rails in this service

- Names and ages are redacted at parse (`[PERSON]`, `[AGE]`; social contacts `[CONTACT]`); the result always passes
  `osint_common.ethics.find_pii`, which proves only that none of ITS patterns survived: it is the same pattern
  family the redactor uses, so it cannot see what they miss. **What the redactor does not promise**: no NER runs at
  parse, so a name with no cue, no known surname and no role noun ("Viral Doshi says"), a single given name after an
  unlisted verb, or an ALL-CAPS headline can survive. The honest figure is the held-out recall
  (`tests/test_heldout_recall.py`, three corpora of invented names; the one written blind and never tuned on scored
  latin-name recall 0.882, Indic 1.0, age markers 0.895, keep 0.987). Cue-less names are read through role and kin
  nouns ("Biker <Given> <Surname>", "husband <Given> <Surname>"), a common-surname list ("<Given> <Surname>"),
  Gujarati "-bhai"/"-ben" given names, both sides of "alias"/"@", "<Given>, a <role>," and "<Name>'s body/family".
  **Indic script**: a Gujarati or Devanagari word that is neither a gazetteer place nor an ordinary word is
  withheld as `[WITHHELD]` in every tier (no Indic NER yet), and Indic ages ("૩૫ વર્ષીય", "(૬૦)") become `[AGE]`.
  A social post's age and sex shorthand ("F(28)", "22M", "27/F") is `[AGE]` (a bare "15M" in a post is redacted
  too: accepted over-redaction). Beyond the shared cue patterns, a cue-introduced name runs on over a 4th,
  initialled or hyphenated name word; "the victim, <Name>,", "the deceased as <Name>", "Mr.<Name>" and Title-Case
  "Accused <Name> <Name> Held" are read; and the name right before an age ("<Name>, [AGE]," / "<Name> ([AGE])")
  is redacted. A Reddit user mention or page (`u/<name>`, `/u/<name>`, `/user/<name>`, `r/u_<name>`,
  `reddit.com/u/<name>`) becomes `[PERSON]` in every tier, news, GDELT and official included. Social posts are
  redacted most aggressively: `@<name>` and "insta: <handle>" mentions too (in news an `@`-account, usually an
  outlet's or an office's, is kept), and every capitalised run (initials such as "K." included) that no
  gazetteer phrase covers and that is not a generic word (a place noun such as "Road" never vouches for the name
  before it).
  There is no NER yet: a bare name with no cue word in a news headline, a single-word name in a post, or a name in
  Devanagari or Gujarati script is not detected.
- Every URL written in a news or social title or text is redacted (a slug or a profile path can name a person):
  a Reddit user page becomes `[PERSON]`, any other URL `[URL]`. `pii_redactions` counts every replacement
  (`[PERSON]`, `[AGE]`, `[CONTACT]`, `[URL]`).
- Reddit poster blocks are never read, and the "submitted by" footer is cut; GDELT actor and person columns are
  never read; court-record portals (case captions name the parties) are dropped; the Google News display name
  (free text, maybe a blog's owner) is cut from titles and descriptions, and only the outlet's domain is kept.
- News- and social-tier URLs are never emitted, stored or logged: the signal keeps the outlet's domain and a
  `url_sha256:` hint of the canonical URL. Official sources keep their identifier URLs.
- `raw` is a scalar whitelist (`RAW_ALLOWED_KEYS`), never the source record.
- Egress goes only to an allow-list of exact hosts over https, with redirects checked hop by hop; the oracle is
  loopback only; every XML, RSS, CAP and Atom document is parsed with `defusedxml`.

## Tests

`pytest` here; `tests/fixtures/README.md` gives the provenance of every fixture. `tests/fixtures/capture/` is the
synthetic sandbox seed (import-compatible; only its SACHET file is real, public domain).
