"""The stoplist guard (the PoC's "India" ↔ "indira" fix): India never matches Indira, short tokens never
fuzzy-match, and fuzzy matching runs on multi-word names only."""

from __future__ import annotations

import difflib

import pytest

from osint_geo.gazetteer import GENERIC_STOPWORDS
from osint_geo.resolver import FUZZY_STOP, GazetteerResolver

from _synthetic import make_signal


@pytest.fixture(scope="module")
def resolver() -> GazetteerResolver:
    return GazetteerResolver()


def test_the_trap_is_real():
    # why the guard exists: difflib alone would take "india" for "indira"
    assert difflib.SequenceMatcher(None, "india", "indira").ratio() > 0.9


@pytest.mark.parametrize(
    "title",
    [
        "India records its wettest October",
        "INDIA: monsoon withdraws late",
        "India's cities brace for heavy rain",
        "Indian Express: markets steady",
        "Times of India reports a quiet weekend",
        "India Today: traffic advisory for the festival",
        "Team India arrives for the series",
    ],
)
def test_india_never_matches_indira(resolver, title):
    g = resolver.resolve(make_signal(title, f"{title}. Nothing else happened."))
    assert g is None or "indira" not in (g.toponym or "").lower()
    assert g is None


def test_india_never_matches_indira_in_any_window(resolver):
    text = "India bridge circle India bridge India circle north India bridge north"
    mentions = resolver.mentions(text)
    assert all("indira" not in m.form for m in mentions)


def test_the_real_indira_places_still_resolve(resolver):
    g = resolver.resolve(make_signal("Indira Bridge closed for repairs", "Indira Bridge closed for repairs tonight."))
    assert g is not None and g.toponym == "Indira Bridge (Airport–Motera)" and g.method == "gazetteer_exact"
    g = resolver.resolve(make_signal("Jam at Indira Bridge Circle", "A long jam at Indira Bridge Circle."))
    assert g is not None and g.junction_id == 13


def test_no_bare_given_name_or_common_word_alias(resolver):
    gaz = resolver.gazetteer
    for word in ("indira", "india", "gandhi", "nehru", "income", "science", "helmet", "prahlad", "ellis", "bhat",
                 "pakwan", "airport", "dehgam"):
        assert gaz.lookup(word) == (), word


@pytest.mark.parametrize("typo", ["Bopl", "Pldi", "Odhv", "Gotaa", "Nikl", "Karnavti", "Navrangpur"])
def test_short_or_single_tokens_never_fuzzy_match(resolver, typo):
    g = resolver.resolve(make_signal(f"Traffic jam in {typo}", f"Traffic jam in {typo} this evening."))
    assert g is None, (typo, g)


def test_multi_word_names_fuzzy_match(resolver):
    g = resolver.resolve(make_signal("Accident near Karnavti Club", "An accident near Karnavti Club this evening."))
    assert g is not None and g.toponym == "Karnavati Club (SG Highway)" and g.method == "gazetteer_fuzzy"
    assert g.segment_id == 1045
    ex = resolver.explain(make_signal("Accident near Karnavti Club", "An accident near Karnavti Club this evening."))
    assert all(0.9 <= m["score"] < 1.0 for m in ex["mentions"])
    # a fuzzy match is never as sure as the exact alias
    exact = resolver.resolve(make_signal("Accident near Karnavati Club", "An accident near Karnavati Club."))
    assert exact is not None and exact.confidence > g.confidence


def test_fuzzy_reads_a_misspelt_junction_with_a_rewritten_place_word(resolver):
    g = resolver.resolve(make_signal("Signal down at Shivranjni char rasta", "Signal down at Shivranjni char rasta."))
    assert g is not None and g.junction_id == 18 and g.method == "gazetteer_fuzzy"


def test_fuzzy_needs_two_words_and_eight_characters(resolver):
    gaz = resolver.gazetteer
    assert gaz.fuzzy("karnavti") is None  # single word: the pool holds multi-word forms only
    assert gaz.fuzzy("cg rd") is None  # too short to be a fuzzy candidate pool form at ratio 0.9
    assert gaz.fuzzy("karnavti club") == ("karnavati club", pytest.approx(0.963, abs=0.001))


def test_windows_with_a_stop_word_or_only_generic_words_are_skipped(resolver):
    for text in (
        "Gujarat university campus news",  # "news" and "gujarat" are fuzzy stop words; exact form handled apart
        "the road near the circle and the bridge",
        "cross road near the station junction",
    ):
        assert resolver._fuzzy_mentions(resolver.gazetteer.tokens(text.replace("university", "univrsity"))) == []
    assert {"india", "indian", "gujarat", "ahmedabad", "amdavad"} <= FUZZY_STOP
    assert {"road", "circle", "bridge", "nagar", "near"} <= GENERIC_STOPWORDS


def test_exact_matches_win_over_fuzzy(resolver):
    # with an exact place present the fuzzy stage never runs, so a near-miss elsewhere in the text adds nothing
    mentions = resolver.mentions("Fire at Law Garden; smoke seen from Karnavti Club")
    assert [m.form for m in mentions] == ["law garden"] and mentions[0].method == "gazetteer_exact"


def test_a_misspelt_place_is_never_surer_than_the_same_place_spelt_right(resolver):
    for typo, right in (
        ("Karnavti Club crash. Seen near Karnavti Club.", "Karnavati Club crash. Seen near Karnavati Club."),
        ("Accident near Karnavti Club", "Accident near Karnavati Club"),
        ("Signal down at Shivranjni char rasta", "Signal down at Shivranjani char rasta"),
    ):
        g_typo, g_right = resolver.resolve(make_signal(typo, typo)), resolver.resolve(make_signal(right, right))
        assert g_typo is not None and g_right is not None and g_typo.toponym == g_right.toponym
        assert g_typo.method == "gazetteer_fuzzy" and g_typo.confidence <= g_right.confidence, (typo, g_typo, g_right)


def test_cue_bound_names_are_the_first_fuzzy_candidates(resolver):
    names = resolver._grammar_names("Jam near Karnavti Club; diversion opp. Law Gardn and near Karnavti Club")
    assert [n for n, _ in names] == [("karnavti", "club"), ("law", "gardn")]
    mentions = resolver.mentions("Jam near Karnavti Club; diversion opp. Law Gardn and near Karnavti Club")
    assert [m.form for m in mentions] == ["karnavati club", "law garden", "karnavati club"]
    assert all(m.method == "gazetteer_fuzzy" for m in mentions)
