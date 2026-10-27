"""GazetteerResolver on the canonical synthetic fixtures (osint_common.testing) and on hand-made synthetic signals.

Every signal here is synthetic: fictional publishers (``*.example``), no real person, redacted placeholders only.
"""

from __future__ import annotations

import json
import re
import threading

import pytest

from osint_common import ethics, testing
from osint_common.pipeline import GeoResolver
from osint_common.types import Geocode, RawOsintSignal
from osint_geo import resolver as resolver_mod
from osint_geo import translit
from osint_geo.gazetteer import Gazetteer, norm
from osint_geo.resolver import CONTEXT_FORMS, DISTRICT_AHMEDABAD, GazetteerResolver

from _synthetic import make_signal

KARNAVATI = "Karnavati Club (SG Highway)"
ODHAV = "Odhav Ring Road Circle (SP Ring Road)"
#: a city-scoped source (source locality 1.0): the fictional community on the fictional social host
LOCAL = {"source": "reddit_rss", "publisher": "social-a.example/r/example_city"}


@pytest.fixture(scope="module")
def resolver() -> GazetteerResolver:
    return GazetteerResolver()


# ----------------------------------------------------------------------------------------------- the protocol
def test_implements_the_geo_resolver_protocol(resolver):
    assert isinstance(resolver, GeoResolver)


# ----------------------------------------------------------------------------------------------- SG Highway
def test_sg_highway_replica_resolves_karnavati_club_on_segment_1045(resolver):
    first = testing.sg_highway_signals()[0]
    g = resolver.resolve(first)
    want = testing.sg_highway_geocode()
    assert isinstance(g, Geocode)
    assert g.signal_id == first.signal_id == want.signal_id
    assert (g.toponym, g.feature_type, g.segment_id, g.junction_id) == (KARNAVATI, "landmark", 1045, None)
    assert g.snapped_to == want.snapped_to == "SG Highway (Prahlad Nagar)"
    assert g.method == want.method == "gazetteer_exact"
    assert g.residual_m == pytest.approx(want.residual_m, abs=1.0)
    assert g.confidence == want.confidence == 0.719 and g.bucket == want.bucket == "medium"
    assert (g.lon, g.lat) == (want.lon, want.lat)
    assert not g.area_level and g.area_scope is None
    assert KARNAVATI not in g.alternatives and len(g.alternatives) == len(set(g.alternatives)) <= 3
    assert "SG Highway (Prahlad Nagar)" in g.alternatives


def test_every_sg_highway_report_lands_on_segment_1045(resolver):
    for s in testing.sg_highway_signals():
        g = resolver.resolve(s)
        assert g is not None and g.segment_id == 1045, (s.title, g)
        assert g.toponym in (KARNAVATI, "SG Highway (Prahlad Nagar)")


def test_a_road_toponym_is_on_the_network(resolver):
    g = resolver.resolve(testing.sg_highway_signals()[1])  # "... on SG Highway near Prahlad Nagar ..."
    assert g is not None and g.feature_type == "road" and g.toponym == "SG Highway (Prahlad Nagar)"
    assert g.segment_id == 1045 and g.residual_m == 0.0 and g.snapped_to is None


# ----------------------------------------------------------------------------------------------- Odhav
def test_odhav_replica_keeps_junction_11(resolver):
    g = resolver.resolve(testing.odhav_robbery_signal())
    assert g is not None
    assert (g.toponym, g.feature_type, g.junction_id, g.segment_id) == (ODHAV, "junction", 11, None)
    assert g.residual_m == 0.0 and g.snapped_to is None
    assert g.confidence == pytest.approx(0.718, abs=0.01) and g.bucket == "medium"


# ----------------------------------------------------------------------------------------------- area levels (R28)
def test_sachet_district_alert_is_district_level(resolver):
    g = resolver.resolve(testing.sachet_district_signal())
    assert g is not None
    assert g.area_level and g.area_scope == "district" and g.method == "area_fallback" and g.feature_type == "admin"
    assert (g.lon, g.lat) == (DISTRICT_AHMEDABAD.lon, DISTRICT_AHMEDABAD.lat)
    assert g.confidence <= 0.4 and g.bucket == "low"
    assert g.segment_id is None and g.junction_id is None and g.snapped_to is None and g.residual_m is None
    assert g.toponym == "Ahmedabad (district)"


def test_sachet_state_nowcast_is_state_level_without_a_point(resolver):
    g = resolver.resolve(testing.sachet_state_signal())
    assert g is not None
    assert g.area_level and g.area_scope == "state" and g.method == "area_fallback"
    assert g.lon is None and g.lat is None
    assert g.confidence <= 0.25 and g.toponym == "Gujarat (state)"
    assert g.segment_id is None and g.junction_id is None


def test_gdelt_in32_alone_is_none(resolver):
    s = make_signal("Clashes reported, details awaited", source="gdelt_events", publisher=None,
                    admin_codes=["GDELT_ADM1:IN32"])
    assert resolver.resolve(s) is None


def test_gdelt_in09_alone_is_state_level(resolver):
    s = make_signal("Protest reported, details awaited", source="gdelt_events", publisher=None,
                    admin_codes=["GDELT_ADM1:IN09"])
    g = resolver.resolve(s)
    assert g is not None and g.area_scope == "state" and g.lon is None and g.confidence <= 0.25


def test_gdelt_fullname_naming_ahmedabad_is_district_level(resolver):
    s = make_signal("Protest reported, details awaited", source="gdelt_events", publisher=None,
                    place_names=["Ahmedabad, Gujarat, India"], admin_codes=["GDELT_ADM1:IN09"])
    g = resolver.resolve(s)
    assert g is not None and g.area_scope == "district" and g.confidence <= 0.4
    assert (g.lon, g.lat) == (DISTRICT_AHMEDABAD.lon, DISTRICT_AHMEDABAD.lat)


def test_another_district_code_is_none(resolver):
    s = make_signal("Heavy rain warning for the district", source="sachet_cap", publisher="sachet.ndma.gov.in",
                    admin_codes=["LGD:GANDHINAGAR"])
    assert resolver.resolve(s) is None


def test_only_official_and_gdelt_sources_use_the_area_fallback(resolver):
    # a news or social payload carrying an admin code is not an official area: no city centroid for it
    for source, publisher in (("google_news_rss", "news-a.example"), ("reddit_rss", "social-a.example/r/example_city")):
        s = make_signal("Rain all evening, roads slow", source=source, publisher=publisher,
                        admin_codes=["LGD:AHMEDABAD"])
        assert resolver.resolve(s) is None, source


