"""attach(): read-only. Novel against the Kalupur-pursuit live fixture; corroborates an ACTIVE live corridor event
(an ``event:`` URN) of a compatible kind within 900 m (or on its route) that overlaps in time; never a convoy, a
protected movement, a pursuit or an ANPR event; never for an area-level situation, chatter, a stale report or no
live state."""

from __future__ import annotations

from datetime import timedelta

from analysis_fixtures import (
    FETCHED,
    KALUPUR_PURSUIT,
    KARNAVATI_CLUB,
    NEHRU_BRIDGE_ROAD,
    FakeResolver,
    at,
    district,
    karnavati,
    live_event,
    live_state,
    make_signal,
    offset,
    point,
    road,
    sg_highway_geocodes,
)
from osint_common import testing
from osint_common import kinds
from osint_analysis.attach import ATTACH_RADIUS_M, CORROBORATING_KINDS, LiveSubject, attach, attach_one
from osint_analysis.classify import classify
from osint_analysis.correlate import correlate
from osint_analysis.fusion import make_member, stage1
from osint_analysis.pipeline import run_pipeline

EVENT = "event:00000000-0000-4000-8000-0000000000aa"


def situations(signals, geocodes):
    by_id = {g.signal_id: g for g in geocodes}
    return correlate(stage1([make_member(s, by_id[s.signal_id], classify(s)) for s in signals]))


def test_sg_highway_is_novel_against_the_kalupur_pursuit():
    sg = testing.sg_highway_signals()
    live = testing.live_state_kalupur_pursuit()
    before = live.model_dump_json()
    (sit,) = situations(sg, sg_highway_geocodes(sg))
    result = attach([sit], live)
    assert [r.novel for r in result] == [True]
    assert result[0].corroborates_live_urn is None
    assert live.model_dump_json() == before  # read-only
    run = run_pipeline(sg, resolver=FakeResolver(sg_highway_geocodes(sg)), live=live)
    assert run.resolved[0].attach.novel and run.counts.attached_to_live == 0


def test_corroborates_a_live_event_within_900_m_that_overlaps_in_time():
    crash = make_signal(title="Multi-vehicle crash near Karnavati Club", published_at=at(60))
    live = live_state(live_event(EVENT, kind="road_accident", lonlat=offset(KARNAVATI_CLUB, east_m=600)))
    (sit,) = situations([crash], [karnavati(crash)])
    got = attach_one(sit, live)
    assert not got.novel and got.corroborates_live_urn == EVENT
    assert 590 <= got.distance_m <= 610
    run = run_pipeline([crash], resolver=FakeResolver([karnavati(crash)]), live=live)
    assert run.resolved[0].attach.corroborates_live_urn == EVENT and run.counts.attached_to_live == 1


def test_beyond_900_m_is_novel():
    crash = make_signal(title="Multi-vehicle crash near Karnavati Club", published_at=at(60))
    beyond = offset(KARNAVATI_CLUB, east_m=ATTACH_RADIUS_M + 150)
    live = live_state(live_event(EVENT, kind="road_accident", lonlat=beyond))
    (sit,) = situations([crash], [karnavati(crash)])
    assert attach_one(sit, live).novel


def test_on_the_live_route_corroborates_even_beyond_900_m():
    # a report on Nehru Bridge Road (segment 1015); a promoted accident event whose route spine is that segment and
    # whose point is ~1 km away
    report = make_signal(title="Multi-vehicle crash on Nehru Bridge Road", published_at=at(60))
    geo = road(report, 1015, NEHRU_BRIDGE_ROAD, toponym="Nehru Bridge Road")
    (sit,) = situations([report], [geo])
    accident = live_event(EVENT, kind="road_accident", lonlat=KALUPUR_PURSUIT, segments=[1015])
    got = attach_one(sit, live_state(accident))
    assert not got.novel and got.corroborates_live_urn == EVENT
    assert got.distance_m > ATTACH_RADIUS_M


def test_a_report_on_the_pursuit_route_never_corroborates_the_pursuit():
    # the same crash lies on the Kalupur pursuit's spine (segment 1015): a pursuit is human-initiated and OSINT never
    # links a report to it
    report = make_signal(title="Multi-vehicle crash on Nehru Bridge Road", published_at=at(60))
    geo = road(report, 1015, NEHRU_BRIDGE_ROAD, toponym="Nehru Bridge Road")
    (sit,) = situations([report], [geo])
    live = testing.live_state_kalupur_pursuit()
    assert 1015 in live.live_events[0].segment_ids and live.live_events[0].event_kind == "vehicle_pursuit"
    assert attach_one(sit, live).novel
    run = run_pipeline([report], resolver=FakeResolver([geo]), live=live)
    assert run.resolved[0].attach.novel and run.counts.attached_to_live == 0


