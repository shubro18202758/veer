"""Stage 2 (correlate.correlate): the SG Highway affray+collision composite; unrelated classes never correlate;
same-level co-location; time overlap; the deterministic RESPONSE_PRIORITY tie-break; the candidate filter never
changes the result."""

from __future__ import annotations

import random

import pytest

from analysis_fixtures import (
    KARNAVATI_CLUB,
    ODHAV_CIRCLE,
    PALDI_CROSS_ROADS,
    at,
    district,
    karnavati,
    make_signal,
    offset,
    point,
    sg_highway_geocodes,
    state,
    FakeResolver,
)
from osint_common import kinds, testing
from osint_analysis.classify import classify
from osint_analysis.correlate import correlate, rank_classes, related
from osint_analysis.fusion import make_member, stage1
from osint_analysis.pipeline import run_pipeline


def situations(signals, geocodes):
    by_id = {g.signal_id: g for g in geocodes}
    members = [make_member(s, by_id[s.signal_id], classify(s)) for s in signals]
    return correlate(stage1(members))


def test_sg_highway_replica_is_one_situation_affray_plus_collision():
    sg = testing.sg_highway_signals()
    sits = situations(sg, sg_highway_geocodes(sg))
    assert len(sits) == 1
    (sit,) = sits
    assert list(sit.classes) == ["road_accident", "public_conflict"]
    assert sit.primary_class == "road_accident" and sit.correlated
    assert len(sit.members) == 5
    # and through the pipeline: the composite subtype, the primary class's kinds
    result = run_pipeline(sg, resolver=FakeResolver(sg_highway_geocodes(sg)))
    (event,) = result.resolved
    assert event.is_event
    assert event.correlated_classes == ["road_accident", "public_conflict"]
    assert event.subtype == "affray+collision"
    assert (event.veer_event_kind, event.veer_incident_kind) == ("road_accident", "accident")
    assert event.segment_id == 1045 and event.toponym == "Karnavati Club (SG Highway)"
    assert result.counts.correlated == 1


def test_unrelated_classes_never_correlate_even_at_one_point():
    pairs = [
        ("Fire at a showroom near Karnavati Club", "Multi-vehicle crash near Karnavati Club"),  # fire + accident
        ("Jewellery shop robbed near Karnavati Club", "Waterlogging near Karnavati Club after heavy rain"),
        ("Huge crowd at the Karnavati Club fair", "Wall collapse near Karnavati Club"),  # gathering + infra
    ]
    for t1, t2 in pairs:
        a, b = make_signal(title=t1), make_signal(title=t2, publisher="news-b.example")
        ca, cb = classify(a).event_class, classify(b).event_class
        assert not related(ca, cb), (ca, cb)
        assert len(situations([a, b], [karnavati(a), karnavati(b)])) == 2, (ca, cb)


def test_every_related_pair_correlates_when_co_located_and_overlapping():
    cue = {
        "road_accident": "Multi-vehicle crash", "public_conflict": "Stone pelting", "reported_crime": "Shop robbed",
        "unrest": "Traders observe bandh", "urban_flooding": "Waterlogging", "infra_failure": "Wall collapse",
        "road_closure": "Road closed for metro work", "weather_hazard": "Thunderstorm warning",
        "fire": "Massive fire", "hazard": "Chemical spill", "public_gathering": "Huge crowd",
        "procession": "Rath Yatra procession",
    }
    for pair in kinds.RELATED_CLASSES:
        x, y = sorted(pair)
        a = make_signal(title=f"{cue[x]} near Paldi cross roads", published_at=at(0))
        b = make_signal(title=f"{cue[y]} near Paldi cross roads", publisher="news-b.example", published_at=at(60))
        assert (classify(a).event_class, classify(b).event_class) == (x, y)
        geos = [point(s, PALDI_CROSS_ROADS, toponym="Paldi Cross Roads", feature_type="junction", junction_id=4)
                for s in (a, b)]
        sits = situations([a, b], geos)
        assert len(sits) == 1 and set(sits[0].classes) == {x, y}, pair