def test_a_finer_toponym_beats_the_area_code(resolver):
    s = make_signal("Waterlogging warning", "Waterlogging likely near Paldi Cross Roads during the next 3 hours.",
                    source="sachet_cap", publisher="sachet.ndma.gov.in", admin_codes=["LGD:AHMEDABAD"])
    g = resolver.resolve(s)
    assert g is not None and not g.area_level and g.junction_id == 4


# ----------------------------------------------------------------------------------------------- honest None
@pytest.mark.parametrize(
    "title",
    [
        "Markets close higher on festive demand",
        "Weather to stay dry through the weekend, says forecaster",
        "Cricket: home side wins the series 3-1",
        "",
    ],
)
def test_unresolvable_text_is_none(resolver, title):
    s = make_signal(title or "No place named here", "Nothing in this report names a place in the city.")
    assert resolver.resolve(s) is None


def test_a_city_name_alone_is_never_a_point(resolver):
    s = make_signal("Ahmedabad: traffic slow in the evening", "Ahmedabad saw slow traffic across the city.",
                    place_names=["Ahmedabad"])
    assert resolver.resolve(s) is None


# ------------------------------------------------------------------------------- "airport" is not a junction alias
@pytest.mark.parametrize(
    "title",
    [
        "Flights delayed at Delhi airport after fog",
        "Mumbai airport runway closed for repairs",
        "Bomb threat email sent to an airport",
    ],
)
def test_another_citys_airport_is_none(resolver, title):
    # "airport" was the first-word alias of junction 14 "Airport Circle (Hansol)": any city's airport pinned there
    assert resolver.resolve(make_signal(title, f"{title}. Passengers were told to check their flight status.")) is None


def test_the_airport_word_never_gives_airport_circle(resolver):
    s = make_signal("Fire at the airport in Ahmedabad", "Fire at the airport in Ahmedabad; flights were held.")
    g = resolver.resolve(s)
    assert g is None or g.junction_id != 14
    assert resolver.gazetteer.lookup("airport") == ()


def test_the_airport_and_airport_circle_by_their_own_names(resolver):
    g = resolver.resolve(make_signal("Smoke seen near Ahmedabad airport", "Smoke seen near Ahmedabad airport."))
    assert g is not None and g.toponym == "SVP International Airport" and g.feature_type == "landmark"
    # "Airport Circle" is a circle by any city's airport (review r2): it counts in a signal placed in the city
    for kwargs in (LOCAL, {"place_names": ["Ahmedabad"]}):
        s = make_signal("Jam at Airport Circle", "A long jam at Airport Circle this morning.", **kwargs)
        g = resolver.resolve(s)
        assert g is not None and g.junction_id == 14, kwargs
    assert resolver.resolve(make_signal("Jam at Airport Circle", "A long jam at Airport Circle this morning.")) is None


def test_a_town_a_junction_is_named_after_is_not_the_junction(resolver):
    # Dehgam is a town outside the city; Dehgam Circle (junction 31) is only on the road to it
    assert resolver.resolve(make_signal("Accident in Dehgam", "An accident in Dehgam town.", **LOCAL)) is None
    g = resolver.resolve(make_signal("Jam at Dehgam Circle", "A long jam at Dehgam Circle."))
    assert g is not None and g.junction_id == 31


# ----------------------------------------------------------------------- the context gate (common words, namesakes)
@pytest.mark.parametrize(
    "title",
    [
        "ISRO launches a new weather satellite",
        "Satellite TV channels raise prices",
        "ISKCON Bangalore celebrates festival",
        "Crowd at ISKCON temple in Bengaluru",
        "Bhadra wins award",
        "Karnavati Express delayed by four hours",
        "Heritage walk recalls old Karnavati",
        "Ring road jam in Surat",
        "Ring road jam in Rajkot",
        "Fire at civil hospital in Surat",
        "Mumbai riverfront project approved",
        "Fire on Gandhi Road in Chennai",
        "Vaishnodevi yatra resumes",
        "Accident near the civl hospital in Surat",  # fuzzy matching never reaches a gated form either
    ],
)
def test_context_forms_from_elsewhere_are_none(resolver, title):
    # a national outlet that names no Ahmedabad word: these words mean something else there
    assert resolver.resolve(make_signal(title, f"{title}. More details are awaited.")) is None


@pytest.mark.parametrize(
    ("title", "kwargs", "toponym"),
    [
        ("Waterlogging in Satellite, Ahmedabad", {}, "Satellite"),  # the text names the city
        ("Water main burst near Satellite, 380015", {}, "Satellite"),  # an Ahmedabad PIN
        ("Ahmedabad riverfront walkway closed", {}, "Sabarmati Riverfront"),
        ("Fire at civil hospital", LOCAL, "Civil Hospital Asarwa"),  # a city-scoped source
        ("Crowd outside the ISKCON temple", LOCAL, "ISKCON Temple"),
        ("Bhadra closed for repairs", {"place_names": ["Ahmedabad"]}, "Bhadra Fort"),  # a hint naming the city
    ],
)
def test_context_forms_count_in_a_text_about_the_city(resolver, title, kwargs, toponym):
    g = resolver.resolve(make_signal(title, f"{title}. More details are awaited.", **kwargs))
    assert g is not None and g.toponym == toponym and g.method == "gazetteer_exact"


def test_a_local_ring_road_report_is_on_the_ring_road(resolver):
    g = resolver.resolve(make_signal("Ring road jam", "Ring road jam near the toll plaza.", **LOCAL))
    assert g is not None and g.feature_type == "road" and g.toponym.startswith("SP Ring Road")


@pytest.mark.parametrize(
    ("title", "toponym"),
    [
        ("Car crash near Karnavati Club", KARNAVATI),
        ("Fire at Asarwa Civil Hospital", "Civil Hospital Asarwa"),
        ("Sabarmati Riverfront walkway closed", "Sabarmati Riverfront"),
        ("Signal down at Iskcon cross roads", "Iskcon Cross Roads (SG Highway)"),
    ],
)
def test_the_longer_forms_that_carry_the_place_are_never_gated(resolver, title, toponym):
    g = resolver.resolve(make_signal(title, f"{title}. More details are awaited."))  # a national outlet
    assert g is not None and g.toponym == toponym, (title, g)


def test_sp_ring_road_is_never_gated(resolver):
    g = resolver.resolve(make_signal("Jam on SP Ring Road after a breakdown", "Jam on SP Ring Road."))
    assert g is not None and g.feature_type == "road" and g.toponym.startswith("SP Ring Road")


