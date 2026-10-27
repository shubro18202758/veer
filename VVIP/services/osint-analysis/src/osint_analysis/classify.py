"""Classify a signal into a fine situation class and a Veer kind (OSINT SPEC §1.6, §2.1; GEOSPATIAL_AND_DSS §A10).

Events are about PLACES and SITUATIONS, never persons. Reported crime enters only from REPORTED TEXT, as a
situation for RESPONSE (``reported_crime`` or ``public_disorder``), and OSINT never emits ``crime_incident``
(ANPR/watchlist origin) or ``vehicle_pursuit`` (human-initiated): :func:`_final_check` raises on either, whatever
a row, an exemplar or a future edit says, and :class:`~osint_common.types.Classification` refuses both again.

The rules, in order:

1. **The SACHET rule.** An official CAP alert (``sachet_cap``; ``imd`` alerts reach Veer the same way) is a
   flood situation (``urban_flooding`` / ``waterlogging`` / ``flooding``) when it carries a flood word, and an
   honest ``weather_hazard`` / ``hazard`` otherwise, whose subtype names the alert's own event
   (:func:`cap_subtype`: ``rain``, ``thunderstorm``, ``heat``, ... from ``cap_event`` or the text, else
   ``weather_advisory``): a light-rain nowcast is neither a flood nor a storm.
2. **The PoC lexicon**, :data:`CLASS_LEXICON`, in its order, first matching row wins; ``matched_terms`` lists
   every keyword of that row found in the title and text. The text is read through :func:`normalize_text` (NFKC,
   format characters dropped, poster handles stripped, whitespace collapsed, lower-cased), and a keyword matches a
   WHOLE word (:func:`keyword_forms`):

   * the keyword itself or a regular inflection of its last word: ``-s``, ``-es``, ``-ed``, ``-d``, ``-ing``, a
     final ``y`` as ``-ies``/``-ied``, a doubled final consonant (``mobs``, ``mobbed``, ``crashes``, ``looted``,
     ``robberies``), so ``mob`` never matches "mobile", ``strike`` never "striker", ``toxic`` never "toxicology";
   * the derived words of :data:`DERIVED_FORMS`, each with its plural: the agent nouns the PoC's substring test
     caught ("protesters", "looters", "chain snatchers", "brawlers", "marchers") and a few derived nouns
     ("gas leakage", "oil spillage"), found by checking every keyword against a dictionary;
   * a noun of :data:`NOUN_KEYWORDS` takes a plural only (``concerts``, never "concerted"; ``fairs``, never
     "fairly");
   * a stem of :data:`STEM_KEYWORDS` matches any continuation (``waterlogged``, ``inundation``, ``flooded``,
     ``heavy rainfall``) except the listed ones ("floodlights" are not a flood);
   * two context rules (:data:`CONTEXT_RULES`): the month ("by March", "March 15") is not a ``march``, and a
     "lightning strike" is weather, not a ``strike``.

   On the PoC's 107 signals this classifies exactly as the PoC's plain substring test did.

   **Poster handles are never a cue** (ethics rule 2: a handle is never stored, shown, tracked or scored).
   :func:`strip_handles` removes Reddit's ``submitted by /u/<name> [link] [comments]`` trailer, any other
   ``/u/<name>``, ``u/<name>`` or ``reddit.com/user/<name>``, and the ``[link]``/``[comments]`` boilerplate inside
   :func:`normalize_text`, so a handle never classifies a post ("/u/crash-test-kid" is not a road accident), never
   adds a similarity token (two posts by one poster are not more alike than two posts by two posters) and never
   reaches an embedder.
3. **Zero-shot fallback** (optional, off without an :class:`~osint_common.pipeline.Embedder`): a lexicon miss
   from an official or news tier is compared with one exemplar sentence per class; the nearest class wins when
   its cosine is at least :data:`ZERO_SHOT_MIN_COSINE` and leads the runner-up by :data:`ZERO_SHOT_MIN_MARGIN`.
   ``matched_terms`` is then ``["zero-shot"]``, so the provenance of the class stays visible. Social posts are
   never zero-shot classified: a social signal gets an event class only from an explicit lexicon cue.
4. Otherwise ``general_news``: not an event, never surfaced.

``veer_incident_kind`` stays inside ``traffic.incidents.incident_kind`` as relaxed by migration 021, which added
``robbery``, ``road_rage`` and ``public_disorder`` for exactly these rows (the PoC used ``other`` and ``protest``
because the CHECK did not allow them yet).
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Callable, Mapping, Sequence
from types import MappingProxyType
from typing import NamedTuple

import numpy as np

from osint_common.pipeline import Embedder
from osint_common.types import Classification, RawOsintSignal

__all__ = [
    "CAP_FLOOD_TERMS",
    "CAP_SOURCES",
    "CAP_SUBTYPES",
    "CLASS_LABELS",
    "CLASS_LEXICON",
    "CONTEXT_RULES",
    "DERIVED_FORMS",
    "FORBIDDEN_OSINT_KINDS",
    "NOUN_KEYWORDS",
    "STEM_KEYWORDS",
    "LexiconRow",
    "ZERO_SHOT_EXEMPLARS",
    "ZERO_SHOT_MIN_COSINE",
    "ZERO_SHOT_MIN_MARGIN",
    "ZERO_SHOT_TERM",
    "ZERO_SHOT_TIERS",
    "cap_subtype",
    "classify",
    "classify_with_vectors",
    "default_row",
    "exemplar_texts",
    "keyword_forms",
    "keyword_matches",
    "lexicon_classify",
    "normalize_text",
    "similarity_text",
    "strip_handles",
    "zero_shot",
    "zero_shot_eligible",
]


class LexiconRow(NamedTuple):
    """One classifier row: the class, its fine subtype, the Veer kinds it maps to, and its cue keywords."""

    event_class: str
    subtype: str
    veer_event_kind: str
    veer_incident_kind: str
    keywords: tuple[str, ...]


#: The PoC's ``CLASS_LEXICON`` (veer_osint_poc.py), rows and keywords in the PoC's order; first match wins. Only
#: the incident kinds of the first three rows changed: migration 021 added ``robbery``, ``road_rage`` and
#: ``public_disorder`` to ``traffic.incidents`` for them.
CLASS_LEXICON: tuple[LexiconRow, ...] = (
    LexiconRow(
        "reported_crime",
        "daylight_robbery",
        "reported_crime",
        "robbery",
        (
            "robbery", "robbed", "loot", "looted", "chain snatch", "snatching", "dacoity", "mugging", "burglary",
            "heist", "gunpoint", "theft at", "atm break",
        ),
    ),
    LexiconRow(
        "reported_crime",
        "road_rage",
        "reported_crime",
        "road_rage",
        ("road rage", "beaten on road", "attacked motorist", "thrashed", "assault after"),
    ),
    LexiconRow(
        "public_conflict",
        "affray",
        "public_disorder",
        "public_disorder",
        (
            "clash", "brawl", "scuffle", "stone pelting", "stone-pelting", "mob", "beaten by mob", "communal tension",
            "group fight", "violence erupted", "locals thrash",
        ),
    ),
    LexiconRow(
        "road_accident",
        "collision",
        "road_accident",
        "accident",
        (
            "accident", "road accident", "crash", "collision", "hit-and-run", "hit and run", "overturned", "rammed",
            "mishap", "vehicles collided", "truck overturn", "hits three", "hits 3", "multi-vehicle", "multi vehicle",
        ),
    ),
    LexiconRow(
        "fire",
        "structure_fire",
        "hazard",
        "other",
        (
            "fire broke", "fire breaks", "blaze", "gutted", "fire at", "massive fire", "caught fire", "fire brigade",
            "flames",
        ),
    ),
    LexiconRow(
        "urban_flooding",
        "waterlogging",
        "flooding",
        "weather",
        (
            "waterlog", "water-log", "water logg", "flood", "inundat", "submerg", "knee-deep", "heavy rain",
            "downpour", "rain fury", "deluge",
        ),
    ),
    LexiconRow(
        "infra_failure",
        "collapse",
        "infra_failure",
        "route_blockage",
        (
            "bridge collapse", "building collapse", "wall collapse", "slab collapse", "road caved", "cave-in",
            "gas leak", "power outage", "transformer blast",
        ),
    ),
    LexiconRow(
        "hazard",
        "spill",
        "hazard",
        "other",
        ("chemical spill", "gas leak", "hazardous", "toxic", "oil spill", "leakage"),
    ),
    LexiconRow(
        "public_gathering",
        "mass_gathering",
        "mass_gathering",
        "crowd_surge",
        (
            "rally", "gathering", "huge crowd", "mela", "fair", "concert", "festival crowd", "jam packed",
            "devotees",
        ),
    ),
    LexiconRow(
        "procession",
        "procession",
        "procession",
        "other",
        ("procession", "yatra", "rath yatra", "shobha yatra", "march"),
    ),
    LexiconRow(
        "unrest",
        "protest",
        "public_disorder",
        "protest",
        ("protest", "agitation", "demonstration", "bandh", "dharna", "strike", "gherao"),
    ),
    LexiconRow(
        "road_closure",
        "closure",
        "work_zone",
        "route_blockage",
        (
            "road closed", "diversion", "roadblock", "traffic diverted", "lane closure", "metro work", "dug up",
            "route changed", "closed for",
        ),
    ),
    LexiconRow(
        "weather_hazard",
        "storm",
        "hazard",
        "weather",
        (
            "thunderstorm", "lightning", "cyclone", "heatwave", "heat wave", "cold wave", "rainfall warning",
            "weather warning", "squall",
        ),
    ),
)

#: Official CAP alert feeds the SACHET rule classifies (IMD and SDMA alerts reach Veer through SACHET).
CAP_SOURCES: frozenset[str] = frozenset({"sachet_cap", "imd"})
#: The PoC's flood words for a CAP alert.
CAP_FLOOD_TERMS: tuple[str, ...] = (
    "flood", "waterlog", "inundat", "heavy rain", "very heavy", "extremely heavy", "submerg",
)
_CAP_FLOOD = LexiconRow("urban_flooding", "waterlogging", "flooding", "weather", CAP_FLOOD_TERMS)
_CAP_WEATHER = LexiconRow("weather_hazard", "weather_advisory", "hazard", "weather", ())
#: The subtype of a non-flood CAP alert, from its ``<event>`` (``raw.cap_event``) first, else its text: first match
#: wins, most severe first (F-HONEST OSINT-7: every such alert used to be "storm", a light-rain nowcast included).
#: Nothing matched: ``weather_advisory``.
CAP_SUBTYPES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("cyclone", ("cyclone", "cyclonic", "depression")),
    ("thunderstorm", ("thunderstorm", "thunder", "lightning", "squall", "hailstorm", "hail")),
    ("dust_storm", ("dust storm", "duststorm", "dust raising")),
    ("heat", ("heat wave", "heatwave", "heat", "hot and humid", "warm night")),
    ("cold", ("cold wave", "coldwave", "cold day", "frost")),
    ("fog", ("fog",)),
    ("strong_wind", ("strong wind", "gusty wind", "high wind", "surface wind")),
    ("rain", ("rain", "rainfall", "drizzle", "shower")),
)
_CAP_SUBTYPE_RES: tuple[tuple[str, tuple[re.Pattern[str], ...]], ...] = tuple(
    (sub, tuple(re.compile(rf"(?<![a-z]){re.escape(t)}(?:s|y)?(?![a-z])") for t in terms))
    for sub, terms in CAP_SUBTYPES
)


def cap_subtype(signal: RawOsintSignal) -> str:
    """A non-flood CAP alert's honest subtype (:data:`CAP_SUBTYPES`): its ``cap_event`` first, else its text."""
    event = signal.raw.get("cap_event") if isinstance(signal.raw.get("cap_event"), str) else None
    for hay in (event, f"{signal.title} {signal.text}"):
        if not hay:
            continue
        low = normalize_text(hay)
        for sub, patterns in _CAP_SUBTYPE_RES:
            if any(rx.search(low) for rx in patterns):
                return sub
    return "weather_advisory"

