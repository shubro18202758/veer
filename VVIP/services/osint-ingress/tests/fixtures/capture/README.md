# Synthetic OSINT capture (the sandbox seed)

This directory is laid out exactly like a PoC raw capture directory (`osint/prototype/out/raw/`), so
`python -m osint_ingress import-poc tests/fixtures/capture <cache_dir>` reads it unchanged. It seeds the int3cl
sandbox (plan §7 step C4, R13), so every dev-deck screenshot, recorded contract fixture and docs image built
from int3cl is synthetic.

**Labels.** `import-poc` reads the table below: every file marked **synthetic** is imported as a synthetic cache entry,
so the signals parsed from it carry `provenance_label: SIMULATED` (never `NEWS-REPORTED` or `UNVERIFIED-OSINT`: no
outlet or community reported them), and the situations built from them stay `SIMULATED`. The one real file, the
SACHET sample, keeps `OFFICIAL-VERIFIED`. The real PoC captures are never copied here; they are read in place for parity runs on
int3c only.

| file | provenance | what it is |
|---|---|---|
| `sachet_gujarat_live.xml` | **real** | NDMA SACHET CAP RSS for Gujarat, **public domain** (its own `<copyright>public domain</copyright>`), copied verbatim from the PoC capture (sha256 `5859003279823785ee36e1071cee5ffa8158c00ff639c5246fbb4bc3540eef4d`). 10 CAP weather alerts about districts issued through IMD Ahmedabad: 1 names Ahmedabad (a district-level alert), 9 are state-wide nowcasts naming other districts. It carries no person: its `<author>` element is the NDMA control-room mailbox, and the parser never reads it. |
| `gnews_live.xml` | **synthetic** | A replica of the Google News RSS search schema (channel, items with `title`, `link`, `guid`, `pubDate`, `description`, `<source url>`). Fictional publishers `news-a.example` and `news-b.example`; fictional names and ages to exercise redaction; the PoC's toponyms and class cues: four collision reports and one "beaten by mob" report near Karnavati Club on SG Highway, a robbery at Odhav Ring Road Circle, two general items. Not Google News content. |
| `reddit_live.rss` | **synthetic** | A replica of Reddit's community Atom schema, for the fictional community `r/example_city` (`entry` with an `author` block, `content` HTML with Reddit's "submitted by" footer, `id`, `link`, `updated`, `published`, `title`, `category`). Every poster block and handle (`synthetic_user_NN`) is fictional and exists to prove the parser never reads it. Four posts: a road closure at Paldi cross roads and a crowd at Kankaria Lake (single social posts, held), a thank-you naming a fictional person, and a request with a fictional handle and e-mail address. The publisher is the fictional community `reddit.com/r/example_city` (never a real community: fabricated posts are not attributed to one). |
| `gdelt_doc_live.json` | **synthetic** | A replica of the GDELT DOC 2.0 ArtList JSON schema (`articles[]` with `url`, `url_mobile`, `title`, `seendate`, `socialimage`, `domain`, `language`, `sourcecountry`). Four general civic items from the fictional publishers, one in Hindi, with fictional names and an age; one item repeats a cue-introduced name without its cue (document-level name learning). |
| `gdelt_lastupdate_live.txt` | **synthetic** | A replica of GDELT's `lastupdate.txt`: it names `20261020120000.export.CSV.zip` with its real size and MD5; the mentions and GKG lines point at files that do not exist. Built by `../build_synthetic_gdelt.py`. |
| `20261020120000.export.CSV.zip` | **synthetic** | Three rows in the real 61-column GDELT 2.0 Events schema: an Ahmedabad row (district hint, ADM1 `IN09`), a Gandhinagar row inside the Gujarat bbox (state hint, `IN09`) and a Mumbai row (`IN16`, filtered out). The actor columns hold SENTINEL strings the parser must never read. Built by `../build_synthetic_gdelt.py`; `--check` verifies it. |

## Designed outcome

Parsed by the connectors: `sachet_cap` 10, `google_news_rss` 8, `gdelt_events` 2, `gdelt_doc` 4, `reddit_rss` 4
(28 signals, `pii_redactions` > 0). Through the full pipeline (`osint_analysis.run_pipeline` with the `osint_geo`
resolver) it is designed to give **exactly 3 surfaced situations**:

1. the SG Highway crash near Karnavati Club: four collision reports from two independent fictional publishers
   plus the "beaten by mob" conflict report → one correlated `affray+collision` at segment 1045,
   `SIMULATED`;
2. the robbery at Odhav Ring Road Circle (junction 11), `reported_crime`, a single (simulated) news source;
3. the SACHET Ahmedabad district alert (area-level, `OFFICIAL-VERIFIED`, one source).

Held: the two single social posts (aggregate-only rule), the 9 state-wide nowcasts as `outside_city` (plan R28),
and the general items as not an event class. No `crime_incident` anywhere.

Every publisher ends in `.example`, is the fictional `reddit.com/r/example_city`, or is `sachet.ndma.gov.in`. No real person's
name appears in any file here.