# ------------------------------------------- the 132 Ft. Ring Road by its usual Latin spelling (review r3)
@pytest.mark.parametrize(
    ("title", "kwargs"),
    [
        ("Accident on 132 Feet Ring Road near Helmet Circle", LOCAL),
        ("Jam on 132 foot ring road", LOCAL),
        ("Jam on 132 Ft. Ring Road", LOCAL),
        ("Signal down on 132 Feet Ring Road", {"source": "amc_scrape", "publisher": None}),
        ("Waterlogging on 132 Feet Ring Road, Ahmedabad", {}),
        ("Waterlogging on 132 Feet Ring Road near IIM", {"place_names": ["Ahmedabad"]}),
    ],
)
def test_132_feet_ring_road_is_the_132_ft_ring_road_never_sp_ring_road(resolver, title, kwargs):
    # review r3: r/ahmedabad's "132 Feet Ring Road" gave SP Ring Road (West), seg 1033, at 0.75 high: another road
    sp_ring = {e.segment_id for e in resolver.gazetteer.entries if e.canonical_name.startswith("SP Ring Road")}
    assert sp_ring and 1033 in sp_ring and not sp_ring & {1041, 1044}
    s = make_signal(title, f"{title}. More details are awaited.", **kwargs)
    g = resolver.resolve(s)
    assert g is not None and g.feature_type == "road" and g.segment_id in {1041, 1044}, (title, g)
    assert g.segment_id not in sp_ring and not g.toponym.startswith("SP Ring Road")
    assert {rd["gaz_id"] for rd in resolver.explain(s)["readings"]} <= {75, 78}


def test_the_132_ft_ring_road_spellings_name_gaz_75_and_78(resolver):
    gaz = resolver.gazetteer
    assert set(gaz.lookup("132 ft ring road")) == {75, 78}
    for form in ("132 feet ring road", "132 foot ring road", "૧૩૨ ફૂટ રિંગ રોડ"):
        assert gaz.lookup(form) == gaz.lookup("132 ft ring road"), form
    assert translit.latin_variants("132 ft ring road") == ("132 feet ring road", "132 foot ring road")
    assert {"132 feet ring road", "132 foot ring road"} <= gaz.protect_set


def test_the_gate_covers_the_gujarati_and_hindi_spellings(resolver):
    assert {"રિંગ રોડ", "रिंग रोड", "સિવિલ હોસ્પિટલ", "सिविल अस्पताल", "રિવરફ્રન્ટ"} <= resolver.context_forms
    elsewhere = make_signal("સુરતમાં રિંગ રોડ પર ટ્રાફિક જામ", "સુરતમાં રિંગ રોડ પર ટ્રાફિક જામ.", language="gu")
    assert resolver.resolve(elsewhere) is None
    here = make_signal("અમદાવાદમાં રિંગ રોડ પર ટ્રાફિક જામ", "અમદાવાદમાં રિંગ રોડ પર ટ્રાફિક જામ.", language="gu")
    g = resolver.resolve(here)
    assert g is not None and g.feature_type == "road" and g.toponym.startswith("SP Ring Road")


def test_every_context_form_is_a_gazetteer_form_and_gated(resolver):
    for form in CONTEXT_FORMS:
        assert resolver.gazetteer.lookup(form), form
        assert form in resolver.context_forms, form
    # the state's name in the free text never opens the gate: Surat's ring road is in Gujarat too
    s = make_signal("Ring road jam in Surat, Gujarat", "Ring road jam in Surat, Gujarat.")
    assert resolver.resolve(s) is None
    assert resolver.explain(s)["context_open"] is False


def test_every_bare_route_code_is_gated(resolver):
    # a highway runs on through other towns and states: NH47 through Madhya Pradesh and Maharashtra (review r2)
    codes = {f for f in resolver.gazetteer.forms if re.fullmatch(r"(?:nh|ne|sh)\d+", f)}
    assert codes == {"nh47", "nh147", "sh41", "sh71"}
    assert codes <= resolver.context_forms


def test_the_script_spellings_of_the_gated_forms_are_gated(resolver):
    # from translit's tables and from osm_network.json's Gujarati junction names
    assert {"લાલ દરવાજા", "એરપોર્ટ સર્કલ", "ઇન્કમ ટેક્સ સર્કલ", "એરપોર્ટ રોડ", "एयरपोर्ट रोड", "ડૉ આંબેડકર રોડ",
            "डॉ अंबेडकर रोड", "જમાલપુર", "जमालपुर", "નહેરુ બ્રિજ", "नेहरू पुल", "ઉસ્માનપુરા", "ફ્લાવર પાર્ક",
            "રિવરફ્રન્ટ રોડ"} <= resolver.context_forms
    # the longer names that carry the place are never gated, in any script
    for form in ("એરપોર્ટ સર્કલ હાંસોલ", "સાબરમતી રિવરફ્રન્ટ", "જીએમડીસી ગ્રાઉન્ડ", "એસ પી રિંગ રોડ"):
        assert resolver.gazetteer.lookup(form) and form not in resolver.context_forms, form


def test_a_script_spelling_known_only_from_osm_is_gated_too(resolver):
    # osm_network.json's Gujarati names may spell a gated form that translit's tables do not list; the gate reads
    # them through to_latin ("નહેરુ બ્રિજ રોડ" → "nehru bridge road")
    form = norm("નહેરુ બ્રિજ રોડ")
    assert translit.script_aliases("nehru bridge road") == () and translit.to_latin(form) == "nehru bridge road"
    doc = json.loads(resolver.gazetteer.path.read_text(encoding="utf-8"))
    entry = next(e for e in doc["entries"] if e["gaz_id"] == 49)  # Nehru Bridge Road
    entry["surface_forms"] = sorted({*entry["surface_forms"], form})
    other = GazetteerResolver(gazetteer=Gazetteer.from_document(doc), network=resolver.network)
    assert form in other.context_forms
    elsewhere = make_signal("સુરતમાં નહેરુ બ્રિજ રોડ બંધ", "સુરતમાં નહેરુ બ્રિજ રોડ બંધ.", language="gu")
    assert other.resolve(elsewhere) is None
    here = make_signal("અમદાવાદમાં નહેરુ બ્રિજ રોડ બંધ", "અમદાવાદમાં નહેરુ બ્રિજ રોડ બંધ.", language="gu")
    g = other.resolve(here)
    assert g is not None and g.segment_id == 1015


# ------------------------------------------------- the gate opens on CITY-level evidence only (review r2, R28)
SACHET = {"source": "sachet_cap", "publisher": "sachet.ndma.gov.in"}
#: OS-2's GDELT hint: another Gujarat city's ActionGeo_FullName (with the state code IN09 on the events export)
SURAT = ["Surat, Gujarat, India"]