#: Never from OSINT: ``crime_incident`` is ANPR/watchlist origin, a pursuit is human-initiated.
FORBIDDEN_OSINT_KINDS: frozenset[str] = frozenset({"crime_incident", "vehicle_pursuit"})

#: Sentence-case labels for the situation label ``"<class label> · <place>"`` (C-T).
CLASS_LABELS: Mapping[str, str] = MappingProxyType(
    {
        "reported_crime": "Reported crime",
        "public_conflict": "Public conflict",
        "road_accident": "Road accident",
        "fire": "Fire",
        "urban_flooding": "Urban flooding",
        "infra_failure": "Infrastructure failure",
        "hazard": "Hazard",
        "public_gathering": "Public gathering",
        "procession": "Procession",
        "unrest": "Unrest",
        "road_closure": "Road closure",
        "weather_hazard": "Weather hazard",
        "general_news": "General news",
    }
)

#: One neutral exemplar per class for the zero-shot fallback: situations at places, no person, no name.
ZERO_SHOT_EXEMPLARS: Mapping[str, str] = MappingProxyType(
    {
        "reported_crime": "A robbery or theft was reported at a shop or on a street in the city.",
        "public_conflict": "A clash broke out between groups at a junction and stones were pelted.",
        "road_accident": "A road accident: vehicles collided on the highway and people were injured.",
        "fire": "A fire broke out in a building and fire tenders were called to the spot.",
        "urban_flooding": "Heavy rain left roads waterlogged and underpasses flooded.",
        "infra_failure": "A bridge, wall or building collapsed, or a major power outage hit the area.",
        "hazard": "A chemical spill or a gas leak was reported at an industrial site.",
        "public_gathering": "A huge crowd gathered for a festival, a fair or a rally.",
        "procession": "A religious procession moved along the main road.",
        "unrest": "A protest, a bandh or a demonstration was held in the city.",
        "road_closure": "The road was closed and traffic was diverted for construction work.",
        "weather_hazard": "A thunderstorm, lightning or heat wave warning was issued for the area.",
    }
)
_EXEMPLAR_CLASSES: tuple[str, ...] = tuple(ZERO_SHOT_EXEMPLARS)
_EXEMPLAR_TEXTS: tuple[str, ...] = tuple(ZERO_SHOT_EXEMPLARS.values())
#: The nearest exemplar must be at least this close (cosine of unit vectors) ...
ZERO_SHOT_MIN_COSINE = 0.55
#: ... and lead the runner-up by at least this much, or the signal stays ``general_news``. Both are starting
#: values, not calibrated against bge-m3 in this WP (the embedding host is live-only, and today's service has no
#: read-only ``/embed`` route); the fallback is off unless an embedder is passed.
ZERO_SHOT_MIN_MARGIN = 0.03
#: The tiers whose lexicon misses may be zero-shot classified (never ``social_unverified``).
ZERO_SHOT_TIERS: frozenset[str] = frozenset({"official", "news_wire", "news_regional", "aggregator", "archive"})
ZERO_SHOT_TERM = "zero-shot"

