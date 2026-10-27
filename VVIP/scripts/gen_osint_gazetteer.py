#!/usr/bin/env python3
"""gen_osint_gazetteer.py — Veer's offline OSINT place gazetteer (contract X19), rebuilt deterministically.

Writes ``scripts/data/osint_gazetteer.json``: the places the geo-resolver (``services/osint-geo``) can name, each
with its spellings, a point, an importance prior and, for the network's own features, its id. Places only: no
field outside the X19 list exists, and no person's name ever becomes a phrase on its own.

Inputs (all in the repo, offline):

* ``scripts/data/osm_network.json`` (read only; ``gen_osm_network.py`` owns it): the 34 ``corridor.junctions``
  (English and Gujarati names, OSM node points) and the 49 ``corridor.road_segments`` (road names, the OSM names
  along each, the stored line). © OpenStreetMap contributors, ODbL 1.0;
* the reviewed seed tables below: the PoC's 28 neighbourhoods and 16 landmarks (``build_gazetteer.py``'s ``SEED``,
  ported row for row: approximate city points, hand-placed and reviewable);
* ``osint_geo.translit``: the Gujarati and Hindi spellings and Latin variants.

What each entry's ``surface_forms`` hold (every form in the resolver's normal form, ``osint_geo.gazetteer.norm``):

* junction (ids 1-34, gaz_ids 1-34): its name, the name without the parenthesis ("Paldi Cross Roads"), the first
  word when it names the crossing itself ("shivranjani", "vaishnodevi"; never a generic, a common English word,
  another place the junction is only named after, an area or village it is named after, or a person's given name
  or surname: :data:`FIRST_WORD_DENY`), the
  Gujarati name with and without its parenthesis, its
  Latin transliteration (the PoC's ``GU_LATIN_SEED``) and their script aliases. No bare (single-word) form that
  names an area stays a junction's (F-HONEST OSINT-1): a neighbourhood's or landmark's form ("odhav", "paldi",
  "kalupur", "iskcon", "ellisbridge", in any script) or a word two junctions share ("motera"). A text naming only
  the area resolves to the area, never to a junction pin, and :func:`lint` refuses a build that breaks this. The
  superseded schematic names are
  NOT aliases: they are the pre-OSM labels, often of another place ("Usmanpura Junction" was Sola Cross Roads);
* road (segments 1001-1049, gaz_ids 35-83): its name, its base name, the OSM names along it — a linear name
  covering at least 10 % (and 100 m) or 200 m of it, a point-like name ("RTO Circle", "Parimal Cross Roads", a
  bridge the road runs over: "Fernandes Bridge") at any length unless it is a junction's own name; ``(unnamed)``,
  generic-only names ("Station Road": every city has
  one) and the few metres of another road where it touches the segment left out — the colloquial forms of SG
  Highway, CG Road and SP Ring Road, and their script aliases and Latin variants. Its point is the segment's
  anchor, ``ST_PointOnSurface`` of the line (``osint_geo.geom.interior_point``), where the oracle places the
  segment;
* neighbourhood and landmark (gaz_ids 84-127): the seed row's name and aliases, plus script aliases and variants,
  less the few PoC aliases that name more than one place (:data:`SEED_ALIAS_DENY`).

The gaz_ids, the importance priors and the seed points are the PoC's, so a regenerated file keeps every id. A lint
(:func:`lint`) refuses a build in which a multi-word phrase carries no place-type word or road code (the rule of
``osint-common``'s ``test_gazetteer_phrases_are_places_never_bare_person_names``), a form is not in normal form,
or a form is a bare generic word. ``generated_at`` is the OpenStreetMap extract time of the network it was built
from, so the same inputs give a byte-identical file.

Usage (the standard library alone: ``osint_geo.gazetteer``, ``translit`` and ``geom`` import nothing else, so any
Python 3.12 runs it, gates included; paths resolve from the repo root):

    python scripts/gen_osint_gazetteer.py            # build in memory, report counts and whether the file differs
    python scripts/gen_osint_gazetteer.py --check    # exit 1 when the committed file differs from a rebuild
    python scripts/gen_osint_gazetteer.py --write    # rewrite scripts/data/osint_gazetteer.json
    python scripts/gen_osint_gazetteer.py --overpass [--overpass-json FILE]
        # opt-in, never used by gates: list OSM place nodes in the city bbox that the gazetteer lacks, for a
        # reviewer to add to the seed table by hand (one Overpass request, or a saved response with --overpass-json)
"""