@pytest.mark.parametrize(
    ("title", "kwargs"),
    [
        ("Ring road jam in Surat", {"source": "gdelt_doc", "publisher": None, "place_names": SURAT}),
        ("Fire near civil hospital in Rajkot", {"source": "gdelt_doc", "publisher": None, "place_names": SURAT}),
        # a GDELT DOC article whose URL names only the state (OS-2's _url_place_hints)
        ("Riverfront project in Surat approved",
         {"source": "gdelt_doc", "publisher": None, "place_names": ["gujarat"]}),
        ("Janmashtami at ISKCON temple in Vadodara",
         {"source": "gdelt_doc", "publisher": None, "place_names": ["gujarat"]}),
        ("Fire at civil hospital in Surat", {"source": "gdelt_doc", "publisher": None, "place_names": ["gujarat"]}),
        # SACHET for another district: R28 says None
        ("Heat wave likely; civil hospital on alert in Gandhinagar",
         {**SACHET, "admin_codes": ["LGD:GANDHINAGAR"], "place_names": ["Gandhinagar"]}),
    ],
)
def test_state_or_other_city_evidence_never_opens_the_gate(resolver, title, kwargs):
    s = make_signal(title, f"{title}. More details are awaited.", **kwargs)
    assert resolver.resolve(s) is None, title
    ex = resolver.explain(s)
    assert ex["city_scoped"] is False and ex["context_open"] is False and ex["mentions"] == []


@pytest.mark.parametrize(
    ("title", "kwargs"),
    [
        ("Ring road jam in Surat",
         {"source": "gdelt_events", "publisher": None, "place_names": SURAT, "admin_codes": ["GDELT_ADM1:IN09"]}),
        ("Fire near civil hospital in Rajkot",
         {"source": "gdelt_events", "publisher": None, "place_names": SURAT, "admin_codes": ["GDELT_ADM1:IN09"]}),
        ("Riverfront project in Surat approved",
         {"source": "gdelt_doc", "publisher": None, "admin_codes": ["GDELT_ADM1:IN09"]}),
        ("Heavy rain alert: waterlogging on ring road in Surat",
         {**SACHET, "admin_codes": ["LGD:GUJARAT"], "place_names": ["Gujarat"]}),
        ("Thunderstorm warning for Rajkot; civil hospital on alert",
         {**SACHET, "admin_codes": ["LGD:GUJARAT"], "place_names": ["Gujarat"]}),
        ("Crowd advisory near the ISKCON temple in Vadodara",
         {"source": "gsdma", "publisher": None, "admin_codes": ["LGD:GUJARAT"], "place_names": ["Gujarat"]}),
    ],
)
def test_a_state_level_signal_naming_another_citys_place_stays_state_level(resolver, title, kwargs):
    s = make_signal(title, f"{title}. Stay indoors.", **kwargs)
    g = resolver.resolve(s)
    assert g is not None and g.area_scope == "state" and g.toponym == "Gujarat (state)", (title, g)
    assert g.lon is None and g.lat is None and g.confidence <= 0.25
    ex = resolver.explain(s)
    assert ex["city_scoped"] is False and ex["context_open"] is False
    assert resolver.source_locality(s) == 1.0  # the confidence term keeps the source's scope (the PoC's)


@pytest.mark.parametrize(
    ("title", "kwargs", "toponym"),
    [
        ("Heat wave likely; civil hospital on alert",
         {**SACHET, "admin_codes": ["LGD:AHMEDABAD"], "place_names": ["Ahmedabad"]}, "Civil Hospital Asarwa"),
        ("Protest outside the civil hospital",
         {"source": "gdelt_events", "publisher": None, "place_names": ["Ahmedabad, Gujarat, India"],
          "admin_codes": ["GDELT_ADM1:IN09"]}, "Civil Hospital Asarwa"),
        ("Protest outside the civil hospital",  # the GNS spelling a GDELT FullName may carry
         {"source": "gdelt_events", "publisher": None, "place_names": ["Ahmadabad, Gujarat, India"],
          "admin_codes": ["GDELT_ADM1:IN09"]}, "Civil Hospital Asarwa"),
        ("Fire at civil hospital", {"source": "gdelt_doc", "publisher": None, "place_names": ["ahmedabad", "gujarat"]},
         "Civil Hospital Asarwa"),
        ("Water supply cut near the civil hospital",
         {"source": "amc_scrape", "publisher": None, "admin_codes": ["LGD:AHMEDABAD"], "place_names": ["Ahmedabad"]},
         "Civil Hospital Asarwa"),
        ("Diversion on the ring road tonight", {"source": "ahmedabad_police_scrape", "publisher": None},
         "SP Ring Road"),
        ("Ring road jam", LOCAL, "SP Ring Road"),
    ],
)
def test_city_level_evidence_opens_the_gate(resolver, title, kwargs, toponym):
    s = make_signal(title, f"{title}. More details are awaited.", **kwargs)
    g = resolver.resolve(s)
    assert g is not None and g.toponym.startswith(toponym) and not g.area_level, (title, g)
    ex = resolver.explain(s)
    assert ex["city_scoped"] is True and ex["context_open"] is True


def test_city_scoped_reads_city_level_metadata_only(resolver):
    city = [
        make_signal("Rain all evening", **LOCAL),
        make_signal("Rain all evening", source="amc_scrape", publisher=None),
        make_signal("Rain all evening", source="ahmedabad_police_scrape", publisher=None),
        make_signal("Rain all evening", place_names=["Ahmedabad, Gujarat, India"]),
        make_signal("Rain all evening", place_names=["Ahmadabad"]),
        make_signal("Rain all evening", admin_codes=["LGD:AHMEDABAD"]),
        make_signal("Water main burst near the school, 380007"),
    ]
    state = [
        make_signal("Rain all evening", **SACHET),
        make_signal("Rain all evening", source="gsdma", publisher=None),
        make_signal("Rain all evening", place_names=["Gujarat"]),
        make_signal("Rain all evening", place_names=SURAT),
        make_signal("Rain all evening", admin_codes=["LGD:GUJARAT"]),
        make_signal("Rain all evening", admin_codes=["GDELT_ADM1:IN09"]),
    ]
    for s in city:
        assert resolver.city_scoped(s) and resolver.source_locality(s) == 1.0, s.raw_geo_hint
    for s in state:  # full source locality (the confidence term), but not in the city
        assert not resolver.city_scoped(s) and resolver.source_locality(s) == 1.0, s.raw_geo_hint
    plain = make_signal("Ahmedabad: rain all evening")  # a national outlet naming the city in its text
    assert not resolver.city_scoped(plain) and resolver.source_locality(plain) == 0.3


def test_the_gns_spelling_of_the_city_is_the_district(resolver):
    s = make_signal("Protest reported, details awaited", source="gdelt_events", publisher=None,
                    place_names=["Ahmadabad, Gujarat, India"], admin_codes=["GDELT_ADM1:IN09"])
    g = resolver.resolve(s)
    assert g is not None and g.area_scope == "district" and g.confidence <= 0.4