_WS = re.compile(r"\s+")
_QUOTES = str.maketrans({"‘": "'", "’": "'", "“": '"', "”": '"'})

#: A Reddit account name (3-20 characters today; any length is taken, so a long one is never left half-stripped).
_HANDLE_NAME = r"[A-Za-z0-9_-]{3,}"
#: A poster handle as it is written: a profile link (``reddit.com/user/<name>``, ``…/u/<name>``, with or without
#: the scheme and a subdomain), ``/u/<name>`` or a bare ``u/<name>`` (never inside a word or a path: "menu/item"
#: and "u/s 302", Indian legal shorthand for "under section", are left alone).
_HANDLE_PATTERN = (
    r"(?:(?:https?://)?(?:[\w-]+\.)*reddit\.com/(?:u|user)/" + _HANDLE_NAME + r"/?"
    r"|(?<![\w/])/?u/" + _HANDLE_NAME + r")"
)
_BOILERPLATE_PATTERN = r"\[(?:link|comments)\]"
_HANDLE = re.compile(_HANDLE_PATTERN, re.IGNORECASE)
_BOILERPLATE = re.compile(_BOILERPLATE_PATTERN, re.IGNORECASE)
#: Reddit's RSS trailer "submitted by /u/<name> [link] [comments]" (or with ``[PERSON]`` where parse redacted the
#: name), with the separator before it. "submitted by" alone is taken only when a handle, ``[PERSON]``, the
#: boilerplate or the end of the text follows it: "a petition submitted by March 15" is left alone.
_TRAILER = re.compile(
    r"(?:\s*[,;:|–—-])?\s*\bsubmitted\s+by\s*(?:(?:" + _HANDLE_PATTERN + r"|\[person\])(?:\s*"
    + _BOILERPLATE_PATTERN + r")*|(?:" + _BOILERPLATE_PATTERN + r"\s*)+|$)",
    re.IGNORECASE,
)