from __future__ import annotations

import argparse
import difflib
import json
import os
import re
import sys
import tempfile
import urllib.parse
import urllib.request
from collections import OrderedDict
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "services" / "osint-geo" / "src"))

from osint_geo import translit  # noqa: E402
from osint_geo.gazetteer import GENERIC_STOPWORDS, LICENCE, Gazetteer, norm  # noqa: E402
from osint_geo.geom import interior_point  # noqa: E402

NETWORK_JSON = REPO_ROOT / "scripts" / "data" / "osm_network.json"
OUT_JSON = REPO_ROOT / "scripts" / "data" / "osint_gazetteer.json"

#: The Ahmedabad bbox the seed points lie in (the PoC's), for the Overpass review.
BBOX = {"lat_min": 22.88, "lat_max": 23.17, "lon_min": 72.43, "lon_max": 72.77}

#: Road importance by OSM class (the PoC's priors).
ROAD_IMPORTANCE = {"trunk": 0.8, "primary": 0.7, "secondary": 0.55, "tertiary": 0.45}
#: A junction's importance: signalised 0.85, else 0.7 (the PoC's priors).
JUNCTION_IMPORTANCE = {True: 0.85, False: 0.7}

#: A linear OSM name (a road, flyover, underpass) becomes a road's alias when it covers at least this share of the
#: segment (and this length), or at least OSM_NAME_LONG_M of it: a few metres of another road where it touches the
#: segment ("Satellite Road", 16 m of SG Highway) would attach that road's reports to the wrong segment.
OSM_NAME_MIN_SHARE = 0.10
OSM_NAME_MIN_M = 100.0
OSM_NAME_LONG_M = 200.0
#: A point-like OSM name (a circle, cross roads, chowk, junction) marks a place ON the segment, so it is an alias at
#: any length ("RTO Circle", 28 m of the Chimanbhai Patel Flyover) unless it is one of the 34 junctions' own names.
#: A bridge is one too: the segment's own way runs over it ("Fernandes Bridge", 22 m of Gandhi Road). The singular
#: "cross road" is deliberately not: the one such name, "Astodia Darwaza cross road" (44 m of Kankaria Road, 26 m of
#: Sarangpur Road), is the crossing at junction 5, which the text already resolves to; as a road alias it would
#: split that place across two segments.
POINT_WORDS = frozenset({"circle", "chowk", "junction", "crossing", "chokdi", "bridge"})

#: First words of junction names that are NOT a place on their own: common English words, a generic or an
#: abbreviation, another place the junction is only named after, and the given names and surnames junctions are
#: named after (a person, never a place alias).
FIRST_WORD_DENY: dict[str, str] = {
    "income": "common word (Income Tax Circle)",
    "science": "common word (Science City Circle)",
    "helmet": "common word in traffic news (Helmet Cross Roads)",
    "pakwan": "common word, 'dish' (Pakwan Cross Roads)",
    "airport": "common word, any city's airport (Airport Circle); Ahmedabad's is junction 21 and landmark 120",
    "dehgam": "another place: the town of Dehgam, outside the city (Dehgam Circle is on the road to it)",
    "nehru": "a person's name (Nehru Bridge)",
    "gandhi": "a person's name (Gandhi Ashram Junction)",
    "indira": "a person's name (Indira Bridge)",
    "prahlad": "a given name (Prahlad Nagar Junction); 'prahlad nagar' is the place",
    "ellis": "a surname (Ellis Bridge East); 'ellis bridge' is the place",
    "bhat": "a common surname (Bhat Circle)",
    # F-HONEST OSINT-1: an area the junction is named after is not the crossing; a report naming only the area
    # ("in Sola", "Sarkhej police") is area-level, never a junction pin
    "sola": "an area (Sola: its civil hospital, its police station), not only the cross roads",
    "sarkhej": "an area (Sarkhej town, Sarkhej Roza), not only its ring-road junction",
    "koba": "a village (Koba), not only its circle",
    "aslali": "a village (Aslali), not only its circle",
    "astodia": "an area of the walled city (Astodia), not only its gate",
}

