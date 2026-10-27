"""The regex place grammar: relational, feature and PIN spans, clause boundaries, and the rewrite hits."""

from __future__ import annotations

from osint_geo.gazetteer import load
from osint_geo.grammar import PIN_RE, feature_hits, find_spans, lookup_keys, pin_codes


def _spans(text: str, kind: str):
    return [s for s in find_spans(text) if s.kind == kind]


def test_relational_spans():
    rel = _spans("Accident near Karnavati Club on Tuesday; jam opp. Law Garden", "relational")
    assert [s.head for s in rel] == ["karnavati club", "law garden"]
    assert rel[0].surface == "Karnavati Club" and rel[0].keys == ("karnavati club",)


def test_a_relational_span_never_crosses_a_clause():
    rel = _spans("Seen near Gurukul - The Times of India", "relational")
    assert [s.head for s in rel] == ["gurukul"]
    rel = _spans("He was near. Paldi was quiet", "relational")
    assert rel == []


def test_abbreviations_keep_the_clause():
    rel = _spans("Crash near S.G. Highway flyover", "relational")
    assert rel and rel[0].head.startswith("s g highway")


def test_feature_spans_carry_every_rewrite():
    feat = _spans("Car fire near Paldi char rasta", "feature")
    assert len(feat) == 1
    span = feat[0]
    assert span.head == "paldi" and span.feature == "cross roads"
    assert "paldi cross roads" in span.keys and "paldi char rasta" in span.keys
    feat = _spans("Shops shut at Astodia darwaza and Iskcon cir.", "feature")
    keys = [k for s in feat for k in s.keys]
    assert "astodia darwaja" in keys and "iskcon circle" in keys


def test_feature_heads_stop_at_cue_words():
    feat = _spans("traffic near paldi char rasta", "feature")
    assert feat and all("near" not in k for k in feat[0].keys)


def test_gujarati_feature_span_is_transliterated():
    feat = _spans("થલતેજ ચોકડી પાસે અકસ્માત", "feature")
    assert feat and "thaltej cross roads" in feat[0].keys


def test_lookup_keys():
    assert lookup_keys("Paldi", "char rasta") == ("paldi char rasta", "paldi cross roads")
    assert lookup_keys("Sola", "fly over") == ("sola fly over", "sola flyover", "sola overbridge")
    assert lookup_keys("", "circle") == ()


def test_pin_codes():
    assert pin_codes("Water main burst, Navrangpura 380009. Call 1800-380015-99") == ["380009"]
    assert pin_codes("Ahmedabad-380015, or Ahmedabad 380 054") == ["380015", "380054"]
    assert pin_codes("ref 3800099 or 13800 99 or 380109") == []
    assert PIN_RE.fullmatch("380061") is not None and PIN_RE.fullmatch("382415") is None
    pins = _spans("near the school, 380007.", "pin")
    assert [p.head for p in pins] == ["380007"]


def test_feature_hits_rewrite_against_the_index():
    gaz = load()
    toks = gaz.tokens("jam at paldi char rasta and shivranjani x roads")
    hits = feature_hits(toks, gaz)
    assert {h.form for h in hits} == {"paldi cross roads", "shivranjani cross roads"}
    assert all(h.via == "grammar" for h in hits)
    paldi = next(h for h in hits if h.form == "paldi cross roads")
    assert toks[paldi.start : paldi.end] == ["paldi", "char", "rasta"]


def test_feature_hits_need_a_real_form():
    gaz = load()
    assert feature_hits(gaz.tokens("the old gate"), gaz) == []
    assert feature_hits(gaz.tokens("unknown place char rasta"), gaz) == []


def test_no_spans_in_plain_text():
    assert find_spans("") == [] and find_spans("nothing here at all") == []