# ---------------------------------------------------------- namesakes of other cities and states (review r2)
@pytest.mark.parametrize(
    "title",
    [
        "Truck overturns on NH-47 near Indore",
        "Bus accident on NH 47 in Dhar district of Madhya Pradesh",
        "Accident on NH-147 near Gandhinagar",
        "Accident on SH-41 near Mehsana",
        "Accident on SH71 near Patan",
        "Fire on Dr Ambedkar Road in Dadar, Mumbai",
        "Waterlogging on Airport Road in Bengaluru",
        "Accident on Swami Vivekananda Road in Bandra",
        "Accident on Swami Vivekanand Road in Bandra",  # the fuzzy stage never reaches a gated form either
        "Bonalu celebrations at Lal Darwaza temple in Hyderabad",
        "Train derails near Jamalpur in Bihar",
        "GMDC lignite mine protest in Bhavnagar",
        "GMDC shares rise 5 percent",
        "Accident near RTO Circle in Rajkot",
        "Protest at Maharana Pratap Circle in Udaipur",
        "Traffic jam near Tapovan Circle in Nashik",
        "Nehru Bridge closed for repairs in Surat",
        "Nehru Bridge road closed in Surat",
        "Jam at Airport Circle in Vadodara",
        "Tulip show draws crowds at the flower park in Srinagar",
        "Riverfront road closed for a festival in Lucknow",
        "Water pipeline burst in Usmanpura, Aurangabad",
        "Notices issued by the income tax circle 2 in Pune",
        "Methi na gota: a monsoon recipe",
        "Gota patti lace sales rise before the wedding season",
        # "Gandhi Ashram" is a name many places share: Sevagram in Wardha, Bhitiharwa in Champaran (review r3)
        "Prayer meeting held at Gandhi Ashram in Wardha",
        "Exhibition opens at the Gandhi Ashram in Bhitiharwa, Champaran",
        "Khadi sale at the Gandhi Ashram store in Lucknow",
    ],
)
def test_namesakes_from_elsewhere_are_none(resolver, title):
    # a national outlet whose text names no Ahmedabad word, one mention and two
    for text in (f"{title}. More details are awaited.", title):
        assert resolver.resolve(make_signal(title, text)) is None, (title, text)


@pytest.mark.parametrize(
    ("title", "kwargs", "want"),
    [
        ("Truck overturns on NH-47, Ahmedabad", {}, {"segment_id": 1021}),
        ("Waterlogging on Dr Ambedkar Road in Ahmedabad", {}, {"segment_id": 1043}),
        ("Maharana Pratap Circle jam, Ahmedabad", {}, {"segment_id": 1043}),
        ("Accident near RTO Circle, Ahmedabad", {}, {"segment_id": 1041}),
        ("Nehru Bridge closed for repairs, Ahmedabad", {}, {"segment_id": 1015}),
        ("Jamalpur flower market reopens, Ahmedabad", {}, {"toponym": "Jamalpur"}),
        ("Water main burst in Usmanpura, 380013", {}, {"toponym": "Usmanpura"}),
        ("Lal Darwaja bus terminus crowded", LOCAL, {"junction_id": 3}),
        ("Navratri crowd near GMDC", LOCAL, {"toponym": "GMDC Ground"}),
        ("Waterlogging in Gota after heavy rain", LOCAL, {"toponym": "Gota"}),
        ("Flower park reopens after repairs", LOCAL, {"toponym": "Riverfront Flower Park"}),
        ("Jam at Income Tax Circle", LOCAL, {"junction_id": 2}),
        ("Tapovan Circle signal down", LOCAL, {"segment_id": 1034}),
        ("Airport Road jam after a breakdown", {"source": "amc_scrape", "publisher": None}, {"feature_type": "road"}),
        ("Garba night at GMDC Ground", {}, {"toponym": "GMDC Ground"}),  # the longer form is never gated
        # "Gandhi Ashram" (review r3): gaz 119 in a signal placed in the city; the longer names are never gated
        ("Crowd at Gandhi Ashram, Ahmedabad", {}, {"toponym": "Sabarmati Ashram (Gandhi Ashram)", "segment_id": 1041}),
        ("Crowd at Gandhi Ashram", LOCAL, {"toponym": "Sabarmati Ashram (Gandhi Ashram)", "segment_id": 1041}),
        ("Crowd at Sabarmati Ashram", {}, {"toponym": "Sabarmati Ashram (Gandhi Ashram)", "segment_id": 1041}),
        ("Signal down at Gandhi Ashram Junction", {}, {"junction_id": 7}),
    ],
)
def test_namesakes_count_in_a_signal_placed_in_the_city(resolver, title, kwargs, want):
    g = resolver.resolve(make_signal(title, f"{title}. More details are awaited.", **kwargs))
    assert g is not None, title
    for key, value in want.items():
        assert getattr(g, key) == value, (title, key, getattr(g, key))


@pytest.mark.parametrize(
    ("title", "language"),
    [
        ("Prayer meeting held at Gandhi Ashram in Wardha", "en"),
        ("वर्धा के गांधी आश्रम में प्रार्थना सभा", "hi"),
        ("વર્ધાના ગાંધી આશ્રમમાં પ્રાર્થના સભા", "gu"),
    ],
)
def test_a_gandhi_ashram_elsewhere_is_none_in_every_script(resolver, title, language):
    # review r3: a national outlet's Wardha story was Sabarmati Ashram, seg 1041, 0.678 medium
    assert resolver.resolve(make_signal(title, f"{title}.", language=language)) is None, title
    assert resolver.resolve(make_signal(title, title, language=language)) is None, title


@pytest.mark.parametrize(
    ("title", "kwargs", "language"),
    [
        ("Crowd at Gandhi Ashram, Ahmedabad", {}, "en"),
        ("Crowd at Gandhi Ashram", LOCAL, "en"),
        ("અમદાવાદમાં ગાંધી આશ્રમ પાસે ભીડ", {}, "gu"),
        ("ગાંધી આશ્રમ પાસે ભીડ", LOCAL, "gu"),
        ("अहमदाबाद में गांधी आश्रम के पास भीड़", {}, "hi"),
    ],
)
def test_gandhi_ashram_in_a_signal_placed_in_the_city_is_gaz_119(resolver, title, kwargs, language):
    s = make_signal(title, f"{title}.", language=language, **kwargs)
    g = resolver.resolve(s)
    assert g is not None and g.toponym == resolver.gazetteer.by_id[119].canonical_name and g.segment_id == 1041
    assert resolver.explain(s)["readings"][0]["gaz_id"] == 119


def test_the_gandhi_ashram_gate_covers_its_spellings_but_not_the_junction(resolver):
    assert {"gandhi ashram", "ગાંધી આશ્રમ", "गांधी आश्रम"} <= resolver.context_forms
    for form in ("gandhi ashram junction", "ગાંધી આશ્રમ જંક્શન", "sabarmati ashram", "સાબરમતી આશ્રમ"):
        assert resolver.gazetteer.lookup(form) and form not in resolver.context_forms, form