#: Colloquial road forms, by the road's base name.
COLLOQUIAL: dict[str, tuple[str, ...]] = {
    "sg highway": ("sg highway", "s g highway", "sarkhej gandhinagar highway"),
    "cg road": ("cg road", "c g road", "chimanlal girdharlal road"),
    "sp ring road": ("sp ring road", "s p ring road", "sardar patel ring road", "ring road"),
}

#: The PoC's hand-seeded neighbourhoods and landmarks (``build_gazetteer.py`` SEED, row for row, gaz_ids 84-127):
#: (canonical name, lat, lon, feature type, importance, aliases). Approximate city points, reviewable.
SEED_PLACES: tuple[tuple[str, float, float, str, float, tuple[str, ...]], ...] = (
    ("Navrangpura", 23.0366, 72.5611, "neighbourhood", 0.7, ("navrangpura",)),
    ("Satellite", 23.0300, 72.5170, "neighbourhood", 0.72, ("satellite", "satellite road area")),
    ("Maninagar", 22.9980, 72.6030, "neighbourhood", 0.72, ("maninagar",)),
    ("Paldi", 23.0110, 72.5660, "neighbourhood", 0.65, ("paldi",)),
    ("Bopal", 23.0330, 72.4700, "neighbourhood", 0.65, ("bopal",)),
    ("Naranpura", 23.0560, 72.5560, "neighbourhood", 0.62, ("naranpura",)),
    ("Vastrapur", 23.0380, 72.5260, "neighbourhood", 0.68, ("vastrapur", "vastrapur lake")),
    ("Bodakdev", 23.0400, 72.5100, "neighbourhood", 0.64, ("bodakdev",)),
    ("Thaltej", 23.0500, 72.5080, "neighbourhood", 0.64, ("thaltej",)),
    ("Chandkheda", 23.1100, 72.5850, "neighbourhood", 0.6, ("chandkheda",)),
    ("Naroda", 23.0700, 72.6600, "neighbourhood", 0.62, ("naroda",)),
    ("Vastral", 23.0100, 72.6500, "neighbourhood", 0.58, ("vastral",)),
    ("Ghatlodia", 23.0750, 72.5500, "neighbourhood", 0.6, ("ghatlodia",)),
    ("Sabarmati", 23.0850, 72.5800, "neighbourhood", 0.62, ("sabarmati",)),
    ("Memnagar", 23.0540, 72.5350, "neighbourhood", 0.58, ("memnagar",)),
    ("Gota", 23.1000, 72.5400, "neighbourhood", 0.58, ("gota",)),
    ("Nikol", 23.0470, 72.6650, "neighbourhood", 0.56, ("nikol",)),
    ("Ranip", 23.0870, 72.5700, "neighbourhood", 0.56, ("ranip",)),
    ("Ambawadi", 23.0200, 72.5550, "neighbourhood", 0.6, ("ambawadi",)),
    ("Ellisbridge", 23.0225, 72.5712, "neighbourhood", 0.64, ("ellisbridge", "ellis bridge")),
    ("Vejalpur", 23.0000, 72.5200, "neighbourhood", 0.58, ("vejalpur",)),
    ("Prahlad Nagar", 22.9991, 72.5009, "neighbourhood", 0.64, ("prahlad nagar", "prahladnagar")),
    (
        "Karnavati Club (SG Highway)", 23.0090, 72.5030, "landmark", 0.7,
        ("karnavati", "karnavati club", "karnavati 4 roads", "karnavati four roads", "karnavati circle"),
    ),
    ("Usmanpura", 23.0470, 72.5720, "neighbourhood", 0.56, ("usmanpura",)),
    ("Vadaj", 23.0640, 72.5720, "neighbourhood", 0.54, ("vadaj",)),
    ("Shahibaug", 23.0630, 72.5970, "neighbourhood", 0.6, ("shahibaug", "shahibag")),
    ("Odhav", 23.0250, 72.6730, "neighbourhood", 0.56, ("odhav",)),
    ("Jamalpur", 23.0130, 72.5820, "neighbourhood", 0.56, ("jamalpur",)),
    ("Kankaria Lake", 22.9950, 72.6020, "landmark", 0.78, ("kankaria", "kankaria lake", "kankariya")),
    (
        "Narendra Modi Stadium (Motera)", 23.0920, 72.5972, "landmark", 0.82,
        ("narendra modi stadium", "motera stadium", "motera cricket stadium", "sardar patel stadium"),
    ),
    (
        "Sabarmati Riverfront", 23.0300, 72.5800, "landmark", 0.76,
        ("sabarmati riverfront", "riverfront", "sabarmati river front"),
    ),
    ("ISKCON Temple", 23.0272, 72.5070, "landmark", 0.7, ("iskcon", "iskcon temple")),
    ("Law Garden", 23.0230, 72.5620, "landmark", 0.72, ("law garden",)),
    ("Manek Chowk", 23.0250, 72.5890, "landmark", 0.72, ("manek chowk", "manekchowk")),
    ("Bhadra Fort", 23.0255, 72.5850, "landmark", 0.66, ("bhadra fort", "bhadra")),
    ("Sabarmati Ashram (Gandhi Ashram)", 23.0608, 72.5806, "landmark", 0.74, ("sabarmati ashram", "gandhi ashram")),
    (
        "SVP International Airport", 23.0772, 72.6347, "landmark", 0.8,
        ("svp airport", "ahmedabad airport", "sardar vallabhbhai patel airport", "svpia"),
    ),
    ("Civil Hospital Asarwa", 23.0550, 72.6050, "landmark", 0.76, ("civil hospital", "asarwa civil hospital")),
    ("Gujarat University", 23.0370, 72.5450, "landmark", 0.66, ("gujarat university",)),
    ("GMDC Ground", 23.0380, 72.5420, "landmark", 0.64, ("gmdc ground", "gmdc")),
    (
        "Kalupur Railway Station", 23.0276, 72.6010, "landmark", 0.76,
        ("kalupur", "kalupur station", "ahmedabad railway station", "ahmedabad junction"),
    ),
    ("Teen Darwaja", 23.0245, 72.5870, "landmark", 0.64, ("teen darwaja", "teen darwaza")),
    ("Riverfront Flower Park", 23.0180, 72.5790, "landmark", 0.5, ("flower park",)),
    ("Adalaj", 23.1660, 72.5810, "neighbourhood", 0.5, ("adalaj",)),
)
#: Seed aliases of the PoC that are not carried, with the reason: a name of more than one place is no alias (the
#: seed table above stays the PoC's, row for row). Names that are a place only in a text about the city stay
#: aliases and are gated by the resolver instead (``osint_geo.resolver.CONTEXT_FORMS``).
SEED_ALIAS_DENY: dict[str, str] = {
    "sardar patel stadium": "two stadiums in the city: Motera's under its old name and Navrangpura's",
}

