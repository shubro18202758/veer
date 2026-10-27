"""second_order_flags(): protected corridor, convoy, 108 ambulance route and closure flags, each with a short neutral
note; none for an area-level, stale or held situation, or without a live state."""

from __future__ import annotations

from datetime import timedelta

from analysis_fixtures import (
    KARNAVATI_CLUB,
    ODHAV_CIRCLE,
    FakeResolver,
    at,
    district,
    karnavati,
    live_event,
    live_state,
    make_signal,
    offset,
    point,
)
from osint_common import ethics
from osint_analysis.classify import classify
from osint_analysis.correlate import correlate
from osint_analysis.fusion import make_member, stage1
from osint_analysis.pipeline import run_pipeline
from osint_analysis.second_order import second_order_flags

VVIP = "event:00000000-0000-4000-8000-0000000000c1"
CONVOY = "convoy:mv-0042"
DISPATCH = "dispatch:00000000-0000-4000-8000-0000000000d1"
CLOSURE_EVENT = "event:00000000-0000-4000-8000-0000000000e1"


def crash_situation(published=at(60)):
    crash = make_signal(title="Multi-vehicle crash near Karnavati Club on SG Highway", published_at=published)
    (sit,) = correlate(stage1([make_member(crash, karnavati(crash), classify(crash))]))
    return crash, sit


def kinds_of(flags):
    return [(f.kind, f.urn, f.segment_id) for f in flags]


def test_protected_corridor_flag_on_an_active_protected_movement_route():
    _, sit = crash_situation()
    live = live_state(live_event(VVIP, kind="protected_movement", status="active", segments=[1044, 1045]))
    flags = second_order_flags(sit, live)
    assert kinds_of(flags) == [("protected_corridor", VVIP, 1045)]
    assert "protected movement" in flags[0].note
    # a landmark snapped 190 m onto the segment is "on or near" it, never claimed to be on it
    assert flags[0].note.startswith("Reported on or near segment 1045")


def test_a_planned_protected_movement_is_not_yet_a_second_order_effect():
    _, sit = crash_situation()
    for status in ("planning", "approved"):
        live = live_state(live_event(VVIP, kind="protected_movement", status=status, segments=[1045]))
        assert second_order_flags(sit, live) == []


def test_ambulance_route_flag():
    _, sit = crash_situation()
    flags = second_order_flags(sit, live_state(ambulance=[(DISPATCH, [1020, 1045])]))
    assert kinds_of(flags) == [("ambulance_route", DISPATCH, 1045)]
    assert "108" in flags[0].note


def test_closure_flag():
    _, sit = crash_situation()
    flags = second_order_flags(sit, live_state(closures=[(1045, CLOSURE_EVENT), (1003, CLOSURE_EVENT)]))
    assert kinds_of(flags) == [("closure", CLOSURE_EVENT, 1045)]
    assert "closed" in flags[0].note


def test_convoy_flag_on_its_route_or_near_its_position():
    _, sit = crash_situation()
    on_route = live_event(CONVOY, kind="protected_movement", status="active", segments=[1045])
    assert kinds_of(second_order_flags(sit, live_state(on_route))) == [("convoy", CONVOY, 1045)]
    nearby = live_event(CONVOY, kind="protected_movement", status="active", lonlat=offset(KARNAVATI_CLUB, east_m=400))
    flags = second_order_flags(sit, live_state(nearby))
    assert kinds_of(flags) == [("convoy", CONVOY, None)] and "m from a convoy" in flags[0].note
    far = live_event(CONVOY, kind="protected_movement", status="active", lonlat=offset(KARNAVATI_CLUB, east_m=4000))
    assert second_order_flags(sit, live_state(far)) == []


def test_all_flags_together_ordered_and_deduplicated():
    _, sit = crash_situation()
    live = live_state(
        live_event(VVIP, kind="protected_movement", status="active", segments=[1045, 1045]),
        live_event(CONVOY, kind="protected_movement", status="active", segments=[1045]),
        ambulance=[(DISPATCH, [1045])],
        closures=[(1045, CLOSURE_EVENT)],
    )
    flags = second_order_flags(sit, live)
    assert [f.kind for f in flags] == ["protected_corridor", "convoy", "ambulance_route", "closure"]
    for f in flags:
        assert 0 < len(f.note) <= 200 and ethics.find_pii(f.note) == []


def test_no_flag_off_the_route_for_area_level_or_stale_situations_or_without_live_state():
    _, sit = crash_situation()
    assert second_order_flags(sit, live_state(ambulance=[(DISPATCH, [1003])])) == []
    assert second_order_flags(sit, None) == []
    _, stale = crash_situation(published=at(0) - timedelta(hours=20))
    assert second_order_flags(stale, live_state(ambulance=[(DISPATCH, [1045])])) == []
    alert = make_signal("sachet_cap", title="Heavy rain warning for Ahmedabad district", publisher="sachet.ndma.gov.in",
                        admin_codes=["LGD:AHMEDABAD"], published_at=at(60))
    (area,) = correlate(stage1([make_member(alert, district(alert), classify(alert))]))
    assert second_order_flags(area, live_state(ambulance=[(DISPATCH, [1045])])) == []


def test_a_junction_only_report_raises_only_the_proximity_convoy_flag():
    robbery = make_signal(title="Shop robbed near Odhav Ring Road Circle", published_at=at(60))
    geo = point(robbery, ODHAV_CIRCLE, toponym="Odhav Ring Road Circle", feature_type="junction", junction_id=11)
    (sit,) = correlate(stage1([make_member(robbery, geo, classify(robbery))]))
    live = live_state(
        live_event(CONVOY, kind="protected_movement", status="active", lonlat=offset(ODHAV_CIRCLE, north_m=300)),
        ambulance=[(DISPATCH, [1045])],
    )
    assert [f.kind for f in second_order_flags(sit, live)] == ["convoy"]


def test_the_pipeline_flags_surfaced_situations_only():
    crash = make_signal(title="Multi-vehicle crash near Karnavati Club on SG Highway", published_at=at(60))
    post = make_signal("reddit_rss", title="Crash near Karnavati Club, traffic stuck",
                       publisher="social-a.example/r/example_city",
                       published_at=at(60))
    far_post_geo = point(post, offset(KARNAVATI_CLUB, north_m=-2500), segment_id=1045, residual_m=100.0)
    live = live_state(ambulance=[(DISPATCH, [1045])])
    result = run_pipeline([crash, post], resolver=FakeResolver([karnavati(crash), far_post_geo]), live=live)
    by_event = {r.is_event: r for r in result.resolved}
    assert [f.kind for f in by_event[True].second_order] == ["ambulance_route"]
    assert by_event[False].held_reason == "single social source (aggregate-only rule)"
    assert by_event[False].second_order == []
    allowed = ("protected_corridor", "ambulance_route", "closure", "convoy")
    assert all(f.kind in allowed for f in by_event[True].second_order)