def strip_handles(text: str, replacement: str = " ") -> str:
    """A text without poster handles (ethics rule 2): the ``submitted by <handle> [link] [comments]`` trailer and
    the ``[link]``/``[comments]`` boilerplate are dropped, and every other handle becomes ``replacement`` (a space
    for the analysis view, ``[PERSON]`` for a text that leaves the pipeline). The one helper both views use; an
    unchanged text is returned as it was, a changed one without the spaces left at its ends."""
    out = _TRAILER.sub(" ", text)
    out = _HANDLE.sub(replacement, out)
    out = _BOILERPLATE.sub(" ", out)
    return text if out == text else out.strip()


def normalize_text(text: str | None) -> str:
    """NFKC, format characters (zero-width, soft hyphen) dropped, curly quotes straightened, poster handles stripped
    (:func:`strip_handles`), whitespace collapsed, lower-cased: the one text view every classifier, similarity and
    embedder rule reads."""
    s = unicodedata.normalize("NFKC", text or "")
    s = "".join(ch for ch in s if unicodedata.category(ch) != "Cf").translate(_QUOTES)
    return _WS.sub(" ", strip_handles(s)).strip().lower()


#: Stems: the keyword matches at the start of a word, whatever follows ("waterlogged", "inundation", "submerged",
#: "flooded", "heavy rainfall") — except the continuations listed with it ("floodlights", "floodlit").
STEM_KEYWORDS: Mapping[str, tuple[str, ...]] = MappingProxyType(
    {
        "waterlog": (),
        "water-log": (),
        "water logg": (),
        "inundat": (),
        "submerg": (),
        "flood": ("light", "lit"),
        "heavy rain": (),
    }
)
#: Nouns (and an adjective) whose verb-like endings are other words: a plural only ("concerts", never "concerted";
#: "fairs", never "fairing").
NOUN_KEYWORDS: frozenset[str] = frozenset({"concert", "fair", "mela", "toxic"})
#: Derived words a keyword also matches, each with its plural (``-s``/``-es``). They are the words the PoC's plain
#: substring test caught and a whole-word rule would miss, found by testing every keyword against a dictionary:
#: the agent nouns ("protesters block the highway", "looters target a shop", "chain snatchers strike again") and a
#: few derived nouns ("gas leakage" keeps the PoC's first match, infra_failure). Deliberately absent, because the
#: substring test was wrong there: "striker(s)" (a footballer), "mobile"/"mobster" (``mob``), "accidental" (an
#: "accidental fire" is a fire), "blazer", "Protestant", "protestations", "metro workers" (not a work zone),
#: "toxicology".
DERIVED_FORMS: Mapping[str, tuple[str, ...]] = MappingProxyType(
    {
        "loot": ("looter",),
        "chain snatch": ("chain snatcher",),
        "snatching": ("snatcher",),
        "brawl": ("brawler",),
        "gas leak": ("gas leakage",),
        "chemical spill": ("chemical spillage",),
        "oil spill": ("oil spillage",),
        "rally": ("rallyist",),
        "procession": ("processional",),
        "march": ("marcher",),
        "protest": ("protester", "protestor"),
    }
)