def test_related_but_too_far_or_too_late_does_not_correlate():
    a = make_signal(title="Multi-vehicle crash near Karnavati Club", published_at=at(0))
    far = make_signal(title="Stone pelting after a crash", publisher="news-b.example", published_at=at(30))
    late = make_signal(title="Stone pelting after a crash", publisher="news-b.example", published_at=at(13 * 60))
    assert len(situations([a, far], [karnavati(a), point(far, offset(KARNAVATI_CLUB, north_m=1500))])) == 2
    # 13 h later is beyond both point windows (6 h)
    assert len(situations([a, late], [karnavati(a), karnavati(late)])) == 2


def _two_accidents_and_a_clash(clash_north_m: float):
    """Two accidents 2.2 km apart (Stage 1 keeps them apart) and a clash report between them on one line."""
    title = "Multi-vehicle crash on the highway, three injured"
    a1 = make_signal(title=title, published_at=at(0))
    a2 = make_signal(title=title, publisher="news-b.example", published_at=at(10))
    clash = make_signal(title="Stone pelting and clash near the highway", publisher="news-c.example",
                        published_at=at(20))
    geos = [
        point(a1, KARNAVATI_CLUB, toponym="Karnavati Club"),
        point(a2, offset(KARNAVATI_CLUB, north_m=2200), toponym="Two km north"),
        point(clash, offset(KARNAVATI_CLUB, north_m=clash_north_m), toponym="Between"),
    ]
    return a1, a2, clash, geos


def test_a_report_between_two_accidents_joins_only_one_of_them():
    # the clash is 1.1 km from each accident (within the 1.2 km Stage-2 radius of both): it must not chain them
    a1, a2, clash, geos = _two_accidents_and_a_clash(1100)
    sits = situations([a1, a2, clash], geos)
    assert len(sits) == 2
    for sit in sits:
        assert len({c.event_class for c in sit.clusters}) == len(sit.clusters)  # one cluster per class
    by_members = {frozenset(m.signal_id for m in s.members): s for s in sits}
    # equidistant: the earlier accident takes the clash, the later one keeps its own place
    assert set(by_members) == {frozenset({a1.signal_id, clash.signal_id}), frozenset({a2.signal_id})}
    # nearer to the second accident: the clash joins it instead
    a1, a2, clash, geos = _two_accidents_and_a_clash(1300)
    sits = situations([a1, a2, clash], geos)
    assert {frozenset(m.signal_id for m in s.members) for s in sits} == {
        frozenset({a1.signal_id}), frozenset({a2.signal_id, clash.signal_id})
    }
    # through the pipeline: two surfaced accidents, each at its own place, one of them affray+collision
    result = run_pipeline([a1, a2, clash], resolver=FakeResolver(geos))
    assert result.counts.surfaced == 2 and result.counts.correlated == 1
    assert sorted(r.toponym for r in result.resolved) == ["Karnavati Club", "Two km north"]
    # and in any input order
    for order in ([clash, a2, a1], [a2, clash, a1]):
        again = situations(order, geos)
        assert {frozenset(m.signal_id for m in s.members) for s in again} == {
            frozenset({a1.signal_id}), frozenset({a2.signal_id, clash.signal_id})
        }


def test_equally_near_candidates_go_to_the_earlier_cluster():
    # two flood alerts for the district that Stage 1 keeps apart (no shared words) and a thunderstorm alert for the
    # same district: both joins are at distance 0, the earlier flood alert takes the storm, the other stays alone
    sachet = {"publisher": "sachet.ndma.gov.in", "admin_codes": ["LGD:AHMEDABAD"]}
    flood1 = make_signal("sachet_cap", title="Heavy rain warning for Ahmedabad district", published_at=at(0), **sachet)
    flood2 = make_signal("sachet_cap", title="Waterlogging likely in low-lying areas", published_at=at(10), **sachet)
    storm = make_signal("sachet_cap", title="Thunderstorm warning", published_at=at(20), **sachet)
    assert [classify(s).event_class for s in (flood1, flood2, storm)] == [
        "urban_flooding", "urban_flooding", "weather_hazard"
    ]
    sits = situations([storm, flood2, flood1], [district(s) for s in (flood1, flood2, storm)])
    assert {frozenset(m.signal_id for m in s.members) for s in sits} == {
        frozenset({flood1.signal_id, storm.signal_id}), frozenset({flood2.signal_id})
    }


