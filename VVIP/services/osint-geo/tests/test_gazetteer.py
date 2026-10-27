"""The X19 gazetteer: format, places only (no field outside the list), the ODbL notice, the protect-set, the
normaliser, the longest-match index, the path rules, and the generator (deterministic, --check)."""

from __future__ import annotations

import copy
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

from osint_common import ethics
from osint_geo import gazetteer as gz
from osint_geo import translit
from osint_geo.gazetteer import ENTRY_FIELDS, LICENCE, META_FIELDS, Gazetteer, load, norm

from _poc import POC_GAZETTEER

REPO = Path(__file__).resolve().parents[3]
GAZ_JSON = REPO / "scripts" / "data" / "osint_gazetteer.json"
NETWORK_JSON = REPO / "scripts" / "data" / "osm_network.json"
GENERATOR = REPO / "scripts" / "gen_osint_gazetteer.py"


def _generator():
    spec = importlib.util.spec_from_file_location("gen_osint_gazetteer", GENERATOR)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def doc() -> dict:
    return json.loads(GAZ_JSON.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def gaz() -> Gazetteer:
    return load()


# ------------------------------------------------------------------------------------------------- X19 format
def test_x19_format(doc):
    assert set(doc) == {"meta", "entries"}
    assert set(doc["meta"]) == set(META_FIELDS)
    assert doc["meta"]["entries"] == len(doc["entries"]) == 127
    for e in doc["entries"]:
        assert list(e) == list(ENTRY_FIELDS), e.get("gaz_id")
        assert e["feature_type"] in gz.FEATURE_TYPES
        assert isinstance(e["surface_forms"], list) and all(isinstance(f, str) for f in e["surface_forms"])
    assert [e["gaz_id"] for e in doc["entries"]] == list(range(1, 128))
    counts = {t: sum(1 for e in doc["entries"] if e["feature_type"] == t) for t in ("road", "junction",
                                                                                   "neighbourhood", "landmark")}
    assert counts == {"road": 49, "junction": 34, "neighbourhood": 28, "landmark": 16}


def test_odbl_notice(doc, gaz):
    assert doc["meta"]["licence"] == LICENCE == "© OpenStreetMap contributors, ODbL 1.0"
    assert gaz.meta["licence"] == LICENCE
    assert "OpenStreetMap" in doc["meta"]["source"]


def test_ids_are_the_network_of_record(doc):
    net = json.loads(NETWORK_JSON.read_text(encoding="utf-8"))
    junctions = [e for e in doc["entries"] if e["feature_type"] == "junction"]
    roads = [e for e in doc["entries"] if e["feature_type"] == "road"]
    assert [e["junction_id"] for e in junctions] == [j["junction_id"] for j in net["junctions"]]
    assert [e["canonical_name"] for e in junctions] == [j["name"] for j in net["junctions"]]
    assert [e["segment_id"] for e in roads] == [s["segment_id"] for s in net["segments"]]
    assert [e["canonical_name"] for e in roads] == [s["road_name"] for s in net["segments"]]
    for e in doc["entries"]:
        if e["feature_type"] in ("neighbourhood", "landmark"):
            assert e["junction_id"] is None and e["segment_id"] is None and e["source"] == "seed_hand"


def test_the_pocs_ids_and_priors_are_kept(doc):
    poc = POC_GAZETTEER
    if not poc.is_file():
        pytest.skip("PoC gazetteer not present (read in place only)")
    old = {e["gaz_id"]: e for e in json.loads(poc.read_text(encoding="utf-8"))["entries"]}
    for e in doc["entries"]:
        o = old[e["gaz_id"]]
        assert (e["canonical_name"], e["feature_type"], e["junction_id"], e["segment_id"], e["importance"]) == (
            o["canonical_name"], o["feature_type"], o["junction_id"], o["segment_id"], o["importance"])
        if e["feature_type"] != "road":  # roads now sit on their segment's anchor (ST_PointOnSurface)
            assert (e["lon"], e["lat"]) == (o["lon"], o["lat"])


def test_points_are_in_the_city(doc):
    for e in doc["entries"]:
        assert 72.43 <= e["lon"] <= 72.77 and 22.88 <= e["lat"] <= 23.17, e["canonical_name"]


# ------------------------------------------------------------------------------------------------- places only
def test_places_only_no_person_key(doc):
    ethics.assert_no_person_keys(doc)
    for e in doc["entries"]:
        assert not any(ethics.is_forbidden_key(k) for k in e if k != "surface_forms")


@pytest.mark.parametrize("extra", ["victim", "author", "notes", "person_name", "reporter", "owner"])
def test_a_key_outside_the_x19_list_is_refused(doc, extra):
    bad = copy.deepcopy(doc)
    bad["entries"][5][extra] = "x"
    with pytest.raises(ValueError, match="outside the X19 field list"):
        Gazetteer.from_document(bad)


def test_a_meta_or_top_level_key_outside_the_list_is_refused(doc):
    bad = copy.deepcopy(doc)
    bad["meta"]["uploader"] = "x"
    with pytest.raises(ValueError, match="X19"):
        Gazetteer.from_document(bad)
    bad = copy.deepcopy(doc)
    bad["people"] = []
    with pytest.raises(ValueError, match="top-level"):
        Gazetteer.from_document(bad)


@pytest.mark.parametrize(
    "field,value",
    [
        ("gaz_id", True),
        ("gaz_id", 0),
        ("feature_type", "person"),
        ("lon", 200.0),
        ("lat", float("nan")),
        ("importance", 1.5),
        ("surface_forms", "paldi"),
        ("surface_forms", [1, 2]),
        ("canonical_name", ""),
        ("canonical_name", "Paldi\x00"),
        ("lang_primary", "English"),
        ("junction_id", -3),
    ],
)
def test_bad_values_are_refused(doc, field, value):
    bad = copy.deepcopy(doc)
    bad["entries"][0][field] = value
    with pytest.raises(ValueError):
        Gazetteer.from_document(bad)


def test_missing_fields_and_wrong_counts_are_refused(doc):
    bad = copy.deepcopy(doc)
    del bad["entries"][3]["importance"]
    with pytest.raises(ValueError, match="lacks"):
        Gazetteer.from_document(bad)
    bad = copy.deepcopy(doc)
    bad["meta"]["entries"] = 126
    with pytest.raises(ValueError, match="meta.entries"):
        Gazetteer.from_document(bad)
    bad = copy.deepcopy(doc)
    bad["entries"][1]["gaz_id"] = 1
    with pytest.raises(ValueError, match="duplicate"):
        Gazetteer.from_document(bad)
    bad = copy.deepcopy(doc)
    bad["entries"][40]["segment_id"] = None  # a road without its segment
    with pytest.raises(ValueError, match="segment_id"):
        Gazetteer.from_document(bad)


# ------------------------------------------------------------------------------------------------- protect-set
def test_protect_set_holds_every_canonical_name_and_form(doc, gaz):
    assert isinstance(gaz.protect_set, frozenset)
    for e in doc["entries"]:
        assert norm(e["canonical_name"]) in gaz.protect_set
        for f in e["surface_forms"]:
            assert f in gaz.protect_set
    for part in ("karnavati club", "sg highway", "sabarmati ashram", "gandhi ashram", "ashram road",
                 "odhav ring road circle", "dr ambedkar road", "paldi"):
        assert part in gaz.protect_set


def test_protect_set_never_holds_a_bare_person_name(gaz):
    # a sub-phrase of a place named after a person would protect that person's name: none is added
    for name in ("narendra modi", "sardar patel", "chimanbhai patel", "swami vivekananda", "kasturba gandhi",
                 "surendra mangaldas", "sardar vallabhbhai patel", "maharana pratap", "gandhi", "nehru", "indira"):
        assert name not in gaz.protect_set, name


# ------------------------------------------------------------------------------------------------- forms
def test_every_form_is_normal_matchable_and_not_generic(doc):
    for e in doc["entries"]:
        assert e["surface_forms"] == sorted(set(e["surface_forms"])), e["gaz_id"]
        for f in e["surface_forms"]:
            assert norm(f) == f, (e["gaz_id"], f)
            assert len(f) >= gz.MIN_FORM_CHARS
            assert not all(t in gz.GENERIC_STOPWORDS for t in f.split(" ")), (e["gaz_id"], f)


def test_schematic_labels_are_not_aliases(gaz):
    # the pre-OSM schematic names named other places: never a way to reach a junction
    for label, wrong_gid in (("usmanpura junction", 26), ("sp ring road north", 22), ("drive in road east", 25),
                             ("ashram road riverfront junction", 1), ("riverfront west junction", 6)):
        assert wrong_gid not in gaz.lookup(label), label


def test_first_word_aliases_are_places_of_their_own(gaz):
    gen = _generator()
    # a common word or another place a junction is only named after is never its alias (review r1: "airport")
    assert {"airport", "dehgam", "income", "science", "helmet", "pakwan"} <= set(gen.FIRST_WORD_DENY)
    for word in gen.FIRST_WORD_DENY:
        assert gaz.lookup(word) == (), word
    # the junctions' own names still reach them
    assert gaz.lookup("airport circle") == (14,) and gaz.lookup("dehgam circle") == (31,)
    # the first words that stay name the crossing itself
    for word, jid in (("shivranjani", 18), ("vaishnodevi", 12), ("svpi", 21)):
        assert any(gaz.by_id[g].junction_id == jid for g in gaz.lookup(word)), word


def test_an_area_word_is_never_a_junction_alias(doc, gaz):
    # F-HONEST OSINT-1: "odhav" was both the neighbourhood (110) and a form of Odhav Ring Road Circle (junction
    # 11), so "Odhav's Rajendra Park Bridge" was pinned on the junction at residual 0. A bare area word reaches the
    # area only, in every script; a word two junctions share reaches neither
    for word, gid in (("odhav", 110), ("ओढव", 110), ("ઓઢવ", 110), ("paldi", 87), ("પાલડી", 87), ("bopal", 88),
                      ("thaltej", 92), ("shahibaug", 109), ("ellisbridge", 103), ("iskcon", 115), ("kalupur", 124)):
        assert gaz.lookup(word) == (gid,), word
    for word in ("motera", "sola", "sarkhej", "koba", "aslali", "astodia"):
        assert all(gaz.by_id[g].feature_type != "junction" for g in gaz.lookup(word)), word
    # the junctions' own names still reach them
    assert gaz.lookup("odhav ring road circle") == (11,) and gaz.lookup("paldi cross roads") == (4,)
    assert gaz.lookup("motera junction") == (24,) and gaz.lookup("sola cross roads") == (26,)


def test_the_lint_refuses_an_area_word_on_a_junction(doc):
    gen = _generator()
    assert gen.lint(doc) == []
    bad = copy.deepcopy(doc)
    junction = next(e for e in bad["entries"] if e["junction_id"] == 11)
    junction["surface_forms"] = sorted([*junction["surface_forms"], "odhav"])
    assert any("shared with a neighbourhood or landmark: 'odhav'" in p for p in gen.lint(bad))
    bad = copy.deepcopy(doc)
    for jid in (24, 25):
        j = next(e for e in bad["entries"] if e["junction_id"] == jid)
        j["surface_forms"] = sorted([*j["surface_forms"], "motera"])
    assert any("bare junction form shared with another junction: 'motera'" in p for p in gen.lint(bad))


def test_a_bridge_on_the_segment_is_its_alias(doc, gaz):
    # a bridge the road runs over is point-like: an alias at any length ("Fernandes Bridge", 22 m of Gandhi Road)
    gen = _generator()
    assert "bridge" in gen.POINT_WORDS and "cross road" not in gen.POINT_WORDS
    assert [gaz.by_id[g].segment_id for g in gaz.lookup("fernandes bridge")] == [1012]
    # the bridges already over the length rule keep their own segments
    for name, sid in (("nehru bridge", 1015), ("gandhi bridge", 1031), ("indira bridge", 1048)):
        assert sid in [gaz.by_id[g].segment_id for g in gaz.lookup(name)], name
    # the one OSM "... cross road" name is junction 5's crossing, never a road alias split over two segments
    assert gaz.lookup("astodia darwaza cross road") == ()


def test_generator_lint_is_clean_and_phrases_are_places(doc):
    gen = _generator()
    assert gen.lint(doc) == []
    multi = {gen._phrase(f) for e in doc["entries"] for f in e["surface_forms"]} - {""}
    assert len([p for p in multi if " " in p]) > 150


def test_gujarati_and_hindi_aliases(gaz):
    assert gaz.lookup("મણિનગર") == gaz.lookup("मणिनगर") == gaz.lookup("maninagar")
    assert 17 in gaz.lookup("થલતેજ ચાર રસ્તા")  # junction 17, from osm_network.json's name_gu
    assert gaz.lookup("સેટેલાઇટ") == ()  # a common word in Gujarati: deliberately no alias


# ------------------------------------------------------------------------------------------------- normaliser
@pytest.mark.parametrize(
    "raw,want",
    [
        ("S.G. Highway", "s g highway"),
        ("  SG   Highway ", "sg highway"),
        ("NH-147", "nh147"),
        ("NH 47", "nh47"),
        ("Rakhiyal Road SH-68", "rakhiyal road sh68"),
        ("Vastrāpur", "vastrapur"),
        ("Odhav’s Rajendra", "odhav s rajendra"),
        ("Drive-In Road", "drive in road"),
        ("Dr. Ambedkar Road (Lal Darwaja–Shahibaug)", "dr ambedkar road lal darwaja shahibaug"),
        ("પાલડી ચાર રસ્તા (આશ્રમ રોડ - સી.જી. રોડ)", "પાલડી ચાર રસ્તા આશ્રમ રોડ સી જી રોડ"),
        ("પાલ\u200dડી", "પાલડી"),
        ("चांदखे\u095c\u093e", "चांदखे\u0921\u093c\u093e"),  # a precomposed nukta letter decomposes (NFKC)
        ("ＳＧ　Ｈｉｇｈｗａｙ", "sg highway"),
        (None, ""),
    ],
)
def test_norm(raw, want):
    assert norm(raw) == want
    assert norm(norm(raw)) == norm(raw)


def test_translit_is_in_step_with_norm():
    for s in ("S.G. Highway", "પાલડી ચાર રસ્તા (આશ્રમ રોડ)", "चांदखेड़ा", "Lal Darwaja"):
        assert translit._n(s) == norm(s)
    assert translit.to_latin("થલતેજ ચોકડી") == "thaltej cross roads"
    assert translit.to_latin("ઇસ્કોન ચાર રસ્તા") == "iskcon cross roads"
    assert translit.to_latin("અજાણ્યું સ્થળ") is None  # a partial transliteration is never guessed
    assert len(translit.GU_LATIN_SEED) == 11


# ------------------------------------------------------------------------------------------------- longest match
def test_longest_match_prefers_the_longer_form(gaz):
    hits = gaz.match("Crash on SG Highway Prahlad Nagar stretch")
    assert [h.form for h in hits] == ["sg highway prahlad nagar"]
    hits = gaz.match("Crash on SG Highway near Prahlad Nagar")
    assert sorted((h.start, h.form) for h in hits) == [(2, "sg highway"), (5, "prahlad nagar")]
    # the selection order is the PoC's: longer covered text first
    assert [h.form for h in hits] == ["prahlad nagar", "sg highway"]


def test_every_occurrence_is_a_mention(gaz):
    hits = gaz.match("Karnavati Club ... Karnavati Club ... karnavati club")
    assert [h.form for h in hits] == ["karnavati club"] * 3


def test_gujarati_case_endings_are_read(gaz):
    assert [h.form for h in sorted(gaz.match("ઓઢવથી મણિનગરમાં"))] == ["ઓઢવ", "મણિનગર"]
    # a stem that is not a place is left alone
    assert gaz.match("કાલુપુરમ") == []


def test_tokens_never_match_inside_a_word(gaz):
    assert gaz.match("Bopalpur") == [] and gaz.match("Paldiwala") == []


# ------------------------------------------------------------------------------------------------- path rules
def test_path_rules_and_cache(tmp_path, monkeypatch):
    assert load() is load() and load().path is not None and load().path.name == "osint_gazetteer.json"
    custom = tmp_path / "g.json"
    custom.write_text(GAZ_JSON.read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setenv(gz.GAZETTEER_ENV, str(custom))
    assert load().path == custom
    monkeypatch.setenv(gz.GAZETTEER_ENV, str(tmp_path / "missing.json"))
    with pytest.raises(FileNotFoundError):
        load()
    with pytest.raises(FileNotFoundError):
        load(tmp_path / "nope.json")
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps({"meta": {}, "entries": [{"gaz_id": 1}]}), encoding="utf-8")
    with pytest.raises(ValueError):
        load(bad)


def test_entries_read_as_objects_and_mappings(gaz):
    e = gaz.by_id[106]
    assert e.canonical_name == e["canonical_name"] == "Karnavati Club (SG Highway)"
    assert dict(e)["gaz_id"] == 106 and e.get("nope", 1) == 1
    assert json.loads(json.dumps(e.as_dict()))["surface_forms"] == list(e.surface_forms)
    with pytest.raises(KeyError):
        e["victim"]


# ------------------------------------------------------------------------------------------------- generator
def test_generator_is_deterministic_and_matches_the_committed_file():
    gen = _generator()
    a, b = gen.render(gen.build()), gen.render(gen.build())
    assert a == b == GAZ_JSON.read_text(encoding="utf-8")


def test_generator_check_exit_codes(tmp_path):
    ok = subprocess.run([sys.executable, str(GENERATOR), "--check"], capture_output=True, text=True, cwd=REPO)
    assert ok.returncode == 0, ok.stderr
    stale = tmp_path / "stale.json"
    stale.write_text(GAZ_JSON.read_text(encoding="utf-8").replace('"paldi"', '"paldy"', 1), encoding="utf-8")
    bad = subprocess.run([sys.executable, str(GENERATOR), "--check", "--out", str(stale)], capture_output=True,
                         text=True, cwd=REPO)
    assert bad.returncode == 1 and "DIFFERS" in bad.stderr


def test_overpass_review_is_offline_and_writes_nothing(doc):
    gen = _generator()
    response = {"elements": [
        {"type": "node", "lat": 23.05, "lon": 72.53, "tags": {"place": "suburb", "name": "Gurukul"}},
        {"type": "node", "lat": 23.03, "lon": 72.56, "tags": {"place": "suburb", "name": "Navrangpura"}},
        {"type": "node", "lat": 23.0, "lon": 72.6, "tags": {"place": "neighbourhood"}},
    ]}
    lines = gen.overpass_review(response, doc)
    assert len(lines) == 1 and "Gurukul" in lines[0]
    assert "suburb|neighbourhood|quarter" in gen.overpass_query()


def test_every_junction_keeps_its_gujarati_name(doc):
    net = json.loads(NETWORK_JSON.read_text(encoding="utf-8"))
    forms = {e["junction_id"]: set(e["surface_forms"]) for e in doc["entries"] if e["feature_type"] == "junction"}
    for j in net["junctions"]:
        assert norm(j["name_gu"]) in forms[j["junction_id"]], j["junction_id"]


def test_every_seed_alias_of_the_poc_is_kept(doc):
    poc = POC_GAZETTEER
    if not poc.is_file():
        pytest.skip("PoC gazetteer not present (read in place only)")
    deny = _generator().SEED_ALIAS_DENY
    old = {e["gaz_id"]: e for e in json.loads(poc.read_text(encoding="utf-8"))["entries"]}
    dropped = []
    for e in doc["entries"]:
        if e["source"] != "seed_hand":
            continue
        for f in old[e["gaz_id"]]["surface_forms"]:
            if norm(f) in deny:  # a name of more than one place, deliberately not carried (reviewed)
                assert norm(f) not in e["surface_forms"], (e["gaz_id"], f)
                dropped.append(norm(f))
                continue
            assert norm(f) in e["surface_forms"], (e["gaz_id"], f)
    assert sorted(dropped) == sorted(deny)


def test_a_name_of_two_places_is_no_alias(doc, gaz):
    gen = _generator()
    assert set(gen.SEED_ALIAS_DENY) == {"sardar patel stadium"}
    assert all(gen.SEED_ALIAS_DENY.values())
    assert gaz.lookup("sardar patel stadium") == ()
    stadium = next(e for e in doc["entries"] if e["gaz_id"] == 113)
    assert {"narendra modi stadium", "motera stadium", "motera cricket stadium"} <= set(stadium["surface_forms"])


def test_generator_check_needs_the_standard_library_only():
    # osint_geo.gazetteer, translit and geom import nothing outside the stdlib: --check runs on any Python 3.12
    code = (
        "import runpy, sys\n"
        "for m in ('numpy', 'pyproj', 'shapely', 'pydantic'): sys.modules[m] = None\n"
        f"sys.argv = [{str(GENERATOR)!r}, '--check']\n"
        f"runpy.run_path({str(GENERATOR)!r}, run_name='__main__')\n"
    )
    r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, cwd=REPO)
    assert r.returncode == 0, r.stderr
    assert "gazetteer OK" in r.stdout


def test_no_form_reads_as_a_person(doc):
    for e in doc["entries"]:
        for text in (e["canonical_name"], *e["surface_forms"]):
            assert ethics.find_pii(text) == [], (e["gaz_id"], text)


def test_the_seed_notice_credits_the_gazetteer():
    # F-DEPLOY D-16: the gazetteer carries OSM-derived names and points, so it sits in the seed NOTICE's ODbL table
    notice = (REPO / "services" / "corridor-store" / "seed" / "NOTICE.md").read_text(encoding="utf-8")
    rows = [line for line in notice.splitlines() if line.startswith("| `scripts/data/osint_gazetteer.json`")]
    assert len(rows) == 1 and "ODbL" in rows[0]