def test_an_ambiguous_stadium_name_is_no_alias(resolver):
    # "Sardar Patel Stadium" names Motera's stadium (its old name) and Navrangpura's (review r2): no alias at all
    assert resolver.gazetteer.lookup("sardar patel stadium") == ()
    g = resolver.resolve(make_signal("Kabaddi league at Sardar Patel Stadium, Navrangpura", "Matches begin today."))
    assert g is not None and g.toponym == "Navrangpura"
    g = resolver.resolve(make_signal("Crowds at Narendra Modi Stadium", "Crowds at Motera stadium."))
    assert g is not None and g.toponym == "Narendra Modi Stadium (Motera)"


# ------------------------------------------------------------- "Sabarmati": the river and the train (review r2)
@pytest.mark.parametrize(
    ("title", "language"),
    [
        ("Flood alert along Sabarmati river", "en"),
        ("Water released into the Sabarmati riverbed from the dam", "en"),
        ("સાબરમતી નદીમાં પાણી છોડાયું", "gu"),
    ],
)
def test_an_alert_along_the_sabarmati_river_is_not_the_neighbourhood(resolver, title, language):
    s = make_signal(title, f"{title}.", admin_codes=["LGD:GUJARAT"], place_names=["Gujarat"], language=language,
                    **SACHET)
    g = resolver.resolve(s)
    assert g is not None and g.area_scope == "state" and g.toponym == "Gujarat (state)", (title, g)


@pytest.mark.parametrize(
    ("title", "language"),
    [("Sabarmati Express derailed near Ayodhya", "en"), ("साबरमती एक्सप्रेस देरी से चल रही है", "hi")],
)
def test_the_sabarmati_express_is_a_train(resolver, title, language):
    assert resolver.resolve(make_signal(title, f"{title}.", language=language)) is None
    assert resolver.resolve(make_signal(title, f"{title}.", language=language, **LOCAL)) is None


@pytest.mark.parametrize(
    ("title", "toponym"),
    [
        ("Water logging in Sabarmati after heavy rain", "Sabarmati"),
        ("Sabarmati Riverfront walkway closed", "Sabarmati Riverfront"),
        ("Sabarmati river front walkway closed", "Sabarmati Riverfront"),
        ("Crowd at Sabarmati Ashram", "Sabarmati Ashram (Gandhi Ashram)"),
        ("સાબરમતીમાં પાણી ભરાયાં", "Sabarmati"),
    ],
)
def test_the_sabarmati_places_still_resolve(resolver, title, toponym):
    g = resolver.resolve(make_signal(title, f"{title}. More details are awaited."))
    assert g is not None and g.toponym == toponym, (title, g)


# ------------------------------------- a state-level alert naming the bare river name stays state level (review r3)
#: the river named without the next word "river": "into Sabarmati", "Sabarmati in spate", a Gujarati case ending
RIVER_ALERTS = [
    ("Water released from Dharoi dam into Sabarmati; low lying villages alerted", "en"),
    ("Flood warning: Sabarmati in spate after heavy rain upstream", "en"),
    ("ધરોઈ ડેમમાંથી સાબરમતીમાં પાણી છોડાયું", "gu"),
    ("धरोई बांध से साबरमती में पानी छोड़ा गया", "hi"),
    ("Flood warning: Sabarmathi in spate after heavy rain upstream", "en"),
]
#: GDELT's events export: a Gujarat ActionGeo_FullName that is not Ahmedabad, with the state code
GDELT_IN09 = {"source": "gdelt_events", "publisher": None, "admin_codes": ["GDELT_ADM1:IN09"]}


@pytest.mark.parametrize(
    "kwargs",
    [
        {**SACHET, "admin_codes": ["LGD:GUJARAT"], "place_names": ["Gujarat"]},
        {"source": "gsdma", "publisher": None, "admin_codes": ["LGD:GUJARAT"], "place_names": ["Gujarat"]},
        {**GDELT_IN09, "place_names": ["Mehsana, Gujarat, India"]},
        {**GDELT_IN09, "place_names": ["Gujarat, India"]},
    ],
    ids=["sachet-lgd-gujarat", "gsdma-lgd-gujarat", "gdelt-in09-mehsana", "gdelt-in09-gujarat"],
)
@pytest.mark.parametrize(("title", "language"), RIVER_ALERTS)
def test_a_state_level_alert_naming_the_river_stays_state_level(resolver, title, language, kwargs):
    # review r3: these gave the 'Sabarmati' neighbourhood, seg 1032, 0.615 medium, with a point in the city
    s = make_signal(title, f"{title}.", language=language, **kwargs)
    g = resolver.resolve(s)
    assert g is not None and g.toponym == "Gujarat (state)", (title, g)
    assert g.area_level and g.area_scope == "state" and g.method == "area_fallback" and g.feature_type == "admin"
    assert g.lon is None and g.lat is None and g.confidence == 0.25
    assert g.segment_id is None and g.junction_id is None
    ex = resolver.explain(s)
    assert ex["state_scoped"] is True and ex["city_scoped"] is False and ex["mentions"] == []


def test_the_state_gate_covers_every_spelling_of_the_bare_river_name(resolver):
    assert resolver.state_forms == {"sabarmati", "sabarmathi", "સાબરમતી", "साबरमती"}
    assert set(resolver_mod.STATE_GATED_FORMS) == {"sabarmati"}
    # the longer names that carry the place are never state-gated
    for form in ("sabarmati riverfront", "sabarmati ashram", "સાબરમતી રિવરફ્રન્ટ", "સાબરમતી આશ્રમ"):
        assert resolver.gazetteer.lookup(form) and form not in resolver.state_forms, form