#: Words that make a multi-word phrase a PLACE (mirrors osint-common's lint): a place type, or a generic place word.
PLACE_TYPE_WORDS = frozenset(
    {
        "road", "roads", "highway", "circle", "junction", "bridge", "flyover", "underpass", "overbridge", "ramp",
        "cross", "chowk", "ring", "marg", "station", "railway", "metro", "airport", "market", "temple", "ashram",
        "university", "college", "school", "hospital", "club", "stadium", "riverfront", "river", "front", "lake",
        "garden", "park", "fort", "darwaja", "darwaza", "gate", "nagar", "zone", "ward", "district", "city",
        "state", "ahmedabad", "gujarat", "india", "amdavad", "gandhinagar", "brts", "amc", "iim", "iskcon", "svp",
        "gmdc",
    }
)
_ROAD_CODE = re.compile(r"(?:nh|ne|sh)\d+")
#: Reviewed multi-word phrases with no place-type word (osint-common's ``_REVIEWED_PHRASES``): two places side by
#: side in a road's name ("Sarangpur Road (Kalupur–Astodia)").
REVIEWED_PHRASES = frozenset({"kalupur astodia"})

_PARENS = re.compile(r"\s*\(.*?\)\s*")


def _base(name: str) -> str:
    """A name without its parenthesised part ("Paldi Cross Roads (Ashram Road - CG Road)" → "Paldi Cross Roads")."""
    return _PARENS.sub(" ", name).strip()