_ENDINGS = ("", "s", "es", "ed", "d", "ing")
_PLURAL_ENDINGS = ("", "s", "es")
_VOWELS = frozenset("aeiou")
_PREVIOUS_WORD = re.compile(r"(\w+)\W*$")
_LEADING_NUMBER = re.compile(r"[\s,\-]*\d")
#: Words before "march" that make it the month ("by March", "in March", "mid-March", "end of March").
_MONTH_CUES: frozenset[str] = frozenset(
    {
        "in", "by", "since", "until", "till", "from", "of", "this", "next", "last", "early", "mid", "late", "end",
        "before", "after", "during", "through", "throughout",
    }
)
#: Words before "strike" that make it something other than a labour strike.
_NOT_A_STRIKE: frozenset[str] = frozenset({"lightning", "air"})


def _previous_word(hay: str, start: int) -> str:
    found = _PREVIOUS_WORD.search(hay[max(0, start - 48) : start])
    return found.group(1) if found else ""


def _not_the_month(hay: str, m: re.Match[str]) -> bool:
    """``march`` is a march unless it is the month: an inflected form ("marched") always is the verb; the bare word
    is the month after a month cue ("by March") or before a day or a year ("March 15", "March 2027")."""
    if m.group(0) != "march":
        return True
    if _previous_word(hay, m.start()) in _MONTH_CUES:
        return False
    return _LEADING_NUMBER.match(hay, m.end()) is None