def test_a_convoy_or_any_ref_that_is_not_a_corridor_event_is_never_corroborated():
    crash = make_signal(title="Multi-vehicle crash near Karnavati Club", published_at=at(60))
    near = offset(KARNAVATI_CLUB, east_m=400)
    (sit,) = situations([crash], [karnavati(crash)])
    for urn in ("convoy:mv-0042", "movement:mv-0042", "dispatch:00000000-0000-4000-8000-0000000000d1"):
        for kind in ("protected_movement", "road_accident"):
            ref = live_event(urn, kind=kind, lonlat=near, segments=[1045])
            assert attach_one(sit, live_state(ref)).novel, (urn, kind)
    convoy = live_event("convoy:mv-0042", kind="protected_movement", lonlat=near)
    run = run_pipeline([crash], resolver=FakeResolver([karnavati(crash)]), live=live_state(convoy))
    (event,) = run.resolved
    assert event.attach.novel and event.attach.corroborates_live_urn is None
    assert run.counts.attached_to_live == 0
    assert [f.kind for f in event.second_order] == ["convoy"]  # a second-order effect, not a corroboration


def test_a_protected_movement_is_never_corroborated_only_flagged():
    # an accident on segment 1045, which an active VVIP movement's route uses; the movement's point is 5 km away
    crash = make_signal(title="Multi-vehicle crash near Karnavati Club on SG Highway", published_at=at(60))
    vvip = live_event(EVENT, kind="protected_movement", lonlat=offset(KARNAVATI_CLUB, north_m=5000), segments=[1045])
    (sit,) = situations([crash], [karnavati(crash)])
    assert attach_one(sit, live_state(vvip)).novel
    near = live_event(EVENT, kind="protected_movement", lonlat=offset(KARNAVATI_CLUB, east_m=200))
    assert attach_one(sit, live_state(near)).novel  # within 900 m: still a different situation
    (event,) = run_pipeline([crash], resolver=FakeResolver([karnavati(crash)]), live=live_state(vvip)).resolved
    assert event.attach.novel
    assert [(f.kind, f.urn, f.segment_id) for f in event.second_order] == [("protected_corridor", EVENT, 1045)]


def test_only_a_live_event_of_a_compatible_kind_is_corroborated():
    crash = make_signal(title="Multi-vehicle crash near Karnavati Club", published_at=at(60))
    (sit,) = situations([crash], [karnavati(crash)])
    near = offset(KARNAVATI_CLUB, east_m=300)
    for kind in ("procession", "mass_gathering", "work_zone", "hazard", "crime_incident", "vehicle_pursuit"):
        assert attach_one(sit, live_state(live_event(EVENT, kind=kind, lonlat=near))).novel, kind
    accident = live_event(EVENT, kind="road_accident", lonlat=near)
    assert attach_one(sit, live_state(accident)).corroborates_live_urn == EVENT
    # a correlated situation corroborates an event of any of its classes' kinds (affray+collision: public_disorder)
    sg = testing.sg_highway_signals()
    (composite,) = situations(sg, sg_highway_geocodes(sg))
    disorder = live_event(EVENT, kind="public_disorder", lonlat=near)
    assert attach_one(composite, live_state(disorder, as_of=at(120))).corroborates_live_urn == EVENT
    # a crowd report corroborates a planned gathering that is now active; a reported crime never an ANPR event
    crowd = make_signal(title="Huge crowd at the Karnavati Club fair", published_at=at(60))
    (gathering,) = situations([crowd], [karnavati(crowd)])
    assert not attach_one(gathering, live_state(live_event(EVENT, kind="mass_gathering", lonlat=near))).novel
    robbery = make_signal(title="Jewellery shop robbed near Karnavati Club", published_at=at(60))
    (crime,) = situations([robbery], [karnavati(robbery)])
    assert attach_one(crime, live_state(live_event(EVENT, kind="crime_incident", lonlat=near))).novel
    assert not attach_one(crime, live_state(live_event(EVENT, kind="reported_crime", lonlat=near))).novel


def test_the_compatibility_table_covers_every_event_class_and_never_names_a_forbidden_kind():
    assert set(CORROBORATING_KINDS) == set(kinds.EVENT_CLASSES)
    for cls, allowed in CORROBORATING_KINDS.items():
        assert allowed and allowed <= set(kinds.ALL_EVENT_KINDS), cls
        assert not allowed & {"protected_movement", "vehicle_pursuit", "crime_incident"}, cls