def _good(form: str) -> bool:
    """A form worth carrying: three characters or more, not only generic words."""
    return len(form) >= 3 and not all(t in GENERIC_STOPWORDS for t in form.split(" "))


def _expand(forms: list[str]) -> list[str]:
    """Each Latin form plus its script aliases and Latin variants (``osint_geo.translit``). A form dropped as
    generic ("station road": every city has one) brings no alias either, so the scripts never say more than the
    Latin does."""
    out = list(forms)
    for f in forms:
        n = norm(f)
        if not (n and _good(n)):
            continue
        out.extend(translit.script_aliases(n))
        out.extend(translit.latin_variants(n))
    return out


def _finish(forms: list[str]) -> list[str]:
    return sorted({n for n in (norm(f) for f in forms) if n and _good(n)})


def junction_forms(j: dict[str, Any], area_forms: frozenset[str] = frozenset()) -> list[str]:
    """A junction's forms (module docstring), less every bare single-word form in ``area_forms``: the forms of the
    neighbourhoods and landmarks, and the bare words two junctions share (F-HONEST OSINT-1: "Odhav" is the
    neighbourhood, never the Odhav Ring Road Circle pin; "Motera" names two junctions and the stadium area)."""
    return [f for f in _junction_forms(j) if " " in f or f not in area_forms]


def _junction_forms(j: dict[str, Any]) -> list[str]:
    name = j["name"]
    base = _base(name)
    forms = [name, base]
    first = norm(base).split(" ")[0] if norm(base) else ""
    if len(first) >= 4 and first not in GENERIC_STOPWORDS and first not in FIRST_WORD_DENY:
        forms.append(first)
    gu = j.get("name_gu") or ""
    if gu:
        forms += [gu, _base(gu)]
        latin = translit.to_latin(_base(gu))
        if latin:
            forms.append(latin)
    return _finish(_expand(forms))


def _area_forms(junctions: list[dict[str, Any]]) -> frozenset[str]:
    """Every surface form of the seed neighbourhoods and landmarks, plus the single-word junction forms that more
    than one junction carries."""
    seed = {f for canonical, *_r, aliases in SEED_PLACES for f in seed_forms(canonical, aliases)}
    seen: dict[str, int] = {}
    for j in junctions:
        for f in set(_junction_forms(j)):
            if " " not in f:
                seen[f] = seen.get(f, 0) + 1
    return frozenset(seed | {f for f, n in seen.items() if n > 1})


def _point_like(name: str) -> bool:
    toks = name.split(" ")
    return bool(POINT_WORDS.intersection(toks)) or name.endswith(" cross roads")


def road_forms(s: dict[str, Any], junction_names: frozenset[str] = frozenset()) -> list[str]:
    name = s["road_name"]
    base = _base(name)
    forms = [name, base]
    totals: OrderedDict[str, float] = OrderedDict()
    whole = 0.0  # the segment's whole OSM length, its unnamed stretches included
    for pair in s.get("osm_names") or []:
        raw, length = (pair[0], float(pair[1])) if isinstance(pair, list) else (pair, 0.0)
        whole += length
        if not isinstance(raw, str) or raw.strip().lower() == "(unnamed)":
            continue
        for part in re.split(r"[,;]", raw):
            n = norm(part)
            if n:
                totals[n] = totals.get(n, 0.0) + length
    whole = whole or 1.0
    for n, length in totals.items():
        if _point_like(n):
            if n not in junction_names:
                forms.append(n)
        elif (length >= OSM_NAME_MIN_M and length / whole >= OSM_NAME_MIN_SHARE) or length >= OSM_NAME_LONG_M:
            forms.append(n)
    nb = norm(base)
    for prefix, extra in COLLOQUIAL.items():
        if nb == prefix or nb.startswith(prefix + " "):
            forms.extend(extra)
    return _finish(_expand(forms))