def test_a_situation_never_holds_two_clusters_of_one_class_through_another_class():
    # a fire between two separate hazard spills, and an infrastructure failure next to the fire: the fire takes one
    # spill (the nearer), the other spill stays its own situation
    fire = make_signal(title="Massive fire at a godown", published_at=at(0))
    spill_near = make_signal(title="Chemical spill at an industrial unit", publisher="news-b.example",
                             published_at=at(5))
    spill_far = make_signal(title="Oil spill on the service road", publisher="news-c.example", published_at=at(8))
    wall = make_signal(title="Wall collapse next to the godown", publisher="news-d.example", published_at=at(9))
    geos = [
        point(fire, PALDI_CROSS_ROADS, toponym="Paldi"),
        point(spill_near, offset(PALDI_CROSS_ROADS, east_m=500), toponym="East"),
        point(spill_far, offset(PALDI_CROSS_ROADS, east_m=-1000), toponym="West"),
        point(wall, offset(PALDI_CROSS_ROADS, north_m=300), toponym="North"),
    ]
    sits = situations([fire, spill_near, spill_far, wall], geos)
    assert {frozenset(m.signal_id for m in s.members) for s in sits} == {
        frozenset({fire.signal_id, spill_near.signal_id, wall.signal_id}), frozenset({spill_far.signal_id})
    }
    for sit in sits:
        assert len({c.event_class for c in sit.clusters}) == len(sit.clusters)


def test_a_state_cluster_never_correlates_with_a_district_or_point_cluster():
    flood_state = make_signal("sachet_cap", title="Heavy rain warning over many districts",
                              publisher="sachet.ndma.gov.in",
                              admin_codes=["LGD:GUJARAT"])
    wall = make_signal(title="Wall collapse near Paldi cross roads")
    sits = situations([flood_state, wall], [state(flood_state), point(wall, PALDI_CROSS_ROADS)])
    assert len(sits) == 2
    assert any(s.all_state_level for s in sits)


def test_a_district_alert_does_not_locate_a_point_situation_by_containment_alone():
    alert = make_signal("sachet_cap", title="Heavy rain warning for Ahmedabad district", publisher="sachet.ndma.gov.in",
                        admin_codes=["LGD:AHMEDABAD"])
    wall = make_signal(title="Wall collapse near Paldi cross roads")  # infra_failure, related to urban_flooding
    assert related(classify(alert).event_class, classify(wall).event_class)
    assert len(situations([alert, wall], [district(alert), point(wall, PALDI_CROSS_ROADS)])) == 2
    # two district clusters of the same district do correlate
    storm = make_signal("sachet_cap", title="Thunderstorm warning for Ahmedabad district",
                        publisher="sachet.ndma.gov.in",
                        admin_codes=["LGD:AHMEDABAD"])
    sits = situations([alert, storm], [district(alert), district(storm)])
    assert len(sits) == 1 and set(sits[0].classes) == {"urban_flooding", "weather_hazard"}