def test_the_nearest_live_event_wins_and_ties_break_by_urn():
    crash = make_signal(title="Multi-vehicle crash near Karnavati Club", published_at=at(60))
    near = live_event("event:00000000-0000-4000-8000-0000000000b2", kind="road_accident",
                      lonlat=offset(KARNAVATI_CLUB, north_m=200))
    nearer = live_event("event:00000000-0000-4000-8000-0000000000b9", kind="road_accident",
                        lonlat=offset(KARNAVATI_CLUB, north_m=100))
    (sit,) = situations([crash], [karnavati(crash)])
    assert attach_one(sit, live_state(near, nearer)).corroborates_live_urn == nearer.urn
    twin = live_event("event:00000000-0000-4000-8000-0000000000a1", kind="road_accident",
                      lonlat=offset(KARNAVATI_CLUB, north_m=100))
    assert attach_one(sit, live_state(nearer, twin)).corroborates_live_urn == twin.urn


def test_a_stale_report_does_not_corroborate_todays_event():
    old = make_signal(title="Multi-vehicle crash near Karnavati Club", published_at=at(0) - timedelta(hours=12))
    live = live_state(live_event(EVENT, kind="road_accident", lonlat=KARNAVATI_CLUB), as_of=FETCHED)
    (sit,) = situations([old], [karnavati(old)])
    assert attach_one(sit, live).novel  # 12 h + 2 h before as_of, beyond the 6 h point window
    fresh = make_signal(title="Multi-vehicle crash near Karnavati Club", published_at=at(60))
    (sit,) = situations([fresh], [karnavati(fresh)])
    assert not attach_one(sit, live).novel  # the same event, a current report


def test_only_an_active_live_event_is_corroborated():
    # planning / approved have not started (a live ref has no time window to show an overlap); completed and
    # cancelled are over
    crash = make_signal(title="Multi-vehicle crash near Karnavati Club", published_at=at(60))
    (sit,) = situations([crash], [karnavati(crash)])
    for status in ("planning", "approved", "completed", "cancelled"):
        ref = live_event(EVENT, kind="road_accident", status=status, lonlat=KARNAVATI_CLUB)
        assert attach_one(sit, live_state(ref)).novel, status
    ref = live_event(EVENT, kind="road_accident", status="active", lonlat=KARNAVATI_CLUB)
    assert attach_one(sit, live_state(ref)).corroborates_live_urn == EVENT


def test_area_level_situations_and_chatter_are_always_novel():
    alert = make_signal("sachet_cap", title="Thunderstorm warning for Ahmedabad district",
                        publisher="sachet.ndma.gov.in",
                        admin_codes=["LGD:AHMEDABAD"], published_at=at(60))
    live = live_state(live_event(EVENT, kind="hazard", lonlat=(72.5714, 23.0225)))  # exactly on the district point
    (sit,) = situations([alert], [district(alert)])
    assert attach_one(sit, live).novel
    chatter = make_signal(title="City library extends evening hours", published_at=at(60))
    (sit,) = situations([chatter], [point(chatter, KARNAVATI_CLUB)])
    assert attach_one(sit, live_state(live_event(EVENT, kind="road_accident", lonlat=KARNAVATI_CLUB))).novel


def test_no_live_state_means_novel():
    crash = make_signal(title="Multi-vehicle crash near Karnavati Club", published_at=at(60))
    (sit,) = situations([crash], [karnavati(crash)])
    assert attach_one(sit, None).novel


def test_attach_reads_a_resolved_event_too():
    crash = make_signal(title="Multi-vehicle crash near Karnavati Club", published_at=at(60))
    live = live_state(live_event(EVENT, kind="road_accident", lonlat=offset(KARNAVATI_CLUB, east_m=300)))
    (event,) = run_pipeline([crash], resolver=FakeResolver([karnavati(crash)])).resolved
    assert LiveSubject.of(event).segment_ids == frozenset({1045})
    assert LiveSubject.of(event).classes == ("road_accident",)
    assert attach([event], live)[0].corroborates_live_urn == EVENT


def test_kalupur_fixture_point_is_far_from_sg_highway():
    from osint_analysis.fusion import haversine_m

    d = haversine_m(KARNAVATI_CLUB[1], KARNAVATI_CLUB[0], KALUPUR_PURSUIT[1], KALUPUR_PURSUIT[0])
    assert d > 8_000