def seed_forms(canonical: str, aliases: tuple[str, ...]) -> list[str]:
    return _finish(_expand([canonical, *(a for a in aliases if norm(a) not in SEED_ALIAS_DENY)]))


def _osm_extract_time(net: dict[str, Any]) -> str:
    base = net.get("osm_base")
    stamps = sorted(v for v in base.values() if isinstance(v, str)) if isinstance(base, dict) else []
    if not stamps:
        raise SystemExit("osm_network.json carries no osm_base extract time")
    return stamps[-1]


def build(network_path: Path = NETWORK_JSON) -> dict[str, Any]:
    """The X19 document, built in memory from the network and the seed tables (deterministic)."""
    net = json.loads(network_path.read_text(encoding="utf-8"))
    junctions = net.get("junctions") or []
    segments = net.get("segments") or []
    if len(junctions) != 34 or len(segments) != 49:
        raise SystemExit(f"expected 34 junctions and 49 segments, found {len(junctions)} and {len(segments)}")
    entries: list[dict[str, Any]] = []
    # bare words that name an area, never one junction (F-HONEST OSINT-1): a neighbourhood's or landmark's form,
    # or a single-word form two junctions would share
    area_forms = _area_forms(junctions)
    # every Latin form of the 34 junctions: an OSM circle named like one of them stays the junction's alone
    junction_names = frozenset(f for j in junctions for f in junction_forms(j, area_forms) if f.isascii())
    gid = 0
    for j in junctions:
        gid += 1
        entries.append(
            {
                "gaz_id": gid,
                "canonical_name": j["name"],
                "feature_type": "junction",
                "surface_forms": junction_forms(j, area_forms),
                "lon": round(float(j["lon"]), 7),
                "lat": round(float(j["lat"]), 7),
                "junction_id": int(j["junction_id"]),
                "segment_id": None,
                "importance": JUNCTION_IMPORTANCE[bool(j.get("signal_control"))],
                "source": "osm_network.junctions",
                "lang_primary": "en",
            }
        )
    for s in segments:
        gid += 1
        lon, lat = interior_point(s["line"])
        entries.append(
            {
                "gaz_id": gid,
                "canonical_name": s["road_name"],
                "feature_type": "road",
                "surface_forms": road_forms(s, junction_names),
                "lon": round(lon, 7),
                "lat": round(lat, 7),
                "junction_id": None,
                "segment_id": int(s["segment_id"]),
                "importance": ROAD_IMPORTANCE.get(s.get("road_class"), 0.5),
                "source": "osm_network.segments",
                "lang_primary": "en",
            }
        )
    for canonical, lat, lon, ftype, importance, aliases in SEED_PLACES:
        gid += 1
        entries.append(
            {
                "gaz_id": gid,
                "canonical_name": canonical,
                "feature_type": ftype,
                "surface_forms": seed_forms(canonical, aliases),
                "lon": lon,
                "lat": lat,
                "junction_id": None,
                "segment_id": None,
                "importance": importance,
                "source": "seed_hand",
                "lang_primary": "en",
            }
        )
    counts = {t: sum(1 for e in entries if e["feature_type"] == t) for t in ("road", "junction", "neighbourhood",
                                                                            "landmark")}
    doc = {
        "meta": {
            "generated_at": _osm_extract_time(net),
            "source": (
                "Veer OSINT place gazetteer, generated by scripts/gen_osint_gazetteer.py: "
                f"{counts['road']} roads and {counts['junction']} junctions from scripts/data/osm_network.json "
                "(OpenStreetMap, English and Gujarati names), "
                f"{counts['neighbourhood']} neighbourhoods and {counts['landmark']} landmarks from its reviewed "
                "seed table (the PoC's); Gujarati and Hindi aliases from osint_geo.translit; generated_at is the "
                "OpenStreetMap extract time; places only, no person or biometric field"
            ),
            "licence": LICENCE,
            "entries": len(entries),
        },
        "entries": entries,
    }
    problems = lint(doc)
    if problems:
        raise SystemExit("gazetteer lint failed:\n  " + "\n  ".join(problems[:40]))
    Gazetteer.from_document(doc)  # the loader's own X19 / places-only check
    return doc