def _not_a_lightning_strike(hay: str, m: re.Match[str]) -> bool:
    """A "lightning strike" (or an "air strike") is not a labour strike."""
    return _previous_word(hay, m.start()) not in _NOT_A_STRIKE


#: Keywords that also need their context (each occurrence is checked; one good occurrence is a match).
CONTEXT_RULES: Mapping[str, Callable[[str, re.Match[str]], bool]] = MappingProxyType(
    {"march": _not_the_month, "strike": _not_a_lightning_strike}
)


def _doubles(word: str) -> bool:
    """A last syllable consonant-vowel-consonant doubles its consonant before ``-ed``/``-ing`` ("mob" → "mobbed")."""
    return (
        len(word) >= 2
        and word[-1].isalpha()
        and word[-1] not in _VOWELS
        and word[-1] not in "wxy"
        and word[-2] in _VOWELS
        and (len(word) < 3 or word[-3] not in _VOWELS)
    )


def keyword_forms(keyword: str) -> tuple[str, ...]:
    """The whole-word forms a (non-stem) keyword matches: itself, the regular inflections of its last word and its
    :data:`DERIVED_FORMS` with their plurals (see the module docstring), longest first. A keyword ending in a digit
    or a sign matches only itself."""
    k = normalize_text(keyword)
    if not k or not k[-1].isalpha():
        return (k,)
    noun = keyword in NOUN_KEYWORDS
    forms = {k + e for e in (_PLURAL_ENDINGS if noun else _ENDINGS)}
    last = k.rsplit(" ", 1)[-1]
    if len(last) >= 2 and last[-1] == "y" and last[-2] not in _VOWELS:
        forms.add(k[:-1] + "ies")
        if not noun:
            forms.add(k[:-1] + "ied")
    if not noun and _doubles(last):
        forms.update({k + k[-1] + "ed", k + k[-1] + "ing"})
    for derived in DERIVED_FORMS.get(keyword, ()):
        forms.update(normalize_text(derived) + e for e in _PLURAL_ENDINGS)
    return tuple(sorted(forms, key=lambda f: (-len(f), f)))


def _keyword_re(keyword: str) -> re.Pattern[str]:
    """A whole-word match of the keyword's forms; a stem matches the start of a word (bar its exclusions)."""
    k = normalize_text(keyword)
    if keyword in STEM_KEYWORDS:
        never = "".join(f"(?!{re.escape(x)})" for x in STEM_KEYWORDS[keyword])
        return re.compile(r"(?<!\w)" + re.escape(k) + never)
    return re.compile(r"(?<!\w)(?:" + "|".join(re.escape(f) for f in keyword_forms(keyword)) + r")(?!\w)")


def _matches(keyword: str, rx: re.Pattern[str], hay: str) -> bool:
    rule = CONTEXT_RULES.get(keyword)
    if rule is None:
        return rx.search(hay) is not None
    return any(rule(hay, m) for m in rx.finditer(hay))


_COMPILED: tuple[tuple[LexiconRow, tuple[tuple[str, re.Pattern[str]], ...]], ...] = tuple(
    (row, tuple((kw, _keyword_re(kw)) for kw in row.keywords)) for row in CLASS_LEXICON
)
_CAP_FLOOD_RES: tuple[tuple[str, re.Pattern[str]], ...] = tuple((t, _keyword_re(t)) for t in CAP_FLOOD_TERMS)


def keyword_matches(keyword: str, text: str) -> bool:
    """Whether one lexicon keyword matches ``text`` under the rules above (the text is normalised here)."""
    return _matches(keyword, _keyword_re(keyword), normalize_text(text))


def _final_check(veer_event_kind: str | None) -> None:
    """The last gate of every classification: OSINT never emits crime_incident (nor vehicle_pursuit)."""
    if veer_event_kind in FORBIDDEN_OSINT_KINDS:
        raise ValueError(
            f"OSINT must never emit {veer_event_kind}: crime_incident is ANPR/watchlist origin and a pursuit is "
            "human-initiated; a reported crime is reported_crime (or public_disorder) for RESPONSE"
        )


def _from_row(row: LexiconRow, matched: Sequence[str]) -> Classification:
    _final_check(row.veer_event_kind)
    return Classification(
        event_class=row.event_class,  # type: ignore[arg-type]
        subtype=row.subtype,
        veer_event_kind=row.veer_event_kind,  # type: ignore[arg-type]
        veer_incident_kind=row.veer_incident_kind,  # type: ignore[arg-type]
        matched_terms=list(matched)[:64],
    )