def test_priority_ties_break_by_member_count_then_earliest_report():
    # road_accident and public_conflict are both priority 8 (the OS-1 carry-over)
    assert kinds.RESPONSE_PRIORITY["road_accident"] == kinds.RESPONSE_PRIORITY["public_conflict"]
    conflict = [make_signal(title="Stone pelting near Odhav circle", publisher=p, published_at=at(m))
                for p, m in (("news-a.example", 0), ("news-b.example", 10), ("news-c.example", 20))]
    crash = make_signal(title="Multi-vehicle crash near Odhav circle", publisher="news-d.example", published_at=at(-30))
    geos = [point(s, ODHAV_CIRCLE, toponym="Odhav Ring Road Circle", feature_type="junction", junction_id=11)
            for s in (*conflict, crash)]
    (sit,) = situations([*conflict, crash], geos)
    assert list(sit.classes) == ["public_conflict", "road_accident"]  # three conflict reports outnumber one
    one = [conflict[0], crash]
    (sit,) = situations(one, [geos[0], geos[3]])
    assert list(sit.classes) == ["road_accident", "public_conflict"]  # one each: the earliest report leads


def test_rank_classes_is_order_independent():
    sg = testing.sg_highway_signals()
    geos = {g.signal_id: g for g in sg_highway_geocodes(sg)}
    rng = random.Random(3)
    for _ in range(5):
        order = sg[:]
        rng.shuffle(order)
        members = [make_member(s, geos[s.signal_id], classify(s)) for s in order]
        assert rank_classes(members) == ["road_accident", "public_conflict"]
        (sit,) = correlate(stage1(members))
        assert [m.signal_id for m in sit.members] == sorted(
            (s.signal_id for s in sg), key=lambda i: ({s.signal_id: s for s in sg}[i].published_at, i)
        )


@pytest.mark.parametrize("seed", [1, 2, 3])
def test_the_candidate_filter_never_changes_the_situations(monkeypatch, seed):
    # Stage 2 tests only the pairs its vectorised filter lets through: on a random city-wide mix of classes, roads,
    # districts, states and realms, the situations equal those of testing every pair
    from analysis_fixtures import NEHRU_BRIDGE_ROAD, road
    import osint_analysis.correlate as corr

    cue = ["Multi-vehicle crash", "Stone pelting", "Shop robbed", "Traders observe bandh", "Waterlogging",
           "Wall collapse", "Road closed for metro work", "Thunderstorm warning", "Massive fire", "Chemical spill",
           "Huge crowd", "Rath Yatra procession"]
    rng = random.Random(seed)
    signals, geos = [], []
    for i in range(260):
        kind = rng.random()
        label = "SIMULATED" if rng.random() < 0.1 else None
        if kind < 0.08:
            s = make_signal("sachet_cap", title=rng.choice(["Heavy rain warning", "Thunderstorm warning"]),
                            publisher="sachet.ndma.gov.in", admin_codes=["LGD:AHMEDABAD"],
                            published_at=at(rng.uniform(0, 1440)), provenance_label=label)
            geos.append(district(s) if kind < 0.05 else state(s))
        else:
            s = make_signal(title=f"{rng.choice(cue)} near the circle, update {i % 5}",
                            publisher=f"news-{i % 6}.example", published_at=at(rng.uniform(0, 1440)),
                            provenance_label=label)
            where = offset(PALDI_CROSS_ROADS, north_m=rng.uniform(-4000, 4000), east_m=rng.uniform(-4000, 4000))
            if kind < 0.25:
                geos.append(road(s, rng.choice([1015, 1045]), where if rng.random() < 0.5 else NEHRU_BRIDGE_ROAD))
            else:
                geos.append(point(s, where, segment_id=rng.choice([None, 1015, 1045]),
                                  residual_m=rng.uniform(0, 1500)))
        signals.append(s)
    by_id = {g.signal_id: g for g in geos}
    base = stage1([make_member(s, by_id[s.signal_id], classify(s)) for s in signals])

    def shape(sits):
        return sorted((sorted(m.signal_id for m in s.members), list(s.classes)) for s in sits)

    filtered = correlate(base)
    with monkeypatch.context() as m:
        m.setattr(corr, "_candidate_pairs", lambda ordered: [(i, j) for i in range(len(ordered))
                                                             for j in range(i + 1, len(ordered))])
        every_pair = corr.correlate(base)
    assert shape(filtered) == shape(every_pair)
    assert sum(1 for s in filtered if s.correlated) >= 3  # the layout really correlates something