def _phrase(s: str) -> str:
    """osint-common's phrase normal form (ASCII words only), for the place-phrase lint."""
    return re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()


def lint(doc: dict[str, Any]) -> list[str]:
    """Places-only lints over a built document: every form in normal form and not a bare generic word, every
    multi-word phrase (canonical name, its parenthesised parts, each form) carrying a place-type word or a road
    code, unless reviewed, and no junction form that also names a neighbourhood or landmark, or a bare one that
    another junction carries (F-HONEST OSINT-1: an area word is never a junction pin)."""
    problems: list[str] = []
    # F-HONEST OSINT-1: a junction is a precise pin, so no junction form may also name an area
    area_forms = {f for e in doc["entries"] if e["feature_type"] in ("neighbourhood", "landmark")
                  for f in e["surface_forms"]}
    junction_bare: dict[str, int] = {}
    for e in doc["entries"]:
        if e["feature_type"] == "junction":
            for f in e["surface_forms"]:
                if " " not in f:
                    junction_bare[f] = junction_bare.get(f, 0) + 1
    for e in doc["entries"]:
        gid = e["gaz_id"]
        for f in e["surface_forms"]:
            if norm(f) != f:
                problems.append(f"gaz_id {gid}: form not in normal form: {f!r}")
            if not _good(f):
                problems.append(f"gaz_id {gid}: form is a bare generic word or too short: {f!r}")
        names = [e["canonical_name"], *(p for p in re.split(r"[()]", e["canonical_name"]) if p.strip())]
        if e["feature_type"] == "junction":
            for f in e["surface_forms"]:
                if f in area_forms:
                    problems.append(f"gaz_id {gid}: junction form shared with a neighbourhood or landmark: {f!r}")
                if " " not in f and junction_bare.get(f, 0) > 1:
                    problems.append(f"gaz_id {gid}: bare junction form shared with another junction: {f!r}")
        for phrase in {_phrase(x) for x in (*names, *e["surface_forms"])}:
            if " " not in phrase or phrase in REVIEWED_PHRASES:
                continue
            if not any(w in PLACE_TYPE_WORDS or _ROAD_CODE.fullmatch(w) for w in phrase.split(" ")):
                problems.append(f"gaz_id {gid}: phrase without a place-type word: {phrase!r}")
    return problems


def render(doc: dict[str, Any]) -> str:
    """The committed file's exact text (indent 1, UTF-8, a final newline)."""
    return json.dumps(doc, ensure_ascii=False, indent=1) + "\n"


def _summary(doc: dict[str, Any]) -> str:
    entries = doc["entries"]
    by_type: dict[str, int] = {}
    for e in entries:
        by_type[e["feature_type"]] = by_type.get(e["feature_type"], 0) + 1
    forms = sum(len(e["surface_forms"]) for e in entries)
    return (
        f"{len(entries)} entries {json.dumps(by_type, sort_keys=True)}, {forms} surface forms, "
        f"generated_at {doc['meta']['generated_at']}"
    )


# ------------------------------------------------------------------------------------------- the Overpass review
OVERPASS_URL = "https://overpass-api.de/api/interpreter"
USER_AGENT = "Veer-osint-gazetteer/1.0 (offline gazetteer review; one request; +https://github.com/shubro18202758/VVIP)"


def overpass_query() -> str:
    b = BBOX
    box = f"{b['lat_min']},{b['lon_min']},{b['lat_max']},{b['lon_max']}"
    return f'[out:json][timeout:60];(node["place"~"^(suburb|neighbourhood|quarter)$"]({box}););out tags;'