def default_row(event_class: str) -> LexiconRow | None:
    """The first lexicon row of a class: its subtype and kinds are the class's defaults (zero-shot)."""
    for row in CLASS_LEXICON:
        if row.event_class == event_class:
            return row
    return None


def lexicon_classify(signal: RawOsintSignal) -> Classification:
    """Rules 1, 2 and 4 of the module docstring: the SACHET rule, then the lexicon, else ``general_news``."""
    hay = normalize_text(f"{signal.title} {signal.text}")
    if signal.source in CAP_SOURCES:
        if any(_matches(term, rx, hay) for term, rx in _CAP_FLOOD_RES):
            return _from_row(_CAP_FLOOD, ["CAP:flood"])
        return _from_row(_CAP_WEATHER._replace(subtype=cap_subtype(signal)), ["CAP:weather"])
    for row, patterns in _COMPILED:
        hits = [kw for kw, rx in patterns if _matches(kw, rx, hay)]
        if hits:
            return _from_row(row, hits)
    return Classification(event_class="general_news")


def similarity_text(signal: RawOsintSignal, limit: int = 1000) -> str:
    """The text an embedder sees for a signal: its (already redacted) title and text, normalised (no poster handle,
    no Reddit boilerplate) and bounded."""
    title = normalize_text(signal.title)
    text = normalize_text(signal.text)
    body = text if text.startswith(title) else f"{title}. {text}"
    return body[:limit]


def zero_shot_eligible(signal: RawOsintSignal) -> bool:
    """Only official and news tiers are zero-shot classified; never a social post, never a CAP alert."""
    return signal.source_tier in ZERO_SHOT_TIERS and signal.source not in CAP_SOURCES


def zero_shot(vector: np.ndarray, exemplars: np.ndarray) -> tuple[str, float] | None:
    """The nearest exemplar class of a unit vector, or ``None`` when it is not close or not clearly ahead."""
    if exemplars.shape[0] != len(_EXEMPLAR_CLASSES) or vector.shape[-1] != exemplars.shape[-1]:
        return None
    sims = exemplars @ vector
    order = np.argsort(-sims, kind="stable")
    best = float(sims[order[0]])
    second = float(sims[order[1]]) if len(order) > 1 else -1.0
    if best < ZERO_SHOT_MIN_COSINE or best - second < ZERO_SHOT_MIN_MARGIN:
        return None
    return _EXEMPLAR_CLASSES[int(order[0])], best


def _zero_shot_classification(vector: np.ndarray, exemplars: np.ndarray) -> Classification | None:
    found = zero_shot(vector, exemplars)
    if found is None:
        return None
    row = default_row(found[0])
    if row is None:  # pragma: no cover - every exemplar class has a lexicon row (tests pin it)
        return None
    return _from_row(row, [ZERO_SHOT_TERM])


def classify_with_vectors(
    signal: RawOsintSignal, vector: np.ndarray | None = None, exemplars: np.ndarray | None = None
) -> Classification:
    """:func:`classify` with the embeddings already computed (the pipeline embeds everything in one call)."""
    found = lexicon_classify(signal)
    if found.event_class != "general_news" or vector is None or exemplars is None:
        return found
    if not zero_shot_eligible(signal):
        return found
    return _zero_shot_classification(vector, exemplars) or found


def exemplar_texts() -> tuple[str, ...]:
    """The zero-shot exemplar sentences, in :data:`ZERO_SHOT_EXEMPLARS` order."""
    return _EXEMPLAR_TEXTS


def classify(signal: RawOsintSignal, *, embedder: Embedder | None = None) -> Classification:
    """``classify(signal) -> Classification``: never ``crime_incident`` (the contract of OS-4).

    With an ``embedder``, a lexicon miss from an official or news tier gets the zero-shot fallback; an embedder
    that fails (``None`` or an exception) leaves the lexicon's answer.
    """
    found = lexicon_classify(signal)
    if found.event_class != "general_news" or embedder is None or not zero_shot_eligible(signal):
        return found
    from osint_analysis.embed import unit_vectors  # local: embed imports httpx, kept off the lexicon path

    vectors = unit_vectors(embedder, [similarity_text(signal), *_EXEMPLAR_TEXTS])
    if vectors is None:
        return found
    return _zero_shot_classification(vectors[0], vectors[1:]) or found