@pytest.mark.parametrize(
    ("title", "kwargs", "language"),
    [
        # the district code is city-level evidence: the neighbourhood
        ("Waterlogging in Sabarmati area", {**SACHET, "admin_codes": ["LGD:AHMEDABAD"], "place_names": ["Ahmedabad"]},
         "en"),
        ("Waterlogging in Sabarmati area", {**SACHET, "admin_codes": ["LGD:AHMEDABAD"]}, "en"),
        # a state alert whose text names the city: the city word is city-level evidence
        ("Waterlogging in Sabarmati, Ahmedabad", {**SACHET, "admin_codes": ["LGD:GUJARAT"], "place_names": ["Gujarat"]},
         "en"),
        ("અમદાવાદમાં સાબરમતી વિસ્તારમાં પાણી ભરાયાં",
         {**SACHET, "admin_codes": ["LGD:GUJARAT"], "place_names": ["Gujarat"]}, "gu"),
        # GDELT's FullName naming the city
        ("Waterlogging in Sabarmati area", {**GDELT_IN09, "place_names": ["Ahmedabad, Gujarat, India"]}, "en"),
        # a national outlet with no state evidence keeps the form (the PoC's parity row)
        ("Remains found in Sabarmati, police say", {}, "en"),
        ("Waterlogging in Sabarmati area", {}, "en"),
    ],
)
def test_city_level_evidence_or_none_keeps_the_sabarmati_neighbourhood(resolver, title, kwargs, language):
    s = make_signal(title, f"{title}.", language=language, **kwargs)
    g = resolver.resolve(s)
    assert g is not None and g.toponym == "Sabarmati" and g.feature_type == "neighbourhood", (title, kwargs, g)
    # an area (F-HONEST OSINT-3): its point, never Motera Stadium Road 1.2 km away as its segment
    assert g.segment_id is None and g.junction_id is None and g.snapped_to is None and g.residual_m is None
    assert g.lon is not None and g.lat is not None


# ---------------------------------------------------------------------------- the geo hints read (review r2)
def test_only_the_first_hints_are_read(resolver):
    assert (resolver_mod.MAX_HINTS, resolver_mod.MAX_HINT_CHARS) == (8, 200)
    filler = [f"filler {i}" for i in range(8)]
    s = make_signal("Road blocked after a fall of trees", "Traffic diverted.", place_names=[*filler, "Law Garden"])
    assert resolver.resolve(s) is None  # the ninth hint is not read
    s = make_signal("Road blocked after a fall of trees", "Traffic diverted.", place_names=[*filler, "Ahmedabad"])
    assert resolver.source_locality(s) == 0.3 and not resolver.city_scoped(s)
    cut = make_signal("Road blocked after a fall of trees", "Traffic diverted.",
                      place_names=["x" * 200 + " Law Garden"])
    assert resolver.resolve(cut) is None  # past the hint's 200th character
    within = make_signal("Road blocked after a fall of trees", "Traffic diverted.",
                         place_names=[*filler[:-1], "Law Garden"])
    g = resolver.resolve(within)
    assert g is not None and g.toponym == "Law Garden"


def test_a_maximal_hostile_signal_stays_cheap(resolver):
    # 64 hints of 1000 characters of near-miss names: no exact form, so the fuzzy stage scans what is read
    import time

    words = ["karnavatii", "cluub", "laww", "gardenn", "sabarmatii", "ashramm", "pakwann", "crosss", "roadss"]
    blob = " ".join(words[i % len(words)] for i in range(400))
    s = make_signal(blob[:1000], blob[:4000], place_names=[blob[:1000]] * 64, **LOCAL)
    t0 = time.perf_counter()
    resolver.resolve(s)
    assert time.perf_counter() - t0 < 1.0


def test_the_operator_lookup_is_about_the_city(resolver):
    # GET /osint/gazetteer/resolve: an operator's query is local, so the gate is open
    top = resolver.resolve_text("satellite")
    assert top and top[0]["canonical_name"] == "Satellite"


# ----------------------------------------------------------------------------------- generator aliases (review r1)
def test_a_bridge_the_road_runs_over_names_the_road(resolver):
    g = resolver.resolve(make_signal("Book market near Fernandes Bridge reopens", "The book market reopened."))
    assert g is not None and g.segment_id == 1012 and g.toponym == "Gandhi Road"


def test_the_astodia_darwaza_crossing_is_junction_5(resolver):
    # the one OSM "... cross road" name is the crossing at junction 5, not an alias splitting it over two segments
    g = resolver.resolve(make_signal("Traffic jam near Astodia Darwaza cross road", "Jam near the crossing."))
    assert g is not None and g.junction_id == 5 and g.toponym == "Astodia Darwaja"


# ------------------------------------------------------------------------------------ social, grammar, scripts
def test_social_post_resolves_to_the_junction_it_names(resolver):
    g = resolver.resolve(testing.social_single_signal())
    assert g is not None and g.junction_id == 4 and g.feature_type == "junction"
    # r/<community> is a city-scoped source: full locality
    assert resolver.source_locality(testing.social_single_signal()) == 1.0


def test_char_rasta_is_rewritten_to_the_junction(resolver):
    s = make_signal("Car fire near Paldi char rasta", "A car caught fire near Paldi char rasta on Monday.")
    g = resolver.resolve(s)
    assert g is not None and g.junction_id == 4 and g.method == "grammar"
    # the bare "paldi" would also read as the neighbourhood: the rewrite is unambiguous
    assert "Paldi" not in g.alternatives


def test_darwaza_spelling_reaches_the_darwaja(resolver):
    s = make_signal("Shops shut near Astodia darwaza", "Shops near Astodia darwaza were shut for the day.")
    g = resolver.resolve(s)
    assert g is not None and g.junction_id == 5


def test_gujarati_text_with_a_case_ending(resolver):
    s = make_signal("મણિનગરમાં આગ", "મણિનગરમાં એક દુકાનમાં આગ લાગી.", language="gu")
    g = resolver.resolve(s)
    assert g is not None and g.toponym == "Maninagar" and g.feature_type == "neighbourhood"
    assert g.segment_id is None and g.junction_id is None  # an area, not Kankaria Road 2 km away


def test_gujarati_chokdi_reads_as_cross_roads(resolver):
    s = make_signal("થલતેજ ચોકડી પાસે અકસ્માત", "થલતેજ ચોકડી પાસે અકસ્માત થયો.", language="gu")
    g = resolver.resolve(s)
    assert g is not None and g.junction_id == 17


def test_hindi_text(resolver):
    s = make_signal("मणिनगर में आग", "मणिनगर में एक दुकान में आग लगी।", language="hi")
    g = resolver.resolve(s)
    assert g is not None and g.toponym == "Maninagar"


@pytest.mark.parametrize(
    ("text", "form"),
    [
        ("કાંકરિયા તળાવે ભીડ", "કાંકરિયા તળાવ"),  # the vowel sign after a consonant: "at the lake"
        ("મણિનગરે આગ", "મણિનગર"),
        ("પાલડીએ અકસ્માત", "પાલડી"),  # the vowel letter after a vowel: "at Paldi"
    ],
)
def test_both_spellings_of_the_gujarati_e_ending(resolver, text, form):
    mentions = resolver.mentions(text, city=True)
    assert [m.form for m in mentions] == [form]


def test_a_landmark_near_a_junction_still_snaps_to_a_segment(resolver):
    s = make_signal("Crowd outside ISKCON temple", "A large crowd gathered outside the ISKCON temple.", **LOCAL)
    g = resolver.resolve(s)
    assert g is not None and g.feature_type == "landmark" and g.toponym == "ISKCON Temple"
    assert g.segment_id is not None and g.junction_id is None and g.snapped_to