def overpass_review(response: dict[str, Any], doc: dict[str, Any]) -> list[str]:
    """OSM place nodes in the bbox whose name the gazetteer does not carry yet: review lines for a person to add
    to :data:`SEED_PLACES` by hand. Nothing is written."""
    known = {f for e in doc["entries"] for f in e["surface_forms"]}
    lines: list[str] = []
    for el in response.get("elements") or []:
        tags = el.get("tags") or {}
        name = tags.get("name:en") or tags.get("name")
        if not isinstance(name, str) or not name.strip():
            continue
        n = norm(name)
        if not n or n in known:
            continue
        lat, lon = el.get("lat"), el.get("lon")
        near = difflib.get_close_matches(n, sorted(known), n=1, cutoff=0.85)
        hint = f" (close to known form {near[0]!r})" if near else ""
        lines.append(f"candidate: {name} [place={tags.get('place')}] at {lat}, {lon}{hint}")
    return sorted(set(lines))


def _fetch_overpass() -> dict[str, Any]:
    body = urllib.parse.urlencode({"data": overpass_query()}).encode("ascii")
    req = urllib.request.Request(OVERPASS_URL, data=body, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=90) as r:  # noqa: S310 - fixed https endpoint, opt-in only
        return json.loads(r.read().decode("utf-8"))


def _write_atomic(path: Path, text: str) -> None:
    """Replace ``path`` atomically, keeping its permission bits (a new file gets the umask's)."""
    if path.exists():
        mode = path.stat().st_mode & 0o777
    else:
        umask = os.umask(0)
        os.umask(umask)
        mode = 0o666 & ~umask
    fd, tmp = tempfile.mkstemp(prefix=".osint_gazetteer.", suffix=".json", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        os.chmod(tmp, mode)
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--write", action="store_true", help="rewrite scripts/data/osint_gazetteer.json")
    mode.add_argument("--check", action="store_true", help="exit 1 when the committed file differs from a rebuild")
    mode.add_argument("--overpass", action="store_true", help="opt-in review of OSM place nodes (never in gates)")
    ap.add_argument("--overpass-json", type=Path, help="a saved Overpass response for --overpass (offline)")
    ap.add_argument("--network", type=Path, default=NETWORK_JSON, help=argparse.SUPPRESS)
    ap.add_argument("--out", type=Path, default=OUT_JSON, help=argparse.SUPPRESS)
    args = ap.parse_args(argv)

    doc = build(args.network)
    text = render(doc)
    current = args.out.read_text(encoding="utf-8") if args.out.is_file() else None

    if args.overpass:
        response = (
            json.loads(args.overpass_json.read_text(encoding="utf-8")) if args.overpass_json else _fetch_overpass()
        )
        lines = overpass_review(response, doc)
        print(f"overpass review: {len(lines)} place name(s) not in the gazetteer (review by hand; nothing written)")
        for line in lines:
            print("  " + line)
        return 0
    if args.check:
        if current == text:
            print(f"gazetteer OK: {args.out.relative_to(REPO_ROOT) if args.out.is_relative_to(REPO_ROOT) else args.out}"
                  f" matches a rebuild ({_summary(doc)})")
            return 0
        print(f"gazetteer DIFFERS from a rebuild: run {Path(__file__).name} --write ({_summary(doc)})",
              file=sys.stderr)
        if current is not None:
            diff = difflib.unified_diff(
                current.splitlines(), text.splitlines(), "committed", "rebuild", lineterm="", n=1
            )
            for i, line in enumerate(diff):
                if i >= 40:
                    print("  ...", file=sys.stderr)
                    break
                print("  " + line, file=sys.stderr)
        return 1
    if args.write:
        if current == text:
            print(f"gazetteer unchanged ({_summary(doc)})")
            return 0
        _write_atomic(args.out, text)
        print(f"gazetteer written: {args.out} ({_summary(doc)})")
        return 0
    print(f"gazetteer rebuild: {_summary(doc)}; committed file {'matches' if current == text else 'DIFFERS'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
