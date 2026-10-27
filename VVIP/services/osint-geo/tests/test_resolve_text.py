"""``resolve_text`` for ``GET /osint/gazetteer/resolve?q=`` (C-T): ranked, read-only gazetteer lookups."""

from __future__ import annotations

import pytest

from osint_geo.resolver import resolve_text

KEYS = {"gaz_id", "canonical_name", "feature_type", "lon", "lat", "segment_id", "junction_id", "confidence", "method"}


def test_the_ct_candidate_shape():
    out = resolve_text("Karnavati Club")
    assert out and all(set(c) == KEYS for c in out)
    top = out[0]
    assert top["gaz_id"] == 106 and top["canonical_name"] == "Karnavati Club (SG Highway)"
    assert top["feature_type"] == "landmark" and top["segment_id"] == 1045 and top["junction_id"] is None
    assert top["method"] == "gazetteer_exact" and 0.0 <= top["confidence"] <= 1.0


def test_junctions_roads_and_grammar():
    assert resolve_text("odhav ring road circle")[0]["junction_id"] == 11
    sg = resolve_text("SG Highway", limit=10)
    assert {c["segment_id"] for c in sg} == {1016, 1017, 1018, 1040, 1045}
    assert all(c["feature_type"] == "road" for c in sg)
    top = resolve_text("Paldi char rasta")[0]
    assert top["junction_id"] == 4 and top["method"] == "grammar"


def test_ranked_best_first_and_only_the_top_has_a_margin():
    out = resolve_text("prahlad nagar", limit=5)
    assert [c["feature_type"] for c in out[:2]] == ["road", "neighbourhood"]
    assert out[0]["confidence"] > out[1]["confidence"]
    # F-HONEST OSINT-1: the bare area word is the neighbourhood alone, never the Paldi Cross Roads junction
    bare = resolve_text("paldi", limit=5)
    assert [c["feature_type"] for c in bare] == ["neighbourhood"] and bare[0]["segment_id"] is None


def test_fuzzy_multi_word_only():
    fz = resolve_text("Karnavti Club")
    assert fz and fz[0]["gaz_id"] == 106 and fz[0]["method"] == "gazetteer_fuzzy"
    exact = resolve_text("Karnavati Club")
    assert fz[0]["confidence"] < exact[0]["confidence"]


@pytest.mark.parametrize("q", ["india", "India", "road", "the", "", "zz", "Ahmedabad", "karnav", "Indra"])
def test_no_guess(q):
    assert resolve_text(q) == []


def test_limit_and_query_bounds():
    assert len(resolve_text("ring road", limit=3)) == 3
    assert resolve_text("ring road", limit=0) == [] and resolve_text("ring road", limit=-5) == []
    assert len(resolve_text("ring road", limit=10_000)) <= 50
    assert resolve_text("x" * 5000) == []


def test_an_operator_query_is_about_the_city():
    # the context gate is open for an operator's lookup: these resolve here although a national outlet's text
    # naming no Ahmedabad word would not
    assert resolve_text("satellite")[0]["canonical_name"] == "Satellite"
    assert resolve_text("civil hospital")[0]["canonical_name"] == "Civil Hospital Asarwa"
    assert {c["feature_type"] for c in resolve_text("ring road", limit=10)} == {"road"}
    assert resolve_text("airport") == []  # never junction 14 by the common word
    assert resolve_text("ahmedabad airport")[0]["canonical_name"] == "SVP International Airport"


@pytest.mark.parametrize("q", ["132 feet ring road", "132 Foot Ring Road", "132 Ft. Ring Road", "132 ft ring road"])
def test_the_132_ft_ring_road_by_its_usual_spellings(q):
    # review r3: "132 feet ring road" returned only SP Ring Road segments (the bare "ring road" sub-form)
    out = resolve_text(q, limit=10)
    assert {c["gaz_id"] for c in out} == {75, 78}
    assert {c["segment_id"] for c in out} == {1041, 1044}


def test_read_only_and_deterministic():
    a = resolve_text("Law Garden")
    b = resolve_text("Law Garden")
    assert a == b and a[0]["canonical_name"] == "Law Garden"
    a[0]["canonical_name"] = "changed"
    assert resolve_text("Law Garden")[0]["canonical_name"] == "Law Garden"