def test_place_name_hints_are_read(resolver):
    s = make_signal("Road blocked after a fall of trees", "Traffic diverted after trees fell.",
                    place_names=["Law Garden"])
    g = resolver.resolve(s)
    assert g is not None and g.toponym == "Law Garden"


# ----------------------------------------------------------------------------------------------- confidence inputs
def test_source_locality(resolver):
    assert resolver.source_locality(testing.sg_highway_signals()[0]) == 0.3  # a national aggregator, no hint
    assert resolver.source_locality(testing.sachet_district_signal()) == 1.0
    hinted = make_signal("Rain at Paldi", place_names=["Ahmedabad"])
    assert resolver.source_locality(hinted) == 1.0
    pinned = make_signal("Water main burst", "A water main burst near the school, 380007.")
    assert resolver.source_locality(pinned) == 1.0
    # the city's name in the free text is not locality (national outlets name it in passing)
    assert resolver.source_locality(make_signal("Ahmedabad: rain at Paldi")) == 0.3


def test_repeated_mentions_never_inflate_confidence(resolver):
    once = make_signal("Fire near Kankaria Lake", "Fire brigade called.")
    twice = make_signal("Fire near Kankaria Lake", "Fire near Kankaria Lake, fire brigade called.", n=2)
    g1, g2 = resolver.resolve(once), resolver.resolve(twice)
    assert g1 is not None and g2 is not None and g1.toponym == g2.toponym == "Kankaria Lake"
    assert g2.confidence <= g1.confidence


def test_confidence_and_bucket_agree(resolver):
    for s in [*testing.sg_highway_signals(), testing.odhav_robbery_signal(), testing.social_single_signal()]:
        g = resolver.resolve(s)
        assert g is not None
        assert g.bucket == ("high" if g.confidence >= 0.75 else "medium" if g.confidence >= 0.5 else "low")


# ----------------------------------------------------------------------------------------------- determinism, threads
def _all_fixture_signals() -> list[RawOsintSignal]:
    return [
        *testing.sg_highway_signals(),
        testing.odhav_robbery_signal(),
        testing.sachet_district_signal(),
        testing.sachet_state_signal(),
        testing.social_single_signal(),
    ]


def test_deterministic_across_resolvers(resolver):
    other = GazetteerResolver()
    for s in _all_fixture_signals():
        a, b, c = resolver.resolve(s), resolver.resolve(s), other.resolve(s)
        assert (a and a.model_dump()) == (b and b.model_dump()) == (c and c.model_dump())


def test_thread_safe_after_load(resolver):
    signals = _all_fixture_signals()
    want = [g and g.model_dump() for g in (resolver.resolve(s) for s in signals)]
    errors: list[BaseException] = []
    results: list[list] = []

    def work() -> None:
        try:
            for _ in range(20):
                results.append([g and g.model_dump() for g in (resolver.resolve(s) for s in signals)])
        except BaseException as exc:  # pragma: no cover - reported below
            errors.append(exc)

    threads = [threading.Thread(target=work) for _ in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert not errors
    assert all(r == want for r in results) and len(results) == 160


def test_a_mapping_is_validated_as_a_raw_signal(resolver):
    s = testing.odhav_robbery_signal()
    g = resolver.resolve(s.model_dump(mode="json"))
    assert g is not None and g.junction_id == 11
    bad = s.model_dump(mode="json")
    bad["author"] = "someone"  # a person key never gets through
    with pytest.raises(ValueError, match="forbidden_key"):
        resolver.resolve(bad)


def test_geocodes_name_places_never_persons(resolver):
    for s in _all_fixture_signals():
        g = resolver.resolve(s)
        if g is not None:
            dumped = g.model_dump(mode="json")
            ethics.assert_no_person_keys(dumped)
            assert set(dumped) == set(Geocode.model_fields)


def test_explain_reports_forms_never_the_text(resolver):
    s = testing.sg_highway_signals()[0]
    ex = resolver.explain(s)
    assert ex["geocode"]["toponym"] == KARNAVATI and ex["locality"] == 0.3
    assert {m["form"] for m in ex["mentions"]} >= {"karnavati club", "sg highway"}
    assert s.title not in repr(ex) and "speeding" not in repr(ex)


def test_default_resolver_is_shared():
    assert resolver_mod.default_resolver() is resolver_mod.default_resolver()


def test_a_hostile_text_stays_cheap(resolver):
    # a 4000-character text that repeats an eight-segment name: coherence runs over the distinct points, not pairs
    import time

    body = ("ring road " * 400)[:3990]
    s = make_signal("Ring road, Ahmedabad", body)  # the city named: the context gate is open
    t0 = time.perf_counter()
    g = resolver.resolve(s)
    assert time.perf_counter() - t0 < 1.0
    assert g is not None and g.feature_type == "road" and g.segment_id in resolver.network.segments
    # the same text from elsewhere is no mention at all, just as fast
    t0 = time.perf_counter()
    assert resolver.resolve(make_signal("Ring road", body)) is None
    assert time.perf_counter() - t0 < 1.0


# ---------------------------------------------------------------------------- F-HONEST OSINT-1 / OSINT-3
def test_an_area_mention_is_never_pinned_on_the_junction_named_after_it(resolver):
    # the audit's int3c case, paraphrased: a neighbourhood and a different bridge, pinned on junction 11 at
    # residual 0.0 with method gazetteer_exact
    s = make_signal("Lakhs looted after youth kidnapped in Ahmedabad: abducted from Odhav's Rajendra Park Bridge",
                    "Abducted from Odhav's Rajendra Park Bridge, police said.")
    g = resolver.resolve(s)
    assert g is not None and g.toponym == "Odhav" and g.feature_type == "neighbourhood"
    assert g.junction_id is None and g.segment_id is None and g.residual_m is None
    # the junction's own name still pins the junction
    g = resolver.resolve(make_signal("Robbery at Odhav Ring Road Circle", "Robbery at Odhav Ring Road Circle."))
    assert g is not None and g.junction_id == 11


@pytest.mark.parametrize("word", ["Sola", "Motera", "Sarkhej"])
def test_a_bare_area_word_without_an_area_entry_is_honestly_unplaced(resolver, word):
    g = resolver.resolve(make_signal(f"Water supply cut in {word} today", f"Water supply cut in {word} today."))
    assert g is None or g.junction_id is None


def test_a_landmark_beyond_900_m_keeps_no_segment_and_no_snap_credit(resolver):
    g = resolver.resolve(make_signal("Crowd at Kankaria Lake", "Huge crowd at Kankaria Lake this evening."))
    assert g is not None and g.toponym == "Kankaria Lake"
    assert g.segment_id is None and g.snapped_to is None and g.residual_m is None
